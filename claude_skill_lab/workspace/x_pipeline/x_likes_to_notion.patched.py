import os
import json
import sqlite3
import requests

from datetime import date

from dotenv import load_dotenv
from google import genai


# =========================================================
# Paths
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
DB_PATH = os.path.join(BASE_DIR, "state.db")


# =========================================================
# Environment
# =========================================================

load_dotenv(ENV_PATH)

X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_REFRESH_TOKEN = os.getenv("X_REFRESH_TOKEN")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID")

# 「記録_IDEA from SNS」内のIDEA BOXデータベース。
# AI査定が🟢 IDEA BOXへの投稿だけ、ここへもコピーする（INBOX側は残す＝広く浅いCapture、
# IDEA BOXは狭く深いCurated、というユーザー自身の設計メモに沿った役割分担）。
NOTION_IDEA_BOX_DATA_SOURCE_ID = os.getenv("NOTION_IDEA_BOX_DATA_SOURCE_ID")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================================================
# Clients / Headers
# =========================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

notion_headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json",
}


# =========================================================
# .env update
# =========================================================

def update_env_value(key, value):
    """
    .env の指定キーだけを書き換える。
    既存ファイルをそのまま更新するので、
    chmod 600 の権限を維持しやすい。
    """

    with open(ENV_PATH, "r+", encoding="utf-8") as f:
        lines = f.readlines()

        new_lines = []
        found = False

        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        f.seek(0)
        f.writelines(new_lines)
        f.truncate()


# =========================================================
# X OAuth2 Refresh
# =========================================================

def refresh_x_access_token():
    """
    X Access Token の期限切れ時に
    Refresh Token を使って自動更新する。
    """

    global X_ACCESS_TOKEN
    global X_REFRESH_TOKEN

    print("X Access Tokenを更新します")

    response = requests.post(
        "https://api.x.com/2/oauth2/token",
        auth=(
            X_CLIENT_ID,
            X_CLIENT_SECRET
        ),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": X_REFRESH_TOKEN,
        },
        timeout=30,
    )

    response.raise_for_status()

    token_data = response.json()

    new_access_token = token_data["access_token"]

    new_refresh_token = token_data.get(
        "refresh_token",
        X_REFRESH_TOKEN
    )

    # メモリ上のTokenを更新
    X_ACCESS_TOKEN = new_access_token
    X_REFRESH_TOKEN = new_refresh_token

    # 次回起動用に.envへ保存
    update_env_value(
        "X_ACCESS_TOKEN",
        new_access_token
    )

    update_env_value(
        "X_REFRESH_TOKEN",
        new_refresh_token
    )

    print("X Access Token更新成功")


# =========================================================
# X API request helper
# =========================================================

def x_get(url, params=None):
    """
    X APIへGET。

    Access Tokenが期限切れで401になった場合、
    Refresh Tokenで更新して1回だけ再試行する。
    """

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {X_ACCESS_TOKEN}"
        },
        params=params,
        timeout=30,
    )

    if response.status_code == 401:
        print("X Access Tokenの期限切れを検出しました")

        refresh_x_access_token()

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {X_ACCESS_TOKEN}"
            },
            params=params,
            timeout=30,
        )

    response.raise_for_status()

    return response


# =========================================================
# FxTwitter API (本文/引用/Article/メディアの完全取得)
#
# X API公式のtweet.textは280字超のnote_tweetを展開せず、
# 引用ツイートの中身も一切取得できない。
# FxTwitter経由でTweet IDから直接取得することでこれを補う。
#
# 失敗時はNoneを返し、呼び出し側でX API公式のtextへ
# フォールバックする（単一障害点にしない）。
# =========================================================

FXTWITTER_API_BASE = "https://api.fxtwitter.com/status"


def normalize_fxtwitter_status(raw):
    """
    FxTwitterのtweetオブジェクトを、
    本文・作者・引用・Article・メディアだけの
    軽量な辞書に正規化する（quoteは再帰的に正規化）。
    """

    if raw.get("type") == "tombstone":
        return {
            "available": False,
            "reason": raw.get("reason"),
            "message": raw.get("message"),
        }

    article = raw.get("article")

    if article:
        blocks = article.get("content", {}).get("blocks", [])

        article_text = "\n\n".join(
            b.get("text", "") for b in blocks
        )

        article = {
            "title": article.get("title"),
            "preview_text": article.get("preview_text"),
            "text": article_text,
        }

    quote = raw.get("quote")

    if quote:
        quote = normalize_fxtwitter_status(quote)

    media_all = raw.get("media", {}).get("all", []) or []

    media = [
        {
            "type": m.get("type"),
            "url": m.get("url"),
            "width": m.get("width"),
            "height": m.get("height"),
        }
        for m in media_all
    ]

    return {
        "available": True,
        "id": raw.get("id"),
        "url": raw.get("url"),
        "author": {
            "name": raw.get("author", {}).get("name"),
            "screen_name": raw.get("author", {}).get("screen_name"),
        },
        "lang": raw.get("lang"),
        "text": raw.get("text", ""),
        "quote": quote,
        "article": article,
        "media": media,
    }


