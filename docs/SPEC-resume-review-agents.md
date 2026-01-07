# 仕様書: Resume Review Multi-Agent System

## 1. 概要

| 項目 | 内容 |
|------|------|
| 目的 | 職務経歴書のコンテンツとデザインを自動レビュー・修正し、高単価案件（110〜140万円/月）獲得を支援 |
| 実行環境 | ローカルのみ（CLI） |
| 入力 | QMDファイル（`public/assets/resume-ja.qmd`） |
| 出力 | 修正済みQMD + PDF + HTML + MDX |
| 統合方式 | Monorepo（既存resume/配下にagents/を追加） |

---

## 2. ターゲット定義

| 項目 | 内容 |
|------|------|
| **目標単価** | 110〜140万円/月 |
| **目標時期** | 2025年Q1中 |
| **ターゲット職種** | LLM/マルチエージェントエンジニア |
| **リモート率** | フルリモート優先 |

### 単価帯別 必須スキル（市場調査より）

| 単価帯 | 必須スキル |
|--------|-----------|
| 100〜120万円 | LangGraph、Vector DB、LLMOps（LangSmith/LangFuse）、Fine-tuning経験 |
| 120万円+ | MLOps、大規模分散環境、LLMサービング最適化（vLLM/TGI）、チームリード |

### 高単価案件向け必須キーワード

- LangGraph / LangChain
- RAG / Vector DB（Qdrant, Pinecone, Chroma）
- LangSmith / LangFuse
- Fine-tuning（LoRA, QLoRA, PEFT）
- MLOps（MLflow, Kubeflow）
- Vertex AI / SageMaker / Bedrock

---

## 3. ポートフォリオ補完方針

### 基本方針

**実務経験にないスキルは、ポートフォリオで補完する（完成済み前提）**

- エージェントは不足スキルを検出したら、対応するポートフォリオを提案
- ポートフォリオは即座に作成可能（バイブコーディング + 経験により高速実装）
- Revisorはポートフォリオセクションにリンクを追加

### 命名規則

| 項目 | 値 |
|------|-----|
| 基本形式 | `{技術}-{種類}` |
| GitHub URL | `https://github.com/spin-glass/{repo-name}` |
| Demo URL | `https://{repo-name}.spin-glass.dev/` |

**命名パターン（LLMが一貫した名前を生成するためのガイド）**:

| パターン | 用途 | 例 |
|---------|------|-----|
| `{技術}-{用途}` | 特定用途のデモ | `langgraph-multi-agent` |
| `{技術}-{ユースケース}` | ユースケース実装 | `rag-evaluation-pipeline` |
| `{技術}-demo` | シンプルなデモ | `graphrag-demo` |
| `{技術}-benchmark` | ベンチマーク・比較 | `vllm-benchmark` |
| `{技術}-example` | チュートリアル的実装 | `lora-finetuning-example` |

### ポートフォリオ生成例

| 不足スキル | リポジトリ名 | GitHub | Demo |
|-----------|-------------|--------|------|
| LangGraph/Multi-Agent | `langgraph-multi-agent` | `https://github.com/spin-glass/langgraph-multi-agent` | `https://langgraph-multi-agent.spin-glass.dev/` |
| RAG評価パイプライン | `rag-evaluation-pipeline` | `https://github.com/spin-glass/rag-evaluation-pipeline` | `https://rag-evaluation-pipeline.spin-glass.dev/` |
| GraphRAG | `graphrag-demo` | `https://github.com/spin-glass/graphrag-demo` | `https://graphrag-demo.spin-glass.dev/` |
| LLMサービング | `vllm-benchmark` | `https://github.com/spin-glass/vllm-benchmark` | `https://vllm-benchmark.spin-glass.dev/` |
| Fine-tuning | `lora-finetuning-example` | `https://github.com/spin-glass/lora-finetuning-example` | `https://lora-finetuning-example.spin-glass.dev/` |

---

## 4. ディレクトリ構成

