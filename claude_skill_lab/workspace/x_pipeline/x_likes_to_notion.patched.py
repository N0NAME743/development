import os
import json
import sqlite3
import requests

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

def get_data_source_schema():
    response = requests.get(
        f"https://api.notion.com/v1/data_sources/{NOTION_DATA_SOURCE_ID}",
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


# =========================================================
# Gemini
# =========================================================

def generate_ai_content(
    tweet_text,
    category_options,
    language_options,
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

    呼び出し回数は投稿1件につき1回のまま増やさない
    （翻訳対象が増えてもAPIリクエスト数は変わらない）。

    Geminiに失敗した場合は、元投稿ベースのフォールバック値を返す。
    """

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

        translations_raw = data.get("translations") or {}

        translations = {
            key: (
                str(translations_raw[key]).strip()
                if translations_raw.get(key)
                else None
            )
            for key in ["post", "quote", "post_article", "quote_article"]
        }

        return {
            "title": title,
            "summary": summary,
            "language": language,
            "category": category,
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
    """

    if not text:
        return [""]

    return [
        text[i:i + size]
        for i in range(0, len(text), size)
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

def save_to_notion(tweet, username, category_options, language_options):
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
    """

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

    quote = (fx_post or {}).get("quote")
    has_quote = bool(quote and quote.get("available") and quote.get("text"))

    post_article = (fx_post or {}).get("article")
    has_post_article = bool(post_article and post_article.get("text"))

    quote_article = quote.get("article") if quote else None
    has_quote_article = bool(quote_article and quote_article.get("text"))

    # Geminiは1投稿につき1回だけ呼ぶ。
    # 引用元の本文があれば合成して渡す（空要約対策）。
    # LANGUAGE/CATEGORY判定・各セクションの翻訳もこの1回に含める。
    gemini_input = build_gemini_input(tweet_text, fx_post)

    ai = generate_ai_content(
        gemini_input,
        category_options,
        language_options,
        has_quote=has_quote,
        has_post_article=has_post_article,
        has_quote_article=has_quote_article,
    )

    title = ai["title"]
    summary = ai["summary"]
    language = ai["language"]
    category = ai["category"]
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

        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": summary
                        }
                    }
                ]
            }
        },

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

        except Exception as e:
            print(f"Notionスキーマ取得失敗、デフォルト値で継続: {e}")

            category_options = DEFAULT_CATEGORY_OPTIONS
            language_options = DEFAULT_LANGUAGE_OPTIONS

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
