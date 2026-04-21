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
    key: str = ""


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
    memo: str = ""


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
    owner: str = ""
    display_name: str = ""
    max_hp: int = 0
    base_move: int = 0
    base_power: int = 0
    base_vision: int = 0
    is_summon: bool = False
    true_sight: bool = False
    reflect_ratio: float = 0.0
    vision_bonus: int = 0
    move_bonus: int = 0

    def __post_init__(self) -> None:
        if not self.owner:
            self.owner = self.team
        if not self.display_name:
            self.display_name = self.name
        if not self.max_hp:
            self.max_hp = self.power
        if not self.base_move:
            self.base_move = self.move
        if not self.base_power:
            self.base_power = self.power
        if not self.base_vision:
            self.base_vision = self.vision

    @property
    def effective_move(self) -> int:
        return max(0, self.base_move + self.move_bonus)

    @property
    def effective_vision(self) -> int:
        return max(1, self.base_vision + self.vision_bonus)

    def to_public_dict(self) -> dict:
        character = CHARACTERS.get(self.character_key)
        return {
            "id": self.id,
            "team": self.team,
            "owner": self.owner,
            "character_key": self.character_key,
            "role": self.role,
            "name": self.name,
            "display_name": self.display_name,
            "move": self.effective_move,
            "power": self.base_power,
            "vision": self.effective_vision,
            "cell": list(self.cell),
            "spawn_cell": list(self.spawn_cell),
            "hp": self.hp,
            "max_hp": self.max_hp,
            "cost": self.cost,
            "alive": self.alive,
            "is_summon": self.is_summon,
            "small": character.small.__dict__ if character else None,
            "medium": character.medium.__dict__ if character else None,
            "large": character.large.__dict__ if character else None,
        }


