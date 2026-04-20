from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


Cell = Tuple[int, int]
TEAM_SYMBOLS = ("A", "B")
TEAM_NAMES = {"A": "青チーム", "B": "赤チーム"}
BOARD_SIZE = 50
VIEWPORT_SIZE = 15
ROUNDS_PER_SET = 10
MAX_SETS = 10
MIN_SPAWN_DISTANCE = 6


class GameError(ValueError):
    pass


@dataclass(frozen=True)
class SkillDef:
    name: str
    cost: int
    description: str


@dataclass(frozen=True)
class CharacterDef:
    key: str
    role: str
    name: str
    move: int
    power: int
    vision: int
    summary: str
    small: SkillDef
    medium: SkillDef
    large: SkillDef


CHARACTERS: Dict[str, CharacterDef] = {
    "speed_star": CharacterDef(
        "speed_star",
        "スピードスター",
        "スピードスター",
        0,
        10,
        3,
        "高速機動で一直線に戦場を切り裂く突撃役。",
        SkillDef("ダッシュ", 1, "10マスまで移動する。"),
        SkillDef("ブーストバスター", 3, "10マスまで移動し、重なった敵へ戦闘力/5ダメージ。"),
        SkillDef("ソニックスター", 4, "一直線に突進し、進路上と脇をなぎ払う。"),
    ),
    "spiritualist": CharacterDef(
        "spiritualist",
        "霊能力者",
        "ミャーノ・マーリー",
        3,
        4,
        5,
        "視界共有と拘束、追尾霊を扱う術者。",
        SkillDef("サウザンド・アイ", 2, "このセット中、味方の視界を共有する。"),
        SkillDef("ゴールド・バインド", 3, "指定した敵が次に動く時の行動を封じる。"),
        SkillDef("ハンドレッド・ナイト", 4, "追尾する霊を召喚する。"),
    ),
    "archer": CharacterDef(
        "archer",
        "弓兵",
        "アチャ爺",
        6,
        9,
        5,
        "補足した相手を射続ける超遠距離スナイパー。",
        SkillDef("通常射出", 2, "移動中に見えた敵を撃つ。"),
        SkillDef("中距離曲射", 3, "補足した敵を継続して狙い続ける。"),
        SkillDef("超遠距離攻撃", 5, "指定した直線上で最も近い相手を射抜く。"),
    ),
    "soldier": CharacterDef(
        "soldier",
        "雑兵",
        "レオ・アレクス",
        5,
        10,
        3,
        "移動しながら最初の一撃を叩き込む前衛。",
        SkillDef("剣技", 1, "移動中を含め、八方向1マスの最初の敵1体へ戦闘力/3ダメージ。"),
        SkillDef("弱者の祈り", 3, "視界内の味方全員を1回復する。"),
        SkillDef("主人公補正", 5, "窮地で一時的に大幅強化する。"),
    ),
    "leader": CharacterDef(
        "leader",
        "リーダー",
        "ヴァン・クラリッサ",
        7,
        15,
        4,
        "冷静に戦場を組み替える指揮官。",
        SkillDef("通常業務", 1, "新しく視界に入った敵へ戦闘力/5ダメージ。"),
        SkillDef("再構成", 3, "残りターンの担当順を再設定する。"),
        SkillDef("再配置", 5, "味方を現在の味方位置へ再配置する。"),
    ),
    "saint": CharacterDef(
        "saint",
        "聖女",
        "アリア",
        5,
        1000,
        1,
        "祈りと反射で盤面を支配する聖女。",
        SkillDef("リフレクト", 1, "次の自分の番まで完全反射する。"),
        SkillDef("聖女の祈り", 2, "負傷している味方1体をランダムに3回復する。"),
        SkillDef("見通す目", 3, "このセット中、アリアの手番中だけ全可視になる。"),
    ),
    "psychic": CharacterDef(
        "psychic",
        "サイキッカー",
        "白星 夢",
        4,
        5,
        5,
        "広域ダメージと瞬間移動を扱う超能力者。",
        SkillDef("フラッシュ", 1, "移動不可。半径5マスの相手へ3ダメージ、自分へ1ダメージ。"),
        SkillDef("テレポート", 2, "ランダムな場所へ移動する。"),
        SkillDef("ブラックホール", 4, "自分以外へ距離に応じて5/3/1ダメージ。"),
    ),
    "samurai": CharacterDef(
        "samurai",
        "侍",
        "櫻井 光二郎",
        7,
        10,
        4,
        "間合いだけで敵を斬る老剣士。",
        SkillDef("間合い", 1, "3マス圏の敵へ戦闘力/3ダメージ。"),
        SkillDef("空の間合い", 2, "次の自分の番まで視野に入った敵へ戦闘力/2ダメージ。"),
        SkillDef("極の間合い", 5, "次の自分の番まで近づくものを弾き斬る。"),
    ),
    "berserker": CharacterDef(
        "berserker",
        "バーサーカー",
        "ニック",
        2,
        100,
        2,
        "自傷強化で捕食圏を広げる怪物。",
        SkillDef("ホショク", 1, "捕食圏内の相手へ戦闘力ダメージ。"),
        SkillDef("シュンソク", 2, "戦闘力5消費で移動量を倍にする。"),
        SkillDef("バーサーク", 3, "戦闘力を半減し、捕食圏を1広げる。"),
    ),
    "beastmaster": CharacterDef(
        "beastmaster",
        "獣使い",
        "メイ・スフィン",
        5,
        5,
        3,
        "獣の力と索敵で場を制するレンジャー。",
        SkillDef("獅子ライド", 2, "10マスまで移動し、重なった敵へ4ダメージ。"),
        SkillDef("バードリスニング", 3, "その時点の敵位置をマップに記録する。"),
        SkillDef("ハムマッチ", 4, "ハムスターを召喚する。"),
    ),
}


