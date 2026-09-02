
---

# YAKUMO HACKING MODE — Official Specification

> 本書は、少女ヤクモが高度なハッキング処理を実行する際に発現する特殊状態  
> **`YAKUMO HACKING MODE`** の視覚・表情・演出・運用ルールを定義するOfficial Specificationである。
>
> HACKING MODEは新しい人格・キャラクター・衣装ではなく、**同一のYAKUMOが通常以上の処理能力を使用している状態**として扱う。

---

## 1｜Mode Identity

| 項目 | Official定義 |
|---|---|
| Mode Name | **YAKUMO HACKING MODE** |
| Version | **Official v1.1** |
| Status | **Official** |
| Category | Special State / Hacking |
| Character | YAKUMO |
| Base Form | 少女ヤクモ / Standard Form |
| Default Costume | 変更しない |
| Primary Colors | BLACK × NEON PINK |
| Symbol | 89 |
| Core Concept | **普段の余裕が消え、静かに本気を出したYAKUMO** |

HACKING MODEはCostumeではない。

したがって、`C04`等のCostume IDを割り当てず、C01-B、C02、C03などの衣装とは**別レイヤーの状態変化**として管理する。

HACKING MODEの採用によって、既存のDefault Costumeや各Official Costumeを置き換えない。

---

## 2｜Core Concept

HACKING MODEのテーマは、

> **「いつものYAKUMOが、遊びをやめて本気で処理を始めた瞬間。」**

通常状態では、YAKUMO本来の可愛さ、いたずらっぽい余裕、少しいたずらっぽい雰囲気を維持する。

HACKING MODE発動時も人格そのものは変化しない。

闇堕ち、暴走、悪人格への交代ではなく、**高度なハッキング処理への集中によって、普段表面に出ている遊びや余裕が一時的に薄れる状態**とする。

NORMALとHACKING MODEの差は「善悪」や「人格」の変化ではなく、**処理への集中度と、それに伴う視覚状態・表情の変化**として表現する。

---

## 3｜Expression

### 3.1｜NORMAL

既存Official基準を維持する。

> **NORMAL 80% / MISCHIEF 20%**

- 控えめなω口
- 柔らかなピンク～マゼンタの瞳
- 少しだけ楽しそうな表情
- 可愛さを主体とする
- 「何か企んでない？」と感じる程度のいたずらっぽさ
- 常に強いニヤリ顔や挑発的な表情にはしない

NORMAL時の表情ルールそのものは、HACKING MODEの追加によって変更しない。

---

### 3.2｜HACKING MODE

基本的な表情方向：

> **静かな集中 60% / アンニュイ 40%**

HACKING MODEでは、通常時に見られるいたずらっぽい余裕が一時的に弱まる。

- 通常時の微笑みがほぼ消える
- ω口を弱める
- 口元は小さなニュートラル形状
- 口角を明確に下げない
- 上瞼がNORMALよりわずかに重くなる
- 目の縦幅をわずかに抑える
- 視線は対象を明確に捉える
- 眠そうな表情にはしない
- 眉を怒らせない
- 不機嫌、怒り、悲しみとして表現しない
- 冷酷、病み、狂気、悪役的な表情にしない

重要なのは「怖いYAKUMO」ではなく、

> **「今は遊んでいないYAKUMO」**

と感じられることである。

頬、輪郭、鼻、頭部比率等の本人性を担う顔造形はNORMALから変更しない。

---

## 4｜HACKING EYE

HACKING EYEは、HACKING MODEを象徴する最重要視覚サインとする。

### 4.1｜Eye Position

HACKING EYEは、

> **YAKUMO本人から見て左目**

に固定する。

正面からYAKUMOを見た場合、**画面・鑑賞者から見て右側の目**となる。

鏡像化された画像や構図上の左右反転によって、設定上の左右を変更しない。

---

### 4.2｜Eye Structure

左目のみ以下の状態へ変化する。