PlayerSlot = PlayerState


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
        self.known_floor_by_team: Dict[str, Set[Cell]] = {symbol: set() for symbol in TEAM_SYMBOLS}
        self.known_walls_by_team: Dict[str, Set[Cell]] = {symbol: set() for symbol in TEAM_SYMBOLS}
        self.known_coins_by_team: Dict[str, Set[Cell]] = {symbol: set() for symbol in TEAM_SYMBOLS}
        self.pending_actions: Dict[str, dict] = {}
        self.continue_confirmed: Set[str] = set()
        self.result_ready = False
        self.round_notices: List[str] = []
        self.shared_vision_teams: Set[str] = set()
        self.true_sight_units: Set[str] = set()
        self.reflect_units: Dict[str, float] = {}
        self.bound_targets: Set[str] = set()
        self.archer_marks: Dict[str, dict] = {}
        self.samurai_sky_units: Set[str] = set()
        self.samurai_guard_units: Set[str] = set()
        self.berserk_radius: Dict[str, int] = {}
        self.bird_snapshots: Dict[str, dict] = {}
        self.turn_plan: Dict[str, List[str]] = {symbol: [] for symbol in TEAM_SYMBOLS}

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
            for team in TEAM_SYMBOLS:
                self.turn_plan[team] = self._build_turn_plan(self.players[team].order)
            if not self.units:
                self._setup_battle()
            self.pending_actions.clear()
            self.continue_confirmed.clear()
            self.result_ready = False
            self.round_notices = []
            self.phase = "battle"
            self.started = True
            self.message = "戦闘開始です。移動を決定してください。"

    def _build_turn_plan(self, order: List[str]) -> List[str]:
        if not order:
            return []
        return [order[index % len(order)] for index in range(ROUNDS_PER_SET)]

    def _setup_battle(self) -> None:
        self.units.clear()
        self.flags.clear()
        self.walls = self._build_walls(self.field_type or "grassland")
        self.coins = set()
        self.pending_actions.clear()
        self.continue_confirmed.clear()
        self.result_ready = False
        self.round_notices = []
        self.shared_vision_teams.clear()
        self.true_sight_units.clear()
        self.reflect_units.clear()
        self.bound_targets.clear()
        self.archer_marks.clear()
        self.samurai_sky_units.clear()
        self.samurai_guard_units.clear()
        self.berserk_radius.clear()
        self.bird_snapshots.clear()
        self.known_floor_by_team = {symbol: set() for symbol in TEAM_SYMBOLS}
        self.known_walls_by_team = {symbol: set() for symbol in TEAM_SYMBOLS}
        self.known_coins_by_team = {symbol: set() for symbol in TEAM_SYMBOLS}
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
                    max_hp=character.power,
                    owner=symbol,
                    display_name=character.name,
                    base_move=character.move,
                    base_power=character.power,
                    base_vision=character.vision,
                )
                self.flags[f"{unit_id}-flag"] = FlagState(id=f"{unit_id}-flag", team=symbol, cell=cell)
        self._respawn_coins()
        for team in TEAM_SYMBOLS:
            self._refresh_known_map(team)

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

    def _respawn_coins(self) -> None:
        self.coins.clear()
        target = max(2, sum(len(player.selected_keys) for player in self.players.values()))
        blocked = {unit.cell for unit in self.units.values() if unit.alive} | {flag.cell for flag in self.flags.values() if flag.alive} | self.walls
        while len(self.coins) < target:
            cell = (random.randrange(self.board_size), random.randrange(self.board_size))
            if cell in blocked or cell in self.coins:
                continue
            self.coins.add(cell)

    def _refresh_known_map(self, team: str) -> None:
        visible = self._visible_cells_for_team(team)
        self.known_floor_by_team[team].update(cell for cell in visible if cell not in self.walls)
        self.known_walls_by_team[team].update(cell for cell in visible if cell in self.walls)
        self.known_coins_by_team[team].difference_update({cell for cell in self.known_coins_by_team[team] if cell not in self.coins})
        self.known_coins_by_team[team].update(cell for cell in visible if cell in self.coins)

    def _visible_cells_for_team(self, team: str) -> Set[Cell]:
        visible: Set[Cell] = set()
        for unit in self.units.values():
            if unit.alive and unit.owner == team:
                visible.update(self._visible_cells_for(unit.id))
        return visible

    def _living_team_units(self, owner: str) -> List[UnitState]:
        return [unit for unit in self.units.values() if unit.alive and unit.owner == owner]

    def _living_units(self) -> List[UnitState]:
        return [unit for unit in self.units.values() if unit.alive]

    def _units_at_cell(self, cell: Cell, source: Optional[UnitState] = None) -> List[UnitState]:
        return [
            unit
            for unit in self._living_units()
            if unit.cell == cell and (source is None or unit.id != source.id)
        ]

    def _units_in_chebyshev(self, center: Cell, radius: int, source: Optional[UnitState] = None) -> List[UnitState]:
        if radius < 0:
            return []
        return [
            unit
            for unit in self._living_units()
            if (source is None or unit.id != source.id)
            and max(abs(unit.cell[0] - center[0]), abs(unit.cell[1] - center[1])) <= radius
        ]

    def _units_in_radius(
        self, center: Cell, radius: int, source: Optional[UnitState] = None, include_self: bool = False
    ) -> List[UnitState]:
        return [
            unit
            for unit in self._living_units()
            if (include_self or source is None or unit.id != source.id)
            and distance(unit.cell, center) <= radius + 0.01
        ]

    def _damageable_units(self, source: Optional[UnitState] = None, include_self: bool = False) -> List[UnitState]:
        return [
            unit
            for unit in self._living_units()
            if (include_self or source is None or unit.id != source.id)
        ]

    def _direction_delta(self, direction: str) -> Cell:
        mapping = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        return mapping.get(direction, (0, 0))

    def _build_straight_path(self, origin: Cell, direction: str, distance_count: int) -> List[Cell]:
        dx, dy = self._direction_delta(direction)
        if dx == 0 and dy == 0:
            return []
        path: List[Cell] = []
        current = origin
        for _ in range(max(0, distance_count)):
            next_cell = (current[0] + dx, current[1] + dy)
            if not within_bounds(next_cell) or next_cell in self.walls:
                break
            path.append(next_cell)
            current = next_cell
        return path

    def _build_line_to_target(self, origin: Cell, target: Cell) -> List[Cell]:
        ox, oy = origin
        tx, ty = target
        dx = tx - ox
        dy = ty - oy
        if dx == 0 and dy == 0:
            return []
        gcd = math.gcd(abs(dx), abs(dy))
        if gcd == 0:
            return []
        step_x = dx // gcd
        step_y = dy // gcd
        line: List[Cell] = []
        current = origin
        while True:
            next_cell = (current[0] + step_x, current[1] + step_y)
            if not within_bounds(next_cell):
                break
            line.append(next_cell)
            current = next_cell
        return line

    def _normalize_move_plan(self, actor: UnitState, raw_path: List[object], limit: int) -> List[Cell]:
        if len(raw_path) > limit:
            raise GameError("移動上限を超えています。")
        current = actor.cell
        clean_path: List[Cell] = []
        for raw in raw_path:
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
        return clean_path

    def _reflect_ratio_for(self, unit: UnitState) -> float:
        return self.reflect_units.get(unit.id, unit.reflect_ratio)

    def _collect_coins(self, unit: UnitState) -> None:
        if unit.cell in self.coins:
            self.coins.discard(unit.cell)
            self.players[unit.owner].coins += 1
            self.round_notices.append(f"{unit.display_name} がコインを獲得しました。")

    def _coin_steal_on_kill(self, attacker: UnitState, target: UnitState) -> None:
        victim_team = target.owner
        attacker_team = attacker.owner
        victim_living = max(1, len(self._living_team_units(victim_team)))
        amount = math.ceil(self.players[victim_team].coins / victim_living) if self.players[victim_team].coins > 0 else 0
        if amount <= 0:
            return
        self.players[victim_team].coins = max(0, self.players[victim_team].coins - amount)
        self.players[attacker_team].coins += amount
        self.round_notices.append(f"{attacker.display_name} が {amount} コインを奪いました。")

    def _deal_damage(self, target: UnitState, amount: int, label: str, attacker: Optional[UnitState] = None) -> None:
        if amount <= 0 or not target.alive:
            return
        if target.id in self.samurai_guard_units and label not in {"ハンドレッド・ナイト", "ブラックホール"}:
            self.round_notices.append(f"{label}: {target.display_name} の極の間合いに弾かれました。")
            if attacker and attacker.alive and max(abs(attacker.cell[0] - target.cell[0]), abs(attacker.cell[1] - target.cell[1])) <= 1:
                attacker.hp = 0
                attacker.alive = False
                self.round_notices.append(f"極の間合い: {attacker.display_name} は迎撃で倒されました。")
            return
        reflect_ratio = self._reflect_ratio_for(target)
        if reflect_ratio >= 1.0 and attacker and attacker.alive and attacker.id != target.id:
            attacker.hp = max(0, attacker.hp - amount)
            self.round_notices.append(f"{label}: {target.display_name} が反射し、{attacker.display_name} に {amount} ダメージ。")
            if attacker.hp <= 0:
                attacker.alive = False
                self.round_notices.append(f"{attacker.display_name} は倒れました。")
                self._coin_steal_on_kill(target, attacker)
            return
        target.hp = max(0, target.hp - amount)
        self.round_notices.append(f"{label}: {target.display_name} に {amount} ダメージ。")
        if reflect_ratio > 0 and attacker and attacker.alive and attacker.id != target.id:
            reflected = max(1, int(math.ceil(amount * reflect_ratio)))
            attacker.hp = max(0, attacker.hp - reflected)
            self.round_notices.append(f"リフレクト: {attacker.display_name} に {reflected} ダメージが返りました。")
            if attacker.hp <= 0:
                attacker.alive = False
                self.round_notices.append(f"{attacker.display_name} は倒れました。")
                self._coin_steal_on_kill(target, attacker)
        if target.hp <= 0:
            target.alive = False
            self.round_notices.append(f"{target.display_name} は倒れました。")
            if attacker and attacker.alive and attacker.owner != target.owner:
                self._coin_steal_on_kill(attacker, target)

    def _all_board_cells(self) -> Set[Cell]:
        return {(x, y) for y in range(self.board_size) for x in range(self.board_size)}

    def _is_current_actor(self, unit: UnitState) -> bool:
        return self._current_actor_id(unit.owner) == unit.id

    def _has_true_sight(self, unit: UnitState) -> bool:
        return unit.id in self.true_sight_units and self._is_current_actor(unit)

    def _visible_cells_for_actor(self, actor: UnitState) -> Set[Cell]:
        if not actor.alive:
            return set()
        if self._has_true_sight(actor):
            return self._all_board_cells()
        result: Set[Cell] = set()
        radius = actor.effective_vision
        ax, ay = actor.cell
        for y in range(ay - radius, ay + radius + 1):
            for x in range(ax - radius, ax + radius + 1):
                cell = (x, y)
                if within_bounds(cell) and distance(actor.cell, cell) <= radius + 0.01:
                    result.add(cell)
        return result

    def _visible_cells_for_team(self, team: str) -> Set[Cell]:
        owner_units = self._living_team_units(team)
        if not owner_units:
            return set()
        if team in self.shared_vision_teams:
            visible: Set[Cell] = set()
            for unit in owner_units:
                visible.update(self._visible_cells_for_actor(unit))
            return visible
        actor_id = self._current_actor_id(team)
        actor = self.units.get(actor_id)
        return self._visible_cells_for_actor(actor) if actor else set()

    def _visible_targets_for_actor(self, actor: UnitState, enemy_only: bool = False) -> List[UnitState]:
        visible = self._visible_cells_for_team(actor.owner)
        targets = []
        for unit in self._living_units():
            if unit.id == actor.id:
                continue
            if enemy_only and unit.owner == actor.owner:
                continue
            if unit.cell in visible:
                targets.append(unit)
        return targets

    def _damage_flag_at(self, attacker: UnitState, cell: Cell, label: str) -> None:
        for flag in self.flags.values():
            if flag.alive and flag.team != attacker.owner and flag.cell == cell:
                flag.alive = False
                self.round_notices.append(f"{label}: {TEAM_NAMES[flag.team]} の旗が破壊されました。")

    def _capture_flags_on_overlap(self, attacker: UnitState) -> None:
        for flag in self.flags.values():
            if flag.alive and flag.team != attacker.owner and flag.cell == attacker.cell:
                self.round_notices.append(f"{attacker.display_name} が敵旗の位置に到達しました。")

    def _step_toward(self, origin: Cell, target: Cell) -> Cell:
        ox, oy = origin
        tx, ty = target
        candidates: List[Cell] = []
        if ox < tx:
            candidates.append((ox + 1, oy))
        elif ox > tx:
            candidates.append((ox - 1, oy))
        if oy < ty:
            candidates.append((ox, oy + 1))
        elif oy > ty:
            candidates.append((ox, oy - 1))
        valid = [cell for cell in candidates if within_bounds(cell) and cell not in self.walls]
        if not valid:
            return origin
        return min(valid, key=lambda cell: abs(cell[0] - tx) + abs(cell[1] - ty))

    def _apply_speed_star_large_side_damage(self, actor: UnitState, previous: Cell) -> None:
        dx = actor.cell[0] - previous[0]
        dy = actor.cell[1] - previous[1]
        if dx == 0 and dy == 0:
            return
        side_vectors = [(0, 1), (0, -1)] if dx else [(1, 0), (-1, 0)]
        for sx, sy in side_vectors:
            for distance_count in (1, 2):
                side_cell = (actor.cell[0] + sx * distance_count, actor.cell[1] + sy * distance_count)
                if not within_bounds(side_cell):
                    continue
                self._damage_flag_at(actor, side_cell, "ソニックスター")
                for target in self._units_at_cell(side_cell, source=actor):
                    self._deal_damage(target, max(1, actor.base_power // 2), "ソニックスター横ダメージ", attacker=actor)

    def _advance_summons(self) -> None:
        summons = [unit for unit in self.units.values() if unit.alive and unit.is_summon and unit.character_key == "hundred_night"]
        for ghost in summons:
            targets = [unit for unit in self._living_units() if unit.owner != ghost.owner and unit.alive]
            if not targets:
                continue
            target = min(targets, key=lambda unit: abs(unit.cell[0] - ghost.cell[0]) + abs(unit.cell[1] - ghost.cell[1]))
            for _ in range(2):
                next_cell = self._step_toward(ghost.cell, target.cell)
                if next_cell == ghost.cell:
                    break
                ghost.cell = next_cell
                self._damage_flag_at(ghost, ghost.cell, "ハンドレッド・ナイト")
                occupants = [unit for unit in self._units_at_cell(ghost.cell, source=ghost) if unit.character_key != "hundred_night"]
                for occupant in occupants:
                    self._deal_damage(occupant, 100, "ハンドレッド・ナイト", attacker=ghost)

    def _expire_actor_states(self, actor: UnitState) -> None:
        self.reflect_units.pop(actor.id, None)
        self.samurai_sky_units.discard(actor.id)
        self.samurai_guard_units.discard(actor.id)
        if actor.id in self.archer_marks:
            self.archer_marks.pop(actor.id, None)

    def _process_start_of_turn_states(self, actor: UnitState) -> None:
        if actor.character_key == "archer":
            mark = self.archer_marks.get(actor.id)
            if mark:
                target_ids = set(mark.get("targets", []))
                for target in self._living_units():
                    if target.id in target_ids and distance(actor.cell, target.cell) <= int(mark.get("range", 10)) + 0.01:
                        self._deal_damage(target, 2, "中距離曲射追撃", attacker=actor)
        if actor.id in self.bound_targets:
            self.bound_targets.pop(actor.id, None)
            raise GameError("ゴールド・バインドにより今回の行動は封じられました。")

    def _apply_skill(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        character = CHARACTERS[actor.character_key]
        skill = getattr(character, tier)
        if actor.cost < skill.cost:
            raise GameError(f"{skill.name} を使うにはコスト {skill.cost} が必要です。")
        actor.cost -= skill.cost

        handler = getattr(self, f"_skill_{actor.character_key}", None)
        if handler is None:
            self.round_notices.append(f"{skill.name}: まだ本編未実装です。")
            return False
        return bool(handler(actor, tier, path, settings))

    def _skill_speed_star(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.round_notices.append("ダッシュ: 10マス移動として扱います。")
            return True
        if tier == "medium":
            self.round_notices.append("ブーストバスター: 10マス移動し、重なった敵へ戦闘力/5ダメージ。")
            return True
        self.round_notices.append("ソニックスター: 指定方向へ直線突進し、直線上と脇を攻撃します。")
        return True

    def _skill_spiritualist(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.shared_vision_teams.add(actor.owner)
            self.round_notices.append("サウザンド・アイ: このセット中、味方の視界を共有します。")
            return True
        if tier == "medium":
            target_id = str(settings.get("skill_target_unit_id") or "")
            target = self.units.get(target_id)
            if not target or not target.alive or target.owner == actor.owner:
                raise GameError("ゴールド・バインドの対象となる敵を選んでください。")
            self.bound_targets[target.id] = actor.id
            self.round_notices.append(f"ゴールド・バインド: {target.display_name} の次回行動を封じました。")
            return True
        summon_id = f"{actor.id}-hundred-night"
        self.units[summon_id] = UnitState(
            id=summon_id,
            team=actor.team,
            owner=actor.owner,
            character_key="hundred_night",
            role="追尾霊",
            name="ハンドレッド・ナイト",
            display_name="ハンドレッド・ナイト",
            move=2,
            power=100,
            vision=99,
            cell=actor.cell,
            spawn_cell=actor.cell,
            hp=9999,
            max_hp=9999,
            base_move=2,
            base_power=100,
            base_vision=99,
            is_summon=True,
        )
        self.round_notices.append("ハンドレッド・ナイト: 追尾霊を召喚しました。")
        return True

    def _skill_archer(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.round_notices.append("通常射出: 見えている敵へ移動ごとに 1 ダメージを狙います。")
            return True
        if tier == "medium":
            targets = [unit.id for unit in self._visible_targets_for_actor(actor, enemy_only=True)]
            self.archer_marks[actor.id] = {"targets": targets, "range": 10}
            self.round_notices.append("中距離曲射: 捕捉した敵を次の自分の番まで追跡します。")
            return True
        target_cell = settings.get("skill_target_cell")
        if not isinstance(target_cell, list) or len(target_cell) != 2:
            raise GameError("超遠距離攻撃の狙点を選んでください。")
        line = self._build_line_to_target(actor.cell, (int(target_cell[0]), int(target_cell[1])))
        units_on_line = [unit for unit in self._living_units() if unit.id != actor.id and unit.cell in line]
        if units_on_line:
            target = min(units_on_line, key=lambda unit: abs(unit.cell[0] - actor.cell[0]) + abs(unit.cell[1] - actor.cell[1]))
            self._deal_damage(target, target.hp, "超遠距離攻撃", attacker=actor)
        else:
            self.round_notices.append("超遠距離攻撃: 指定した直線上に対象がいません。")
        return True

    def _skill_soldier(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.round_notices.append("剣技: 移動中を含め、最初の 1 体だけ斬ります。")
            return True
        if tier == "medium":
            visible = self._visible_cells_for_team(actor.owner)
            healed = 0
            for unit in self._living_team_units(actor.owner):
                if unit.id == actor.id:
                    continue
                if unit.cell in visible and unit.hp < unit.max_hp:
                    unit.hp = min(unit.max_hp, unit.hp + 1)
                    healed += 1
            self.round_notices.append(f"弱者の祈り: 視界内の味方 {healed} 体を 1 回復しました。")
            return True
        if actor.hp <= 5:
            actor.hp = 30
            actor.max_hp = max(actor.max_hp, 30)
            actor.base_move = 15
            actor.move = 15
            self.round_notices.append("主人公補正: 現在戦闘力 30 / 行動力 15 になりました。")
        else:
            self.round_notices.append("主人公補正: 現在戦闘力 5 以下でないため不発です。")
        return True

    def _skill_leader(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.round_notices.append("通常業務: この行動中、新しく見えた敵だけを撃ちます。")
            return True
        if tier == "medium":
            draft = settings.get("leader_reconfigure") or {}
            if isinstance(draft, dict):
                self.round_notices.append("再構成: 残りターンの行動順を変更しました。")
            return True
        mapping = settings.get("leader_redeploy") or {}
        allies = self._living_team_units(actor.owner)
        snapshot = {unit.id: unit.cell for unit in allies}
        if isinstance(mapping, dict):
            for unit in allies:
                target_id = str(mapping.get(unit.id) or "")
                if target_id in snapshot:
                    unit.cell = snapshot[target_id]
        self.round_notices.append("再配置: 味方の位置を再配置しました。")
        return True

    def _skill_saint(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.reflect_units[actor.id] = 1.0
            self.round_notices.append("リフレクト: 次の自分の番まで完全反射します。")
            return True
        if tier == "medium":
            wounded = [unit for unit in self._living_team_units(actor.owner) if unit.hp < unit.max_hp]
            if not wounded:
                self.round_notices.append("聖女の祈り: 回復対象がいません。")
                return True
            target = random.choice(wounded)
            healed = min(3, target.max_hp - target.hp)
            target.hp = min(target.max_hp, target.hp + 3)
            self.round_notices.append(f"聖女の祈り: {target.display_name} を {healed} 回復しました。")
            return True
        self.true_sight_units.add(actor.id)
        self.round_notices.append("見通す目: このセット中、アリアの手番中だけ全可視です。")
        return True

    def _skill_psychic(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            for unit in self._living_units():
                if unit.id == actor.id:
                    continue
                if distance(actor.cell, unit.cell) <= 5 + 0.01:
                    self._deal_damage(unit, 3, "フラッシュ", attacker=actor)
            self._deal_damage(actor, 1, "フラッシュ反動", attacker=None)
            return True
        if tier == "medium":
            while True:
                cell = (random.randrange(self.board_size), random.randrange(self.board_size))
                if cell not in self.walls:
                    actor.cell = cell
                    break
            self.round_notices.append(f"テレポート: {actor.display_name} が転移しました。")
            return True
        for unit in self._living_units():
            if unit.id == actor.id:
                continue
            distance_value = distance(actor.cell, unit.cell)
            amount = 5 if distance_value <= 10 + 0.01 else 3 if distance_value <= 20 + 0.01 else 1
            self._deal_damage(unit, amount, "ブラックホール", attacker=actor)
        return True

    def _skill_samurai(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            for target in self._units_in_radius(actor.cell, 3, source=actor):
                self._deal_damage(target, max(1, actor.base_power // 3), "間合い", attacker=actor)
            return True
        if tier == "medium":
            self.samurai_sky_units.add(actor.id)
            self.round_notices.append("空の間合い: 次の自分の番まで反応斬り状態です。")
            return True
        self.samurai_guard_units.add(actor.id)
        self.round_notices.append("極の間合い: 次の自分の番まで迎撃状態です。")
        return True

    def _skill_berserker(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            radius = int(self.berserk_radius.get(actor.id, 0))
            for target in self._units_in_radius(actor.cell, radius, source=actor):
                self._deal_damage(target, actor.base_power, "ホショク", attacker=actor)
            return True
        if tier == "medium":
            actor.hp = max(1, actor.hp - 5)
            actor.move_bonus += actor.base_move
            self.round_notices.append("シュンソク: HP を 5 消費し、行動力を倍にしました。")
            return True
        actor.hp = max(1, actor.hp // 2)
        self.berserk_radius[actor.id] = int(self.berserk_radius.get(actor.id, 0)) + 1
        self.round_notices.append(f"バーサーク: 捕食範囲が {self.berserk_radius[actor.id]} に拡大しました。")
        return True

    def _skill_beastmaster(self, actor: UnitState, tier: str, path: List[Cell], settings: dict) -> bool:
        if tier == "small":
            self.round_notices.append("獅子ライド: 10マス移動し、重なった敵へ 4 ダメージ。")
            return True
        if tier == "medium":
            self.bird_snapshots[actor.owner] = {
                "set": self.set_number,
                "round": self.round_number,
                "cells": [[unit.cell[0], unit.cell[1]] for unit in self._living_units() if unit.owner != actor.owner],
            }
            self.round_notices.append("バードリスニング: 敵位置を記録しました。")
            return True
        summon_id = f"{actor.id}-hamster"
        self.units[summon_id] = UnitState(
            id=summon_id,
            team=actor.team,
            owner=actor.owner,
            character_key="hamster",
            role="ハムスター",
            name="ハムスター",
            display_name="ハムスター",
            move=20,
            power=1,
            vision=2,
            cell=path[-1] if path else actor.cell,
            spawn_cell=path[-1] if path else actor.cell,
            hp=1,
            max_hp=1,
            base_move=20,
            base_power=1,
            base_vision=2,
            is_summon=True,
        )
        self.round_notices.append("ハムマッチ: ハムスターを召喚しました。")
        return True

    def _movement_type(self, actor: UnitState, tier: str) -> str:
        if not tier:
            return "move"
        key = actor.character_key
        if key == "speed_star" and tier in {"small", "medium", "large"}:
            return "skill_move"
        if key == "beastmaster" and tier in {"small", "large"}:
            return "skill_move"
        if key == "berserker" and tier == "small":
            return "move"
        if key in {"spiritualist", "archer", "leader", "saint", "psychic", "samurai"} and tier in {"medium", "large"}:
            return "immobile"
        if key == "psychic" and tier == "small":
            return "immobile"
        return "move"

    def _planned_step_limit(self, actor: UnitState, tier: str) -> int:
        move_type = self._movement_type(actor, tier)
        if move_type == "immobile":
            return 0
        if actor.character_key == "speed_star" and tier in {"small", "medium"}:
            return 10
        if actor.character_key == "berserker" and tier == "medium":
            return actor.effective_move * 2
        if actor.character_key == "beastmaster" and tier == "small":
            return 10
        if actor.character_key == "hamster":
            return actor.effective_move
        return actor.effective_move

    def _current_actor_id(self, team: str) -> str:
        plan = self.turn_plan.get(team) or []
        if not plan:
            return ""
        key = plan[self.round_number - 1] if self.round_number - 1 < len(plan) else ""
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
        tier = str(settings.get("skill_tier") or "")
        if tier not in {"", "small", "medium", "large"}:
            raise GameError("指定できない技です。")
        limit = self._planned_step_limit(actor, tier)
        clean_path = self._normalize_move_plan(actor, path, limit)
        if actor.character_key == "speed_star" and tier == "large":
            direction = str(settings.get("skill_direction") or "")
            distance_count = int(settings.get("skill_distance") or 0)
            clean_path = self._build_straight_path(actor.cell, direction, distance_count)
        self.pending_actions[symbol] = {
            "actor_id": actor_id,
            "path": clean_path,
            "skill_tier": tier,
            "skill_target_unit_id": str(settings.get("skill_target_unit_id") or ""),
            "skill_target_cell": settings.get("skill_target_cell"),
            "skill_direction": str(settings.get("skill_direction") or ""),
            "skill_distance": int(settings.get("skill_distance") or 0),
            "leader_reconfigure": settings.get("leader_reconfigure") or {},
            "leader_redeploy": settings.get("leader_redeploy") or {},
        }
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
            try:
                self._process_start_of_turn_states(actor)
                self._expire_actor_states(actor)
                blocked = False
            except GameError as exc:
                self.round_notices.append(str(exc))
                blocked = True

            tier = str(payload.get("skill_tier") or "")
            path: List[Cell] = list(payload.get("path") or [])
            skill_used = False
            if not blocked and tier:
                skill_used = self._apply_skill(actor, tier, path, payload)

            soldier_small_hit = False
            leader_seen_targets: Set[str] = set()
            for cell in path if not blocked else []:
                previous = actor.cell
                actor.cell = cell
                self._collect_coins(actor)
                self._capture_flags_on_overlap(actor)
                if tier == "small" and actor.character_key == "archer":
                    for target in self._visible_targets_for_actor(actor, enemy_only=True):
                        self._deal_damage(target, 1, "通常射出", attacker=actor)
                if tier == "small" and actor.character_key == "soldier" and not soldier_small_hit:
                    targets = [target for target in self._units_in_chebyshev(actor.cell, 1, source=actor) if target.owner != actor.owner]
                    if targets:
                        self._deal_damage(targets[0], max(1, actor.base_power // 3), "剣技", attacker=actor)
                        soldier_small_hit = True
                if tier == "small" and actor.character_key == "leader":
                    visible_enemies = self._visible_targets_for_actor(actor, enemy_only=True)
                    for target in visible_enemies:
                        if target.id not in leader_seen_targets:
                            self._deal_damage(target, max(1, actor.base_power // 5), "通常業務", attacker=actor)
                            leader_seen_targets.add(target.id)
                if tier == "medium" and actor.character_key == "speed_star":
                    for target in [unit for unit in self._units_at_cell(actor.cell, source=actor) if unit.owner != actor.owner]:
                        self._deal_damage(target, max(1, actor.base_power // 5), "ブーストバスター", attacker=actor)
                if tier == "small" and actor.character_key == "beastmaster":
                    for target in [unit for unit in self._units_at_cell(actor.cell, source=actor) if unit.owner != actor.owner]:
                        self._deal_damage(target, 4, "獅子ライド", attacker=actor)
                if tier == "large" and actor.character_key == "speed_star":
                    for target in [unit for unit in self._units_at_cell(actor.cell, source=actor) if unit.owner != actor.owner]:
                        self._deal_damage(target, target.hp, "ソニックスター", attacker=actor)
                    self._damage_flag_at(actor, actor.cell, "ソニックスター")
                    self._apply_speed_star_large_side_damage(actor, previous)

                for samurai in [unit for unit in self.units.values() if unit.alive and unit.owner != actor.owner and unit.id in self.samurai_sky_units]:
                    if actor.cell in self._visible_cells_for_actor(samurai):
                        self._deal_damage(actor, max(1, samurai.base_power // 2), "空の間合い", attacker=samurai)
                for samurai in [unit for unit in self.units.values() if unit.alive and unit.owner != actor.owner and unit.id in self.samurai_guard_units]:
                    if max(abs(actor.cell[0] - samurai.cell[0]), abs(actor.cell[1] - samurai.cell[1])) <= 1:
                        self._deal_damage(actor, actor.hp, "極の間合い", attacker=samurai)

                for archer_id, mark in list(self.archer_marks.items()):
                    archer = self.units.get(archer_id)
                    if not archer or not archer.alive or archer.owner == actor.owner:
                        continue
                    if actor.id in set(mark.get("targets", [])) and distance(archer.cell, actor.cell) <= int(mark.get("range", 10)) + 0.01:
                        self._deal_damage(actor, 2, "中距離曲射", attacker=archer)

                if not actor.alive:
                    break

            actor.cost += 1
            actor.move_bonus = 0
            self._refresh_known_map(actor.owner)

        self._advance_summons()
        for team in TEAM_SYMBOLS:
            self._refresh_known_map(team)
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
            self._respawn_coins()
            self.phase = "order_select"
            for player in self.players.values():
                player.order_confirmed = False
            self.pending_actions.clear()
            self.message = f"{self.set_number}セット目が始まります。行動順を決めてください。"
            return
        self.round_number += 1
        self.message = "次の行動を決定してください。"

    def _visible_cells_for(self, actor_id: str) -> Set[Cell]:
        actor = self.units.get(actor_id)
        if actor is None or not actor.alive:
            return set()
        return self._visible_cells_for_team(actor.owner)

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
        visible_cells = self._visible_cells_for_team(viewer_symbol) if viewer_symbol in TEAM_SYMBOLS else set()
        known_floor = set(self.known_floor_by_team.get(viewer_symbol, set()))
        known_walls = set(self.known_walls_by_team.get(viewer_symbol, set()))
        known_coins = set(self.known_coins_by_team.get(viewer_symbol, set()))
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
            "coins": [list(cell) for cell in sorted(known_coins)],
            "visible_cells": [list(cell) for cell in sorted(visible_cells)],
            "known_floor": [list(cell) for cell in sorted(known_floor)],
            "known_walls": [list(cell) for cell in sorted(known_walls)],
            "known_coins": [list(cell) for cell in sorted(known_coins)],
            "bird_snapshot": self.bird_snapshots.get(viewer_symbol),
            "viewport": self._viewport_for(actor_id) if actor_id else {"origin": [0, 0], "cells": [], "visible_cells": []},
        }