FIELD_OPTIONS = (
    {"key": "grassland", "name": "草原", "summary": "視界を取りやすい標準マップ。"},
    {"key": "maze", "name": "迷宮", "summary": "壁が多く、索敵が重要になるマップ。"},
    {"key": "volcano", "name": "火山", "summary": "危険地帯が点在する変則マップ。"},
    {"key": "debug_lab", "name": "お試し部屋", "summary": "将来のデバッグ用フィールド。いまは準備中です。"},
)


@dataclass
class PlayerState:
    symbol: str
    name: str
    connected: bool = False
    selected_keys: List[str] = field(default_factory=list)
    order: List[str] = field(default_factory=list)
    roster_confirmed: bool = False
    order_confirmed: bool = False
    coins: int = 0

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "selected_keys": list(self.selected_keys),
            "order": list(self.order),
            "roster_confirmed": self.roster_confirmed,
            "order_confirmed": self.order_confirmed,
            "coins": self.coins,
        }


@dataclass
class UnitState:
    id: str
    team: str
    character_key: str
    role: str
    name: str
    move: int
    power: int
    vision: int
    cell: Cell
    spawn_cell: Cell
    hp: int
    cost: int = 0
    alive: bool = True

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "team": self.team,
            "character_key": self.character_key,
            "role": self.role,
            "name": self.name,
            "move": self.move,
            "power": self.power,
            "vision": self.vision,
            "cell": list(self.cell),
            "spawn_cell": list(self.spawn_cell),
            "hp": self.hp,
            "max_hp": self.power,
            "cost": self.cost,
            "alive": self.alive,
        }


@dataclass
class FlagState:
    id: str
    team: str
    cell: Cell
    alive: bool = True

    def to_public_dict(self) -> dict:
        return {"id": self.id, "team": self.team, "cell": list(self.cell), "alive": self.alive}


def within_bounds(cell: Cell) -> bool:
    x, y = cell
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE


def distance(a: Cell, b: Cell) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


