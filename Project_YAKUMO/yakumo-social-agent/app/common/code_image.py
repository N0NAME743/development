"""コード画像化（docs/architecture.md 11章 構想メモ「案2」）。

ツイート本文に複数行のコードをそのまま貼ると改行・インデントが崩れるため、
短い1行コマンドはテキストのまま、複数行のコード例だけをPNG画像に変換して
X投稿に添付する。外部の「綺麗なコード画像」サービス（carbon.now.sh等）には
依存しない方針（第三者サービスへの依存を避けたいというユーザーの意向）のため、
Pygments + Pillowでこのプロセス内だけで完結させる。

前提: 実行環境に fontconfig と DejaVu Sans Mono フォントが必要
（PygmentsのImageFormatterが内部で`fc-list`を呼びフォントパスを解決するため）。
Raspberry Pi等、未導入の環境では
`apt-get install fontconfig fonts-dejavu-core` が必要な場合がある。
"""

import re

from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

FONT_NAME = "DejaVu Sans Mono"
STYLE = "monokai"

# ```python\n...\n``` 形式のfenced code blockを検出する（言語名は省略可）。
_CODE_FENCE_RE = re.compile(r"```([\w+-]*)\n(.*?)```", re.DOTALL)

# これ未満の改行数（=実質1行）は画像化せずテキストのまま残す
# （architecture.md 11章: 短い1行コマンドはテキストのまま）。
_MIN_NEWLINES_TO_IMAGE = 2


def code_to_image(code: str, language: str = "text") -> bytes:
    """コード文字列をシンタックスハイライト付きPNG画像（バイト列）に変換する。

    未知の言語名が渡された場合はプレーンテキスト表示にフォールバックする
    （投稿全体を失敗させたくないため）。
    """

    try:
        lexer = get_lexer_by_name(language, stripnl=False)
    except ClassNotFound:
        lexer = TextLexer(stripnl=False)

    formatter = ImageFormatter(
        font_name=FONT_NAME,
        line_numbers=False,
        style=STYLE,
    )

    return highlight(code, lexer, formatter)


def extract_code_block(text: str) -> tuple[str, dict | None]:
    """テキスト中の最初の複数行fenced code blockを抜き出す。

    戻り値: (コードブロックを取り除いた残りのテキスト, 抽出した{"language", "code"} または None)
    見つからない、または1行しかない場合は (text, None) をそのまま返す。
    """

    match = _CODE_FENCE_RE.search(text)

    if match is None:
        return text, None

    code = match.group(2)

    if code.count("\n") < _MIN_NEWLINES_TO_IMAGE:
        return text, None

    language = match.group(1) or "text"
    remaining = (text[: match.start()] + text[match.end() :]).strip()

    return remaining, {"language": language, "code": code.rstrip("\n")}


def split_text_and_media(text: str) -> tuple[str, list[dict]]:
    """投稿本文からコードブロックを抜き出し、(本文, mediaリスト) を返す。

    見つかったコードブロックは `{"type": "code_image", "language", "code"}` として
    PostCandidate.media に格納できる形にする。見つからなければ media は空リスト。
    """

    remaining, code_block = extract_code_block(text)

    if code_block is None:
        return text, []

    return remaining, [{"type": "code_image", **code_block}]


def first_code_image(media: list[dict]) -> dict | None:
    """media一覧から最初の code_image エントリを返す（無ければNone）。"""

    for item in media:
        if item.get("type") == "code_image":
            return item

    return None
