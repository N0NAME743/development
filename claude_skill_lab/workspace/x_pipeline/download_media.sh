#!/usr/bin/env bash
# Phase 2: download photo media from an X post (via fetch_x_post.sh's normalized JSON)
# so it can be analyzed (e.g. read by Claude). Video handling is Phase 3.
#
# Usage: ./download_media.sh "<X post URL>" [output_dir]
# Prints a JSON array of downloaded file paths (photos only) to stdout.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
err() { echo "Error: $*" >&2; exit 1; }

[[ $# -ge 1 ]] || err "usage: $0 <X post URL> [output_dir]"
url="$1"
outdir="${2:-$SCRIPT_DIR/downloads}"

post_json=$("$SCRIPT_DIR/fetch_x_post.sh" "$url")
status_id=$(jq -r '.id' <<<"$post_json")
target_dir="$outdir/$status_id"
mkdir -p "$target_dir"

photo_urls=$(jq -r '.media[] | select(.type == "photo") | .url' <<<"$post_json")

if [[ -z "$photo_urls" ]]; then
  echo "[]"
  exit 0
fi

paths=()
i=0
while IFS= read -r photo_url; do
  [[ -z "$photo_url" ]] && continue
  i=$((i + 1))
  ext="${photo_url##*.}"
  ext="${ext%%\?*}"
  [[ "$ext" =~ ^[A-Za-z0-9]{2,4}$ ]] || ext="jpg"
  dest="$target_dir/photo_${i}.${ext}"
  curl -sS -m 30 -o "$dest" "$photo_url" || err "failed to download $photo_url"
  paths+=("$dest")
done <<<"$photo_urls"

printf '%s\n' "${paths[@]}" | jq -R . | jq -s .
