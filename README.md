# Resume & Portfolio

[![CI](https://github.com/spin-glass/resume/actions/workflows/ci.yml/badge.svg)](https://github.com/spin-glass/resume/actions/workflows/ci.yml)

職務経歴書とポートフォリオを管理するモノレポです。

## 🔗 Live Site

- **🌐 Resume (職務経歴書)**: [resume.spin-glass.dev](https://resume.spin-glass.dev/)
- **📁 Portfolio**: [resume.spin-glass.dev/portfolio](https://resume.spin-glass.dev/portfolio)

## ✨ Features

- **AI-Powered Resume Review**: LLMを活用した職務経歴書の自動レビュー・最適化
- **Multi-Format Export**: Quarto によるPDF/HTML生成
- **Automated PDF Generation**: GitHub Actions でPDFを自動生成・アーティファクト保存
- **Portfolio Showcase**: プロジェクト・技術スタックの可視化

## 📦 Repository Structure

```text
resume/                       # Monorepo root
├── packages/
│   ├── web/                 # Astro web application
│   │   └── src/pages/
│   │       ├── index.mdx    # 職務経歴書ページ
│   │       └── portfolio/   # ポートフォリオページ
│   └── resume-review/       # Python AI review tool (LangGraph)
├── resume/                  # Resume source files
│   ├── resume-ja.qmd       # Canonical resume source (Quarto)
│   └── output/             # Generated PDF/HTML
├── scripts/                 # Build and sync scripts
└── specs/                   # Feature specifications
```

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | Astro 5 |
| **Resume Source** | Quarto (QMD) |
| **PDF Generation** | LuaLaTeX / Puppeteer |
| **AI Review** | LangGraph + OpenAI GPT-4o |
| **Deployment** | Vercel |
| **CI/CD** | GitHub Actions |
| **Package Manager** | pnpm (Monorepo) |

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Preview resume (with hot reload)
pnpm quarto:preview:html
```

## 📋 Resume Update Workflow

1. **Edit**: `resume/resume-ja.qmd` を編集
2. **Preview**: `pnpm quarto:preview:html` でリアルタイムプレビュー
3. **Build**: `pnpm resume:build` でPDF/HTML/MDXを生成
4. **Review** (optional): `pnpm review` でAIレビューを実行
5. **Deploy**: `git push` → Vercelが自動デプロイ

## 📄 Commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Astro開発サーバー起動 |
| `pnpm build` | Webアプリビルド |
| `pnpm quarto:preview:html` | HTMLプレビュー（自動更新） |
| `pnpm quarto:pdf` | PDF生成 |
| `pnpm resume:build` | 全て生成（PDF/HTML/MDX） |
| `pnpm review` | AIレビュー実行 |
| `pnpm review:dry` | AIレビュー（ドライラン） |

## 🤖 AI Resume Review

`packages/resume-review` は LangGraph ベースのマルチエージェントシステムです：

- **Gap Analysis**: 求人要件と職務経歴のギャップ分析
- **Experience Reconciliation**: STAR形式での経験抽出・整理
- **Multi-Agent Optimization**: 複数エージェントによる最適化

```bash
# Run AI review with dry-run
pnpm review:dry

# Run full review with changes applied
pnpm review
```

## 📖 Requirements

- Node.js 22+
- pnpm 9+
- Python 3.13+
- Quarto CLI
- LuaLaTeX (TeX Live)

## 📝 License

MIT License - see [LICENSE](LICENSE)
