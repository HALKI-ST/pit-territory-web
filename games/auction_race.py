from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


MAX_PLAYERS = 8
DEFAULT_STARTING_BALANCE = 50_000
DEFAULT_DICE_SIDES = 6
DEFAULT_TRACK_LENGTH = 30
DEFAULT_TAPE_BONUS = 15_000
DEFAULT_QUICK_BIDS = [0, 1_000, 2_000, 5_000, 8_000, 10_000]
DEFAULT_GOAL_REWARDS = [50_000, 20_000, 10_000, 5_000, 2_000, 1_000]
DEFAULT_PLUS_COUNT = 14
DEFAULT_MINUS_COUNT = 9
DEFAULT_FORWARD_COUNT = 2
DEFAULT_BACKWARD_COUNT = 2
DEFAULT_FORWARD_STEPS = 3
DEFAULT_BACKWARD_STEPS = 3
DEFAULT_NET_TILE_TOTAL = 10_000
DEFAULT_MONEY_TILE_MIN = 1_000
DEFAULT_MONEY_TILE_MAX = 5_000
SNAKE_COLUMNS = 6


@dataclass
class AuctionPlayerState:
    symbol: str
    name: str
    balance: int
    position: int = 0
    connected: bool = False
    status: str = "waiting"
    locked_bid: Optional[int] = None
    last_bid: Optional[int] = None
    placement: Optional[int] = None
    finish_reward: int = 0
    last_delta: int = 0

    def is_loser(self) -> bool:
        return self.status in {"bankrupt", "resigned"}

    def can_act(self) -> bool:
        return self.status == "playing"

    def to_public_dict(self, viewer_symbol: str, reveal_all: bool) -> dict:
        balance_visible = reveal_all or self.symbol == viewer_symbol
        return {
            "symbol": self.symbol,
            "name": self.name,
            "position": self.position,
            "connected": self.connected,
            "status": self.status,
            "placement": self.placement,
            "finish_reward": self.finish_reward,
            "last_bid": self.last_bid if reveal_all else None,
            "locked_bid": self.locked_bid is not None,
            "balance_visible": balance_visible,
            "balance": self.balance if balance_visible else None,
            "last_delta": self.last_delta if reveal_all or self.symbol == viewer_symbol else None,
        }


