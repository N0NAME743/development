
---

# YAKUMO Costume Registry

> 本書は、YAKUMOの公式衣装・候補衣装・派生衣装を一覧管理する衣装目録である。  
> 衣装を選択するときは本書を入口とし、具体的な構造・配色・装飾は各衣装の個別仕様書および公式参照画像で確認する。

---

## 1｜Registry Information

| 項目 | 内容 |
| --- | --- |
| Document | **YAKUMO Costume Registry** |
| Version | **1.3** |
| Status | **Official Index** |
| Character | **YAKUMO** |
| Standard Form | **少女ヤクモ** |
| Default Costume | **C01-B Cyber Pleats Style / Standard Form** |
| Costume ID Format | **C + 2桁以上の連番／既存派生記号** |

本書は衣装の詳細設定を複製しない。

各衣装の存在、状態、用途、最新版、参照先およびDefault指定のみを管理する。

衣装を変更してもYAKUMO本人やMONYを別キャラクターとして再設計しない。

---

## 2｜Official Costume Index

| ID | Official Name | Status | Category | Form | Current Version / Authority | Default |
| --- | --- | --- | --- | --- | --- | --- |
| **C01-B** | **Cyber Pleats Style** | Official Costume | Default / Cyber Street | 少女ヤクモ / Standard Form | `YAKUMO_Visual_Bible_v1.3.md` / `YAKUMO_Master_v2.0.png` | **Yes** |
| **C02** | **Cyber Beach Style** | Official Costume | Summer / Swimwear | 少女ヤクモ / Standard Form | `YAKUMO_Costume_C02_Cyber_Beach_v1.1.md` | No |
| **C03** | **Cyber Idol Style** | Official Costume | Stage / Idol | 少女ヤクモ / Standard Form | `YAKUMO_Costume_C03_Cyber_Idol_v1.1.md` | No |

C01-B、C02、C03のStatus、用途、Default指定はv1.2から変更しない。

C02およびC03は、v1.1でVisual Bible v1.3およびMONY v2.0体系へのReference Migrationを完了している。

---

## 3｜Costume Selection Rule

### Costume指定がない場合

**C01-B Cyber Pleats Style / Standard Form**を使用する。

### Costume IDが指定された場合

本RegistryでIDとStatusを確認し、該当する個別仕様書の最新版を適用する。

```text
Costume: C01-B
```

→ Default CostumeのCyber Pleats Styleを使用する。

```text
Costume: C02
```

→ Official CostumeのCyber Beach Style v1.1を使用する。

```text
Costume: C03
```

→ Official CostumeのCyber Idol Style v1.1を使用する。

衣装を切り替えても、YAKUMO本人の顔・髪・身体・Visual Coreは別人化させない。

YAKUMO本人については、

- 実際の顔造形・身体比率・基本造形：`YAKUMO_Master_v2.0.png`
- 共通Visual Rule：`YAKUMO_Visual_Bible_v1.3.md`

を基準とする。

MONYが登場する場合も、衣装に合わせてMONY本体を再設計しない。

---

## 4｜Costume Records

### C01-B｜Cyber Pleats Style

| 項目 | 内容 |
| --- | --- |
| Status | Official Costume |
| Role | **Default Costume** |
| Category | Default / Cyber Street |
| Form | 少女ヤクモ / Standard Form |
| Specification | `YAKUMO_Visual_Bible_v1.3.md` |
| Official Visual Reference | `YAKUMO_Master_v2.0.png` |
| Notes | 指定がない場合に使用。C02以降の追加によって置換しない。 |

---

### C02｜Cyber Beach Style

| 項目 | 内容 |
| --- | --- |
| Status | Official Costume |
| Role | Alternate Official Costume |
| Category | Summer / Swimwear |
| Form | 少女ヤクモ / Standard Form |
| Current Version | **v1.1** |
| Specification | `YAKUMO_Costume_C02_Cyber_Beach_v1.1.md` |
| Costume Reference | `YAKUMO_C02_Cyber_Beach_Reference_v1.0.png` |
| Notes | 黒主体のスポーティーなセパレート水着。C01-Bを置換しない。 |

C02 v1.1では、衣装デザインを変更せず、Visual Bible v1.3およびMONY v2.0体系へのReference Migrationを完了している。

C02に定義されたMONY用Summer Accessory等の衣装固有要素はC02仕様書を使用する。

MONY本人の現行造形・Expression・Operational Stateは、本Registry第8節およびC02 v1.1のReference Priorityを使用する。

---

### C03｜Cyber Idol Style

