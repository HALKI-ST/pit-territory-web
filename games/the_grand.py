from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from games.the_grand_old import TheGrandOldGame


TEAM_SYMBOLS = ("A", "B")


class GameError(ValueError):
    pass


FIELD_OPTIONS = (
    {"key": "grassland", "name": "草原", "summary": "見通しのよい標準フィールドです。"},
    {"key": "maze", "name": "迷宮", "summary": "壁が多く、視界共有と位置取りが重要です。"},
    {"key": "volcano", "name": "火山", "summary": "危険地形が点在する荒れたフィールドです。"},
    {"key": "debug_lab", "name": "お試し部屋", "summary": "本編ではなく、技検証用のデバッグ部屋です。"},
)


def skill(name: str, cost: int, description: str) -> dict:
    return {"name": name, "cost": cost, "description": description}


CHARACTERS = [
    {
        "key": "speed_star",
        "role": "スピードスター",
        "name": "スピードスター",
        "move": 0,
        "power": 10,
        "vision": 3,
        "summary": "機械の身体に閉じ込められても速さを求め続ける。",
        "small": skill("ダッシュ", 1, "技で移動する。10マスまで移動する。"),
        "medium": skill("ブーストバスター", 3, "技で移動する。10マスまで移動し、重なった敵に戦闘力/5ダメージ。"),
        "large": skill("ソニックスター", 4, "技で移動する。方向と距離を入力して一直線に突進する。"),
    },
    {
        "key": "spiritualist",
        "role": "霊能力者",
        "name": "ミャーノ・マーリー",
        "move": 3,
        "power": 4,
        "vision": 5,
        "summary": "呪いとともに戦う霊能力者。",
        "small": skill("サウザンド・アイ", 2, "このセット中、味方の視界を共有する。"),
        "medium": skill("ゴールド・バインド", 3, "指定した敵が次に動くときの行動を封じる。"),
        "large": skill("ハンドレッド・ナイト", 4, "追尾する幽霊を放つ。"),
    },
    {
        "key": "archer",
        "role": "弓兵",
        "name": "アチャ爺",
        "move": 6,
        "power": 9,
        "vision": 5,
        "summary": "近代兵器に屈しない老兵の弓兵。",
        "small": skill("通常射出", 2, "移動しながら、見つけた敵を撃ち続ける。"),
        "medium": skill("中距離曲射", 3, "移動不可。捕捉した敵へ継続ダメージを狙う。"),
        "large": skill("超遠距離攻撃", 5, "指定した狙点を通る直線上の一番近い相手を撃ち抜く。"),
    },
    {
        "key": "soldier",
        "role": "雑兵",
        "name": "レオ・アレクス",
        "move": 5,
        "power": 10,
        "vision": 3,
        "summary": "勇者の血を引く雑兵。",
        "small": skill("剣技", 1, "移動中を含め、八方向1マスに入った最初の相手1体だけを斬る。"),
        "medium": skill("弱者の祈り", 3, "視界内の味方全員を1回復する。"),
        "large": skill("主人公補正", 5, "追い詰められるほど覚醒する。"),
    },
    {
        "key": "leader",
        "role": "リーダー",
        "name": "ヴァン・クラリッサ",
        "move": 7,
        "power": 15,
        "vision": 4,
        "summary": "苛烈な戦場を生き残り続ける指揮官。",
        "small": skill("通常業務", 1, "そのターン中に新しく視界へ入った敵だけを撃つ。"),
        "medium": skill("再構成", 3, "残りターンの担当キャラを自由に組み直す。"),
        "large": skill("再配置", 5, "味方を、いま味方がいる位置へ再配置する。"),
    },
    {
        "key": "saint",
        "role": "聖女",
        "name": "アリア",
        "move": 5,
        "power": 1000,
        "vision": 1,
        "summary": "聖布で目を隠した聖女。",
        "small": skill("リフレクト", 1, "完全な反射。次に自分の番が来るまで有効。"),
        "medium": skill("聖女の祈り", 2, "満タンでない味方1体をランダムに+3回復する。"),
        "large": skill("見通す目", 3, "このセット中、アリアの手番では全体を把握できる。"),
    },
    {
        "key": "psychic",
        "role": "サイキッカー",
        "name": "白星 夢",
        "move": 4,
        "power": 5,
        "vision": 5,
        "summary": "明るく危ういサイキッカー。",
        "small": skill("フラッシュ", 1, "移動不可。半径5マス以内の相手へ3ダメージ、自分は1ダメージ。"),
        "medium": skill("テレポート", 2, "ランダムな空きマスへ移動する。"),
        "large": skill("ブラックホール", 4, "自分以外に距離別ダメージを与える。"),
    },
    {
        "key": "samurai",
        "role": "侍",
        "name": "櫻井 光二郎",
        "move": 7,
        "power": 10,
        "vision": 4,
        "summary": "抜く前に勝負を決める居合の達人。",
        "small": skill("間合い", 1, "3マス圏の敵へ斬撃を飛ばす。"),
        "medium": skill("空の間合い", 2, "視界に入ってきたものへ斬撃を飛ばす。"),
        "large": skill("極の間合い", 5, "次の自分の番まで、近付いたものを弾く。"),
    },
    {
        "key": "berserker",
        "role": "バーサーカー",
        "name": "ニック",
        "move": 2,
        "power": 100,
        "vision": 2,
        "summary": "鎖と識別刻印を残した実験体。",
        "small": skill("ホショク", 1, "捕食圏内の相手を押し潰す。"),
        "medium": skill("シュンソク", 2, "体力を削って加速する。"),
        "large": skill("バーサーク", 3, "捕食圏を広げる。"),
    },
    {
        "key": "beastmaster",
        "role": "獣使い",
        "name": "メイ・スフィン",
        "move": 5,
        "power": 5,
        "vision": 3,
        "summary": "動物と絆を結ぶ獣使い。",
        "small": skill("獅子ライド", 2, "移動中に重なった敵へ4ダメージ。"),
        "medium": skill("バードリスニング", 3, "その時点の敵位置を手掛かりとして記録する。"),
        "large": skill("ハムマッチ", 4, "ハムスターを召喚し、操作できるようにする。"),
    },
]

