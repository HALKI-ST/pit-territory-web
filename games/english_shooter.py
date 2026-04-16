from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from games.english_shooter_extra_bank import EXTRA_WORD_BANK


class GameError(ValueError):
    pass


SEAT_ORDER = ["P1"]
TOTAL_TIME_SECONDS = 60
TRANSLATION_LIMIT_SECONDS = 5
ENEMY_DEFEAT_BONUS_SECONDS = 30
DIRECT_HIT_DAMAGE = 5
SPELLING_HIT_DAMAGE = 1
ENEMY_LINEUP = [
    {"name": "Scout Slime", "jp_name": "偵察スライム", "hp": 10, "boss": False},
    {"name": "Armor Bat", "jp_name": "装甲コウモリ", "hp": 14, "boss": False},
    {"name": "Phantom Knight", "jp_name": "幻影ナイト", "hp": 18, "boss": False},
    {"name": "Storm Golem", "jp_name": "嵐のゴーレム", "hp": 22, "boss": False},
    {"name": "Final Dragon", "jp_name": "ラスボスドラゴン", "hp": 28, "boss": True},
]
WORD_BANK = [
    {"english": "ability", "japanese": ["能力"]},
    {"english": "absorb", "japanese": ["吸収する"]},
    {"english": "abundant", "japanese": ["豊富な"]},
    {"english": "accurate", "japanese": ["正確な"]},
    {"english": "achieve", "japanese": ["達成する"]},
    {"english": "acquire", "japanese": ["習得する", "得る"]},
    {"english": "adapt", "japanese": ["適応する"]},
    {"english": "additional", "japanese": ["追加の"]},
    {"english": "adjust", "japanese": ["調整する"]},
    {"english": "admire", "japanese": ["感心する"]},
    {"english": "advance", "japanese": ["前進する", "進歩する"]},
    {"english": "advantage", "japanese": ["利点"]},
    {"english": "affect", "japanese": ["影響する"]},
    {"english": "agriculture", "japanese": ["農業"]},
    {"english": "ancient", "japanese": ["古代の"]},
    {"english": "announce", "japanese": ["発表する"]},
    {"english": "anxious", "japanese": ["不安な"]},
    {"english": "apologize", "japanese": ["謝る"]},
    {"english": "apparent", "japanese": ["明らかな"]},
    {"english": "application", "japanese": ["応募", "申請"]},
    {"english": "appreciate", "japanese": ["感謝する", "正しく理解する"]},
    {"english": "approach", "japanese": ["近づく", "取り組み"]},
    {"english": "appropriate", "japanese": ["適切な"]},
    {"english": "approve", "japanese": ["承認する"]},
    {"english": "argument", "japanese": ["議論", "口論"]},
    {"english": "arrange", "japanese": ["手配する", "整理する"]},
    {"english": "artificial", "japanese": ["人工の"]},
    {"english": "aspect", "japanese": ["側面"]},
    {"english": "assist", "japanese": ["助ける", "支援する"]},
    {"english": "assume", "japanese": ["想定する"]},
    {"english": "attempt", "japanese": ["試みる", "試み"]},
    {"english": "attractive", "japanese": ["魅力的な"]},
    {"english": "authority", "japanese": ["権威", "当局"]},
    {"english": "available", "japanese": ["利用できる"]},
    {"english": "avoid", "japanese": ["避ける"]},
    {"english": "aware", "japanese": ["気づいて"]},
    {"english": "benefit", "japanese": ["利益", "恩恵"]},
    {"english": "brief", "japanese": ["簡潔な"]},
    {"english": "calculate", "japanese": ["計算する"]},
    {"english": "candidate", "japanese": ["候補者"]},
    {"english": "capacity", "japanese": ["容量", "能力"]},
    {"english": "category", "japanese": ["分類"]},
    {"english": "challenge", "japanese": ["挑戦"]},
    {"english": "circumstance", "japanese": ["状況"]},
    {"english": "civilization", "japanese": ["文明"]},
    {"english": "combine", "japanese": ["組み合わせる"]},
    {"english": "comment", "japanese": ["意見", "コメント"]},
    {"english": "commerce", "japanese": ["商業"]},
    {"english": "compete", "japanese": ["競争する"]},
    {"english": "complex", "japanese": ["複雑な"]},
    {"english": "concentrate", "japanese": ["集中する"]},
    {"english": "concern", "japanese": ["懸念", "関心"]},
    {"english": "conduct", "japanese": ["行う", "実施する"]},
    {"english": "confident", "japanese": ["自信がある"]},
    {"english": "confirm", "japanese": ["確認する"]},
    {"english": "consequence", "japanese": ["結果"]},
    {"english": "consider", "japanese": ["考慮する"]},
    {"english": "constant", "japanese": ["一定の"]},
    {"english": "construct", "japanese": ["建設する"]},
    {"english": "consume", "japanese": ["消費する"]},
    {"english": "contemporary", "japanese": ["現代の"]},
    {"english": "contribute", "japanese": ["貢献する"]},
    {"english": "convince", "japanese": ["納得させる"]},
    {"english": "critical", "japanese": ["重大な", "批判的な"]},
    {"english": "curious", "japanese": ["好奇心の強い"]},
    {"english": "decline", "japanese": ["減少する", "断る"]},
    {"english": "define", "japanese": ["定義する"]},
    {"english": "delay", "japanese": ["遅らせる", "遅延"]},
    {"english": "deliver", "japanese": ["配達する"]},
    {"english": "demand", "japanese": ["要求", "需要"]},
    {"english": "demonstrate", "japanese": ["実証する"]},
    {"english": "deny", "japanese": ["否定する"]},
    {"english": "departure", "japanese": ["出発"]},
    {"english": "derive", "japanese": ["引き出す", "由来する"]},
    {"english": "deserve", "japanese": ["値する"]},
    {"english": "despite", "japanese": ["にもかかわらず"]},
    {"english": "destroy", "japanese": ["破壊する"]},
    {"english": "detail", "japanese": ["詳細"]},
    {"english": "device", "japanese": ["装置"]},
    {"english": "differ", "japanese": ["異なる"]},
    {"english": "disappear", "japanese": ["消える"]},
    {"english": "disaster", "japanese": ["災害"]},
    {"english": "discipline", "japanese": ["規律", "学問分野"]},
    {"english": "discover", "japanese": ["発見する"]},
    {"english": "distant", "japanese": ["遠い"]},
    {"english": "distribute", "japanese": ["配る", "分配する"]},
    {"english": "domestic", "japanese": ["国内の"]},
    {"english": "efficient", "japanese": ["効率的な"]},
    {"english": "eliminate", "japanese": ["排除する"]},
    {"english": "emerge", "japanese": ["現れる"]},
    {"english": "emotion", "japanese": ["感情"]},
    {"english": "emphasize", "japanese": ["強調する"]},
    {"english": "enable", "japanese": ["可能にする"]},
    {"english": "encounter", "japanese": ["遭遇する"]},
    {"english": "encourage", "japanese": ["励ます"]},
    {"english": "enormous", "japanese": ["巨大な"]},
    {"english": "entire", "japanese": ["全体の"]},
    {"english": "environment", "japanese": ["環境"]},
    {"english": "essential", "japanese": ["不可欠な"]},
    {"english": "estimate", "japanese": ["見積もる"]},
    {"english": "evidence", "japanese": ["証拠"]},
    {"english": "evolve", "japanese": ["進化する"]},
    {"english": "examine", "japanese": ["調べる"]},
    {"english": "exception", "japanese": ["例外"]},
    {"english": "exchange", "japanese": ["交換する", "交換"]},
    {"english": "expand", "japanese": ["拡大する"]},
    {"english": "expense", "japanese": ["費用"]},
    {"english": "explore", "japanese": ["探検する", "探る"]},
    {"english": "express", "japanese": ["表現する"]},
    {"english": "extreme", "japanese": ["極端な"]},
    {"english": "facility", "japanese": ["施設"]},
    {"english": "factor", "japanese": ["要因"]},
    {"english": "familiar", "japanese": ["よく知られた"]},
    {"english": "feature", "japanese": ["特徴"]},
    {"english": "flexible", "japanese": ["柔軟な"]},
    {"english": "focus", "japanese": ["集中する", "焦点"]},
    {"english": "frequent", "japanese": ["頻繁な"]},
    {"english": "fundamental", "japanese": ["基本的な"]},
    {"english": "generate", "japanese": ["生み出す"]},
    {"english": "generous", "japanese": ["気前のよい"]},
    {"english": "gradually", "japanese": ["徐々に"]},
    {"english": "guarantee", "japanese": ["保証する", "保証"]},
    {"english": "harmful", "japanese": ["有害な"]},
    {"english": "hesitate", "japanese": ["ためらう"]},
    {"english": "identify", "japanese": ["特定する"]},
    {"english": "ignore", "japanese": ["無視する"]},
    {"english": "immediate", "japanese": ["即座の"]},
    {"english": "impact", "japanese": ["影響", "衝撃"]},
    {"english": "improve", "japanese": ["改善する"]},
    {"english": "include", "japanese": ["含む"]},
    {"english": "increase", "japanese": ["増やす", "増加"]},
    {"english": "independent", "japanese": ["独立した"]},
    {"english": "individual", "japanese": ["個人の"]},
    {"english": "industry", "japanese": ["産業"]},
    {"english": "inevitable", "japanese": ["避けられない"]},
    {"english": "influence", "japanese": ["影響", "影響する"]},
    {"english": "inform", "japanese": ["知らせる"]},
    {"english": "initial", "japanese": ["最初の"]},
    {"english": "injure", "japanese": ["傷つける"]},
    {"english": "inquiry", "japanese": ["問い合わせ", "調査"]},
    {"english": "insist", "japanese": ["主張する"]},
    {"english": "inspire", "japanese": ["刺激を与える"]},
    {"english": "instance", "japanese": ["例"]},
    {"english": "intend", "japanese": ["意図する"]},
    {"english": "intense", "japanese": ["激しい"]},
    {"english": "interpret", "japanese": ["解釈する"]},
    {"english": "interrupt", "japanese": ["妨げる"]},
    {"english": "involve", "japanese": ["含む", "関与させる"]},
    {"english": "isolated", "japanese": ["孤立した"]},
    {"english": "justice", "japanese": ["正義"]},
    {"english": "laboratory", "japanese": ["研究室"]},
    {"english": "logical", "japanese": ["論理的な"]},
    {"english": "maintain", "japanese": ["維持する"]},
    {"english": "majority", "japanese": ["大多数"]},
    {"english": "manufacture", "japanese": ["製造する"]},
    {"english": "measure", "japanese": ["測る", "対策"]},
    {"english": "medical", "japanese": ["医療の"]},
    {"english": "mental", "japanese": ["精神の"]},
    {"english": "mention", "japanese": ["述べる"]},
    {"english": "modify", "japanese": ["修正する"]},
    {"english": "monitor", "japanese": ["監視する"]},
    {"english": "mutual", "japanese": ["相互の"]},
    {"english": "narrow", "japanese": ["狭い"]},
    {"english": "necessary", "japanese": ["必要な"]},
    {"english": "neglect", "japanese": ["怠る"]},
    {"english": "obvious", "japanese": ["明白な"]},
    {"english": "occasion", "japanese": ["機会"]},
    {"english": "occupy", "japanese": ["占める"]},
    {"english": "ordinary", "japanese": ["普通の"]},
    {"english": "organize", "japanese": ["組織する", "整理する"]},
    {"english": "original", "japanese": ["元の", "独創的な"]},
    {"english": "participate", "japanese": ["参加する"]},
    {"english": "particular", "japanese": ["特定の"]},
    {"english": "patient", "japanese": ["忍耐強い", "患者"]},
    {"english": "perform", "japanese": ["行う", "演じる"]},
    {"english": "permit", "japanese": ["許可する"]},
    {"english": "persuade", "japanese": ["説得する"]},
    {"english": "phenomenon", "japanese": ["現象"]},
    {"english": "policy", "japanese": ["方針", "政策"]},
    {"english": "portion", "japanese": ["部分"]},
    {"english": "practical", "japanese": ["実用的な"]},
    {"english": "predict", "japanese": ["予測する"]},
    {"english": "preserve", "japanese": ["保護する", "保存する"]},
    {"english": "prevent", "japanese": ["防ぐ"]},
    {"english": "primary", "japanese": ["主要な"]},
    {"english": "principle", "japanese": ["原理", "原則"]},
    {"english": "proceed", "japanese": ["進む"]},
    {"english": "process", "japanese": ["過程"]},
    {"english": "produce", "japanese": ["生産する"]},
    {"english": "professional", "japanese": ["専門的な", "職業の"]},
    {"english": "profit", "japanese": ["利益"]},
    {"english": "promote", "japanese": ["促進する"]},
    {"english": "proof", "japanese": ["証明"]},
    {"english": "property", "japanese": ["財産", "特性"]},
    {"english": "protect", "japanese": ["守る"]},
    {"english": "purchase", "japanese": ["購入する", "購入"]},
    {"english": "recognize", "japanese": ["認識する"]},
    {"english": "recommend", "japanese": ["勧める"]},
    {"english": "recover", "japanese": ["回復する"]},
    {"english": "reduce", "japanese": ["減らす"]},
    {"english": "reflect", "japanese": ["反映する"]},
    {"english": "refuse", "japanese": ["拒否する"]},
    {"english": "regard", "japanese": ["みなす"]},
    {"english": "region", "japanese": ["地域"]},
    {"english": "regular", "japanese": ["定期的な"]},
    {"english": "release", "japanese": ["解放する", "発売する"]},
    {"english": "reliable", "japanese": ["信頼できる"]},
    {"english": "remain", "japanese": ["残る"]},
    {"english": "remove", "japanese": ["取り除く"]},
    {"english": "replace", "japanese": ["置き換える"]},
    {"english": "require", "japanese": ["必要とする"]},
    {"english": "research", "japanese": ["研究"]},
    {"english": "resource", "japanese": ["資源"]},
    {"english": "respond", "japanese": ["反応する", "返答する"]},
    {"english": "restore", "japanese": ["回復させる"]},
    {"english": "restrict", "japanese": ["制限する"]},
    {"english": "reveal", "japanese": ["明らかにする"]},
    {"english": "routine", "japanese": ["日課"]},
    {"english": "satisfy", "japanese": ["満足させる"]},
    {"english": "scheme", "japanese": ["計画"]},
    {"english": "significant", "japanese": ["重要な"]},
    {"english": "similar", "japanese": ["似ている"]},
    {"english": "solve", "japanese": ["解決する"]},
    {"english": "specific", "japanese": ["具体的な", "特定の"]},
    {"english": "stable", "japanese": ["安定した"]},
    {"english": "standard", "japanese": ["標準"]},
    {"english": "strategy", "japanese": ["戦略"]},
    {"english": "sufficient", "japanese": ["十分な"]},
    {"english": "survive", "japanese": ["生き残る"]},
    {"english": "transfer", "japanese": ["移す", "移転する"]},
    {"english": "transform", "japanese": ["変える", "変形させる"]},
    {"english": "transport", "japanese": ["輸送する"]},
    {"english": "typical", "japanese": ["典型的な"]},
    {"english": "universal", "japanese": ["普遍的な"]},
    {"english": "valuable", "japanese": ["価値のある"]},
    {"english": "various", "japanese": ["さまざまな"]},
    {"english": "vehicle", "japanese": ["乗り物"]},
    {"english": "visible", "japanese": ["目に見える"]},
    {"english": "wealth", "japanese": ["富"]},
]


