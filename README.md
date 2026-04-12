# ST-SPACE Game Rooms

FastAPI と WebSocket で動く、ブラウザ向けのオンライン対戦ゲーム集です。

現在は次の2ゲームを選べます。

- `落とし穴陣取りゲーム`
- `セリすごろく`

## できること

- 1つのロビーからゲームを選んで部屋を作成
- ルームIDで友達を招待
- WebSocket でリアルタイム同期
- 同じ部屋のまま再戦
- セリすごろくは 2〜8 人まで参加可能

## 必要なもの

ローカルで動かすだけなら、次だけあれば十分です。

- Python 3.10 以上
- ターミナル
- ブラウザ

このバージョンでは不要です。

- 有料サーバー
- ログイン
- アカウント作成
- データベース

## 起動方法

1. 依存関係を入れます。

   ```bash
   pip install -r requirements.txt
   ```

2. サーバーを起動します。

   ```bash
   python -m uvicorn app:app --reload
   ```

3. ブラウザで開きます。

   [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 遊び方

### 落とし穴陣取りゲーム

- 2人対戦です
- 部屋主が先手を決めます
- 移動、ジャンプ、ピット、行動終了が使えます
- 足跡の数が多い方の勝ちです

### セリすごろく

- 参加人数はルームに入った人数で決まります
- 部屋主が「この人数で開始する」を押すと開始します
- 毎ラウンド、出目が先に公開されます
- 各プレイヤーは銀行で入札額を 1000 円単位で入力します
- 全員が確定すると自動でジャッジされます
- 最高額の人が出目を購入して進みます
- 同額トップが複数人いたときは、出目を人数で割ったマス数だけ全員が進みます
- 残高はゲーム終了まで自分にだけ見えます
- 残高がマイナスになると脱落です
- 降参ボタンも使えます
- 最後に残高が最も高い人の勝ちです

## セリすごろくの初期設定

`games/auction_race.py` で、次の値を手動調整できます。

- 初期所持金
- サイコロ上限
- コース長の計算式
- 先着テープのボーナス
- クイック入札ボタン
- 金額マスの候補

主にこのあたりです。

- `DEFAULT_STARTING_BALANCE`
- `DEFAULT_DICE_SIDES`
- `DEFAULT_TRACK_EXTRA`
- `DEFAULT_TRACK_PER_PLAYER`
- `DEFAULT_TAPE_BONUS`
- `DEFAULT_QUICK_BIDS`
- `BOARD_MONEY_VALUES`

## ファイル構成

```text
pit_territory_web/
  app.py
  requirements.txt
  render.yaml
  games/
    pit_territory.py
    auction_race.py
    registry.py
  static/
    index.html
    styles.css
    app.js
```

## Render へ公開するとき

この構成は FastAPI が API と WebSocket と静的ファイルをまとめて配信するので、Render では `Web Service` ひとつで動かせます。

無料プランでも試せますが、次の点は知っておくと安心です。

- 一定時間アクセスがないとスリープする
- 最初のアクセスで起動待ちが発生する
- 状態はメモリ保存なので、再起動するとルームは消える

## 今後の拡張向けメモ

- 新しいゲームは `games/` に追加
- `games/registry.py` に登録
- 画面が専用UIを必要とするなら `static/app.js` と `static/index.html` を拡張

今の土台は、複数ゲームを1つのURLで切り替えて遊ぶ前提で作っています。