def fetch_fxtwitter_post(tweet_id):
    """
    FxTwitter経由で本文・引用・Article・メディアを取得する。

    失敗した場合はNoneを返す。
    呼び出し側はX API公式のtextへフォールバックすること。
    """

    try:
        response = requests.get(
            f"{FXTWITTER_API_BASE}/{tweet_id}",
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != 200:
            print(
                f"FxTwitter取得失敗 (code={data.get('code')}): {tweet_id}"
            )

            return None

        return normalize_fxtwitter_status(data["tweet"])

    except Exception as e:
        print(
            f"FxTwitter取得失敗: {tweet_id} {e}"
        )

        return None


# =========================================================
# SQLite
# =========================================================

def init_db():
    """
    保存済みTweet IDを管理するSQLite DBを初期化。
    """

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_tweets (
            tweet_id TEXT PRIMARY KEY,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    return conn


def already_processed(conn, tweet_id):
    """
    TweetがすでにNotionへ保存済みか確認。
    """

    row = conn.execute(
        "SELECT 1 FROM processed_tweets WHERE tweet_id = ?",
        (tweet_id,)
    ).fetchone()

    return row is not None


def mark_processed(conn, tweet_id):
    """
    保存成功したTweet IDを処理済みとして登録。
    """

    conn.execute(
        "INSERT OR IGNORE INTO processed_tweets (tweet_id) VALUES (?)",
        (tweet_id,)
    )

    conn.commit()


# =========================================================
# X API
# =========================================================

def get_my_user_id():
    """
    認証ユーザー自身のX User IDを取得。
    """

    response = x_get(
        "https://api.x.com/2/users/me"
    )

    return response.json()["data"]["id"]


def get_liked_posts(user_id):
    """
    最新20件のLiked Postsを取得。
    """

    response = x_get(
        f"https://api.x.com/2/users/{user_id}/liked_tweets",
        params={
            "max_results": 20,
            "tweet.fields": "author_id,created_at,text",
            "expansions": "author_id",
            "user.fields": "username,name",
        },
    )

    return response.json()


# =========================================================
# Notion schema (CATEGORY / LANGUAGE の選択肢を実行時に取得)
#
# 選択肢をコードに固定せず、Notion側の現在のプロパティ定義
# から毎回取得する。手動で追加したCATEGORYも、次回実行時には
# 自動的にAIの選択肢に含まれるようになる。
# =========================================================

def get_data_source_schema(data_source_id=None):
    response = requests.get(
        f"https://api.notion.com/v1/data_sources/{data_source_id or NOTION_DATA_SOURCE_ID}",
        headers=notion_headers,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def get_select_option_names(schema, property_name, kind):
    """
    kind: "select" または "multi_select"
    """

    prop = schema.get("properties", {}).get(property_name, {})

    options = prop.get(kind, {}).get("options", [])

    return [o["name"] for o in options if o.get("name")]


# デフォルト値（Notionのスキーマ取得に失敗した場合のフォールバック用）
DEFAULT_CATEGORY_OPTIONS = ["未分類"]
DEFAULT_LANGUAGE_OPTIONS = [
    "🇯🇵 日本語", "🇺🇸 English", "🇨🇳 中文", "🇪🇸 Español", "🌐 Other",
]
DEFAULT_AI_HANTEI_OPTIONS = [
    "🟢 IDEA BOXへ", "⚪ 保留", "🔴 重複", "⚠️ 取得失敗",
]
DEFAULT_IDEA_BOX_TAG_OPTIONS = []
DEFAULT_IDEA_BOX_PROJECT_OPTIONS = []
DEFAULT_IDEA_BOX_AI_HYOKA_OPTIONS = ["高", "中", "低"]

# ⚠️ 取得失敗はコード側で直接設定する専用値（Geminiには選ばせない）。
AI_HANTEI_FETCH_FAILED = "⚠️ 取得失敗"

# この値になったときだけ、IDEA BOXデータベースへも複製する。
AI_HANTEI_IDEA_BOX = "🟢 IDEA BOXへ"

# 本文が一切取得できなかった場合の定型タイトル・要約
# （以前ChatGPTで手動運用していたときの表記に合わせている）
FETCH_FAILED_TITLE = "対象のX投稿の内容が取得できなかったためタイトルを生成できません"
FETCH_FAILED_SUMMARY = "対象のX投稿の内容が確認できないため、AI整理メモを作成できません。"


def get_recent_inbox_titles(limit=30):
    """
    直近のINBOXページタイトルを取得する。
    AI査定（🔴 重複）判定の材料として使う。
    取得に失敗しても空リストで継続する（重複判定が甘くなるだけで、
    パイプライン自体は止めない）。
    """

    try:
        response = requests.post(
            f"https://api.notion.com/v1/data_sources/{NOTION_DATA_SOURCE_ID}/query",
            headers=notion_headers,
            json={
                "sorts": [{"timestamp": "created_time", "direction": "descending"}],
                "page_size": limit,
            },
            timeout=30,
        )

        response.raise_for_status()

        titles = []

        for page in response.json().get("results", []):
            title_rt = page.get("properties", {}).get("Name", {}).get("title", [])

            if title_rt:
                titles.append(title_rt[0]["plain_text"])

        return titles

    except Exception as e:
        print(f"直近タイトルの取得失敗、重複判定なしで継続: {e}")

        return []


# ユーザーの興味分野（AI査定「🟢 IDEA BOXへ」判定の目安として使う）。
# 実際の興味の変化に合わせて、ここを直接編集してよい。
USER_INTEREST_PROFILE = """
・AIコーディングツール、Claude Code関連
・プロンプトエンジニアリング、AIエージェントの自動化
・画像/動画生成AI
・個人開発・自動化パイプライン構築（Notion連携、Raspberry Piでの自前運用など）
"""


# =========================================================
# Gemini
# =========================================================

def generate_ai_content(
    tweet_text,
    category_options,
    language_options,
    ai_hantei_options=None,
    recent_titles=None,
    idea_box_tag_options=None,
    idea_box_project_options=None,
    idea_box_ai_hyoka_options=None,
    has_quote=False,
    has_post_article=False,
    has_quote_article=False,
):
    """
    Geminiを使って、1回のAPI呼び出しで以下をまとめて生成する。

    1. クリックしたくなる自然な日本語タイトル
    2. 読みやすい日本語整理メモ（引用元・Articleの内容も踏まえる）
    3. LANGUAGE（元投稿の言語。Notionの既存選択肢から1つ）
    4. CATEGORY（Notionの既存選択肢から。無ければ["未分類"]）
    5. 各セクションの日本語訳（原文が日本語以外の場合のみ。
       原文は消さずページ側で併記する）
    6. AI査定（🟢 IDEA BOXへ / ⚪ 保留 / 🔴 重複。以前ChatGPTで手動判定していたものの自動化）
    7. IDEA BOX用の付随情報（AI査定が🟢の場合だけ実際に使用される。
       「気になった理由・使い道」「AI評価」「タグ」「関連プロジェクト」）

    呼び出し回数は投稿1件につき1回のまま増やさない
    （判定・生成項目が増えてもAPIリクエスト数は変わらない）。

    Geminiに失敗した場合は、元投稿ベースのフォールバック値を返す
    （AI査定は安全側の「⚪ 保留」にする。誤って🟢と判定するより保留の方が安全）。
    """

    ai_hantei_options = ai_hantei_options or DEFAULT_AI_HANTEI_OPTIONS
    recent_titles = recent_titles or []
    idea_box_tag_options = idea_box_tag_options or DEFAULT_IDEA_BOX_TAG_OPTIONS
    idea_box_project_options = idea_box_project_options or DEFAULT_IDEA_BOX_PROJECT_OPTIONS
    idea_box_ai_hyoka_options = idea_box_ai_hyoka_options or DEFAULT_IDEA_BOX_AI_HYOKA_OPTIONS

    # Geminiに選ばせるのは「⚠️ 取得失敗」を除いた選択肢のみ。
    # （取得失敗はコード側で直接判定するため、AIの判断対象にしない）
    ai_hantei_choices = [
        o for o in ai_hantei_options if o != AI_HANTEI_FETCH_FAILED
    ]
    fallback_ai_hantei = "⚪ 保留" if "⚪ 保留" in ai_hantei_choices else (
        ai_hantei_choices[0] if ai_hantei_choices else None
    )

    fallback_title = (
        tweet_text
        .replace("\n", " ")
        .strip()[:60]
    )

    fallback_summary = tweet_text.strip()

    fallback = {
        "title": fallback_title,
        "summary": fallback_summary,
        "language": None,
        "category": ["未分類"] if "未分類" in category_options else [],
        "ai_hantei": fallback_ai_hantei,
        "idea_box_reason": "",
        "idea_box_ai_hyoka": None,
        "idea_box_tags": [],
        "idea_box_projects": [],
        "translations": {
            "post": None,
            "quote": None,
            "post_article": None,
            "quote_article": None,
        },
    }

    if not GEMINI_API_KEY:
        return fallback

    category_list_text = "\n".join(
        f"・{c}" for c in category_options
    ) or "・未分類"

    language_list_text = "\n".join(
        f"・{lang}" for lang in language_options
    ) or "・🌐 Other"

    ai_hantei_list_text = "\n".join(
        f"・{h}" for h in ai_hantei_choices
    ) or "・⚪ 保留"

    idea_box_tag_list_text = "\n".join(
        f"・{t}" for t in idea_box_tag_options
    ) or "（既存タグなし。空配列でよい）"

    idea_box_project_list_text = "\n".join(
        f"・{p}" for p in idea_box_project_options
    ) or "（既存プロジェクトタグなし。空配列でよい）"

    idea_box_ai_hyoka_list_text = "\n".join(
        f"・{h}" for h in idea_box_ai_hyoka_options
    ) or "・中"

    recent_titles_text = "\n".join(
        f"・{t}" for t in recent_titles
    ) or "（直近の投稿なし）"

    needed_translation_keys = ["post"]

    if has_quote:
        needed_translation_keys.append("quote")

    if has_post_article:
        needed_translation_keys.append("post_article")

    if has_quote_article:
        needed_translation_keys.append("quote_article")

    prompt = f"""
以下のX投稿を、個人用Notionデータベースで
後から見返しやすい形に整理してください。

投稿本文には、引用元投稿やArticle本文が
[引用元投稿] [Article本文] というラベル付きで
追加されている場合があります。

【最重要ルール】
title と summary は、投稿が何語であっても
必ず日本語で書いてください。
中国語・英語・その他どの言語の投稿であっても、
title と summary に原文の言語をそのまま
残すことは禁止です（例外なし）。

translations は title/summary とは別の、
本文全体を一字一句日本語に翻訳するための
独立した項目です。translationsで翻訳するからといって
title/summaryを原文の言語のままにしてはいけません。
title/summaryは常に日本語、translationsは
必要な場合のみ本文全体の日本語訳、という
2つの別々の仕事だと考えてください。

必ずJSON形式で、次の項目を返してください。

{{
  "title": "日本語タイトル（原文が何語でも必ず日本語）",
  "summary": "日本語の整理メモ（原文が何語でも必ず日本語）",
  "language": "投稿本文（[引用元投稿]や[Article本文]は含まない、一番最初の投稿）の言語",
  "category": ["該当するカテゴリ名の配列"],
  "ai_hantei": "下記の選択肢から1つ",
  "ai_hantei_reason": "判定理由（日本語、1文程度）",
  "idea_box_reason": "気になった理由・使い道（日本語、1〜2文。ai_hanteiが🟢以外でも一応埋める）",
  "idea_box_ai_hyoka": "下記の選択肢から1つ（情報としての価値の高さ）",
  "idea_box_tags": ["下記の既存タグ一覧から該当するものだけの配列。無理に選ばない"],
  "idea_box_projects": ["下記の既存プロジェクト一覧から関連するものだけの配列。無理に選ばない"],
  "translations": {{
    "post": "投稿本文の日本語訳、または null",
    "quote": "[引用元投稿]の日本語訳、または null（無ければ常にnull）",
    "post_article": "[Article本文]（投稿自身のArticle）の日本語訳、または null（無ければ常にnull）",
    "quote_article": "引用先がArticleの場合その日本語訳、または null（無ければ常にnull）"
  }}
}}

【title の条件】

・必ず日本語（原文が中国語・英語などでも日本語。これが最優先）
・25〜45文字程度を目安にする
・後から一覧を見たとき、思わずもう一度開きたくなるタイトルにする
・ただし内容が具体的に分かることを最優先する
・単なる投稿本文の冒頭コピーにしない
・煽りすぎない
・「ヤバい」「絶対見るべき」「知らないと損」などの釣り表現は禁止
・「〜について」のような曖昧なタイトルを避ける
・製品名、サービス名、AI名、技術名などは必要なら原文表記を残す
・タイトルだけで内容の特徴や価値がある程度分かるようにする


【summary の条件】

・必ず日本語（原文が中国語・英語などでも日本語。これが最優先）
・100〜250文字程度を目安にする
・元投稿の重要な内容を整理して読みやすくする
・長い投稿は要点を圧縮する
・短い投稿は無理に長くしない
・必要なら改行を使って読みやすくする
・元投稿にない情報を勝手に追加しない
・事実と推測を混同しない
・宣伝的、感情的、冗長な表現は整理する
・URL、製品名、サービス名など重要情報は必要なら残す
・原文の意味を変えない


【language の条件】

・以下の選択肢の表記そのまま、1つだけを返す
・判定対象は投稿本文のみ（[引用元投稿]や[Article本文]は無視する）

{language_list_text}


【category の条件】

・以下の既存カテゴリの表記そのまま使い、配列で返す（複数可）
・新しいカテゴリ名を勝手に作らない
・内容に近いものが無ければ ["未分類"] とする

{category_list_text}


【ai_hantei の条件】

以下の選択肢から1つだけ選ぶ。

{ai_hantei_list_text}

判定基準:

・「🟢 IDEA BOXへ」: 具体的な手法・ツール・実装が書かれており、後から自分の作業に応用・参照する価値がある
・「⚪ 保留」: 単なるニュース・宣伝・感想止まりで深掘りする価値が薄い場合、または下記の興味分野に直結せず今の自分には不要と思われる場合
・「🔴 重複」: 下記の直近投稿一覧と話題・内容が明確に重複している場合

【ユーザーの興味分野（🟢 IDEA BOXへ 判定の目安）】
{USER_INTEREST_PROFILE}
上記に直結しない一般ニュース・宣伝・感想止まりの投稿は「⚪ 保留」寄りに判定する。

厳密な判定である必要はない。迷ったら「⚪ 保留」にしてよい（最終確認は人間が行う）。

【直近のINBOX投稿タイトル（重複判定用）】

{recent_titles_text}


【idea_box_reason / idea_box_ai_hyoka / idea_box_tags / idea_box_projects の条件】

これらは、ai_hanteiが「🟢 IDEA BOXへ」の場合にのみ実際に使用される
（別データベース「IDEA BOX」へ複製する際の項目）。それ以外の判定でも
一応埋めてよいが、手を抜いて構わない。

・idea_box_reason: なぜ気になったか、後で何に使えそうかを1〜2文で
・idea_box_ai_hyoka: 情報としての価値。以下から1つだけ選ぶ

{idea_box_ai_hyoka_list_text}

・idea_box_tags: 以下の既存タグの表記そのまま使い、配列で返す（複数可、0個でもよい）。新しいタグ名を勝手に作らない

{idea_box_tag_list_text}

・idea_box_projects: 以下の既存プロジェクトの表記そのまま使い、配列で返す（複数可、0個でもよい）。新しい名前を勝手に作らない。明確に関連しなければ空配列にする

{idea_box_project_list_text}


【translations の条件】

・必要なキーは次の通り: {needed_translation_keys}
・上記に無いキーは常に null
・対応する原文がすでに自然な日本語の場合は null
・原文が日本語以外の場合のみ、自然な日本語訳を作る
・原文の意味を変えない、情報を足さない
・要約ではなく全文の翻訳にする


【X投稿】

{tweet_text}
"""

    try:
        interaction = gemini_client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
        )

        raw = interaction.output_text.strip()

        # GeminiがMarkdownコードブロック付きで
        # JSONを返した場合に除去する。
        if raw.startswith("```"):
            lines = raw.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            raw = "\n".join(lines).strip()

            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        data = json.loads(raw)

        title = str(
            data.get(
                "title",
                fallback_title
            )
        ).strip()

        summary = str(
            data.get(
                "summary",
                fallback_summary
            )
        ).strip()

        if not title:
            title = fallback_title

        if not summary:
            summary = fallback_summary

        # 想定外に長いタイトルを防ぐ
        title = title[:100]

        # languageはNotionの既存選択肢と完全一致する場合のみ採用。
        # 一致しなければ未設定のままにする（誤った値を書き込まない）。
        language = data.get("language")

        if language not in language_options:
            language = None

        # categoryはNotionの既存選択肢に含まれるものだけ採用。
        # Geminiが新しい名前を捏造しても無視する。
        category = data.get("category") or []

        if not isinstance(category, list):
            category = [category]

        category = [
            c for c in category
            if isinstance(c, str) and c in category_options
        ]

        if not category:
            category = ["未分類"] if "未分類" in category_options else []

        # ai_hanteiはNotionの既存選択肢（⚠️ 取得失敗を除く）と
        # 完全一致する場合のみ採用。一致しなければ安全側の
        # フォールバック値（⚪ 保留 相当）にする。
        ai_hantei = data.get("ai_hantei")

        if ai_hantei not in ai_hantei_choices:
            print(
                f"AI査定の判定値が選択肢外のためフォールバックします: {ai_hantei!r}"
            )
            ai_hantei = fallback_ai_hantei

        translations_raw = data.get("translations") or {}

        translations = {
            key: (
                str(translations_raw[key]).strip()
                if translations_raw.get(key)
                else None
            )
            for key in ["post", "quote", "post_article", "quote_article"]
        }

        idea_box_reason = str(data.get("idea_box_reason") or "").strip()

        idea_box_ai_hyoka = data.get("idea_box_ai_hyoka")

        if idea_box_ai_hyoka not in idea_box_ai_hyoka_options:
            idea_box_ai_hyoka = None

        idea_box_tags = data.get("idea_box_tags") or []

        if not isinstance(idea_box_tags, list):
            idea_box_tags = [idea_box_tags]

        idea_box_tags = [
            t for t in idea_box_tags
            if isinstance(t, str) and t in idea_box_tag_options
        ]

        idea_box_projects = data.get("idea_box_projects") or []

        if not isinstance(idea_box_projects, list):
            idea_box_projects = [idea_box_projects]

        idea_box_projects = [
            p for p in idea_box_projects
            if isinstance(p, str) and p in idea_box_project_options
        ]

        return {
            "title": title,
            "summary": summary,
            "language": language,
            "category": category,
            "idea_box_reason": idea_box_reason,
            "idea_box_ai_hyoka": idea_box_ai_hyoka,
            "idea_box_tags": idea_box_tags,
            "idea_box_projects": idea_box_projects,
            "ai_hantei": ai_hantei,
            "translations": translations,
        }

    except Exception as e:
        print(
            f"Gemini整理失敗: {e}"
        )

        # Gemini障害時でもNotion保存は継続
        return fallback


# =========================================================
# Notion block helpers
# =========================================================

def chunk_text(text, size=1900):
    """
    Notionのrich_text 1要素あたり2000文字制限に対応するため、
    長いテキストを安全な長さに分割する。

    Notion側の文字数カウントはUTF-16コードユニット単位。
    絵文字や装飾用Unicode文字（Mathematical Alphanumeric Symbolsなど）は
    サロゲートペアでUTF-16 2ユニットになるが、Pythonの文字数（コードポイント数）
    では1文字として数えられるため、Python文字数で単純に区切ると
    実際のUTF-16長が制限を超えることがある。そのためUTF-16換算の長さで区切る。
    """

    if not text:
        return [""]

    chunks = []
    current = []
    current_len = 0

    for ch in text:
        ch_len = 2 if ord(ch) > 0xFFFF else 1

        if current_len + ch_len > size and current:
            chunks.append("".join(current))
            current = []
            current_len = 0

        current.append(ch)
        current_len += ch_len

    if current:
        chunks.append("".join(current))

    return chunks


def rich_text_property(text):
    """
    Notionのrich_textプロパティ値を作る。
    2000文字（UTF-16基準）を超える場合はchunk_textで分割し、
    複数のrich_textオブジェクトとして返す（本文ブロックと同じ理由）。
    """

    if not text:
        return []

    return [
        {"text": {"content": chunk}}
        for chunk in chunk_text(text)
    ]


def paragraph_blocks(text):
    if not text:
        return []

    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": chunk}}
                ]
            },
        }
        for chunk in chunk_text(text)
    ]