```
resume/
├── pages/
│   └── ja/
│       └── index.mdx              # Web用（QMDから自動生成）
├── public/
│   └── assets/
│       ├── resume-ja.qmd          # ★ ソースファイル（レビュー対象）
│       ├── resume-ja.pdf          # PDF出力
│       ├── resume-ja.html         # HTML出力
│       └── header.tex             # LaTeXヘッダー
├── scripts/
│   └── sync_qmd_to_mdx.py         # QMD→MDX変換
├── agents/                        # 【新規】Python agents
│   ├── src/
│   │   ├── __init__.py
│   │   ├── cli.py                 # CLIエントリーポイント
│   │   ├── graph.py               # LangGraphワークフロー
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── evaluators.py      # 評価エージェント
│   │   │   ├── reviewers.py       # 統合レビュアー
│   │   │   └── revisors.py        # 修正エージェント
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── state.py           # 状態定義
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── screenshot.py      # スクリーンショット取得
│   │       └── qmd.py             # QMDパース・出力
│   ├── tests/
│   │   └── test_graph.py
│   ├── pyproject.toml
│   └── README.md
├── docs/
│   └── SPEC-resume-review-agents.md
├── package.json                   # npm scripts定義
├── resume.pdf                     # ルートのPDF（コピー）
└── .env                           # ANTHROPIC_API_KEY
```

---

## 5. CLI インターフェース

### 5.1 コマンド

```bash
# 基本実行
cd resume/agents
python -m src.cli review --input ../public/assets/resume-ja.qmd

# オプション付き
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --output ../public/assets/resume-ja.qmd \
  --target-role "生成AI/LLMエンジニア" \
  --screenshot-url "http://localhost:3000/ja" \
  --max-iterations 3 \
  --threshold 8.0 \
  --dry-run
```

### 5.2 オプション一覧

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--input` | path | 必須 | 入力QMDファイルパス |
| `--output` | path | 入力と同じ | 出力QMDファイルパス |
| `--target-role` | string | "生成AI/LLMエンジニア" | ターゲット職種 |
| `--screenshot-url` | url | None | スクリーンショット取得URL |
| `--max-iterations` | int | 3 | 最大イテレーション数 |
| `--threshold` | float | 8.0 | 通過スコア閾値 |
| `--dry-run` | flag | False | 修正を適用せず結果のみ表示 |
| `--verbose` | flag | False | 詳細ログ出力 |

### 5.3 出力例

```
$ python -m src.cli review --input ../public/assets/resume-ja.qmd --verbose

🚀 Resume Review System Starting...

📄 Input: ../public/assets/resume-ja.qmd (2,847 chars)
🎯 Target Role: 生成AI/LLMエンジニア
📸 Screenshot: Capturing http://localhost:3000/ja ...

═══════════════════════════════════════════════════════════
 CONTENT PHASE
═══════════════════════════════════════════════════════════

── Iteration 1/3 ──────────────────────────────────────────

[Recruiter]      Score: 6/10
  ✓ MLOps経験が明確
  ✗ タグラインがない
  ✗ RAG経験が目立たない
  ✗ LangGraph経験なし → ポートフォリオ追加: langgraph-multi-agent

[TechWriter]     Score: 7/10
  ✓ 技術スタックが具体的
  ✗ STAR形式が不完全
  ✗ 数値化が不足

[Copywriter]     Score: 5/10
  ✗ フックが弱い
  ✗ 差別化ポイントが不明確

[Reviewer]       Integrated Score: 6.0/10
  Priority Issues:
  1. [HIGH] タグラインの追加
  2. [HIGH] RAG経験の前面化
  3. [HIGH] ポートフォリオ追加: langgraph-multi-agent
  4. [MEDIUM] 成果の数値化

[Revisor]        Applying revisions...
  ✓ Added tagline
  ✓ Moved RAG project to prominent position
  ✓ Added portfolio: langgraph-multi-agent
      GitHub: https://github.com/spin-glass/langgraph-multi-agent
      Demo: https://langgraph-multi-agent.spin-glass.dev/

── Iteration 2/3 ──────────────────────────────────────────

...

═══════════════════════════════════════════════════════════
 SUMMARY
═══════════════════════════════════════════════════════════

✅ Review Complete!

Content Phase:  6.0 → 8.0 (3 iterations)
Design Phase:   6.5 → 8.0 (2 iterations)

