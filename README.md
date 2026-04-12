# ST-SPACE Game Rooms

FastAPI と WebSocket で動く、ブラウザ向けのオンライン対戦ゲーム集です。
いまは次の 3 ゲームを遊べます。

- 落とし穴陣取りゲーム
- セリすごろく
- ネズミとり

## できること

- ルームを作成して友達と合流
- ルームコードを共有して 2 人以上で参加
- 同じ URL の中でゲームを選択
- ブラウザだけで対戦

## 必要なもの

- Python 3.10 以上
- ターミナル
- ブラウザ

## 実行方法

1. 依存関係を入れます

```bash
pip install -r requirements.txt
```

2. 開発サーバーを起動します

```bash
python -m uvicorn app:app --reload
```

3. ブラウザで開きます

[http://127.0.0.1:8000](http://127.0.0.1:8000)

## ゲーム一覧

### 落とし穴陣取りゲーム

- 2 人用です
- 5x5 の盤で移動、ピット設置、ジャンプを使い分けます
- 足跡の数が多い方が勝ちです

### セリすごろく

- 2 人から 8 人まで遊べます
- サイコロの出目を全員でセリして進みます
- 残高を守りながら、最終的に一番お金を残した人が勝ちです

### ネズミとり

- 2 人用です
- 人間側とネズミ側に分かれます
- 最初に壁を 10 本、`人間 → ネズミ → 人間 ...` の順で交互に置いて迷路を作ります
- 壁は袋小路や 4 本以上の交差を作れません
- 迷路完成後は追跡フェーズに入り、人間は 2 つの駒のどちらかを 1 マス動かします
- ネズミは毎ターンちょうど 2 マス動きます
- 人間は 10 ターン以内に捕まえるか、ネズミを動けなくすると勝ちです
- ネズミは 10 ターン逃げ切れば勝ちです

## ファイル構成

```text
pit_territory_web/
  app.py
  requirements.txt
  render.yaml
  games/
    pit_territory.py
    auction_race.py
    mouse_trap.py
    registry.py
  static/
    index.html
    styles.css
    app.js
```

## 公開について

この構成は Render の `Web Service` でそのまま公開しやすい形です。
GitHub に push したあと、Render でリポジトリをつなげば公開 URL を作れます。

## 次にゲームを増やすとき

1. `games/` に新しいゲームロジックを追加します
2. `games/registry.py` に登録します
3. `static/index.html` と `static/app.js` と `static/styles.css` に画面を追加します

同じ URL の中でゲームを増やしていく方針に向いています。