- 強膜：**BLACK**
- 虹彩：**高輝度NEON MAGENTA**
- 瞳孔周辺：薄いデジタルリング
- 微量のピンク系glitch
- 必要に応じて微細なdata particle
- 発光は虹彩を中心とし、顔全体へ過剰に侵食させない

右目はYAKUMO本来のピンク～マゼンタの瞳を維持する。

両目を恒常的にHACKING EYEへ変更しない。

---

### 4.3｜Design Intent

BLACKの強膜による異質さと、YAKUMO固有のNEON MAGENTAを組み合わせる。

その目的は生物的な怪物化ではなく、

> **電脳存在であるYAKUMOの処理状態が、視覚的に表面化したもの**

として成立させることである。

HACKING EYE周辺へ大規模な亀裂、傷、侵食、触手状構造等を追加することを基本仕様としない。

---

## 5｜Hair Breakdown

通常YAKUMOの左右の大きなツインお団子は、YAKUMOのVisual Coreとして維持する。

Hair BreakdownはVisual Coreであるツインお団子を変更・廃止するものではなく、HACKING MODE中に限って発生する一時的な状態変化として扱う。

ツインお団子として認識できる基本シルエットは常に維持する。

### 5.1｜HACKING時

- ツインお団子の基本シルエットは残す
- お団子の一部から毛束がほどける
- 長い黒髪がNORMALより不規則に流れる
- ピンクの毛束・メッシュがわずかに強く発光する
- 顔周辺へ数本の毛束が自然に落ちてもよい
- 少量のピンク系data particleを伴ってよい
- 完全なロングヘアへ変更しない
- ツインお団子そのものを完全消失させない

Hair Breakdownの表現では、崩壊量よりも**ツインお団子としての識別性**を優先する。

---

### 5.2｜Asymmetric Breakdown

Hair Breakdownは完全な左右対称にしない。

> **HACKING EYEのある本人左側をやや強く崩す。**

目安として、

- 本人左側 / HACKING EYE側：崩れが強い
- 本人右側 / NORMAL EYE側：比較的安定

とする。

ただし、極端な左右差によって別の髪型に見えるほど崩さない。

これにより、HACKING EYEを中心としてYAKUMOの描画・処理状態が乱れているような非対称性を作る。

---

## 6｜Visual Effects

HACKING MODEでは以下の視覚エフェクトを使用できる。

- BLACK data particles
- NEON PINK / MAGENTA glitch
- 微細なpixel noise
- digital ring
- scanline
- code fragment
- broken UI fragment
- `89`を利用した限定的なUI表現

ただし、これらは**YAKUMO本人より目立たせない。**

### 6.1｜Effect Priority

基本的な視線誘導は、

**HACKING EYE**

↓

**Expression**

↓

**Hair Breakdown**

↓

**Digital Effects**

の順とする。

設定立ち絵では特にエフェクト量を抑える。

HACKING MODEを表現するために、画面全体をコード、UI、グリッチで埋める必要はない。

### 6.2｜89

`89`はYAKUMOの主要シンボルとして使用可能。

ただしHACKING MODEを理由として、

- 大量に反復する
- 顔周辺へ無秩序に配置する
- 衣装へ新しい89を大量追加する

ことは避ける。

着用中のCostumeに存在する`89`を基本として維持し、追加UIとして使用する場合も限定的に扱う。

HACKING MODEの発動は、衣装上の`89`の数・位置・形状を変更する理由にはならない。

---

## 7｜Costume Rule

HACKING MODEは衣装ではない。

そのため、発動によって着用中の衣装そのものを変更しない。

例えば、

`C01-B + HACKING MODE`

`C02 + HACKING MODE`

`C03 + HACKING MODE`

という組み合わせを可能とする。

衣装の構造、配色、装飾、アクセサリー、`89`の配置、左右非対称性は、Costume Registryおよび各Official Costume Specificationを優先する。

Costume指定がない場合は、既存のCostume Registryに従い、

> **C01-B Cyber Pleats Style / Standard Form**

を使用する。

