# Proposal: Gap-Driven Portfolio Workflow

**Target Feature**: 021-gap-driven-portfolio  
**Concept**: Resume Driven Development + Just-in-Time Portfolio Generation

## 概要

「募集要項（JD）に対して自身の経験（Resume）で不足しているスキル（ギャップ）を特定し、それを埋めるためのポートフォリオページを先行して生成・提示する」という新しいワークフローの提案。

従来の実績ベースのポートフォリオではなく、**「採用されるために必要な証拠を、オンデマンドで生成/発掘する」** という逆転のアプローチをとる。

## コア・コンセプト

1.  **Just-in-Time Proof**: 何年も前の実績ではなく、「今、その技術を使える」ことを示すデモやドキュメントを即座に提示する。
2.  **Asset Mining**: 自身の過去のコードベース（GitHub/Local）から、言及されていないが使える技術の証拠を発掘する。
3.  **Spec as a Portfolio**: 実装コードがなくても、詳細な「設計書」「技術選定理由」自体をポートフォリオとして提示し、アーキテクト能力を示す。

## 提案ワークフロー

```mermaid
graph TB
    Input[募集要項 & Resume] --> Analyzer[Gap Analysis Agent]
    
    Analyzer -->|不足スキル特定| Strategy{戦略立案}
    
    Strategy -->|Local/GitHubにコードあり| Miner[Code Miner Agent]
    Strategy -->|知見はあるがコードなし| Architect[Spec Builder Agent]
    Strategy -->|完全新規| Prototyper[PoC Builder Agent]
    
    Miner -->|リバースエンジニアリング| Generator[Portfolio Gen]
    Architect -->|設計ドキュメント作成| Generator
    Prototyper -->|ミニマル実装 & Docs| Generator
    
    Generator --> WebPage[ポートフォリオページ生成]
    WebPage --> Revisor[Resume Revisor]
    
    Revisor --> Output[最適化されたResume]
    
    subgraph "Output"
        Output -- リンク --> WebPage
    end
```

## エージェント構成案

### 1. Gap Analysis Agent
*   **役割**: JDとResumeの差分分析。
*   **入力**: JDテキスト, Resume (Markdown)
*   **動作**: 「必須要件: React」vs「Resume: Vue.js経験のみ」→ **GAP: React** を検出。
*   **出力**: `GapReport(skill="React", urgency="High", context="Frontend migration")`

### 2. Code Miner Agent (The Archaeologist)
*   **役割**: 埋蔵コードの発掘。
*   **動作**: ユーザーのローカル開発フォルダ (`~/dev`) や GitHub を検索。
*   **探索クエリ**: "import React", "package.json dependencies react"
*   **判定**: 「3年前に作った個人アプリでReactを使っている」→ 採用。

### 3. Spec Builder / Code Reviewer Agent (The Architect)
*   **役割**: 実装詳細の解説によりスキルを証明。
*   **動作**:
    *   **Minerルート**: 発掘したコードを読み込み、「なぜこの設計にしたか」「どういう技術的課題を解決したか」を言語化（今回のアーキテクチャ図生成と同じロジック）。
    *   **新規ルート**: コードがない場合でも、「もしこのJDのシステムを作るならこう設計する」という**Design Doc**を作成し、アーキテクトとしての能力を証明する。

### 4. Portfolio Page Generator
*   **役割**: MDXページの生成。
*   **テンプレート**:
    *   **Architecture Showcase**: アーキテクチャ図メイン（今回実装したもの）。
    *   **Proof of Concept**: 小さなデモとそのコード解説。
    *   **Technical Essay**: 特定技術に対する深い考察記事。

## ユーザー体験 (UX)

1.  **Trigger**: ユーザーが「この求人に応募したい」とURLを投げる。
2.  **Analysis**: システムが「ReactとGraphQLの経験記述が弱いです」と警告。
3.  **Suggestion**:
    *   「`~/dev/hobby/graphql-server` に過去のコードがあります。これをポートフォリオ化しますか？」
    *   「あるいは、React x GraphQL の設計ベストプラクティス記事を生成しますか？」
4.  **Action**: ユーザー承認後、数分で `/portfolio/graphql-architecture` が生成される。
5.  **Completion**: 職務経歴書の備考欄に「※GraphQLの実装能力については、[こちらのアーキテクチャ設計書](/portfolio/graphql-architecture)をご参照ください」と追記される。

## 実装フェーズへのロードマップ

1.  **Phase 1: Gap Analyzer (CLI)**
    *   JDとResumeを入力し、不足スキルをリストアップする単純なスクリプト。
2.  **Phase 2: Code Miner (Local Search)**
    *   `ripgrep` 等を使ってローカルのコード資産を検索し、要約するツール。
3.  **Phase 3: Integration**
    *   既存の `resume-review` パイプラインに組み込み、ポートフォリオ生成まで一気通貫で行う。
