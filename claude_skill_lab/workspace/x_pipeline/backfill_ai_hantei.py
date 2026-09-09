"""
記録_Research INBOXの既存ページのうち、AI査定が未設定のものへ
自動判定（🟢 IDEA BOXへ / ⚪ 保留 / 🔴 重複 / ⚠️ 取得失敗）を
後追いで適用する一回限りのバックフィルスクリプト。

x_likes_to_notion.py（本番パイプライン）の判定ロジックをそのまま
再利用する。新規いいねが入ってくるたびに動く自動化は既にあるが、
それが追加される前から溜まっていた過去のページはAI査定が空のまま
になっているため、それだけを狙って埋める。

書き込むのはAI査定プロパティのみ。LANGUAGE/CATEGORYは
過去に手動で設定されている可能性があるため、このスクリプトでは
一切上書きしない（スコープを最小限に保つ）。

使い方:
    python3 backfill_ai_hantei.py             # dry-run（Notionには何も書き込まない）
    python3 backfill_ai_hantei.py --limit 10   # 最初の10件だけdry-run
    python3 backfill_ai_hantei.py --apply       # 実際に書き込む
    python3 backfill_ai_hantei.py --apply --limit 10  # 実際に10件だけ書き込む

Gemini無料枠のRPD/RPM制限があるため、まず --limit を小さくして
1回試し、問題なければ --limit を外して全件流すこと。
"""

import argparse
import importlib.util
import os
import re
import sys
import time

import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 本番(Pi)では x_likes_to_notion.py という名前でデプロイされている
# 前提（memory参照）。この開発リポジトリ内ではファイル名が
# x_likes_to_notion.patched.py のままなので、通常importが
# 失敗した場合はファイルパス指定で読み込む。
try:
    import x_likes_to_notion as pipeline
except ImportError:
    spec = importlib.util.spec_from_file_location(
        "x_likes_to_notion",
        os.path.join(BASE_DIR, "x_likes_to_notion.patched.py"),
    )
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)


STATUS_ID_RE = re.compile(r"/status(?:es)?/(\d+)")


def extract_tweet_id(url):
    if not url:
        return None

    m = STATUS_ID_RE.search(url)

    return m.group(1) if m else None


def get_untagged_inbox_pages(page_size=100):
    """
    AI査定プロパティが空のINBOXページを全件取得する（ページネーション対応）。
    """

    pages = []
    cursor = None

    while True:
        body = {
            "filter": {
                "property": "AI査定",
                "select": {"is_empty": True},
            },
            "page_size": page_size,
        }

        if cursor:
            body["start_cursor"] = cursor

        response = requests.post(
            f"https://api.notion.com/v1/data_sources/{pipeline.NOTION_DATA_SOURCE_ID}/query",
            headers=pipeline.notion_headers,
            json=body,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        pages.extend(data.get("results", []))

        if not data.get("has_more"):
            break

        cursor = data.get("next_cursor")

    return pages


def get_page_title(page):
    title_rt = page.get("properties", {}).get("Name", {}).get("title", [])

    if title_rt:
        return title_rt[0].get("plain_text", "")

    return ""


def get_page_url(page):
    return page.get("properties", {}).get("URL", {}).get("url")


def build_idea_box_children(tweet_text, tweet_url, summary, translations, fx_post):
    """
    IDEA BOXへ複製する際の本文ブロックを組み立てる。

    既存INBOXページの実際のブロック列を再取得する代わりに、
    x_likes_to_notion.pyの save_to_notion() と同じ組み立て方で
    再構成する（内容は同一になるはず。原文はFxTwitterから
    取り直したもの、翻訳はこのバックフィル実行時のGemini出力）。
    """

    children = [
        pipeline.heading_block("📝 AI整理メモ"),
        *pipeline.paragraph_blocks(summary),
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "embed",
            "embed": {"url": tweet_url},
        },
    ]

    if translations.get("post"):
        children.append(pipeline.heading_block("🇯🇵 元投稿（日本語訳）"))
        children += pipeline.paragraph_blocks(translations["post"])
        children.append(pipeline.heading_block("🌐 原文"))
        children += pipeline.paragraph_blocks(tweet_text)
    else:
        children.append(pipeline.heading_block("原文"))
        children += pipeline.paragraph_blocks(tweet_text)

    if fx_post:
        children += pipeline.extra_blocks_from_fx_post(fx_post, translations)

    return children


def update_ai_hantei(page_id, ai_hantei):
    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=pipeline.notion_headers,
        json={
            "properties": {
                "AI査定": {"select": {"name": ai_hantei}},
            }
        },
        timeout=30,
    )

    response.raise_for_status()


