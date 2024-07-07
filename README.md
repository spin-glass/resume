# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/). This resume is developed by Next.js template [Nextra](https://nextra.site/)
``

## Update Resume

1. When updating resume

(Todo: develop workflow for following works)

- update `public/assets/*.qmd`
- reflect the above change to `pages/index`
- apply `quarto render` to assets to `public/assets/*.qmd` to create `public/assets/resume-ja` (Todo: develop English resume automatically)

## Development Environment

```{sh}
pnpm run dev
```
