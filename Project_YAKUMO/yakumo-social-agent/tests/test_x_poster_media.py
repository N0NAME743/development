import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.models import PostCandidate
from app.x import poster as poster_module
from app.x.poster import XPoster


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def _set_x_env(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("X_CLIENT_ID", "cid")
    monkeypatch.setenv("X_CLIENT_SECRET", "secret")
    monkeypatch.setenv("X_ACCESS_TOKEN", "token")
    monkeypatch.setenv("X_REFRESH_TOKEN", "refresh")


def test_post_uploads_code_image_and_attaches_media_id(monkeypatch):
    _set_x_env(monkeypatch)

    calls = []

    def fake_post(url, headers=None, json=None, data=None, files=None, timeout=None):
        calls.append({"url": url, "json": json, "data": data, "files": files})

        if url.endswith("/media/upload"):
            return _FakeResponse({"data": {"id": "media-123"}})

        return _FakeResponse({"data": {"id": "tweet-999"}})

    monkeypatch.setattr(poster_module.requests, "post", fake_post)

    candidate = PostCandidate(
        source_entry_id="e1",
        content_hash="h",
        text="見て！",
        media=[{"type": "code_image", "language": "python", "code": "print(1)\nprint(2)"}],
    )

    tweet_id = XPoster().post(candidate)

    assert tweet_id == "tweet-999"
    assert len(calls) == 2
    assert calls[0]["url"].endswith("/media/upload")
    assert calls[0]["files"]["media"][2] == "image/png"
    assert calls[1]["url"] == "https://api.x.com/2/tweets"
    assert calls[1]["json"] == {
        "text": "見て！",
        "media": {"media_ids": ["media-123"]},
    }


def test_post_without_code_image_skips_media_upload(monkeypatch):
    _set_x_env(monkeypatch)

    calls = []

    def fake_post(url, headers=None, json=None, data=None, files=None, timeout=None):
        calls.append(url)
        return _FakeResponse({"data": {"id": "tweet-1"}})

    monkeypatch.setattr(poster_module.requests, "post", fake_post)

    candidate = PostCandidate(source_entry_id="e1", content_hash="h", text="普通の投稿")

    XPoster().post(candidate)

    assert calls == ["https://api.x.com/2/tweets"]