HACKING MODE専用衣装へ自動的に着替えたり、着用中のCostumeが変形したりすることを基本仕様としない。

HACKING MODEを理由として、新規のストラップ、バックル、ロゴ、アクセサリー、装甲、端末、発光部品等を衣装へ追加しない。

---

## 8｜Personality Rule

HACKING MODEによってYAKUMOの人格を変更しない。

YAKUMO本人の、

- 記憶
- 価値観
- 他者との関係
- MONYとの関係
- 基本的な善悪判断
- いたずら好きな本質

はNORMALから連続している。

変化するのは主に、

> **表情・集中度・視覚的な処理状態**

である。

そのため、

- 殺意を前面に出す
- 残虐になる
- 他者を見下す
- 冷酷な別人格になる
- 悪人格へ交代する
- 「悪のYAKUMO」として振る舞う
- HACKING MODE中だけ性格が完全に変わる

といった解釈は基本仕様としない。

HACKING MODE解除後にNORMALへ戻れば、普段のいたずらっぽいYAKUMOらしい表情・振る舞いも自然に戻る。

---

# 9｜MONY Synchronization

HACKING MODE発動時、MONYはYAKUMOの処理状態に同期し、

> **Operational State：HACKING SYNC**

へ移行する。

HACKING SYNCは、MONY v2.0に定義された基本Operational Stateの一つであり、MONYが別形態へ変身したり、別キャラクター・別端末へ変化したりする状態ではない。

MONYの人格、意思、YAKUMOとの対等な相棒関係についてもNORMALから連続している。

---

## 9.1｜Forced State Display

HACKING SYNC中のMONYは、Standard Expressionの自由選択を一時的に停止し、Face Displayを以下へ同期する。

> **MONY Forced State Display：`× ×`**

`× ×`はNORMAL、RELAX / SATISFIED、HAPPY、SPECIAL等と同列のStandard Expressionではない。

これは、

> **HACKING SYNC専用のForced State Display**

として扱う。

`× ×`の具体的な表示形状については、

> **`MONY_Expression_Reference_v1.0.png`**

をOfficial Expression Referenceとして使用する。

HACKING SYNC中に、`× ×`へ口、頬、追加記号、別の目、その他の感情記号を加えない。

---

## 9.2｜Visual Continuity

HACKING SYNCへ移行しても、MONYのVisual Coreは維持する。

変更しない基本要素：

- 本体サイズ
- 丸みの強い黒い球体ボディ
- 球体シルエット
- Rabbit Antennaの基本形状
- Face Displayの基本領域
- Side Communication Ringの基本形状
- Side Communication Ringを主要位置とする`89`
- Digital Hovering Finの基本形状
- Bottom Hovering Systemの基本構造
- BLACK × NEON PINK
- ウサギ型デジタル端末としてのIdentity

MONYの実際の造形については、

> **`MONY_Master_v2.0.png`**

をOfficial Visual Masterとする。

HACKING SYNCを理由として、MONYの形状、サイズ、基本配色、パーツ構成を再設計しない。

---

## 9.3｜HACKING SYNC Activity

HACKING SYNCでは、MONYの既存機構について活動・発光表現をNORMALより強めることができる。

主な対象：

- Rabbit Antenna内部のネオンピンク系通信ライン
- Side Communication Ring
- Digital Hovering Fin
- Bottom Hovering System

また、必要に応じて、

- 控えめなglitch
- data fragment
- code fragment
- pixel noise
- 小型Digital UI

等をMONY周辺へ使用できる。

ただし、これらは**既存機構の活動状態を示す演出**であり、新しい機構や装備ではない。

MONY本体の識別性とFace Displayの`× ×`をDigital Effectより優先する。

---

## 9.4｜State Continuity Rule

HACKING SYNCにおける状態変化は主として、

> **Display / Lighting / Activity / Digital Effect**

によって表現する。

以下をHACKING SYNCのために自動追加しない。

