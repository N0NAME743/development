
# 2026年1月23日作成途中
# 最終的にyfinanceで事業概要が取れない場合の代替手段にしたい

import requests
import zipfile
import io
from datetime import datetime, timedelta

# =========================
# 設定
# =========================
EDINET_API_KEY = "YOUR_API_KEY_HERE"   # ← 必須
EDINET_BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"

# EDINET コード（例：マイクロ波化学  E04788）
EDINET_CODE = "E04788"

# =========================
# 1. 提出書類一覧取得
# =========================
def get_latest_securities_report(edinet_code):
    date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    url = f"{EDINET_BASE_URL}/documents.json"
    params = {
        "date": date,
        "type": 2,            # 2 = 有価証券報告書
        "edinetCode": edinet_code,
        "Subscription-Key": EDINET_API_KEY
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    for doc in data.get("results", []):
        if doc.get("docTypeCode") == "120":  # 有価証券報告書
            return doc["docID"]

    return None


# =========================
# 2. 書類ダウンロード
# =========================
def download_document(doc_id):
    url = f"{EDINET_BASE_URL}/documents/{doc_id}"
    params = {
        "type": 1,  # 1 = ZIP
        "Subscription-Key": EDINET_API_KEY
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.content


# =========================
# 3. ZIP 展開（中身確認）
# =========================
def extract_xbrl(zip_bytes):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        files = z.namelist()
        xbrl_files = [f for f in files if f.endswith(".xbrl")]

        if not xbrl_files:
            return None

        with z.open(xbrl_files[0]) as f:
            return f.read().decode("utf-8", errors="ignore")


# =========================
# 実行
# =========================
if __name__ == "__main__":
    doc_id = get_latest_securities_report(EDINET_CODE)
    if not doc_id:
        print("有価証券報告書が見つかりません")
        exit(1)

    zip_data = download_document(doc_id)
    xbrl_text = extract_xbrl(zip_data)

    if not xbrl_text:
        print("XBRL が取得できません")
        exit(1)

    # ここでは中身を確認するだけ
    print(xbrl_text[:2000])
