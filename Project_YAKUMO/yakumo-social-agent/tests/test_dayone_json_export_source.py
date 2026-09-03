import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.source.dayone_json_export_source import JSONExportSource

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def test_reads_entries_and_skips_empty_text():
    source = JSONExportSource(FIXTURES_DIR)
    entries = source.fetch_new_entries()

    ids = [e.entry_id for e in entries]

    assert "FIXTURE0001" in ids
    assert "FIXTURE0002" not in ids  # 本文が空のエントリーは除外される

    entry = next(e for e in entries if e.entry_id == "FIXTURE0001")
    assert "AI" in entry.text
    assert entry.created_at == "2026-09-04T09:15:00Z"