| 項目 | 内容 |
| --- | --- |
| Status | Official Costume |
| Role | Alternate Official Costume |
| Category | Stage / Idol |
| Form | 少女ヤクモ / Standard Form |
| Current Version | **v1.1** |
| Specification | `YAKUMO_Costume_C03_Cyber_Idol_v1.1.md` |
| Costume Reference | `YAKUMO_C03_Cyber_Idol_Reference_v1.0.png` |
| Notes | 黒×ピンクを核に、白フリルと限定的なゴールドを加えた左右非対称のステージ衣装。C01-Bを置換しない。 |

C03 v1.1では、衣装デザインを変更せず、Visual Bible v1.3およびMONY v2.0体系へのReference Migrationを完了している。

C03に定義されたMONY Motif、Stage Effect、Stage Integration等の衣装固有要素はC03仕様書を使用する。

MONY本人の現行造形・Expression・Operational Stateは、本Registry第8節およびC03 v1.1のReference Priorityを使用する。

保留中のC03 Redesign Conceptは、現行Official Costumeには反映しない。

---

## 5｜Status Definitions

| Status | 意味 | 制作での扱い |
| --- | --- | --- |
| **Official Costume** | 正式採用済みの衣装 | 通常制作で指定・使用可能 |
| **Candidate** | 正式採用を検討中 | Candidate指定時のみ使用。Officialとして扱わない |
| **Concept** | 初期アイデア | 検討・発展用。設定の正解として扱わない |
| **Variation** | 既存衣装の範囲内の派生 | 元衣装を置換せず、指定された作品でのみ使用 |
| **Test** | 再現性や表現を確認する試作 | Official資料へ自動反映しない |
| **Archived** | 現行では使用しない旧版・旧衣装 | 履歴確認用。最新版より優先しない |

新しいアイデアは、ユーザーが「正式採用」「Officialにする」等を明示するまでは、Candidate、Concept、VariationまたはTestとして登録する。

---

## 6｜ID and Naming Rules

### Costume ID

- 新しい独立衣装は、既存のOfficial / Candidate / Concept等で使用済みのCostume IDを確認し、**次の未使用C番号**を採番する
- 現在の次期採番候補は **`C04`**
- 一度使用したIDを、別の衣装へ再利用しない
- `C01-B`は既存Default Costumeの正式IDとして維持する
- C02およびC03も既存Official Costume IDとして維持する
- 単なる配色差や小物差は、原則として新しいC番号ではなくVariationとして管理する
- シルエット、用途、主要構造が独立している場合に新しいC番号を付与する

### Specification Filename

```text
YAKUMO_Costume_CNN_Short_Name_vMAJOR.MINOR.md
```

### Reference Filename

```text
YAKUMO_CNN_Short_Name_Reference_vMAJOR.MINOR.png
```

### Examples

```text
YAKUMO_Costume_C02_Cyber_Beach_v1.1.md
YAKUMO_C02_Cyber_Beach_Reference_v1.0.png
YAKUMO_Costume_C03_Cyber_Idol_v1.1.md
YAKUMO_C03_Cyber_Idol_Reference_v1.0.png
YAKUMO_Costume_C04_[Short_Name]_v1.0.md
```

---

## 7｜Version Management

- Registryは衣装の追加、Status変更、最新版の変更、共通参照体系の更新があったときに更新する
- 個別衣装の内容変更は、その衣装の仕様書側でバージョン管理する
- 軽微な説明追加や許容Variationの拡張はMINOR更新とする
- Reference Migrationや現行Versionの更新反映もMINOR更新として扱える
- シルエット、主要構造、必須モチーフ等の再設計はMAJOR更新とする
- 旧版は履歴として保持し、現行版と競合する旧仕様を復活させない
- Registryには各衣装の**現在有効な最新版だけ**を掲載する
- Default Costumeの変更は、ユーザーが明示的に正式採用した場合にのみ行う

Registryのバージョンは、衣装自体の追加だけでなく、Visual Bible、Master、MONY等の共通参照基準や、各Costume Specificationの現行版が変更され、Registryの運用上の意味が変化する場合にもMINOR更新できる。

今回のv1.3は、

> **C02 / C03 Reference Migration Completion Update**

として扱う。

衣装そのもののデザイン変更ではない。

---

## 8｜Reference Priority

衣装を使用する際は、対象ごとに以下を優先する。

### 8.1｜YAKUMO本人

1. `YAKUMO_Master_v2.0.png`
2. `YAKUMO_Visual_Bible_v1.3.md`
3. 各衣装仕様書

