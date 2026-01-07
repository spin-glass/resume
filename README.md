# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/)
This resume is developed by Next.js template [Nextra](https://nextra.site/)

## Resume更新フロー

### 1. QMDファイルを編集

`public/assets/resume-ja.qmd` を編集します。

### 2. プレビューで確認

```bash
# HTMLプレビュー（推奨）
npm run quarto:preview:html

# PDFプレビュー
npm run quarto:preview
```

ブラウザが開き、ファイル保存時に自動更新されます。

### 3. ビルド（PDF/HTML/MDX生成）

```bash
npm run resume:build
```

以下が実行されます：
- `resume-ja.qmd` → `resume-ja.pdf` / `resume.pdf`
- `resume-ja.qmd` → `resume-ja.html`
- `resume-ja.qmd` → `pages/ja/index.mdx`

### 4. デプロイ

```bash
git add .
git commit -m "職務経歴を更新"
git push
```

Vercelが自動でデプロイします。

## npm scripts一覧

| コマンド | 説明 |
|---------|------|
| `npm run quarto:preview` | PDFプレビュー（自動更新） |
| `npm run quarto:preview:html` | HTMLプレビュー（自動更新） |
| `npm run quarto:pdf` | PDF生成 |
| `npm run quarto:html` | HTML生成 |
| `npm run sync` | QMD → MDX同期 |
| `npm run resume:build` | 全て生成（PDF/HTML/MDX） |
| `npm run dev` | Next.js開発サーバー |

## Development Environment

```sh
pnpm run dev
```

## Requirements

- Quarto CLI
- LuaLaTeX (TeX Live)
- Japanese fonts (Hiragino Mincho Pro)
