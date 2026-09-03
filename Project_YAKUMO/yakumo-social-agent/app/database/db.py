"""SQLiteでの状態管理・重複防止。指示書7章の必須項目 + state（8章）を保持する。

セキュリティ要件13章: ここでのログ出力に元投稿の要約全文を含めない
（source_textはDBには保存するが、print/loggingへは絶対に流さない）。
"""

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.common.state import PostState, validate_transition

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entry_id TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'NEW',
    source_text TEXT,
    source_url TEXT,
    ai_judgement_json TEXT,
    draft_text TEXT,
    review_json TEXT,
    revision_instruction TEXT,
    discord_message_id TEXT,
    approval_status TEXT,
    x_post_id TEXT,
    x_posted_at TEXT,
    processed_at TEXT,
    draft_generated_at TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def already_processed(self, source_entry_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM posts WHERE source_entry_id = ?", (source_entry_id,)
            ).fetchone()

        return row is not None

    def create_new(
        self, source_entry_id: str, source_text: str, source_url: str | None = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO posts (source_entry_id, content_hash, state, source_text, source_url, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_entry_id,
                    content_hash(source_text),
                    PostState.NEW.value,
                    source_text,
                    source_url,
                    _now(),
                ),
            )

    def get(self, source_entry_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM posts WHERE source_entry_id = ?", (source_entry_id,)
            ).fetchone()

    def transition(
        self,
        source_entry_id: str,
        next_state: PostState,
        **fields: str,
    ) -> None:
        row = self.get(source_entry_id)

        if row is None:
            raise ValueError(f"unknown source_entry_id: {source_entry_id}")

        current = PostState(row["state"])
        validate_transition(current, next_state)

        fields["state"] = next_state.value
        fields["updated_at"] = _now()

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [source_entry_id]

        with self._connect() as conn:
            conn.execute(
                f"UPDATE posts SET {set_clause} WHERE source_entry_id = ?", values
            )

    # --- 投稿ペース制御（app/pipeline/queue.py）用 ---

    def get_last_posted_at(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT x_posted_at FROM posts WHERE state = ? ORDER BY x_posted_at DESC LIMIT 1",
                (PostState.POSTED.value,),
            ).fetchone()

        return row["x_posted_at"] if row else None

    def get_next_approved(self) -> sqlite3.Row | None:
        """承認済みでまだ投稿されていないものを、承認が古い順（updated_at昇順）で1件返す。"""

        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM posts WHERE state = ? ORDER BY updated_at ASC LIMIT 1",
                (PostState.APPROVED.value,),
            ).fetchone()