class AuctionRaceGame:
    game_type = "auction_race"
    title = "セリすごろく"
    subtitle = "サイコロの出目をセリで買って進む、銀行つきの多人数すごろく。"
    min_players = 2
    max_players = MAX_PLAYERS
    seat_order = ["A", "B", "C", "D", "E", "F", "G", "H"]
    host_control_actions = {"start_match", "update_settings"}

    def __init__(self) -> None:
        self.players: Dict[str, AuctionPlayerState] = {}
        self.started = False
        self.game_over = False
        self.results_revealed = False
        self.awaiting_judge = False
        self.message = "参加者を集めてください。"
        self.winner_text = ""
        self.round_number = 0
        self.current_roll = 0
        self.current_roll_max = DEFAULT_DICE_SIDES
        self.starting_balance = DEFAULT_STARTING_BALANCE
        self.track_length = 0
        self.track_length_setting = DEFAULT_TRACK_LENGTH
        self.plus_count = DEFAULT_PLUS_COUNT
        self.minus_count = DEFAULT_MINUS_COUNT
        self.forward_count = DEFAULT_FORWARD_COUNT
        self.backward_count = DEFAULT_BACKWARD_COUNT
        self.forward_steps = DEFAULT_FORWARD_STEPS
        self.backward_steps = DEFAULT_BACKWARD_STEPS
        self.net_tile_total = DEFAULT_NET_TILE_TOTAL
        self.money_tile_min = DEFAULT_MONEY_TILE_MIN
        self.money_tile_max = DEFAULT_MONEY_TILE_MAX
        self.quick_bids = list(DEFAULT_QUICK_BIDS)
        self.goal_rewards = list(DEFAULT_GOAL_REWARDS)
        self.board_tiles: List[dict] = []
        self.tile_layout_text = ""
        self.tape_bonus_position: Optional[int] = None
        self.tape_bonus_value = DEFAULT_TAPE_BONUS
        self.tape_bonus_claimed_by: Optional[str] = None
        self.finished_order: List[str] = []
        self.activity_log: List[str] = []
        self.round_history: List[dict] = []

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
        cleaned = name.strip() or f"Player {symbol}"
        if symbol not in self.players:
            self.players[symbol] = AuctionPlayerState(symbol=symbol, name=cleaned[:24], balance=self.starting_balance)
        else:
            self.players[symbol].name = cleaned[:24]
            if not self.started:
                self.players[symbol].balance = self.starting_balance
        self.refresh_waiting_message()

    def refresh_waiting_message(self) -> None:
        if self.started:
            return
        if len(self.joined_symbols()) < self.min_players:
            self.message = "2人以上集まると開始できます。"
        else:
            self.message = "人数がそろいました。設定を確認してから、部屋を作った人が開始してください。"

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in self.seat_order if symbol in self.players]

    def start_if_ready(self) -> None:
        self.refresh_waiting_message()

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        if action == "start_match":
            self.start_match()
            return
        if action == "update_settings":
            self.update_settings(settings or {})
            return
        raise GameError("不明な管理操作です。")

    def apply_player_action(self, symbol: str, action: str, bid_amount: Optional[int] = None, **_: object) -> None:
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")

        if action == "judge_round":
            self._judge_round()
            return
        if action == "show_results":
            self._show_results()
            return

        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.game_over:
            raise GameError("ゲームは終了しています。")

        player = self.players[symbol]
        if not player.can_act():
            raise GameError("このプレイヤーはもう行動できません。")

        if action == "place_bid":
            self._place_bid(player, bid_amount)
        elif action == "resign":
            self._resign(player)
        else:
            raise GameError("不明な操作です。")

        if self._all_active_players_ready():
            self.awaiting_judge = True
            self.message = "全員の入札がそろいました。ジャッジボタンで公開してください。"

    def update_settings(self, settings: dict) -> None:
        if self.started:
            raise GameError("ゲーム開始後は設定を変更できません。")

        self.starting_balance = self._parse_non_negative_int(settings.get("starting_balance"), self.starting_balance, minimum=1_000)
        self.current_roll_max = self._parse_non_negative_int(settings.get("dice_sides"), self.current_roll_max, minimum=2)
        self.track_length_setting = self._parse_non_negative_int(settings.get("track_length"), self.track_length_setting, minimum=6)
        self.plus_count = self._parse_non_negative_int(settings.get("plus_count"), self.plus_count, minimum=0)
        self.minus_count = self._parse_non_negative_int(settings.get("minus_count"), self.minus_count, minimum=0)
        self.forward_count = self._parse_non_negative_int(settings.get("forward_count"), self.forward_count, minimum=0)
        self.backward_count = self._parse_non_negative_int(settings.get("backward_count"), self.backward_count, minimum=0)
        self.forward_steps = self._parse_non_negative_int(settings.get("forward_steps"), self.forward_steps, minimum=1)
        self.backward_steps = self._parse_non_negative_int(settings.get("backward_steps"), self.backward_steps, minimum=1)
        self.net_tile_total = self._parse_int(settings.get("net_tile_total"), self.net_tile_total)
        self.money_tile_min = self._parse_non_negative_int(settings.get("money_tile_min"), self.money_tile_min, minimum=1_000)
        self.money_tile_max = self._parse_non_negative_int(settings.get("money_tile_max"), self.money_tile_max, minimum=1_000)
        self.tape_bonus_value = self._parse_non_negative_int(settings.get("tape_bonus_value"), self.tape_bonus_value, minimum=0)
        tape_position = self._parse_optional_int(settings.get("tape_bonus_position"), minimum=1)
        goal_rewards = self._parse_goal_rewards(settings.get("goal_rewards"), self.goal_rewards)
        tile_layout_text = str(settings.get("tile_layout_text", self.tile_layout_text or "")).strip()

        if self.money_tile_min % 1_000 != 0 or self.money_tile_max % 1_000 != 0:
            raise GameError("金額マスの下限と上限は 1000 円単位で設定してください。")
        if self.money_tile_min > self.money_tile_max:
            raise GameError("金額マスの下限は上限以下にしてください。")

        configured_tiles = self.plus_count + self.minus_count + self.forward_count + self.backward_count
        middle_count = self.track_length_setting - 1
        if configured_tiles > middle_count:
            raise GameError("設定したマス数の合計がコース長を超えています。")
        if tape_position is not None and tape_position >= self.track_length_setting:
            raise GameError("先着テープ位置はゴール手前に設定してください。")

        self.goal_rewards = goal_rewards
        self.tile_layout_text = tile_layout_text
        self.tape_bonus_position = tape_position
        for player in self.players.values():
            player.balance = self.starting_balance
        self.refresh_waiting_message()
        self.message = "設定を更新しました。内容を確認してから開始してください。"

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("開始には2人以上必要です。")

        self.started = True
        self.game_over = False
        self.results_revealed = False
        self.awaiting_judge = False
        self.round_number = 1
        self.track_length = self.track_length_setting

        if self.tape_bonus_position is None:
            self.tape_bonus_position = max(2, self.track_length // 2)
        elif self.tape_bonus_position >= self.track_length:
            raise GameError("先着テープ位置はゴール手前に設定してください。")

        self.board_tiles = self._build_board_tiles(
            self.track_length,
            self.tile_layout_text,
            self.plus_count,
            self.minus_count,
            self.forward_count,
            self.backward_count,
            self.net_tile_total,
            self.money_tile_min,
            self.money_tile_max,
        )
        self.tape_bonus_claimed_by = None
        self.finished_order = []
        self.activity_log = []
        self.round_history = []

        for symbol in self.joined_symbols():
            player = self.players[symbol]
            player.balance = self.starting_balance
            player.position = 0
            player.status = "playing"
            player.locked_bid = None
            player.last_bid = None
            player.placement = None
            player.finish_reward = 0
            player.last_delta = 0

        self.current_roll = self._roll_die()
        self.message = f"ラウンド {self.round_number}。出目は {self.current_roll}。全員が入札してください。"

    def reset_for_rematch(self) -> None:
        saved_names = {symbol: player.name for symbol, player in self.players.items()}
        saved_connections = {symbol: player.connected for symbol, player in self.players.items()}
        saved_settings = self._settings_dict()
        self.__init__()
        self.update_settings(saved_settings)
        for symbol, name in saved_names.items():
            self.set_player_name(symbol, name)
            self.players[symbol].connected = saved_connections[symbol]
        self.message = "再戦の準備ができました。設定を見直すなら今のうちに変更してください。"

    def active_players(self) -> List[AuctionPlayerState]:
        return [player for player in self.players.values() if player.status == "playing"]

    def non_loser_players(self) -> List[AuctionPlayerState]:
        return [player for player in self.players.values() if not player.is_loser()]

    def _roll_die(self) -> int:
        return random.randint(1, self.current_roll_max)

    def _build_board_tiles(
        self,
        track_length: int,
        layout_text: str,
        plus_count: int,
        minus_count: int,
        forward_count: int,
        backward_count: int,
        net_tile_total: int,
        money_tile_min: int,
        money_tile_max: int,
        shuffle_events: bool = True,
        randomize_values: bool = True,
    ) -> List[dict]:
        tiles = [{"kind": "start", "value": 0, "label": "スタート"}]
        middle_count = track_length - 1
        custom_tiles = self._parse_tile_layout(layout_text)
        if custom_tiles:
            tiles.extend(custom_tiles[:middle_count])
            while len(tiles) < track_length:
                tiles.append({"kind": "blank", "value": 0, "label": "空き"})
        else:
            configured_tiles = plus_count + minus_count + forward_count + backward_count
            blanks = max(0, middle_count - configured_tiles)
            plus_values, minus_values = self._build_money_values(
                plus_count,
                minus_count,
                net_tile_total,
                money_tile_min,
                money_tile_max,
                randomize=randomize_values,
            )
            events: List[dict] = []

            for value in plus_values:
                events.append({"kind": "plus", "value": value, "label": f"+{value:,}円"})
            for value in minus_values:
                events.append({"kind": "minus", "value": -value, "label": f"-{value:,}円"})
            for _ in range(forward_count):
                events.append({"kind": "forward", "value": self.forward_steps, "label": f"+{self.forward_steps}マス"})
            for _ in range(backward_count):
                events.append({"kind": "backward", "value": -self.backward_steps, "label": f"-{self.backward_steps}マス"})
            for _ in range(blanks):
                events.append({"kind": "blank", "value": 0, "label": "空き"})

            if shuffle_events:
                random.shuffle(events)
            tiles.extend(events[:middle_count])
        tiles.append({"kind": "goal", "value": 0, "label": "ゴール"})
        return tiles

    def _parse_tile_layout(self, layout_text: str) -> List[dict]:
        if not layout_text:
            return []
        tiles: List[dict] = []
        for token in [token.strip() for token in layout_text.replace("\n", ",").split(",")]:
            if not token:
                continue
            upper = token.upper()
            if upper in {"0", "BLANK", "EMPTY", "B"}:
                tiles.append({"kind": "blank", "value": 0, "label": "空き"})
                continue
            if upper.startswith("F"):
                value = int(upper[1:] or self.forward_steps)
                tiles.append({"kind": "forward", "value": value, "label": f"+{value}マス"})
                continue
            if upper.startswith("R"):
                value = int(upper[1:] or self.backward_steps)
                tiles.append({"kind": "backward", "value": -value, "label": f"-{value}マス"})
                continue
            try:
                value = int(token)
            except ValueError as exc:
                raise GameError("マス配置には整数、0、F2、R2 のような形式を使ってください。") from exc
            if value > 0:
                tiles.append({"kind": "plus", "value": value, "label": f"+{value:,}円"})
            elif value < 0:
                tiles.append({"kind": "minus", "value": value, "label": f"-{abs(value):,}円"})
            else:
                tiles.append({"kind": "blank", "value": 0, "label": "空き"})
        return tiles

    def _build_money_values(
        self,
        plus_count: int,
        minus_count: int,
        net_tile_total: int,
        money_tile_min: int,
        money_tile_max: int,
        randomize: bool = True,
    ) -> tuple[list[int], list[int]]:
        min_units = money_tile_min // 1_000
        max_units = money_tile_max // 1_000
        target_units = net_tile_total // 1_000

        if plus_count == 0 and minus_count == 0:
            if target_units != 0:
                raise GameError("金額マスがないため、青赤マスの合計値を設定できません。")
            return [], []
        if plus_count == 0:
            if target_units > 0:
                raise GameError("合計値をプラスにするには青マスを1つ以上入れてください。")
            minus_total = (-target_units) * 1_000
            distributor = self._distribute_total_random if randomize else self._distribute_total_bounded
            return [], distributor(minus_total, minus_count, money_tile_min, money_tile_max)
        if minus_count == 0:
            plus_total = target_units * 1_000
            distributor = self._distribute_total_random if randomize else self._distribute_total_bounded
            return distributor(plus_total, plus_count, money_tile_min, money_tile_max), []

        minus_low = minus_count * min_units
        minus_high = minus_count * max_units
        plus_low = plus_count * min_units
        plus_high = plus_count * max_units

        feasible_minus_low = max(minus_low, plus_low - target_units)
        feasible_minus_high = min(minus_high, plus_high - target_units)
        if feasible_minus_low > feasible_minus_high:
            raise GameError("金額マスの下限・上限と合計値の設定が両立していません。")

        if randomize:
            minus_total_units = random.randint(feasible_minus_low, feasible_minus_high)
        else:
            minus_total_units = (feasible_minus_low + feasible_minus_high) // 2

        plus_total_units = minus_total_units + target_units
        minus_total = minus_total_units * 1_000
        plus_total = plus_total_units * 1_000

        distributor = self._distribute_total_random if randomize else self._distribute_total_bounded
        plus_values = distributor(plus_total, plus_count, money_tile_min, money_tile_max)
        minus_values = distributor(minus_total, minus_count, money_tile_min, money_tile_max)
        return plus_values, minus_values

    def _distribute_total_bounded(self, total: int, count: int, minimum: int, maximum: int) -> list[int]:
        if count <= 0:
            return []
        if total < count * minimum or total > count * maximum:
            raise GameError("金額マスの合計値が上下限設定と合っていません。")

        values = [minimum] * count
        remaining = total - count * minimum
        step_cap = maximum - minimum
        index = 0
        while remaining > 0:
            add = min(1_000, remaining, step_cap - (values[index] - minimum))
            if add > 0:
                values[index] += add
                remaining -= add
            index = (index + 1) % count
        return values

    def _distribute_total_random(self, total: int, count: int, minimum: int, maximum: int) -> list[int]:
        if count <= 0:
            return []
        if total < count * minimum or total > count * maximum:
            raise GameError("金額マスの合計値が上下限設定と合っていません。")

        min_units = minimum // 1_000
        max_units = maximum // 1_000
        remaining_units = total // 1_000
        values_units: list[int] = []
        for index in range(count):
            rest = count - index - 1
            low = max(min_units, remaining_units - rest * max_units)
            high = min(max_units, remaining_units - rest * min_units)
            values_units.append(random.randint(low, high))
            remaining_units -= values_units[-1]
        random.shuffle(values_units)
        return [value * 1_000 for value in values_units]

    def _place_bid(self, player: AuctionPlayerState, bid_amount: Optional[int]) -> None:
        if self.awaiting_judge:
            raise GameError("いまはジャッジ待ちです。")
        if bid_amount is None:
            raise GameError("入札額を入力してください。")
        amount = int(bid_amount)
        if amount < 0:
            raise GameError("入札額は0以上にしてください。")
        if amount % 1_000 != 0:
            raise GameError("入札額は1000円単位にしてください。")
        if amount > player.balance:
            raise GameError("残高を超える入札はできません。")
        player.locked_bid = amount
        self.message = f"{player.name} が入札を確定しました。"

    def _resign(self, player: AuctionPlayerState) -> None:
        player.status = "resigned"
        player.locked_bid = None
        player.last_bid = None
        player.last_delta = 0
        self.activity_log.append(f"{player.name} は降参し、この時点で敗北が確定しました。")
        self.message = f"{player.name} は降参しました。"
        if self._should_finish():
            self._finish_game()

    def _all_active_players_ready(self) -> bool:
        active = self.active_players()
        return bool(active) and all(player.locked_bid is not None for player in active)

    def _judge_round(self) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.game_over:
            raise GameError("ゲームは終了しています。")
        if not self.awaiting_judge:
            raise GameError("まだ全員の入札がそろっていません。")
        self._resolve_round()

    def _resolve_round(self) -> None:
        active = self.active_players()
        if not active:
            self._finish_game()
            return

        round_log = {
            "round": self.round_number,
            "roll": self.current_roll,
            "bids": {},
            "winners": [],
            "move_amount": 0,
            "events": [],
            "movement": [],
            "snapshot": {"before": self._player_positions()},
            "summary": "",
        }

        for player in active:
            bid = player.locked_bid or 0
            round_log["bids"][player.symbol] = {"name": player.name, "amount": bid}
            player.balance -= bid
            player.last_bid = bid
            player.locked_bid = None
            player.last_delta = -bid
            if player.balance < 0:
                player.status = "bankrupt"
                round_log["events"].append(f"{player.name} は入札支払いで残高がマイナスになり、破産負けになりました。")

        still_active = self.active_players()
        if still_active:
            highest_bid = max(player.last_bid or 0 for player in still_active)
            winners = [player for player in still_active if (player.last_bid or 0) == highest_bid]
            move_amount = self.current_roll // len(winners)
            round_log["winners"] = [player.symbol for player in winners]
            round_log["move_amount"] = move_amount
            round_log["summary"] = self._build_round_summary(winners, move_amount)
            self.activity_log.append(round_log["summary"])

            for winner in winners:
                before_pos = winner.position
                round_log["events"].extend(self._advance_player(winner, move_amount))
                round_log["movement"].append({"symbol": winner.symbol, "name": winner.name, "from": before_pos, "to": winner.position})

        round_log["snapshot"]["after"] = self._player_positions()
        round_log["snapshot"]["tape_claimed_by"] = self.tape_bonus_claimed_by
        self.round_history.append(round_log)
        self.awaiting_judge = False

        if self._should_finish():
            self._finish_game()
            return

        self.round_number += 1
        self.current_roll = self._roll_die()
        self.message = f"ラウンド {self.round_number}。出目は {self.current_roll}。全員が入札してください。"

    def _advance_player(self, player: AuctionPlayerState, steps: int) -> List[str]:
        events: List[str] = []
        if steps <= 0:
            events.append(f"{player.name} は同額トップでしたが 0 マス移動でした。")
            return events

        start_pos = player.position
        end_pos = min(self.track_length, player.position + steps)
        player.position = end_pos

        if self.tape_bonus_position is not None and self.tape_bonus_claimed_by is None and start_pos < self.tape_bonus_position <= end_pos:
            self.tape_bonus_claimed_by = player.symbol
            player.balance += self.tape_bonus_value
            player.last_delta += self.tape_bonus_value
            events.append(f"{player.name} が先着テープを最初に切り、{self.tape_bonus_value:,}円を獲得しました。")

        if end_pos >= self.track_length:
            events.extend(self._finish_player(player))
            return events

        tile = self.board_tiles[end_pos]
        if tile["kind"] in {"plus", "minus"}:
            player.balance += tile["value"]
            player.last_delta += tile["value"]
            if tile["value"] >= 0:
                events.append(f"{player.name} は青マスで {tile['value']:,}円を受け取りました。")
            else:
                events.append(f"{player.name} は赤マスで {abs(tile['value']):,}円を支払いました。")
        elif tile["kind"] == "forward":
            next_pos = min(self.track_length, player.position + tile["value"])
            player.position = next_pos
            events.append(f"{player.name} は進むマスでさらに {tile['value']} マス進みました。")
        elif tile["kind"] == "backward":
            next_pos = max(0, player.position + tile["value"])
            player.position = next_pos
            events.append(f"{player.name} は戻るマスで {abs(tile['value'])} マス戻りました。")
        else:
            events.append(f"{player.name} は空きマスに止まりました。")

        if player.position >= self.track_length:
            events.extend(self._finish_player(player))
            return events

        if player.balance < 0:
            player.status = "bankrupt"
            events.append(f"{player.name} はマス効果で残高がマイナスになり、破産負けになりました。")
        return events

    def _finish_player(self, player: AuctionPlayerState) -> List[str]:
        player.position = self.track_length
        player.status = "finished"
        self.finished_order.append(player.symbol)
        player.placement = len(self.finished_order)
        reward = self._finish_reward_for_place(player.placement)
        player.finish_reward = reward
        player.balance += reward
        player.last_delta += reward
        return [f"{player.name} が {player.placement} 位でゴールし、{reward:,}円を獲得しました。"]

    def _finish_reward_for_place(self, place: int) -> int:
        non_loser_count = len(self.non_loser_players())
        if place >= non_loser_count:
            return 0
        if place <= len(self.goal_rewards):
            return self.goal_rewards[place - 1]
        last_reward = self.goal_rewards[-1]
        while place > len(self.goal_rewards):
            last_reward = max(1_000, last_reward // 2)
            place -= 1
        return last_reward

    def _player_positions(self) -> Dict[str, int]:
        return {symbol: self.players[symbol].position for symbol in self.joined_symbols()}

    def _build_round_summary(self, winners: List[AuctionPlayerState], move_amount: int) -> str:
        if len(winners) == 1:
            return f"ラウンド {self.round_number}: {winners[0].name} が勝って {move_amount} マス進みました。"
        names = " / ".join(player.name for player in winners)
        return f"ラウンド {self.round_number}: {names} が勝って {move_amount} マスずつ進みました。"

    def _should_finish(self) -> bool:
        return len(self.active_players()) <= 1

    def _finish_game(self) -> None:
        self.game_over = True
        self.started = False
        self.results_revealed = False
        self.awaiting_judge = False
        self.winner_text = ""
        self.message = "試合終了です。結果を見るボタンで勝者を確認し、その後は感想戦モードに入れます。"

    def _show_results(self) -> None:
        if not self.game_over:
            raise GameError("まだ結果発表できません。")
        if self.results_revealed:
            return
        eligible = self.non_loser_players()
        if not eligible:
            self.winner_text = "全員が破産または降参で敗北しました。"
        else:
            best_balance = max(player.balance for player in eligible)
            winners = [player.name for player in eligible if player.balance == best_balance]
            self.winner_text = f"{' / '.join(winners)} の勝ちです。最終残高は {best_balance:,}円です。"
        self.results_revealed = True
        self.message = "結果発表が終わりました。感想戦で各ターンの動きと入札を確認できます。"

    def _parse_non_negative_int(self, raw: object, fallback: int, minimum: int = 0) -> int:
        if raw in {None, ""}:
            return fallback
        try:
            value = int(raw)
        except ValueError as exc:
            raise GameError("設定値は整数で入力してください。") from exc
        if value < minimum:
            raise GameError(f"{minimum} 以上の値を入力してください。")
        return value

    def _parse_int(self, raw: object, fallback: int) -> int:
        if raw in {None, ""}:
            return fallback
        try:
            return int(raw)
        except ValueError as exc:
            raise GameError("設定値は整数で入力してください。") from exc

    def _parse_optional_int(self, raw: object, minimum: int = 0) -> Optional[int]:
        if raw in {None, ""}:
            return None
        try:
            value = int(raw)
        except ValueError as exc:
            raise GameError("設定値は整数で入力してください。") from exc
        if value < minimum:
            raise GameError(f"{minimum} 以上の値を入力してください。")
        return value

    def _parse_goal_rewards(self, raw: object, fallback: List[int]) -> List[int]:
        text = str(raw).strip() if raw not in {None, ""} else ""
        if not text:
            return list(fallback)
        rewards = []
        for token in text.replace("\n", ",").split(","):
            token = token.strip()
            if not token:
                continue
            try:
                value = int(token)
            except ValueError as exc:
                raise GameError("ゴール報酬は整数をカンマ区切りで入力してください。") from exc
            if value < 0:
                raise GameError("ゴール報酬は0以上にしてください。")
            rewards.append(value)
        if not rewards:
            raise GameError("ゴール報酬を1つ以上入力してください。")
        return rewards

    def _settings_dict(self) -> dict:
        configured_tiles = self.plus_count + self.minus_count + self.forward_count + self.backward_count
        blank_count = max(0, self.track_length_setting - 1 - configured_tiles)
        return {
            "starting_balance": self.starting_balance,
            "dice_sides": self.current_roll_max,
            "track_length": self.track_length_setting,
            "plus_count": self.plus_count,
            "minus_count": self.minus_count,
            "forward_count": self.forward_count,
            "backward_count": self.backward_count,
            "forward_steps": self.forward_steps,
            "backward_steps": self.backward_steps,
            "blank_count": blank_count,
            "net_tile_total": self.net_tile_total,
            "money_tile_min": self.money_tile_min,
            "money_tile_max": self.money_tile_max,
            "tape_bonus_position": self.tape_bonus_position,
            "tape_bonus_value": self.tape_bonus_value,
            "goal_rewards": ",".join(str(value) for value in self.goal_rewards),
            "tile_layout_text": self.tile_layout_text,
            "quick_bids": self.quick_bids,
        }

    def _goal_reward_summary(self) -> List[dict]:
        non_loser_count = max(2, len(self.non_loser_players()) or len(self.joined_symbols()) or 2)
        results = []
        for index, reward in enumerate(self.goal_rewards, start=1):
            if index >= non_loser_count:
                break
            results.append({"place": index, "reward": reward})
        return results

    def to_public_dict(self, viewer_symbol: Optional[str] = None) -> dict:
        reveal_all = self.results_revealed
        viewer = viewer_symbol or ""
        ordered_symbols = self.joined_symbols()
        preview_track_length = self.track_length or self.track_length_setting
        preview_tape_position = self.tape_bonus_position if self.tape_bonus_position is not None else max(2, preview_track_length // 2)
        preview_tiles = self.board_tiles or self._build_board_tiles(
            preview_track_length,
            self.tile_layout_text,
            self.plus_count,
            self.minus_count,
            self.forward_count,
            self.backward_count,
            self.net_tile_total,
            self.money_tile_min,
            self.money_tile_max,
            shuffle_events=False,
            randomize_values=False,
        )
        return {
            "game_type": self.game_type,
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "results_revealed": self.results_revealed,
            "awaiting_judge": self.awaiting_judge,
            "message": self.message,
            "winner_text": self.winner_text if self.results_revealed else "",
            "round_number": self.round_number,
            "current_roll": self.current_roll,
            "current_roll_max": self.current_roll_max,
            "track_length": preview_track_length,
            "track_columns": SNAKE_COLUMNS,
            "board_tiles": preview_tiles,
            "tape_bonus_position": preview_tape_position,
            "tape_bonus_value": self.tape_bonus_value,
            "tape_bonus_claimed_by": self.tape_bonus_claimed_by,
            "quick_bids": self.quick_bids,
            "starting_balance": self.starting_balance,
            "goal_rewards": self._goal_reward_summary(),
            "settings": self._settings_dict(),
            "activity_log": self.activity_log[-8:],
            "round_history": self.round_history,
            "players": {symbol: self.players[symbol].to_public_dict(viewer, reveal_all) for symbol in ordered_symbols},
        }
