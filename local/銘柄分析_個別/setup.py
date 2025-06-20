# ==============================
# Sec｜Setup.py
# ==============================

"""
初回実行時に必要なライブラリ：
pip install -r requirements.txt
または個別に以下を実行してください：

pip install yfinance japanize-matplotlib mplfinance ta pandas matplotlib openpyxl
"""

print("📄 このファイルは実行されています:", __file__)

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ✅ グローバルフォント設定（日本語表示用）
JP_FONT = "IPAexGothic"
plt.rcParams['font.family'] = JP_FONT

# ✅ Excelファイルパス
EXCEL_PATH = "Symbols.xlsx"

# ✅ 使用可能なIPAフォント確認（任意）
for f in fm.fontManager.ttflist:
    if 'IPAex' in f.name:
        print("✅ 利用可能なIPAフォント:", f.name, f.fname)
