"""Xの文字数制約。2026年時点の仕様（無料アカウント基準）。

URLは実際の長さに関わらずt.coにより固定23文字としてカウントされる。
YAKUMOの投稿は「本文 + 改行 + リンク」の構成にするため、
本文はこのモジュールの REACTION_TEXT_BUDGET 以内に収める。

Xの現在の仕様が変わった場合（無料枠の上限変更、リンク処理の変更等）は
ここだけを直せばよい。
"""

X_POST_MAX_CHARS = 280
X_LINK_CHARS = 23  # t.coによる固定長
LINK_SEPARATOR_CHARS = 1  # 本文とリンクの間の改行1文字

REACTION_TEXT_BUDGET = X_POST_MAX_CHARS - X_LINK_CHARS - LINK_SEPARATOR_CHARS  # 256


def fits_with_link(reaction_text: str) -> bool:
    return len(reaction_text) <= REACTION_TEXT_BUDGET


def fits_full_post(full_text_without_link_shortening: str, has_link: bool) -> bool:
    """リンクをt.co換算した上での投稿全体の文字数チェック。"""

    if not has_link:
        return len(full_text_without_link_shortening) <= X_POST_MAX_CHARS

    # full_text_without_link_shortening は "本文\n実URL" の形。
    # 実URLをt.co換算の23文字とみなして再計算する。
    lines = full_text_without_link_shortening.rsplit("\n", 1)
    reaction_text = lines[0] if len(lines) == 2 else full_text_without_link_shortening

    return fits_with_link(reaction_text)
