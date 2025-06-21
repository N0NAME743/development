# ==============================
# Sec｜gyazo_uploader.py
# ==============================

import requests

print("📄 このファイルは実行されています:", __file__)

def upload_to_gyazo(image_path: str, access_token: str, desc: str = None) -> str:
    """
    Gyazoへ画像をアップロードしてURLを返す

    Args:
        image_path (str): 画像ファイルのパス
        access_token (str): Gyazo APIトークン
        desc (str, optional): Gyazo画像の説明文（任意）

    Returns:
        str: Gyazo画像URL（失敗時はNone）
    """
    upload_url = "https://upload.gyazo.com/api/upload"

    try:
        with open(image_path, 'rb') as image_file:
            data = {'access_token': access_token}
            if desc:
                data['desc'] = desc

            response = requests.post(
                upload_url,
                data=data,
                files={'imagedata': image_file},
                timeout=10
            )

        response.raise_for_status()

        url = response.json().get("url")
        if not url:
            print("⚠️ Gyazoアップロードは成功しましたが、URLが取得できませんでした。")
            return None

        print(f"✅ Gyazoアップロード成功: {url}")
        return url

    except requests.exceptions.Timeout:
        print("❌ タイムアウトによりGyazoアップロードに失敗しました。")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTPエラーが発生しました: {e}")
        if e.response is not None:
            print(f"  - ステータスコード: {e.response.status_code}")
            print(f"  - レスポンス内容: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 予期せぬエラー: {e}")

    return None
