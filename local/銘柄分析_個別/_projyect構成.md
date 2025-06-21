更新：2025年6月21日 

/project-root/
├── setup.py                ← フォント・パス・ライブラリなどの初期設定
├── stock_data.py           ← データ取得（yfinance + Excel）
├── chart_config.py         ← チャート描画（mplfinance・注釈付き）
├── gyazo_uploader.py       ← Gyazoへのアップロード処理（API連携）
├── main.py                 ← 全体統括・ループ処理
├── output/                 ← チャート画像出力
│   └── chart/YYYY-MM-DD/chart_XXXX.png     
├── result/                 ← 出力ログ・Excelファイルなど
│   └── gyazo_links.xlsx 
