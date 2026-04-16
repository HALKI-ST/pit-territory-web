from __future__ import annotations

import asyncio
import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from games import GAME_CATALOG, create_game
from games.english_shooter import WORD_BANK as ENGLISH_SHOOTER_WORD_BANK


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ROOM_CODE_CHARS = string.ascii_uppercase + string.digits


class CreateRoomRequest(BaseModel):
    name: str = ""
    game_type: str


class JoinRoomRequest(BaseModel):
    name: str = ""


def game_seat_order(game: Any) -> list[str]:
    return list(getattr(game, "seat_order", []))


def game_max_players(game: Any) -> int:
    max_players = getattr(game, "max_players", None)
    if isinstance(max_players, int):
        return max_players
    seats = game_seat_order(game)
    return len(seats) if seats else 2


def game_min_players(game: Any) -> int:
    min_players = getattr(game, "min_players", None)
    if isinstance(min_players, int):
        return min_players
    return 2


def game_host_actions(game: Any) -> set[str]:
    return set(getattr(game, "host_control_actions", set()))


def game_started(game: Any) -> bool:
    started = getattr(game, "started", False)
    if callable(started):
        return bool(started())
    return bool(started)


def game_allows_midgame_join(game: Any) -> bool:
    return bool(getattr(game, "allow_midgame_join", False))


def game_to_public_dict(game: Any, viewer_symbol: str) -> dict:
    try:
        return game.to_public_dict(viewer_symbol=viewer_symbol)
    except TypeError:
        return game.to_public_dict()


def set_game_connection(game: Any, symbol: str, connected: bool) -> None:
    if hasattr(game, "update_connection"):
        game.update_connection(symbol, connected)
    elif symbol in getattr(game, "players", {}):
        game.players[symbol].connected = connected


def get_game_error_message(exc: Exception) -> str | None:
    if isinstance(exc, ValueError):
        return str(exc)
    return None


@dataclass
class Room:
    code: str
    game_type: str
    game: Any
    host_token: str
    token_to_symbol: Dict[str, str] = field(default_factory=dict)
    sockets: Dict[str, WebSocket] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def host_symbol(self) -> str:
        return self.token_to_symbol.get(self.host_token, "")

    def player_count(self) -> int:
        return len(self.token_to_symbol)

    def next_available_symbol(self) -> str | None:
        for symbol in game_seat_order(self.game):
            if symbol not in self.token_to_symbol.values():
                return symbol
        return None

    def public_state_for(self, player_token: str) -> dict:
        viewer_symbol = self.token_to_symbol.get(player_token, "")
        state = game_to_public_dict(self.game, viewer_symbol)
        return {
            "room_code": self.code,
            "player_symbol": viewer_symbol,
            "players_joined": self.player_count(),
            "min_players": game_min_players(self.game),
            "max_players": game_max_players(self.game),
            "game_type": self.game_type,
            "host_symbol": self.host_symbol(),
            **state,
        }

    def reset_game(self) -> None:
        if hasattr(self.game, "reset_for_rematch"):
            self.game.reset_for_rematch()
            return

        saved_names = {
            symbol: player.name
            for symbol, player in getattr(self.game, "players", {}).items()
        }
        saved_connections = {
            symbol: player.connected
            for symbol, player in getattr(self.game, "players", {}).items()
        }
        self.game = create_game(self.game_type)
        for symbol, name in saved_names.items():
            self.game.set_player_name(symbol, name)
            set_game_connection(self.game, symbol, saved_connections.get(symbol, False))


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
    disconnected: list[str] = []
    for token, websocket in room.sockets.items():
        try:
            await websocket.send_json({"type": "state", "state": room.public_state_for(token)})
        except Exception:
            disconnected.append(token)

    for token in disconnected:
        room.sockets.pop(token, None)
        symbol = room.token_to_symbol.get(token)
        if symbol:
            set_game_connection(room.game, symbol, False)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/games")
async def games() -> dict:
    return {"games": GAME_CATALOG}


@app.get("/api/english-shooter-words")
async def english_shooter_words() -> dict:
    words = [
        {
            "english": item["english"],
            "japanese": " / ".join(item["japanese"]),
        }
        for item in ENGLISH_SHOOTER_WORD_BANK
    ]
    return {"words": words, "count": len(words)}