- 新規装甲
- 武器
- 大型翼
- 大型スラスター
- 追加アンテナ
- 新しいSide Unit
- 新しいCommunication Ring
- 新規アクセサリー
- 新しい`89`
- 新規ロゴ
- その他の未定義パーツ

Digital Hovering Finを大型の翼へ変形・拡張しない。

Rabbit Antennaを別形状へ変形させない。

Side Communication Ringを別機構へ置き換えない。

---

## 9.5｜HACKING SYNC Is Not Maximum Output

HACKING SYNCは、

> **MONYの全機能が最大出力になる状態**

とは定義しない。

また、

> **NORMAL → COMMUNICATION → HACKING SYNC**

という出力段階・強化段階を意味しない。

NORMAL、COMMUNICATION、HACKING SYNCは、それぞれMONYの活動状態を示すOperational Stateである。

HACKING SYNCを理由として、

- MAX OUTPUT
- OVERDRIVE
- COMBAT MODE
- BATTLE MODE
- FULL POWER
- 第二段階HACKING
- 強化形態

等を自動的に派生させない。

必要になった場合は、新しいConceptとして別途検討する。

---

## 9.6｜MONY Reference Priority

HACKING MODE中のMONYについては、対象ごとに以下を基準とする。

**MONYの人格・役割・YAKUMOとの関係性**

→ `YAKUMO Character Bible v1.2.md`

**MONY固有のVisual Design / Expression System / Operational State**

→ `MONY v2.0 Specification v1.0 Official.md`

**MONY本体の実際の造形**

→ `MONY_Master_v2.0.png`

**Face Displayの具体的形状**

→ `MONY_Expression_Reference_v1.0.png`

**YAKUMO HACKING MODEとの同期条件・演出**

→ 本書

`MONY_Master_v1.0.png`は、

> **Legacy / Archived Reference**

として扱い、現行MONYの造形基準には使用しない。

v2.0と競合する旧本体形状、Rabbit Antenna、Face Display、側面機構、翼、`89`配置、その他の造形をHACKING MODE用MONYへ復活させない。

---

## 10｜State Transition

HACKING MODE v1.1では、YAKUMO本人の基本状態遷移を引き続きシンプルに定義する。

### Basic Sequence

**NORMAL**

↓

**HACKING MODE**

↓

**RETURN**

↓

**NORMAL**

とする。

MONYが登場している場合、YAKUMOのHACKING MODEに同期してMONY側のOperational Stateも変化する。

---

### 10.1｜NORMAL → HACKING MODE

発動時には主に以下が変化する。

- 本人左目がHACKING EYEへ変化
- 表情から普段のいたずらっぽい余裕が薄れる
- Hair Breakdownが発生
- ピンクの毛束の発光がわずかに強まる
- 少量のglitch / data particleが発生
- MONY登場時はOperational Stateが**HACKING SYNC**へ移行
- MONYのFace DisplayがForced State Display **`× ×`**へ同期

人格や衣装そのものは変化しない。

MONYについても本体造形や人格そのものは変化しない。

---

### 10.2｜RETURN

HACKING MODE解除時には、

- 左目のHACKING EYE解除
- 通常のピンク～マゼンタ瞳へ復帰
- Hair Breakdown解除
- ツインお団子構造復元
- 過剰処理による発光・glitch・data particle消失
- HACKING用Expression解除
- NORMAL表情へ復帰

する。

MONYがHACKING SYNC中の場合は、

- HACKING SYNCを解除
- Forced State Display `× ×`を解除
- HACKING SYNC固有の強調された発光・活動表現を解除
- 通常のOperational Stateへ復帰
- Standard Expressionの使用を再開

する。

MONYの復帰後の具体的なStandard Expressionは、その場面におけるMONY自身の感情・反応に応じて決定できる。

必ず`・ω・`へ固定する必要はない。

復帰は「別人格から元に戻る」のではなく、**高負荷処理状態が終了して通常状態へ戻ること**を意味する。

---

### 10.3｜Upper State

現時点では、

- MAX OUTPUT
- OVERDRIVE
- 第二段階HACKING
- 両目HACKING EYE

