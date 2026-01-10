# 開発ロードマップ

**最終更新**: 2026-01-10

---

## ステータスサマリー

| # | 機能 | ステータス | 優先度 | 備考 |
|---|------|-----------|--------|------|
| 12 | デザイン自動修正機能 | 🔵 未着手 | 低 | CSS自動生成、セクション順序調整 |
| 13 | ReviewState Pydantic化 | 🔵 未着手 | 中 | TypedDict → BaseModel |
| 14 | Webサイトのデザイン修正 | 🔵 未着手 | 中 | 左側余白の調整、モバイル対応等 |

---

## 未着手機能

### 12. デザイン自動修正機能 (Design Auto Fix)

**優先度**: 低
**目的**: デザインレビューのフィードバックを自動的に適用し、視覚的品質を向上

#### 背景

デザインレビュー機能は「フィードバックのみ」を提供:
- UX Designer: 情報設計の評価
- Visual Designer: 視覚表現の評価

フィードバックは出力されるが、**修正は手動で行う必要がある**。

#### 機能要件

1. **CSS 自動生成・適用** (FR-D01)
   - 余白調整、フォントサイズ調整、コントラスト改善
   - `styles/resume-custom.css` を生成

2. **セクション順序の自動調整** (FR-D02)
   - 重要セクションを上部に移動
   - YAML frontmatterは変更しない

3. **Quarto テーマ推奨** (FR-D03)
   - 問題パターンに応じた最適テーマを提案

4. **インタラクティブプレビュー** (FR-D04)
   - 修正前後の比較プレビュー

#### 実装フェーズ

1. Phase 1: CSS自動生成 (CSSGeneratorAgent)
2. Phase 2: セクション順序最適化
3. Phase 3: テーマ推奨
4. Phase 4: プレビュー機能

#### 関連ファイル (予定)

```
packages/resume-review/src/
├── agents/design/
│   ├── css_generator.py
│   ├── section_analyzer.py
│   └── theme_recommender.py
├── models/design.py
└── services/
    ├── css_applier.py
    └── section_reorderer.py
```

---

### 13. ReviewState Pydantic リファクタリング

**優先度**: 中
**目的**: LangGraph Studio でのデフォルト入力サポートと型安全性の向上

#### 背景

現在の `ReviewState` は `TypedDict` で定義されているため:

1. **デフォルト値が設定できない**: Studio から実行時に全フィールドを手動入力する必要がある
2. **バリデーションがない**: 不正な値が渡されてもランタイムまでエラーが発生しない
3. **シリアライズが手動**: JSON との相互変換に追加コードが必要

#### 提案する変更

**Before: TypedDict**
```python
class ReviewState(TypedDict, total=False):
    resume: Resume
    target_role: str
    score_threshold: float
    # ...
```

**After: Pydantic BaseModel**
```python
class ReviewState(BaseModel):
    resume: Resume
    target_role: str = "LLM/Multi-Agent Engineer"
    score_threshold: float = Field(default=8.0, ge=0, le=10)
    max_iterations: int = Field(default=3, ge=1)
    dry_run: bool = False
    # ...
```

#### 期待される効果

| 項目 | Before | After |
|------|--------|-------|
| デフォルト値 | ❌ 不可 | ✅ 可能 |
| バリデーション | ❌ なし | ✅ 自動 |
| Studio での UX | 全フィールド入力必須 | 必須のみ入力 |

#### 実装フェーズ

1. Phase 1: State の Pydantic 化
2. Phase 2: ノード関数の更新 (`state["key"]` → `state.key`)
3. Phase 3: テストの更新

---

### 14. Webサイトのデザイン修正 (Web Design Fix)

**優先度**: 中
**目的**: 履歴書表示サイトのレイアウトを改善し、視覚的なバランスを整える

#### 背景

現在のWeb表示において、左側の余白が極端に大きく、全体のコンテンツバランスが崩れている（特に広いディスプレイ環境）。

#### 修正内容

1. **左側レイアウトの調整** (FR-W01)
   - サイドバーが不要な場合のレイアウト最適化
   - メインコンテンツの最大幅とマージンの見直し
2. **レスポンシブ対応の強化** (FR-W02)
   - モバイル・タブレット環境での最適な余白設定
3. **テーマ設定の最適化** (FR-W03)
   - `nextra-theme-docs` のレイアウトパターンの再検討

---

### 完了済み機能

→ [archive/future-specs-2026-01.md](archive/future-specs-2026-01.md) を参照

| # | 機能 | 完了日 | specs フォルダ |
|---|------|--------|---------------|
| 1 | StateGraph エージェントノード分離 | 2026-01-10 | `specs/011-stategraph-node-separation/` |
| 2 | 求人パーソナライズ機能 | 2026-01-09 | `specs/010-job-personalization/` |
| 3 | モノレポリファクタリング | 2026-01-08 | `specs/002-monorepo-refactor/` |
| 4 | マルチモデル・ハイブリッド構成 | 2026-01-09 | `specs/003-multi-model-hybrid/` |
| 6 | 構造検証・自動修復機能 | 2026-01-09 | (組み込み) |
| 7 | Quarto構文検証機能 | 2026-01-09 | (組み込み) |
| 8 | Quarto検証失敗時の自動リトライ | 2026-01-09 | `specs/009-quarto-retry-loop/` |

---

## ドキュメントガバナンス

### ドキュメントカテゴリ

| カテゴリ | 配置場所 | 目的 | 備考 |
|---------|---------|------|------|
| **ガイド** | ルート直下 | 開発者向け指示・規約 | `README.md`, `CLAUDE.md` |
| **ロードマップ** | `docs/roadmap.md` | 開発計画・ステータス | |
| **機能仕様** | `specs/{NNN}-{name}/` | 開発中機能の詳細設計 | 完了後は `contracts/` 以外アーカイブ扱い |
| **パッケージDoc** | `packages/*/README.md`| パッケージの使い方 | |
| **コンテンツ** | `resume/` | 履歴書ソース(Product) | `resume-ja.qmd` が正本 |
| **メタデータ** | `.specify/` | プロジェクト管理テンプレート | 開発プロセスを定義 |

### コンテンツガバナンス (Resume)

1. **正本 (Single Source of Truth)**
   - `resume/resume-ja.qmd` が唯一の正本です。
   - 内容の修正は必ずこのファイルに対して行ってください。

2. **生成ファイル (Generated Artifacts)**
   - 以下のファイルは `pnpm resume:build` または `pnpm sync` で自動生成されます。手動編集しないでください。
     - `packages/web/pages/ja/index.mdx`
     - `resume/output/*.pdf`
     - `resume/output/*.html`

3. **一時ファイル**
   - `resume/review_*/` ディレクトリはAIレビューの実行ログです。Gitにはコミットされません（`.gitignore` 設定済み）。

### 新機能追加時のルール

1. `docs/roadmap.md` に概要を追記
2. `specs/{NNN}-{name}/` に詳細仕様を作成
   - 必須: `spec.md`, `plan.md`, `tasks.md`
   - 任意: `data-model.md`, `research.md`, `quickstart.md`, `contracts/`
3. 完了後、`CLAUDE.md` に要点を反映
4. `docs/roadmap.md` のステータスを更新
