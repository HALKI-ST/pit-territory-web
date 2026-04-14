from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


class GameError(ValueError):
    pass


WORD_POOL = [
    "宇宙船", "星空", "流れ星", "月面", "太陽光", "北極", "南極", "海底", "深海魚", "灯台",
    "遊園地", "図書館", "映画館", "喫茶店", "温泉街", "商店街", "駅前", "地下鉄", "高速道路", "空港ロビー",
    "キャンプ", "花火", "桜並木", "雪だるま", "砂浜", "入道雲", "夕焼け", "朝焼け", "虹色", "霧の森",
    "ロケット", "カメラ", "イヤホン", "スマホ", "ノート", "リモコン", "キーボード", "トランプ", "ラジオ", "懐中電灯",
    "チョコ", "パン屋", "おにぎり", "みそ汁", "アイス", "レモン", "りんご", "いちご", "焼き鳥", "カレー",
    "王様", "姫君", "騎士団", "魔法使い", "探偵", "泥棒", "船長", "職人", "先生", "発明家",
    "ロボット", "怪獣", "忍者", "ドラゴン", "妖精", "海賊", "宇宙人", "恐竜", "ペンギン", "パンダ",
    "音楽室", "美術館", "体育館", "屋上", "教室", "研究所", "病院", "工場", "庭園", "水族館",
    "ガラス", "歯車", "宝石箱", "金庫", "手紙", "地図帳", "望遠鏡", "双眼鏡", "砂時計",
    "青空", "赤い糸", "白い羽", "黒板", "銀貨", "金メダル", "水玉", "花束", "風船", "紙飛行機",
    "山道", "川辺", "湖畔", "洞窟", "火山灰", "氷山", "草原", "竹林", "石畳", "木陰",
    "ダンス", "拍手", "合図", "作戦", "暗号", "秘密基地", "冒険", "勝負", "休憩", "おまつり",
    "ホテル", "レストラン", "コンビニ", "スーパー", "デパート", "タクシー", "バス", "モノレール", "エレベーター", "エスカレーター",
    "ベランダ", "クローゼット", "ソファ", "テーブル", "ベッド", "カーテン", "シャワー", "バスタブ", "タオル", "スリッパ",
    "ボタン", "アクセサリー", "ネックレス", "ブレスレット", "サングラス", "ヘルメット", "ユニフォーム", "マフラー", "セーター", "パーカー",
    "サンドイッチ", "ハンバーグ", "オムライス", "スパゲティ", "サラダ", "プリン", "ゼリー", "ヨーグルト", "ミルク", "コーヒー",
    "ジュース", "ソーダ", "シロップ", "キャラメル", "バニラ", "シナモン", "スパイス", "マシュマロ", "ビスケット", "ピアノ",
    "ギター", "ドラム", "バイオリン", "フルート", "サックス", "トランペット", "メロディー", "リズム", "ハーモニー", "アニメ",
    "ドラマ", "ミステリー", "ファンタジー", "ホラー", "コメディ", "ヒーロー", "ヒロイン", "ライバル", "チャンピオン", "エンジン",
    "ブレーキ", "ハンドル", "タイヤ", "ペダル", "ジェット", "ミサイル", "コンパス", "アンテナ", "スイッチ", "ウイルス",
    "エネルギー", "パワー", "イメージ", "メッセージ", "スケジュール", "プロジェクト", "チームワーク", "チャンス", "ミラクル", "ピンチ",
    "ヒント", "ルール", "ステージ", "ゴール", "スタート", "ジャンプ", "ダッシュ", "スピード", "バランス", "リラックス",
    "アトリエ", "ギャラリー", "スタジアム", "アリーナ", "プラネタリウム", "ミュージアム", "ターミナル", "ラウンジ", "ゲート", "フェリー",
    "クルーザー", "ボート", "ヨット", "トロッコ", "ケーブルカー", "ゴンドラ", "リフト", "トンネル", "ジャンクション", "ロータリー",
    "パーキング", "ガレージ", "アトラクション", "テーマパーク", "プール", "サウナ", "スパ", "リゾート", "ヴィラ", "ペンション",
    "ロッジ", "チャペル", "スタジオ", "ホール", "ロビー", "フロント", "オフィス", "カウンター",
    "フードコート", "カフェ", "バーガー", "ピザ", "グラタン", "ドリア",
    "ラザニア", "リゾット", "オムレツ", "スープ", "ポトフ", "シチュー", "グミ", "キャンディ", "ガム", "クッキー",
    "ドーナツ", "クロワッサン", "マカロン", "ティラミス", "パンケーキ", "ワッフル", "タルト", "ムース", "シャーベット",
    "ココア", "ラテ", "カフェオレ", "スムージー", "コーラ", "ジンジャーエール", "エスプレッソ", "カプチーノ", "ハーブティー",
    "フォーク", "スプーン", "ナイフ", "トレー", "グラス", "マグカップ", "ポット", "ケトル", "トースター", "ミキサー",
    "ブレンダー", "オーブン", "レンジ", "クーラー", "ヒーター", "クリーナー", "フィルター", "バッテリー", "モーター", "レバー",
    "ギア", "メーター", "センサー", "モニター", "ディスプレイ", "タブレット", "ディスク", "プリンター", "スキャナー", "マイク",
    "スピーカー", "ヘッドホン", "ペンダント", "リング", "チャーム", "ブローチ", "リュック", "トートバッグ", "ポーチ",
    "スーツケース", "キャリーケース", "キャップ", "ジャケット", "コート", "スカーフ", "ネクタイ", "ベルト", "スニーカー", "ブーツ",
    "サンダル", "パンプス", "グローブ", "ミトン", "ハンカチ", "キャンドル", "ランプ", "シャンデリア", "ポスター", "アルバム",
    "フィルム", "スクリーン", "シナリオ", "コミック", "ノベル", "エッセイ", "ガイドブック", "パンフレット", "カタログ", "パズル",
    "クイズ", "カード", "ボード", "サイコロ", "トークン", "トロフィー", "フィギュア", "マスコット", "キャラクター",
    "モンスター", "エイリアン", "ナイト", "クイーン", "プリンス", "ハンター", "レンジャー",
    "ウィザード", "エルフ", "ゴブリン", "フェニックス", "ユニコーン", "グリフォン", "サファリ", "オアシス", "ピラミッド", "コロッセオ",
    "オペラハウス", "タワー", "ドーム", "ゲレンデ", "マリーナ", "パビリオン", "モニュメント", "ランドマーク", "パラダイス", "ユートピア",
    "ハンマー", "ドライバー", "スパナ", "ペンチ", "ニッパー", "レンチ", "ロンドン", "パリ", "ローマ", "ベルリン", "ニューヨーク", "シドニー", "イタリア", "フランス", "エジプト",
    "剣", "盾", "塔", "雲", "雪", "花", "夢", "影", "鍵", "鏡", "泉", "滝", "舟", "玉", "鬼",
    "稲妻", "噴水", "水滴", "水面", "水路", "水門", "水車", "水晶", "水源", "火花",
    "炎上", "火柱", "火口", "火薬", "火種", "灰色", "炭火", "土砂", "土壁", "土俵",
    "砂利", "岩場", "岩石", "鉱石", "鉄橋", "鉄塔", "鉄道", "銅像", "銀河", "星座",
    "月光", "日食", "白夜", "天井", "天窓", "雲海", "霜柱", "雪原", "雪道", "氷柱",
    "結晶", "風車", "風鈴", "突風", "山脈", "山頂", "尾根", "谷間", "渓流", "湿原",
    "平原", "森林", "古城", "王冠", "玉座", "宮殿", "神殿", "寺院", "鳥居", "社殿",
    "参道", "門番", "茶室", "旅館", "宿屋", "広場", "路地", "石橋", "坂道", "街灯",
    "波止場", "市場", "牧場", "農園", "果樹園", "花壇", "花畑", "温室", "苗木", "若葉",
    "紅葉", "落葉", "新芽", "花粉", "根元", "木材", "木琴", "竹笛", "紙箱", "紙袋",
    "羊皮紙", "巻物", "日記", "手帳", "短冊", "古書", "文庫", "辞典", "印鑑", "判子",
    "封筒", "便箋", "書斎", "机上", "本棚", "筆箱", "鉛筆", "絵筆", "硯石", "黒曜石",
    "水差し", "湯呑み", "茶碗", "丼鉢", "皿洗い", "台所", "食卓", "食器", "包丁", "鍋敷き",
    "蒸気", "炊飯", "米粒", "麦畑", "果実", "野菜", "香草", "桃園", "梅林",
    "蜜柑", "青果", "菓子", "煎餅", "団子", "羊羹", "干物", "塩焼き", "串焼き", "天ぷら",
    "鍋物", "汁椀", "酒場", "銘茶", "薬味", "薬草", "漢方", "診察", "処方", "看板",
    "暖簾", "番傘", "提灯", "行灯", "床間", "座布団", "戸棚", "押入れ", "玄関", "廊下",
    "縁側", "雨戸", "障子", "畳縁", "座敷", "客間", "庭石", "池泉", "噴煙", "滝壺",
    "滝道", "泉水", "湖水", "川岸", "船頭", "船室", "甲板", "船旅", "航路", "寄港",
    "出港", "帆船", "飛行場", "滑走路", "改札口", "停留所", "車窓", "乗船券", "入場券", "招待状",
    "合唱", "独唱", "演奏", "名曲", "楽譜", "音色", "音量", "響き", "余韻", "劇場",
    "舞台裏", "幕間", "開幕", "終幕", "衣装", "化粧", "素顔", "真相", "証拠", "手掛かり",
    "容疑", "犯人", "名探偵", "怪事件", "難事件", "名勝負", "決着", "対決", "作戦会議", "奇襲",
    "守備", "攻撃", "援軍", "大将", "兵士", "軍勢", "武将", "剣士", "弓矢", "刀傷",
    "鎧兜", "宝刀", "秘宝", "財宝", "宝庫", "金塊", "貨幣", "小判", "貯金箱", "帳面",
    "計算", "暗記", "試験", "答案", "宿題", "学級", "校舎", "講堂", "運動場", "部室",
    "委員会", "放課後", "始業式", "終業式", "遠足", "修学", "研究", "実験", "観察", "標本",
    "模型", "発見", "発想", "工芸", "細工", "名工", "名人", "達人", "勇者", "賢者",
    "使者", "旅人", "少年", "少女", "青年", "老人", "村人", "町人", "名士", "人気者",
    "働き者", "恥じらい", "怒り顔", "笑顔", "寝顔", "横顔", "後ろ姿", "足跡", "物音", "気配",
    "予感", "直感", "本音", "弱音", "願望", "希望", "絶望", "幸福", "不安", "安心",
    "平和", "混乱", "騒動", "祝祭", "祭壇", "祝福", "祈願", "願書", "運命", "偶然",
    "必然", "永遠", "瞬間", "昨日", "明日", "未来", "過去", "現在", "朝露", "夕立",
    "夜空", "夜道", "夜明け", "昼下がり", "木漏れ日", "陽だまり", "薄明", "人影", "旅路", "帰路",
    "近道", "抜け道", "分かれ道", "一本道", "見晴らし", "展望", "絶景", "名所", "旧跡", "秘境",
    "楽園", "桃源郷", "辺境", "異郷", "故郷", "郷土", "民話", "昔話", "伝承", "神話",
    "伝説級",
]

