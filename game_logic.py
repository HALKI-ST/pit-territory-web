from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


BOARD_SIZE = 5
DIRECTION_DELTAS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

Cell = Tuple[int, int]


class GameError(ValueError):
    pass


@dataclass
class PlayerState:
    symbol: str
    name: str
    position: Cell
    trails: Set[Cell] = field(default_factory=set)
    pits_left: int = 2
    jumps_left: int = 1
    last_action: Optional[str] = None
    surrendered: bool = False
    connected: bool = False

    @property
    def score(self) -> int:
        return len(self.trails)

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "position": list(self.position),
            "trails": [list(cell) for cell in sorted(self.trails)],
            "pits_left": self.pits_left,
            "jumps_left": self.jumps_left,
            "last_action": self.last_action,
            "surrendered": self.surrendered,
            "connected": self.connected,
            "score": self.score,
        }


class GameState:
    def __init__(self) -> None:
        self.players: Dict[str, PlayerState] = {
            "O": PlayerState("O", "Player O", (0, 0)),
            "X": PlayerState("X", "Player X", (BOARD_SIZE - 1, BOARD_SIZE - 1)),
        }
        self.turn = "O"
        self.pits: Set[Cell] = set()
        self.started = False
        self.game_over = False
        self.message = "もう1人の参加を待っています。"
        self.winner_text = ""

    def set_player_name(self, symbol: str, name: str) -> None:
        cleaned = name.strip() or f"Player {symbol}"
        self.players[symbol].name = cleaned[:24]

    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

    def occupied_cells(self) -> Set[Cell]:
        return {player.position for player in self.players.values()}

    def trail_owner(self, cell: Cell) -> Optional[str]:
        for symbol, player in self.players.items():
            if cell in player.trails:
                return symbol
        return None

    def can_move_to(self, cell: Cell) -> bool:
        return (
            self.in_bounds(cell)
            and cell not in self.occupied_cells()
            and cell not in self.pits
            and self.trail_owner(cell) is None
        )

    def start_if_ready(self) -> None:
        if all(player.name for player in self.players.values()):
            self.started = True
            self.message = f"{self.players[self.turn].name}（{self.turn}）の手番です。"

    def apply_action(
        self,
        symbol: str,
        action: str,
        direction: Optional[str] = None,
        cell: Optional[List[int]] = None,
    ) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.game_over:
            raise GameError("ゲームは終了しています。")
        if symbol != self.turn:
            raise GameError("いまはあなたの手番ではありません。")

        player = self.players[symbol]
        if player.surrendered:
            raise GameError("あなたはすでに行動終了しています。")

        if action == "move":
            self._move(player, direction)
        elif action == "jump":
            self._jump(player, direction)
        elif action == "pit":
            self._pit(player, cell)
        elif action == "pass":
            self._pass(player)
        else:
            raise GameError("不明な行動です。")

    def _move(self, player: PlayerState, direction: Optional[str]) -> None:
        dx, dy = self._parse_direction(direction)
        new_cell = (player.position[0] + dx, player.position[1] + dy)
        if not self.can_move_to(new_cell):
            raise GameError("そこには移動できません。")

        origin = player.position
        player.trails.add(origin)
        player.position = new_cell
        player.last_action = "move"
        self.message = f"{player.name} が {self.cell_label(new_cell)} に移動しました。"
        self._end_turn()

    def _jump(self, player: PlayerState, direction: Optional[str]) -> None:
        if player.jumps_left <= 0:
            raise GameError("ジャンプはもう使えません。")

        dx, dy = self._parse_direction(direction)
        middle = (player.position[0] + dx, player.position[1] + dy)
        landing = (player.position[0] + dx * 2, player.position[1] + dy * 2)
        if not self.in_bounds(middle) or not self.in_bounds(landing):
            raise GameError("ジャンプの着地点が盤面の外です。")
        if not self.can_move_to(landing):
            raise GameError("そこにはジャンプで着地できません。")

        origin = player.position
        player.trails.add(origin)
        player.position = landing
        player.jumps_left -= 1
        player.last_action = "jump"
        self.message = f"{player.name} が {self.cell_label(landing)} にジャンプしました。"
        self._end_turn()

    def _pit(self, player: PlayerState, cell: Optional[List[int]]) -> None:
        if player.pits_left <= 0:
            raise GameError("落とし穴はもう置けません。")
        if player.last_action == "pit":
            raise GameError("落とし穴は2ターン連続で置けません。")
        if not isinstance(cell, list) or len(cell) != 2:
            raise GameError("落とし穴を置くマスを選んでください。")

        target = (int(cell[0]), int(cell[1]))
        if not self.in_bounds(target):
            raise GameError("指定したマスは盤面の外です。")
        if target in self.occupied_cells():
            raise GameError("駒のある場所には落とし穴を置けません。")
        if target in self.pits:
            raise GameError("そこにはすでに落とし穴があります。")
        if self.trail_owner(target) is not None:
            raise GameError("足跡のある場所には落とし穴を置けません。")

        self.pits.add(target)
        player.pits_left -= 1
        player.last_action = "pit"
        self.message = f"{player.name} が {self.cell_label(target)} に落とし穴を置きました。"
        self._end_turn()

    def _pass(self, player: PlayerState) -> None:
        player.surrendered = True
        player.last_action = "pass"
        self.message = f"{player.name} は以後行動しません。"
        self._end_turn()

    def _parse_direction(self, direction: Optional[str]) -> Cell:
        if direction not in DIRECTION_DELTAS:
            raise GameError("移動方向が正しくありません。")
        return DIRECTION_DELTAS[direction]

    def _end_turn(self) -> None:
        if all(player.surrendered for player in self.players.values()):
            self._finish_game()
            return

        current = self.players[self.turn]
        next_symbol = "X" if self.turn == "O" else "O"
        next_player = self.players[next_symbol]

        if current.surrendered and not next_player.surrendered:
            self.turn = next_symbol
            return

        if next_player.surrendered and not current.surrendered:
            self.message += f" {next_player.name} は行動終了しているため、{current.name} が続けて行動します。"
            return

        self.turn = next_symbol

    def _finish_game(self) -> None:
        self.game_over = True
        o_score = self.players["O"].score
        x_score = self.players["X"].score
        if o_score > x_score:
            self.winner_text = f"{self.players['O'].name} の勝ちです。 {o_score} 対 {x_score}"
        elif x_score > o_score:
            self.winner_text = f"{self.players['X'].name} の勝ちです。 {x_score} 対 {o_score}"
        else:
            self.winner_text = f"引き分けです。 {o_score} 対 {x_score}"
        self.message = "ゲーム終了です。"

    @staticmethod
    def cell_label(cell: Cell) -> str:
        return f"({cell[0] + 1}, {cell[1] + 1})"

    def to_public_dict(self) -> dict:
        return {
            "board_size": BOARD_SIZE,
            "turn": self.turn,
            "started": self.started,
            "game_over": self.game_over,
            "message": self.message,
            "winner_text": self.winner_text,
            "pits": [list(cell) for cell in sorted(self.pits)],
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
        }
