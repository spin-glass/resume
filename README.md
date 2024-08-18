# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/)
This resume is developed by Next.js template [Nextra](https://nextra.site/)

## Updating workflow

![workflow](./workflow.drawio.svg)

1. Update `pages/ja/index.mdx` in Japanese

2. Translate into English using [Crowdin](https://crowdin.com/profile/spin-glass)

3. After aprroving translation, execute `crowdin_sync_and_merge` workflow in [GitHub Actions](https://github.com/spin-glass/resume/actions) manually

## Development Environment

```{sh}
pnpm run dev
```
