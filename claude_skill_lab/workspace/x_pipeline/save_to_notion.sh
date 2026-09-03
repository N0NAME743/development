#!/usr/bin/env bash
# X post URL -> fetch_x_post.sh -> create a page in the Notion "Research INBOX" database.
# Property values are set to safe defaults (CATEGORY=未分類, AI査定=pending, LANGUAGE left
# unset — language auto-detection/translation is a later phase, not done here).
# The post's text/quote/article/media go into the page BODY (blocks), matching this
# database's actual schema (no rich-text property for post content).
#
# Usage: ./save_to_notion.sh "<X post URL>"
# Requires .env in this directory: NOTION_TOKEN=..., NOTION_DATABASE_ID=...

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

err() { echo "Error: $*" >&2; exit 1; }

[[ $# -eq 1 ]] || err "usage: $0 <X post URL>"
url="$1"

[[ -f "$ENV_FILE" ]] || err "$ENV_FILE not found (need NOTION_TOKEN and NOTION_DATABASE_ID)"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${NOTION_TOKEN:?NOTION_TOKEN not set in .env}"
: "${NOTION_DATABASE_ID:?NOTION_DATABASE_ID not set in .env}"

post_json=$("$SCRIPT_DIR/fetch_x_post.sh" "$url")

payload=$(jq -n --arg db "$NOTION_DATABASE_ID" --argjson post "$post_json" '
def chunk_text(s; n):
  if (s | length) <= n then [s]
  else [s[0:n]] + chunk_text(s[n:]; n)
  end;

def rich_text_blocks(s):
  if (s == null or s == "") then []
  else [ chunk_text(s; 1900)[] | {object:"block", type:"paragraph", paragraph:{rich_text:[{type:"text", text:{content:.}}]}} ]
  end;

def heading(s):
  {object:"block", type:"heading_2", heading_2:{rich_text:[{type:"text", text:{content:s}}]}};

def image_block(url):
  {object:"block", type:"image", image:{type:"external", external:{url:url}}};

def title_for(p):
  if (p.article != null) then (p.article.title // "(no title)")
  elif (p.text // "") != "" then ((p.author.screen_name // "unknown") + ": " + ((p.text // "")[0:70]))
  elif (p.quote != null and (p.quote.text // "") != "") then ("(quote) " + (p.quote.author.screen_name // "unknown") + ": " + ((p.quote.text // "")[0:60]))
  else ((p.author.screen_name // "unknown") + " の投稿")
  end;

{
  parent: {database_id: $db},
  properties: {
    "Name": {title: [{type:"text", text:{content: (title_for($post))[0:200]}}]},
    "URL": {url: $post.url},
    "CATEGORY": {multi_select: [{name:"未分類"}]},
    "AI査定": {select: {name:"⚪ 保留"}}
  },
  children: (
    (heading("本文")) as $h_body |
    (rich_text_blocks($post.text)) as $body |
    (
      if $post.quote != null then
        [heading("引用: @" + ($post.quote.author.screen_name // "unknown"))]
        + rich_text_blocks($post.quote.text)
        + (if $post.quote.article != null then
            [heading("引用先Article: " + ($post.quote.article.title // ""))]
            + rich_text_blocks($post.quote.article.text)
          else [] end)
      else [] end
    ) as $quote_blocks |
    (
      if $post.article != null then
        [heading("Article: " + ($post.article.title // ""))]
        + rich_text_blocks($post.article.text)
      else [] end
    ) as $article_blocks |
    (
      if ($post.media // []) | length > 0 then
        [heading("画像")] + [ $post.media[] | select(.type=="photo") | image_block(.url) ]
      else [] end
    ) as $media_blocks |
    [$h_body] + $body + $quote_blocks + $article_blocks + $media_blocks
    + [heading("元投稿"), {object:"block", type:"bookmark", bookmark:{url: $post.url}}]
  )
}
')

response=$(curl -sS -m 20 -w '\n%{http_code}' "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d "$payload")
http_code=$(tail -n1 <<<"$response")
body=$(sed '$d' <<<"$response")

if [[ "$http_code" != "200" ]]; then
  err "Notion API returned HTTP ${http_code}: $(jq -r '.message // .' <<<"$body" 2>/dev/null || echo "$body")"
fi

page_id=$(jq -r '.id' <<<"$body")
page_url=$(jq -r '.url' <<<"$body")
echo "Saved: $page_url"
jq -n --arg id "$page_id" --arg url "$page_url" '{page_id:$id, page_url:$url}'
