# Implementation Plan: Portfolio & Agent Showcase

**Feature**: 019-portfolio-showcase  
**Status**: In Progress  
**Date**: 2026-01-11

---

## Implementation Strategy

### Stage 1: Documentation & Web Pages (FR-PF01)
**Scope**: このPRで実装  
**Duration**: 1-2日

1. Specification & Documentation
2. Agent Architecture Documentation
3. Web Portfolio Pages
4. Navigation Updates
5. Documentation Updates

### Stage 2: Living Portfolio Chatbot (FR-PF02)
**Scope**: 後のPRで実装  
**Duration**: 2-3日（別途計画）

---

## Stage 1 Implementation Steps

### Step 1: Create Specification Files

**Files**:
- [x] `specs/019-portfolio-showcase/spec.md`
- [ ] `specs/019-portfolio-showcase/plan.md` (this file)
- [ ] `specs/019-portfolio-showcase/tasks.md`

**Validation**: ファイルが存在し、roadmap.mdと整合している

---

### Step 2: Architecture Documentation

#### 2.1 Create Architecture Document

**File**: `packages/resume-review/docs/architecture.md`

**Content Sections**:
1. **Overview** (1-2パラグラフ)
   - プロジェクトの目的
   - 主要技術スタック

2. **System Architecture**
   - LangGraph StateGraphの概要
   - 全体フロー図（Mermaid）

3. **State Management**
   - Pydantic ReviewStateの設計
   - State遷移パターン

4. **Multi-Agent Orchestration**
   - Fan-out/Fan-inパターン
   - 各エージェント（Recruiter, TechWriter, Copywriter, UX, Visual）の役割
   - 並列実行の実装

5. **Cost Optimization**
   - マルチモデル戦略（Gemini, OpenAI, Anthropic）
   - コスト削減実績（50%）
   - パフォーマンス向上（70%高速化）

6. **Tool Integration**
   - Screenshot capture (Playwright)
   - Quarto validation
   - Multi-model LLM client

**Mermaid Diagrams**:
- StateGraph全体フロー
- Fan-out/Fan-inノード構造
- State遷移図

**Validation**: 
- [ ] Markdownが正しくレンダリングされる
- [ ] Mermaid図が表示される
- [ ] 技術的に正確

---

#### 2.2 Update README.md

**File**: `packages/resume-review/README.md`

