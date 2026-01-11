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
| 18 | エージェントの信頼性向上・評価基盤 | 🔵 未着手 | 高 | 精度検証、自動テスト、LLM評価 |
| 18 | Career Knowledge Base (詳細経歴DB) | 🔵 未着手 | 高 | 詳細情報の構造化、数値の推計ロジック |
| 19 | Portfolio & Agent Showcase | ✅ 完了 (FR-PF01) | 高 | エージェント機能のWeb統合 (Stage 1完了) |
| 20 | Recruiting Advantage Features | 🔵 未着手 | 中 | Tech Radar, CI/CD強化 |
| 21 | Automated Portfolio Generation | 🔵 未着手 | 中 | コード解析によるドキュメント/ポートフォリオ自動生成 |

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


### 18. エージェントの信頼性向上・評価基盤 (Agent Reliability & Evaluation)

**優先度**: 高
**目的**: 現在のAIエージェントによるレビューや修正が、期待通り適切に行われているかを定量的・客観的に検証する仕組みを構築する。

#### 背景
現状、エージェントの出力（職務経歴書の修正内容など）が適切であるかの自動テストが存在せず、品質が保証されていない。一般的なNLP/LLM評価手法を導入し、改善サイクルを回せるようにする。

#### 機能要件
1. **ゴールデンデータセットの作成** (FR-AGE01)
   - 正解となる修正例やレビューコメントのセットを作成
2. **LLM評価の導入 (LLM-as-a-Judge)** (FR-AGE02)
   - Ragas や LangSmith 等を活用し、エージェントの修正内容を別のLLMが客観的に評価する仕組みの構築
3. **エージェントノードのユニットテスト** (FR-AGE03)
   - LangGraph の各ノード（State遷移、ツール呼び出し）に対する Jest/Pytest による自動テストの実装
4. **回帰テストパイプライン** (FR-AGE04)
   - プロンプト変更時に、全体の出力品質が低下していないかを確認する評価ジョブのCI統合


### 15. Career Knowledge Base (詳細職務経歴書)

**優先度**: 高
**目的**: 職務経歴書(Resume)より詳細な、"情報の引き出し"としての職務経歴詳細データベースを構築する。記憶の曖昧さを補完し、面談時の質疑応答精度を高める。

#### 機能要件

1.  **詳細経歴コンテンツの構造化** (FR-CKB01)
    -   `resume-ja.qmd` よりも粒度の細かいデータスキーマの定義 (Astro Content Collections想定)
    -   必須フィールド: `context`, `problem`, `solution`, `tech_stack`, `metrics`, `metrics_estimation_method`
2.  **個別プロジェクト詳細ページ** (FR-CKB02)
    -   Webサイト上でプロジェクトごとの詳細ページ (`/career/[projectId]`) を生成
3.  **指標値の推計・復元ワークフロー** (FR-CKB03)
    -   過去の数値実績が曖昧な項目について、論理的な推計ロジックを記録するセクションを設ける ("Quantitative Proxy Analysis")

### 16. Portfolio & Agent Showcase

**優先度**: 高
**目的**: 書類上の経験不足(Agent開発, LLM統合, MLOps)を補完するため、本リポジトリ内のコードそのものをポートフォリオとして機能させる。

#### 機能要件

1.  **Agent Toolsの公式化** (FR-PF01)
    -   `packages/resume-review` を主要ポートフォリオとして位置づけ
    -   アーキテクチャ解説ページを作成 (LangGraph, State Management, Tool Use)
2.  **Living Portfolio (AIチャットボット)** (FR-PF02)
    -   Webサイト上に `resume-review` エージェントを埋め込み、訪問者が経歴について質問できるインターフェースを提供

### 17. Recruiting Advantage Features

**優先度**: 中
**目的**: 採用担当者やエンジニアに対して、技術力(設計力、品質管理)をアピールするための機能群を追加する。

#### 機能要件

1.  **Interactive Tech Radar** (FR-RA01)
    -   スキル一覧をただのリストではなく、クリックして使用プロジェクトを確認できるインタラクティブな可視化として実装
2.  **Design & Architecture as Code** (FR-RA02)
    -   `specs/` ディレクトリの整備状況自体を、SPEC駆動開発の実践例としてアピールできるようドキュメント化
3.  **Automated Quality Gates** (FR-RA03)
    -   CI/CDパイプライン(GitHub Actions)を強化し、MLOps/DevOpsの実践能力を可視化 (Strict Linting, Testing, Auto-Documentation)




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