def heading_block(text):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [
                {"type": "text", "text": {"content": text}}
            ]
        },
    }


def image_block(url):
    return {
        "object": "block",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": url},
        },
    }


def text_with_translation_blocks(original_text, translated_text):
    """
    翻訳があれば「🇯🇵 日本語訳」→「🌐 原文」の順で両方残す。
    翻訳が無ければ原文だけを返す（見た目を変えない）。
    """

    if translated_text:
        return (
            [heading_block("🇯🇵 日本語訳")]
            + paragraph_blocks(translated_text)
            + [heading_block("🌐 原文")]
            + paragraph_blocks(original_text)
        )

    return paragraph_blocks(original_text)


def extra_blocks_from_fx_post(fx_post, translations=None):
    """
    引用・Article・画像があれば、Notionページ末尾に追加する
    ブロック列を作る。何もなければ空リスト。

    translationsが渡されていれば、該当セクションに
    日本語訳を原文と併記する（無ければ原文のみ）。
    """

    translations = translations or {}

    blocks = []

    quote = fx_post.get("quote")

    if quote and quote.get("available"):
        quote_author = quote.get("author", {}).get("screen_name", "unknown")

        blocks.append(heading_block(f"🔁 引用: @{quote_author}"))
        blocks += text_with_translation_blocks(
            quote.get("text", ""),
            translations.get("quote"),
        )

        quote_article = quote.get("article")

        if quote_article:
            blocks.append(heading_block(
                f"📰 引用先Article: {quote_article.get('title', '')}"
            ))
            blocks += text_with_translation_blocks(
                quote_article.get("text", ""),
                translations.get("quote_article"),
            )

    article = fx_post.get("article")

    if article:
        blocks.append(heading_block(
            f"📰 Article: {article.get('title', '')}"
        ))
        blocks += text_with_translation_blocks(
            article.get("text", ""),
            translations.get("post_article"),
        )

    photos = [
        m for m in fx_post.get("media", [])
        if m.get("type") == "photo"
    ]

    if photos:
        blocks.append(heading_block("🖼 画像"))
        blocks += [image_block(p["url"]) for p in photos]

    return blocks


