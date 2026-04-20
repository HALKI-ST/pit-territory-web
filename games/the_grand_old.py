from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple


Cell = Tuple[int, int]
TEAM_SYMBOLS = ("A", "B")
TEAM_NAMES = {"A": "Alpha", "B": "Bravo"}
DEBUG_FIELD_TYPE = "debug_lab"
FIELD_TYPES = ("grassland", "maze", "volcano", DEBUG_FIELD_TYPE)
BOARD_SIZE = 50
VIEWPORT_SIZE = 15
MIN_SPAWN_DISTANCE = 10
MAX_SETS = 10
ROUNDS_PER_SET = 10
COIN_TARGET = 20


class GameError(ValueError):
    pass


@dataclass(frozen=True)
class SkillDef:
    key: str
    name: str
    cost: int
    description: str


@dataclass(frozen=True)
class CharacterDef:
    key: str
    name: str
    move: int
    power: int
    vision: int
    small: SkillDef
    medium: SkillDef
    large: SkillDef
    memo: str


CHARACTERS: Dict[str, CharacterDef] = {
    "speed_star": CharacterDef("speed_star", "スピードスター", 0, 10, 3, SkillDef("dash", "ダッシュ", 1, "10マスまで移動する。"), SkillDef("boost_buster", "ブーストバスター", 2, "移動しつつ十字方向を攻撃する。"), SkillDef("sonic_star", "ソニックスター", 5, "一直線に突っ切る。"), "機械の身体に閉じ込められても速さを求め続ける。"),
    "spiritualist": CharacterDef("spiritualist", "ミャーノ・マーリー", 3, 4, 5, SkillDef("thousand_eye", "サウザンド・アイ", 2, "このセット中、味方の視界を共有する。"), SkillDef("gold_bind", "ゴールド・バインド", 3, "相手1体を拘束する。"), SkillDef("hundred_night", "ハンドレッド・ナイト", 4, "追尾する幽霊を放つ。"), "呪いとともに戦う霊能力者。"),
    "archer": CharacterDef("archer", "アチャ爺", 6, 9, 5, SkillDef("normal_shot", "通常射出", 2, "視界内の敵を狙い続ける。"), SkillDef("curve_shot", "中距離曲射", 3, "追跡射撃で継続ダメージを狙う。"), SkillDef("long_shot", "超遠距離攻撃", 5, "超長距離から狙撃する。"), "近代兵器に屈しない老兵の弓兵。"),
    "soldier": CharacterDef("soldier", "レオ・アレクス", 5, 10, 3, SkillDef("sword", "剣技", 1, "近接攻撃。"), SkillDef("prayer", "弱者の祈り", 3, "味方を支援する。"), SkillDef("hero", "主人公補正", 5, "追い詰められるほど覚醒する。"), "勇者の血を引く雑兵。"),
    "leader": CharacterDef("leader", "ヴァン・クラリッサ", 7, 15, 4, SkillDef("sidearm", "通常業務", 1, "銃での基本攻撃。"), SkillDef("reconfigure", "再構成", 3, "行動順を組み直す。"), SkillDef("redeploy", "再配達", 5, "味方を再配置する。"), "苛烈な戦場を生き残り続ける指揮官。"),
    "saint": CharacterDef("saint", "アリア", 5, 1000, 1, SkillDef("reflect", "リフレクト", 1, "受けたダメージの一部を返す。"), SkillDef("prayer_of_saint", "聖女の祈り", 2, "味方を祝福する。"), SkillDef("true_sight", "見通す目", 3, "視界を広げる。"), "聖布で目を隠した聖女。"),
    "psychic": CharacterDef("psychic", "白星 夢", 4, 5, 5, SkillDef("flash", "フラッシュ", 1, "このセット中、探知力を上げる。"), SkillDef("teleport", "テレポート", 2, "ランダムに転移する。"), SkillDef("blackhole", "ブラックホール", 4, "広域に精神衝撃を放つ。"), "明るく危ういサイキッカー。"),
    "samurai": CharacterDef("samurai", "櫻井 光二郎", 7, 10, 4, SkillDef("spacing", "間合い", 1, "三マス圏を斬る。"), SkillDef("sky_spacing", "空の間合い", 2, "反応斬りを放つ。"), SkillDef("ultimate_spacing", "極の間合い", 5, "完璧な居合の構えを取る。"), "抜く前に勝負を決める居合の達人。"),
    "berserker": CharacterDef("berserker", "ニック", 2, 100, 2, SkillDef("devour", "ホショク", 1, "接触した相手を押し潰す。"), SkillDef("shunsoku", "シュンソク", 2, "体力を削って加速する。"), SkillDef("berserk", "バーサーク", 3, "攻撃範囲を広げる。"), "鎖と識別刻印を残した実験体。"),
    "beastmaster": CharacterDef("beastmaster", "メイ・スフィン", 5, 5, 3, SkillDef("lion_ride", "獅子ライド", 2, "獣の勢いで突進する。"), SkillDef("bird_listening", "バードリスニング", 3, "敵位置の手掛かりを得る。"), SkillDef("ham_match", "ハムマッチ", 4, "ハムスターを召喚する。"), "動物と絆を結ぶ獣使い。"),
}

CHARACTERS["speed_star"] = CharacterDef(
    "speed_star",
    "スピードスター",
    0,
    10,
    3,
    SkillDef("dash", "ダッシュ", 1, "技で移動する。攻撃力なし。10マスまで移動する。"),
    SkillDef("boost_buster", "ブーストバスター", 3, "技で移動する。攻撃力は戦闘力/5。10マスまで移動し、移動中に敵と同じマスへ重なるたびに攻撃する。"),
    SkillDef("sonic_star", "ソニックスター", 4, "技で移動する。方向と距離を入力して一直線に突進し、進行方向上は撃破、左右2マスには戦闘力/2ダメージを与える。"),
    "機械の身体に閉じ込められても速さを求め続ける。",
)


