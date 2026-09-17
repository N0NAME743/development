#!/usr/bin/env bash
# devcontainer再構築のたびにSSH鍵(~/.ssh)が消えてGitHub認証をやり直す問題への対応。
# ワークスペース(ホストにバインドマウントされ、再構築後も残る)にSSH鍵を退避しておき、
# コンテナ起動のたびに ~/.ssh へ復元する。postCreateCommandから再実行されても冪等。
set -euo pipefail

REPO_ROOT="/workspaces/development/claude_skill_lab"
PERSIST_DIR="${REPO_ROOT}/.devcontainer/ssh-persist"
SSH_DIR="$HOME/.ssh"

mkdir -p "$PERSIST_DIR"
mkdir -p "$SSH_DIR" && chmod 700 "$SSH_DIR"

if [ -f "$PERSIST_DIR/id_ed25519" ]; then
  cp "$PERSIST_DIR/id_ed25519" "$SSH_DIR/id_ed25519"
  cp "$PERSIST_DIR/id_ed25519.pub" "$SSH_DIR/id_ed25519.pub"
  chmod 600 "$SSH_DIR/id_ed25519"
  chmod 644 "$SSH_DIR/id_ed25519.pub"
  echo "SSH鍵を永続ストレージ($PERSIST_DIR)から復元しました"
elif [ -f "$SSH_DIR/id_ed25519" ]; then
  cp "$SSH_DIR/id_ed25519" "$PERSIST_DIR/id_ed25519"
  cp "$SSH_DIR/id_ed25519.pub" "$PERSIST_DIR/id_ed25519.pub"
  chmod 600 "$PERSIST_DIR/id_ed25519"
  echo "SSH鍵を永続ストレージ($PERSIST_DIR)に保存しました。次回のdevcontainer再構築でも復元されます"
else
  echo "SSH鍵が見つかりません。ssh-keygen -t ed25519 -C \"<comment>\" -f $SSH_DIR/id_ed25519 で新規作成し、公開鍵をGitHubに登録してください"
fi

if [ -f "$SSH_DIR/id_ed25519" ] && ! ssh-keygen -F github.com -f "$SSH_DIR/known_hosts" >/dev/null 2>&1; then
  ssh-keyscan -t ed25519 github.com >> "$SSH_DIR/known_hosts" 2>/dev/null
  echo "github.com のホスト鍵を known_hosts に追加しました"
fi
