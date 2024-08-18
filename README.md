# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/). This resume is developed by Next.js template [Nextra](https://nextra.site/)
``

## Update Resume

1. When updating resume

    - update `pages/ja/index.mdx`

2. Translate in English

    - Translate using [Crowdin](https://crowdin.com/profile/spin-glass)

    - After aproving, execute `crowdin_sync_and_merge` workflow in [GitHub Actions](https://github.com/spin-glass/resume/actions) manually

## Development Environment

```{sh}
pnpm run dev
```