等のYAKUMO側上位状態を**Official設定として定義しない。**

MONYについても、HACKING SYNCより上位の強化状態を本仕様から自動的に派生させない。

将来的に物語・演出上必要になった場合に、新しいConceptとして個別に検討する。

HACKING MODE v1.1の成立に上位形態を必要としない。

---

## 11｜Reference Policy

### 11.1｜General Principle

HACKING MODEを表現する場合も、YAKUMO本人、Visual Core、着用衣装、MONYの既存Official基準を維持する。

HACKING MODEは既存Officialデザインの上に適用される**状態レイヤー**であり、既存のMaster、Bible、Costume Specification、MONY Specificationを置き換えるものではない。

資料間で表現が競合する場合は、それぞれの役割に応じて以下を基準とする。

**YAKUMO本人の実際の造形**

→ `YAKUMO_Master_v2.0.png`

**顔・髪・体型・配色・Visual Core**

→ `YAKUMO_Visual_Bible_v1.3.md`

**着用衣装**

→ `YAKUMO_Costume_Registry_v1.3.md`  
＋ 該当する各Official Costume Specification  
＋ 該当するOfficial Costume Reference

**HACKING MODE固有の状態変化**

→ 本書 `YAKUMO HACKING MODE Specification v1.1 Official`

**MONY固有仕様**

→ `MONY v2.0 Specification v1.0 Official.md`

**MONYの実際の造形**

→ `MONY_Master_v2.0.png`

**MONYのFace Display**

→ `MONY_Expression_Reference_v1.0.png`

Supplementary / Development Referenceは、これらのOfficial基準より下位の補助資料として扱う。

---

### 11.2｜NORMAL YAKUMO

通常YAKUMO本人の造形は、

1. `YAKUMO_Master_v2.0.png`
2. `YAKUMO_Visual_Bible_v1.3.md`

を基準とする。

HACKING MODEの追加によって、NORMAL YAKUMOのOfficial Master、Visual Core、Standard Formを変更または置換しない。

HACKING MODE中も、顔型、身体比率、年齢感、基本的な髪型、本人固有の配色および識別要素はNORMAL YAKUMOから連続させる。

---

### 11.3｜Supplementary / Development Reference

以下の画像は、HACKING MODEの開発および方向性確認に使用された補助Referenceである。

**Face / Expression Development Reference**

`YAKUMO_HACKING_MODE_FaceStudy_v0.4.png`

主な参照対象：

- HACKING EYEの視覚方向
- 瞼の重さ
- 視線
- 口元
- 静かな集中＋アンニュイのExpression

**Full Body Development Reference**

`YAKUMO_HACKING_MODE_FullBody_v0.6.png`

主な参照対象：

- HACKING MODEの全身印象
- Hair Breakdownの方向性
- HACKING状態における全体バランス
- 控えめなデジタルエフェクト

**Reproduction Test Images**

Draft v0.2の再現性検証で生成された各テスト画像。

主な参照対象：

- HACKING EYEの再現性
- Expressionの再現性
- Hair Breakdownの再現性
- Digital Effectsの適正量
- MONYのHACKING SYNC表現
- 画像生成時に起こりやすい逸脱の確認

これらはすべて、

> **Supplementary / Development Reference**

として扱う。

Official Master、Official Costume Reference、MONY Official Master、または新しいOfficialデザインには指定しない。

---

### 11.4｜Non-Canonical Elements in Development Images

Face Study v0.4、Full Body v0.6および再現テスト画像には、画像生成上の偶発的な差異や追加要素が含まれる場合がある。

以下のような要素は、本書または既存Official資料で明示されていない限り、Official設定として採用しない。

