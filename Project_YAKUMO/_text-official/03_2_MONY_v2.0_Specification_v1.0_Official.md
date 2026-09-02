---

# MONY v2.0 Specification v1.0 Official

## 0｜Document Status

本書は、YAKUMOの相棒「MONY / モニィ」のOfficialビジュアルおよび動作状態仕様を定義する。
MONY v2.0 Specification Draft v0.2 は正式採用され、本書をもってMONY v2.0の仕様をOfficialとする。
MONY v2.0は新しいキャラクターではない。
既存MONYの人格・役割・YAKUMOとの関係性・基本機能を継承した上で、ビジュアル設計および動作状態表現を再整理したものである。
MONYの実際の造形確認には、現行Official Visual Masterである`MONY_Master_v2.0.png`を使用する。
`MONY_Master_v1.0.png`はLegacy / Archived Referenceとして扱い、現行MONYの造形Authorityとして使用しない。
---

# 1｜MONY Identity

| 項目 | Official定義 |
| --- | --- |
| Name | **モニィ / MONY** |
| Version | **2.0** |
| Specification | **v1.0 Official** |
| Status | **OFFICIAL** |
| Type | **ウサギ型ハイテクデジタル端末** |
| Role | **YAKUMOの友達・相棒・共犯者** |
| Primary Colors | **BLACK × NEON PINK** |
| Symbol | **89** |
| Visual Concept | **Cute Cyber Companion Unit** |
| Adopted Design | **MONY v2.0 — C Revised** |
| Official Specification | **本書** |
| Visual Master | `MONY_Master_v2.0.png` |

MONYはYAKUMOと常に行動する、ウサギ型のハイテクデジタル端末である。
一見すると可愛らしい小型マスコットだが、内部には高度な演算・通信機能を持つ。
MONYはYAKUMOの命令だけを実行する従属端末ではなく、自身の意思を持つ対等な友達・相棒である。
YAKUMOを止める、からかう、勝負する、面白い情報を見つける、いたずらへ参加する、あるいは何もせずそばにいる、といった既存の関係性・人格設定はv2.0でも変更しない。
---

# 2｜Design Concept

MONY v2.0のデザインテーマは、

> **「普段はかわいい。必要な時だけ、高性能端末としての本質が見える。」**

とする。
通常状態では、マスコットとしての親しみやすさ、一目で認識できる単純なシルエット、表情の読み取りやすさを優先する。
高度な演算・通信能力を表現するために外装へ過剰なメカディテールを追加するのではなく、主要機構は内部へ収納する。
動作状態が変化した場合も別形態へ変身せず、

- ディスプレイ
- 発光
- 通信機構
- アンテナ
- ホバリング機構
- 周辺Digital Effect


によって機能状態を表現する。
---

# 3｜v1.0から継承する要素

MONY v2.0は既存MONYと同一個体である。
## 3.1｜Character / Role


- 名前はモニィ / MONY
- YAKUMOの相棒
- YAKUMOと対等な存在
- 自身の意思を持つ
- 相棒兼共犯者として行動する
- ウサギ型ハイテクデジタル端末
- 高度な演算・通信能力を持つ


これらはCharacter Bibleで定義されているMONYの根幹であり、v2.0でも変更しない。
## 3.2｜Visual Identity


- 黒主体
- ネオンピンクの発光アクセント
- 球体を基本とするボディ
- ウサギ耳×2
- ピンク系フェイスディスプレイ
- 側面通信ユニット
- 小型の翼／移動補助機構
- 小型サイズ
- 89
- ウサギ × デジタル


既存MONYのVisual Identityを継承し、v2.0ではこれらを新しい造形へ再整理する。
---

# 4｜v2.0 Visual Design

## 4.1｜Body

基本ボディを、
シンプルで丸みの強いマットブラック系球体

とする。
外装のパネルラインやメカディテールは最小限とし、NORMAL状態では内部の複雑さを外観へ過剰に露出させない。
## 4.2｜Rabbit Ear Antenna

既存の「ウサギ耳＝通信アンテナ」という機能設定を継承する。
v2.0では、

- v1.0よりコンパクト
- 太め
- 先端に丸みを持つ
- 内部にネオンピンクの通信ラインを持つ


造形とする。
ウサギ耳としての可愛さと、通信アンテナとしての機械的説得力を両立させる。
## 4.3｜Face Display

前面に大型のピンクLED系フェイスディスプレイを配置する。
MONYの第一印象ではメカディテールよりも顔を優先する。
フェイス表示は単なる情報表示ではなく、MONY自身の意思・感情を視覚的に伝える主要コミュニケーション手段とする。
## 4.4｜Side Communication Unit