📝 Changes Applied:
  1. Added tagline: "LLM/RAGを活用した推薦システムの設計から運用まで"
  2. Moved RAG project from side work to main experience
  3. Added portfolio section:
     - langgraph-multi-agent (LangGraph, Multi-Agent)
     - rag-evaluation-pipeline (RAG, LangFuse)
  4. Added metrics: CTR improvement 15%, processing time -40%
  5. Restructured skills into categories (実務/ポートフォリオ)

📄 Output: ../public/assets/resume-ja.qmd (3,412 chars)

🔨 Portfolio to create:
  - langgraph-multi-agent
  - rag-evaluation-pipeline

Next Steps:
  $ npm run resume:build   # Generate PDF/HTML/MDX
  $ npm run dev            # Preview changes
```

---

## 6. 状態定義

```python
# agents/src/models/state.py

from typing import TypedDict, Literal, Annotated
import operator


class PortfolioItem(TypedDict):
    repo_name: str                          # e.g., "langgraph-multi-agent"
    skills: list[str]                       # e.g., ["LangGraph", "Multi-Agent"]
    github_url: str                         # auto-generated
    demo_url: str                           # auto-generated


class Issue(TypedDict):
    description: str
    action_type: Literal["add_content", "add_portfolio", "restructure", "emphasize"]
    suggestion: str
    portfolio: PortfolioItem | None         # add_portfolioの場合のみ


class Feedback(TypedDict):
    agent: str
    score: int                              # 1-10
    strengths: list[str]
    issues: list[Issue]                     # Issue オブジェクトのリスト
    priority: Literal["high", "medium", "low"]


class ReviewerOutput(TypedDict):
    integrated_score: float
    priority_issues: list[Issue]            # 統合されたIssueリスト
    portfolios_to_add: list[PortfolioItem]  # 追加すべきポートフォリオ（重複排除済み）
    passed: bool


class ResumeReviewState(TypedDict):
    # === Configuration ===
    target_role: str
    max_iterations: int
    threshold: float
    screenshot_url: str | None
    
    # === Input ===
    original_content: str
    
    # === Current State ===
    current_content: str
    current_screenshot: str | None          # base64
    phase: Literal["content", "design"]
    iteration: int
    
    # === Feedbacks (per iteration, reset each iteration) ===
    current_feedbacks: list[Feedback]
    
    # === Reviewer Output ===
    reviewer_output: ReviewerOutput | None
    
    # === Portfolio tracking (append-only) ===
    added_portfolios: Annotated[list[PortfolioItem], operator.add]  # reducer追加
    
    # === History (append-only) ===
    revision_history: Annotated[list[dict], operator.add]
    # {phase, iteration, changes: list[str], before_score, after_score}
    
    # === Phase Results ===
    content_final_score: float | None
    content_iterations: int | None
    design_final_score: float | None
    design_iterations: int | None
    
    # === Output ===
    final_content: str
    summary: str
