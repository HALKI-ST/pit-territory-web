from __future__ import annotations

import asyncio
import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from games import GAME_CATALOG, create_game
from games.pit_territory import GameError


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ROOM_CODE_CHARS = string.ascii_uppercase + string.digits


class CreateRoomRequest(BaseModel):
    name: str = ""
    game_type: str


class JoinRoomRequest(BaseModel):
    name: str = ""


@dataclass
class Room:
    code: str
    game_type: str
    game: object
    token_to_symbol: Dict[str, str] = field(default_factory=dict)
    sockets: Dict[str, WebSocket] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def public_state(self) -> dict:
        state = self.game.to_public_dict()
        return {
            "room_code": self.code,
            "players_joined": len(self.token_to_symbol),
            "game_type": self.game_type,
            **state,
        }


rooms: Dict[str, Room] = {}
app = FastAPI(title="ST-SPACE Games")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def generate_room_code(length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(ROOM_CODE_CHARS) for _ in range(length))
        if code not in rooms:
            return code


def create_token() -> str:
    return secrets.token_urlsafe(24)


def get_room_or_404(room_code: str) -> Room:
    room = rooms.get(room_code.upper())
    if room is None:
        raise HTTPException(status_code=404, detail="ルームが見つかりません。")
    return room


async def broadcast_state(room: Room) -> None:
    state_message = {"type": "state", "state": room.public_state()}
    disconnected = []
    for token, websocket in room.sockets.items():
        try:
            await websocket.send_json(state_message)
        except Exception:
            disconnected.append(token)

    for token in disconnected:
        room.sockets.pop(token, None)
        symbol = room.token_to_symbol.get(token)
        if symbol:
            room.game.players[symbol].connected = False


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/games")
async def games() -> dict:
    return {"games": GAME_CATALOG}


@app.post("/api/rooms")
async def create_room(payload: CreateRoomRequest) -> dict:
    try:
        game = create_game(payload.game_type)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="未対応のゲームです。") from exc

    room_code = generate_room_code()
    room = Room(code=room_code, game_type=payload.game_type, game=game)
    token = create_token()
    room.token_to_symbol[token] = "O"
    room.game.set_player_name("O", payload.name)
    rooms[room_code] = room
    return {
        "room_code": room_code,
        "player_token": token,
        "player_symbol": "O",
        "game_type": payload.game_type,
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, payload: JoinRoomRequest) -> dict:
    room = get_room_or_404(room_code)

    if len(room.token_to_symbol) >= 2:
        raise HTTPException(status_code=400, detail="このルームは満員です。")

    token = create_token()
    room.token_to_symbol[token] = "X"
    room.game.set_player_name("X", payload.name)
    room.game.start_if_ready()
    await broadcast_state(room)
    return {
        "room_code": room.code,
        "player_token": token,
        "player_symbol": "X",
        "game_type": room.game_type,
    }


@app.websocket("/ws/{room_code}/{player_token}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_token: str) -> None:
    room = rooms.get(room_code.upper())
    if room is None or player_token not in room.token_to_symbol:
        await websocket.close(code=1008)
        return

    symbol = room.token_to_symbol[player_token]
    await websocket.accept()

    async with room.lock:
        room.sockets[player_token] = websocket
        room.game.players[symbol].connected = True
        if len(room.token_to_symbol) == 2:
            room.game.start_if_ready()
        await broadcast_state(room)

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "action":
                await websocket.send_json(
                    {"type": "error", "message": "対応していないメッセージです。"}
                )
                continue

            async with room.lock:
                try:
                    room.game.apply_action(
                        symbol=symbol,
                        action=payload.get("action", ""),
                        direction=payload.get("direction"),
                        cell=payload.get("cell"),
                    )
                except GameError as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                else:
                    await broadcast_state(room)
    except WebSocketDisconnect:
        async with room.lock:
            room.sockets.pop(player_token, None)
            room.game.players[symbol].connected = False
            room.game.message = f"{room.game.players[symbol].name} が切断しました。"
            await broadcast_state(room)