class TheGrandGame:
    game_type = "the_grand"
    title = "The Grand"
    subtitle = "広域フィールド対戦プロトタイプ"
    category = "original"
    min_players = 2
    max_players = 2
    player_label = "2 players"
    seat_order = list(TEAM_SYMBOLS)
    host_control_actions = {"advance_phase", "confirm_field"}

    def __init__(self) -> None:
        self.players: Dict[str, PlayerState] = {
            symbol: PlayerState(symbol=symbol, name=f"Player {symbol}")
            for symbol in TEAM_SYMBOLS
        }
        self.phase = "waiting"
        self.started = False
        self.game_over = False
        self.message = "2人そろうまで待機中です。"
        self.winner_text = ""
        self.field_type = ""
        self.board_size = BOARD_SIZE
        self.viewport_size = VIEWPORT_SIZE
        self.set_number = 1
        self.round_number = 1
        self.units: Dict[str, UnitState] = {}
        self.flags: Dict[str, FlagState] = {}
        self.walls: Set[Cell] = set()
        self.coins: Set[Cell] = set()
        self.pending_actions: Dict[str, dict] = {}
        self.continue_confirmed: Set[str] = set()
        self.result_ready = False
        self.round_notices: List[str] = []

    @classmethod
    def catalog_entry(cls) -> dict:
        return {
            "game_type": cls.game_type,
            "title": cls.title,
            "subtitle": cls.subtitle,
            "category": cls.category,
            "status": "prototype",
            "min_players": cls.min_players,
            "max_players": cls.max_players,
            "player_label": cls.player_label,
        }

    def set_player_name(self, symbol: str, name: str) -> None:
        if symbol in self.players:
            cleaned = (name or f"Player {symbol}").strip()[:24]
            self.players[symbol].name = cleaned or f"Player {symbol}"

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected
        self.start_if_ready()

    def start_if_ready(self) -> None:
        if all(self.players[symbol].connected for symbol in TEAM_SYMBOLS):
            if self.phase == "waiting":
                self.message = "両プレイヤーが揃いました。部屋主はフィールド選択へ進めます。"
        elif self.phase == "waiting":
            self.message = "2人そろうまで待機中です。"

    def reset_for_rematch(self) -> None:
        saved = {symbol: (player.name, player.connected) for symbol, player in self.players.items()}
        self.__init__()
        for symbol, (name, connected) in saved.items():
            self.players[symbol].name = name
            self.players[symbol].connected = connected
        self.start_if_ready()

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        settings = settings or {}
        if action == "advance_phase":
            self._advance_phase()
            return
        if action == "confirm_field":
            self._confirm_field(settings)
            return
        raise GameError("未対応のホスト操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        settings: Optional[dict] = None,
        **_: object,
    ) -> None:
        settings = settings or {}
        if action == "update_setup":
            self._update_setup(symbol, settings)
            return
        if action == "confirm_roster":
            self._confirm_roster(symbol)
            return
        if action == "confirm_order":
            self._confirm_order(symbol, settings)
            return
        if action == "submit_turn":
            self._submit_turn(symbol, settings)
            return
        if action == "confirm_result":
            self._confirm_result(symbol)
            return
        raise GameError("未対応の操作です。")

    def _advance_phase(self) -> None:
        if self.phase != "waiting":
            raise GameError("この段階では進めません。")
        if not all(self.players[symbol].connected for symbol in TEAM_SYMBOLS):
            raise GameError("両プレイヤーが揃ってから始めてください。")
        self.phase = "field_select"
        self.message = "フィールドを選んでください。"

    def _confirm_field(self, settings: dict) -> None:
        if self.phase != "field_select":
            raise GameError("いまはフィールドを決める段階ではありません。")
        field_type = settings.get("field_type", "")
        if field_type not in {entry["key"] for entry in FIELD_OPTIONS}:
            raise GameError("未対応のフィールドです。")
        self.field_type = field_type
        if field_type == "debug_lab":
            self.phase = "battle"
            self.started = True
            self.message = "お試し部屋は準備中です。いったん簡易戦闘へ入ります。"
            self._setup_battle()
            return
        self.phase = "character_select"
        self.message = "キャラクターを選んで編成を確定してください。"

    def _clean_selected_keys(self, selected_keys: List[str]) -> List[str]:
        seen: Set[str] = set()
        cleaned: List[str] = []
        for key in selected_keys:
            if key in CHARACTERS and key not in seen:
                seen.add(key)
                cleaned.append(key)
        return cleaned[:10]

    def _update_setup(self, symbol: str, settings: dict) -> None:
        player = self.players[symbol]
        if self.phase == "character_select":
            selected_keys = self._clean_selected_keys(settings.get("selected_keys", []))
            player.selected_keys = selected_keys
            player.roster_confirmed = False
            player.order_confirmed = False
            if player.selected_keys:
                player.order = list(player.selected_keys)
            return
        if self.phase == "order_select":
            priority = [key for key in settings.get("priority", []) if key in player.selected_keys]
            if sorted(priority) != sorted(player.selected_keys):
                raise GameError("行動順には選んだキャラを1回ずつ入れてください。")
            player.order = priority
            player.order_confirmed = False
            return
        raise GameError("この段階では編成変更できません。")

    def _confirm_roster(self, symbol: str) -> None:
        if self.phase != "character_select":
            raise GameError("いまは編成確定の段階ではありません。")
        player = self.players[symbol]
        if not player.selected_keys:
            raise GameError("少なくとも1体選んでください。")
        player.roster_confirmed = True
        player.order = list(player.selected_keys)
        self.message = "両チームの編成確定を待っています。"
        if all(self.players[s].roster_confirmed for s in TEAM_SYMBOLS):
            self.phase = "order_select"
            for current in self.players.values():
                current.order_confirmed = False
            self.message = "このセットの行動順を決めてください。"

    def _confirm_order(self, symbol: str, settings: dict) -> None:
        if self.phase != "order_select":
            raise GameError("いまは行動順確定の段階ではありません。")
        player = self.players[symbol]
        priority = [key for key in settings.get("priority", []) if key in player.selected_keys]
        if sorted(priority) != sorted(player.selected_keys):
            raise GameError("行動順には選んだキャラを1回ずつ入れてください。")
        player.order = priority
        player.order_confirmed = True
        if all(self.players[s].order_confirmed for s in TEAM_SYMBOLS):
            self._setup_battle()
            self.phase = "battle"
            self.started = True
            self.message = "戦闘開始です。移動を決定してください。"

    def _setup_battle(self) -> None:
        self.units.clear()
        self.flags.clear()
        self.walls = self._build_walls(self.field_type or "grassland")
        self.coins = set()
        self.pending_actions.clear()
        self.continue_confirmed.clear()
        self.result_ready = False
        self.round_notices = []
        used_cells: Set[Cell] = set()
        for symbol in TEAM_SYMBOLS:
            for index, key in enumerate(self.players[symbol].selected_keys):
                character = CHARACTERS[key]
                cell = self._roll_spawn(used_cells)
                used_cells.add(cell)
                unit_id = f"{symbol}-{index + 1}"
                self.units[unit_id] = UnitState(
                    id=unit_id,
                    team=symbol,
                    character_key=key,
                    role=character.role,
                    name=character.name,
                    move=character.move,
                    power=character.power,
                    vision=character.vision,
                    cell=cell,
                    spawn_cell=cell,
                    hp=character.power,
                )
                self.flags[f"{unit_id}-flag"] = FlagState(id=f"{unit_id}-flag", team=symbol, cell=cell)

    def _build_walls(self, field_type: str) -> Set[Cell]:
        walls: Set[Cell] = set()
        if field_type == "maze":
            for x in range(2, BOARD_SIZE - 2, 4):
                for y in range(1, BOARD_SIZE - 1):
                    if y % 5 != 0:
                        walls.add((x, y))
        elif field_type == "volcano":
            for x in range(0, BOARD_SIZE, 7):
                for y in range(0, BOARD_SIZE, 7):
                    if 0 < x < BOARD_SIZE - 1 and 0 < y < BOARD_SIZE - 1:
                        walls.add((x, y))
        return walls

    def _roll_spawn(self, used_cells: Set[Cell]) -> Cell:
        while True:
            cell = (random.randrange(BOARD_SIZE), random.randrange(BOARD_SIZE))
            if cell in self.walls or cell in used_cells:
                continue
            if all(distance(cell, other) >= MIN_SPAWN_DISTANCE for other in used_cells):
                return cell

    def _current_actor_id(self, team: str) -> str:
        player = self.players[team]
        if not player.order:
            return ""
        key = player.order[(self.round_number - 1) % len(player.order)]
        for unit in self.units.values():
            if unit.team == team and unit.character_key == key and unit.alive:
                return unit.id
        for unit in self.units.values():
            if unit.team == team and unit.alive:
                return unit.id
        return ""

    def _submit_turn(self, symbol: str, settings: dict) -> None:
        if self.phase != "battle":
            raise GameError("いまは戦闘中ではありません。")
        if self.result_ready:
            raise GameError("まず結果を確認してください。")
        actor_id = self._current_actor_id(symbol)
        if not actor_id:
            raise GameError("行動できるキャラがいません。")
        path = settings.get("path", []) or []
        actor = self.units.get(actor_id)
        if actor is None or not actor.alive:
            raise GameError("行動キャラが見つかりません。")
        max_steps = actor.move
        if len(path) > max_steps:
            raise GameError("行動力を超える移動はできません。")
        current = actor.cell
        clean_path: List[Cell] = []
        for raw in path:
            if not isinstance(raw, (list, tuple)) or len(raw) != 2:
                raise GameError("移動先の形式が正しくありません。")
            cell = (int(raw[0]), int(raw[1]))
            if not within_bounds(cell):
                raise GameError("移動先が盤外です。")
            if abs(cell[0] - current[0]) + abs(cell[1] - current[1]) != 1:
                raise GameError("移動は十字1マスずつ指定してください。")
            if cell in self.walls:
                raise GameError("壁には進めません。")
            clean_path.append(cell)
            current = cell
        self.pending_actions[symbol] = {"actor_id": actor_id, "path": clean_path}
        self.message = "相手の行動決定を待っています。"
        if len(self.pending_actions) == 2:
            self._resolve_round()

    def _resolve_round(self) -> None:
        self.round_notices = []
        for team in TEAM_SYMBOLS:
            payload = self.pending_actions.get(team, {})
            actor = self.units.get(payload.get("actor_id", ""))
            if actor is None or not actor.alive:
                continue
            for cell in payload.get("path", []):
                if cell in self.walls:
                    break
                actor.cell = cell
                actor.cost += 1
        self.pending_actions.clear()
        self.result_ready = True
        self.continue_confirmed.clear()
        self.message = "行動結果を確認して次へ進んでください。"

    def _confirm_result(self, symbol: str) -> None:
        if not self.result_ready:
            raise GameError("いまは確認する結果がありません。")
        self.continue_confirmed.add(symbol)
        if len(self.continue_confirmed) < 2:
            self.message = "相手が結果確認を終えるのを待っています。"
            return
        self.result_ready = False
        self.continue_confirmed.clear()
        if self.round_number >= ROUNDS_PER_SET:
            self.round_number = 1
            self.set_number += 1
            if self.set_number > MAX_SETS:
                self.game_over = True
                self.winner_text = "仮実装のため勝敗計算は次の段階で入れます。"
                self.message = "全セット終了です。"
                return
            self.phase = "order_select"
            for player in self.players.values():
                player.order_confirmed = False
            self.message = f"{self.set_number}セット目が始まります。行動順を決めてください。"
            return
        self.round_number += 1
        self.message = "次の行動を決定してください。"

    def _visible_cells_for(self, actor_id: str) -> Set[Cell]:
        actor = self.units.get(actor_id)
        if actor is None or not actor.alive:
            return set()
        result: Set[Cell] = set()
        radius = actor.vision
        ax, ay = actor.cell
        for y in range(ay - radius, ay + radius + 1):
            for x in range(ax - radius, ax + radius + 1):
                cell = (x, y)
                if within_bounds(cell) and distance(actor.cell, cell) <= radius + 0.01:
                    result.add(cell)
        return result

    def _viewport_for(self, actor_id: str) -> dict:
        actor = self.units.get(actor_id)
        if actor is None or not actor.alive:
            return {"origin": [0, 0], "cells": [], "visible_cells": []}
        half = VIEWPORT_SIZE // 2
        start_x = max(0, min(BOARD_SIZE - VIEWPORT_SIZE, actor.cell[0] - half))
        start_y = max(0, min(BOARD_SIZE - VIEWPORT_SIZE, actor.cell[1] - half))
        cells: List[List[int]] = []
        for y in range(start_y, start_y + VIEWPORT_SIZE):
            for x in range(start_x, start_x + VIEWPORT_SIZE):
                cells.append([x, y])
        visible = [[cell[0], cell[1]] for cell in self._visible_cells_for(actor_id)]
        return {"origin": [start_x, start_y], "cells": cells, "visible_cells": visible}

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        actor_id = self._current_actor_id(viewer_symbol) if viewer_symbol in TEAM_SYMBOLS else ""
        viewer_waiting = bool(viewer_symbol in self.pending_actions) and not self.result_ready
        visible_cells = self._visible_cells_for(actor_id) if actor_id else set()
        known_floor = {cell for cell in visible_cells if cell not in self.walls}
        known_walls = {cell for cell in visible_cells if cell in self.walls}
        visible_units: Dict[str, dict] = {}
        for unit_id, unit in self.units.items():
            if not unit.alive:
                continue
            if viewer_symbol in TEAM_SYMBOLS and unit.team != viewer_symbol and unit.cell not in visible_cells:
                continue
            visible_units[unit_id] = unit.to_public_dict()
        return {
            "game_type": self.game_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "phase": self.phase,
            "started": self.started,
            "game_over": self.game_over,
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
            "field_type": self.field_type,
            "field_options": list(FIELD_OPTIONS),
            "catalog": [
                {
                    "key": entry.key,
                    "role": entry.role,
                    "name": entry.name,
                    "move": entry.move,
                    "power": entry.power,
                    "vision": entry.vision,
                    "summary": entry.summary,
                    "small": entry.small.__dict__,
                    "medium": entry.medium.__dict__,
                    "large": entry.large.__dict__,
                }
                for entry in CHARACTERS.values()
            ],
            "set_number": self.set_number,
            "round_number": self.round_number,
            "board_size": self.board_size,
            "viewport_size": self.viewport_size,
            "viewer_symbol": viewer_symbol,
            "viewer_actor_id": actor_id,
            "viewer_waiting": viewer_waiting,
            "viewer_continue_confirmed": viewer_symbol in self.continue_confirmed,
            "result_ready": self.result_ready,
            "round_notices": list(self.round_notices),
            "units": visible_units,
            "flags": {flag_id: flag.to_public_dict() for flag_id, flag in self.flags.items()},
            "walls": [list(cell) for cell in sorted(known_walls)],
            "coins": [list(cell) for cell in sorted(self.coins)],
            "visible_cells": [list(cell) for cell in sorted(visible_cells)],
            "known_floor": [list(cell) for cell in sorted(known_floor)],
            "known_walls": [list(cell) for cell in sorted(known_walls)],
            "viewport": self._viewport_for(actor_id) if actor_id else {"origin": [0, 0], "cells": [], "visible_cells": []},
        }
