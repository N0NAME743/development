# setup.py

"""
初回実行時に必要なライブラリ：
pip install -r requirements.txt
または個別に以下を実行してください：

pip install yfinance japanize-matplotlib mplfinance ta pandas matplotlib openpyxl
"""

import japanize_matplotlib
import matplotlib.pyplot as plt

# ✅ グローバルフォント設定
JP_FONT = "IPAexGothic"
plt.rcParams['font.family'] = JP_FONT

# ✅ Excelファイルパス
EXCEL_PATH = "Symbols.xlsx"