CHARACTER_BY_KEY = {entry["key"]: entry for entry in CHARACTERS}


@dataclass
class GrandPlayer:
    symbol: str
    name: str
    connected: bool = False
    selected_keys: List[str] = field(default_factory=list)
    roster_confirmed: bool = False
    order: List[str] = field(default_factory=list)
    order_confirmed: bool = False

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "selected_keys": list(self.selected_keys),
            "roster_confirmed": self.roster_confirmed,
            "order": list(self.order),
            "order_confirmed": self.order_confirmed,
        }


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
        self.players: Dict[str, GrandPlayer] = {
            symbol: GrandPlayer(symbol=symbol, name=f"Player {symbol}")
            for symbol in TEAM_SYMBOLS
        }
        self.phase = "waiting"
        self.started = False
        self.game_over = False
        self.message = "2プレイヤーが揃うまで待機中です。"
        self.winner_text = ""
        self.field_type = ""
        self.set_number = 1
        self.turn_number = 1
        self.legacy_battle: TheGrandOldGame | None = None

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
            cleaned = (name or f"Player {symbol}").strip()
            self.players[symbol].name = cleaned[:24] or f"Player {symbol}"
        if self.legacy_battle is not None:
            self.legacy_battle.set_player_name(symbol, name)

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected
        if self.legacy_battle is not None:
            self.legacy_battle.update_connection(symbol, connected)
        self.start_if_ready()

    def joined_count(self) -> int:
        return sum(1 for player in self.players.values() if player.connected)

    def start_if_ready(self) -> None:
        if self.joined_count() >= 2:
            if self.phase == "waiting":
                self.message = "両プレイヤーが揃いました。部屋主はフィールド選択へ進めます。"
        elif self.phase == "waiting":
            self.message = "2プレイヤーが揃うまで待機中です。"

    def _clean_selected_keys(self, selected_keys: List[str]) -> List[str]:
        seen = set()
        cleaned: List[str] = []
        for key in selected_keys:
            if key in CHARACTER_BY_KEY and key not in seen:
                seen.add(key)
                cleaned.append(key)
        return cleaned[:10]

    def _sync_from_legacy(self) -> None:
        if self.legacy_battle is None:
            return
        self.phase = self.legacy_battle.phase
        self.started = self.legacy_battle.started
        self.game_over = self.legacy_battle.game_over
        self.message = self.legacy_battle.message
        self.winner_text = self.legacy_battle.winner_text
        self.field_type = self.legacy_battle.field_type
        self.set_number = self.legacy_battle.set_number
        self.turn_number = self.legacy_battle.round_number

    def _start_legacy_mode(self, field_type: str) -> None:
        legacy = TheGrandOldGame()
        for symbol in TEAM_SYMBOLS:
            legacy.players[symbol].name = self.players[symbol].name
            legacy.players[symbol].connected = self.players[symbol].connected
            legacy.players[symbol].selected_keys = list(self.players[symbol].selected_keys)
            legacy.players[symbol].priority = list(self.players[symbol].order or self.players[symbol].selected_keys)
            legacy.players[symbol].roster_confirmed = True
            legacy.players[symbol].order_confirmed = True
        legacy.field_type = field_type
        if field_type == "debug_lab":
            legacy.phase = "field_select"
            legacy._confirm_field({"field_type": field_type})
        else:
            legacy._build_match_state()
            legacy._begin_battle()
        self.legacy_battle = legacy
        self._sync_from_legacy()

    def handle_action(self, symbol: str, action: str, payload: dict | None = None) -> None:
        payload = payload or {}
        settings = payload.get("settings") or {}

        if self.phase in {"battle", "order_select", "lab"} and self.legacy_battle is not None:
            if action in {"submit_turn", "confirm_result", "resign", "rematch", "confirm_order", "update_setup"}:
                self.legacy_battle.apply_player_action(symbol, action, settings=settings)
                self._sync_from_legacy()
                return

        if action == "advance_phase":
            if self.phase != "waiting":
                raise GameError("この操作は現在の段階では使えません。")
            if self.joined_count() < 2:
                raise GameError("両プレイヤーが揃ってから進めてください。")
            self.phase = "field_select"
            self.message = "フィールドを1つ選んでください。"
            return

        if action == "confirm_field":
            if self.phase != "field_select":
                raise GameError("まだフィールド選択の段階ではありません。")
            field_type = settings.get("field_type", "")
            valid_keys = {option["key"] for option in FIELD_OPTIONS}
            if field_type not in valid_keys:
                raise GameError("有効なフィールドを選んでください。")
            self.field_type = field_type
            if field_type == "debug_lab":
                self._start_legacy_mode(field_type)
            else:
                self.phase = "character_select"
                self.message = "キャラクターを選んで編成を決めてください。"
            return

        if action == "update_setup":
            if self.phase != "character_select":
                raise GameError("いまはキャラ編成の段階ではありません。")
            player = self.players[symbol]
            player.selected_keys = self._clean_selected_keys(list(settings.get("selected_keys") or []))
            player.roster_confirmed = False
            player.order = []
            player.order_confirmed = False
            return

        if action == "confirm_roster":
            if self.phase != "character_select":
                raise GameError("まだ編成確定の段階ではありません。")
            player = self.players[symbol]
            if not player.selected_keys:
                raise GameError("少なくとも1体は選んでください。")
            player.roster_confirmed = True
            if all(self.players[team].roster_confirmed for team in TEAM_SYMBOLS):
                self.phase = "order_select"
                for team in TEAM_SYMBOLS:
                    if not self.players[team].order:
                        self.players[team].order = list(self.players[team].selected_keys)
                self.message = "行動順を確定してください。"
            else:
                self.message = "相手の編成確定を待っています。"
            return

        if action == "confirm_order":
            if self.phase != "order_select":
                raise GameError("まだ行動順設定の段階ではありません。")
            player = self.players[symbol]
            order = list(settings.get("priority") or [])
            if sorted(order) != sorted(player.selected_keys):
                raise GameError("行動順には選択したキャラクターをちょうど1回ずつ入れてください。")
            player.order = order
            player.order_confirmed = True
            if all(self.players[team].order_confirmed for team in TEAM_SYMBOLS):
                self._start_legacy_mode(self.field_type or "grassland")
            else:
                self.message = "相手の行動順確定を待っています。"
            return

        raise GameError("未対応の操作です。")

    def apply_host_action(self, action: str, settings: dict | None = None, **_: object) -> None:
        self.handle_action("A", action, {"settings": settings or {}})

    def apply_player_action(self, symbol: str, action: str, settings: dict | None = None, **_: object) -> None:
        self.handle_action(symbol, action, {"settings": settings or {}})

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        if self.legacy_battle is not None and self.phase in {"battle", "order_select", "lab"}:
            payload = self.legacy_battle.to_public_dict(viewer_symbol)
            for player in (payload.get("players") or {}).values():
                if "priority" in player and "order" not in player:
                    player["order"] = list(player.get("priority") or [])
            payload["game_type"] = self.game_type
            payload["title"] = self.title
            payload["subtitle"] = self.subtitle
            payload["field_options"] = list(FIELD_OPTIONS)
            return payload

        return {
            "game_type": self.game_type,
            "title": self.title,
            "subtitle": self.subtitle,
            "phase": self.phase,
            "started": self.started,
            "game_over": self.game_over,
            "message": self.message,
            "winner_text": self.winner_text,
            "field_type": self.field_type,
            "field_options": list(FIELD_OPTIONS),
            "catalog": list(CHARACTERS),
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
            "viewer_symbol": viewer_symbol,
            "host_symbol": "A",
            "set_number": self.set_number,
            "turn_number": self.turn_number,
        }
