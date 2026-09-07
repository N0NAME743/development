import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.code_image import (
    code_to_image,
    extract_code_block,
    first_code_image,
    split_text_and_media,
)


def test_extract_code_block_returns_none_without_fence():
    text = "ただの投稿文だよ"
    remaining, block = extract_code_block(text)

    assert remaining == text
    assert block is None


def test_extract_code_block_ignores_single_line_code():
    text = "コマンドはこれ: ```pip install foo```"
    remaining, block = extract_code_block(text)

    assert block is None
    assert remaining == text


def test_extract_code_block_extracts_multiline_code():
    text = "見つけた！\n```python\ndef hi():\n    print('hi')\n```\nすごくない？"
    remaining, block = extract_code_block(text)

    assert block == {"language": "python", "code": "def hi():\n    print('hi')"}
    assert "```" not in remaining
    assert "見つけた" in remaining
    assert "すごくない" in remaining


def test_extract_code_block_defaults_language_when_omitted():
    text = "```\nline1\nline2\n```"
    _, block = extract_code_block(text)

    assert block["language"] == "text"


def test_split_text_and_media_wraps_code_block_as_media_item():
    text = "```js\nconst a = 1;\nconsole.log(a);\n```"
    remaining, media = split_text_and_media(text)

    assert media == [
        {"type": "code_image", "language": "js", "code": "const a = 1;\nconsole.log(a);"}
    ]
    assert remaining == ""


def test_split_text_and_media_no_code_returns_empty_media_list():
    remaining, media = split_text_and_media("普通の投稿")

    assert remaining == "普通の投稿"
    assert media == []


def test_first_code_image_finds_code_type_entry():
    media = [{"type": "code_image", "language": "python", "code": "x = 1"}]

    assert first_code_image(media) == media[0]


def test_first_code_image_returns_none_when_absent():
    assert first_code_image([]) is None
    assert first_code_image([{"type": "other"}]) is None


def test_code_to_image_produces_valid_png_bytes():
    data = code_to_image("print('hi')\nprint('there')", language="python")

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 100


def test_code_to_image_falls_back_to_plain_text_for_unknown_language():
    data = code_to_image("some\nrandom\ntext", language="not-a-real-lexer")

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
