from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


SLOT_ORDER = [
    "set_count",
    "turns_per_set",
    "hand_size",
    "carry_limit",
    "play_limit",
    "target_tens",
    "target_ones",
    "invert_multiple",
]
SLOT_LABELS = {
    "set_count": "セット数",
    "turns_per_set": "1セットのターン数",
    "hand_size": "手札枚数",
    "carry_limit": "繰り越し上限",
    "play_limit": "1ターンに出せる最大枚数",
    "target_tens": "目標値の10の位",
    "target_ones": "目標値の1の位",
    "invert_multiple": "反転条件の倍数",
}
DEFAULT_RULES = {
    "set_count": 5,
    "turns_per_set": 3,
    "hand_size": 9,
    "carry_limit": 4,
    "play_limit": 2,
    "target_tens": 6,
    "target_ones": 7,
    "invert_multiple": 8,
}
SET_SEQUENCE = list(range(2, 10))
CARD_VALUES = list(range(2, 10))
SEAT_ORDER = ["P1", "P2"]
TOTAL_COPIES_PER_VALUE = 4


@dataclass
class FiveRulerPlayer:
    symbol: str
    name: str
    connected: bool = False
    set_wins: int = 0
    current_hand: List[int] | None = None
    carry_cards: List[int] | None = None
    selected_cards: List[int] | None = None
    ready_setup: bool = False
    ready_carry: bool = False
    ready_trim: bool = False
    resigned: bool = False

    def to_public_dict(self, viewer_symbol: str) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "set_wins": self.set_wins,
            "hand": list(self.current_hand or []) if self.symbol == viewer_symbol else None,
            "carry_cards": list(self.carry_cards or []) if self.symbol == viewer_symbol else None,
            "selected_cards": list(self.selected_cards or []) if self.symbol == viewer_symbol else None,
            "ready_setup": self.ready_setup,
            "ready_carry": self.ready_carry,
            "ready_trim": self.ready_trim,
            "resigned": self.resigned,
        }


