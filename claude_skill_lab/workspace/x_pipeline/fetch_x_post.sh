#!/usr/bin/env bash
# Phase 1 MVP: X URL -> Status ID -> FxTwitter API -> normalized JSON
# (本文・作者・引用・Article・メディアURL一覧を返す。画像解析・動画処理はPhase2/3で追加)
#
# Usage: ./fetch_x_post.sh "<X post URL>"

set -euo pipefail

API_BASE="https://api.fxtwitter.com/status"

err() { echo "Error: $*" >&2; exit 1; }

[[ $# -eq 1 ]] || err "usage: $0 <X post URL>"
url="$1"

# Status ID extraction: works for twitter.com / x.com / mobile.twitter.com / m.twitter.com,
# and already-fixed fxtwitter.com/vxtwitter.com links.
if [[ "$url" =~ /status(es)?/([0-9]+) ]]; then
  status_id="${BASH_REMATCH[2]}"
else
  err "could not extract a status ID from: $url"
fi

response=$(curl -sS -m 15 -w '\n%{http_code}' "${API_BASE}/${status_id}") || err "network request to FxTwitter API failed"
http_code=$(tail -n1 <<<"$response")
body=$(sed '$d' <<<"$response")

jq -e . >/dev/null 2>&1 <<<"$body" || err "FxTwitter API did not return JSON (HTTP ${http_code}); status ID '${status_id}' may be malformed"
[[ "$http_code" == "200" ]] || err "FxTwitter API returned HTTP ${http_code}: $(jq -r '.message // .' <<<"$body")"

api_code=$(jq -r '.code' <<<"$body")
[[ "$api_code" == "200" ]] || err "FxTwitter API error (code ${api_code}): $(jq -r '.message' <<<"$body")"

jq '
def normalize_status:
  if .type == "tombstone" then
    {
      available: false,
      reason: .reason,
      message: .message
    }
  else
    {
      available: true,
      id: .id,
      url: .url,
      author: {
        name: .author.name,
        screen_name: .author.screen_name,
        url: ("https://x.com/" + .author.screen_name)
      },
      created_at: .created_at,
      lang: .lang,
      text: .text,
      quote: (if .quote then (.quote | normalize_status) else null end),
      article: (
        if .article then {
          title: .article.title,
          preview_text: .article.preview_text,
          text: ([.article.content.blocks[]?.text] | join("\n\n"))
        } else null end
      ),
      media: [ (.media.all // [])[] | {type: .type, url: .url, width: .width, height: .height} ]
    }
  end;

.tweet | normalize_status
' <<<"$body"