YAKUMO本人の顔、髪、身体比率、年齢感等を衣装に合わせて再設計しない。

---

### 8.2｜衣装

1. 本Registryで指定された現行の個別衣装仕様書
2. 当該衣装のOfficial Costume Reference
3. 制作ごとの演出指定

現在の個別衣装仕様書：

- C02 → `YAKUMO_Costume_C02_Cyber_Beach_v1.1.md`
- C03 → `YAKUMO_Costume_C03_Cyber_Idol_v1.1.md`

衣装の構造、左右非対称性、`89`、アクセサリー等については、対象衣装の仕様書を優先する。

---

### 8.3｜人格・世界観

1. `YAKUMO Character Bible v1.2.md`
2. 用途別の公式運用資料

衣装変更によってYAKUMOまたはMONYの人格・関係性を変更しない。

---

### 8.4｜MONY

MONYについては、対象ごとに役割を分ける。

**人格・役割・YAKUMOとの関係性**

1. `YAKUMO Character Bible v1.2.md`

**MONY固有のVisual Design / Expression System / Operational State**

1. `MONY v2.0 Specification v1.0 Official.md`
2. `YAKUMO_Visual_Bible_v1.3.md`

**MONY本体の実際の造形**

1. `MONY_Master_v2.0.png`

**Face Displayの具体的な形状**

1. `MONY_Expression_Reference_v1.0.png`

**衣装固有のMONY accessory / motif / stage effect**

1. 該当する各Costume Specification

衣装固有要素を適用しても、

- MONY本体のサイズ関係
- 球体シルエット
- Rabbit Antenna
- Face Display領域
- Side Communication Ring
- `89`の主要配置
- Digital Hovering Fin
- Bottom Hovering System
- BLACK × NEON PINK
- ウサギ型デジタル端末としてのIdentity

等の現行Visual Coreを不用意に変更しない。

`MONY_Master_v1.0.png`は、

> **Legacy / Archived Reference**

として扱い、現行MONYの造形基準には使用しない。

Visual Bible v1.3でもMONY Master v1.0はLegacy / Archivedとされ、現行造形にはMaster v2.0を使用する体系になっています。

---

### 8.5｜C02 / C03 Current MONY Integration

C02 v1.1およびC03 v1.1は、いずれもMONY v2.0体系へのReference Migrationを完了している。

したがって、v1.2まで存在した、

> C02 / C03の旧仕様書に残る`MONY_Master_v1.0.png`をRegistry側で暫定的に上書きする

という移行措置は、v1.3では不要とする。

現在は各Costume Specification自身が、MONYについて以下を直接参照する。

- `MONY v2.0 Specification v1.0 Official.md`
- `MONY_Master_v2.0.png`
- `MONY_Expression_Reference_v1.0.png`
- `YAKUMO_Visual_Bible_v1.3.md`

C02 / C03でMONYが登場する場合は、Registryによる暫定補正ではなく、**各v1.1 Specificationに定義された現行Reference Priorityを直接使用する。**

C02 v1.1ではMONY v2.0とFloat Ringの役割分離まで完了しています。  
C03 v1.1でもMONY v2.0とStage Effect / Motifの役割分離が完了しています。

---

### 8.6｜Special State

HACKING MODEはCostumeではない。

`YAKUMO HACKING MODE Specification v1.1 Official`は、

> **Special State / Hacking**

として衣装とは別レイヤーで管理する。

したがって、

- Costume IDを割り当てない
- Official Costume Indexへ登録しない
- C01-B、C02、C03を置き換えない

HACKING MODEは、

```text
C01-B + HACKING MODE
C02 + HACKING MODE
C03 + HACKING MODE
```

のように、選択されたCostumeへ重ねて適用できる。

HACKING MODE適用時の状態変化については、

`YAKUMO HACKING MODE Specification v1.1 Official`

を使用する。

HACKING MODE v1.1ではMONYもOperational State `HACKING SYNC`として扱われ、別形態へ再設計しないことが明確化されています。

---

### Reference Role Summary

> **Registry = どの衣装を使うか**  
> **Costume Specification = その衣装が何であるか**  
> **Costume Reference = その衣装を着た作例／構造確認資料**  
> **YAKUMO Master = YAKUMO本人がどう見えるか**  
> **Visual Bible = YAKUMO / MONYのVisual Rule**  
> **MONY Specification = MONY固有のVisual / Expression / Operational Rule**  
> **MONY Master = MONY本人がどう見えるか**  
> **MONY Expression Reference = MONYのFace Displayがどう見えるか**  
> **Special State Specification = 衣装とは別レイヤーの状態変化**

