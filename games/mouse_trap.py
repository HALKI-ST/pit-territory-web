from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


class GameError(ValueError):
    pass


BOARD_SIZE = 5
MAX_WALLS = 10
MAX_CHASE_TURNS = 10
Cell = Tuple[int, int]

IDS = [
    ["s1", "s2", "s3", "s4"],
    ["s6", "s7", "s8", "s9"],
    ["s11", "s12", "s13", "s14"],
    ["s16", "s17", "s18", "s19"],
    ["s21", "s22", "s23", "s24"],
]
IDH = [
    ["h1", "h2", "h3", "h4", "h5"],
    ["h6", "h7", "h8", "h9", "h10"],
    ["h11", "h12", "h13", "h14", "h15"],
    ["h16", "h17", "h18", "h19", "h20"],
]
VALID_S_IDS = {item for row in IDS for item in row}
VALID_H_IDS = {item for row in IDH for item in row}


@dataclass
class MouseTrapPlayer:
    symbol: str
    name: str
    connected: bool = False

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
        }


@dataclass
class MouseTrapState:
    walls: Set[str] = field(default_factory=set)
    humans: List[Cell] = field(default_factory=lambda: [(0, 0), (4, 4)])
    mouse: Cell = (2, 2)
    phase: str = "build"
    wall_turn_index: int = 0
    chase_turn: int = 1
    active_side: str = "H"
    mouse_steps_taken: int = 0
    game_over: bool = False
    winner: Optional[str] = None
    winner_text: str = ""
    message: str = "人間から壁を置き始めます。"
    build_log: List[str] = field(default_factory=list)
    chase_log: List[str] = field(default_factory=list)


