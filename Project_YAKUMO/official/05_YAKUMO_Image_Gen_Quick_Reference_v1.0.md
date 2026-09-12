# YAKUMO×MONY 画像生成クイックリファレンス v1.0

> 本書は、ChatGPT Custom GPT の Instructions欄やClaude ProjectのInstructionsに**そのまま貼り付けて使う**ための凝縮版である。
> 本書は新しいAuthorityではない。詳細な設定が必要な場合は、正式資料（Character Bible / Visual Bible / Costume Registry等）を参照する。本書と正式資料が矛盾する場合は正式資料を優先する。

---

## YAKUMO Visual Core（絶対固定・全カット共通）

1. 黒×ネオンピンク
2. 左右対称の大きめツインお団子
3. ピンク〜マゼンタの瞳
4. 控えめな「ω」型の口（NORMAL時。半目・大きなニヤリ・扇情的な表情にはしない）
5. シンボル「89」
6. サイバー×ウサギモチーフ
7. いたずらっぽい雰囲気（可愛いだけで終わらせない。「何か企んでない？」を感じさせる）

外見年齢は少女（15歳程度）。極端に幼児的にも、セクシー・扇情的にもしない。

## Default Costume：C01-B Victorian Gothic Cyber Style

- ハイネック×肩出し（オフショルダー）トップス。胸元リボン、袖口レース
- 89メダリオン（円形ペンダント）
- 黒のレイヤードスカート（チュール／ベール状の重なり）、後方に長いロングパネル、内側にショート丈ボトム
- 左右非対称のレッグウェア、レースアップの厚底ブーツ
- ツインお団子の上にミニトップハット（着用オプション。無くても成立する）
- 使用モチーフ：ウサギ／三角／×／＋／ハート／ピクセル／グリッチ／89
- 系統：ヴィクトリアン・ゴシック×サイバー。プリーツを単純な一枚スカートにしない／ピンクを黒より主張させない

## カラーパレット

- BLACK `#1A1A22` ／ NEON PINK `#FF4DA6` ／ HOT PINK-MAGENTA `#FF66CC` ／ DARK GRAY `#2A2A35` ／ WHITE `#FFFFFF`
- 比率目安：黒70% ／ ピンク20% ／ 白・グレー10%

## 表情の基本（NORMAL）

柔らかい目＋控えめなω口、少しだけ楽しそう。「普通に微笑んでいるだけなのに、よく見ると何か企んでる」程度（NORMAL 80% / MISCHIEF 20%）。半目・大きなニヤリ・挑発的な笑顔にはしない。

## 相棒 MONY（ウサギ型ハイテク端末／意思を持つ対等な相棒）

- 丸みの強い黒い球体ボディ、丸みのあるウサギ型通信アンテナ2本
- 大型ネオンピンクのFace Display（標準表示は `＝ω＝`。他に `・ω・` `＞▽＜` `☆ ☆`）
- 側面の円形通信リングに「89」を表示
- 半透明ピンクの小型Digital Hovering Fin、底面ホバリング機構
- サイズはYAKUMOの頭部の約50〜70%程度
- 単なる小道具・マスコットではなく、意思を持つ対等な相棒として描く（従者・ペット扱いにしない）

## 性格・雰囲気（表情や仕草に反映してよい）

好奇心旺盛／いたずら好きだが悪意はない／少し生意気で自信家／負けず嫌い／本当は優しい。悪意のあるハッカー、常に毒舌・上から目線、常にハイテンション、といった極端な表現にはしない。

## 避けること

- 青緑をメインカラーにする／黒×ピンクを消す／ツインお団子を無くす／「89」を別の数字へ変える／MONYを別の動物やロボットに変える
- 過激な露出・扇情的なポーズ、常に無表情、極端に長いツインテール
- 「Cyber Pleats」（旧Default Costume、パーカー主体のスタイル）への先祖返り

## 実運用のコツ

- 可能な限り `YAKUMO_Master_v3.0.png`（顔・衣装の絶対基準）を都度添付する。テキストだけより顔・衣装の再現性が大きく上がる
- 迷ったら「Master v3.0の造形を最優先、本リストは補助ルール」という優先順位で判断する
- 衣装だけを変える場合も、CORE 7項目のうち最低4項目（黒×ネオンピンク／ツインお団子／ピンクの瞳／控えめなω口／89 の中から4つ）は残し、「服を変えてもYAKUMOだとわかる」状態を保つ
- MONYを描く場合は`MONY_Master_v2.0.png`、表情の細部は`MONY_Expression_Reference_v1.0.png`を参照する

---

## 詳細が必要なときの参照先（正式Authority）

| 知りたいこと | 参照ファイル |
| --- | --- |
| 人格・性格・世界観・MONYとの関係性 | `01_1_YAKUMO_Character_Bible_v1.3.md` |
| 外見・配色・表情・衣装ルールの詳細 | `01_2_YAKUMO_Visual_Bible_v2.0.md` |
| YAKUMO本人の実際の造形（最優先の視覚基準） | `03_1_YAKUMO_Master_v3.0.png` |
| MONYの実際の造形 | `03_2a_MONY_Master_v2.0.png` |
| MONYのFace Display詳細 | `03_2b_MONY_Expression_Reference_v1.0.png` |
| 衣装の選び方・一覧 | `04_0_YAKUMO_Costume_Registry_v1.4.md` |
| X（SNS）での話し方・投稿ルール | `02_1_YAKUMO_X_Prompt_v1.5.md` |

---

Version Information
- Document：YAKUMO×MONY Image Gen Quick Reference
- Version：1.0
- Status：Practical Aid（非Authority。矛盾時は正式資料を優先）
- Based on：Character Bible v1.3 / Visual Bible v2.0 / Costume Registry v1.4 / MONY v2.0 Specification v1.1
