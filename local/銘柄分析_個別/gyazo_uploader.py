# ==============================
# Sec｜gyazo_uploader.py
# ==============================

import os
import time
import json
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

today_str = datetime.today().strftime('%Y-%m-%d')      # 既存の日付（例：2025-06-23）
today_compact = datetime.today().strftime('%Y%m%d')    # 新しい形式（例：20250623）

load_dotenv()

GYAZO_ACCESS_TOKEN = os.getenv("GYAZO_ACCESS_TOKEN")
UPLOAD_LOG_PATH = Path(f"result/{today_str}/gyazo_uploaded_{today_compact}.json")

class GyazoUploader:
    def __init__(self, access_token=GYAZO_ACCESS_TOKEN, log_path=UPLOAD_LOG_PATH):
        self.access_token = access_token
        self.log_path = Path(log_path)
        self.uploaded_hashes, self.log_data = self._load_log()

    def _load_log(self):
        if not self.log_path.exists():
            return set(), []
        with open(self.log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(entry["hash"] for entry in data), data

    def _save_log(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.log_data, f, ensure_ascii=False, indent=2)

    def _calculate_hash(self, file_path):
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def upload(self, image_path, max_retry=3):
        file_path = Path(image_path)
        if not file_path.exists():
            print(f"❌ ファイルが存在しません: {file_path}")
            return None

        image_hash = self._calculate_hash(file_path)
        if image_hash in self.uploaded_hashes:
            print(f"⏭️ すでにアップロード済み（スキップ）: {file_path.name}")
            return None

        for attempt in range(1, max_retry + 1):
            start_time = time.time()
            try:
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://upload.gyazo.com/api/upload",
                        data={"access_token": self.access_token},
                        files={"imagedata": f},
                        timeout=15,
                    )
                duration = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ アップロード成功: {file_path.name}（{duration:.2f}秒）")
                    self._record_upload(image_hash, file_path.name, data["url"])
                    self._save_log()
                    time.sleep(self._dynamic_sleep(duration))
                    return data["url"]

                elif response.status_code == 429:
                    print(f"🚫 レート制限（429）: {file_path.name} → 30秒待機して再試行")
                    time.sleep(30)

                elif response.status_code == 503:
                    print(f"⚠️ サーバー過負荷（503）: {file_path.name} → 10秒待機して再試行")
                    time.sleep(10)

                else:
                    print(f"❌ アップロード失敗: {response.status_code} - {response.text}")
                    break  # 致命的な失敗とみなして終了

            except Exception as e:
                print(f"⚠️ 通信エラー: {e} → {10*attempt}秒待機して再試行")
                time.sleep(10 * attempt)

        print(f"❌ 最終的に失敗: {file_path.name}")
        return None

    def _record_upload(self, image_hash, file_name, url):
        self.uploaded_hashes.add(image_hash)
        self.log_data.append({
            "hash": image_hash,
            "file_name": file_name,
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    def _dynamic_sleep(self, duration):
        if duration > 2.5:
            return 5
        elif duration > 1.5:
            return 2
        return 1

