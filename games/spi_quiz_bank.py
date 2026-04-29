from __future__ import annotations

import random


def _shuffle_question(rng: random.Random, prompt: str, answer: str, distractors: list[str], category: str, explanation: str, qid: str) -> dict:
    choices = [answer, *distractors]
    rng.shuffle(choices)
    return {
        "id": qid,
        "category": category,
        "prompt": prompt,
        "choices": choices,
        "answer_index": choices.index(answer),
        "explanation": explanation,
    }


def build_spi_question_bank() -> list[dict]:
    bank: list[dict] = []
    rng = random.Random(20260430)

    synonym_sets = [
        ("簡潔", "要点だけを短くまとめていること", ["回りくどいこと", "手順が複雑なこと", "勢いが強いこと"]),
        ("柔軟", "状況に合わせて考え方や動き方を変えられること", ["決まりを増やすこと", "反対を押し通すこと", "最初の案だけを守ること"]),
        ("堅実", "無理をせず着実に進めること", ["勢いで決めること", "偶然に頼ること", "人任せにすること"]),
        ("妥当", "事情に照らしてちょうどよいこと", ["極端に厳しいこと", "無関係なこと", "曖昧で決まらないこと"]),
        ("慎重", "よく確かめながら進めること", ["すぐ飛びつくこと", "規則を破ること", "順番を省くこと"]),
        ("明朗", "明るくはっきりしていること", ["不機嫌で閉鎖的なこと", "危険が多いこと", "不規則なこと"]),
        ("繁忙", "とても忙しいこと", ["十分に休めること", "予定がないこと", "会話が少ないこと"]),
        ("温厚", "穏やかで怒りにくいこと", ["対立を好むこと", "判断が遅いこと", "話題が多いこと"]),
        ("顕著", "目立ってはっきりしていること", ["隠れて見えないこと", "あとから加わること", "速く動くこと"]),
        ("即答", "その場ですぐ答えること", ["後日に持ち越すこと", "複数人で分担すること", "比率で表すこと"]),
        ("推測", "確かな証拠がそろう前に見当をつけること", ["確認して断定すること", "資料を印刷すること", "順番を入れ替えること"]),
        ("抑制", "強すぎる動きや感情をおさえること", ["さらに加速すること", "外に広げること", "途中で切り分けること"]),
        ("継続", "途中でやめずに続けること", ["一度で終えること", "別案に変えること", "外部に譲ること"]),
        ("簡略", "必要な部分を残して短くすること", ["意味を増やすこと", "複数案を比較すること", "回数を数えること"]),
        ("補完", "足りない部分を補って整えること", ["全体を削ること", "順位を入れ替えること", "外側へ移すこと"]),
    ]
    for index, (word, answer, distractors) in enumerate(synonym_sets, start=1):
        bank.append(
            _shuffle_question(
                rng,
                f"次の語の意味として最も近いものを選びなさい。『{word}』",
                answer,
                distractors,
                "verbal",
                f"『{word}』は {answer} を表します。",
                f"syn-{index}",
            )
        )

    antonym_sets = [
        ("促進", "抑制", ["維持", "共有", "集約"]),
        ("拡張", "縮小", ["観察", "流通", "共感"]),
        ("肯定", "否定", ["依頼", "予測", "同意"]),
        ("上昇", "下降", ["固定", "連結", "移送"]),
        ("公開", "非公開", ["増額", "継続", "再考"]),
        ("詳細", "概略", ["具体", "反復", "正答"]),
        ("連続", "断続", ["直列", "協力", "恒常"]),
        ("適任", "不適任", ["無関心", "高収益", "既定"]),
        ("積極", "消極", ["対等", "整列", "明示"]),
        ("先行", "後続", ["開始", "実験", "認識"]),
        ("安定", "変動", ["固定", "共有", "集中"]),
        ("包括", "限定", ["分配", "圧縮", "照合"]),
        ("受諾", "拒否", ["応答", "説明", "掲載"]),
        ("容易", "困難", ["連想", "共有", "発見"]),
        ("早期", "後期", ["短期", "転記", "共有"]),
    ]
    for index, (word, answer, distractors) in enumerate(antonym_sets, start=1):
        bank.append(
            _shuffle_question(
                rng,
                f"次の語と反対の意味に最も近いものを選びなさい。『{word}』",
                answer,
                distractors,
                "verbal",
                f"『{word}』の反対側にある意味は『{answer}』です。",
                f"ant-{index}",
            )
        )

    relation_sets = [
        (("犬", "動物"), "バナナ : 果物", ["赤 : 青", "針 : 縫う", "船 : 港"], "前者が後者に含まれる関係です。"),
        (("教師", "学校"), "医師 : 病院", ["鉛筆 : 紙", "春 : 夏", "長い : 短い"], "ある役割の人と主な活動場所の関係です。"),
        (("定規", "測る"), "温度計 : はかる", ["会議 : 静か", "道路 : 地図", "本棚 : 読む"], "道具とその主な用途の関係です。"),
        (("利益", "損失"), "賛成 : 反対", ["列車 : 駅", "調査 : 集計", "雲 : 雨"], "意味が対になる関係です。"),
        (("鉄", "金属"), "米 : 穀物", ["赤 : 信号", "泳ぐ : 海", "朝 : 時計"], "前者が後者の一種です。"),
        (("注文", "確認"), "応募 : 受付", ["数字 : 単位", "布 : 針", "出発 : 到着"], "ある行為のあとに続く定番の手順です。"),
        (("紙", "木材"), "パン : 小麦", ["雪 : 冬", "時計 : 分", "駅 : 乗車"], "製品と主原料の関係です。"),
        (("原因", "結果"), "努力 : 成果", ["机 : 椅子", "南 : 北", "写真 : 明るい"], "前者が後者を生む関係です。"),
        (("昼", "夜"), "成功 : 失敗", ["運ぶ : 荷物", "封筒 : 手紙", "点 : 線"], "対立する概念の関係です。"),
        (("会員", "登録"), "商品 : 購入", ["道路 : 渋滞", "針 : 指", "空 : 雲"], "対象とそれに対する典型的な行為の関係です。"),
        (("駅", "路線"), "部署 : 組織", ["砂糖 : 甘い", "川 : 速い", "登る : 山"], "前者が後者の構成要素です。"),
        (("企画", "実行"), "準備 : 本番", ["風 : 涼しい", "砂 : 海", "本 : 文字"], "前段階と本体の流れです。"),
        (("苗", "植物"), "卵 : 鳥", ["冬 : 雪", "筆 : 絵", "遠い : 近い"], "成長前と成長後の関係です。"),
        (("議論", "結論"), "分析 : 判断", ["夏 : 海", "靴 : 足", "昼 : 明るい"], "前者を経て後者に至る関係です。"),
        (("鍵", "解錠"), "パスワード : 認証", ["紙 : 白い", "列 : 番号", "窓 : 風"], "手段と目的の関係です。"),
    ]
    for index, (pair, answer, distractors, explanation) in enumerate(relation_sets, start=1):
        bank.append(
            _shuffle_question(
                rng,
                f"『{pair[0]} : {pair[1]}』と最も近い関係を選びなさい。",
                answer,
                distractors,
                "verbal",
                explanation,
                f"rel-{index}",
            )
        )

    for index in range(1, 21):
        base = 40 + index * 3
        percent = 10 + (index % 6) * 5
        answer_value = base * (100 + percent) // 100
        distractors = [str(answer_value + 2), str(answer_value - 2), str(answer_value + percent)]
        bank.append(
            _shuffle_question(
                rng,
                f"{base} 個の商品を {percent}% 増やした個数はいくつか。",
                str(answer_value),
                distractors,
                "nonverbal",
                f"{base} × {(100 + percent) / 100:.2f} = {answer_value} です。",
                f"pct-{index}",
            )
        )

    for index in range(1, 16):
        cost = 400 + index * 80
        markup = 20 + (index % 5) * 5
        discount = 10 + (index % 4) * 5
        sale_price = int(cost * (1 + markup / 100) * (1 - discount / 100))
        profit = sale_price - cost
        bank.append(
            _shuffle_question(
                rng,
                f"原価 {cost} 円の商品を {markup}% 上乗せで定価にし、その後 {discount}% 引きで売った。利益はいくらか。",
                str(profit),
                [str(profit + 20), str(profit - 20), str(sale_price)],
                "nonverbal",
                f"売価は {sale_price} 円、利益は 売価 {sale_price} - 原価 {cost} = {profit} 円です。",
                f"pl-{index}",
            )
        )

    for index in range(1, 16):
        speed = 30 + index * 3
        minutes = 20 + index
        distance = speed * minutes / 60
        answer = f"{distance:.1f}".rstrip("0").rstrip(".")
        bank.append(
            _shuffle_question(
                rng,
                f"時速 {speed} km で {minutes} 分進んだ。進んだ距離は何 km か。",
                answer,
                [
                    f"{distance + 1:.1f}".rstrip("0").rstrip("."),
                    f"{distance - 1:.1f}".rstrip("0").rstrip("."),
                    str(speed + minutes),
                ],
                "nonverbal",
                f"{minutes} 分は {minutes}/60 時間なので、{speed} × {minutes}/60 = {answer} km です。",
                f"spd-{index}",
            )
        )

    for index in range(1, 16):
        a_days = 4 + index % 5
        b_days = 6 + index % 4
        total = a_days * b_days / (a_days + b_days)
        answer = f"{total:.1f}".rstrip("0").rstrip(".")
        bank.append(
            _shuffle_question(
                rng,
                f"Aさんは1人で {a_days} 日、Bさんは1人で {b_days} 日かかる仕事がある。2人で同時に行うと何日かかるか。",
                answer,
                [
                    f"{total + 1:.1f}".rstrip("0").rstrip("."),
                    f"{total - 1:.1f}".rstrip("0").rstrip("."),
                    str(a_days + b_days),
                ],
                "nonverbal",
                f"1日の仕事量は 1/{a_days} と 1/{b_days}。合計は {(a_days + b_days)}/{a_days * b_days} なので、必要日数は {answer} 日です。",
                f"wrk-{index}",
            )
        )

    sequence_sets = [
        ([3, 6, 12, 24], "48", ["30", "36", "42"], "毎回2倍になっています。"),
        ([5, 9, 13, 17], "21", ["19", "22", "25"], "毎回4ずつ増えています。"),
        ([2, 5, 10, 17], "26", ["24", "28", "30"], "差が 3, 5, 7 と増えているので次は +9 です。"),
        ([81, 27, 9, 3], "1", ["0", "2", "6"], "毎回3で割っています。"),
        ([1, 4, 9, 16], "25", ["20", "24", "27"], "平方数の並びです。"),
        ([7, 10, 16, 25], "37", ["34", "35", "39"], "差が 3, 6, 9 と増えているので次は +12 です。"),
        ([64, 32, 16, 8], "4", ["2", "6", "10"], "毎回2で割っています。"),
        ([11, 15, 20, 26], "33", ["31", "34", "36"], "差が 4, 5, 6 なので次は +7 です。"),
        ([100, 90, 72, 46], "12", ["18", "22", "28"], "引く数が 10, 18, 26 と 8 ずつ増えるので次は 34 です。"),
        ([8, 11, 17, 26], "38", ["35", "39", "41"], "差が 3, 6, 9 なので次は +12 です。"),
        ([14, 28, 56, 112], "224", ["168", "196", "256"], "毎回2倍です。"),
        ([4, 7, 13, 22], "34", ["31", "33", "36"], "差が 3, 6, 9 なので次は +12 です。"),
    ]
    for index, (series, answer, distractors, explanation) in enumerate(sequence_sets, start=1):
        text = "、".join(str(value) for value in series)
        bank.append(
            _shuffle_question(
                rng,
                f"数列 {text} の次に入る数を選びなさい。",
                answer,
                distractors,
                "nonverbal",
                explanation,
                f"seq-{index}",
            )
        )

    return bank


SPI_QUESTION_BANK = build_spi_question_bank()