def build_gemini_input(tweet_text, fx_post):
    """
    Geminiへ渡すテキストを組み立てる。

    引用ツイートは、投稿者自身のコメント文だけでは
    内容がほぼ空のことが多いため、引用元の本文
    （Article含む）もここで合成しておく。
    そうしないと「AI整理メモ」が空同然になる。
    """

    parts = [tweet_text]

    if fx_post:
        quote = fx_post.get("quote")

        if quote and quote.get("available"):
            quote_text = quote.get("text", "")

            quote_article = quote.get("article")

            if quote_article and quote_article.get("text"):
                quote_text = (
                    quote_text + "\n\n" + quote_article["text"]
                ).strip()

            if quote_text:
                parts.append(f"[引用元投稿]\n{quote_text}")

        article = fx_post.get("article")

        if article and article.get("text"):
            parts.append(f"[Article本文]\n{article['text']}")

    return "\n\n".join(p for p in parts if p).strip()


# =========================================================
# Notion API
# =========================================================

def save_to_notion(
    tweet,
    username,
    category_options,
    language_options,
    ai_hantei_options=None,
    recent_titles=None,
    idea_box_tag_options=None,
    idea_box_project_options=None,
    idea_box_ai_hyoka_options=None,
):
    """
    Notionへページを作成する。

    ページ構成：

    AI生成タイトル
        ↓
    AI整理メモ
        ↓
    X Embed
        ↓
    原文（外国語なら日本語訳＋原文を併記）
        ↓
    （あれば）引用 / Article / 画像（それぞれ外国語なら日本語訳併記）

    recent_titlesが渡されていれば、保存したタイトルをその場でリストへ
    追記する（同一実行内で複数件処理する際も🔴重複判定に反映させるため）。

    AI査定が🟢 IDEA BOXへだった場合、INBOXへの保存に加えて
    「記録_IDEA from SNS」内のIDEA BOXデータベースへもコピーする
    （INBOX側はそのまま残す＝広く浅いCapture、IDEA BOXは狭く深いCurated）。
    """

    if recent_titles is None:
        recent_titles = []

    fallback_text = tweet.get("text", "").strip()
    fallback_url = f"https://x.com/{username}/status/{tweet['id']}"

    # X API公式のtextは280字超のnote_tweetを展開せず、
    # 引用ツイートの中身も取得できないため、
    # FxTwitter経由で完全な本文を取り直す。
    # 失敗時はX API公式のtextへフォールバックする。
    fx_post = fetch_fxtwitter_post(tweet["id"])

    if fx_post and fx_post.get("available") and fx_post.get("text"):
        tweet_text = fx_post["text"].strip()
        tweet_url = fx_post.get("url") or fallback_url
    else:
        tweet_text = fallback_text
        tweet_url = fallback_url
        fx_post = None

    if not tweet_text:
        # 本文が一切取得できなかった場合はGeminiを呼ばず、
        # 定型のタイトル・要約で「⚠️ 取得失敗」として保存する。
        title = FETCH_FAILED_TITLE
        summary = FETCH_FAILED_SUMMARY
        language = None
        category = ["未分類"] if "未分類" in category_options else []
        ai_hantei = AI_HANTEI_FETCH_FAILED if (
            ai_hantei_options is None or AI_HANTEI_FETCH_FAILED in ai_hantei_options
        ) else None
        idea_box_reason = ""
        idea_box_ai_hyoka = None
        idea_box_tags = []
        idea_box_projects = []
        translations = {
            "post": None, "quote": None, "post_article": None, "quote_article": None,
        }
    else:
        quote = (fx_post or {}).get("quote")
        has_quote = bool(quote and quote.get("available") and quote.get("text"))

        post_article = (fx_post or {}).get("article")
        has_post_article = bool(post_article and post_article.get("text"))

        quote_article = quote.get("article") if quote else None
        has_quote_article = bool(quote_article and quote_article.get("text"))

        # Geminiは1投稿につき1回だけ呼ぶ。
        # 引用元の本文があれば合成して渡す（空要約対策）。
        # LANGUAGE/CATEGORY/AI査定判定・各セクションの翻訳もこの1回に含める。
        gemini_input = build_gemini_input(tweet_text, fx_post)

        ai = generate_ai_content(
            gemini_input,
            category_options,
            language_options,
            ai_hantei_options=ai_hantei_options,
            recent_titles=recent_titles,
            idea_box_tag_options=idea_box_tag_options,
            idea_box_project_options=idea_box_project_options,
            idea_box_ai_hyoka_options=idea_box_ai_hyoka_options,
            has_quote=has_quote,
            has_post_article=has_post_article,
            has_quote_article=has_quote_article,
        )

        title = ai["title"]
        summary = ai["summary"]
        language = ai["language"]
        category = ai["category"]
        ai_hantei = ai["ai_hantei"]
        idea_box_reason = ai["idea_box_reason"]
        idea_box_ai_hyoka = ai["idea_box_ai_hyoka"]
        idea_box_tags = ai["idea_box_tags"]
        idea_box_projects = ai["idea_box_projects"]
        translations = ai["translations"]

    children = [
        # -------------------------------------------------
        # AI整理メモ
        # -------------------------------------------------
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "📝 AI整理メモ"
                        }
                    }
                ]
            }
        },

        *paragraph_blocks(summary),

        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },

        # -------------------------------------------------
        # X Embed
        # -------------------------------------------------
        {
            "object": "block",
            "type": "embed",
            "embed": {
                "url": tweet_url
            }
        },

    ]

    # -------------------------------------------------
    # 原文（外国語なら日本語訳を先に、原文も併記）
    # -------------------------------------------------
    if translations.get("post"):
        children.append(heading_block("🇯🇵 元投稿（日本語訳）"))
        children += paragraph_blocks(translations["post"])
        children.append(heading_block("🌐 原文"))
        children += paragraph_blocks(tweet_text)
    else:
        children.append(heading_block("原文"))
        children += paragraph_blocks(tweet_text)

    # -------------------------------------------------
    # 引用 / Article / 画像（あれば）
    # -------------------------------------------------
    if fx_post:
        children += extra_blocks_from_fx_post(fx_post, translations)

    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        },

        "URL": {
            "url": tweet_url
        },

        "既読": {
            "checkbox": False
        },

        "CATEGORY": {
            "multi_select": [{"name": c} for c in category]
        },
    }

    # languageがNotionの既存選択肢と一致しなかった場合は
    # プロパティ自体を送らない（誤った値を書き込まない）。
    if language:
        properties["LANGUAGE"] = {"select": {"name": language}}

    if ai_hantei:
        properties["AI査定"] = {"select": {"name": ai_hantei}}

    payload = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": NOTION_DATA_SOURCE_ID,
        },

        "properties": properties,

        "children": children,
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=notion_headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    # 同一実行内でこの後処理する投稿の🔴重複判定にも反映されるよう、
    # 保存できたタイトルをその場で追記する。
    recent_titles.insert(0, title)

    if ai_hantei == AI_HANTEI_IDEA_BOX:
        author_name = (
            (fx_post or {}).get("author", {}).get("name")
            or (fx_post or {}).get("author", {}).get("screen_name")
            or username
        )

        try:
            save_to_idea_box(
                tweet_url,
                title,
                summary,
                idea_box_reason,
                idea_box_ai_hyoka,
                idea_box_tags,
                idea_box_projects,
                author_name,
                children,
            )
        except Exception as e:
            # INBOXへの保存は既に成功しているので、IDEA BOX側の失敗で
            # 全体を失敗扱いにはしない（ログだけ残す）。
            print(f"IDEA BOXへのコピー失敗: {e}")