@dataclass
class PlayerSlot:
    symbol: str
    name: str
    connected: bool = False
    selected_keys: List[str] = field(default_factory=list)
    priority: List[str] = field(default_factory=list)
    roster_confirmed: bool = False
    order_confirmed: bool = False
    coins: int = 0
    known_floor: Set[Cell] = field(default_factory=set)
    known_walls: Set[Cell] = field(default_factory=set)
    known_lava: Set[Cell] = field(default_factory=set)
    known_coins: Set[Cell] = field(default_factory=set)

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "selected_keys": list(self.selected_keys),
            "priority": list(self.priority),
            "roster_confirmed": self.roster_confirmed,
            "order_confirmed": self.order_confirmed,
            "coins": self.coins,
        }


@dataclass
class FlagState:
    id: str
    team: str
    cell: Cell
    alive: bool = True


@dataclass
class UnitState:
    id: str
    owner: str
    character_key: str
    display_name: str
    move: int
    base_power: int
    base_vision: int
    cell: Cell
    spawn_cell: Cell
    hp: int
    cost: int = 0
    alive: bool = True
    is_summon: bool = False
    move_bonus: int = 0
    vision_bonus: int = 0
    true_sight: bool = False
    reflect_ratio: float = 0.0
    bound: bool = False
    guard_radius: int = 0

    @property
    def effective_move(self) -> int:
        return max(0, self.move + self.move_bonus)

    @property
    def effective_vision(self) -> int:
        return max(1, self.base_vision + self.vision_bonus)

    @property
    def max_hp(self) -> int:
        return self.base_power


def ceil_half(value: int) -> int:
    return max(1, math.ceil(value / 2))