側面には円形通信ユニットを配置する。
これは、
MONYの主要な通信・演算インターフェース

として扱う。
円形リングを基本形状とし、ネオンピンクの発光によって稼働状態を表現する。
主要な89表示位置は、この側面通信リングを基本とする。
89を外装全体へ無秩序に反復しない。
## 4.5｜Digital Hovering Fin

既存MONYの「小さな翼＝電脳空間での移動補助」という機能を継承する。
v2.0では単純な妖精型の翼ではなく、
半透明ピンクのDigital Hovering Fin

として再解釈する。
外形には小さな翼としての視覚的名残を維持する。
内部にはデジタル回路を思わせる構造・発光表現を持たせ、MONY固有の移動補助機構として成立させる。
大型の翼にはしない。
## 4.6｜Bottom Hovering System

MONYは通常、空中を小型浮遊端末として移動可能とする。
底面にはホバリング機構を内蔵し、稼働時には控えめなピンク系発光によって浮遊状態を視覚化する。
具体的な推進方式・エネルギー源・出力値等は未定義とする。
生成設定画内に記載された技術名称や数値をOfficial設定として扱わない。
## 4.7｜Internal Core

MONY内部には既存設定どおり高度な演算・通信機構が存在する。
v2.0では、この高性能機構が球体外装内部へ収納されているという設計を採用する。
ただし、

- CPU構成
- 記憶容量
- 動力方式
- Core名称
- 演算性能
- 通信速度


等の具体的スペックは未定義とする。
設定画に偶発的に生成された内部名称・スペックはOfficial設定ではない。
---

# 5｜Visual Core

MONY v2.0をMONYとして認識させるため、以下をOfficial Visual Coreとする。

1. 丸みの強い黒い球体ボディ
2. 丸みを持つ2本のウサギ型通信アンテナ
3. 大型ネオンピンク系フェイスディスプレイ
4. 側面の円形通信リング
5. 側面通信リングを主要位置とする89
6. 小型の半透明ピンクDigital Hovering Fin
7. 底面ホバリング機構
8. BLACK × NEON PINK
9. ウサギ × デジタル
10. 小型マスコットとして認識できるシルエット
このVisual Coreを維持した上で、表情・発光・状態・ポーズ等を変化させる。
---

# 6｜Expression System

MONYの**Expression（感情表示）とOperational State（動作状態）**を別レイヤーとして扱う。
## 6.1｜Standard Expressions

| Expression | Display | Meaning |
| --- | --- | --- |
| NORMAL | `・ω・` | 通常 |
| RELAX / SATISFIED | `＝ω＝` | 満足・のほほん・リラックス |
| HAPPY | `＞▽＜` | 喜び |
| SPECIAL | `☆ ☆` | 特殊・興奮 |

Standard ExpressionsはMONY自身の感情・反応を表示する。
Operational Stateとは原則として独立しており、状態に応じて特定Expressionへ自動固定しない。
## 6.2｜Forced State Display

HACKING SYNCでは通常のExpression SystemよりOperational State側の表示規則を優先する。
| Operational State | Forced Display |
| --- | --- |
| HACKING SYNC | `× ×` |

× ×は通常のStandard Expressionではなく、
HACKING SYNC時のみ使用されるForced State Display

として扱う。
HACKING SYNC中はStandard Expressionの自由選択を停止し、フェイスディスプレイを× ×へ強制同期する。
## 6.3｜COMMUNICATION

COMMUNICATIONは固定ExpressionではなくOperational Stateとして扱う。
したがってCOMMUNICATION中でも状況に応じて、
・ω・
＝ω＝
＞▽＜
等のStandard Expressionを使用可能とする。
通信状態そのものはアンテナ・側面リング・フィン・発光等によって表現する。
---

# 7｜Operational State

MONY v2.0では以下を3種類の基本Operational Stateとする。
NORMAL / COMMUNICATION / HACKING SYNC

これらは能力レベルや形態の上下関係を示すものではなく、同一MONYの異なる機構稼働状態を表す。
NORMAL → COMMUNICATION → HACKING SYNC
という一方向のパワーアップ段階として扱わない。
---

# 8｜NORMAL

MONYの標準状態。
### Visual


- 基本シルエットを維持
- 発光量は控えめ
- アンテナは通常状態
- 側面通信リングは低活動
- Digital Hovering Finは通常状態
- 底面ホバリングは安定した低～通常出力
- 外部Digital Effectは原則不要
### Default Expression


・ω・
ただし感情に応じて他のStandard Expressionへ変更可能。
NORMALはMONYの基準造形を最も明確に確認できる状態とする。
---