def save_to_idea_box(
    tweet_url,
    title,
    summary,
    idea_box_reason,
    idea_box_ai_hyoka,
    idea_box_tags,
    idea_box_projects,
    author_name,
    children,
):
    """
    「記録_IDEA from SNS」内のIDEA BOXデータベースへ複製する。
    INBOX側はそのまま残す（広く浅いCapture）、IDEA BOXは狭く深いCurated、
    というユーザー自身の設計メモに沿った役割分担。

    本文（AI整理メモ・原文・引用/Article/画像）もINBOX側と同じ
    childrenブロック列をそのまま複製する（プロパティのみだと
    後から見返す際に内容が空同然になってしまうため）。
    """

    if not NOTION_IDEA_BOX_DATA_SOURCE_ID:
        print(
            "NOTION_IDEA_BOX_DATA_SOURCE_ID未設定のため、"
            "IDEA BOXへのコピーをスキップします"
        )
        return

    properties = {
        "Name": {
            "title": [{"text": {"content": title}}]
        },
        "URL": {
            "url": tweet_url
        },
        "一言要約": {
            "rich_text": rich_text_property(summary)
        },
        "ソース種別": {
            "select": {"name": "X"}
        },
        "ステータス": {
            "select": {"name": "未整理"}
        },
        "取得日": {
            "date": {"start": date.today().isoformat()}
        },
    }

    if author_name:
        properties["元投稿者・作者"] = {
            "rich_text": rich_text_property(author_name)
        }

    if idea_box_reason:
        properties["気になった理由・使い道"] = {
            "rich_text": rich_text_property(idea_box_reason)
        }

    if idea_box_ai_hyoka:
        properties["AI評価"] = {"select": {"name": idea_box_ai_hyoka}}

    if idea_box_tags:
        properties["タグ"] = {
            "multi_select": [{"name": t} for t in idea_box_tags]
        }

    if idea_box_projects:
        properties["関連プロジェクト"] = {
            "multi_select": [{"name": p} for p in idea_box_projects]
        }

    payload = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": NOTION_IDEA_BOX_DATA_SOURCE_ID,
        },

        "properties": properties,

        "children": children,
    }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=notion_headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    print(f"IDEA BOXへコピー完了: {title}")


