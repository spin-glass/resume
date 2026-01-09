# Resume Monorepo

This is the monorepo for my [resume](https://resume.spin-glass.dev/).

## Repository Structure

```text
resume/                      # Monorepo root
├── packages/
│   ├── web/                # Next.js/Nextra web application
│   └── resume-review/      # Python AI review tool
├── resume/                 # Resume source files
│   ├── resume-ja.qmd      # Canonical resume source
│   └── output/            # Generated PDF/HTML
└── scripts/               # Build and sync scripts
```

## Resume更新フロー

### 1. QMDファイルを編集

`resume/resume-ja.qmd` を編集します。

### 2. プレビューで確認

```bash
# HTMLプレビュー（推奨）
pnpm quarto:preview:html

# PDFプレビュー
pnpm quarto:preview
```

ブラウザが開き、ファイル保存時に自動更新されます。

### 3. ビルド（PDF/HTML/MDX生成）

```bash
pnpm resume:build
```

以下が実行されます：
- `resume/resume-ja.qmd` → `resume/output/resume-ja.pdf`
- `resume/resume-ja.qmd` → `resume/output/resume-ja.html`
- `resume/resume-ja.qmd` → `packages/web/pages/ja/index.mdx`

### 4. AIレビュー（オプション）

```bash
# ドライラン（変更プレビューのみ）
pnpm review:dry

# フルレビュー（変更適用）
pnpm review

# スクリーンショット付きフルレビュー
pnpm review:full
```

### 5. デプロイ

```bash
git add .
git commit -m "職務経歴を更新"
git push
```

Vercelが自動でデプロイします。

## コマンド一覧

すべてのコマンドはリポジトリルートから実行します。

| コマンド | 説明 |
|---------|------|
| `pnpm dev` | Next.js開発サーバー起動 |
| `pnpm build` | Webアプリビルド |
| `pnpm quarto:preview` | PDFプレビュー（自動更新） |
| `pnpm quarto:preview:html` | HTMLプレビュー（自動更新） |
| `pnpm quarto:pdf` | PDF生成 |
| `pnpm quarto:html` | HTML生成 |
| `pnpm sync` | QMD → MDX同期 |
| `pnpm resume:build` | 全て生成（PDF/HTML/MDX） |
| `pnpm review:dry` | AIレビュー（ドライラン） |
| `pnpm review` | AIレビュー実行 |
| `pnpm test:python` | Pythonテスト実行 |
| `pnpm lint:python` | Pythonリント実行 |

## 新規パッケージの追加

```bash
# 1. packages/ディレクトリにパッケージを作成
mkdir packages/new-package
cd packages/new-package

# 2. package.jsonを初期化
pnpm init

# 3. ルートからpnpm installを実行
cd ../..
pnpm install
```

pnpm-workspace.yamlは`packages/*`パターンを使用しているため、新規パッケージは自動的に認識されます。

## Requirements

- Node.js 22.x
- pnpm 9+
- Python 3.13+
- Quarto CLI
- LuaLaTeX (TeX Live)
- Japanese fonts (Hiragino Mincho Pro)