class TheGrandOldGame:
    game_type = "the_grand_old"
    title = "旧 The Grand"
    subtitle = "広域フィールド対戦プロトタイプ"
    category = "original"
    min_players = 2
    max_players = 2
    player_label = "2 players"
    seat_order = list(TEAM_SYMBOLS)
    host_control_actions = {"advance_phase", "confirm_field"}

    def __init__(self) -> None:
        self.players: Dict[str, PlayerSlot] = {
            symbol: PlayerSlot(symbol=symbol, name=f"Player {symbol}")
            for symbol in TEAM_SYMBOLS
        }
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.message = "両プレイヤーの参加を待っています。"
        self.winner_text = ""
        self.field_type = "grassland"
        self.board_size = BOARD_SIZE
        self.viewport_size = VIEWPORT_SIZE
        self.set_number = 1
        self.round_number = 1
        self.coin_target = COIN_TARGET
        self.units: Dict[str, UnitState] = {}
        self.flags: Dict[str, FlagState] = {}
        self.walls: Set[Cell] = set()
        self.lava: Set[Cell] = set()
        self.coins: Set[Cell] = set()
        self.pending_actions: Dict[str, dict] = {}
        self.continue_confirmed: Set[str] = set()
        self.replay_token = 0
        self.last_replay_frames: List[dict] = []
        self.round_notices: List[str] = []
        self.debug_lab = None

    @classmethod
    def catalog_entry(cls) -> dict:
        return {
            "game_type": cls.game_type,
            "title": cls.title,
            "subtitle": cls.subtitle,
            "category": cls.category,
            "status": "playable",
            "min_players": cls.min_players,
            "max_players": cls.max_players,
            "player_label": cls.player_label,
        }

    def set_player_name(self, symbol: str, name: str) -> None:
        if symbol in self.players:
            self.players[symbol].name = (name or f"Player {symbol}").strip()[:24] or f"Player {symbol}"

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected
            self.start_if_ready()

    def start_if_ready(self) -> None:
        if all(self.players[symbol].connected for symbol in TEAM_SYMBOLS):
            self.message = "両プレイヤーが揃いました。部屋主はフィールド選択へ進めます。"
        else:
            self.message = "両プレイヤーの参加を待っています。"

    def reset_for_rematch(self) -> None:
        saved = {
            symbol: (player.name, player.connected)
            for symbol, player in self.players.items()
        }
        self.__init__()
        for symbol, (name, connected) in saved.items():
            self.players[symbol].name = name
            self.players[symbol].connected = connected
        self.start_if_ready()

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        settings = settings or {}
        if self.phase == "lab" and self.debug_lab is not None:
            self.debug_lab.apply_host_action(action, settings)
            return
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
        cell: Optional[List[int]] = None,
        settings: Optional[dict] = None,
        **_: object,
    ) -> None:
        settings = settings or {}
        if self.phase == "lab" and self.debug_lab is not None:
            self.debug_lab.apply_player_action("A", action, cell=cell, settings=settings)
            self.message = self.debug_lab.message
            return
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
        if action == "resign":
            self._finish(self._enemy_of(symbol), f"{self.players[symbol].name} resigned.")
            return
        if action == "rematch":
            self.reset_for_rematch()
            return
        raise GameError("未対応のプレイヤー操作です。")

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        if self.phase == "lab" and self.debug_lab is not None:
            payload = self.debug_lab.to_public_dict("A")
            payload["game_type"] = self.game_type
            payload["title"] = self.title
            payload["field_type"] = DEBUG_FIELD_TYPE
            payload["phase"] = "lab"
            payload["message"] = self.debug_lab.message
            return payload
        player = self.players.get(viewer_symbol)
        visible_cells = self._visible_cells_for_viewer(viewer_symbol)
        replay_frames = self._viewer_replay_frames(viewer_symbol)
        replay_units = replay_frames[-1]["units"] if replay_frames else None
        units_payload = self._viewer_units_payload(viewer_symbol, visible_cells, replay_units)
        return {
            "game_type": self.game_type,
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "message": self.message,
            "winner_text": self.winner_text,
            "field_type": self.field_type,
            "board_size": self.board_size,
            "viewport_size": self.viewport_size,
            "set_number": self.set_number,
            "max_sets": MAX_SETS,
            "round_number": self.round_number,
            "rounds_per_set": ROUNDS_PER_SET,
            "coin_target": self.coin_target,
            "players": {symbol: slot.to_public_dict() for symbol, slot in self.players.items()},
            "catalog": [self._character_catalog_payload(character) for character in CHARACTERS.values()],
            "flags": [
                {"id": flag.id, "team": flag.team, "cell": list(flag.cell), "alive": flag.alive}
                for flag in self.flags.values()
            ],
            "coins": [list(cell) for cell in sorted(self.coins)],
            "known_floor": [list(cell) for cell in sorted(player.known_floor if player else set())],
            "known_walls": [list(cell) for cell in sorted(player.known_walls if player else set())],
            "known_lava": [list(cell) for cell in sorted(player.known_lava if player else set())],
            "known_coins": [list(cell) for cell in sorted(player.known_coins if player else set())],
            "visible_cells": [list(cell) for cell in sorted(visible_cells)],
            "units": units_payload,
            "viewer_symbol": viewer_symbol,
            "viewer_actor_id": self._current_actor_id(viewer_symbol),
            "enemy_actor_id": self._current_actor_id(self._enemy_of(viewer_symbol)) if viewer_symbol in TEAM_SYMBOLS else "",
            "pending_actions": {team: team in self.pending_actions for team in TEAM_SYMBOLS},
            "viewer_waiting": viewer_symbol in self.pending_actions,
            "result_ready": bool(self.last_replay_frames) and not self.pending_actions and not self.game_over,
            "continue_confirmed": {team: team in self.continue_confirmed for team in TEAM_SYMBOLS},
            "viewer_continue_confirmed": viewer_symbol in self.continue_confirmed,
            "replay_token": self.replay_token,
            "replay_frames": replay_frames,
            "round_notices": list(self.round_notices),
            "setup_note": self._setup_note(),
        }

    def _advance_phase(self) -> None:
        if self.phase != "waiting":
            raise GameError("この段階からは進行できません。")
        if not all(self.players[symbol].connected for symbol in TEAM_SYMBOLS):
            raise GameError("両プレイヤーが接続している必要があります。")
        self.phase = "field_select"
        self.message = "フィールドを選択してください。"

    def _confirm_field(self, settings: dict) -> None:
        if self.phase != "field_select":
            raise GameError("フィールド選択中のみ確定できます。")
        field_type = str(settings.get("field_type") or self.field_type)
        if field_type not in FIELD_TYPES:
            raise GameError("不明なフィールドです。")
        self.field_type = field_type
        if field_type == DEBUG_FIELD_TYPE:
            from games.the_grand_lab import TheGrandLabGame

            self.debug_lab = TheGrandLabGame()
            self.debug_lab.players["A"].name = self.players["A"].name
            self.debug_lab.update_connection("A", True)
            self.phase = "lab"
            self.started = True
            self.message = self.debug_lab.message
            return
        self.phase = "character_select"
        self.message = "各プレイヤーが編成を選択します。"

    def _update_setup(self, symbol: str, settings: dict) -> None:
        if symbol not in self.players:
            raise GameError("不明なプレイヤーです。")
        if self.phase not in {"character_select", "order_select"}:
            raise GameError("設定を変更できるのは戦闘開始前だけです。")
        player = self.players[symbol]
        if "selected_keys" in settings:
            if self.phase != "character_select":
                raise GameError("キャラクター選択はすでに終了しています。")
            selected = [str(key) for key in settings.get("selected_keys", []) if str(key) in CHARACTERS]
            deduped: List[str] = []
            for key in selected:
                if key not in deduped:
                    deduped.append(key)
            if not 1 <= len(deduped) <= len(CHARACTERS):
                raise GameError("キャラクターは1体以上10体以下で選んでください。")
            player.selected_keys = deduped
            player.priority = list(deduped)
            player.roster_confirmed = False
            player.order_confirmed = False
            return
        if "priority" in settings:
            if self.phase != "order_select":
                raise GameError("行動順は行動順設定中のみ変更できます。")
            priority = [str(key) for key in settings.get("priority", [])]
            if set(priority) != set(player.selected_keys) or len(priority) != len(player.selected_keys):
                raise GameError("行動順には選択したキャラクターをちょうど1回ずつ入れてください。")
            player.priority = priority
            player.order_confirmed = False

    def _confirm_roster(self, symbol: str) -> None:
        if self.phase != "character_select":
            raise GameError("編成確定はキャラクター選択中のみ行えます。")
        player = self.players[symbol]
        if not player.selected_keys:
            raise GameError("最低1体はキャラクターを選んでください。")
        player.roster_confirmed = True
        if all(self.players[team].roster_confirmed for team in TEAM_SYMBOLS):
            self._build_match_state()
            self.phase = "order_select"
            self.message = "配置が完了しました。各チームの行動順を決めてください。"
        else:
            self.message = f"{self.players[symbol].name} が編成を確定しました。"

    def _confirm_order(self, symbol: str, settings: Optional[dict] = None) -> None:
        if self.phase != "order_select":
            raise GameError("行動順確定は行動順設定中のみ行えます。")
        settings = settings or {}
        if "priority" in settings:
            self._update_setup(symbol, {"priority": settings.get("priority", [])})
        player = self.players[symbol]
        if set(player.priority) != set(player.selected_keys):
            raise GameError("行動順が完成していません。")
        player.order_confirmed = True
        if all(self.players[team].order_confirmed for team in TEAM_SYMBOLS):
            self._begin_battle()
        else:
            self.message = f"{self.players[symbol].name} が行動順を確定しました。"

    def _setup_note(self) -> str:
        if self.phase == "waiting":
            return "両プレイヤーが揃ったら、部屋主がフィールド選択へ進みます。"
        if self.phase == "field_select":
            return "フィールドを1つ選択します。草原・迷宮・火山なら本編、デバッグ用フィールドならお試し部屋へ進みます。"
        if self.phase == "character_select":
            return "1体から10体まで、重複なしでキャラを選びます。"
        if self.phase == "order_select":
            return "1セット10ターンで循環する行動順を決めます。"
        if self.game_over:
            return self.winner_text or "Game over."
        if self.pending_actions:
            return "行動を決定しました。相手の入力を待っています。"
        if self.last_replay_frames:
            return "行動結果を確認して、次へ進んでください。"
        return "このターンの移動を決定してください。"

    def _build_match_state(self) -> None:
        self.board_size = BOARD_SIZE
        self.walls = self._generate_walls(self.field_type)
        self.lava = self._generate_lava(self.field_type)
        self.units = {}
        self.flags = {}
        self.pending_actions = {}
        self.continue_confirmed = set()
        self.last_replay_frames = []
        self.round_notices = []
        self.round_notices = []
        self.replay_token = 0
        for player in self.players.values():
            player.coins = 0
            player.order_confirmed = False
            player.known_floor = set()
            player.known_walls = set()
            player.known_lava = set()
            player.known_coins = set()

        spawn_cells = self._generate_spawn_cells(sum(len(self.players[team].selected_keys) for team in TEAM_SYMBOLS))
        cursor = 0
        for team in TEAM_SYMBOLS:
            for key in self.players[team].selected_keys:
                character = CHARACTERS[key]
                spawn = spawn_cells[cursor]
                cursor += 1
                unit_id = f"{team}:{key}"
                self.units[unit_id] = UnitState(
                    id=unit_id,
                    owner=team,
                    character_key=key,
                    display_name=character.name,
                    move=character.move,
                    base_power=character.power,
                    base_vision=character.vision,
                    cell=spawn,
                    spawn_cell=spawn,
                    hp=character.power,
                )
                self.flags[f"flag:{unit_id}"] = FlagState(id=f"flag:{unit_id}", team=team, cell=spawn)
        self._spawn_coins()
        self._seed_initial_memory()

    def _begin_battle(self) -> None:
        self.started = True
        self.game_over = False
        self.phase = "battle"
        if self.set_number < 1:
            self.set_number = 1
        if self.round_number < 1:
            self.round_number = 1
        self.pending_actions = {}
        self.continue_confirmed = set()
        self.last_replay_frames = []
        self.message = "1セット1ターン目です。両プレイヤーが行動を決めてください。"
        self._remember_all_visible()

    def _submit_turn(self, symbol: str, settings: dict) -> None:
        if self.phase != "battle" or not self.started or self.game_over:
            raise GameError("いまは戦闘中ではありません。")
        if symbol in self.pending_actions:
            raise GameError("このチームはすでに行動を決定しています。")
        actor = self._current_actor(symbol)
        actor_id = str(settings.get("actor_id") or "")
        skill_tier = str(settings.get("skill_tier") or "")
        if actor:
            if actor_id and actor_id != actor.id:
                raise GameError("このターンに行動できるキャラクターではありません。")
            plan = self._normalize_move_plan(
                actor,
                settings.get("path") or settings.get("plan") or [],
                max_steps=self._planned_step_limit(actor, skill_tier),
            )
            if actor.character_key == "speed_star" and skill_tier == "large":
                direction = str(settings.get("skill_direction") or "")
                distance = int(settings.get("skill_distance") or 0)
                straight_plan = self._build_straight_path(actor.cell, direction, distance)
                if straight_plan:
                    plan = straight_plan
        else:
            plan = []
        self.pending_actions[symbol] = {
            "actor_id": actor.id if actor else "",
            "path": plan,
            "turn_action": str(settings.get("turn_action") or "move"),
            "skill_tier": skill_tier,
            "skill_direction": str(settings.get("skill_direction") or ""),
            "skill_distance": int(settings.get("skill_distance") or 0),
        }
        if len(self.pending_actions) < 2:
            self.message = f"{self.players[symbol].name} が行動を決定しました。相手の入力を待っています。"
            return
        self._resolve_round()

    def _confirm_result(self, symbol: str) -> None:
        if self.phase != "battle" or self.game_over:
            raise GameError("確認待ちの結果がありません。")
        if self.pending_actions or not self.last_replay_frames:
            raise GameError("まだ確認できる結果がありません。")
        self.continue_confirmed.add(symbol)
        if len(self.continue_confirmed) < len(TEAM_SYMBOLS):
            self.message = f"{self.players[symbol].name} が結果確認を終えました。相手を待っています。"
            return
        self.continue_confirmed = set()
        self.last_replay_frames = []
        self._advance_after_result()

    def _planned_step_limit(self, actor: UnitState, skill_tier: str) -> int:
        if skill_tier == "small" and actor.character_key in {"speed_star", "beastmaster"}:
            return 10
        if skill_tier == "medium" and actor.character_key == "speed_star":
            return 10
        if skill_tier == "large" and actor.character_key == "speed_star":
            return self.board_size
        return actor.effective_move

    def _direction_delta(self, direction: str) -> Optional[Cell]:
        mapping = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        return mapping.get(direction)

    def _build_straight_path(self, origin: Cell, direction: str, distance: int) -> List[Cell]:
        delta = self._direction_delta(direction)
        if not delta or distance <= 0:
            return []
        path: List[Cell] = []
        x, y = origin
        for _ in range(min(distance, self.board_size)):
            x += delta[0]
            y += delta[1]
            cell = (x, y)
            if not self._in_bounds(cell):
                break
            path.append(cell)
        return path

    def _normalize_move_plan(self, actor: UnitState, raw_path: object, max_steps: Optional[int] = None) -> List[Cell]:
        if not isinstance(raw_path, list):
            return []
        plan: List[Cell] = []
        previous = actor.cell
        step_limit = actor.effective_move if max_steps is None else max(0, int(max_steps))
        for item in raw_path[:step_limit]:
            if not isinstance(item, list) or len(item) != 2:
                continue
            cell = (int(item[0]), int(item[1]))
            if not self._in_bounds(cell):
                continue
            if self._manhattan(previous, cell) != 1:
                break
            if cell in self.walls:
                break
            plan.append(cell)
            previous = cell
        return plan

    def _resolve_round(self) -> None:
        frames: List[dict] = []
        actors = {team: self._current_actor(team) for team in TEAM_SYMBOLS}
        self.round_notices = []
        self._reset_round_bonuses()
        self._apply_pre_move_skills(actors)
        step_count = max(len(self.pending_actions.get(team, {}).get("path", [])) for team in TEAM_SYMBOLS)
        step_count = max(1, step_count)

        for team, actor in actors.items():
            if actor and actor.alive:
                actor.cost += 1

        for step_index in range(step_count):
            for team in TEAM_SYMBOLS:
                actor = actors[team]
                if actor is None or not actor.alive:
                    continue
                if actor.bound:
                    continue
                path = self.pending_actions.get(team, {}).get("path", [])
                if step_index < len(path):
                    next_cell = path[step_index]
                    if next_cell not in self.walls:
                        previous_cell = actor.cell
                        actor.cell = next_cell
                        self._collect_coin(actor)
                        self._apply_contact_skills(actor, team, previous_cell)
            self._apply_reactive_skills(actors)
            self._remember_all_visible()
            frames.append(self._snapshot_frame())
            self._check_victory()
            if self.game_over:
                break

        if not self.game_over:
            self._apply_post_move_skills(actors)
            self._remember_all_visible()
            frames.append(self._snapshot_frame())
            self._check_victory()
            if self.game_over:
                self.pending_actions = {}
                self.continue_confirmed = set()
                self.replay_token += 1
                self.last_replay_frames = frames
                return

        self.pending_actions = {}
        self.continue_confirmed = set()
        self.replay_token += 1
        self.last_replay_frames = frames
        if self.game_over:
            return
        self.message = f"{self.set_number}セット {self.round_number}ターンの結果です。確認後に次へ進んでください。"

    def _advance_after_result(self) -> None:
        self.round_notices = []
        self.round_number += 1
        if self.round_number > ROUNDS_PER_SET:
            self._end_set()
            return
        self.message = f"{self.set_number}セット {self.round_number}ターン目です。両プレイヤーが行動を決めてください。"

    def _end_set(self) -> None:
        self.set_number += 1
        if self.set_number > MAX_SETS:
            self._finish_by_coins()
            return
        self.round_number = 1
        self.pending_actions = {}
        self.continue_confirmed = set()
        self.round_notices = []
        self.phase = "order_select"
        self._spawn_coins()
        self._remember_all_visible()
        for player in self.players.values():
            player.order_confirmed = False
            if not player.priority:
                player.priority = list(player.selected_keys)
        self.message = f"{self.set_number}セット目が始まりました。コインが再配置されています。"

    def _finish_by_coins(self) -> None:
        coins_a = self.players["A"].coins
        coins_b = self.players["B"].coins
        if coins_a == coins_b:
            self._finish("", f"コイン同数の引き分けです。 {coins_a} - {coins_b}")
            return
        winner = "A" if coins_a > coins_b else "B"
        self._finish(winner, f"{self.players[winner].name} がコイン勝利しました。 {coins_a} - {coins_b}")

    def _finish(self, winner: str, reason: str) -> None:
        self.game_over = True
        self.winner_text = reason
        self.message = reason

    def _check_victory(self) -> None:
        for team in TEAM_SYMBOLS:
            enemy = self._enemy_of(team)
            enemy_total = len(self.players[enemy].selected_keys)
            enemy_alive = [unit for unit in self.units.values() if unit.owner == enemy and unit.alive]
            enemy_flags_alive = [flag for flag in self.flags.values() if flag.team == enemy and flag.alive]
            enemy_dead = enemy_total - len(enemy_alive)
            if self.players[team].coins >= self.coin_target:
                self._finish(team, f"{self.players[team].name} が{self.coin_target}コインを集めて勝利しました。")
                return
            if enemy_total and enemy_dead >= ceil_half(enemy_total):
                self._finish(team, f"{self.players[team].name} が敵の過半数を撃破しました。")
                return
            if enemy_total and not enemy_flags_alive:
                self._finish(team, f"{self.players[team].name} が敵の旗をすべて破壊しました。")
                return

    def _collect_coin(self, actor: UnitState) -> None:
        if actor.cell in self.coins:
            self.coins.remove(actor.cell)
            self.players[actor.owner].coins += 1
            for player in self.players.values():
                player.known_coins.discard(actor.cell)

    def _destroy_enemy_flag_at(self, attacker_team: str, cell: Cell) -> bool:
        for flag in self.flags.values():
            if not flag.alive or flag.team == attacker_team or flag.cell != cell:
                continue
            flag.alive = False
            attacker_name = self.players.get(attacker_team).name if attacker_team in self.players else attacker_team
            flag_name = "青旗" if flag.team == "A" else "赤旗"
            self.round_notices.append(f"{attacker_name} が {flag_name} を破壊しました。")
            return True
        return False

    def _destroy_enemy_flags_in_cells(self, attacker_team: str, cells: Iterable[Cell]) -> bool:
        destroyed = False
        for cell in cells:
            destroyed = self._destroy_enemy_flag_at(attacker_team, cell) or destroyed
        return destroyed

    def _kill_unit(self, unit: UnitState, attacker_team: str = "") -> None:
        if not unit.alive:
            return
        unit.alive = False
        if attacker_team and attacker_team != unit.owner:
            defender_alive = max(1, len([entry for entry in self.units.values() if entry.owner == unit.owner and entry.alive]))
            stolen = min(self.players[unit.owner].coins, math.ceil(self.players[unit.owner].coins / defender_alive))
            self.players[unit.owner].coins -= stolen
            self.players[attacker_team].coins += stolen

    def _reset_round_bonuses(self) -> None:
        for unit in self.units.values():
            unit.move_bonus = 0
            unit.vision_bonus = 0
            unit.true_sight = False
            unit.reflect_ratio = 0.0
            unit.bound = False
            unit.guard_radius = 0

    def _apply_pre_move_skills(self, actors: Dict[str, Optional[UnitState]]) -> None:
        for team, actor in actors.items():
            if actor is None or not actor.alive:
                continue
            action = self.pending_actions.get(team, {})
            skill_tier = action.get("skill_tier") or ""
            if skill_tier not in {"small", "medium", "large"}:
                continue
            character = CHARACTERS.get(actor.character_key)
            if not character:
                action["skill_tier"] = ""
                continue
            skill = getattr(character, skill_tier, None)
            if not skill or actor.cost < skill.cost:
                action["skill_tier"] = ""
                continue
            actor.cost -= skill.cost
            self._resolve_skill(actor, team, skill_tier)

    def _resolve_skill(self, actor: UnitState, team: str, skill_tier: str) -> None:
        key = actor.character_key
        if key == "speed_star" and skill_tier == "small":
            action = self.pending_actions.get(team, {})
            action["path"] = self._normalize_move_plan(actor, action.get("path", []), max_steps=10)
        elif key == "speed_star" and skill_tier == "medium":
            action = self.pending_actions.get(team, {})
            action["path"] = self._normalize_move_plan(actor, action.get("path", []), max_steps=10)
        elif key == "speed_star" and skill_tier == "large":
            action = self.pending_actions.get(team, {})
            direction = str(action.get("skill_direction") or "")
            distance = int(action.get("skill_distance") or 0)
            action["path"] = self._build_straight_path(actor.cell, direction, distance) or self._normalize_move_plan(actor, action.get("path", []), max_steps=self.board_size)
        elif key == "spiritualist" and skill_tier == "small":
            for unit in self.units.values():
                if unit.owner == team and unit.alive:
                    unit.vision_bonus = max(unit.vision_bonus, actor.effective_vision)
        elif key == "spiritualist" and skill_tier == "medium":
            enemy_actor = self._current_actor(self._enemy_of(team))
            if enemy_actor:
                enemy_actor.bound = True
        elif key == "spiritualist" and skill_tier == "large":
            self._damage_visible_enemy(actor, team, 100)
        elif key == "archer" and skill_tier == "small":
            self._damage_visible_enemy(actor, team, 1)
        elif key == "archer" and skill_tier == "medium":
            self._damage_visible_enemy(actor, team, 2)
        elif key == "archer" and skill_tier == "large":
            self._damage_visible_enemy(actor, team, 9999)
        elif key == "soldier" and skill_tier == "small":
            self._damage_adjacent_enemy(actor, team, max(1, actor.max_hp // 3))
        elif key == "soldier" and skill_tier == "medium":
            actor.hp = min(actor.max_hp, actor.hp + 1)
        elif key == "soldier" and skill_tier == "large":
            if actor.hp <= 5:
                actor.hp = 30
                actor.move_bonus = max(actor.move_bonus, 10)
        elif key == "leader" and skill_tier == "small":
            self._damage_visible_enemy(actor, team, max(1, actor.max_hp // 5))
        elif key == "leader" and skill_tier == "medium":
            actor.cost += 2
        elif key == "leader" and skill_tier == "large":
            action = self.pending_actions.get(team, {})
            path = action.get("path", [])
            if path:
                actor.cell = path[-1]
                action["path"] = []
        elif key == "saint" and skill_tier == "small":
            actor.reflect_ratio = 0.1
        elif key == "saint" and skill_tier == "medium":
            actor.hp = min(actor.max_hp, actor.hp + 3)
        elif key == "saint" and skill_tier == "large":
            actor.true_sight = True
        elif key == "psychic" and skill_tier == "small":
            actor.vision_bonus += 3
        elif key == "psychic" and skill_tier == "medium":
            actor.cell = (random.randrange(self.board_size), random.randrange(self.board_size))
        elif key == "psychic" and skill_tier == "large":
            for unit in self.units.values():
                if unit.alive:
                    self._apply_damage(actor, unit, 2, team, allow_reflect=False)
        elif key == "samurai" and skill_tier == "small":
            self._damage_enemy_in_range(actor, team, 3, max(1, actor.max_hp // 3))
        elif key == "samurai" and skill_tier == "medium":
            self._damage_visible_enemy(actor, team, max(1, actor.max_hp // 2))
        elif key == "samurai" and skill_tier == "large":
            actor.guard_radius = 1
        elif key == "berserker" and skill_tier == "small":
            self._damage_same_cell_enemy(actor, team, actor.max_hp)
        elif key == "berserker" and skill_tier == "medium":
            actor.hp = max(1, actor.hp - 5)
            actor.move_bonus += actor.move
        elif key == "berserker" and skill_tier == "large":
            actor.hp = max(1, actor.hp // 2)
            self._damage_enemy_in_range(actor, team, 2, max(1, actor.max_hp // 2))
        elif key == "beastmaster" and skill_tier == "small":
            action = self.pending_actions.get(team, {})
            action["path"] = self._normalize_move_plan(actor, action.get("path", []), max_steps=10)
        elif key == "beastmaster" and skill_tier == "medium":
            enemy_actor = self._current_actor(self._enemy_of(team))
            if enemy_actor:
                self.players[team].known_floor.add(enemy_actor.cell)
                self.players[team].known_coins.discard(enemy_actor.cell)
        elif key == "beastmaster" and skill_tier == "large":
            self.players[team].coins += 1

    def _apply_contact_skills(self, actor: UnitState, team: str, previous_cell: Optional[Cell] = None) -> None:
        if actor.character_key == "beastmaster":
            self._destroy_enemy_flag_at(team, actor.cell)
            for unit in self.units.values():
                if unit.owner != team and unit.alive and self._manhattan(actor.cell, unit.cell) == 1:
                    self._apply_damage(actor, unit, 4, team)
        if actor.character_key == "speed_star" and self.pending_actions.get(team, {}).get("skill_tier") == "medium":
            self._damage_same_cell_enemy(actor, team, max(1, actor.max_hp // 5))
        if actor.character_key == "speed_star" and self.pending_actions.get(team, {}).get("skill_tier") == "large":
            self._destroy_enemy_flag_at(team, actor.cell)
            for unit in self.units.values():
                if unit.owner != team and unit.alive and unit.cell == actor.cell:
                    self._apply_damage(actor, unit, unit.hp, team)
            self._apply_speed_star_large_side_damage(actor, team, previous_cell)

    def _apply_speed_star_large_side_damage(self, actor: UnitState, team: str, previous_cell: Optional[Cell]) -> None:
        if previous_cell is None:
            return
        dx = actor.cell[0] - previous_cell[0]
        dy = actor.cell[1] - previous_cell[1]
        if dx == 0 and dy == 0:
            return
        side_vectors = [(0, 1), (0, -1)] if dx else [(1, 0), (-1, 0)]
        damage = max(1, actor.max_hp // 2)
        for sx, sy in side_vectors:
            for distance in (1, 2):
                side_cell = (actor.cell[0] + sx * distance, actor.cell[1] + sy * distance)
                self._destroy_enemy_flag_at(team, side_cell)
                for unit in self.units.values():
                    if unit.owner != team and unit.alive and unit.cell == side_cell:
                        self._apply_damage(actor, unit, damage, team)

    def _apply_post_move_skills(self, actors: Dict[str, Optional[UnitState]]) -> None:
        for team, actor in actors.items():
            if actor is None or not actor.alive:
                continue
            tier = self.pending_actions.get(team, {}).get("skill_tier") or ""
            if actor.character_key == "speed_star" and tier == "medium":
                continue

    def _apply_reactive_skills(self, actors: Dict[str, Optional[UnitState]]) -> None:
        for team, actor in actors.items():
            if actor is None or not actor.alive:
                continue
            if actor.character_key == "archer" and self.pending_actions.get(team, {}).get("skill_tier") == "small":
                self._damage_visible_enemy(actor, team, 1)
            if actor.character_key == "archer" and self.pending_actions.get(team, {}).get("skill_tier") == "medium":
                self._damage_visible_enemy(actor, team, 2)
            if actor.guard_radius > 0:
                for unit in self.units.values():
                    if unit.owner != team and unit.alive and self._manhattan(actor.cell, unit.cell) <= actor.guard_radius:
                        self._apply_damage(actor, unit, unit.hp, team)

    def _apply_damage(
        self,
        attacker: Optional[UnitState],
        target: UnitState,
        amount: int,
        attacker_team: str,
        *,
        allow_reflect: bool = True,
    ) -> None:
        if amount <= 0 or not target.alive:
            return
        target.hp -= amount
        if target.hp <= 0:
            self._kill_unit(target, attacker_team)
        if (
            allow_reflect
            and attacker
            and attacker.alive
            and target.alive
            and target.reflect_ratio > 0
            and attacker.owner != target.owner
        ):
            reflected = max(1, math.ceil(amount * target.reflect_ratio))
            self._apply_damage(None, attacker, reflected, target.owner, allow_reflect=False)

    def _damage_visible_enemy(self, actor: UnitState, team: str, amount: int) -> None:
        visible = self._vision_from(actor.cell, actor.effective_vision if not actor.true_sight else self.board_size)
        targets = [
            unit for unit in self.units.values()
            if unit.owner != team and unit.alive and tuple(unit.cell) in visible
        ]
        if not targets:
            flags = [flag for flag in self.flags.values() if flag.alive and flag.team != team and tuple(flag.cell) in visible]
            if flags:
                target_flag = min(flags, key=lambda flag: self._manhattan(actor.cell, flag.cell))
                self._destroy_enemy_flag_at(team, target_flag.cell)
            return
        target = min(targets, key=lambda unit: self._manhattan(actor.cell, unit.cell))
        self._apply_damage(actor, target, amount, team)

    def _damage_adjacent_enemy(self, actor: UnitState, team: str, amount: int) -> None:
        self._destroy_enemy_flags_in_cells(
            team,
            (
                (actor.cell[0] + dx, actor.cell[1] + dy)
                for dx in (-1, 0, 1)
                for dy in (-1, 0, 1)
                if dx != 0 or dy != 0
            ),
        )
        for unit in self.units.values():
            if unit.owner != team and unit.alive and self._manhattan(actor.cell, unit.cell) <= 1:
                self._apply_damage(actor, unit, amount, team)
                return

    def _damage_enemy_in_range(self, actor: UnitState, team: str, radius: int, amount: int) -> None:
        self._destroy_enemy_flags_in_cells(
            team,
            (
                (x, y)
                for x in range(actor.cell[0] - radius, actor.cell[0] + radius + 1)
                for y in range(actor.cell[1] - radius, actor.cell[1] + radius + 1)
                if self._in_bounds((x, y)) and self._manhattan(actor.cell, (x, y)) <= radius
            ),
        )
        targets = [
            unit for unit in self.units.values()
            if unit.owner != team and unit.alive and self._manhattan(actor.cell, unit.cell) <= radius
        ]
        if not targets:
            return
        target = min(targets, key=lambda unit: self._manhattan(actor.cell, unit.cell))
        self._apply_damage(actor, target, amount, team)

    def _damage_same_cell_enemy(self, actor: UnitState, team: str, amount: int) -> None:
        self._destroy_enemy_flag_at(team, actor.cell)
        for unit in self.units.values():
            if unit.owner != team and unit.alive and unit.cell == actor.cell:
                self._apply_damage(actor, unit, amount, team)

    def _current_actor_id(self, team: str) -> str:
        player = self.players.get(team)
        if not player or not player.priority:
            return ""
        key = player.priority[(self.round_number - 1) % len(player.priority)]
        return f"{team}:{key}"

    def _current_actor(self, team: str) -> Optional[UnitState]:
        actor_id = self._current_actor_id(team)
        actor = self.units.get(actor_id)
        if actor and actor.alive:
            return actor
        return None

    def _visible_cells_for_viewer(self, viewer_symbol: str) -> Set[Cell]:
        actor = self._current_actor(viewer_symbol)
        if actor is None:
            return set()
        if actor.true_sight:
            return {(x, y) for y in range(self.board_size) for x in range(self.board_size)}
        return self._vision_from(actor.cell, actor.effective_vision)

    def _remember_all_visible(self) -> None:
        for team in TEAM_SYMBOLS:
            self._remember_visible_for(team)

    def _remember_visible_for(self, team: str) -> None:
        actor = self._current_actor(team)
        if actor is None:
            return
        visible = self._vision_from(actor.cell, actor.effective_vision)
        player = self.players[team]
        for flag in self.flags.values():
            player.known_floor.add(flag.cell)
        for unit in self.units.values():
            if unit.owner == team:
                player.known_floor.add(unit.cell)
        for cell in visible:
            player.known_floor.add(cell)
            if cell in self.walls:
                player.known_walls.add(cell)
            if cell in self.lava:
                player.known_lava.add(cell)
            if cell in self.coins:
                player.known_coins.add(cell)
            else:
                player.known_coins.discard(cell)

    def _seed_initial_memory(self) -> None:
        for team in TEAM_SYMBOLS:
            player = self.players[team]
            for flag in self.flags.values():
                player.known_floor.add(flag.cell)
            for unit in self.units.values():
                if unit.owner == team:
                    player.known_floor.add(unit.cell)
            self._remember_visible_for(team)

    def _snapshot_frame(self) -> dict:
        return {
            "units": {
                unit_id: {
                    "id": unit.id,
                    "owner": unit.owner,
                    "character_key": unit.character_key,
                    "name": unit.display_name,
                    "cell": [unit.cell[0], unit.cell[1]],
                    "alive": unit.alive,
                    "hp": unit.hp,
                    "cost": unit.cost,
                }
                for unit_id, unit in self.units.items()
            },
            "coins": [list(cell) for cell in sorted(self.coins)],
            "flags": {
                flag.id: {"id": flag.id, "team": flag.team, "cell": [flag.cell[0], flag.cell[1]], "alive": flag.alive}
                for flag in self.flags.values()
            },
        }

    def _viewer_replay_frames(self, viewer_symbol: str) -> List[dict]:
        if not viewer_symbol or not self.last_replay_frames:
            return []
        frames: List[dict] = []
        actor_id = self._current_actor_id(viewer_symbol)
        for frame in self.last_replay_frames:
            actor_payload = frame["units"].get(actor_id)
            if actor_payload and actor_payload["alive"]:
                origin = (actor_payload["cell"][0], actor_payload["cell"][1])
                vision = self.units[actor_id].effective_vision if actor_id in self.units else 1
                visible = self._vision_from(origin, vision)
            else:
                visible = set()
            units_payload = {}
            for unit_id, payload in frame["units"].items():
                cell = (payload["cell"][0], payload["cell"][1])
                if payload["owner"] == viewer_symbol or cell in visible:
                    units_payload[unit_id] = payload
            frames.append(
                {
                    "units": units_payload,
                    "visible_cells": [list(cell) for cell in sorted(visible)],
                    "coins": frame["coins"],
                    "flags": list(frame["flags"].values()),
                }
            )
        return frames

    def _viewer_units_payload(
        self,
        viewer_symbol: str,
        visible_cells: Set[Cell],
        replay_units: Optional[dict] = None,
    ) -> dict:
        source_units = replay_units or {
            unit_id: {
                "id": unit.id,
                "owner": unit.owner,
                "character_key": unit.character_key,
                "name": unit.display_name,
                "cell": [unit.cell[0], unit.cell[1]],
                "alive": unit.alive,
                "hp": unit.hp,
                "cost": unit.cost,
            }
            for unit_id, unit in self.units.items()
        }
        payload = {}
        for unit_id, item in source_units.items():
            cell = (item["cell"][0], item["cell"][1])
            if item["owner"] != viewer_symbol and cell not in visible_cells:
                continue
            unit_state = self.units.get(unit_id)
            character = CHARACTERS.get(item["character_key"])
            payload[unit_id] = {
                "id": unit_id,
                "owner": item["owner"],
                "character_key": item["character_key"],
                "name": item["name"],
                "cell": item["cell"],
                "alive": item["alive"],
                "hp": item["hp"],
                "max_hp": unit_state.max_hp if unit_state else character.power if character else item["hp"],
                "cost": item["cost"],
                "move": unit_state.effective_move if unit_state else character.move if character else 0,
                "vision": unit_state.effective_vision if unit_state else character.vision if character else 1,
                "small": self._skill_payload(character.small) if character else None,
                "medium": self._skill_payload(character.medium) if character else None,
                "large": self._skill_payload(character.large) if character else None,
            }
        return payload

    def _character_catalog_payload(self, character: CharacterDef) -> dict:
        return {
            "key": character.key,
            "name": character.name,
            "move": character.move,
            "power": character.power,
            "vision": character.vision,
            "small": self._skill_payload(character.small),
            "medium": self._skill_payload(character.medium),
            "large": self._skill_payload(character.large),
            "memo": character.memo,
        }

    @staticmethod
    def _skill_payload(skill: SkillDef) -> dict:
        return {
            "key": skill.key,
            "name": skill.name,
            "cost": skill.cost,
            "description": skill.description,
        }

    def _vision_from(self, origin: Cell, radius: int) -> Set[Cell]:
        visible: Set[Cell] = set()
        ox, oy = origin
        for y in range(max(0, oy - 7), min(self.board_size, oy + 8)):
            for x in range(max(0, ox - 7), min(self.board_size, ox + 8)):
                cell = (x, y)
                dx = origin[0] - cell[0]
                dy = origin[1] - cell[1]
                if (dx * dx + dy * dy) ** 0.5 > radius:
                    continue
                if self._line_of_sight(origin, cell):
                    visible.add(cell)
        return visible

    def _line_of_sight(self, start: Cell, end: Cell) -> bool:
        points = self._bresenham(start, end)
        for point in points[1:-1]:
            if point in self.walls:
                return False
        return True

    def _generate_spawn_cells(self, total: int) -> List[Cell]:
        cells: List[Cell] = []
        attempts = 0
        blocked = self.walls | self.lava
        while len(cells) < total and attempts < 20000:
            attempts += 1
            candidate = (random.randrange(self.board_size), random.randrange(self.board_size))
            if candidate in blocked:
                continue
            if any(self._manhattan(candidate, other) < MIN_SPAWN_DISTANCE for other in cells):
                continue
            cells.append(candidate)
        if len(cells) < total:
            raise GameError("初期配置を正常に作れませんでした。")
        return cells

    def _spawn_coins(self) -> None:
        self.coins = set()
        target_count = sum(len(self.players[team].selected_keys) for team in TEAM_SYMBOLS)
        blocked = self.walls | self.lava | {flag.cell for flag in self.flags.values()}
        blocked |= {unit.cell for unit in self.units.values() if unit.alive}
        attempts = 0
        while len(self.coins) < target_count and attempts < 20000:
            attempts += 1
            cell = (random.randrange(self.board_size), random.randrange(self.board_size))
            if cell in blocked:
                continue
            self.coins.add(cell)

    def _generate_walls(self, field_type: str) -> Set[Cell]:
        count = {"grassland": 120, "maze": 520, "volcano": 180}[field_type]
        cells: Set[Cell] = set()
        while len(cells) < count:
            x = random.randrange(self.board_size)
            y = random.randrange(self.board_size)
            if field_type == "maze":
                length = random.randint(2, 6)
                horizontal = random.random() < 0.5
                for index in range(length):
                    cell = (x + index, y) if horizontal else (x, y + index)
                    if self._in_bounds(cell):
                        cells.add(cell)
            else:
                cells.add((x, y))
        return cells

    def _generate_lava(self, field_type: str) -> Set[Cell]:
        if field_type != "volcano":
            return set()
        cells: Set[Cell] = set()
        while len(cells) < 180:
            cells.add((random.randrange(self.board_size), random.randrange(self.board_size)))
        return cells

    def _all_cells(self) -> Iterable[Cell]:
        for x in range(self.board_size):
            for y in range(self.board_size):
                yield (x, y)

    def _enemy_of(self, team: str) -> str:
        return "B" if team == "A" else "A"

    @staticmethod
    def _manhattan(a: Cell, b: Cell) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.board_size and 0 <= cell[1] < self.board_size

    @staticmethod
    def _bresenham(start: Cell, end: Cell) -> List[Cell]:
        x0, y0 = start
        x1, y1 = end
        points: List[Cell] = []
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return points
