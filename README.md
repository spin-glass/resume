# About this repository

This is the repository for my [resume](https://resume.spin-glass.dev/). This resume is developed by Next.js template [Nextra](https://nextra.site/)
``

## Update Resume

1. When updating resume

- update `public/assets/*.qmd`

## Development Environment

```{sh}
pnpm run dev
```

## Test GitHub Actions

```{sh}
export DOCKER_HOST=$(docker context inspect colima | jq -r '.[0].Endpoints.docker.Host')
act --container-architecture linux/amd64
```