**Changes**:
- トップに「## Portfolio Showcase」セクション追加
- バッジ追加（オプション）:
  - ![LangGraph](https://img.shields.io/badge/LangGraph-1.0-blue)
  - ![Multi-Model](https://img.shields.io/badge/Multi--Model-Gemini%20%7C%20OpenAI%20%7C%20Claude-green)
- アーキテクチャドキュメントへのリンク: `[Architecture Documentation](docs/architecture.md)`
- 主要技術スタック一覧（視覚的表示）

**Validation**:
- [ ] READMEがGitHubで正しく表示される
- [ ] リンクが機能する

---

### Step 3: Web Portfolio Pages

#### 3.1 Portfolio Landing Page

**File**: `packages/web/src/pages/portfolio.mdx`

**Content**:
```mdx
---
layout: ../layouts/MainLayout.astro
title: 'Portfolio - Resume Review Agent System'
description: 'Multi-agent AI system for resume review and optimization'
---

# Portfolio: Resume Review Agent System

[1-2パラグラフのプロジェクト概要]

## Technical Highlights
- LangGraph StateGraph for orchestration
- Multi-model hybrid (Gemini, OpenAI, Anthropic)
- 50% cost reduction, 70% faster execution
- Fan-out/Fan-in parallel agent execution
- Pydantic 2.0 for type-safe state management

## Architecture Overview
[Mermaid diagram - simplified version]

## Learn More
- [Architecture Details](/portfolio/architecture)
- [GitHub Repository](https://github.com/spin-glass/resume)
- [README](https://github.com/spin-glass/resume/tree/main/packages/resume-review)
```

**Validation**:
- [ ] `/portfolio` にアクセスできる
- [ ] Mermaid図が表示される
- [ ] リンクが機能する

---

#### 3.2 Architecture Details Page

**File**: `packages/web/src/pages/portfolio/architecture.mdx`

**Content**:
- `packages/resume-review/docs/architecture.md` をベースに作成
- Astro frontmatter追加
- Tailwind CSSでスタイリング調整
- ナビゲーションブレッドクラム追加

**Styling**:
- 見出しに適切なスペーシング
- コードブロックにシンタックスハイライト
- Mermaid図を中央配置

**Validation**:
- [ ] `/portfolio/architecture` にアクセスできる
- [ ] architecture.mdの内容が表示される
- [ ] レスポンシブデザインが機能する

---

### Step 4: Navigation Updates

**File**: `packages/web/src/layouts/MainLayout.astro`

**Changes**:
- ナビゲーションリンク追加: `<a href="/portfolio">Portfolio</a>`
- モバイルメニューにも追加
- 現在のページをハイライト（`aria-current="page"` 使用）

**Validation**:
- [ ] デスクトップナビゲーションに表示される
- [ ] モバイルメニューに表示される
- [ ] ポートフォリオページで「Portfolio」がハイライトされる

---

### Step 5: Documentation Updates

#### 5.1 Update roadmap.md

**File**: `docs/roadmap.md`

**Changes**:
- feature 16 (19) のステータスを「🟢 進行中」に更新
- 完了後、「✅ 完了」に変更
- 「完了済み機能」テーブルに追加

#### 5.2 Update CLAUDE.md

**File**: `CLAUDE.md`

**Changes**:
- 「Recent Changes」セクションに追記:
  ```
  - 019-portfolio-showcase: Agent architecture documentation and web portfolio pages
  ```

**Validation**:
- [ ] roadmap.mdのステータスが正確
- [ ] CLAUDE.mdが最新

---

## Testing Strategy

### Unit Tests
- **Python**: 既存のpytestが全てパス
  ```bash
  cd packages/resume-review
  pytest
  ```

### Integration Tests
- **Astro Build**:
  ```bash
  cd packages/web
  pnpm build
  ```
- ビルドエラーがないことを確認

### Manual Testing
1. **ローカルdev server**:
   ```bash
   cd packages/web
   pnpm dev
   ```
2. ブラウザで以下をテスト:
   - `http://localhost:4321/portfolio`
   - `http://localhost:4321/portfolio/architecture`
   - ナビゲーションリンク
   - モバイル表示

3. **本番ビルド**:
   ```bash
   VERCEL=1 pnpm build
   pnpm preview
   ```

---

## Rollout Plan

### Phase 1: Development
- [ ] Stage 1実装完了
- [ ] ローカルテスト完了

### Phase 2: Review & Refinement
- [ ] セルフレビュー
- [ ] ドキュメント完全性確認
- [ ] 誤字脱字チェック

### Phase 3: Deployment
- [ ] コミット & プッシュ
- [ ] Vercelに自動デプロイ
- [ ] 本番環境で動作確認

### Phase 4: Documentation
- [ ] walkthrough.md作成
- [ ] roadmap.md最終更新

---

## Success Metrics

### Qualitative
- [ ] 採用担当者が技術スタックを5分以内に理解できる
- [ ] アーキテクチャドキュメントが読みやすい
- [ ] Webページが視覚的に魅力的

### Quantitative
- [ ] ページロード時間 < 3秒
- [ ] Lighthouse Score > 90（Performance）
- [ ] モバイル・デスクトップ両対応

---

## Risks & Contingencies

| Risk | Mitigation |
|------|------------|
| Mermaid図が複雑すぎる | 複数の小さい図に分割 |
| ドキュメントが長すぎる | サマリーセクションを追加 |
| ナビゲーション変更で既存ページが影響 | 小さい変更に留め、全ページテスト |

---

## Next Steps (Stage 2)

Living Portfolio Chatbot (FR-PF02) の実装:
- チャットインターフェース設計
- Vercel Serverless Functions実装
- LangGraph API統合
- レート制限・セキュリティ対策

**予定**: 別PRで実装（feature/020等）