class MouseTrapGame:
    game_type = "mouse_trap"
    title = "ネズミとり"
    subtitle = "迷宮を作ってから、人間がネズミを追い詰める非対称2人対戦。"
    min_players = 2
    max_players = 2
    seat_order = ["H", "M"]
    host_control_actions: set[str] = set()

    def __init__(self) -> None:
        self.players: Dict[str, MouseTrapPlayer] = {
            "H": MouseTrapPlayer("H", "人間"),
            "M": MouseTrapPlayer("M", "ネズミ"),
        }
        self.state = MouseTrapState()

    @classmethod
    def catalog_entry(cls) -> dict:
        return {
            "game_type": cls.game_type,
            "title": cls.title,
            "subtitle": cls.subtitle,
            "status": "playable",
            "min_players": cls.min_players,
            "max_players": cls.max_players,
        }

    def set_player_name(self, symbol: str, name: str) -> None:
        cleaned = name.strip()
        default_name = "人間" if symbol == "H" else "ネズミ"
        self.players[symbol].name = cleaned[:24] if cleaned else default_name

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def reset_for_rematch(self) -> None:
        saved_names = {symbol: player.name for symbol, player in self.players.items()}
        saved_connections = {symbol: player.connected for symbol, player in self.players.items()}
        self.__init__()
        for symbol, name in saved_names.items():
            self.players[symbol].name = name
            self.players[symbol].connected = saved_connections[symbol]
        self.state.message = "再戦の準備ができました。人間から壁を置き始めます。"

    def start_if_ready(self) -> None:
        self.state.message = "人間から壁を置き始めます。"

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        cell: Optional[List[int]] = None,
        edge_id: Optional[str] = None,
        piece: Optional[str] = None,
        **_: object,
    ) -> None:
        if self.state.game_over:
            raise GameError("ゲームは終了しています。")
        if action == "resign":
            self._resign(symbol)
            return
        if symbol != self.state.active_side:
            raise GameError("いまはあなたの番ではありません。")

        if self.state.phase == "build":
            if action != "place_wall":
                raise GameError("壁作成フェーズでは壁を置くだけです。")
            if not edge_id:
                raise GameError("壁の位置を選んでください。")
            self._place_wall(symbol, edge_id)
            return

        if self.state.phase != "chase":
            raise GameError("不正なフェーズです。")

        if action == "move_human":
            if not isinstance(cell, list) or len(cell) != 2:
                raise GameError("移動先を選んでください。")
            self._move_human(tuple(cell), piece or "")
            return
        if action == "move_mouse":
            if not isinstance(cell, list) or len(cell) != 2:
                raise GameError("移動先を選んでください。")
            self._move_mouse(tuple(cell))
            return
        raise GameError("不明な操作です。")

    def _place_wall(self, symbol: str, edge_id: str) -> None:
        if edge_id in self.state.walls:
            raise GameError("その壁はすでに置かれています。")
        if edge_id not in self.all_edges():
            raise GameError("壁の位置が不正です。")

        candidate = set(self.state.walls)
        candidate.add(edge_id)
        if self._creates_dead_end(candidate):
            raise GameError("袋小路になる壁は置けません。")
        if self._creates_four_chain(candidate):
            raise GameError("壁が4本以上連なる置き方はできません。")

        self.state.walls.add(edge_id)
        actor_label = "人間" if symbol == "H" else "ネズミ"
        self.state.build_log.append(f"{len(self.state.walls)}本目: {actor_label} が壁 {edge_id} を配置")
        self.state.wall_turn_index += 1

        if len(self.state.walls) >= MAX_WALLS:
            self.state.phase = "chase"
            self.state.active_side = "H"
            self.state.message = "迷宮が完成しました。人間の番です。10ターン以内に捕まえてください。"
            return

        self.state.active_side = "M" if self.state.active_side == "H" else "H"
        next_label = "人間" if self.state.active_side == "H" else "ネズミ"
        self.state.message = f"{actor_label} が壁を置きました。次は {next_label} の番です。"

    def _move_human(self, destination: Cell, piece: str) -> None:
        if piece not in {"H1", "H2"}:
            raise GameError("動かす人間を選んでください。")
        index = 0 if piece == "H1" else 1
        origin = self.state.humans[index]
        if not self._is_adjacent_and_open(origin, destination):
            raise GameError("そのマスへは動けません。")
        if destination in self.state.humans and destination != origin:
            raise GameError("もう一方の人間がいるマスには動けません。")

        self.state.humans[index] = destination
        self.state.chase_log.append(
            f"{self.state.chase_turn}ターン目: 人間が {piece} を {self.cell_label(origin)} から {self.cell_label(destination)} へ移動"
        )

        if destination == self.state.mouse:
            self._finish("H", "人間がネズミを捕まえました。")
            return
        if not self.mouse_has_any_two_step_route():
            self._finish("H", "ネズミを動けなくしました。人間の勝ちです。")
            return

        self.state.active_side = "M"
        self.state.mouse_steps_taken = 0
        self.state.message = "ネズミの番です。2マス動いてください。"

    def _move_mouse(self, destination: Cell) -> None:
        origin = self.state.mouse
        if destination in self.state.humans:
            raise GameError("人間がいるマスには入れません。")
        if not self._is_adjacent_and_open(origin, destination):
            raise GameError("そのマスへは動けません。")

        self.state.mouse = destination
        self.state.mouse_steps_taken += 1

        if self.state.mouse_steps_taken < 2:
            if not self.mouse_has_any_one_step_route():
                self._finish("H", "ネズミを動けなくしました。人間の勝ちです。")
                return
            self.state.message = "ネズミは続けて2歩目を動いてください。"
            return

        self.state.chase_log.append(
            f"{self.state.chase_turn}ターン目: ネズミが {self.cell_label(origin)} から {self.cell_label(destination)} まで2マス移動"
        )
        if self.state.chase_turn >= MAX_CHASE_TURNS:
            self._finish("M", "10ターン逃げ切りました。ネズミの勝ちです。")
            return

        self.state.chase_turn += 1
        self.state.active_side = "H"
        self.state.mouse_steps_taken = 0
        self.state.message = f"{self.state.chase_turn}ターン目。人間の番です。"

    def _resign(self, symbol: str) -> None:
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        winner = "M" if symbol == "H" else "H"
        loser_label = "人間" if symbol == "H" else "ネズミ"
        winner_label = "ネズミ" if winner == "M" else "人間"
        self._finish(winner, f"{loser_label} 側が降参しました。{winner_label} の勝ちです。")

    def mouse_has_any_one_step_route(self) -> bool:
        for neighbor in self._neighbors(self.state.mouse):
            if neighbor not in self.state.humans:
                return True
        return False

    def mouse_has_any_two_step_route(self) -> bool:
        for first in self._neighbors(self.state.mouse):
            if first in self.state.humans:
                continue
            for second in self._neighbors(first):
                if second in self.state.humans:
                    continue
                return True
        return False

    def _neighbors(self, cell: Cell) -> List[Cell]:
        r, c = cell
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and not self._blocked(cell, (nr, nc)):
                neighbors.append((nr, nc))
        return neighbors

    def _blocked(self, a: Cell, b: Cell) -> bool:
        if a[0] == b[0]:
            row = a[0]
            col = min(a[1], b[1])
            return f"v:{row}:{col}" in self.state.walls
        row = min(a[0], b[0])
        col = a[1]
        return f"h:{row}:{col}" in self.state.walls

    def _is_adjacent_and_open(self, origin: Cell, destination: Cell) -> bool:
        if not (0 <= destination[0] < BOARD_SIZE and 0 <= destination[1] < BOARD_SIZE):
            return False
        if abs(origin[0] - destination[0]) + abs(origin[1] - destination[1]) != 1:
            return False
        return not self._blocked(origin, destination)

    def all_edges(self) -> Set[str]:
        edges = set()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE - 1):
                edges.add(f"v:{row}:{col}")
        for row in range(BOARD_SIZE - 1):
            for col in range(BOARD_SIZE):
                edges.add(f"h:{row}:{col}")
        return edges

    def _creates_dead_end(self, walls: Set[str]) -> bool:
        target = {self._edge_to_legacy_id(edge_id) for edge_id in walls}
        patterns = [
            [IDS[0][0], IDS[1][0], IDH[1][0]],
            [IDH[0][0], IDH[0][1], IDS[0][1]],
            [IDS[0][0], IDH[0][0]],
            [IDS[4][3], IDS[3][3], IDH[2][4]],
            [IDH[3][4], IDH[3][3], IDS[4][2]],
            [IDS[4][3], IDH[3][4]],
        ]
        return any(all(item in target for item in pattern) for pattern in patterns)

    def _creates_four_chain(self, walls: Set[str]) -> bool:
        legacy_ids = {self._edge_to_legacy_id(edge_id) for edge_id in walls}
        adjacency: Dict[str, Set[str]] = {wall_id: set() for wall_id in legacy_ids}
        for wall_id in legacy_ids:
            for neighbor in self._legacy_neighbors(wall_id):
                if neighbor in legacy_ids:
                    adjacency[wall_id].add(neighbor)

        seen: Set[str] = set()
        for wall_id in legacy_ids:
            if wall_id in seen:
                continue
            stack = [wall_id]
            component_size = 0
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                component_size += 1
                stack.extend(adjacency[current] - seen)
            if component_size >= 4:
                return True
        return False

    def _edge_to_legacy_id(self, edge_id: str) -> str:
        kind, row_text, col_text = edge_id.split(":")
        row = int(row_text)
        col = int(col_text)
        if kind == "v":
            return IDS[row][col]
        return IDH[row][col]

    def _legacy_neighbors(self, wall_id: str) -> Set[str]:
        kind = wall_id[0]
        number = int(wall_id[1:])
        neighbors: Set[str] = set()
        if kind == "s":
            candidates = [
                f"s{number - 5}",
                f"h{number - 5}",
                f"h{number - 4}",
                f"s{number + 5}",
                f"h{number + 1}",
                f"h{number}",
            ]
        else:
            candidates = [
                f"h{number - 1}",
                f"s{number + 4}",
                f"s{number - 1}",
                f"h{number + 1}",
                f"s{number + 5}",
                f"s{number}",
            ]
        for candidate in candidates:
            if candidate in VALID_S_IDS or candidate in VALID_H_IDS:
                neighbors.add(candidate)
        return neighbors

    def _finish(self, winner: str, message: str) -> None:
        self.state.game_over = True
        self.state.winner = winner
        self.state.winner_text = message
        self.state.message = message

    @staticmethod
    def cell_label(cell: Cell) -> str:
        return f"({cell[0] + 1}, {cell[1] + 1})"

    def to_public_dict(self, viewer_symbol: Optional[str] = None) -> dict:
        return {
            "game_type": self.game_type,
            "title": self.title,
            "phase": self.state.phase,
            "started": True,
            "game_over": self.state.game_over,
            "winner_text": self.state.winner_text,
            "message": self.state.message,
            "active_side": self.state.active_side,
            "wall_count": len(self.state.walls),
            "max_walls": MAX_WALLS,
            "chase_turn": self.state.chase_turn,
            "max_chase_turns": MAX_CHASE_TURNS,
            "mouse_steps_taken": self.state.mouse_steps_taken,
            "humans": [list(cell) for cell in self.state.humans],
            "mouse": list(self.state.mouse),
            "walls": sorted(self.state.walls),
            "build_log": self.state.build_log[-10:],
            "chase_log": self.state.chase_log[-10:],
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
        }
