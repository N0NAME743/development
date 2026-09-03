"""config/ と ../_text-official/ からプロンプト素材を実行時に読み込む。

Character Bible / X Prompt はここで複製せず、常に本家ファイルを直接読む
（config/yakumo_profile.md, config/yakumo_writing_rules.md 参照）。
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # yakumo-social-agent/
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
PROMPTS_DIR = os.path.join(CONFIG_DIR, "prompts")

# Project_YAKUMO/_text-official/ への相対パス（yakumo-social-agent/ の一つ上）
YAKUMO_ROOT = os.path.dirname(PROJECT_ROOT)
OFFICIAL_DIR = os.path.join(YAKUMO_ROOT, "_text-official")

CHARACTER_BIBLE_PATH = os.path.join(
    OFFICIAL_DIR, "01_1_YAKUMO_Character_Bible_v1.2.md"
)
X_PROMPT_PATH = os.path.join(OFFICIAL_DIR, "02_1_YAKUMO_X_Prompt_v1.4.md")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_character_bible() -> str:
    return _read(CHARACTER_BIBLE_PATH)


def load_x_prompt() -> str:
    return _read(X_PROMPT_PATH)


def load_content_policy() -> str:
    return _read(os.path.join(CONFIG_DIR, "content_policy.md"))


def load_prompt_template(name: str) -> str:
    """name: 'select_content' | 'transform_to_yakumo' | 'final_review'"""

    return _read(os.path.join(PROMPTS_DIR, f"{name}.md"))


def render(template: str, **values: str) -> str:
    """{{KEY}} プレースホルダーを置換する。素朴な実装で十分（テンプレートエンジン不要）。"""

    rendered = template

    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)

    return rendered
