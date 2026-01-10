# 開発ロードマップ

**最終更新**: 2026-01-10

---

## ステータスサマリー

| # | 機能 | ステータス | 優先度 | 備考 |
|---|------|-----------|--------|------|
| 12 | デザイン自動修正機能 | ✅ 完了 | 低 | CSS自動生成、セクション順序調整 |
| 13 | ReviewState Pydantic化 | ✅ 完了 | 中 | TypedDict → BaseModel |
| 14 | Webサイトのデザイン刷新(Astro移行) | 🔵 未着手 | 中 | astro-example参照、Astro5+TailwindCSS4 |

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

### 14. Webサイトのデザイン刷新 - Astro移行 (Web Design Overhaul)

**優先度**: 中
**目的**: 履歴書表示サイトをNextra/Next.jsからAstroベースに移行し、デザイン・パフォーマンスを大幅改善

#### 背景

現在のWeb表示において、左側の余白が極端に大きく、全体のコンテンツバランスが崩れている。
暫定対応として `--nextra-sidebar-width` を調整したが、根本的なデザイン刷新が必要。

#### 移行元リポジトリ

- **参照**: [spin-glass/astro-example](https://github.com/spin-glass/astro-example)
- **デモ**: https://spin-glass.github.io/astro-example/

#### 技術スタック（移行後）

| 項目 | 現在 | 移行後 |
|------|------|--------|
| フレームワーク | Next.js 14 + Nextra | Astro 5 |
| CSS | Tailwind CSS 3 | Tailwind CSS 4 |
| プレゼン | なし | Slidev |
| ブログ | なし | Quarto |
| PDF出力 | Quarto | Puppeteer |

#### 機能要件

1. **Astro移行** (FR-W01)
   - `packages/web` をAstroベースに再構築
   - 既存のmdxコンテンツをAstroに移行
2. **レイアウト最適化** (FR-W02)
   - サイドバーの廃止またはコンパクト化
   - メインコンテンツ中心のレイアウト
3. **レスポンシブ対応の強化** (FR-W03)
   - モバイル・タブレット環境での最適表示
4. **Slidev統合** (FR-W04) - 任意
   - プレゼンテーションスライドの追加



### 完了済み機能

→ [archive/future-specs-2026-01.md](archive/future-specs-2026-01.md) を参照

| # | 機能 | 完了日 | specs フォルダ |
|---|------|--------|---------------|
| 1 | StateGraph エージェントノード分離 | 2026-01-10 | `specs/011-stategraph-node-separation/` |
| 2 | 求人パーソナライズ機能 | 2026-01-09 | `specs/010-job-personalization/` |
| 3 | モノレポリファクタリング | 2026-01-08 | `specs/002-monorepo-refactor/` |
| 4 | マルチモデル・ハイブリッド構成 | 2026-01-09 | `specs/003-multi-model-hybrid/` |
| 5 | デザイン自動修正機能 | 2026-01-10 | (013-design-auto-fix) |
| 6 | 構造検証・自動修復機能 | 2026-01-09 | (組み込み) |
| 7 | Quarto構文検証機能 | 2026-01-09 | (組み込み) |
| 8 | Quarto検証失敗時の自動リトライ | 2026-01-09 | `specs/009-quarto-retry-loop/` |
| 9 | ReviewState Pydantic化 | 2026-01-10 | (feature/013-*) |

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