# 9｜COMMUNICATION

通信・データ処理等を行っている状態。
基本形状はNORMALから変更しない。
主に、

- 耳内部通信ラインの発光増加
- 側面通信リングの稼働・発光増加
- Digital Hovering Finの発光増加
- 底面ホバリング光の必要範囲での増加


によって活動状態を表現する。
COMMUNICATIONはExpressionではない。
感情に対応したStandard Expressionを独立して使用可能とする。
---

# 10｜HACKING SYNC

YAKUMOがHACKING MODEへ移行した際、MONYがその処理状態へ同期したOperational State。
MONYの形状、サイズ、基本配色、ウサギ型デジタル端末としての構造、YAKUMOとの関係性は変更しない。
## 10.1｜HACKING Display

HACKING SYNC中はStandard Expressionの自由選択を停止し、
× ×

へ強制同期する。
### 表示仕様


- ネオンピンク
- 左右2個の×
- NORMAL時の左右の目に相当する位置
- 通常の目を残さない
- 口を表示しない
- 頬表示を追加しない
- その他の顔記号を追加しない
- MONYのフェイスディスプレイとして自然なサイズ
- 過度に巨大化させない
## 10.2｜HACKING Activation

HACKING SYNCを、
MONY HACKING FORMへの変身

として扱わない。
基本シルエットおよび主要パーツ形状を維持したまま、

- Ear Antennaの発光強化
- Side Communication Ringの発光強化
- Digital Hovering Finの発光強化
- Bottom Hovering Systemの発光強化
- 控えめなピンク系glitch
- data fragment
- code / UI effect


等によって高負荷・高活動状態を表現可能とする。
## 10.3｜HACKING SYNC Output Rule

HACKING SYNCは、
MONYの全機能を最大出力へ移行させる状態ではない。

HACKING SYNCとは、YAKUMOのHACKING MODEにMONYが処理・通信面で同期しているOperational Stateを意味する。
したがって、

- 演算能力
- 通信能力
- ホバリング出力
- Digital Hovering Fin
- その他の内部機構


が常に最大出力になるとは定義しない。
発光強度や活動表現の増加はHACKING SYNC状態を視覚的に認識させるための表現であり、MONY全機能の最大稼働を意味しない。
---

# 11｜State Continuity Rule

すべてのOperational Stateにおいて、
同じMONYであること

を最優先する。
NORMAL、COMMUNICATION、HACKING SYNC間で、

- 本体サイズ
- 球体シルエット
- 耳の基本形状
- 側面通信ユニットの基本形状
- Digital Hovering Finの基本形状
- 基本配色
- 89の主要配置


を変更しない。
状態変化は主として、
Display / Lighting / Activity / Digital Effect

で表現する。
---

# 12｜Size Relationship

MONYの具体的な絶対寸法は固定しない。
既存Visual Bibleの、
MONYはYAKUMOの頭部より小さく、少女YAKUMOの頭部の50〜70%程度

を継承する。
また、

- 卓上に置ける
- 自然に抱えられる
- YAKUMOの肩付近を飛べる


程度の小型サイズ感を維持する。
Candidate設定画に記載された約10cm前後等の数値はOfficial寸法として採用しない。
---

# 13｜Color Rule

基本配色：
BLACK × NEON PINK

黒を主体とし、ピンクは顔・通信機構・アンテナ内部・Digital Hovering Fin・ホバリング光等の機能的アクセントとして使用する。
YAKUMO Visual Bibleの、
黒い世界の中でピンクが発光する

という共通配色思想を維持する。
白、グレー等は表示・ハイライト・機械構造上の補助色として限定的に使用可能。
---

# 14｜89 Rule

89はYAKUMO世界とMONYを接続するブランドモチーフとして維持する。
MONY v2.0では、
側面Communication Ring

を主要な89表示位置とする。
必要以上に耳・顔・背面・翼・ボディ全面・UIへ89を大量反復しない。
構図上追加する場合でも、MONYそのもののシルエット・顔・通信リングより目立たせない。
---

# 15｜Character Rule

MONY v2.0への外観変更によって、MONYの人格・YAKUMOとの関係性を変更しない。
MONYは、
かわいいペット

ではなく、
かわいい外見を持つ、意思のあるYAKUMOの対等な相棒

である。
マスコット性を強化しても、単なるアクセサリー、小道具、ペットとして扱わない。
---

# 16｜Accessories / Variations

衣装・季節・イベント等に合わせてMONYへ小型アクセサリーを追加する場合、MONY本体のVisual Coreを変更しない。
既存のC02 Black × Pink Float Ring等もこの原則に従う。
アクセサリーは、
MONYがアクセサリーを装着している

