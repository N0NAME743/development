"""Xの文字数制約。2026年時点の仕様（無料アカウント基準）。

元投稿へのリンクは付与しない（X APIが2026年2月以降、リンク付き投稿を
大幅に高く従量課金するようになったため。docs/credentials.md 3章参照）。
そのため本文はXの投稿上限をそのまま使える。
"""

X_POST_MAX_CHARS = 280

REACTION_TEXT_BUDGET = X_POST_MAX_CHARS