```

---

## 7. エージェント仕様

### 7.1 Recruiter（採用担当）

**ペルソナ**: LLM/マルチエージェント案件を発注する企業の採用担当・PM

**Input**: `current_content`, `target_role`

**基本方針**: 
- 高単価案件（100万円+）の要件を基準に評価
- **実務経験がないスキルは「ポートフォリオで補完」として提案**（ポートフォリオは完成済み前提）

| 観点 | 説明 | チェック項目 |
|------|------|-------------|
| **即戦力性** | すぐに稼働できるか | LangGraph/LangChain実務経験、RAG構築経験の有無 |
| **スキルマッチ** | 100万円+案件の要件を満たすか | LangGraph、Vector DB、LLMOps、Fine-tuning の記載 |
| **市場希少性** | 差別化できるスキルがあるか | vLLM/TGI、MLOps（MLflow/Kubeflow）、大規模環境経験 |
| **リード経験** | 120万円+に必要な要素 | チームリード、アーキテクチャ設計、技術選定の実績 |
| **本番経験** | PoC止まりでないか | 評価パイプライン、運用、監視の経験 |
| **ポートフォリオ補完** | 不足スキルの補完状況 | 必要なポートフォリオが記載されているか |

**スコア基準**:

| スコア | 基準 |
|--------|------|
| 9-10 | 120万円+案件に即アサイン可能（実務 + ポートフォリオで網羅） |
| 7-8 | 100〜120万円案件に適合 |
| 5-6 | 80〜100万円案件レベル |
| 3-4 | エントリーレベル（〜80万円） |
| 1-2 | LLM/マルチエージェント案件に不適合 |

**Output形式**:

```json
{
  "score": 6,
  "strengths": [
    "MLOps（Vertex AI Pipelines）の実務経験が明確",
    "RAG案件の本番経験あり"
  ],
  "issues": [
    {
      "description": "LangGraph/Multi-Agent経験が記載されていない",
      "action_type": "add_portfolio",
      "portfolio": {
        "repo_name": "langgraph-multi-agent",
        "skills": ["LangGraph", "Multi-Agent", "Claude API"]
      },
      "suggestion": "ポートフォリオセクションにlanggraph-multi-agentを追加"
    },
    {
      "description": "タグラインがない",
      "action_type": "add_content",
      "suggestion": "冒頭に専門性を示す一言を追加"
    }
  ],
  "priority": "high"
}
```

**action_type の種類**:

| action_type | 説明 | Revisorの対応 |
|-------------|------|--------------|
| `add_content` | 既存経験を元に追記可能 | テキストを追加・修正 |
| `add_portfolio` | 実務経験がない → ポートフォリオで補完 | ポートフォリオセクションにリンク追加 |
| `restructure` | 構造・配置の変更 | セクション移動・再構成 |
| `emphasize` | 既存内容の強調 | 表現の強化、位置の変更 |

---

### 7.2 TechWriter（テクニカルライター）

**ペルソナ**: 技術責任者が面談前に確認する視点

**Input**: `current_content`

| 観点 | 説明 | チェック項目 |
|------|------|-------------|
| **技術深度** | 表面的でなく深い理解が伝わるか | アーキテクチャ選定理由、トレードオフの記述 |
| **STAR形式** | 課題→行動→結果の流れ | 各プロジェクトで「なぜ」「どう解決」「結果」が明確 |
| **数値化** | 成果が定量的か | CTR改善率、レイテンシ短縮、コスト削減の具体値 |
| **スケール感** | 大規模環境の経験が伝わるか | データ量、リクエスト数、チーム規模の記載 |
| **技術選定力** | 比較検討した経験があるか | 「〇〇と比較して△△を採用」の記述 |
| **最新技術** | 2024年以降のトレンドを押さえているか | LangGraph、GraphRAG、vLLM等の言及 |

**スコア基準**:

| スコア | 基準 |
|--------|------|
| 9-10 | 技術ブログとして公開できるレベル |
| 7-8 | 技術責任者が納得する詳細さ |
| 5-6 | 内容は伝わるが深さが不足 |
| 3-4 | 表面的、具体性に欠ける |
| 1-2 | 技術的に不正確または曖昧 |

**Output形式**:

```json
{
  "score": 7,
  "strengths": [
    "技術スタックが具体的に記載されている",
    "Two-Tower Architectureの実装詳細が明確"
  ],
  "issues": [
    {
      "description": "STAR形式が不完全（結果の数値化が不足）",
      "action_type": "add_content",
      "suggestion": "CTR改善率、処理時間短縮などの具体的数値を追加"
    }
  ],
  "priority": "medium"
}
```

---

### 7.3 Copywriter（コピーライター）

**ペルソナ**: 多数の候補者から選ぶ採用担当の「最初の10秒」

**Input**: `current_content`, `target_role`

| 観点 | 説明 | チェック項目 |
|------|------|-------------|
| **タグライン** | 一言で専門性が伝わるか | 冒頭3行以内に差別化された一言 |
| **ポジショニング** | 100万円+エンジニアとして認識されるか | シニア感、リード経験、戦略的視点 |
| **希少性** | 「この人しかいない」感 | 推薦システム×LLMの組み合わせ、業界特化 |
| **フック** | 最初の3行で興味を引けるか | 具体的数字、ユニークな経験、インパクト |
| **ストーリー** | キャリアの一貫性 | 推薦システム→LLM/RAGへの自然な流れ |
| **CTA** | ポートフォリオへの導線 | GitHubリンク、デモリンクの明示 |

**タグライン例**:

```
❌ 弱い: MLエンジニア / データサイエンティスト
△ 普通: LLM/RAGエンジニア
✅ 強い: 推薦システム×LLMで、設計から本番運用まで一気通貫
✅ 強い: LangGraphでマルチエージェント基盤を構築するMLエンジニア
```

**スコア基準**:

| スコア | 基準 |
|--------|------|
| 9-10 | 「この人と話したい」と即座に思わせる |
| 7-8 | 印象に残り、他候補者と差別化されている |
| 5-6 | 無難だが埋もれる可能性 |
| 3-4 | 平凡、100万円+のシニア感がない |
| 1-2 | ターゲット層に響かない |

**Output形式**:

```json
{
  "score": 5,
  "strengths": [
    "技術的な深さは伝わる"
  ],
  "issues": [
    {
      "description": "タグラインがない",
      "action_type": "add_content",
      "suggestion": "冒頭に「推薦システム×LLMで、設計から本番運用まで」のような一言を追加"
    },
    {
      "description": "ポートフォリオへの導線がない",
      "action_type": "add_portfolio",
      "portfolio": {
        "repo_name": "rag-evaluation-pipeline",
        "skills": ["RAG", "LangFuse", "Ragas"]
      },
      "suggestion": "CTAとしてポートフォリオセクションを追加"
    }
  ],
  "priority": "high"
}
```

---

### 7.4 UX Designer（UXデザイナー）

**ペルソナ**: 5分で候補者を評価したい技術責任者

**Input**: `current_screenshot`

| 観点 | 説明 | チェック項目 |
|------|------|-------------|
| **ファーストビュー** | スクロールなしで何が伝わるか | タグライン、主要スキル、代表実績 |
| **ポートフォリオ導線** | デモへのアクセスしやすさ | リンクの視認性、クリックしやすさ |
| **スキル可視化** | 技術スタックが一目でわかるか | カテゴリ分け（LLM/MLOps/Cloud等） |
| **情報階層** | 重要情報が上部にあるか | 高単価案件向けスキルの配置順序 |
| **スキャナビリティ** | 30秒で要点が把握できるか | 見出しの明確さ、キーワードの視認性 |
| **CTA** | 次のアクションが明確か | 連絡先、GitHubリンク、デモリンク |

**ファーストビュー必須要素**:
1. タグライン（一言で専門性）
2. 主要スキル（LangGraph, RAG, MLOps）
3. 代表的な実績数字（例: CTR +15%、3つの本番システム）
4. ポートフォリオCTA（デモへのリンク）

**スコア基準**:

| スコア | 基準 |
|--------|------|
| 9-10 | 5秒で「100万円+エンジニア」と認識される |
| 7-8 | 重要情報にすぐアクセスできる |
| 5-6 | 情報はあるが探す必要がある |
| 3-4 | 構造が不明確、迷う |
| 1-2 | 何者かわからない |

**Output形式**:

```json
{
  "score": 6,
  "strengths": [
    "情報階層は概ね適切"
  ],
  "issues": [
    {
      "description": "ファーストビューの情報密度が低い",
      "action_type": "restructure",
      "suggestion": "冒頭にタグライン、主要スキル、代表実績数字を集約"
    },
    {
      "description": "ポートフォリオへのリンクが目立たない",
      "action_type": "emphasize",
      "suggestion": "ポートフォリオセクションを上部に移動、リンクを強調"
    }
  ],
  "priority": "high"
}
```

---

### 7.5 Visual Designer（ビジュアルデザイナー）

**ペルソナ**: プロフェッショナルな印象を求める採用担当

**Input**: `current_screenshot`

| 観点 | 説明 | チェック項目 |
|------|------|-------------|
| **プロフェッショナル感** | シニアエンジニアに相応しい印象か | 落ち着いた色使い、洗練されたレイアウト |
| **視覚的階層** | 重要情報が目立つか | スキル、実績数字、CTAの強調 |
| **タイポグラフィ** | 読みやすく信頼感があるか | フォント選択、サイズ階層、行間 |
| **余白** | 情報が詰まりすぎていないか | セクション間の余白、呼吸感 |
| **一貫性** | デザインルールが統一されているか | 色、装飾、アイコンスタイル |
| **差別化** | 他の職務経歴書と視覚的に差別化されているか | ユニークな要素 |

**スコア基準**:

| スコア | 基準 |
|--------|------|
| 9-10 | デザイン自体がスキルの証明になる |
| 7-8 | プロフェッショナルで好印象 |
| 5-6 | 無難だが印象に残らない |
| 3-4 | デザインがマイナス要因 |
| 1-2 | 信頼性を損なう見た目 |

**Output形式**:

```json
{
  "score": 7,
  "strengths": [
    "クリーンなレイアウト",
    "タイポグラフィが読みやすい"
  ],
  "issues": [
    {
      "description": "視覚的な強調が不足",
      "action_type": "emphasize",
      "suggestion": "スキルセクションの視認性を向上、キーワードの強調"
    }
  ],
  "priority": "medium"
}
```

---

### 7.6 統合レビュアー（Reviewer）

**Input**: `current_feedbacks: list[Feedback]`

**処理**:
1. 各エージェントのスコアを重み付き平均
2. issuesをaction_type別に分類
3. **ポートフォリオ提案を集約・重複排除**
4. 優先度でソート・統合
5. 通過判定（`integrated_score >= threshold`）

**重み付け**:

| Agent | 重み | 理由 |
|-------|------|------|
| Recruiter | 30% | 高単価案件要件とのマッチ度が最重要 |
| Copywriter | 25% | 第一印象・差別化が案件獲得に直結 |
| TechWriter | 20% | 技術的信頼性の担保 |
| UX Designer | 15% | 情報到達性 |
| Visual Designer | 10% | 印象の補強 |

**Output**:

```json
{
  "integrated_score": 6.2,
  "priority_issues": [
    {
      "priority": "high",
      "description": "タグラインがない",
      "suggestion": "冒頭に一言で専門性を示す文を追加",
      "action_type": "add_content",
      "source_agents": ["Recruiter", "Copywriter"]
    },
    {
      "priority": "high",
      "description": "LangGraph/Multi-Agent経験が記載されていない",
      "suggestion": "ポートフォリオセクションにlanggraph-multi-agentを追加",
      "action_type": "add_portfolio",
      "source_agents": ["Recruiter"]
    },
    {
      "priority": "medium",
      "description": "成果の数値化が不足",
      "suggestion": "CTR改善率などの具体的数値を追加",
      "action_type": "add_content",
      "source_agents": ["TechWriter"]
    }
  ],
  "portfolios_to_add": [
    {
      "repo_name": "langgraph-multi-agent",
      "skills": ["LangGraph", "Multi-Agent", "Claude API"],
      "github_url": "https://github.com/spin-glass/langgraph-multi-agent",
      "demo_url": "https://langgraph-multi-agent.spin-glass.dev/"
    },
    {
      "repo_name": "rag-evaluation-pipeline",
      "skills": ["RAG", "LangFuse", "Ragas"],
      "github_url": "https://github.com/spin-glass/rag-evaluation-pipeline",
      "demo_url": "https://rag-evaluation-pipeline.spin-glass.dev/"
    }
  ],
  "passed": false
}
```

---

### 7.7 修正エージェント（Revisor）

**Input**: `current_content`, `priority_issues`, `portfolios_to_add`, `phase`

**修正ルール**:

| action_type | Revisorの対応 | 例 |
|-------------|--------------|-----|
| `add_content` | 既存経験を元にテキスト追加・修正 | タグライン追加、数値化 |
| `add_portfolio` | ポートフォリオセクションにリンク追加 | GitHub/Demoリンク追加 |
| `restructure` | セクション移動・再構成 | RAG案件を職務経歴に昇格 |
| `emphasize` | 表現の強化、位置の変更 | キーワード強調、上位移動 |

**絶対にやらないこと**:
- 実務経験がないスキルを「実務経験」として追記する（嘘になる）
- 存在しない成果を捏造する

**ポートフォリオセクションのテンプレート**:

```markdown
---

