# 開発ロードマップ

**最終更新**: 2026-01-11

---

## ステータスサマリー

| # | 機能 | ステータス | 優先度 | 備考 |
|---|------|-----------|--------|------|
| 14 | Webサイトのデザイン刷新(Astro移行) | ✅ 完了 | 中 | Astro 5 + TailwindCSS 4 |
| 15 | Slidev統合 (プレゼンスライド) | 🔵 未着手 | 低 | |
| 16 | 多言語対応 (i18n) | 🔵 未着手 | 中 | |
| 17 | データ視覚化 (Timeline/Charts) | 🔵 未着手 | 中 | |

---

## 未着手機能

### 15. Slidev統合 (Presentation Slides)

**優先度**: 低
**目的**: 職務経歴書の内容からSlidevを使用してプレゼンテーションスライドを自動生成・表示する

#### 機能要件
1. `packages/web` 内に Slidev を統合
2. `resume-ja.qmd` または構造化データからスライド用マークダウンを生成
3. Webサイト上でスライドとして閲覧可能にする


### 16. 多言語対応の強化 (Multi-language Support)

**優先度**: 中
**目的**: Astroサイトを多言語（日本語・英語）に完全対応させる

#### 機能要件
1. Astroのi18n機能を活用したルーティング (`/ja`, `/en`)
2. 英語版 `resume-en.qmd` の作成と同期フローの構築
3. 言語切り替えスイッチのUI実装


### 17. タイムライン・視覚化機能の強化 (Data Visualization)

**優先度**: 中
**目的**: 経歴やスキルセットをチャートやタイムラインで視覚的に表示する

#### 機能要件
1. Shadcn UI / Tremor 等を利用したグラフ表示
2. インタラクティブな職歴タイムラインの構築
3. スキルマトリックスのレーダーチャート表示


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
| 14 | Webサイトのデザイン刷新 (Astro移行) | 2026-01-11 | `specs/014-astro-migration/` |

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
