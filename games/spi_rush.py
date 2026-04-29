from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from games.spi_quiz_bank import SPI_QUESTION_BANK


class GameError(ValueError):
    pass


SEAT_ORDER = [f"P{index}" for index in range(1, 7)]
DEFAULT_QUESTION_COUNT = 12
DEFAULT_TIME_LIMIT = 12
REVEAL_SECONDS = 3.5


@dataclass
class SpiRushPlayer:
    symbol: str
    name: str
    connected: bool = False
    score: int = 0
    streak: int = 0
    last_choice: int | None = None
    last_correct: bool = False

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "score": self.score,
            "streak": self.streak,
            "last_choice": self.last_choice,
            "last_correct": self.last_correct,
        }


class SpiRushGame:
    game_type = "spi_rush"
    title = "SPI Rush"
    subtitle = "SPI風の言語・非言語を早押し四択で競う、1人から遊べる対戦学習ゲームです。"
    category = "original"
    min_players = 1
    max_players = len(SEAT_ORDER)
    player_label = "1-6人"
    seat_order = list(SEAT_ORDER)
    allow_midgame_join = False
    host_control_actions = {"start_match", "update_settings", "next_question"}

    def __init__(self) -> None:
        self.players: Dict[str, SpiRushPlayer] = {}
        self.settings = {
            "category": "mixed",
            "question_count": DEFAULT_QUESTION_COUNT,
            "time_limit": DEFAULT_TIME_LIMIT,
        }
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.round_number = 0
        self.question_deadline: float | None = None
        self.reveal_deadline: float | None = None
        self.message = "出題分野と問題数を決めて、SPIの早押し対戦を始めましょう。"
        self.winner_text = ""
        self.question_set: List[dict] = []
        self.current_question: dict | None = None
        self.answers_this_round: Dict[str, dict] = {}
        self.question_winner_symbol = ""
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
        existing_score = self.players[symbol].score if symbol in self.players else 0
        existing_streak = self.players[symbol].streak if symbol in self.players else 0
        self.players[symbol] = SpiRushPlayer(
            symbol=symbol,
            name=cleaned[:24],
            connected=connected,
            score=existing_score,
            streak=existing_streak,
        )
        if not self.started:
            self.message = (
                "この人数で開始できます。"
                if len(self.joined_symbols()) >= self.min_players
                else "1人以上そろうと開始できます。"
            )

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        if not self.started:
            self.message = "この人数で開始できます。"

    def reset_for_rematch(self) -> None:
        saved = {
            symbol: (player.name, player.connected)
            for symbol, player in self.players.items()
        }
        saved_settings = dict(self.settings)
        self.__init__()
        self.settings.update(saved_settings)
        for symbol, (name, connected) in saved.items():
            self.players[symbol] = SpiRushPlayer(symbol=symbol, name=name, connected=connected)

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        settings = settings or {}
        if action == "update_settings":
            self.update_settings(settings)
            return
        if action == "start_match":
            self.start_match()
            return
        if action == "next_question":
            self.advance_if_needed()
            return
        raise GameError("未対応のホスト操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        card_index: Optional[int] = None,
        **_: object,
    ) -> None:
        if action == "answer_choice":
            self.submit_choice(symbol, card_index)
            return
        if action == "resign":
            self.resign(symbol)
            return
        raise GameError("未対応の操作です。")

    def update_settings(self, settings: dict) -> None:
        if self.started and not self.game_over:
            raise GameError("ゲーム中は設定を変更できません。")
        category = str(settings.get("category", self.settings["category"]))
        if category not in {"mixed", "verbal", "nonverbal"}:
            raise GameError("出題分野が不正です。")
        try:
            question_count = int(settings.get("question_count", self.settings["question_count"]))
            time_limit = int(settings.get("time_limit", self.settings["time_limit"]))
        except (TypeError, ValueError) as exc:
            raise GameError("問題数と制限時間は数字で入力してください。") from exc
        if question_count < 5 or question_count > 30:
            raise GameError("問題数は 5 から 30 の間で設定してください。")
        if time_limit < 5 or time_limit > 25:
            raise GameError("制限時間は 5 から 25 秒の間で設定してください。")
        self.settings.update(
            {
                "category": category,
                "question_count": question_count,
                "time_limit": time_limit,
            }
        )
        self.message = "設定を更新しました。"

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("1人以上そろってから開始してください。")

        pool = [
            question for question in SPI_QUESTION_BANK
            if self.settings["category"] == "mixed" or question["category"] == self.settings["category"]
        ]
        if len(pool) < self.settings["question_count"]:
            raise GameError("その条件では問題数が足りません。")

        self.started = True
        self.game_over = False
        self.phase = "question"
        self.round_number = 0
        self.question_set = random.sample(pool, self.settings["question_count"])
        self.history = []
        self.winner_text = ""
        for player in self.players.values():
            player.score = 0
            player.streak = 0
            player.last_choice = None
            player.last_correct = False
        self._advance_to_next_question()

    def submit_choice(self, symbol: str, card_index: Optional[int]) -> None:
        self._advance_time()
        if not self.started or self.game_over:
            raise GameError("いまは解答できません。")
        if self.phase != "question" or not self.current_question:
            raise GameError("いまは解答フェーズではありません。")
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        if symbol in self.answers_this_round:
            raise GameError("この問題にはすでに解答しています。")
        if card_index is None:
            raise GameError("選択肢を選んでください。")
        choice_index = int(card_index)
        if choice_index < 0 or choice_index >= len(self.current_question["choices"]):
            raise GameError("選択肢が不正です。")

        player = self.players[symbol]
        correct = choice_index == self.current_question["answer_index"]
        player.last_choice = choice_index
        player.last_correct = correct
        self.answers_this_round[symbol] = {"choice_index": choice_index, "correct": correct}

        if correct:
            elapsed = max(0.0, time.time() - (self.question_deadline - self.settings["time_limit"]))
            base_score = max(40, 120 - int(elapsed * 10))
            streak_bonus = min(player.streak * 5, 20)
            gain = base_score + streak_bonus
            player.score += gain
            player.streak += 1
            self.question_winner_symbol = symbol
            self.phase = "reveal"
            self.reveal_deadline = time.time() + REVEAL_SECONDS
            self.message = f"{player.name} が正解。+{gain} 点。"
            self.history.append(
                f"Q{self.round_number}: {player.name} 正解 (+{gain}) / 正答 {self.current_question['choices'][self.current_question['answer_index']]}"
            )
            for other_symbol, other_player in self.players.items():
                if other_symbol != symbol and other_symbol not in self.answers_this_round:
                    other_player.streak = 0
            return

        player.score = max(0, player.score - 5)
        player.streak = 0
        self.message = f"{player.name} は不正解。-5 点。"

        unanswered = [joined for joined in self.joined_symbols() if joined not in self.answers_this_round]
        if not unanswered:
            self._reveal_without_winner("全員が不正解でした。")

    def advance_if_needed(self) -> None:
        self._advance_time(force=True)

    def resign(self, symbol: str) -> None:
        if symbol not in self.players:
            return
        leaving_name = self.players[symbol].name
        del self.players[symbol]
        self.answers_this_round.pop(symbol, None)
        if len(self.joined_symbols()) < self.min_players:
            self.started = False
            self.game_over = False
            self.phase = "waiting"
            self.message = "人数が足りなくなったため待機中に戻りました。"
            return
        self.message = f"{leaving_name} がルームを離れました。"

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        self._advance_time()
        current = self.current_question or {
            "prompt": "",
            "choices": [],
            "answer_index": 0,
            "explanation": "",
            "category": self.settings["category"],
        }
        active_players = [self.players[symbol] for symbol in self.joined_symbols()]
        leader = max(active_players, key=lambda item: item.score, default=None)
        return {
            "title": self.title,
            "game_type": self.game_type,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "round_number": self.round_number,
            "question_count": len(self.question_set),
            "message": self.message,
            "winner_text": self.winner_text,
            "settings": dict(self.settings),
            "question_deadline": self.question_deadline,
            "reveal_deadline": self.reveal_deadline,
            "current_question": {
                "prompt": current["prompt"],
                "choices": list(current["choices"]),
                "answer_index": current["answer_index"] if self.phase in {"reveal", "finished"} else None,
                "explanation": current["explanation"] if self.phase in {"reveal", "finished"} else "",
                "category": current["category"],
            },
            "question_winner_symbol": self.question_winner_symbol,
            "leader_name": leader.name if leader else "",
            "leader_score": leader.score if leader else 0,
            "players": {
                symbol: player.to_public_dict()
                for symbol, player in self.players.items()
            },
            "player_order": self.joined_symbols(),
            "answers_this_round": dict(self.answers_this_round),
            "viewer_has_answered": viewer_symbol in self.answers_this_round,
            "history": list(self.history),
        }

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in SEAT_ORDER if symbol in self.players]

    def _advance_to_next_question(self) -> None:
        self.round_number += 1
        if self.round_number > len(self.question_set):
            self._finish_match()
            return
        self.current_question = self.question_set[self.round_number - 1]
        self.phase = "question"
        self.question_deadline = time.time() + self.settings["time_limit"]
        self.reveal_deadline = None
        self.question_winner_symbol = ""
        self.answers_this_round = {}
        for player in self.players.values():
            player.last_choice = None
            player.last_correct = False
        label = "言語" if self.current_question["category"] == "verbal" else "非言語"
        self.message = f"第 {self.round_number} 問 ({label})。早押しで答えてください。"

    def _finish_match(self) -> None:
        self.started = False
        self.game_over = True
        self.phase = "finished"
        self.question_deadline = None
        self.reveal_deadline = None
        rankings = sorted(self.players.values(), key=lambda item: (-item.score, item.name))
        if rankings:
            top_score = rankings[0].score
            winners = [player.name for player in rankings if player.score == top_score]
            if len(winners) == 1:
                self.winner_text = f"{winners[0]} の勝ちです。"
            else:
                self.winner_text = "引き分けです。トップは " + " / ".join(winners)
        else:
            self.winner_text = "試合終了です。"
        self.message = self.winner_text

    def _reveal_without_winner(self, message: str) -> None:
        self.phase = "reveal"
        self.reveal_deadline = time.time() + REVEAL_SECONDS
        self.question_winner_symbol = ""
        self.message = message
        correct_choice = self.current_question["choices"][self.current_question["answer_index"]]
        self.history.append(f"Q{self.round_number}: 正答は {correct_choice}")

    def _advance_time(self, force: bool = False) -> None:
        now = time.time()
        if self.phase == "question" and self.question_deadline is not None and (force or now >= self.question_deadline):
            if not self.question_winner_symbol:
                self._reveal_without_winner("時間切れです。")
            return
        if self.phase == "reveal" and self.reveal_deadline is not None and (force or now >= self.reveal_deadline):
            self._advance_to_next_question()
