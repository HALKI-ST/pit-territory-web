from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


SEAT_ORDER = ["A", "B"]
COLORS = [
    ("red", "赤"),
    ("blue", "青"),
    ("green", "緑"),
    ("yellow", "黄"),
    ("purple", "紫"),
    ("orange", "橙"),
]
FLAG_COUNT = 9


@dataclass
class BattleLinePlayer:
    symbol: str
    name: str
    connected: bool = False
    hand: List[dict] | None = None

    def __post_init__(self) -> None:
        if self.hand is None:
            self.hand = []

    def public_summary(self, include_hand: bool = False) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "hand_count": len(self.hand),
            "hand": [card.copy() for card in self.hand] if include_hand else [],
        }


class BattleLineGame:
    game_type = "battle_line"
    title = "戦線"
    subtitle = "2人で9本の旗を奪い合う陣形勝負。3連取または合計5本先取で勝利です。"
    category = "classic"
    min_players = 2
    max_players = 2
    player_label = "2人"
    seat_order = list(SEAT_ORDER)
    allow_midgame_join = False
    host_control_actions = {"start_match"}

    def __init__(self) -> None:
        self.players: Dict[str, BattleLinePlayer] = {}
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.turn = "A"
        self.deck: List[dict] = []
        self.flags: List[dict] = [self._new_flag(index) for index in range(FLAG_COUNT)]
        self.claimed_flags: Dict[str, List[int]] = {"A": [], "B": []}
        self.winner_text = ""
        self.message = "2人そろったら部屋主が開始してください。"
        self.history: List[str] = []
        self.play_counter = 0

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
        cleaned = (name or "").strip() or symbol
        existing = self.players.get(symbol)
        if existing:
            existing.name = cleaned[:24]
        else:
            self.players[symbol] = BattleLinePlayer(symbol=symbol, name=cleaned[:24])
        if not self.started:
            self.message = "2人そろったら部屋主が開始してください。"

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        if not self.started:
            self.message = (
                "部屋主が開始すると対戦が始まります。"
                if len(self.joined_symbols()) >= self.min_players
                else "2人そろうと開始できます。"
            )

    def reset_for_rematch(self) -> None:
        saved = {
            symbol: (player.name, player.connected)
            for symbol, player in self.players.items()
        }
        self.__init__()
        for symbol, (name, connected) in saved.items():
            self.players[symbol] = BattleLinePlayer(symbol=symbol, name=name, connected=connected)
        self.start_if_ready()

    def apply_host_action(self, action: str, **_: object) -> None:
        if action == "start_match":
            self.start_match()
            return
        raise GameError("未対応のホスト操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        card_index: Optional[int] = None,
        selected_cards: Optional[List[int]] = None,
        **_: object,
    ) -> None:
        if action == "resign":
            self._resign(symbol)
            return
        if action != "play_card":
            raise GameError("未対応の操作です。")
        self._play_card(symbol, card_index, selected_cards)

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("2人そろってから開始してください。")

        self.started = True
        self.game_over = False
        self.phase = "playing"
        self.turn = random.choice(SEAT_ORDER)
        self.deck = self._build_deck()
        self.flags = [self._new_flag(index) for index in range(FLAG_COUNT)]
        self.claimed_flags = {"A": [], "B": []}
        self.winner_text = ""
        self.history = []
        self.play_counter = 0
        for player in self.players.values():
            player.hand = []
        for _ in range(7):
            for symbol in SEAT_ORDER:
                self._draw_to_hand(symbol)
        self.message = f"{self.players[self.turn].name} の手番です。旗にカードを1枚出してください。"
        self.history.append("ゲーム開始。9本の旗を取り合います。")

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        flags_payload = []
        for flag in self.flags:
            flags_payload.append(
                {
                    "index": flag["index"],
                    "claimed_by": flag["claimed_by"],
                    "cards": {
                        symbol: [card.copy() for card in flag["cards"][symbol]]
                        for symbol in SEAT_ORDER
                    },
                    "formation": {
                        symbol: self._formation_label(flag["cards"][symbol])
                        if len(flag["cards"][symbol]) == 3
                        else ""
                        for symbol in SEAT_ORDER
                    },
                }
            )

        player_payload = {}
        for symbol in SEAT_ORDER:
            player = self.players.get(symbol)
            if not player:
                continue
            player_payload[symbol] = player.public_summary(include_hand=symbol == viewer_symbol)

        viewer_hand = []
        if viewer_symbol in self.players:
            viewer_hand = [card.copy() for card in self.players[viewer_symbol].hand]

        return {
            "title": self.title,
            "game_type": self.game_type,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "turn": self.turn,
            "message": self.message,
            "winner_text": self.winner_text,
            "deck_count": len(self.deck),
            "flags": flags_payload,
            "claimed_flags": {symbol: sorted(indices) for symbol, indices in self.claimed_flags.items()},
            "players": player_payload,
            "player_order": [symbol for symbol in SEAT_ORDER if symbol in self.players],
            "viewer_hand": viewer_hand,
            "history": list(self.history),
        }

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in SEAT_ORDER if symbol in self.players]

    def _play_card(
        self,
        symbol: str,
        card_index: Optional[int],
        selected_cards: Optional[List[int]],
    ) -> None:
        if not self.started or self.game_over:
            raise GameError("まだゲーム中ではありません。")
        if symbol != self.turn:
            raise GameError("自分の手番ではありません。")

        hand = self.players.get(symbol)
        if not hand:
            raise GameError("プレイヤー情報が見つかりません。")

        chosen_flag = None
        if selected_cards:
            try:
                chosen_flag = int(selected_cards[0])
            except (TypeError, ValueError):
                chosen_flag = None
        if chosen_flag is None:
            raise GameError("出す旗を選んでください。")
        if chosen_flag < 0 or chosen_flag >= FLAG_COUNT:
            raise GameError("旗の場所が不正です。")

        if card_index is None:
            raise GameError("手札のカードを選んでください。")
        card_index = int(card_index)
        if card_index < 0 or card_index >= len(hand.hand):
            raise GameError("カードが見つかりません。")

        flag = self.flags[chosen_flag]
        if flag["claimed_by"]:
            raise GameError("その旗はすでに取られています。")
        if len(flag["cards"][symbol]) >= 3:
            raise GameError("その旗にはもう3枚置いています。")

        card = hand.hand.pop(card_index)
        flag["cards"][symbol].append(card)
        self.play_counter += 1
        if len(flag["cards"][symbol]) == 3:
            flag["completed_at"][symbol] = self.play_counter

        self.history.append(f"{self.players[symbol].name} が旗 {chosen_flag + 1} に {self._card_label(card)} を配置。")
        self._draw_to_hand(symbol)
        self._resolve_claims()

        if self.game_over:
            return

        self.turn = self._other_symbol(symbol)
        self.message = f"{self.players[self.turn].name} の手番です。"

    def _resolve_claims(self) -> None:
        newly_claimed: List[str] = []
        for flag in self.flags:
            if flag["claimed_by"]:
                continue
            a_cards = flag["cards"]["A"]
            b_cards = flag["cards"]["B"]
            if len(a_cards) < 3 or len(b_cards) < 3:
                continue

            winner = self._compare_formations(a_cards, b_cards, flag["completed_at"])
            flag["claimed_by"] = winner
            self.claimed_flags[winner].append(flag["index"])
            newly_claimed.append(f"{self.players[winner].name} が旗 {flag['index'] + 1} を確保。")

        if newly_claimed:
            self.history.extend(newly_claimed)

        winner = self._match_winner()
        if winner:
            self.game_over = True
            self.phase = "finished"
            self.turn = ""
            self.winner_text = f"{self.players[winner].name} の勝ちです。"
            self.message = self.winner_text

    def _match_winner(self) -> str | None:
        for symbol in SEAT_ORDER:
            claimed = sorted(self.claimed_flags[symbol])
            if len(claimed) >= 5:
                return symbol
            streak = 1
            for previous, current in zip(claimed, claimed[1:]):
                streak = streak + 1 if current == previous + 1 else 1
                if streak >= 3:
                    return symbol
        return None

    def _resign(self, symbol: str) -> None:
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        winner = self._other_symbol(symbol)
        self.game_over = True
        self.started = True
        self.phase = "finished"
        self.turn = ""
        self.winner_text = f"{self.players[winner].name} の勝ちです。"
        self.message = f"{self.players[symbol].name} が降参しました。{self.winner_text}"
        self.history.append(self.message)

    def _draw_to_hand(self, symbol: str) -> None:
        if self.deck and symbol in self.players:
            self.players[symbol].hand.append(self.deck.pop())

    def _build_deck(self) -> List[dict]:
        deck = []
        for color_key, color_label in COLORS:
            for strength in range(1, 11):
                deck.append(
                    {
                        "id": f"{color_key}-{strength}",
                        "color": color_key,
                        "color_label": color_label,
                        "strength": strength,
                    }
                )
        random.shuffle(deck)
        return deck

    @staticmethod
    def _new_flag(index: int) -> dict:
        return {
            "index": index,
            "claimed_by": "",
            "cards": {"A": [], "B": []},
            "completed_at": {"A": None, "B": None},
        }

    @staticmethod
    def _card_label(card: dict) -> str:
        return f"{card['color_label']}{card['strength']}"

    @staticmethod
    def _other_symbol(symbol: str) -> str:
        return "B" if symbol == "A" else "A"

    def _compare_formations(self, a_cards: List[dict], b_cards: List[dict], completed_at: dict) -> str:
        a_rank = self._formation_rank(a_cards)
        b_rank = self._formation_rank(b_cards)
        if a_rank > b_rank:
            return "A"
        if b_rank > a_rank:
            return "B"

        a_completed = completed_at.get("A") or 10**9
        b_completed = completed_at.get("B") or 10**9
        return "A" if a_completed <= b_completed else "B"

    def _formation_rank(self, cards: List[dict]) -> tuple:
        strengths = sorted(card["strength"] for card in cards)
        colors = {card["color"] for card in cards}
        is_flush = len(colors) == 1
        is_straight = strengths[0] + 1 == strengths[1] and strengths[1] + 1 == strengths[2]
        total = sum(strengths)
        counts = sorted((strengths.count(value) for value in set(strengths)), reverse=True)

        if is_flush and is_straight:
            return (4, max(strengths), total)
        if counts == [3]:
            return (3, strengths[0], total)
        if is_flush:
            return (2, total, max(strengths))
        if is_straight:
            return (1, max(strengths), total)
        return (0, total, sorted(strengths, reverse=True))

    def _formation_label(self, cards: List[dict]) -> str:
        rank = self._formation_rank(cards)[0]
        return {
            4: "連番同色",
            3: "三つ揃い",
            2: "同色",
            1: "連番",
            0: "合計勝負",
        }.get(rank, "")
