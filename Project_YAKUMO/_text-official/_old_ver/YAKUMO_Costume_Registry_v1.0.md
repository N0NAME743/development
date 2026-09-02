# YAKUMO Costume Registry

> 本書は、YAKUMOの公式衣装・候補衣装・派生衣装を一覧管理する衣装目録である。  
> 衣装を選択するときは本書を入口とし、具体的な構造・配色・装飾は各衣装の個別仕様書および公式参照画像で確認する。

---

## 1｜Registry Information

| 項目 | 内容 |
| --- | --- |
| Document | **YAKUMO Costume Registry** |
| Version | **1.0** |
| Status | **Official Index** |
| Character | **YAKUMO** |
| Standard Form | **少女ヤクモ** |
| Default Costume | **C01-B Cyber Pleats Style / Standard Form** |
| Costume ID Format | **C + 2桁以上の連番／既存派生記号** |

本書は衣装の詳細設定を複製しない。各衣装の存在、状態、用途、最新版、参照先およびDefault指定のみを管理する。

---

## 2｜Official Costume Index

| ID | Official Name | Status | Category | Form | Current Version / Authority | Default |
| --- | --- | --- | --- | --- | --- | --- |
| **C01-B** | **Cyber Pleats Style** | Official Costume | Default / Cyber Street | 少女ヤクモ / Standard Form | `YAKUMO_Visual_Bible_v1.2.md` / `YAKUMO_Master_v2.0.png` | **Yes** |
| **C02** | **Cyber Beach Style** | Official Costume | Summer / Swimwear | 少女ヤクモ / Standard Form | `YAKUMO_Costume_C02_Cyber_Beach_v1.0.md` | No |

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

→ Official CostumeのCyber Beach Styleを使用する。

衣装を切り替えても、YAKUMO本人の顔・髪・身体・Visual Coreは別人化させない。顔と身体造形は `YAKUMO_Master_v2.0.png`、共通の視覚ルールは `YAKUMO_Visual_Bible_v1.2.md` を優先する。

---

## 4｜Costume Records

### C01-B｜Cyber Pleats Style

| 項目 | 内容 |
| --- | --- |
| Status | Official Costume |
| Role | **Default Costume** |
| Category | Default / Cyber Street |
| Form | 少女ヤクモ / Standard Form |
| Specification | `YAKUMO_Visual_Bible_v1.2.md` |
| Official Visual Reference | `YAKUMO_Master_v2.0.png` |
| Notes | 指定がない場合に使用。C02以降の追加によって置換しない。 |

### C02｜Cyber Beach Style

| 項目 | 内容 |
| --- | --- |
| Status | Official Costume |
| Role | Alternate Official Costume |
| Category | Summer / Swimwear |
| Form | 少女ヤクモ / Standard Form |
| Current Version | v1.0 |
| Specification | `YAKUMO_Costume_C02_Cyber_Beach_v1.0.md` |
| Costume Reference | `YAKUMO_C02_Cyber_Beach_Reference_v1.0.png` |
| Notes | 黒主体のスポーティーなセパレート水着。C01-Bを置換しない。 |

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

- 新しい独立衣装は `C03`、`C04`、`C05`……の順で採番する
- 一度使用したIDを、別の衣装へ再利用しない
- `C01-B`は既存Default Costumeの正式IDとして維持する
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
YAKUMO_Costume_C02_Cyber_Beach_v1.0.md
YAKUMO_C02_Cyber_Beach_Reference_v1.0.png
YAKUMO_Costume_C03_[Short_Name]_v1.0.md
```

---

## 7｜Version Management

- Registryは衣装の追加、Status変更、最新版の変更があったときに更新する
- 個別衣装の内容変更は、その衣装の仕様書側でバージョン管理する
- 軽微な説明追加や許容Variationの拡張はMINOR更新とする
- シルエット、主要構造、必須モチーフ等の再設計はMAJOR更新とする
- 旧版は履歴として保持し、現行版と競合する旧仕様を復活させない
- Registryには各衣装の**現在有効な最新版だけ**を掲載する
- Default Costumeの変更は、ユーザーが明示的に正式採用した場合にのみ行う

Registryのバージョンは、衣装の追加やStatus／Default変更など、目録の意味が変わる更新時に上げる。

---

## 8｜Reference Priority

衣装を使用する際は、対象ごとに以下を優先する。

### YAKUMO本人

1. `YAKUMO_Master_v2.0.png`
2. `YAKUMO_Visual_Bible_v1.2.md`
3. 各衣装仕様書

### 衣装

1. 本Registryで指定された現行の個別衣装仕様書
2. 当該衣装のOfficial Costume Reference
3. 制作ごとの演出指定

### 人格・世界観

1. `YAKUMO Character Bible v1.1.md`
2. 用途別の公式運用資料

### MONY

1. `MONY_Master_v1.0.png`
2. Character Bible / Visual Bibleのモニィ定義
3. 各衣装仕様書に定義された季節アクセサリー

> **Registry = どの衣装を使うか**  
> **Costume Specification = その衣装が何であるか**  
> **Costume Reference = その衣装を着た作例**  
> **YAKUMO Master = YAKUMO本人がどう見えるか**

---

## 9｜Recommended Directory Structure

```text
COSTUMES/
├─ YAKUMO_Costume_Registry_v1.0.md
├─ C01-B/
│  └─ references/
├─ C02/
│  ├─ YAKUMO_Costume_C02_Cyber_Beach_v1.0.md
│  └─ references/
│     └─ YAKUMO_C02_Cyber_Beach_Reference_v1.0.png
├─ C03/
│  └─ ...
└─ archive/
   └─ ...
```

実際の保存場所がフラット構成の場合でも、ファイル名とRegistry上の参照名が一致していれば運用できる。既存Official資料を無理に移動せず、今後追加する衣装から段階的に整理してよい。

---

## 10｜Adding a New Costume

新衣装を追加するときは、次の順序で管理する。

1. 既存衣装との重複とVisual Coreへの整合性を確認する
2. 次の未使用C番号を割り当てる
3. CandidateまたはConceptとして個別仕様書を作る
4. 必要に応じてReference画像を作る
5. ユーザーが正式採用を明示する
6. StatusをOfficial Costumeへ更新する
7. 本RegistryのOfficial Costume Indexへ追加する
8. Change Logへ登録内容を記録する

新衣装を追加しても、Default Costumeは自動変更しない。

---

## Version Information

- Document：YAKUMO Costume Registry
- Version：1.0
- Status：Official Index
- Character：YAKUMO
- Standard Form：少女ヤクモ
- Default Costume：C01-B Cyber Pleats Style / Standard Form
- Registered Official Costumes：2

---

## v1.0 Change Log

- YAKUMOの衣装を一元管理するCostume Registryを新設
- C01-B Cyber Pleats StyleをDefault Costumeとして登録
- C02 Cyber Beach Style v1.0をOfficial Costumeとして登録
- Costume ID、Status、命名、バージョンおよび追加手順を定義
- Costume指定がない場合はC01-Bを使用する選択ルールを明文化