## ポートフォリオ

| プロジェクト | 技術スタック | リンク |
|-------------|-------------|--------|
| langgraph-multi-agent | LangGraph, Multi-Agent, Claude API | [GitHub](https://github.com/spin-glass/langgraph-multi-agent) / [Demo](https://langgraph-multi-agent.spin-glass.dev/) |
| rag-evaluation-pipeline | RAG, LangFuse, Ragas | [GitHub](https://github.com/spin-glass/rag-evaluation-pipeline) / [Demo](https://rag-evaluation-pipeline.spin-glass.dev/) |
```

**URL生成ルール**:

```python
def generate_portfolio_urls(repo_name: str) -> tuple[str, str]:
    github_url = f"https://github.com/spin-glass/{repo_name}"
    demo_url = f"https://{repo_name}.spin-glass.dev/"
    return github_url, demo_url
```

**Output**:

```json
{
  "revised_content": "...(修正後のQMD)...",
  "changes": [
    {
      "action_type": "add_content",
      "description": "Added tagline at the beginning"
    },
    {
      "action_type": "add_portfolio",
      "description": "Added portfolio: langgraph-multi-agent",
      "portfolio": {
        "repo_name": "langgraph-multi-agent",
        "github_url": "https://github.com/spin-glass/langgraph-multi-agent",
        "demo_url": "https://langgraph-multi-agent.spin-glass.dev/"
      }
    },
    {
      "action_type": "restructure",
      "description": "Moved RAG project from side work to main experience"
    }
  ],
  "added_portfolios": [
    {
      "repo_name": "langgraph-multi-agent",
      "skills": ["LangGraph", "Multi-Agent", "Claude API"],
      "github_url": "https://github.com/spin-glass/langgraph-multi-agent",
      "demo_url": "https://langgraph-multi-agent.spin-glass.dev/"
    }
  ]
}
```

**制約**:
- High優先度のissueから順に対応
- 1イテレーションで最大3つのissueに対応
- 元の内容を大幅に変えない（追加・移動・強調が主）
- QMDのYAMLフロントマターは保持する

---

## 8. ワークフロー仕様

### 8.1 フロー図

```
START
  │
  ▼
[Initialize]
  │ phase = "content"
  │ iteration = 0
  │ current_content = original_content
  │ added_portfolios = []
  │
  ▼
┌─────────────────────────────────────┐
│         CONTENT LOOP                │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ iteration += 1              │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│                ▼                    │
│  ┌─────────────────────────────┐   │
│  │ Content Evaluators (並列)   │   │
│  │ [Recruiter, TechWriter,     │   │
│  │  Copywriter]                │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│                ▼                    │
│  ┌─────────────────────────────┐   │
│  │ Content Reviewer            │   │
│  │ (ポートフォリオ提案を集約)    │   │
│  └─────────────┬───────────────┘   │
│                │                    │
│        ┌───────┴───────┐           │
│        ▼               ▼           │
│   [passed=true    [passed=false    │
│    OR iter>=max]   AND iter<max]   │
│        │               │           │
│        │               ▼           │
│        │    ┌─────────────────┐   │
│        │    │ Content Revisor │   │
│        │    │ (ポートフォリオ追加)│   │
│        │    └────────┬────────┘   │
│        │             │            │
│        │             └──────┐     │
│        ▼                    │     │
│   [Save Results]◀───────────┘     │
│                                    │
└─────────────────┬──────────────────┘
                  │
                  ▼
          [Generate HTML]
          (npm run quarto:html)
                  │
                  ▼
          [Take Screenshot]
          (Playwrightでキャプチャ)
                  │
                  ▼
┌─────────────────────────────────────┐
│         DESIGN LOOP                 │
│                                     │
│  (同様の構造)                        │
│  Evaluators: [UX, Visual]          │
│  Revisor: Design Revisor           │
│                                     │
│  ※修正後は再度HTML生成→スクリーンショット│
│                                     │
└─────────────────┬──────────────────┘
                  │
                  ▼
           [Summarize]
           (追加されたポートフォリオ一覧を出力)
                  │
                  ▼
                 END
```

### 8.2 並列実行の実装方針

Content Evaluators（Recruiter, TechWriter, Copywriter）は並列実行で高速化します。

| 方式 | 説明 | 採用 |
|------|------|------|
| `asyncio.gather` | 単一ノード内で3つのLLM呼び出しを並列実行 | ✅ 推奨 |
| LangGraph `Send` API | 各エージェントを並列ノードとして実行 | ○ 複雑だが柔軟 |
| 順次実行 | シンプルだが遅い | △ |

**実装例（asyncio.gather）**:

```python
async def content_evaluators_node(state: ResumeReviewState) -> dict:
    content = state["current_content"]
    target_role = state["target_role"]
    
    # 並列実行
    recruiter_task = recruiter_agent.ainvoke(content, target_role)
    techwriter_task = techwriter_agent.ainvoke(content)
    copywriter_task = copywriter_agent.ainvoke(content, target_role)
    
    feedbacks = await asyncio.gather(
        recruiter_task, 
        techwriter_task, 
        copywriter_task
    )
    
    return {"current_feedbacks": list(feedbacks)}
```

### 8.3 終了条件

| 条件 | Content Phase | Design Phase |
|------|--------------|--------------|
| スコア閾値達成 | `content_score >= threshold` | `design_score >= threshold` |
| 最大イテレーション | `iteration >= max_iterations` | `iteration >= max_iterations` |

両方のPhaseで、いずれかの条件を満たしたら次へ進む。

### 8.4 スクリーンショット取得タイミング

| タイミング | 条件 |
|-----------|------|
| Design Phase開始時 | 必須 |
| Design Loop各イテレーション | Revisorが修正を適用した後 |

**取得方法**:
1. `screenshot_url`が指定されている場合: Playwrightで取得
2. 指定されていない場合: Design Phaseをスキップ

---

## 9. npm scripts統合

```json
// package.json（scriptsセクション）
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "quarto:pdf": "cd public/assets && quarto render resume-ja.qmd --to pdf && cp resume-ja.pdf ../../resume.pdf",
    "quarto:html": "cd public/assets && quarto render resume-ja.qmd --to html",
    "quarto:preview": "cd public/assets && quarto preview resume-ja.qmd",
    "quarto:preview:html": "cd public/assets && quarto preview resume-ja.qmd --to html",
    "sync": "python3 scripts/sync_qmd_to_mdx.py",
    "resume:build": "npm run quarto:pdf && npm run quarto:html && npm run sync",
    "review": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd",
    "review:dry": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd --dry-run --verbose",
    "review:full": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd --screenshot-url http://localhost:3000/ja --verbose",
    "review:build": "npm run review && npm run resume:build"
  }
}
```

### npm scripts一覧

| コマンド | 説明 |
|---------|------|
| `npm run review` | エージェントによるレビュー実行 |
| `npm run review:dry` | ドライラン（変更なし、詳細出力） |
| `npm run review:full` | スクリーンショット付きフルレビュー |
| `npm run review:build` | レビュー + ビルド（PDF/HTML/MDX生成） |
| `npm run resume:build` | ビルドのみ（PDF/HTML/MDX生成） |
| `npm run quarto:preview:html` | HTMLプレビュー |
| `npm run dev` | Next.js開発サーバー |

---

## 10. 環境構築

### 10.1 必要なファイル

```toml
# agents/pyproject.toml