- 追加された`89`
- 新規ストラップ
- 新規バックル
- 新規アクセサリー
- 新規ロゴ
- 新規衣装パーツ
- 衣装の構造変更
- Costumeの配色変更
- 左右非対称構造の変更
- 身体比率や顔造形の変化
- 過剰に長くなった髪
- ツインテール化したHair Breakdown
- MONYの形状変更
- MONYの人型化または強化形態化
- MONYの大型翼化
- MONYへの新規装甲・武器・追加アンテナ
- MONYの`89`配置変更または過剰な反復
- 過剰なUI、コード、glitch
- その他、生成時に偶発的に追加された装飾や構造

開発画像内に描かれているという理由だけで、その要素を設定として継承しない。

画像とOfficial文書が競合する場合は、Official Master、Visual Bible、MONY v2.0 Specification、Costume Registry、各Costume Specification、本仕様を役割に応じて優先する。

---

### 11.5｜Future Official HACKING MODE Master

HACKING MODE専用のOfficial Masterは、v1.1制定時点でも未指定とする。

将来的に専用Masterを制作する場合は、`YAKUMO_Master_v2.0.png`を本人造形の基準とし、該当するOfficial Costumeの構造を維持した上で、原則として以下のHACKING MODE固有要素のみを反映する。

- 本人左目のHACKING EYE
- HACKING MODE Expression
- 一時的なHair Breakdown
- 控えめなDigital Effects
- MONY登場時のHACKING SYNC

MONYを描写する場合は、

- `MONY_Master_v2.0.png`
- `MONY_Expression_Reference_v1.0.png`
- `MONY v2.0 Specification v1.0 Official.md`

を基準とする。

完成した画像は、既存Official資料との整合性を確認した後、明示的な正式採用を経て初めてOfficial HACKING MODE Masterとして扱う。

---

## 12｜Image Generation Rule

HACKING MODEを画像化する場合は、

> **「新しいHACKINGキャラクターをデザインする」のではなく、「現在のYAKUMOをHACKING MODEへ移行させる」**

ことを基本とする。

MONYについても、

> **「HACKING用MONYを新しくデザインする」のではなく、「現在のMONY v2.0をHACKING SYNCへ移行させる」**

ことを基本とする。

参照関係は次のように分ける。

**YAKUMO本人**

→ `YAKUMO_Master_v2.0.png`

**通常Visual Core**

→ `YAKUMO_Visual_Bible_v1.3.md`

**着用衣装**

→ Costume Registry  
＋ 該当Costume Specification  
＋ 該当Official Costume Reference

**HACKING状態**

→ 本仕様

**HACKING表現の補助**

→ Supplementary / Development Reference

**MONY本人**

→ `MONY_Master_v2.0.png`

**MONY固有仕様**

→ `MONY v2.0 Specification v1.0 Official.md`

**MONY Face Display**

→ `MONY_Expression_Reference_v1.0.png`

**MONY HACKING SYNC**

→ MONY v2.0 Specification  
＋ 本仕様のSynchronization Rule

Supplementary / Development Referenceに偶然現れた衣装ディテール、身体造形、アクセサリー、`89`、MONYの構造等を、新しいOfficial設定へ自動採用しない。

### 12.1｜YAKUMO変更対象

画像生成時にYAKUMO側で変更を許可する基本対象は、

1. 本人左目
2. 表情
3. 髪の部分的な崩れ
4. 周囲の控えめなエフェクト

とする。

それ以外の本人造形、衣装構造、装飾、配色、`89`配置、左右非対称性は、参照するOfficial資料を維持する。

### 12.2｜MONY変更対象

MONYが登場する場合、HACKING SYNCによって変更を許可する基本対象は、

1. Face Displayを`× ×`へ変更
2. 既存発光部の活動・発光強度
3. 周囲の控えめなDigital Effect

とする。

MONYの本体造形、サイズ、球体シルエット、Rabbit Antenna、Side Communication Ring、`89`主要位置、Digital Hovering Fin、Bottom Hovering System、基本配色は変更しない。

---

## 13｜Avoid

HACKING MODEでは以下を避ける。