class FiveRulerGame:
    game_type = "five_ruler"
    title = "five ruler"
    subtitle = "隠しルール改変で数字をずらしながら、セットごとの勝負を奪い合う2人用カードゲーム。"
    category = "original"
    min_players = 2
    max_players = 2
    player_label = "2人用"
    seat_order = list(SEAT_ORDER)
    host_control_actions = {"start_match"}
    setup_mode = "full"

    def __init__(self) -> None:
        self.players: Dict[str, FiveRulerPlayer] = {}
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.message = "2人そろうと開始できます。"
        self.winner_text = ""
        self.current_set = 0
        self.current_turn = 0
        self.turn_log: List[dict] = []
        self.set_log: List[dict] = []
        self.activity_log: List[str] = []
        self.discard_pile: List[int] = []
        self.revealed_changes: List[dict] = []
        self.current_rule_cards: Dict[str, int] = dict(DEFAULT_RULES)
        self.rule_change_plans: Dict[str, Dict[int, dict]] = {}
        self.turn_submissions: Dict[str, List[int]] = {}
        self.set_turn_wins: Dict[str, int] = {}
        self.last_set_result: Optional[dict] = None
        self.last_turn_result: Optional[dict] = None

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
        cleaned = name.strip() or symbol
        self.players[symbol] = FiveRulerPlayer(symbol=symbol, name=cleaned[:24])
        if symbol not in self.rule_change_plans:
            self.rule_change_plans[symbol] = self._default_plan()
        self._refresh_waiting_message()

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        self._refresh_waiting_message()

    def reset_for_rematch(self) -> None:
        saved_players = {
            symbol: (player.name, player.connected)
            for symbol, player in self.players.items()
        }
        self.__init__()
        for symbol, (name, connected) in saved_players.items():
            self.players[symbol] = FiveRulerPlayer(symbol=symbol, name=name, connected=connected)
            self.rule_change_plans[symbol] = self._default_plan()
        self._refresh_waiting_message()

    def apply_host_action(self, action: str, **_: object) -> None:
        if action == "start_match":
            self.start_match()
            return
        raise GameError("未対応のホスト操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        settings: Optional[dict] = None,
        selected_cards: Optional[List[int]] = None,
        **_: object,
    ) -> None:
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        if action == "submit_rule_plan":
            self._submit_rule_plan(symbol, settings or {})
            return
        if action == "submit_turn_cards":
            self._submit_turn_cards(symbol, selected_cards or [])
            return
        if action == "submit_carry_cards":
            self._submit_carry_cards(symbol, selected_cards or [])
            return
        if action == "submit_trim_cards":
            self._submit_trim_cards(symbol, selected_cards or [])
            return
        if action == "next_turn":
            self._advance_after_turn_result()
            return
        if action == "resign":
            self._resign(symbol)
            return
        raise GameError("未対応の操作です。")

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("2人そろってから開始してください。")
        self.started = True
        self.game_over = False
        self.phase = "setup"
        self.message = "ルール改変の配置を8マスぶん決めてください。"
        self.winner_text = ""
        self.current_set = 0
        self.current_turn = 0
        self.turn_log = []
        self.set_log = []
        self.activity_log = []
        self.discard_pile = []
        self.revealed_changes = []
        self.current_rule_cards = dict(DEFAULT_RULES)
        self.turn_submissions = {}
        self.set_turn_wins = {}
        self.last_set_result = None
        self.last_turn_result = None
        for symbol in self.joined_symbols():
            player = self.players[symbol]
            player.set_wins = 0
            player.current_hand = []
            player.carry_cards = []
            player.selected_cards = []
            player.ready_setup = False
            player.ready_carry = False
            player.ready_trim = False
            player.resigned = False
            self.rule_change_plans[symbol] = self._default_plan()

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        viewer_plan = self.rule_change_plans.get(viewer_symbol, {})
        active_rules = self._active_rules()
        return {
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {
                symbol: player.to_public_dict(viewer_symbol)
                for symbol, player in self.players.items()
            },
            "player_order": self.joined_symbols(),
            "current_set": self.current_set,
            "current_turn": self.current_turn,
            "turns_per_set": active_rules["turns_per_set"],
            "set_turn_wins": dict(self.set_turn_wins),
            "last_turn_result": self.last_turn_result,
            "setup_mode": self.setup_mode,
            "next_planning_set": self._next_planning_set(),
            "active_rules": [
                {
                    "key": key,
                    "label": SLOT_LABELS[key],
                    "value": active_rules[key],
                    "changed_this_set": any(change["slot_key"] == key for change in self.revealed_changes),
                    "change_summary": next((change["summary"] for change in self.revealed_changes if change["slot_key"] == key), ""),
                }
                for key in SLOT_ORDER
            ],
            "rule_texts": self._rule_texts(),
            "target_value": self._target_value(),
            "setup_plan": self._public_plan_for_viewer(viewer_symbol, viewer_plan),
            "revealed_changes": list(self.revealed_changes),
            "discard_pile": list(self.discard_pile),
            "turn_submissions_locked": {
                symbol: bool(self.turn_submissions.get(symbol))
                for symbol in self.joined_symbols()
            },
            "turn_log": list(self.turn_log),
            "set_log": list(self.set_log),
            "activity_log": list(self.activity_log[-16:]),
            "last_set_result": self.last_set_result,
            "start_requirements": "2人そろったら部屋主が開始できます。",
        }

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in self.seat_order if symbol in self.players]

    def _refresh_waiting_message(self) -> None:
        if self.started:
            return
        if len(self.joined_symbols()) < self.min_players:
            self.message = "2人そろうと開始できます。"
        else:
            self.message = "2人そろいました。部屋主が開始するとルール改変の配置に入ります。"

    def _default_plan(self) -> Dict[int, dict]:
        return {
            set_number: {
                "set_number": set_number,
                "slot_key": None,
                "card_value": None,
                "revealed": False,
            }
            for set_number in SET_SEQUENCE
        }

    def _public_plan_for_viewer(self, viewer_symbol: str, viewer_plan: Dict[int, dict]) -> List[dict]:
        rows = []
        for set_number in SET_SEQUENCE:
            row = {"set_number": set_number, "players": []}
            for symbol in self.joined_symbols():
                plan = self.rule_change_plans.get(symbol, {}).get(set_number, {})
                is_owner = symbol == viewer_symbol
                if plan.get("revealed") or is_owner or self.game_over:
                    row["players"].append(
                        {
                            "symbol": symbol,
                            "slot_key": plan.get("slot_key"),
                            "slot_label": SLOT_LABELS.get(plan.get("slot_key", ""), "未設定"),
                            "card_value": plan.get("card_value"),
                            "revealed": bool(plan.get("revealed")) or is_owner or self.game_over or self.phase == "setup",
                        }
                    )
                else:
                    row["players"].append(
                        {
                            "symbol": symbol,
                            "slot_key": None,
                            "slot_label": "未公開",
                            "card_value": None,
                            "revealed": False,
                        }
                    )
            rows.append(row)
        return rows

    def _submit_rule_plan(self, symbol: str, payload: dict) -> None:
        if not self.started or self.phase != "setup":
            raise GameError("今はルール改変の配置フェーズではありません。")
        entries = payload.get("entries")
        if not isinstance(entries, list) or len(entries) != len(SET_SEQUENCE):
            raise GameError("2セット目から9セット目まで、8行すべて設定してください。")

        used_slots = set()
        used_values = set()
        plan = {}
        for raw in entries:
            set_number = int(raw.get("set_number", 0))
            slot_key = str(raw.get("slot_key", ""))
            card_value = int(raw.get("card_value", 0))
            if set_number not in SET_SEQUENCE:
                raise GameError("セット番号の指定が不正です。")
            if slot_key not in SLOT_ORDER:
                raise GameError("変更先ルールが不正です。")
            if card_value not in CARD_VALUES:
                raise GameError("改変カードは2から9を1回ずつ使ってください。")
            if slot_key in used_slots:
                raise GameError("同じルール枠は1回しか使えません。")
            if card_value in used_values:
                raise GameError("同じ数字カードは1回しか使えません。")
            used_slots.add(slot_key)
            used_values.add(card_value)
            plan[set_number] = {
                "set_number": set_number,
                "slot_key": slot_key,
                "card_value": card_value,
                "revealed": False,
            }

        self.rule_change_plans[symbol] = plan
        self.players[symbol].ready_setup = True
        self.activity_log.append(f"{self.players[symbol].name} が改変配置を確定しました。")

        if all(self.players[s].ready_setup for s in self.joined_symbols()):
            self._begin_set(1)
        else:
            self.message = "もう一人の配置確定を待っています。"

    def _begin_set(self, set_number: int) -> None:
        self.current_set = set_number
        self.current_turn = 0
        self.turn_submissions = {}
        self.set_turn_wins = {symbol: 0 for symbol in self.joined_symbols()}
        self.last_set_result = None
        self.last_turn_result = None
        self.revealed_changes = []
        self.discard_pile = []
        for symbol in self.joined_symbols():
            self.players[symbol].selected_cards = []
            self.players[symbol].ready_carry = False
            self.players[symbol].ready_trim = False

        if set_number > 1:
            self._apply_rule_changes_for_set(set_number)
            total_sets = self._active_rules()["set_count"]
            if total_sets < self.current_set:
                self._resolve_set_count_collapse()
                return

        if self._deal_new_hands():
            self.phase = "trim"
            self.message = f"第{self.current_set}セットの手札が上限を超えています。残すカードを選んでください。"
            return
        active_rules = self._active_rules()
        if active_rules["turns_per_set"] <= 0:
            self.activity_log.append(f"第{self.current_set}セットはターン数0のため即終了しました。")
            self._finish_set()
            return

        self.phase = "battle"
        self.message = f"第{self.current_set}セット開始。手札からカードを出してください。"

    def _apply_rule_changes_for_set(self, set_number: int) -> None:
        changes = []
        for symbol in self.joined_symbols():
            plan = self.rule_change_plans[symbol][set_number]
            plan["revealed"] = True
            changes.append(
                {
                    "symbol": symbol,
                    "player_name": self.players[symbol].name,
                    "slot_key": plan["slot_key"],
                    "slot_label": SLOT_LABELS[plan["slot_key"]],
                    "card_value": plan["card_value"],
                }
            )

        grouped: Dict[str, List[dict]] = {}
        for change in changes:
            grouped.setdefault(change["slot_key"], []).append(change)

        replaced_values: List[int] = []

        applied = []
        for slot_key, slot_changes in grouped.items():
            previous = self.current_rule_cards[slot_key]
            replaced_values.append(previous)
            if len(slot_changes) == 1:
                new_value = slot_changes[0]["card_value"]
                source = "single"
                summary = f"{slot_changes[0]['card_value']} に変更"
            else:
                values = [item["card_value"] for item in slot_changes]
                new_value = abs(max(values) - min(values))
                source = "difference"
                summary = f"{max(values)} - {min(values)} = {new_value}"
            self.current_rule_cards[slot_key] = new_value
            applied.append(
                {
                    "slot_key": slot_key,
                    "slot_label": SLOT_LABELS[slot_key],
                    "previous_value": previous,
                    "new_value": new_value,
                    "source": source,
                    "summary": summary,
                    "changes": slot_changes,
                }
            )

        self.discard_pile = replaced_values
        self.revealed_changes = applied
        if applied:
            self.activity_log.append(f"第{set_number}セット開始時に {len(applied)} 個のルール変更が反映されました。")

    def _resolve_set_count_collapse(self) -> None:
        changes = [change for change in self.revealed_changes if change["slot_key"] == "set_count"]
        involved = []
        for change in changes:
            for item in change["changes"]:
                involved.append(item["symbol"])
        involved = list(dict.fromkeys(involved))
        if not involved:
            involved = self.joined_symbols()

        top_score = max(self.players[symbol].set_wins for symbol in involved)
        losers = [symbol for symbol in involved if self.players[symbol].set_wins == top_score]
        loser_names = " / ".join(self.players[symbol].name for symbol in losers)
        self.game_over = True
        self.phase = "finished"
        self.winner_text = f"セット数が現在セット未満になったため特殊終了。敗者: {loser_names}"
        self.message = self.winner_text

    def _deal_new_hands(self) -> bool:
        rules = self._active_rules()
        hand_size = max(0, rules["hand_size"])
        pool = self._build_draw_pool()
        rng = random.Random()
        rng.shuffle(pool)
        trim_required = False

        for symbol in self.joined_symbols():
            player = self.players[symbol]
            carry_cards = list(player.carry_cards or [])
            player.carry_cards = carry_cards
            if len(carry_cards) > hand_size:
                player.current_hand = sorted(carry_cards)
                player.ready_trim = False
                trim_required = True
            else:
                needed = max(0, hand_size - len(carry_cards))
                drawn = pool[:needed]
                del pool[:needed]
                full_hand = sorted(carry_cards + drawn)
                player.current_hand = full_hand
                player.ready_trim = True
            player.selected_cards = []
            player.ready_carry = False
        return trim_required

    def _build_draw_pool(self) -> List[int]:
        counts = Counter({value: TOTAL_COPIES_PER_VALUE for value in CARD_VALUES})
        for value in self.current_rule_cards.values():
            counts[value] -= 1
        pool: List[int] = []
        for value in CARD_VALUES:
            pool.extend([value] * max(0, counts[value]))
        return pool

    def _enter_set_action_phase(self) -> None:
        active_rules = self._active_rules()
        if active_rules["turns_per_set"] <= 0:
            self.activity_log.append(f"第{self.current_set}セットはターン数0のため即終了しました。")
            self._finish_set()
            return
        self.phase = "battle"
        self.message = f"第{self.current_set}セット開始。手札からカードを出してください。"

    def _resume_after_trim(self) -> None:
        self._enter_set_action_phase()

    def _submit_turn_cards(self, symbol: str, selected_cards: List[int]) -> None:
        if not self.started or self.phase != "battle":
            raise GameError("今はターンのカード提出フェーズではありません。")
        player = self.players[symbol]
        if player.current_hand is None:
            raise GameError("手札がありません。")
        rules = self._active_rules()
        play_limit = max(0, rules["play_limit"])
        if len(selected_cards) > play_limit:
            raise GameError(f"このセットでは最大 {play_limit} 枚までしか出せません。")
        if symbol in self.turn_submissions:
            raise GameError("すでにこのターンの提出は完了しています。")

        hand_counter = Counter(player.current_hand)
        chosen_counter = Counter(selected_cards)
        for value, count in chosen_counter.items():
            if hand_counter[value] < count:
                raise GameError("手札にないカードを出そうとしています。")

        self.turn_submissions[symbol] = list(selected_cards)
        player.selected_cards = list(selected_cards)
        self.activity_log.append(f"{player.name} が第{self.current_set}セット {self.current_turn + 1} ターン目のカードを確定しました。")

        if all(symbol in self.turn_submissions for symbol in self.joined_symbols()):
            self._resolve_turn()
        else:
            self.message = "もう一人の提出を待っています。"

    def _resolve_turn(self) -> None:
        self.current_turn += 1
        target = self._target_value()
        invert_multiple = self._active_rules()["invert_multiple"]
        rows = []
        for symbol in self.joined_symbols():
            cards = self.turn_submissions.get(symbol, [])
            value = self._cards_to_value(cards)
            rows.append(
                {
                    "symbol": symbol,
                    "player_name": self.players[symbol].name,
                    "cards": list(cards),
                    "value": value,
                    "distance": None if value is None else abs(value - target),
                }
            )

        winner_symbol = self._determine_turn_winner(rows, invert_multiple)
        if winner_symbol:
            self.set_turn_wins[winner_symbol] += 1

        for row in rows:
            player = self.players[row["symbol"]]
            for card in row["cards"]:
                player.current_hand.remove(card)
                self.discard_pile.append(card)
            player.selected_cards = []

        log_row = {
            "set_number": self.current_set,
            "turn_number": self.current_turn,
            "target_value": target,
            "invert_multiple": invert_multiple,
            "rows": rows,
            "winner_symbol": winner_symbol,
            "winner_name": self.players[winner_symbol].name if winner_symbol else "引き分け",
        }
        self.turn_log.append(log_row)
        self.last_turn_result = log_row
        self.turn_submissions = {}
        self.phase = "turn_result"
        self.message = f"第{self.current_set}セット {self.current_turn} ターン目の結果を確認してください。"

    def _advance_after_turn_result(self) -> None:
        if not self.started or self.phase != "turn_result":
            raise GameError("今は次へ進めるタイミングではありません。")
        if self.current_turn >= self._active_rules()["turns_per_set"]:
            self._finish_set()
            return
        self.phase = "battle"
        self.message = f"第{self.current_set}セット {self.current_turn + 1} ターン目のカードを選んでください。"

    def _cards_to_value(self, cards: List[int]) -> Optional[int]:
        if len(cards) == 0:
            return None
        value = 1
        for card in cards:
            value *= card
        return value

    def _determine_turn_winner(self, rows: List[dict], invert_multiple: int) -> Optional[str]:
        left, right = rows
        if left["value"] is None and right["value"] is None:
            return None
        if left["value"] is None:
            return right["symbol"]
        if right["value"] is None:
            return left["symbol"]

        if left["distance"] == right["distance"]:
            return None

        stronger = left if left["distance"] < right["distance"] else right
        weaker = right if stronger is left else left
        difference = abs(left["value"] - right["value"])
        should_invert = invert_multiple > 0 and difference != 0 and difference % invert_multiple == 0
        return weaker["symbol"] if should_invert else stronger["symbol"]

    def _finish_set(self) -> None:
        left_symbol, right_symbol = self.joined_symbols()
        left_wins = self.set_turn_wins[left_symbol]
        right_wins = self.set_turn_wins[right_symbol]
        set_winner = None
        if left_wins > right_wins:
            set_winner = left_symbol
        elif right_wins > left_wins:
            set_winner = right_symbol

        if set_winner:
            self.players[set_winner].set_wins += 1

        result = {
            "set_number": self.current_set,
            "turns_won": {
                left_symbol: left_wins,
                right_symbol: right_wins,
            },
            "winner_symbol": set_winner,
            "winner_name": self.players[set_winner].name if set_winner else "引き分け",
            "rules": dict(self._active_rules()),
            "revealed_changes": list(self.revealed_changes),
        }
        self.last_set_result = result
        self.set_log.append(result)
        self.last_turn_result = None

        total_sets = self._active_rules()["set_count"]
        if self.current_set >= total_sets:
            self._finish_match()
            return

        self.phase = "carry"
        self.message = f"第{self.current_set}セット終了。繰り越すカードを選んでください。"
        for symbol in self.joined_symbols():
            self.players[symbol].carry_cards = []
            self.players[symbol].ready_carry = False
            self.players[symbol].ready_trim = False

    def _submit_carry_cards(self, symbol: str, selected_cards: List[int]) -> None:
        if not self.started or self.phase != "carry":
            raise GameError("今は繰り越し選択フェーズではありません。")
        player = self.players[symbol]
        hand = list(player.current_hand or [])
        limit = max(0, self._active_rules()["carry_limit"])
        if len(selected_cards) > limit:
            raise GameError(f"このセットでは最大 {limit} 枚までしか繰り越せません。")
        hand_counter = Counter(hand)
        chosen_counter = Counter(selected_cards)
        for value, count in chosen_counter.items():
            if hand_counter[value] < count:
                raise GameError("手札にないカードを繰り越そうとしています。")
        player.carry_cards = sorted(selected_cards)
        player.ready_carry = True
        self.activity_log.append(f"{player.name} が繰り越しカードを確定しました。")
        if all(self.players[s].ready_carry for s in self.joined_symbols()):
            self._cleanup_after_set()
            self._begin_set(self.current_set + 1)
        else:
            self.message = "もう一人の繰り越し選択を待っています。"

    def _submit_trim_cards(self, symbol: str, selected_cards: List[int]) -> None:
        if not self.started or self.phase != "trim":
            raise GameError("今は手札調整フェーズではありません。")
        player = self.players[symbol]
        hand = list(player.current_hand or [])
        hand_size = max(0, self._active_rules()["hand_size"])
        if len(selected_cards) != hand_size:
            raise GameError(f"残すカードはちょうど {hand_size} 枚選んでください。")

        hand_counter = Counter(hand)
        chosen_counter = Counter(selected_cards)
        for value, count in chosen_counter.items():
            if hand_counter[value] < count:
                raise GameError("手札にないカードは残せません。")

        keep = Counter(selected_cards)
        for value in hand:
            if keep[value] > 0:
                keep[value] -= 1
            else:
                self.discard_pile.append(value)

        player.current_hand = sorted(selected_cards)
        player.ready_trim = True
        self.activity_log.append(f"{player.name} が手札調整を完了しました。")

        if all(self.players[s].ready_trim for s in self.joined_symbols()):
            for joined_symbol in self.joined_symbols():
                self.players[joined_symbol].ready_trim = False
            self._resume_after_trim()
        else:
            self.message = "もう一人の手札調整が終わるのを待っています。"

    def _cleanup_after_set(self) -> None:
        for symbol in self.joined_symbols():
            player = self.players[symbol]
            current_hand = list(player.current_hand or [])
            keep = Counter(player.carry_cards or [])
            for value in current_hand:
                if keep[value] > 0:
                    keep[value] -= 1
                else:
                    self.discard_pile.append(value)
            player.current_hand = []

    def _finish_match(self) -> None:
        self.game_over = True
        self.phase = "finished"
        scores = {symbol: self.players[symbol].set_wins for symbol in self.joined_symbols()}
        top_score = max(scores.values(), default=0)
        winners = [symbol for symbol, score in scores.items() if score == top_score]
        if len(winners) == 1:
            self.winner_text = f"勝者: {self.players[winners[0]].name}"
        else:
            names = " / ".join(self.players[symbol].name for symbol in winners)
            self.winner_text = f"引き分け: {names}"
        self.message = "試合終了。結果と各セットの変化を確認できます。"

    def _resign(self, symbol: str) -> None:
        self.players[symbol].resigned = True
        self.game_over = True
        self.phase = "finished"
        other = [item for item in self.joined_symbols() if item != symbol]
        if other:
            self.winner_text = f"勝者: {self.players[other[0]].name}"
        else:
            self.winner_text = "試合終了"
        self.message = f"{self.players[symbol].name} が降参しました。"

    def _target_value(self) -> int:
        rules = self._active_rules()
        return rules["target_tens"] * 10 + rules["target_ones"]

    def _active_rules(self) -> Dict[str, int]:
        return dict(self.current_rule_cards)

    def _next_planning_set(self) -> Optional[int]:
        if self.current_set <= 0:
            return 2
        candidate = self.current_set + 1
        total_sets = self._active_rules()["set_count"]
        if candidate > total_sets or candidate not in SET_SEQUENCE:
            return None
        return candidate

    def _rule_texts(self) -> List[str]:
        rules = self._active_rules()
        target = self._target_value()
        return [
            (
                f"A<br>"
                f"このゲームは、<span class=\"five-ruler-inline-number\">{rules['turns_per_set']}</span>ターンの勝負を、"
                f"合計<span class=\"five-ruler-inline-number\">{rules['set_count']}</span>セット行う。<br>"
                f"各セットの勝者を決め、最終的に最も多くのセットを取ったプレイヤーが勝利する。<br>"
                f"また、何らかの理由で現在のセット数より合計セット数が少なくなった場合は、"
                f"その処理に関わったプレイヤーのうち、その時点で最も多くセット数を取っていた者が敗者となる。"
            ),
            (
                f"B<br>"
                f"各セットの開始時、各プレイヤーに手札を"
                f"<span class=\"five-ruler-inline-number\">{rules['hand_size']}</span>枚配る。<br>"
                f"使用したカードは墓地に置く。セットが終わると、シャッフルし再度山札を作る。<br>"
                f"そのセットで最後まで使わなかったカードは、"
                f"次のセットに最大<span class=\"five-ruler-inline-number\">{rules['carry_limit']}</span>枚まで"
                f"繰り越すことができる。"
            ),
            (
                f"C<br>"
                f"各ターン、プレイヤーは手札から"
                f"最大<span class=\"five-ruler-inline-number\">{rules['play_limit']}</span>枚までカードを出せる。<br>"
                f"出したカードの掛け算の結果を、そのターンの数値とする。<br>"
                f"また、カードを出さなかった場合、そのターンは敗北となる。"
            ),
            (
                f"D<br>"
                f"ターンの数値は、<span class=\"five-ruler-inline-number\">{target}</span>に近いほど強い。<br>"
                f"ただし、両者の数値の差が"
                f"<span class=\"five-ruler-inline-number\">{rules['invert_multiple']}</span>の倍数である場合、"
                f"本来強い側が負けとなる。<br>"
                f"ゲームにおいて両者が同等の強さの場合、引き分けとなり、ゲームはそのまま次に進む。"
            ),
            (
                f"E<br>"
                f"ゲーム開始時に、ルール内の数字をセット数毎に変更する。<br>"
                f"変更に使える数字も変更箇所も同じものは選べない。<br>"
                f"変更した数字は、最初のセット終了以降、セットごとに逐次適用される。<br>"
                f"複数の変更が同時に行われた場合は、数字の差分が適用される。"
            ),
        ]