@app.post("/api/rooms")
async def create_room(payload: CreateRoomRequest) -> dict:
    try:
        game = create_game(payload.game_type)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="未対応のゲームです。") from exc

    first_symbol = game_seat_order(game)[0]
    room_code = generate_room_code()
    token = create_token()
    room = Room(code=room_code, game_type=payload.game_type, game=game, host_token=token)
    room.token_to_symbol[token] = first_symbol
    room.game.set_player_name(first_symbol, payload.name)
    rooms[room_code] = room
    return {
        "room_code": room_code,
        "player_token": token,
        "player_symbol": first_symbol,
        "game_type": payload.game_type,
    }


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, payload: JoinRoomRequest) -> dict:
    room = get_room_or_404(room_code)

    if game_started(room.game) and not game_allows_midgame_join(room.game):
        raise HTTPException(status_code=400, detail="ゲーム開始後は途中参加できません。")

    if room.player_count() >= game_max_players(room.game):
        raise HTTPException(status_code=400, detail="このルームは満員です。")

    symbol = room.next_available_symbol()
    if symbol is None:
        raise HTTPException(status_code=400, detail="参加できる席がありません。")

    token = create_token()
    room.token_to_symbol[token] = symbol
    room.game.set_player_name(symbol, payload.name)
    if hasattr(room.game, "start_if_ready"):
        room.game.start_if_ready()
    await broadcast_state(room)
    return {
        "room_code": room.code,
        "player_token": token,
        "player_symbol": symbol,
        "game_type": room.game_type,
    }


def ensure_host(room: Room, player_token: str) -> None:
    if room.host_token != player_token:
        raise ValueError("部屋を作った人だけがこの操作を行えます。")


def apply_player_action(room: Room, symbol: str, payload: dict) -> None:
    action = payload.get("action", "")
    if hasattr(room.game, "apply_player_action"):
        room.game.apply_player_action(
            symbol=symbol,
            action=action,
            bid_amount=payload.get("bid_amount"),
            direction=payload.get("direction"),
            cell=payload.get("cell"),
            edge_id=payload.get("edge_id"),
            piece=payload.get("piece"),
            clue_text=payload.get("clue_text"),
            clue_count=payload.get("clue_count"),
            card_index=payload.get("card_index"),
            answer_text=payload.get("answer_text"),
            winner_symbols=payload.get("winner_symbols"),
        )
        return

    room.game.apply_action(
        symbol=symbol,
        action=action,
        direction=payload.get("direction"),
        cell=payload.get("cell"),
    )


def apply_host_action(room: Room, payload: dict) -> None:
    action = payload.get("action", "")
    if action in game_host_actions(room.game) and hasattr(room.game, "apply_host_action"):
        room.game.apply_host_action(
            action=action,
            start_choice=payload.get("start_choice"),
            settings=payload.get("settings"),
            target_symbol=payload.get("target_symbol"),
            assigned_team=payload.get("assigned_team"),
            assigned_role=payload.get("assigned_role"),
        )
        return

    if action == "set_start_player" and hasattr(room.game, "set_start_player"):
        room.game.set_start_player(payload.get("start_choice", ""))
        return

    raise ValueError("不明な管理操作です。")


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
        set_game_connection(room.game, symbol, True)
        if hasattr(room.game, "start_if_ready"):
            room.game.start_if_ready()
        await broadcast_state(room)

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "action":
                await websocket.send_json({"type": "error", "message": "対応していないメッセージです。"})
                continue

            async with room.lock:
                try:
                    action = payload.get("action", "")
                    if action == "rematch":
                        room.reset_game()
                    elif action in game_host_actions(room.game) or action == "set_start_player":
                        ensure_host(room, player_token)
                        apply_host_action(room, payload)
                    else:
                        apply_player_action(room, symbol, payload)
                except Exception as exc:
                    message = get_game_error_message(exc)
                    if message is None:
                        raise
                    await websocket.send_json({"type": "error", "message": message})
                else:
                    await broadcast_state(room)
    except WebSocketDisconnect:
        async with room.lock:
            room.sockets.pop(player_token, None)
            set_game_connection(room.game, symbol, False)
            player_name = getattr(room.game.players.get(symbol), "name", symbol)
            room.game.message = f"{player_name} が切断しました。"
            await broadcast_state(room)