def build_word_bank() -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for item in [*WORD_BANK, *EXTRA_WORD_BANK]:
        english = item["english"].strip().lower()
        if english in seen:
            continue
        japanese_list = [part.strip() for part in item["japanese"] if part.strip() and "?" not in part]
        if not japanese_list:
            continue
        seen.add(english)
        merged.append(
            {
                "english": item["english"].strip(),
                "japanese": japanese_list,
            }
        )
    return merged


WORD_BANK = build_word_bank()


def normalize_text(value: str) -> str:
    return "".join(value.strip().lower().split())


@dataclass
class EnglishShooterPlayer:
    symbol: str
    name: str
    connected: bool = False
    hp: int = 20
    max_hp: int = 20
    combo: int = 0
    total_damage: int = 0
    translation_hits: int = 0

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "combo": self.combo,
            "total_damage": self.total_damage,
            "translation_hits": self.translation_hits,
        }


class EnglishShooterGame:
    game_type = "english_shooter"
    title = "English Shooter"
    subtitle = "英語を訳して撃つ、1〜4人対応のタイピングバトル。"
    category = "original"
    min_players = 1
    max_players = 4
    player_label = "1〜4人用"
    seat_order = ["P1", "P2", "P3", "P4"]
    host_control_actions = {"start_match", "update_settings"}

    def __init__(self) -> None:
        self.players: Dict[str, EnglishShooterPlayer] = {
            "P1": EnglishShooterPlayer(symbol="P1", name="P1"),
            "P2": EnglishShooterPlayer(symbol="P2", name="P2"),
            "P3": EnglishShooterPlayer(symbol="P3", name="P3"),
            "P4": EnglishShooterPlayer(symbol="P4", name="P4"),
        }
        self.settings = {
            "mode": "solo",
            "player_hp": 20,
        }
        self.started = False
        self.game_over = False
        self.phase = "waiting"
        self.message = "モードとHPを決めてゲーム開始を押してください。"
        self.winner_text = ""
        self.enemy_index = 0
        self.enemy_hp = ENEMY_LINEUP[0]["hp"]
        self.enemy_max_hp = ENEMY_LINEUP[0]["hp"]
        self.question_number = 0
        self.question_deadline: Optional[float] = None
        self.game_deadline: Optional[float] = None
        self.current_prompt: Optional[dict] = None
        self.used_words: List[str] = []
        self.battle_log: List[str] = []
        self.last_answer_symbol = ""

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
        if symbol not in self.players:
            return
        cleaned = name.strip() or symbol
        self.players[symbol].name = cleaned[:24]

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected

    def start_if_ready(self) -> None:
        if self.started:
            return
        if self.connected_count() >= 2:
            self.message = "モードとHPを決めて開始できます。対戦・協力は2人そろうと遊べます。"
        else:
            self.message = "1人でソロ開始できます。対戦・協力はもう1人参加すると始められます。"

    def reset_for_rematch(self) -> None:
        saved_names = {symbol: player.name for symbol, player in self.players.items()}
        saved_connections = {symbol: player.connected for symbol, player in self.players.items()}
        saved_settings = dict(self.settings)
        self.__init__()
        self.settings.update(saved_settings)
        for symbol, name in saved_names.items():
            self.players[symbol].name = name
            self.players[symbol].connected = saved_connections[symbol]
        self._sync_player_hp(reset_runtime=True)

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        if action == "update_settings":
            self.update_settings(settings or {})
            return
        if action == "start_match":
            self.start_match()
            return
        raise GameError("不明な管理操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        answer_text: Optional[str] = None,
        **_: object,
    ) -> None:
        self._advance_time()
        if action == "submit_answer":
            self.submit_answer(symbol, answer_text or "")
            return
        if action == "resign":
            self.resign(symbol)
            return
        raise GameError("不明な操作です。")

    def connected_symbols(self) -> List[str]:
        return [symbol for symbol, player in self.players.items() if player.connected]

    def connected_count(self) -> int:
        return len(self.connected_symbols())

    def active_symbols(self) -> List[str]:
        if self.settings["mode"] == "solo":
            return self.connected_symbols()[:1] or ["P1"]
        if self.settings["mode"] == "versus":
            return self.connected_symbols()[:2]
        return self.connected_symbols()[:4]

    def mode_label(self) -> str:
        labels = {
            "solo": "ソロ",
            "versus": "対戦",
            "coop": "協力",
        }
        return labels.get(self.settings["mode"], self.settings["mode"])

    def update_settings(self, settings: dict) -> None:
        if self.started and not self.game_over:
            raise GameError("ゲーム開始後は設定を変えられません。")

        mode = str(settings.get("mode", self.settings["mode"]))
        if mode not in {"solo", "versus", "coop"}:
            raise GameError("モード設定が不正です。")

        try:
            player_hp = int(settings.get("player_hp", self.settings["player_hp"]))
        except (TypeError, ValueError) as exc:
            raise GameError("プレイヤーHPは数字で入力してください。") from exc

        if player_hp < 5 or player_hp > 200:
            raise GameError("プレイヤーHPは5〜200で設定してください。")

        self.settings["mode"] = mode
        self.settings["player_hp"] = player_hp
        self._sync_player_hp(reset_runtime=True)
        self.message = f"設定を更新しました。現在は{self.mode_label()}モードです。"

    def start_match(self) -> None:
        mode = self.settings["mode"]
        active = self.active_symbols()
        if mode == "solo":
            if not active:
                raise GameError("1人以上の参加が必要です。")
        elif mode == "versus":
            if len(active) < 2:
                raise GameError("対戦モードは2人そろうと開始できます。")
        else:
            if len(active) < 2:
                raise GameError("協力モードは2〜4人で開始できます。")

        self.started = True
        self.game_over = False
        self.phase = "translation"
        self.winner_text = ""
        self.enemy_index = 0
        self.enemy_hp = ENEMY_LINEUP[0]["hp"]
        self.enemy_max_hp = ENEMY_LINEUP[0]["hp"]
        self.question_number = 0
        self.game_deadline = time.time() + TOTAL_TIME_SECONDS
        self.used_words = []
        self.battle_log = []
        self.last_answer_symbol = ""
        self._sync_player_hp(reset_runtime=True)
        if mode == "solo":
            self.message = "ソロ開始。5秒以内に日本語訳を入れると大ダメージです。"
        elif mode == "versus":
            self.message = "対戦開始。5秒以内の日本語訳成功で相手に大ダメージ、連続正解でボーナスが伸びます。"
        else:
            self.message = "協力開始。みんなで敵を倒してください。撃破すると時間が30秒回復します。"
        self._next_prompt()

    def resign(self, symbol: str) -> None:
        if not self.started or self.game_over:
            return
        actor = self.players[symbol]
        if self.settings["mode"] == "versus":
            other = self._opponents_of(symbol)
            winner_name = other[0].name if other else "もう一人"
            self.winner_text = f"{actor.name} が降参しました。{winner_name} の勝ちです。"
        elif self.settings["mode"] == "coop":
            self.winner_text = f"{actor.name} が降参しました。協力ミッション失敗です。"
        else:
            self.winner_text = f"{actor.name} が降参しました。"
        self.message = self.winner_text
        self.game_over = True
        self.phase = "finished"
        self.question_deadline = None

    def submit_answer(self, symbol: str, answer_text: str) -> None:
        if not self.started or self.game_over:
            raise GameError("まずゲームを開始してください。")
        if symbol not in self.active_symbols():
            raise GameError("今の試合には参加していません。")

        self._advance_time()
        if not self.current_prompt:
            raise GameError("問題の準備中です。")

        answer = normalize_text(answer_text)
        if not answer:
            raise GameError("答えを入力してください。")

        prompt = self.current_prompt
        actor = self.players[symbol]
        if self.phase == "translation":
            valid_answers = {normalize_text(item) for item in prompt["japanese"]}
            if answer not in valid_answers:
                raise GameError("日本語訳が違います。")
            actor.combo += 1
            actor.translation_hits += 1
            combo_bonus = min(actor.combo - 1, 5)
            damage = DIRECT_HIT_DAMAGE + combo_bonus
            self.last_answer_symbol = symbol
            self._apply_translation_hit(actor, damage, combo_bonus)
            return

        if self.phase == "spelling":
            if answer != normalize_text(prompt["english"]):
                raise GameError("表示された英単語を正しく入力してください。")
            actor.combo = 0
            self.last_answer_symbol = symbol
            self._apply_spelling_hit(actor)
            return

        raise GameError("今は回答できません。")

    def _apply_translation_hit(self, actor: EnglishShooterPlayer, damage: int, combo_bonus: int) -> None:
        prompt = self.current_prompt or {"english": "", "primary_japanese": ""}
        combo_text = f" 連続ボーナス+{combo_bonus}。" if combo_bonus > 0 else ""
        actor.total_damage += damage

        if self.settings["mode"] == "versus":
            target = self._opponents_of(actor.symbol)[0]
            target.hp = max(0, target.hp - damage)
            log_text = (
                f"{actor.name}: {prompt['english']} → {prompt['primary_japanese']} 正解。"
                f" {target.name}に{damage}ダメージ。{combo_text}".strip()
            )
            self._push_log(log_text)
            if target.hp == 0:
                self.game_over = True
                self.phase = "finished"
                self.winner_text = f"{actor.name} の勝ちです。"
                self.message = self.winner_text
                self.question_deadline = None
                return
            self.message = f"{actor.name} の正解で {target.name} に {damage} ダメージ。次の問題です。"
            self._next_prompt()
            return

        self._deal_enemy_damage(
            damage=damage,
            actor=actor,
            log_text=(
                f"{actor.name}: {prompt['english']} → {prompt['primary_japanese']} 正解。"
                f" {damage}ダメージ。{combo_text}".strip()
            ),
        )

    def _apply_spelling_hit(self, actor: EnglishShooterPlayer) -> None:
        prompt = self.current_prompt or {"english": "", "primary_japanese": ""}
        damage = SPELLING_HIT_DAMAGE
        actor.total_damage += damage

        if self.settings["mode"] == "versus":
            target = self._opponents_of(actor.symbol)[0]
            target.hp = max(0, target.hp - damage)
            log_text = (
                f"{actor.name}: {prompt['primary_japanese']} → {prompt['english']} 正解。"
                f" {target.name}に{damage}ダメージ。"
            )
            self._push_log(log_text)
            if target.hp == 0:
                self.game_over = True
                self.phase = "finished"
                self.winner_text = f"{actor.name} の勝ちです。"
                self.message = self.winner_text
                self.question_deadline = None
                return
            self.message = f"{actor.name} が英単語を打ち切りました。次の問題です。"
            self._next_prompt()
            return

        self._deal_enemy_damage(
            damage=damage,
            actor=actor,
            log_text=f"{actor.name}: {prompt['primary_japanese']} → {prompt['english']} 正解。{damage}ダメージ。",
        )

    def _deal_enemy_damage(self, damage: int, actor: EnglishShooterPlayer, log_text: str) -> None:
        self.enemy_hp = max(0, self.enemy_hp - damage)
        self._push_log(log_text)

        if self.enemy_hp == 0:
            defeated_enemy = ENEMY_LINEUP[self.enemy_index]
            if defeated_enemy["boss"]:
                self.game_over = True
                self.phase = "finished"
                self.winner_text = f"{actor.name} の一撃でラスボス撃破。ゲームクリアです。"
                self.message = self.winner_text
                self.question_deadline = None
                return

            self.enemy_index += 1
            next_enemy = ENEMY_LINEUP[self.enemy_index]
            self.enemy_hp = next_enemy["hp"]
            self.enemy_max_hp = next_enemy["hp"]
            if self.game_deadline is not None:
                self.game_deadline += ENEMY_DEFEAT_BONUS_SECONDS
            self.message = (
                f"{defeated_enemy['jp_name']}を撃破。残り時間が{ENEMY_DEFEAT_BONUS_SECONDS}秒回復しました。"
                f" 次は {next_enemy['jp_name']} です。"
            )
            self._next_prompt()
            return

        self.message = f"{actor.name} の攻撃が決まりました。次の問題です。"
        self._next_prompt()

    def _advance_time(self) -> None:
        now = time.time()
        if (
            self.started
            and not self.game_over
            and self.game_deadline is not None
            and now >= self.game_deadline
        ):
            self.question_deadline = None
            self._finish_by_timeout()
            return

        if (
            self.phase == "translation"
            and self.question_deadline is not None
            and now >= self.question_deadline
            and self.current_prompt is not None
        ):
            self.phase = "spelling"
            self.question_deadline = None
            self.message = (
                f"5秒経過。日本語は「{self.current_prompt['primary_japanese']}」です。"
                " ここからは英単語をそのまま打ってください。"
            )

    def _finish_by_timeout(self) -> None:
        self.game_over = True
        self.phase = "finished"

        if self.settings["mode"] == "versus":
            active = [self.players[symbol] for symbol in self.active_symbols()]
            if len(active) >= 2 and active[0].hp != active[1].hp:
                winner = max(active, key=lambda item: item.hp)
                self.winner_text = f"時間切れ。残りHPが多い {winner.name} の勝ちです。"
            else:
                self.winner_text = "時間切れ。引き分けです。"
        else:
            self.winner_text = "時間切れです。敵を倒し切れませんでした。"

        self.message = self.winner_text

    def _opponents_of(self, symbol: str) -> List[EnglishShooterPlayer]:
        return [
            self.players[player_symbol]
            for player_symbol in self.active_symbols()
            if player_symbol != symbol
        ]

    def _sync_player_hp(self, reset_runtime: bool = False) -> None:
        base_hp = int(self.settings["player_hp"])
        for player in self.players.values():
            player.max_hp = base_hp
            if reset_runtime or player.hp > base_hp or player.hp <= 0:
                player.hp = base_hp
            if reset_runtime:
                player.combo = 0
                player.total_damage = 0
                player.translation_hits = 0

    def _push_log(self, line: str) -> None:
        self.battle_log.append(line)
        if len(self.battle_log) > 14:
            self.battle_log = self.battle_log[-14:]

    def _next_prompt(self) -> None:
        pool = [item for item in WORD_BANK if item["english"] not in self.used_words]
        if not pool:
            self.used_words = []
            pool = list(WORD_BANK)

        prompt = random.choice(pool)
        self.used_words.append(prompt["english"])
        masked = "〇" * len(prompt["japanese"][0])
        self.current_prompt = {
            "english": prompt["english"],
            "japanese": list(prompt["japanese"]),
            "primary_japanese": prompt["japanese"][0],
            "masked_length": len(prompt["japanese"][0]),
            "masked_japanese": masked,
        }
        self.phase = "translation"
        self.question_deadline = time.time() + TRANSLATION_LIMIT_SECONDS
        self.question_number += 1

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        self._advance_time()
        enemy = ENEMY_LINEUP[self.enemy_index]
        prompt = self.current_prompt or {
            "english": "",
            "primary_japanese": "",
            "masked_length": 0,
            "masked_japanese": "",
        }
        active_symbols = self.active_symbols()
        viewer = self.players.get(viewer_symbol)
        active_players = [self.players[symbol] for symbol in active_symbols if symbol in self.players]
        top_attacker = max(active_players, key=lambda item: item.total_damage, default=None)
        return {
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
            "mode": self.settings["mode"],
            "mode_label": self.mode_label(),
            "settings": dict(self.settings),
            "active_symbols": list(active_symbols),
            "viewer_combo": viewer.combo if viewer else 0,
            "viewer_hp": viewer.hp if viewer else 0,
            "viewer_max_hp": viewer.max_hp if viewer else 0,
            "top_attacker_symbol": top_attacker.symbol if top_attacker else "",
            "top_attacker_name": top_attacker.name if top_attacker else "",
            "top_attacker_damage": top_attacker.total_damage if top_attacker else 0,
            "enemy_index": self.enemy_index + 1,
            "enemy_total": len(ENEMY_LINEUP),
            "enemy_name": enemy["name"],
            "enemy_jp_name": enemy["jp_name"],
            "enemy_hp": self.enemy_hp,
            "enemy_max_hp": self.enemy_max_hp,
            "is_boss": enemy["boss"],
            "question_number": self.question_number,
            "question_deadline": self.question_deadline,
            "game_deadline": self.game_deadline,
            "remaining_seconds": max(0, int(self.game_deadline - time.time())) if self.game_deadline is not None else 0,
            "defeat_bonus_seconds": ENEMY_DEFEAT_BONUS_SECONDS,
            "translation_limit_seconds": TRANSLATION_LIMIT_SECONDS,
            "damage_values": {
                "direct": DIRECT_HIT_DAMAGE,
                "spelling": SPELLING_HIT_DAMAGE,
            },
            "current_prompt": {
                "english": prompt["english"],
                "masked_length": prompt["masked_length"],
                "masked_japanese": prompt["masked_japanese"],
                "primary_japanese": prompt["primary_japanese"],
                "revealed_japanese": prompt["primary_japanese"] if self.phase != "translation" else "",
            },
            "battle_log": list(self.battle_log),
            "last_answer_symbol": self.last_answer_symbol,
        }