- YAKUMOを別人化する
- 顔型を別キャラクターへ変更する
- 身体比率・年齢感を変更する
- 通常状態までHACKING Expressionにする
- HACKING EYEを本人右目へ移動する
- 両目を常時黒強膜にする
- HACKING EYE周辺を過剰に怪物化する
- 怒り顔を基本表情にする
- 不機嫌さを基本感情にする
- 病み・狂気・残虐性を人格へ追加する
- 闇堕ちとして扱う
- ツインお団子を完全消失させる
- 完全な別髪型へ変更する
- Hair Breakdownをロングツインテール化する
- HACKING MODE専用衣装へ勝手に変更する
- Costumeそのものを変形させる
- 新規のストラップ、バックル、アクセサリー、ロゴを追加する
- `89`を過剰に増殖させる
- UI、コード、glitchでYAKUMO本人を隠す
- MONYを別形態・別キャラクターへ再設計する
- MONYを人型化する
- MONYを重装甲化する
- MONYへ武器を追加する
- MONYへ大型翼・大型スラスターを追加する
- MONYへ追加アンテナを設ける
- MONYのSide Communication Ringを別機構へ変更する
- MONYのDigital Hovering Finを大型翼化する
- MONYの`89`を別位置へ大量追加する
- HACKING SYNCをMONYの全機能最大出力として扱う
- `× ×`をStandard Expressionとして扱う
- `× ×`へ口、頬、追加記号等を加える
- COMMUNICATIONをHACKING SYNCの前段階・低出力状態として扱う
- `MONY_Master_v1.0.png`の旧造形を現行MONYへ復活させる
- Supplementary / Development Referenceの偶発的要素を設定化する
- 未定義のMAX OUTPUT等を自動的に追加する

---

## 14｜Design Principle

HACKING MODEを見たとき、

> **「新しいキャラクターになった」**

ではなく、

> **「あ、YAKUMOが本気になった。」**

と認識できることを最重要目標とする。

NORMAL時の、

**可愛さ＋いたずらっぽい余裕**

と、

HACKING MODE時の、

**静かな集中＋わずかなアンニュイさ**

のコントラストによって、同一人物の中にある二つの表情を成立させる。

HACKING EYE、Hair Breakdown、glitch等はその変化を視覚化するためのものであり、YAKUMO本人のVisual Coreを置き換えるものではない。

MONYについても同様に、HACKING SYNCを見たとき、

> **「別のMONYになった」**

のではなく、

> **「いつものMONYがYAKUMOのHACKING MODEへ同期している」**

と認識できることを基本とする。

MONY v2.0のVisual Coreを維持したまま、

**`× ×` Forced State Display**

＋

**既存機構の活動・発光**

＋

**控えめなDigital Effect**

によってHACKING SYNCを成立させる。

---

# Version Information

| 項目 | 内容 |
|---|---|
| Document | **YAKUMO HACKING MODE Specification** |
| Official Version | **1.1** |
| Status | **Official** |
| Category | Special State / Hacking |
| Character | YAKUMO |
| HACKING EYE | **本人左目固定** |
| Base Transition | **NORMAL → HACKING MODE → RETURN** |
| Upper State | **Not Defined** |
| Default Costume | **C01-B Cyber Pleats Style / Standard Form** |
| Costume ID | **Not Assigned / Special State** |
| Official HACKING MODE Master | **Not Assigned** |
| MONY Operational State | **HACKING SYNC** |
| MONY Forced State Display | **`× ×`** |
| MONY Specification | `MONY v2.0 Specification v1.0 Official.md` |
| MONY Official Visual Master | `MONY_Master_v2.0.png` |
| MONY Official Expression Reference | `MONY_Expression_Reference_v1.0.png` |
| Legacy MONY Master | `MONY_Master_v1.0.png` — Legacy / Archived |
| Full Body Development Reference | `YAKUMO_HACKING_MODE_FullBody_v0.6.png` |
| Face Development Reference | `YAKUMO_HACKING_MODE_FaceStudy_v0.4.png` |
| Reproduction Test Images | **Supplementary / Development Reference** |
| Previous Version | **YAKUMO HACKING MODE Specification v1.0 Official** |
| Source Draft | **YAKUMO HACKING MODE Draft v0.2** |
| Officialization | **Approved / Adopted** |

