# Portfolio & Agent Showcase Feature Specification

**Feature ID**: 019 (対応するroadmap項目: 16)  
**Status**: In Progress  
**Priority**: 高  
**Created**: 2026-01-11

---

## Overview

本リポジトリの`packages/resume-review`エージェントシステムを、採用担当者向けポートフォリオとして機能させる。書類上の経験不足（Agent開発、LLM統合、MLOps）を補完し、技術力を可視化する。

## Business Context

### Problem Statement
- 経歴書に「エージェント開発」「LLM統合」の実績が不足
- GitHubリポジトリが存在するが、採用担当者が技術力を把握しづらい
- AIエージェントの設計・実装能力が伝わりにくい

### Target Users
1. 採用担当者（技術理解度：中〜高）
2. 技術面接官（エンジニアリングマネージャー、テックリード）
3. ビジネスパートナー候補

### Success Criteria
- 採用担当者がWebサイト訪問後5分以内に技術スタックを理解できる
- アーキテクチャドキュメントから設計思想が明確に伝わる
- GitHubリポジトリへのトラフィックが増加

---

## Functional Requirements

### FR-PF01: Agent Tools の公式化

**目的**: `packages/resume-review`を主要ポートフォリオとして位置づけ、アーキテクチャと設計思想を明示する。

#### Requirements

1. **アーキテクチャドキュメント** (`packages/resume-review/docs/architecture.md`)
   - **内容**:
     - LangGraph StateGraph の活用法
     - Fan-out/Fan-in パターン（並列エージェント実行）
     - State Management（Pydantic 2.0使用）
     - Tool Use（マルチモデル設定、Playwright Screenshot等）
     - コスト最適化戦略（Claude単一利用から50%削減）
   - **形式**: Markdown（Mermaid図含む）
   - **サブセクション**:
     - System Architecture
     - State Management
     - Multi-Agent Orchestration
     - Cost Optimization
     - Tool Integration

2. **README更新** (`packages/resume-review/README.md`)
   - トップに「Portfolio Showcase」バッジセクション追加
   - アーキテクチャドキュメントへのリンク
   - 主要技術スタック一覧（視覚的に強調）

3. **Webポートフォリオページ** (`packages/web/src/pages/portfolio.mdx`)
   - プロジェクト概要（1-2パラグラフ）
   - 技術的ハイライト（箇条書き）
   - アーキテクチャ概要図（Mermaid）
   - GitHubリポジトリリンク
   - 詳細ページへのリンク

4. **アーキテクチャ詳細ページ** (`packages/web/src/pages/portfolio/architecture.mdx`)
   - `packages/resume-review/docs/architecture.md`をベースに作成
   - Astro + Tailwind CSSでスタイリング
   - インタラクティブな図（可能な範囲で）

### FR-PF02: Living Portfolio (Chatbot)

**Status**: Stage 2 で実装予定（後のPR）

**目的**: Webサイト上で訪問者がエージェントと対話し、経歴について質問できるインタラクティブな体験を提供する。

#### Requirements（参考）

1. **チャットインターフェース** (`packages/web/src/components/PortfolioChat.tsx`)
   - React コンポーネント（Astro統合）
   - メッセージ送受信UI
   - ストリーミング対応（逐次表示）

2. **サーバーレスAPI** (`packages/web/src/pages/api/chat.ts`)
   - Vercel Serverless Functions
   - LangGraph API または Python CLI直接呼び出し
   - 環境変数でAPIキー管理
   - レート制限実装

3. **Demoページ** (`packages/web/src/pages/portfolio/demo.astro`)
   - PortfolioChatコンポーネント埋め込み
   - 使い方説明
   - サンプル質問の提示

---

## Non-Functional Requirements

### NFR-01: Performance
- ポートフォリオページの初期ロード時間 < 3秒
- Mermaid図のレンダリング < 1秒

### NFR-02: SEO
- 各ページに適切な`<title>`と`<meta description>`
- Open Graph タグ設定（Twitter Card含む）

### NFR-03: Accessibility
- WCAG 2.1 AA準拠
- キーボードナビゲーション対応

### NFR-04: Responsive Design
- モバイル、タブレット、デスクトップ対応
- Tailwind CSSのresponsive utilities使用

---

## Technical Design

### Architecture Overview

```
packages/
├── resume-review/          # Pythonエージェントシステム
│   ├── docs/
│   │   └── architecture.md # 新規作成
│   └── README.md           # 更新
└── web/                    # Astro Webサイト
    └── src/
        ├── pages/
        │   ├── portfolio.mdx           # 新規作成
        │   └── portfolio/
        │       └── architecture.mdx    # 新規作成
        └── layouts/
            └── MainLayout.astro        # 更新（ナビゲーション追加）
```

### Technology Stack

- **Frontend**: Astro 5, Tailwind CSS 4, MDX
- **Documentation**: Markdown, Mermaid
- **Deployment**: Vercel (既存設定を利用)

---

## User Stories

### US-01: 採用担当者がアーキテクチャを理解する
**As a** 採用担当者  
**I want to** エージェントシステムのアーキテクチャを簡潔に理解したい  
**So that** 候補者の技術力を評価できる

**Acceptance Criteria**:
- ポートフォリオページにアクセスできる
- アーキテクチャ図が視覚的にわかりやすい
- 主要技術（LangGraph、Pydantic、Multi-LLM）が明記されている

### US-02: エンジニアが設計思想を深掘りする
**As a** 技術面接官  
**I want to** 詳細な設計ドキュメントを読みたい  
**So that** 候補者の設計能力を評価できる

**Acceptance Criteria**:
- アーキテクチャ詳細ページが存在する
- Fan-out/Fan-inパターンの説明がある
- コスト最適化の戦略が記載されている

---

## Out of Scope

以下は本featureの対象外（将来的に検討）：
- Living Portfolio Chatbot（Stage 2で実装）
- プロジェクトデモ動画の埋め込み
- インタラクティブなコード実行環境
- 詳細なパフォーマンスメトリクスダッシュボード

---

## Dependencies

- Feature 14: Astro Migration（完了済み）
- Existing: `packages/resume-review` README.md
- Existing: Astro navigation component

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mermaid図が複雑すぎて読みづらい | 中 | シンプルな図に分割、段階的表示 |
| ドキュメントが技術的すぎて採用担当者が理解できない | 高 | 各セクションに「Summary」を追加、専門用語に注釈 |
| ナビゲーション更新が他のページに影響 | 低 | 既存のMainLayout.astroを慎重に編集 |

---

## Acceptance Criteria

### AC-01: アーキテクチャドキュメント
- [ ] `packages/resume-review/docs/architecture.md` が作成されている
- [ ] LangGraph StateGraphの説明がある
- [ ] Mermaid図が含まれている
- [ ] コスト最適化セクションがある

### AC-02: Webポートフォリオページ
- [ ] `/portfolio` ページが表示される
- [ ] GitHub リポジトリへのリンクがある
- [ ] アーキテクチャ詳細ページへのリンクがある

### AC-03: アーキテクチャ詳細ページ
- [ ] `/portfolio/architecture` ページが表示される
- [ ] architecture.mdの内容が適切にレンダリングされている
- [ ] Tailwind CSSでスタイリングされている

### AC-04: ナビゲーション
- [ ] グローバルナビゲーションに「Portfolio」リンクが追加されている
- [ ] モバイルでも適切に表示される

---

## References

- [roadmap.md](../../docs/roadmap.md) - feature 16
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Astro Documentation](https://docs.astro.build/)
- [Mermaid Documentation](https://mermaid.js.org/)
