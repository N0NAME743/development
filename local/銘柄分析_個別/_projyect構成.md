更新：2025年6月21日 

/project-root/
├── 1.setup.py                ← フォント・パス・ライブラリなどの初期設定
├── 2.stock_data.py           ← データ取得（yfinance + Excel）
├── 3.chart_config.py         ← チャート描画（mplfinance・注釈付き）
├── 4.gyazo_uploader.py       ← Gyazoへのアップロード処理（API連携）
├── 5.slack_notifier.py       ← 🆕 Slack通知の処理（Webhook＋整形）
├── 6.database.py           ← 🆕 データベース保存・取得の管理（SQLite用）
├── 7.main.py                 ← 全体統括・ループ処理
├── output/                 ← チャート画像出力
│   └── chart/YYYY-MM-DD/chart_XXXX.png     
├── result/                 ← 出力ログ・Excelファイルなど
│   └── gyazo_links.xlsx 