# =========================================================
# Main
# =========================================================

def main():
    conn = init_db()

    try:
        # CATEGORY/LANGUAGEの選択肢はNotion側の現在の定義から取得する。
        # 手動で追加したCATEGORYも次回実行時にはここで拾われる。
        # 取得に失敗してもパイプライン全体は止めず、
        # デフォルト値（未分類のみ等）で継続する。
        try:
            schema = get_data_source_schema()

            category_options = get_select_option_names(
                schema, "CATEGORY", "multi_select"
            ) or DEFAULT_CATEGORY_OPTIONS

            language_options = get_select_option_names(
                schema, "LANGUAGE", "select"
            ) or DEFAULT_LANGUAGE_OPTIONS

            ai_hantei_options = get_select_option_names(
                schema, "AI査定", "select"
            ) or DEFAULT_AI_HANTEI_OPTIONS

        except Exception as e:
            print(f"Notionスキーマ取得失敗、デフォルト値で継続: {e}")

            category_options = DEFAULT_CATEGORY_OPTIONS
            language_options = DEFAULT_LANGUAGE_OPTIONS
            ai_hantei_options = DEFAULT_AI_HANTEI_OPTIONS

        # IDEA BOX（記録_IDEA from SNS内）の既存タグ・関連プロジェクト・AI評価の
        # 選択肢も同様に実行時取得する。NOTION_IDEA_BOX_DATA_SOURCE_ID未設定なら
        # IDEA BOXへのコピー機能自体をスキップする（INBOXへの保存は通常通り継続）。
        idea_box_tag_options = DEFAULT_IDEA_BOX_TAG_OPTIONS
        idea_box_project_options = DEFAULT_IDEA_BOX_PROJECT_OPTIONS
        idea_box_ai_hyoka_options = DEFAULT_IDEA_BOX_AI_HYOKA_OPTIONS

        if NOTION_IDEA_BOX_DATA_SOURCE_ID:
            try:
                idea_box_schema = get_data_source_schema(NOTION_IDEA_BOX_DATA_SOURCE_ID)

                idea_box_tag_options = get_select_option_names(
                    idea_box_schema, "タグ", "multi_select"
                ) or DEFAULT_IDEA_BOX_TAG_OPTIONS

                idea_box_project_options = get_select_option_names(
                    idea_box_schema, "関連プロジェクト", "multi_select"
                ) or DEFAULT_IDEA_BOX_PROJECT_OPTIONS

                idea_box_ai_hyoka_options = get_select_option_names(
                    idea_box_schema, "AI評価", "select"
                ) or DEFAULT_IDEA_BOX_AI_HYOKA_OPTIONS

            except Exception as e:
                print(f"IDEA BOXスキーマ取得失敗、デフォルト値で継続: {e}")

        # 🔴重複判定用に直近のINBOXタイトルを取得しておく。
        # 同一実行内で新たに保存したタイトルは save_to_notion() が
        # このリストへ追記していく。
        recent_titles = get_recent_inbox_titles(limit=30)

        user_id = get_my_user_id()

        data = get_liked_posts(
            user_id
        )

        users = {
            user["id"]: user
            for user in data.get(
                "includes",
                {}
            ).get(
                "users",
                []
            )
        }

        tweets = data.get(
            "data",
            []
        )

        # 古いLike → 新しいLikeの順番で保存
        for tweet in reversed(tweets):
            tweet_id = tweet["id"]

            # 保存済みならスキップ
            if already_processed(
                conn,
                tweet_id
            ):
                continue

            author = users.get(
                tweet.get("author_id"),
                {}
            )

            username = author.get(
                "username",
                "unknown"
            )

            try:
                save_to_notion(
                    tweet,
                    username,
                    category_options,
                    language_options,
                    ai_hantei_options=ai_hantei_options,
                    recent_titles=recent_titles,
                    idea_box_tag_options=idea_box_tag_options,
                    idea_box_project_options=idea_box_project_options,
                    idea_box_ai_hyoka_options=idea_box_ai_hyoka_options,
                )

                # Notion保存成功後だけ処理済みにする
                mark_processed(
                    conn,
                    tweet_id
                )

                print(
                    f"保存成功: {tweet_id} @{username}"
                )

            except Exception as e:
                print(
                    f"保存失敗: {tweet_id} @{username} {e}"
                )

    finally:
        conn.close()


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    main()