---

# v1.0 → v1.1 Change Log

- MONY v2.0正式採用後の現行Official体系へHACKING MODE Specificationを移行
- MONYの造形基準を`MONY_Master_v1.0.png`から**`MONY_Master_v2.0.png`へ更新**
- `MONY_Master_v1.0.png`を現行造形基準から除外し、**Legacy / Archived Reference**へ移行
- `MONY v2.0 Specification v1.0 Official.md`をMONY固有のVisual Design、Expression System、Operational Stateの基準資料として追加
- `MONY_Expression_Reference_v1.0.png`をFace DisplayのOfficial Expression Referenceとして追加
- HACKING MODE発動時のMONY同期状態を、単なるDisplay変更から**Operational State：HACKING SYNC**へ正式整理
- `× ×`をStandard Expressionではなく、**HACKING SYNC専用Forced State Display**として整理
- HACKING SYNC中はStandard Expressionの自由選択を停止し、Face Displayを`× ×`へ同期する規則を反映
- HACKING SYNC中もMONY v2.0のVisual Coreを維持するState Continuity Ruleを反映
- MONYの本体サイズ、球体シルエット、Rabbit Antenna、Face Display領域、Side Communication Ring、Digital Hovering Fin、Bottom Hovering System、BLACK × NEON PINK、`89`主要位置をHACKING SYNC中も変更しないことを明文化
- HACKING SYNCではRabbit Antenna内部ライン、Side Communication Ring、Digital Hovering Fin、Bottom Hovering System等の**既存機構の活動・発光を強めることができる**と整理
- HACKING SYNCにおいて控えめなglitch、data、code、pixel noise、Digital UIを使用可能とした
- MONYの状態変化を主として**Display / Lighting / Activity / Digital Effect**で表現する方針を正式反映
- HACKING SYNCを理由とする新規装甲、武器、大型翼、大型スラスター、追加アンテナ、新規アクセサリー、新規機構等の自動追加を禁止
- Digital Hovering Finを大型翼へ変形・拡張しないことを明文化
- HACKING SYNCをMONYの全機能最大出力として扱わないことを明文化
- NORMAL / COMMUNICATION / HACKING SYNCを出力段階・強化段階として扱わないことを反映
- RETURN時にMONYのHACKING SYNCおよびForced State Display `× ×`を解除する規則を追加
- RETURN後のMONYはStandard Expressionの使用を再開し、必ず`・ω・`へ固定する必要はないことを明文化
- Image Generation RuleをYAKUMO側とMONY側へ分離し、MONY側で変更可能な対象をFace Display、既存発光部の活動・発光、控えめなDigital Effectへ整理
- MONYのHACKING用別デザインを新規生成せず、**現在のMONY v2.0をHACKING SYNCへ移行させる**ことを画像生成原則として追加
- Supplementary / Development Referenceに含まれる旧MONY造形や偶発的な追加パーツを現行設定へ継承しないことを強化
- Reference PolicyのMONY参照体系をv2.0へ全面更新
- Visual Bible参照を`YAKUMO_Visual_Bible_v1.2.md`から**`YAKUMO_Visual_Bible_v1.3.md`へ更新**
- YAKUMO本人のHACKING EYE、Expression、Hair Breakdown、Visual Effects、Costume Rule、Personality Rule、基本State TransitionおよびDesign Principleの中核仕様には変更なし
- HACKING EYEは引き続き**YAKUMO本人から見て左目固定**
- YAKUMO側のMAX OUTPUT、OVERDRIVE、第二段階HACKING、両目HACKING EYE等の上位状態は引き続きOfficial設定として定義しない
- HACKING MODEがCostumeではなく、既存衣装へ重ねて適用する**Special State**である原則を維持
- HACKING MODE専用Official Masterは引き続き**Not Assigned**とする

---

**End of Official Specification**

---
