#!/usr/bin/env python3
"""business.json + template/index.html.j2 から dist/index.html を生成する。

デモサイトは素の静的HTML/CSS/JSとして配信する（フレームワーク不要）。
電話番号・住所などは複数箇所に登場するため、business.jsonを唯一の
情報源とし、手打ちによる表記ゆれ・typoを防ぐためだけにこのビルド
ステップを設けている。ビルド時にのみJinja2を使用し、生成物（dist/）
自体はプレーンなHTML/CSS/JSでランタイム依存を持たない。

使い方:
    pip install -r requirements.txt
    python3 build.py
"""

import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "template"
SRC_DIR = BASE_DIR / "src"
DIST_DIR = BASE_DIR / "dist"
BUSINESS_JSON = BASE_DIR / "business.json"


def main() -> None:
    business = json.loads(BUSINESS_JSON.read_text(encoding="utf-8"))

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("index.html.j2")
    html = template.render(business=business)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")

    shutil.copytree(SRC_DIR / "css", DIST_DIR / "css")
    shutil.copytree(SRC_DIR / "js", DIST_DIR / "js")

    print(f"ビルド完了: {DIST_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