[project]
name = "resume-review-agents"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "langgraph>=0.2.0",
    "langchain-anthropic>=0.3.0",
    "playwright>=1.48.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.8.0",
]

[project.scripts]
resume-review = "src.cli:main"
```

### 10.2 セットアップ手順

```bash
# 1. Python環境作成
cd resume/agents
python -m venv .venv
source .venv/bin/activate

# 2. 依存関係インストール
pip install -e .

# 3. Playwright ブラウザインストール
playwright install chromium

# 4. 環境変数設定
cp .env.example .env
# ANTHROPIC_API_KEY を設定

# 5. 動作確認
python -m src.cli review --input ../public/assets/resume-ja.qmd --dry-run
```

---

## 11. 制約事項・注意点

| 項目 | 制約 |
|------|------|
| API コスト | 1回のフル実行で約 $0.50〜$1.00（イテレーション数による） |
| 実行時間 | 約2〜5分（ネットワーク状況による） |
| QMD互換性 | YAMLフロントマターは保持、本文のみ修正 |
| 破壊的変更 | `--dry-run`で事前確認を推奨 |
| スクリーンショット | ローカルでdev server起動が必要 |
| 実務経験の追加 | Revisorは存在しない実務経験を追加しない |
| ポートフォリオ | 完成済み前提で即座にリンク追加可能 |

---

## 12. 今後の拡張（対象外）

- Human-in-the-loop（承認フロー）
- LangFuse統合（トレーシング）
- Streamlit UI
- CI/CD統合
- 英語版対応