SEAT_ORDER = [f"P{index}" for index in range(1, 13)]
TEAM_LABELS = {"red": "赤チーム", "blue": "青チーム"}
ROLE_LABELS = {"master": "マスター", "spy": "スパイ"}


@dataclass
class WordSpyPlayer:
    symbol: str
    name: str
    connected: bool = False

    def to_public_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "connected": self.connected,
        }


class WordSpyGame:
    game_type = "word_spy"
    title = "ワードゲーム"
    subtitle = "マスターがヒントを出し、スパイが言葉カードを取り合うチーム戦。"
    category = "classic"
    min_players = 4
    max_players = len(SEAT_ORDER)
    player_label = "4人～"
    seat_order = list(SEAT_ORDER)
    allow_midgame_join = True
    host_control_actions = {"assign_role", "start_match"}

    def __init__(self) -> None:
        self.players: Dict[str, WordSpyPlayer] = {}
        self.assignments: Dict[str, dict] = {}
        self.started = False
        self.game_over = False
        self.current_team = "red"
        self.phase = "waiting"
        self.current_hint_word = ""
        self.current_hint_count = 0
        self.guesses_made = 0
        self.guesses_allowed = 0
        self.cards: List[dict] = []
        self.winner_text = ""
        self.message = "4人以上集まったら、マスターとスパイの役職を決めてください。"
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
        self.players[symbol] = WordSpyPlayer(symbol=symbol, name=cleaned[:24])
        if symbol not in self.assignments:
            self.assignments[symbol] = self._default_assignment_for_symbol(symbol)
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
        saved_assignments = {
            symbol: assignment.copy()
            for symbol, assignment in self.assignments.items()
        }
        self.__init__()
        for symbol in self.seat_order:
            if symbol not in saved_players:
                continue
            name, connected = saved_players[symbol]
            self.players[symbol] = WordSpyPlayer(symbol=symbol, name=name, connected=connected)
            self.assignments[symbol] = saved_assignments.get(
                symbol,
                self._default_assignment_for_symbol(symbol),
            )
        self._refresh_waiting_message()

    def apply_host_action(
        self,
        action: str,
        target_symbol: Optional[str] = None,
        assigned_team: Optional[str] = None,
        assigned_role: Optional[str] = None,
        **_: object,
    ) -> None:
        if action == "assign_role":
            self._assign_role(target_symbol, assigned_team, assigned_role)
            return
        if action == "start_match":
            self.start_match()
            return
        raise GameError("不明な管理操作です。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        clue_text: Optional[str] = None,
        clue_count: Optional[int] = None,
        card_index: Optional[int] = None,
        **_: object,
    ) -> None:
        if action == "resign":
            self._resign(symbol)
            return
        if action == "end_turn":
            self._end_turn(symbol)
            return

        if not self.started:
            raise GameError("まだゲームが始まっていません。")
        if self.game_over:
            raise GameError("ゲームは終了しています。")
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")

        if action == "give_hint":
            self._give_hint(symbol, clue_text or "", clue_count)
            return
        if action == "reveal_card":
            self._reveal_card(symbol, card_index)
            return
        raise GameError("不明な操作です。")

    def start_match(self) -> None:
        ready, reason = self._start_readiness()
        if not ready:
            raise GameError(reason)

        self.started = True
        self.game_over = False
        self.current_team = random.choice(["red", "blue"])
        self.phase = "hint"
        self.current_hint_word = ""
        self.current_hint_count = 0
        self.guesses_made = 0
        self.guesses_allowed = 0
        self.cards = self._build_cards(self.current_team)
        self.winner_text = ""
        self.history = []
        self.message = f"{self._team_label(self.current_team)}のマスターがヒントを出してください。"

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        viewer_assignment = self.assignments.get(viewer_symbol, {})
        viewer_can_see_roles = self._viewer_can_see_roles(viewer_symbol)
        cards = []
        for index, card in enumerate(self.cards):
            role = card["role"] if (card["revealed"] or viewer_can_see_roles) else None
            cards.append(
                {
                    "index": index,
                    "word": card["word"],
                    "role": role,
                    "revealed": card["revealed"],
                }
            )

        return {
            "title": self.title,
            "started": self.started,
            "game_over": self.game_over,
            "phase": self.phase,
            "current_team": self.current_team,
            "current_hint_word": self.current_hint_word,
            "current_hint_count": self.current_hint_count,
            "guesses_made": self.guesses_made,
            "guesses_allowed": self.guesses_allowed,
            "guesses_remaining": max(0, self.guesses_allowed - self.guesses_made) if self.phase == "guess" else 0,
            "message": self.message,
            "winner_text": self.winner_text,
            "players": {
                symbol: player.to_public_dict()
                for symbol, player in self.players.items()
            },
            "player_order": [symbol for symbol in self.seat_order if symbol in self.players],
            "viewer_assignment": self._assignment_payload(viewer_symbol),
            "assignments": {
                symbol: self._assignment_payload(symbol)
                for symbol in self.seat_order
                if symbol in self.players
            },
            "teams": {
                "red": self._team_panel("red", viewer_symbol),
                "blue": self._team_panel("blue", viewer_symbol),
            },
            "cards": cards,
            "history": list(self.history),
            "start_ready": self._start_readiness()[0],
            "start_requirements": self._start_readiness()[1],
        }

    def _assign_role(
        self,
        target_symbol: Optional[str],
        assigned_team: Optional[str],
        assigned_role: Optional[str],
    ) -> None:
        if target_symbol not in self.players:
            raise GameError("対象プレイヤーが見つかりません。")
        if assigned_team not in TEAM_LABELS:
            raise GameError("チーム指定が不正です。")
        if assigned_role not in ROLE_LABELS:
            raise GameError("役職指定が不正です。")

        current_assignment = self.assignments.get(target_symbol, {})
        if self.started and not self.game_over:
            if assigned_role != "spy" or current_assignment.get("role") != "spy":
                raise GameError("試合中に変更できるのは、スパイの所属チームだけです。")

        if assigned_role == "master":
            current_master = self._master_symbol(assigned_team)
            if current_master and current_master != target_symbol:
                self.assignments[current_master]["role"] = "spy"

        self.assignments[target_symbol] = {
            "team": assigned_team,
            "role": assigned_role,
        }
        self._refresh_waiting_message()

    def _refresh_waiting_message(self) -> None:
        if self.started:
            return
        ready, reason = self._start_readiness()
        self.message = "開始できます。部屋を作った人がスタートしてください。" if ready else reason

    def _build_cards(self, starting_team: str) -> List[dict]:
        words = random.sample(WORD_POOL, 25)
        roles = (
            [starting_team] * 9
            + [self._other_team(starting_team)] * 8
            + ["neutral"] * 7
            + ["assassin"]
        )
        random.shuffle(roles)
        return [
            {"word": word, "role": role, "revealed": False}
            for word, role in zip(words, roles)
        ]

    def _give_hint(self, symbol: str, clue_text: str, clue_count: Optional[int]) -> None:
        if self.phase != "hint":
            raise GameError("今はヒントを出すフェーズではありません。")
        if not self._can_give_hint(symbol):
            raise GameError("このターンにヒントを出せるのは現在チームのマスターだけです。")

        clue = clue_text.strip()
        if not clue:
            raise GameError("ヒントの単語を入力してください。")
        if clue_count is None:
            raise GameError("ヒントの数字を入力してください。")

        count = int(clue_count)
        if count < 1 or count > 9:
            raise GameError("ヒントの数字は 1 から 9 にしてください。")

        self.current_hint_word = clue[:24]
        self.current_hint_count = count
        self.guesses_made = 0
        self.guesses_allowed = count + 1
        self.phase = "guess"
        self.history.append(
            f"{self._team_label(self.current_team)}: マスターが「{self.current_hint_word} {self.current_hint_count}」を提示"
        )
        self.message = f"{self._team_label(self.current_team)}のスパイがカードを選んでください。"

    def _reveal_card(self, symbol: str, card_index: Optional[int]) -> None:
        if self.phase != "guess":
            raise GameError("今は推理フェーズではありません。")
        if not self._can_guess(symbol):
            raise GameError("このターンに推理できるのは現在チームのスパイだけです。")
        if card_index is None or not 0 <= int(card_index) < len(self.cards):
            raise GameError("カード位置が不正です。")

        card = self.cards[int(card_index)]
        if card["revealed"]:
            raise GameError("そのカードはすでに公開されています。")

        card["revealed"] = True
        role = card["role"]
        word = card["word"]
        self.guesses_made += 1
        self.history.append(
            f"{self._team_label(self.current_team)}: {self.players[symbol].name} が「{word}」を公開"
        )

        if role == "assassin":
            loser = self.current_team
            winner = self._other_team(loser)
            self._finish(
                winner,
                f"{self._team_label(loser)}が暗殺カード「{word}」を引きました。{self._team_label(winner)}の勝ちです。",
            )
            return

        if self._remaining_agents("red") == 0:
            self._finish("red", "赤チームが自分のカードをすべて取り切りました。赤チームの勝ちです。")
            return
        if self._remaining_agents("blue") == 0:
            self._finish("blue", "青チームが自分のカードをすべて取り切りました。青チームの勝ちです。")
            return

        if role == self.current_team:
            if self.guesses_made >= self.guesses_allowed:
                self._advance_turn(f"推理回数を使い切ったため、{self._team_label(self._other_team(self.current_team))}へ交代します。")
            else:
                self.message = f"正解です。{self._team_label(self.current_team)}は続けて推理できます。"
            return

        role_label = {
            "neutral": "一般カード",
            "red": "赤チームのカード",
            "blue": "青チームのカード",
        }.get(role, "カード")
        self._advance_turn(f"「{word}」は{role_label}でした。ターン交代です。")

    def _end_turn(self, symbol: str) -> None:
        if not self.started or self.game_over:
            raise GameError("いまはターン終了できません。")
        if self.phase != "guess":
            raise GameError("推理フェーズ中のみターン終了できます。")
        if not self._can_guess(symbol):
            raise GameError("現在チームのスパイだけが推理終了できます。")

        team = self.current_team
        self.history.append(f"{self._team_label(team)}: スパイが推理を終了")
        self._advance_turn(f"{self._team_label(team)}が推理を終了しました。")

    def _advance_turn(self, message: str) -> None:
        next_team = self._other_team(self.current_team)
        self.current_team = next_team
        self.phase = "hint"
        self.current_hint_word = ""
        self.current_hint_count = 0
        self.guesses_made = 0
        self.guesses_allowed = 0
        self.message = f"{message} 次は{self._team_label(next_team)}のマスターがヒントを出します。"

    def _resign(self, symbol: str) -> None:
        if symbol not in self.players:
            raise GameError("プレイヤーが見つかりません。")
        assignment = self.assignments.get(symbol)
        if not assignment:
            raise GameError("役職情報が見つかりません。")
        loser = assignment["team"]
        winner = self._other_team(loser)
        self._finish(
            winner,
            f"{self._team_label(loser)}が降参しました。{self._team_label(winner)}の勝ちです。",
        )

    def _finish(self, winner: str, message: str) -> None:
        self.game_over = True
        self.phase = "finished"
        self.winner_text = message
        self.message = message
        self.current_team = winner

    def _assignment_payload(self, symbol: str) -> dict:
        assignment = self.assignments.get(symbol, {})
        team = assignment.get("team")
        role = assignment.get("role")
        return {
            "team": team,
            "team_label": self._team_label(team) if team else "未設定",
            "role": role,
            "role_label": ROLE_LABELS.get(role, "未設定"),
            "viewer_can_give_hint": bool(symbol) and self._can_give_hint(symbol),
            "viewer_can_guess": bool(symbol) and self._can_guess(symbol),
            "viewer_is_team_member": bool(symbol) and team in TEAM_LABELS,
        }

    def _team_panel(self, team: str, viewer_symbol: str) -> dict:
        members = self._team_members(team)
        masters = [symbol for symbol in members if self.assignments[symbol]["role"] == "master"]
        spies = [symbol for symbol in members if self.assignments[symbol]["role"] == "spy"]
        return {
            "team": team,
            "label": self._team_label(team),
            "remaining": self._remaining_agents(team),
            "master": self.players[masters[0]].to_public_dict() if masters else None,
            "spies": [self.players[symbol].to_public_dict() for symbol in spies],
            "viewer_is_team_member": viewer_symbol in members,
            "viewer_can_give_hint": self._can_give_hint(viewer_symbol),
            "viewer_can_guess": self._can_guess(viewer_symbol),
        }

    def _default_assignment_for_symbol(self, symbol: str) -> dict:
        index = self.seat_order.index(symbol)
        if index == 0:
            return {"team": "red", "role": "master"}
        if index == 1:
            return {"team": "blue", "role": "master"}
        if index == 2:
            return {"team": "red", "role": "spy"}
        if index == 3:
            return {"team": "blue", "role": "spy"}
        return {"team": "red" if index % 2 == 0 else "blue", "role": "spy"}

    def _start_readiness(self) -> tuple[bool, str]:
        if len(self.players) < self.min_players:
            return False, "4人以上集まると開始できます。"

        red_master = self._master_symbol("red")
        blue_master = self._master_symbol("blue")
        red_spies = self._spy_symbols("red")
        blue_spies = self._spy_symbols("blue")

        missing: List[str] = []
        if not red_master:
            missing.append("赤マスター")
        if not blue_master:
            missing.append("青マスター")
        if not red_spies:
            missing.append("赤スパイ")
        if not blue_spies:
            missing.append("青スパイ")

        if missing:
            return False, "開始前に " + "・".join(missing) + " を決めてください。"
        return True, "開始できます。"

    def _team_members(self, team: str) -> List[str]:
        return [
            symbol
            for symbol in self.seat_order
            if symbol in self.players and self.assignments.get(symbol, {}).get("team") == team
        ]

    def _master_symbol(self, team: str) -> Optional[str]:
        for symbol in self._team_members(team):
            if self.assignments.get(symbol, {}).get("role") == "master":
                return symbol
        return None

    def _spy_symbols(self, team: str) -> List[str]:
        return [
            symbol
            for symbol in self._team_members(team)
            if self.assignments.get(symbol, {}).get("role") == "spy"
        ]

    def _can_give_hint(self, symbol: str) -> bool:
        if not symbol or self.phase != "hint" or self.game_over:
            return False
        assignment = self.assignments.get(symbol, {})
        return assignment.get("team") == self.current_team and assignment.get("role") == "master"

    def _can_guess(self, symbol: str) -> bool:
        if not symbol or self.phase != "guess" or self.game_over:
            return False
        assignment = self.assignments.get(symbol, {})
        return assignment.get("team") == self.current_team and assignment.get("role") == "spy"

    def _remaining_agents(self, team: str) -> int:
        return sum(1 for card in self.cards if card["role"] == team and not card["revealed"])

    def _viewer_can_see_roles(self, viewer_symbol: str) -> bool:
        if self.game_over:
            return True
        return self.assignments.get(viewer_symbol, {}).get("role") == "master"

    @staticmethod
    def _other_team(team: str) -> str:
        return "blue" if team == "red" else "red"

    @staticmethod
    def _team_label(team: Optional[str]) -> str:
        return TEAM_LABELS.get(team or "", "未設定")
