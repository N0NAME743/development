#!/usr/bin/env bash
# Claude Code セッションダッシュボード(ccdash)のエイリアスを ~/.bashrc に登録する。
# devcontainerの再構築(postCreateCommand)でも再実行されるように、冪等になっている。
set -euo pipefail

REPO_ROOT="/workspaces/development/claude_skill_lab"
ALIAS_LINE="alias ccdash=\"node ${REPO_ROOT}/tools/session-dashboard.js\""
BASHRC="$HOME/.bashrc"

if [ -f "$BASHRC" ] && grep -qxF "$ALIAS_LINE" "$BASHRC"; then
  echo "ccdash alias はすでに $BASHRC に設定済みです"
else
  {
    echo ""
    echo "# Claude Code セッションダッシュボード"
    echo "$ALIAS_LINE"
  } >> "$BASHRC"
  echo "ccdash alias を $BASHRC に追加しました"
fi