状態であり、
アクセサリーに合わせて別のMONYへ再設計する

ものではない。
---

# 17｜Avoid

MONY v2.0では以下を避ける。

- 球体を失い一般的な人型ロボットへ変更する
- ウサギ耳を削除する
- BLACK × NEON PINKの基本配色を失う
- 顔ディスプレイを通常の物理的な目・口へ変更する
- 側面円形通信ユニットを無関係な装飾へ置換する
- Digital Hovering Finを巨大な翼へ変更する
- NORMAL状態で過剰なメカ機構を露出する
- 装甲・武装・大型スラスター等を無断追加する
- 89を大量配置する
- HACKING SYNC専用の別ボディを作る
- HACKING SYNCで巨大ウイングを展開する
- HACKING SYNCで新規装甲・新規パーツを追加する
- HACKING Displayへ口・頬・通常目等を追加する
- × ×以外のHACKING顔をOfficial扱いする
- HACKING SYNCをMONY全機能の最大出力状態として固定する
- COMMUNICATIONを特定の感情へ固定する
- Operational Stateによって人格を変更する
- マスコット化を理由にMONYをペット・装飾へ格下げする
- 生成画像内の偶発的ディテールや技術スペックを設定へ自動採用する
---

# 18｜Image Generation Rule

MONY v2.0を画像化する場合、
「毎回新しいMONYをデザインする」のではなく、「同じMONYを異なる状況・表情・状態で描く」

ことを基本とする。
NORMALを造形基準とし、COMMUNICATION / HACKING SYNCでもVisual Coreを維持する。
状態表現のために必要以上の新規パーツを追加しない。
三面図・設定画では、
同一個体・同一構造を別角度から見たもの

としてFRONT / SIDE / BACKの接続関係を成立させる。
---

# 19｜Official Reference Policy

正式採用後の役割別参照優先順位を以下とする。
## 19.1｜Character / Personality / Relationship

1. `YAKUMO Character Bible v1.2.md`

X上での投稿・返信・距離感については、
`YAKUMO X Prompt v1.4.md`を使用する。

本Specificationでは、MONYの人格・関係性を重複定義しない。

## 19.2｜MONY v2.0 Visual Specification


1. 本書 `MONY v2.0 Specification v1.0 Official`
2. `MONY_Master_v2.0.png`
3. `YAKUMO_Visual_Bible_v1.3.md`

ただし、実際の造形確認については`MONY_Master_v2.0.png`を最優先ビジュアルリファレンスとして扱う。

## 19.3｜Face Display

1. `MONY_Expression_Reference_v1.0.png`
2. 本書のExpression System

Face Displayの具体的な表示形状はExpression Referenceを基準とする。

本体造形については`MONY_Master_v2.0.png`を優先する。

## 19.4｜HACKING


1. `YAKUMO_HACKING_MODE_Specification_v1.1_Official.md`
2. 本書のMONY HACKING SYNC仕様

HACKING MODEについては、上記資料を役割に応じて使用する。
---

# Version Information

| 項目 | 内容 |
| --- | --- |
| Document | **MONY v2.0 Specification** |
| Version | **v1.0 Official** |
| Status | **OFFICIAL** |
| Character | **MONY / モニィ** |
| Project | **YAKUMO Project** |
| Adopted Design | **MONY v2.0 — C Revised** |
| Based on | `MONY v2.0 Specification Draft v0.2` |
| Supersedes | `MONY v2.0 Specification Draft v0.2` |
| Previous Visual Generation | **MONY v1.0** |
| Official Visual Master | `MONY_Master_v2.0.png` |

---

# Draft v0.2 → v1.0 Official Change Log

- `MONY v2.0 Specification Draft v0.2`を正式採用
- MONYの人格・YAKUMOとの関係性・ウサギ型デジタル端末としての基本Identityは変更なし
- Visual Designを**MONY v2.0 — C Revised**として正式採用
- **Expression / Operational State / Forced State Display**を独立した概念として整理
- 基本Operational Stateを**NORMAL / COMMUNICATION / HACKING SYNC**の3種類として定義
- HACKING SYNCを別形態への変身ではなく、同一Visual Coreを維持した同期状態として定義
- HACKING SYNC時のForced State Displayを`× ×`として定義
- `MONY_Master_v2.0.png`をOfficial Visual Masterとして参照
- `MONY_Master_v1.0.png`を**Legacy / Archived Reference**として整理
- **新しいMONY人格の追加なし**
- **YAKUMOとの関係性変更なし**

---

**End of Official MONY Specification**

---