class FiveRuler2Game(FiveRulerGame):
    game_type = "five_ruler_2"
    title = "five ruler 2"
    subtitle = "各セット開始時に、次セットぶんの改変を1つずつ決めていく派生版。"
    setup_mode = "incremental"

    def _resume_after_trim(self) -> None:
        next_planning_set = self._next_planning_set()
        if next_planning_set is not None:
            self.phase = "setup"
            self.message = f"第{self.current_set}セットの準備ができました。第{next_planning_set}セットぶんの改変を1つ決めてください。"
            return
        self._enter_set_action_phase()

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("2人そろってから開始してください。")
        self.started = True
        self.game_over = False
        self.phase = "waiting"
        self.message = "第1セットの準備を始めます。"
        self.winner_text = ""
        self.current_set = 0
        self.current_turn = 0
        self.turn_log = []
        self.set_log = []
        self.activity_log = []
        self.discard_pile = []
        self.revealed_changes = []
        self.current_rule_cards = dict(DEFAULT_RULES)
        self.turn_submissions = {}
        self.set_turn_wins = {}
        self.last_set_result = None
        self.last_turn_result = None
        for symbol in self.joined_symbols():
            player = self.players[symbol]
            player.set_wins = 0
            player.current_hand = []
            player.carry_cards = []
            player.selected_cards = []
            player.ready_setup = False
            player.ready_carry = False
            player.ready_trim = False
            player.resigned = False
            self.rule_change_plans[symbol] = self._default_plan()
        self._begin_set(1)

    def _submit_rule_plan(self, symbol: str, payload: dict) -> None:
        if not self.started or self.phase != "setup":
            raise GameError("今は次セットぶんのルール改変を決めるフェーズではありません。")
        planning_set = self._next_planning_set()
        if planning_set is None:
            raise GameError("これ以上先のセットに改変を置けません。")

        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise GameError("改変内容が不正です。")
        entry = next((raw for raw in entries if int(raw.get("set_number", 0)) == planning_set), None)
        if entry is None:
            raise GameError(f"第{planning_set}セットぶんの改変を選んでください。")

        slot_key = str(entry.get("slot_key", ""))
        card_value = int(entry.get("card_value", 0))
        if slot_key not in SLOT_ORDER:
            raise GameError("変更先ルールが不正です。")
        if card_value not in CARD_VALUES:
            raise GameError("改変カードは2から9を1回ずつ使ってください。")

        used_slots = set()
        used_values = set()
        for set_number in SET_SEQUENCE:
            if set_number == planning_set:
                continue
            planned = self.rule_change_plans[symbol].get(set_number)
            if not planned or planned.get("slot_key") is None or planned.get("card_value") is None:
                continue
            used_slots.add(planned["slot_key"])
            used_values.add(planned["card_value"])

        if slot_key in used_slots:
            raise GameError("そのルール枠はすでに別セットで使っています。")
        if card_value in used_values:
            raise GameError("その数字カードはすでに別セットで使っています。")

        self.rule_change_plans[symbol][planning_set] = {
            "set_number": planning_set,
            "slot_key": slot_key,
            "card_value": card_value,
            "revealed": False,
        }
        self.players[symbol].ready_setup = True
        self.activity_log.append(f"{self.players[symbol].name} が第{planning_set}セットぶんの改変を確定しました。")

        if all(self.players[s].ready_setup for s in self.joined_symbols()):
            for player_symbol in self.joined_symbols():
                self.players[player_symbol].ready_setup = False
            if self._active_rules()["turns_per_set"] <= 0:
                self.activity_log.append(f"第{self.current_set}セットはターン数0のため即終了しました。")
                self._finish_set()
            else:
                self._enter_set_action_phase()
                return
                self.message = f"第{self.current_set}セット開始。手札からカードを出してください。"
        else:
            self.message = f"もう一人の第{planning_set}セットぶん改変確定を待っています。"

    def _begin_set(self, set_number: int) -> None:
        self.current_set = set_number
        self.current_turn = 0
        self.turn_submissions = {}
        self.set_turn_wins = {symbol: 0 for symbol in self.joined_symbols()}
        self.last_set_result = None
        self.last_turn_result = None
        self.revealed_changes = []
        self.discard_pile = []
        for symbol in self.joined_symbols():
            self.players[symbol].selected_cards = []
            self.players[symbol].ready_carry = False
            self.players[symbol].ready_trim = False

        if set_number > 1:
            self._apply_rule_changes_for_set(set_number)
            total_sets = self._active_rules()["set_count"]
            if total_sets < self.current_set:
                self._resolve_set_count_collapse()
                return

        if self._deal_new_hands():
            self.phase = "trim"
            self.message = f"第{self.current_set}セットの手札が上限を超えています。残すカードを選んでください。"
            return
        next_planning_set = self._next_planning_set()
        if next_planning_set is not None:
            self.phase = "setup"
            self.message = f"第{self.current_set}セットの手札が配られました。第{next_planning_set}セットぶんの改変を1つ選んでください。"
        else:
            if self._active_rules()["turns_per_set"] <= 0:
                self.activity_log.append(f"第{self.current_set}セットはターン数0のため即終了しました。")
                self._finish_set()
                return
            self._enter_set_action_phase()
            return
            self.message = f"第{self.current_set}セット開始。手札からカードを出してください。"