---

## 9｜Recommended Directory Structure

```text
YAKUMO/
├─ YAKUMO Character Bible v1.2.md
├─ YAKUMO_Visual_Bible_v1.3.md
├─ YAKUMO X Prompt v1.4.md
│
├─ Official Masters/
│  ├─ YAKUMO_Master_v2.0.png
│  ├─ MONY_Master_v2.0.png
│  └─ MONY_Expression_Reference_v1.0.png
│
├─ MONY/
│  └─ MONY v2.0 Specification v1.0 Official.md
│
├─ SPECIAL_STATES/
│  └─ YAKUMO HACKING MODE Specification v1.1 Official.md
│
├─ COSTUMES/
│  ├─ YAKUMO_Costume_Registry_v1.3.md
│  │
│  ├─ C01-B/
│  │  └─ references/
│  │
│  ├─ C02/
│  │  ├─ YAKUMO_Costume_C02_Cyber_Beach_v1.1.md
│  │  └─ references/
│  │     └─ YAKUMO_C02_Cyber_Beach_Reference_v1.0.png
│  │
│  ├─ C03/
│  │  ├─ YAKUMO_Costume_C03_Cyber_Idol_v1.1.md
│  │  └─ references/
│  │     └─ YAKUMO_C03_Cyber_Idol_Reference_v1.0.png
│  │
│  └─ archive/
│     ├─ YAKUMO_Costume_C02_Cyber_Beach_v1.0.md
│     ├─ YAKUMO_Costume_C03_Cyber_Idol_v1.0.md
│     └─ YAKUMO_Costume_Registry_v1.2.md
│
└─ archive/
   ├─ MONY_Master_v1.0.png
   └─ ...
```

このDirectory Structureは推奨例である。

実際の保存場所がフラット構成の場合でも、ファイル名とRegistry上の参照名が明確であれば運用できる。

既存Official資料を無理に移動する必要はない。

---

## 10｜Adding a New Costume

新衣装を追加するときは、次の順序で管理する。

1. 既存衣装との重複とVisual Coreへの整合性を確認する
2. 次の未使用C番号を割り当てる
3. CandidateまたはConceptとして個別仕様書を作る
4. 必要に応じてReference画像を作る
5. YAKUMO本人が`YAKUMO_Master_v2.0.png`および`YAKUMO_Visual_Bible_v1.3.md`と整合していることを確認する
6. MONYを使用する場合はMONY v2.0の現行Official体系と整合していることを確認する
7. Special Stateを併用する場合は該当するOfficial Special State Specificationとのレイヤー分離を確認する
8. ユーザーが正式採用を明示する
9. StatusをOfficial Costumeへ更新する
10. 本RegistryのOfficial Costume Indexへ追加する
11. Change Logへ登録内容を記録する

新衣装を追加しても、Default Costumeは自動変更しない。

---

# Version Information

| 項目 | 内容 |
| --- | --- |
| Document | **YAKUMO Costume Registry** |
| Version | **1.3** |
| Status | **Official Index** |
| Character | **YAKUMO** |
| Standard Form | **少女ヤクモ** |
| Default Costume | **C01-B Cyber Pleats Style / Standard Form** |
| Registered Official Costumes | **3** |
| C02 Current Version | **v1.1** |
| C03 Current Version | **v1.1** |
| YAKUMO Visual Bible | `YAKUMO_Visual_Bible_v1.3.md` |
| YAKUMO Visual Master | `YAKUMO_Master_v2.0.png` |
| MONY Specification | `MONY v2.0 Specification v1.0 Official.md` |
| MONY Visual Master | `MONY_Master_v2.0.png` |
| MONY Expression Reference | `MONY_Expression_Reference_v1.0.png` |
| Special State Reference | `YAKUMO HACKING MODE Specification v1.1 Official` |
| Legacy MONY Master | `MONY_Master_v1.0.png` — Legacy / Archived |

---

## v1.2 → v1.3 Change Log

