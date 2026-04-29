from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


SEAT_ORDER = [f"P{index}" for index in range(1, 13)]
TOPICS = [
    "かわいさ",
    "こわさ",
    "うれしさ",
    "まずさ",
    "速さ",
    "強さ",
    "しずかさ",
    "派手さ",
    "やさしさ",
    "懐かしさ",
    "行きたさ",
    "ドキドキ度",
]


@dataclass
class IkoPlayer:
    symbol: str
    name: str
    connected: bool = False

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
        }


class IkoGame:
    game_type = "iko"
    title = "iko"
    subtitle = "秘密の数字をお題に沿った一言で表し、みんなで小さい順に並べる協力ゲームです。"
    category = "classic"
    min_players = 2
    max_players = len(SEAT_ORDER)
    player_label = "2人以上"
    seat_order = list(SEAT_ORDER)
    allow_midgame_join = False
    host_control_actions = {"start_match", "next_round"}

    def __init__(self) -> None:
        self.players: Dict[str, IkoPlayer] = {}
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.round_number = 0
        self.topic = ""
        self.topic_options = list(TOPICS)
        self.secret_numbers: Dict[str, int] = {}
        self.submissions: Dict[str, dict] = {}
        self.arrangement: List[str] = []
        self.reveal_results: List[dict] = []
        self.success_streak = 0
        self.last_result = ""
        self.winner_text = ""
        self.message = "2人以上で開始できます。秘密の数字をことばで表して並び順を作ります。"
        self.history: List[str] = []

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
        connected = self.players[symbol].connected if symbol in self.players else False
        self.players[symbol] = IkoPlayer(symbol=symbol, name=cleaned[:24], connected=connected)
        if not self.started:
            self.message = (
                "この人数で開始できます。"
                if len(self.joined_symbols()) >= self.min_players
                else "2人以上そろうと開始できます。"
            )

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        if not self.started:
            self.message = (
                "この人数で開始できます。"
                if len(self.joined_symbols()) >= self.min_players
                else "2人以上そろうと開始できます。"
            )

    def reset_for_rematch(self) -> None:
        saved = {
            symbol: (player.name, player.connected)
            for symbol, player in self.players.items()
        }
        self.__init__()
        for symbol, (name, connected) in saved.items():
            self.players[symbol] = IkoPlayer(symbol=symbol, name=name, connected=connected)
        self.start_if_ready()

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        if action == "start_match":
            self.start_match(settings or {})
            return
        if action == "next_round":
            self.next_round(settings or {})
            return
        raise GameError("未対応のホスト操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        answer_text: Optional[str] = None,
        card_index: Optional[int] = None,
        direction: Optional[str] = None,
        **_: object,
    ) -> None:
        if action == "submit_clue":
            self._submit_clue(symbol, answer_text or "")
            return
        if action == "move_clue":
            self._move_clue(symbol, card_index, direction)
            return
        if action == "reveal_order":
            self._reveal_order(symbol)
            return
        if action == "resign":
            self._resign(symbol)
            return
        raise GameError("未対応の操作です。")

    def start_match(self, settings: dict) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("2人以上そろってから開始してください。")
        self.started = True
        self.game_over = False
        self.history = []
        self.success_streak = 0
        self.last_result = ""
        self.winner_text = ""
        self.round_number = 0
        self._begin_round(settings)

    def next_round(self, settings: dict) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.phase != "result":
            raise GameError("結果を確認してから次のラウンドに進んでください。")
        self._begin_round(settings)

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        arrangement = []
        for position, symbol in enumerate(self.arrangement):
            entry = self.submissions.get(symbol, {})
            arrangement.append(
                {
                    "symbol": symbol,
                    "name": self.players[symbol].name,
                    "clue": entry.get("clue", ""),
                    "submitted": bool(entry.get("submitted")),
                    "position": position,
                    "number": self.secret_numbers.get(symbol) if self.phase == "result" else None,
                    "correct": next((item["correct"] for item in self.reveal_results if item["symbol"] == symbol), None),
                }
            )

        return {
            "title": self.title,
            "game_type": self.game_type,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "round_number": self.round_number,
            "topic": self.topic,
            "topic_options": list(self.topic_options),
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {
                symbol: player.to_public_dict()
                for symbol, player in self.players.items()
            },
            "player_order": self.joined_symbols(),
            "viewer_secret_number": self.secret_numbers.get(viewer_symbol),
            "viewer_has_submitted": bool(self.submissions.get(viewer_symbol, {}).get("submitted")),
            "submissions": {
                symbol: {
                    "clue": self.submissions.get(symbol, {}).get("clue", ""),
                    "submitted": bool(self.submissions.get(symbol, {}).get("submitted")),
                }
                for symbol in self.joined_symbols()
            },
            "arrangement": arrangement,
            "reveal_results": list(self.reveal_results),
            "all_submitted": self._all_submitted(),
            "success_streak": self.success_streak,
            "last_result": self.last_result,
            "history": list(self.history),
        }

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in SEAT_ORDER if symbol in self.players]

    def _begin_round(self, settings: dict) -> None:
        self.round_number += 1
        self.phase = "clueing"
        self.topic = (settings.get("topic") or "").strip()[:24] or random.choice(TOPICS)
        self.secret_numbers = {}
        self.submissions = {}
        self.arrangement = self.joined_symbols()
        self.reveal_results = []
        self.last_result = ""
        self.winner_text = ""

        used_numbers = random.sample(range(1, 101), len(self.arrangement))
        for symbol, number in zip(self.arrangement, used_numbers):
            self.secret_numbers[symbol] = number
            self.submissions[symbol] = {"clue": "", "submitted": False}

        self.message = f"ラウンド {self.round_number}。お題は「{self.topic}」。自分の数字を直接言わずに一言で表してください。"
        self.history.append(f"ラウンド {self.round_number} 開始。お題: {self.topic}")

    def _submit_clue(self, symbol: str, clue_text: str) -> None:
        if not self.started or self.phase != "clueing":
            raise GameError("いまはヒント提出フェーズではありません。")
        clue = clue_text.strip()
        if not clue:
            raise GameError("ヒントを入力してください。")
        if any(char.isdigit() for char in clue):
            raise GameError("数字をそのまま書かずに表現してください。")

        self.submissions[symbol] = {
            "clue": clue[:40],
            "submitted": True,
        }
        self.message = f"{self.players[symbol].name} がヒントを出しました。"
        if self._all_submitted():
            self.phase = "arranging"
            self.message = "全員のヒントが出そろいました。相談して、小さい順になるように並べ替えてください。"

    def _move_clue(self, symbol: str, card_index: Optional[int], direction: Optional[str]) -> None:
        if not self.started or self.phase != "arranging":
            raise GameError("いまは並べ替えフェーズではありません。")
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        if card_index is None:
            raise GameError("動かすカードが見つかりません。")
        index = int(card_index)
        if index < 0 or index >= len(self.arrangement):
            raise GameError("動かす位置が不正です。")
        offset = -1 if direction == "left" else 1 if direction == "right" else 0
        target = index + offset
        if target < 0 or target >= len(self.arrangement):
            return
        self.arrangement[index], self.arrangement[target] = self.arrangement[target], self.arrangement[index]
        self.message = f"{self.players[symbol].name} が並び順を調整しました。"

    def _reveal_order(self, symbol: str) -> None:
        if not self.started or self.phase != "arranging":
            raise GameError("いまは公開フェーズに進めません。")
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")

        self.phase = "result"
        self.reveal_results = []
        previous = 0
        all_correct = True
        for arranged_symbol in self.arrangement:
            number = self.secret_numbers[arranged_symbol]
            correct = number >= previous
            if not correct:
                all_correct = False
            previous = max(previous, number)
            self.reveal_results.append(
                {
                    "symbol": arranged_symbol,
                    "name": self.players[arranged_symbol].name,
                    "clue": self.submissions[arranged_symbol]["clue"],
                    "number": number,
                    "correct": correct,
                }
            )

        if all_correct:
            self.success_streak += 1
            self.last_result = "成功"
            self.winner_text = "並び順成功です。みんなで数字の順番を当てられました。"
            self.message = f"成功。連続成功は {self.success_streak} 回です。"
        else:
            self.success_streak = 0
            self.last_result = "失敗"
            self.winner_text = "今回は順番がずれていました。次のラウンドでもう一度挑戦できます。"
            self.message = "失敗。順番が崩れていた場所を見直して次のラウンドへ進みましょう。"

        self.history.append(f"ラウンド {self.round_number}: {self.last_result}")

    def _resign(self, symbol: str) -> None:
        if symbol not in self.players:
            return
        del self.players[symbol]
        self.secret_numbers.pop(symbol, None)
        self.submissions.pop(symbol, None)
        self.arrangement = [item for item in self.arrangement if item != symbol]
        if len(self.joined_symbols()) < self.min_players:
            self.started = False
            self.phase = "waiting"
            self.message = "人数が足りなくなったので待機中に戻りました。"
            return
        self.message = f"{symbol} がルームを離れました。"

    def _all_submitted(self) -> bool:
        return bool(self.arrangement) and all(self.submissions.get(symbol, {}).get("submitted") for symbol in self.arrangement)