def process_page(
    page,
    ai_hantei_options,
    idea_box_tag_options,
    idea_box_project_options,
    idea_box_ai_hyoka_options,
    dry_run,
):
    page_id = page["id"]
    title = get_page_title(page) or "(無題)"
    url = get_page_url(page)

    tweet_id = extract_tweet_id(url)

    if not tweet_id:
        print(f"[スキップ] URLからTweet IDを取得できません: {title!r} url={url!r}")
        return

    fx_post = pipeline.fetch_fxtwitter_post(tweet_id)

    if not fx_post or not fx_post.get("available") or not fx_post.get("text"):
        ai_hantei = pipeline.AI_HANTEI_FETCH_FAILED

        print(f"[判定] {title!r} -> {ai_hantei}（本文取得失敗）")

        if not dry_run:
            update_ai_hantei(page_id, ai_hantei)

        return

    tweet_text = fx_post["text"].strip()

    quote = fx_post.get("quote")
    has_quote = bool(quote and quote.get("available") and quote.get("text"))

    post_article = fx_post.get("article")
    has_post_article = bool(post_article and post_article.get("text"))

    quote_article = quote.get("article") if quote else None
    has_quote_article = bool(quote_article and quote_article.get("text"))

    gemini_input = pipeline.build_gemini_input(tweet_text, fx_post)

    ai = pipeline.generate_ai_content(
        gemini_input,
        category_options=[],
        language_options=[],
        ai_hantei_options=ai_hantei_options,
        recent_titles=[],
        idea_box_tag_options=idea_box_tag_options,
        idea_box_project_options=idea_box_project_options,
        idea_box_ai_hyoka_options=idea_box_ai_hyoka_options,
        has_quote=has_quote,
        has_post_article=has_post_article,
        has_quote_article=has_quote_article,
    )

    ai_hantei = ai["ai_hantei"]

    print(f"[判定] {title!r} -> {ai_hantei}")

    if dry_run:
        return

    update_ai_hantei(page_id, ai_hantei)

    if ai_hantei == pipeline.AI_HANTEI_IDEA_BOX:
        tweet_url = fx_post.get("url") or url

        author_name = (
            fx_post.get("author", {}).get("name")
            or fx_post.get("author", {}).get("screen_name")
        )

        children = build_idea_box_children(
            tweet_text, tweet_url, ai["summary"], ai["translations"], fx_post
        )

        try:
            pipeline.save_to_idea_box(
                tweet_url,
                title,
                ai["summary"],
                ai["idea_box_reason"],
                ai["idea_box_ai_hyoka"],
                ai["idea_box_tags"],
                ai["idea_box_projects"],
                author_name,
                children,
            )
        except Exception as e:
            print(f"[警告] IDEA BOXへのコピー失敗: {title!r} {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="実際にNotionへ書き込む（指定しなければdry-run）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="処理するページ数の上限（Gemini無料枠のRPD/RPM対策）",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=4.5,
        help="各ページ処理後のスリープ秒数（Gemini無料枠 約15RPM対策、デフォルト4.5秒）",
    )
    args = parser.parse_args()

    dry_run = not args.apply

    if dry_run:
        print("=== dry-run モード（--apply を付けない限りNotionへは書き込みません） ===")

    try:
        schema = pipeline.get_data_source_schema()

        ai_hantei_options = pipeline.get_select_option_names(
            schema, "AI査定", "select"
        ) or pipeline.DEFAULT_AI_HANTEI_OPTIONS

    except Exception as e:
        print(f"Notionスキーマ取得失敗、デフォルト値で継続: {e}")

        ai_hantei_options = pipeline.DEFAULT_AI_HANTEI_OPTIONS

    idea_box_tag_options = pipeline.DEFAULT_IDEA_BOX_TAG_OPTIONS
    idea_box_project_options = pipeline.DEFAULT_IDEA_BOX_PROJECT_OPTIONS
    idea_box_ai_hyoka_options = pipeline.DEFAULT_IDEA_BOX_AI_HYOKA_OPTIONS

    if pipeline.NOTION_IDEA_BOX_DATA_SOURCE_ID:
        try:
            idea_box_schema = pipeline.get_data_source_schema(
                pipeline.NOTION_IDEA_BOX_DATA_SOURCE_ID
            )

            idea_box_tag_options = pipeline.get_select_option_names(
                idea_box_schema, "タグ", "multi_select"
            ) or idea_box_tag_options

            idea_box_project_options = pipeline.get_select_option_names(
                idea_box_schema, "関連プロジェクト", "multi_select"
            ) or idea_box_project_options

            idea_box_ai_hyoka_options = pipeline.get_select_option_names(
                idea_box_schema, "AI評価", "select"
            ) or idea_box_ai_hyoka_options

        except Exception as e:
            print(f"IDEA BOXスキーマ取得失敗、デフォルト値で継続: {e}")

    pages = get_untagged_inbox_pages()

    print(f"対象ページ数: {len(pages)}件（AI査定が未設定）")

    if args.limit is not None:
        pages = pages[: args.limit]
        print(f"--limit指定により、先頭{len(pages)}件のみ処理します")

    for i, page in enumerate(pages, start=1):
        print(f"--- [{i}/{len(pages)}] ---")

        try:
            process_page(
                page,
                ai_hantei_options,
                idea_box_tag_options,
                idea_box_project_options,
                idea_box_ai_hyoka_options,
                dry_run,
            )
        except Exception as e:
            print(f"[エラー] ページ処理失敗: {page.get('id')} {e}")

        if i < len(pages):
            time.sleep(args.sleep)

    print("完了")


if __name__ == "__main__":
    main()
