from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


SEAT_ORDER = [f"P{index}" for index in range(1, 13)]
ROUND_SECONDS = 60
INITIALS = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわ")
PROMPTS = [
    "美しいもの", "怖いもの", "やさしいもの", "大切なもの", "テンションが上がるもの", "懐かしいもの",
    "子どものころ好きだったもの", "大人っぽいもの", "朝に見たいもの", "夜に似合うもの", "春っぽいもの", "夏っぽいもの",
    "秋っぽいもの", "冬っぽいもの", "音が印象的なもの", "においが印象的なもの", "触ってみたいもの", "一度は見てみたいもの",
    "学校でよく見るもの", "駅で見かけるもの", "旅行でうれしいもの", "緊張する場面", "がんばった記憶", "小さい幸せ",
    "人に自慢したいもの", "誰でも一度は経験しそうなこと", "名前がかっこいいもの", "かわいいもの", "強そうなもの", "速そうなもの",
    "丸いもの", "細長いもの", "赤いもの", "青いもの", "白いもの", "黒いもの", "甘いもの", "苦いもの",
    "プレゼントでもらうとうれしいもの", "なくすと困るもの", "写真を撮りたくなるもの", "映画に出てきそうなもの", "秘密にしたいこと",
    "覚えておきたいこと", "日本らしいもの", "世界に誇れそうなもの", "笑ってしまうもの", "泣けるもの", "頭がよさそうなもの",
    "意外と身近なもの", "ちょっとぜいたくなもの", "一人で楽しめるもの", "みんなで盛り上がるもの", "昔からあるもの", "未来っぽいもの",
    "長生きしそうなもの", "一度は言ってみたい言葉", "忘れられない思い出", "試してみたいこと", "プロっぽいもの", "健康によさそうなもの",
]


@dataclass
class MorningAnswerPlayer:
    symbol: str
    name: str
    connected: bool = False
    score: int = 0

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "score": self.score,
        }


