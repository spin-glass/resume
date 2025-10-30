# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/)  
This resume is developed by Next.js template [Nextra](https://nextra.site/)

## Updating workflow

![workflow](./workflow.drawio.svg)

1. Update `pages/ja/index.mdx` in Japanese

2. Translate into English using [Crowdin](https://crowdin.com/profile/spin-glass)

3. After approving translation, execute `crowdin_sync_and_merge` workflow in [GitHub Actions](https://github.com/spin-glass/resume/actions) manually

## Quick Start

利用可能なタスク一覧を表示

```sh
task
```

## 主要タスク

### 開発

```sh
task dev    # 開発サーバーを起動
```

### PDF/DOCX生成

```sh
task generate    # PDF/DOCX両方を生成
task pdf         # PDFのみ
task docx        # DOCXのみ
```

### デプロイ

職務経歴を更新してGitHub経由でVercelにデプロイ

```sh
# デフォルトメッセージでデプロイ
task update

# カスタムメッセージでデプロイ
task update MESSAGE="プロジェクト経験を追加"
```

実行内容
- PDF/DOCX生成
- git add
- git commit
- git push（Vercelが自動デプロイ）

## Requirements

- `pandoc` with XeLaTeX support
- Japanese fonts (Hiragino Mincho Pro)
- Task (タスクランナー) - [インストール](https://taskfile.dev/installation/)
