# リペアショップ トップス あきる野店｜デモサイト

**これは店舗から正式に依頼されたWebサイトではありません。** 営業提案の際に「もし専用サイトを作ったらこうなる」を実物で見せるためのデモです。公開情報に基づいて作成しており、料金・実績・レビューなど確認できない情報は一切掲載していません。

サイト本体（`dist/index.html`）とすべてのページにも、公式サイトと誤認されないよう明記しています。

## 概要

- 1ページ完結のランディングページ（スマートフォン優先）
- フレームワーク不要の素のHTML/CSS/JS。API・DB・ログインなし
- 店舗の固有データ（店名・住所・電話・営業時間・サービス内容など）は `business.json` に集約し、そこから `dist/index.html` を生成する構成
  - 電話番号や住所はページ内の何箇所にも登場するため、手打ちでの表記ゆれ・typoを防ぐための最小限のビルドステップ（Jinja2）を挟んでいます
  - 生成後の `dist/` は完全に静的なファイルで、ビルドツールへのランタイム依存はありません

## ディレクトリ構成

```
topps-akiruno/
├── business.json          # 店舗固有データ（情報源はここだけ）
├── template/
│   └── index.html.j2      # ページ全体のJinja2テンプレート
├── src/
│   ├── css/style.css      # スタイル
│   └── js/main.js         # スクロール時の軽いフェードインのみ
├── build.py                # business.json + template/ -> dist/ を生成
├── requirements.txt        # ビルド時にのみ使うJinja2
└── dist/                   # ビルド成果物（実際にデプロイするのはここ）
    ├── index.html
    ├── css/style.css
    └── js/main.js
```

## 起動方法（ローカルで見る）

ビルド済みの `dist/` をそのまま配信するだけです。

```bash
cd dist
python3 -m http.server 8080
```

`http://localhost:8080` を開いて確認してください。

## ビルド方法（内容を変更したとき）

`business.json` または `template/index.html.j2` / `src/` を変更したら、必ず再ビルドしてください。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 build.py
```

`dist/index.html` が再生成されます（`dist/css` `dist/js` も `src/` からコピーされます）。

## デプロイ方法（Vercel）

`dist/` は完全な静的サイトなので、Vercelのビルドステップは不要です。

1. Vercelでこのリポジトリ（またはこのディレクトリ）をインポート
2. **Framework Preset**: `Other`
3. **Build Command**: 空欄のまま（未設定）
4. **Output Directory**: `dist`
5. デプロイ

内容を変更した場合は、ローカルで `python3 build.py` を実行して `dist/` を更新し、コミット・pushしてください（Vercel側で自動的に再デプロイされます）。

## 店舗情報を変更する場所

**`business.json` を編集し、`python3 build.py` を再実行してください。** 店名・住所・電話番号・営業時間・定休日・対応サービス・特徴・FAQ・SEO用のtitle/description/keywords・Google MapsのURLなど、ページに表示される店舗固有の情報はすべてここに集約されています。

`dist/index.html` を直接編集しても次回ビルド時に上書きされて消えるため、変更は必ず `business.json` または `template/` 側に対して行ってください。

### Google MapsのURLについて

指示書内に具体的なURL指定が無かったため、`business.json` の `googleMapsUrl` には住所から生成した標準的な検索URL（`google.com/maps/search/?api=1&query=...`）を設定しています。店舗の正式なGoogleビジネスプロフィールのURLが分かれば、この1箇所を差し替えるだけで反映されます。

## 写真を変更する場所

現在は店舗写真の提供を受けていないため、写真は一切使用していません（CSSの色面とタイポグラフィ、装飾的なSVGのみで構成）。

店舗から写真の提供を受けた場合は、`src/img/`（新規作成）に配置し、`template/index.html.j2` のヒーローセクション（`<section class="hero">` 内）などに `<img>` タグを追加してください。`business.json` に画像パスを持たせる形にすれば、他店舗テンプレートへ流用する際も差し替えが容易です。

## CTAを変更する場所

電話番号・「電話で相談する」ボタンの文言は、`business.json` の `contact.phoneDisplay` / `contact.phoneTel` を変更すれば、ヘッダー・ヒーロー・相談導線・最終CTA・アクセス欄・フッター・モバイル固定CTAのすべてに一括反映されます。ボタンの文言そのものを変えたい場合は `template/index.html.j2`内の該当箇所（`btn--primary` クラスが付いた `<a>` タグ）を編集してください。

## 本番採用する場合の注意

- `template/index.html.j2` の `<meta name="robots" content="noindex, nofollow">` は、デモ段階で検索エンジンに誤って indexされないようにするための安全策です。**正式に店舗サイトとして公開する場合は、この行を削除してください。**
- フッターの「本サイトはWebサイト制作提案用のデモページです」の一文、およびページ上部のデモバナー（`.demo-banner`）は、正式サイトとして採用する際は削除してください。
- 本サイトに掲載されている「27年以上の経験」等の情報は、公開情報をもとにした記載です。正式サイト化の際は、店舗に最終確認を取ってください。

## 動作確認済みの項目

- HTML: タグの開閉バランス、`html.parser` によるパースエラー無し
- 埋め込みSVGアイコン: 12個すべてXMLとして妥当
- CSS: 波括弧の対応確認済み
- ローカルHTTPサーバーでの配信確認（`index.html` / `css/style.css` / `js/main.js` すべて200）
- 見出し階層: `h1`が1つ、各セクションに`h2`が1つずつ、カード等に`h3`（階層の飛ばしなし）
- 電話番号・住所・営業時間・定休日の表記が全箇所で一致していること（ビルドスクリプトで確認）
- 架空情報（料金・実績・レビュー・誇張表現など）が含まれていないこと（`business.json`の内容と指示書の禁止事項を照合）

**未確認の項目（実ブラウザでの目視確認を推奨）**: この環境にはブラウザ・Node.jsが無いため、実際のスマートフォン/PC表示の見た目、Lighthouseスコア、色のコントラスト比の厳密な計測は行っていません。デプロイ後、実機での確認をお願いします。

## 将来のテンプレート化について

このリポジトリは `clients/<業種>/<店舗名>/` という構成にしてあります。他業種（`clients/electrician/`, `clients/plumber/` など）へ展開する場合は、この `topps-akiruno/` ディレクトリを丸ごとコピーし、`business.json` の内容を差し替え、`src/css/style.css` の配色（`:root` のCSS変数）を業種に合わせて調整するだけで再利用できる想定です。`template/index.html.j2` のセクション構成・コンポーネント（`.trouble-card` `.service-card` `.faq-item` 等）はほぼそのまま使い回せます。
