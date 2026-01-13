# @resume/shared-ui

モノレポ全体で共有するUIコンポーネントパッケージ。

## 使い方

### 依存関係の追加

```bash
# packages/web から
pnpm add @resume/shared-ui --workspace
```

### Astroコンポーネントのインポート

```astro
---
import Navigation from '@resume/shared-ui/components/Navigation.astro';
---

<Navigation />
```

## コンポーネント一覧

| コンポーネント | 説明 |
|---------------|------|
| Navigation.astro | グローバルヘッダーナビゲーション |
| Footer.astro | フッター |

## 開発

```bash
# 型チェック
pnpm --filter @resume/shared-ui typecheck
```