class MorningAnswerGame:
    game_type = "morning_answer"
    title = "Morning Answer"
    subtitle = "頭文字とお題に合わせて回答し、マスターが一番よかった答えを選ぶ会話ゲーム。"
    category = "classic"
    min_players = 2
    max_players = len(SEAT_ORDER)
    player_label = "2人～"
    seat_order = list(SEAT_ORDER)
    allow_midgame_join = True
    host_control_actions = {"start_match", "toggle_pause", "next_round"}

    def __init__(self) -> None:
        self.players: Dict[str, MorningAnswerPlayer] = {}
        self.started = False
        self.game_over = False
        self.paused = False
        self.pause_remaining_seconds = ROUND_SECONDS
        self.message = "2人以上集まったら開始できます。"
        self.winner_text = ""
        self.round_number = 0
        self.master_symbol: Optional[str] = None
        self.prompt_initial = ""
        self.prompt_theme = ""
        self.phase = "waiting"
        self.round_deadline: Optional[float] = None
        self.submissions: Dict[str, dict] = {}
        self.last_round_summary: List[str] = []
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
        cleaned = name.strip() or symbol
        self.players[symbol] = MorningAnswerPlayer(symbol=symbol, name=cleaned[:24])
        if self.started and symbol not in self.submissions:
            self.submissions[symbol] = {"text": "", "opened": False, "is_winner": False}
        self._refresh_waiting_message()

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        self._advance_time()
        self._refresh_waiting_message()

    def reset_for_rematch(self) -> None:
        saved_players = {
            symbol: (player.name, player.connected, player.score)
            for symbol, player in self.players.items()
        }
        self.__init__()
        for symbol, (name, connected, score) in saved_players.items():
            self.players[symbol] = MorningAnswerPlayer(
                symbol=symbol,
                name=name,
                connected=connected,
                score=score,
            )
        self._refresh_waiting_message()

    def apply_host_action(self, action: str, **_: object) -> None:
        self._advance_time()
        if action == "start_match":
            self.start_match()
            return
        if action == "toggle_pause":
            self.toggle_pause()
            return
        if action == "begin_reveal":
            self.begin_reveal()
            return
        if action == "next_round":
            self.next_round()
            return
        raise GameError("不明な管理操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        answer_text: Optional[str] = None,
        winner_symbols: Optional[List[str]] = None,
        **_: object,
    ) -> None:
        self._advance_time()
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")

        if action == "submit_answer":
            self._submit_answer(symbol, answer_text or "")
            return
        if action == "open_answer":
            self._open_answer(symbol)
            return
        if action == "begin_reveal":
            self._begin_reveal_by_player(symbol)
            return
        if action == "choose_winners":
            self._choose_winners(symbol, winner_symbols or [])
            return
        if action == "resign":
            self._resign(symbol)
            return
        raise GameError("不明な操作です。")

    def start_match(self) -> None:
        if len(self.joined_symbols()) < self.min_players:
            raise GameError("2人以上集まると開始できます。")
        self.started = True
        self.game_over = False
        self.master_symbol = self.joined_symbols()[0]
        self.history = []
        self.last_round_summary = []
        self._begin_round()

    def toggle_pause(self) -> None:
        if not self.started:
            raise GameError("ゲーム開始後に使えます。")
        if self.phase not in {"writing", "paused"}:
            raise GameError("回答時間だけ一時停止できます。")
        if self.paused:
            self.paused = False
            self.phase = "writing"
            self.round_deadline = time.time() + self.pause_remaining_seconds
            self.message = "一時停止を解除しました。回答を続けてください。"
        else:
            self.paused = True
            self.phase = "paused"
            if self.round_deadline is not None:
                self.pause_remaining_seconds = max(0, int(self.round_deadline - time.time()))
            self.round_deadline = None
            self.message = "一時停止中です。"

    def next_round(self) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.phase != "finished":
            raise GameError("勝者選出が終わってから次に進めます。")
        self._rotate_master()
        self._begin_round()

    def begin_reveal(self) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.phase not in {"writing", "paused"}:
            raise GameError("回答フェーズ中だけ公開に進めます。")
        self.paused = False
        self.round_deadline = None
        self.phase = "revealing"
        self.message = "公開フェーズです。回答した人からオープンしてください。"

    def _begin_reveal_by_player(self, symbol: str) -> None:
        if symbol != self.master_symbol:
            raise GameError("公開へ進めるのはこのラウンドのマスターだけです。")
        self.begin_reveal()

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        self._advance_time()
        active_symbols = self.joined_symbols()
        crown_score = max((self.players[symbol].score for symbol in active_symbols), default=0)
        players = []
        for symbol in active_symbols:
            player = self.players[symbol]
            submission = self.submissions.get(symbol, {})
            players.append(
                {
                    **player.to_public_dict(),
                    "is_master": symbol == self.master_symbol,
                    "has_crown": crown_score > 0 and player.score == crown_score,
                    "submitted": bool(submission.get("text")),
                    "opened": bool(submission.get("opened")),
                    "answer": submission.get("text") if submission.get("opened") else None,
                    "is_winner": bool(submission.get("is_winner")),
                }
            )

        return {
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "paused": self.paused,
            "phase": self.phase,
            "round_number": self.round_number,
            "master_symbol": self.master_symbol,
            "prompt_initial": self.prompt_initial,
            "prompt_theme": self.prompt_theme,
            "round_seconds": ROUND_SECONDS,
            "remaining_seconds": self._remaining_seconds(),
            "round_deadline": self.round_deadline,
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {player["symbol"]: player for player in players},
            "player_order": [player["symbol"] for player in players],
            "submissions": [
                {
                    "symbol": symbol,
                    "name": self.players[symbol].name,
                    "opened": bool(self.submissions.get(symbol, {}).get("opened")),
                    "text": self.submissions.get(symbol, {}).get("text") if self.submissions.get(symbol, {}).get("opened") else None,
                    "is_winner": bool(self.submissions.get(symbol, {}).get("is_winner")),
                }
                for symbol in active_symbols
            ],
            "viewer_symbol": viewer_symbol,
            "viewer_is_master": viewer_symbol == self.master_symbol,
            "viewer_has_submitted": bool(self.submissions.get(viewer_symbol, {}).get("text")),
            "viewer_has_opened": bool(self.submissions.get(viewer_symbol, {}).get("opened")),
            "all_opened": self._all_opened(),
            "history": list(self.history),
            "last_round_summary": list(self.last_round_summary),
        }

    def joined_symbols(self) -> List[str]:
        return [symbol for symbol in self.seat_order if symbol in self.players]

    def _refresh_waiting_message(self) -> None:
        if self.started:
            return
        self.message = (
            "2人以上集まったら、部屋を作った人が開始してください。"
            if len(self.joined_symbols()) >= self.min_players
            else "2人以上集まると開始できます。"
        )

    def _begin_round(self) -> None:
        self.round_number += 1
        self.phase = "writing"
        self.paused = False
        self.pause_remaining_seconds = ROUND_SECONDS
        self.prompt_initial = random.choice(INITIALS)
        self.prompt_theme = random.choice(PROMPTS)
        self.round_deadline = time.time() + ROUND_SECONDS
        self.submissions = {
            symbol: {"text": "", "opened": False, "is_winner": False}
            for symbol in self.joined_symbols()
        }
        master_name = self.players[self.master_symbol].name if self.master_symbol in self.players else "マスター"
        self.winner_text = ""
        self.message = f"{master_name} がマスターです。「{self.prompt_initial}」で始まる「{self.prompt_theme}」を考えてください。"
        self.history.append(
            f"第{self.round_number}回: {master_name} がマスター / お題「{self.prompt_initial}で始まる {self.prompt_theme}」"
        )

    def _advance_time(self) -> None:
        if self.phase == "writing" and not self.paused and self.round_deadline is not None and time.time() >= self.round_deadline:
            self.round_deadline = None
            self.message = "時間は終了しました。マスターが公開へ進むを押してください。"

    def _remaining_seconds(self) -> int:
        if self.phase == "paused":
            return self.pause_remaining_seconds
        if self.phase != "writing" or self.round_deadline is None:
            return 0
        return max(0, int(self.round_deadline - time.time()))

    def _submit_answer(self, symbol: str, answer_text: str) -> None:
        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.phase != "writing":
            raise GameError("いまは回答入力の時間ではありません。")
        answer = answer_text.strip()
        if not answer:
            raise GameError("回答を入力してください。")
        self.submissions[symbol]["text"] = answer[:40]
        self.message = f"{self.players[symbol].name} が回答しました。"
        self._advance_time()

    def _open_answer(self, symbol: str) -> None:
        if self.phase != "revealing":
            raise GameError("いまはオープンの時間ではありません。")
        if not self.submissions.get(symbol, {}).get("text"):
            raise GameError("先に回答を入力してください。")
        self.submissions[symbol]["opened"] = True
        self.message = f"{self.players[symbol].name} の回答が公開されました。"
        if self._all_opened():
            self.phase = "judging"
            self.message = "全員の回答が公開されました。マスターがよかった回答を選んでください。"

    def _choose_winners(self, symbol: str, winner_symbols: List[str]) -> None:
        if symbol != self.master_symbol:
            raise GameError("勝者を選べるのは今のマスターだけです。")
        if self.phase != "judging":
            raise GameError("まだ勝者を選ぶ段階ではありません。")
        valid_winners = [winner for winner in winner_symbols if winner in self.players and self.submissions.get(winner, {}).get("opened")]
        if not valid_winners:
            raise GameError("少なくとも1人は選んでください。")

        for submission in self.submissions.values():
            submission["is_winner"] = False

        winner_names = []
        for winner in valid_winners:
            self.submissions[winner]["is_winner"] = True
            self.players[winner].score += 1
            winner_names.append(self.players[winner].name)

        self.phase = "finished"
        self.last_round_summary = [
            f"{self.players[symbol].name}: {self.submissions[symbol]['text']}"
            for symbol in self.joined_symbols()
            if self.submissions[symbol]["text"]
        ]
        joined_names = " / ".join(winner_names)
        self.winner_text = f"第{self.round_number}回のベスト回答: {joined_names}"
        self.message = "次のラウンドへ進めます。"
        self.history.append(self.winner_text)

    def _resign(self, symbol: str) -> None:
        if symbol not in self.players:
            return
        leaving_name = self.players[symbol].name
        del self.players[symbol]
        self.submissions.pop(symbol, None)

        if len(self.joined_symbols()) < self.min_players:
            self.started = False
            self.phase = "waiting"
            self.master_symbol = self.joined_symbols()[0] if self.joined_symbols() else None
            self.message = "人数が足りなくなりました。2人以上集まると再開できます。"
            return

        if symbol == self.master_symbol:
            self._rotate_master()

        self.message = f"{leaving_name} が退室しました。"
        if self.phase == "revealing" and self._all_opened():
            self.phase = "judging"
            self.message = "全員の回答が公開されました。マスターがよかった回答を選んでください。"

    def _rotate_master(self) -> None:
        active = self.joined_symbols()
        if not active:
            self.master_symbol = None
            return
        if self.master_symbol not in active:
            self.master_symbol = active[0]
            return
        current_index = active.index(self.master_symbol)
        self.master_symbol = active[(current_index + 1) % len(active)]

    def _all_submitted(self) -> bool:
        active = self.joined_symbols()
        return bool(active) and all(self.submissions.get(symbol, {}).get("text") for symbol in active)

    def _all_opened(self) -> bool:
        active = self.joined_symbols()
        ready = [symbol for symbol in active if self.submissions.get(symbol, {}).get("text")]
        return bool(ready) and len(ready) == len(active) and all(self.submissions[symbol].get("opened") for symbol in active)