- Registry Versionを**v1.2からv1.3へ更新**
- 本更新を**C02 / C03 Reference Migration Completion Update**として定義
- C02のCurrent Versionを**v1.0からv1.1へ更新**
- C02 Specification参照を`YAKUMO_Costume_C02_Cyber_Beach_v1.1.md`へ更新
- C03のCurrent Versionを**v1.0からv1.1へ更新**
- C03 Specification参照を`YAKUMO_Costume_C03_Cyber_Idol_v1.1.md`へ更新
- C02 / C03のOfficial Costume Reference画像はv1.0を継続使用
- C02 / C03のCostume Design、Status、Category、Form、Default指定は変更なし
- C02 / C03のMONY v2.0 Reference Migration完了をRegistryへ反映
- v1.2に存在した「C02 / C03 v1.0の旧MONY参照をRegistry側で暫定補正する」移行措置を終了
- C02 / C03では各v1.1 Specification自身のMONY Reference Priorityを直接使用する体系へ移行
- MONYの現行Visual Masterとして`MONY_Master_v2.0.png`を継続使用
- `MONY_Master_v1.0.png`をLegacy / Archived Referenceとして継続
- `MONY v2.0 Specification v1.0 Official.md`をMONY固有仕様の現行Authorityとして継続
- `MONY_Expression_Reference_v1.0.png`をFace Displayの現行Authorityとして継続
- `YAKUMO_Visual_Bible_v1.3.md`を共通Visual Ruleとして継続
- `YAKUMO HACKING MODE Specification v1.1 Official`をSpecial State Referenceとして継続
- Recommended Directory StructureをRegistry v1.3、C02 v1.1、C03 v1.1へ更新
- C02 v1.0 / C03 v1.0 / Registry v1.2をarchive例へ移行
- Costume ID採番規則を固定的な`C04, C05...`表現から、**次の未使用C番号を採番する運用ルール**へ改善
- 現在の次期採番候補を`C04`として明記
- Adding a New CostumeへSpecial Stateとのレイヤー分離確認を追加
- **Registered Official Costumesは3着のまま変更なし**
- **Default CostumeはC01-B Cyber Pleats Style / Standard Formのまま変更なし**
- **新規Costume IDの追加なし**
- **C03 Redesign ConceptのOfficial反映なし**
- **既存衣装デザインの変更なし**

---

## v1.1 → v1.2 Change Log

- Registryの共通Visual参照を`YAKUMO_Visual_Bible_v1.2.md`から`YAKUMO_Visual_Bible_v1.3.md`へ更新
- C01-BのSpecification参照をVisual Bible v1.3へ更新
- YAKUMO本人の造形基準として`YAKUMO_Master_v2.0.png`を継続使用
- MONYの現行Visual Masterを`MONY_Master_v1.0.png`から`MONY_Master_v2.0.png`へ更新
- `MONY_Master_v1.0.png`をLegacy / Archived Referenceへ移行
- `MONY v2.0 Specification v1.0 Official.md`をMONY固有のVisual Design、Expression System、Operational Stateの基準として追加
- `MONY_Expression_Reference_v1.0.png`をFace DisplayのOfficial Expression Referenceとして追加
- MONYの人格・役割、Visual Design、実際の造形、Face Display、Costume固有Accessoryの参照役割を分離
- MONY v2.0のVisual Coreを衣装変更時にも維持する方針を明文化
- C02 / C03の旧MONY Master参照が現行MONY造形を上書きしないことを明文化
- C02 / C03におけるCostume固有Accessory / Motif / Stage Effectは既存v1.0仕様を維持
- C02 / C03自身のCostume Design、Status、Version、Reference画像には変更なし
- HACKING MODE v1.1をSpecial Stateとして整理し、Costume RegistryのOfficial Costume Indexへ追加しないことを明文化
- HACKING MODEをC01-B / C02 / C03へ別レイヤーとして組み合わせられることを明記
- Recommended Directory StructureのRegistry名を`YAKUMO_Costume_Registry_v1.2.md`へ更新
- Recommended Directory StructureへMONY v2.0およびSpecial Stateの管理例を追加
- Adding a New Costume手順へVisual Bible v1.3およびMONY v2.0との整合性確認を追加
- Registered Official Costumesは3着のまま変更なし
- Default CostumeはC01-B Cyber Pleats Style / Standard Formのまま変更なし
- 新規Costume IDの追加なし
- 既存衣装のデザイン変更なし

---

## v1.1 Change Log

- C03 Cyber Idol Style v1.0をOfficial Costumeとして登録
- C03のCategoryをStage / Idol、Formを少女ヤクモ / Standard Formとして登録
- C03仕様書およびOfficial Costume Referenceへの参照を追加
- Registry v1.0を履歴用archiveへ移行

---

## v1.0 Change Log

- YAKUMOの衣装を一元管理するCostume Registryを新設
- C01-B Cyber Pleats StyleをDefault Costumeとして登録
- C02 Cyber Beach Style v1.0をOfficial Costumeとして登録
- Costume ID、Status、命名、バージョンおよび追加手順を定義
- Costume指定がない場合はC01-Bを使用する選択ルールを明文化

---

**End of Official Registry**

---
