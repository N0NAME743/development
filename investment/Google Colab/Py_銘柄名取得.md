
# ✅ 既存データ読み込み
symbols = sheet.col_values(1)[1:]  # A列
existing_names = sheet.col_values(2)[1:]  # B列
existing_prices = sheet.col_values(3)[1:]  # C列
existing_timestamps = sheet.col_values(4)[1:]  # D列

# ✅ 出力用リスト
names = ['Name']
prices = ['Price']
timestamps = ['Time']
failed_symbols = []
updated_count = 0
start_time = time.time()

# ✅ メイン処理ループ
for i, symbol in enumerate(symbols):
    full_symbol = f"{symbol}.T"

    if i > 0 and i % 100 == 0:
        elapsed = time.time() - start_time
        avg = elapsed / i
        rem = avg * (len(symbols) - i)
        print(f"🔄 {i}件処理中… 所要: {elapsed:.1f}s / 残り予想: 約{rem/60:.1f}分")

    # キャッシュ利用
    if full_symbol in cache_df.index:
        row = cache_df.loc[full_symbol]
        names.append(sanitize_value(row["Name"]))
        prices.append(sanitize_value(row["Price"]))
        if i < len(existing_timestamps) and existing_timestamps[i].strip():
            timestamps.append(existing_timestamps[i])
        else:
            timestamps.append(row["Time"])
        continue

    # 新規取得
    try:
        ticker = yf.Ticker(full_symbol)
        info = ticker.info
        name = info.get("shortName", "取得失敗")
        hist = ticker.history(period="5d")
        close_price = hist["Close"].dropna().iloc[-1] if not hist.empty else "N/A"
        if name == "取得失敗" or close_price == "N/A":
            failed_symbols.append(symbol)
    except:
        name = "エラー"
        close_price = "N/A"
        failed_symbols.append(symbol)

    names.append(name)
    prices.append(close_price)
    timestamps.append(now_str)
    cache_df.loc[full_symbol] = [name, close_price, now_str]
    updated_count += 1

# ✅ シートに反映（B〜D列）
sheet.update(range_name="B1", values=[[v] for v in names])
sheet.update(range_name="C1", values=[[v] for v in prices])
sheet.update(range_name="D1", values=[[v] for v in timestamps])

# ✅ キャッシュ保存
cache_df.sort_index(inplace=True)
cache_df.to_csv(CACHE_FILE, encoding="utf-8-sig")
print(f"💾 キャッシュ保存完了: {CACHE_FILE}")

# ✅ バックアップファイル名
backup_title = f"{spreadsheet_title}_{today_str}"

# ✅ 既存バックアップがあれば削除（Drive APIを使用）
try:
    existing_files = drive_service.files().list(
        q=f"name='{backup_title}' and mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id)"
    ).execute()

    if existing_files["files"]:
        file_id = existing_files["files"][0]["id"]
        drive_service.files().delete(fileId=file_id).execute()
        print(f"🗑️ 既存バックアップ削除: {backup_title}")
except Exception as e:
    print(f"⚠️ バックアップ削除エラー: {e}")

# ✅ バックアップ作成（新規ファイル）
backup_sheet = gc.create(backup_title)
backup_ws = backup_sheet.get_worksheet(0)  # ✅ 必ずここで定義
data = sheet.get_all_values()
backup_ws.update(range_name="A1", values=data)

print(f"📁 バックアップ作成完了: {backup_title}")

# ✅ バックアップを元のフォルダに移動
try:
    # 元ファイルの親フォルダを取得
    original_file = drive_service.files().get(fileId=spreadsheet_id, fields='parents').execute()
    parent_folder_id = original_file.get('parents', [None])[0]

    # バックアップのID取得
    result = drive_service.files().list(q=f"name='{backup_title}'", fields="files(id)").execute()
    backup_id = result["files"][0]["id"]

    # ルートから削除、親フォルダに追加
    drive_service.files().update(
        fileId=backup_id,
        addParents=parent_folder_id,
        removeParents="root",
        fields="id, parents"
    ).execute()

    print(f"📂 バックアップを元のフォルダに移動完了（ID: {parent_folder_id}）")
except Exception as e:
    print(f"⚠️ フォルダ移動エラー: {e}")

# ✅ 実行完了ログ
elapsed = time.time() - start_time
print("✅ データ取得・保存すべて完了！")
print(f"📄 元ファイル名: {spreadsheet_title}")
print(f"🆕 新規取得数: {updated_count} 行")
print(f"⏱️ 処理時間: {elapsed:.1f} 秒")

if failed_symbols:
    from collections import defaultdict

    grouped = defaultdict(list)
    for code in failed_symbols:
        try:
            prefix = int(code) // 1000 * 1000  # ← 1,000単位で分類
            grouped[f"{prefix}番台"].append(code)
        except:
            grouped["不明"].append(code)

    print(f"⚠️ 取得失敗銘柄（{len(failed_symbols)}件）:")
    for group in sorted(grouped.keys()):
        print(f"{group}: [{', '.join(grouped[group])}]")
else:
    print("🎉 全銘柄正常に取得完了！")