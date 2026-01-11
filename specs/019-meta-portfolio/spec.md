# Feature 019: Meta Portfolio - 簡易版

## 概要
本リポジトリをポートフォリオとして機能させる。採用担当者を意識し、シンプルかつ効果的に技術力を伝える。

## 背景
- Roadmap ID: 19
- 課題: レジュメ（静的なPDF/Web）だけでは、Agent開発やMLOps、アーキテクチャ設計能力を十分に伝えきれない。
- 解決策: リポジトリ内の主要プロジェクトを1ページにまとめた詳細ページとして公開し、職務経歴書にリンクを記載する。

## 要件

### 1. 職務経歴書への詳細記載
- `resume/resume-ja.qmd` に各プロジェクトの詳細情報を記載
- 技術スタック、課題、解決策、成果を簡潔に記述
- Webポートフォリオページへのリンクを含める

### 2. Webポートフォリオ - 1ページ構成
- **ポートフォリオトップページ** (`/portfolio`):
  - プロジェクト一覧（カード形式）
  - 各プロジェクトへのリンク
  
- **個別プロジェクトページ** (`/portfolio/project/{id}`):
  - **1ページに全情報を集約**
  - セクション:
    - 概要・背景
    - 技術スタック
    - アーキテクチャ（図・コード例）
    - 主要仕様へのリンク（`specs/` 内のドキュメント）
    - 成果
  - ページ分割しない（採用担当者が迷わないように）

### 3. Content Collections (簡素化)
- `specs/` ディレクトリをContent Collectionsとして扱う（既存実装を活用）
- ただし、ユーザー向けには個別プロジェクトページからのリンクとしてのみ表示
- 直接 `/portfolio/specs/{id}` を見せる必要はない

## 設計原則

### 採用担当者ファースト
1. **ページ数を最小限に**: トップページ + プロジェクト詳細ページのみ
2. **情報の集約**: 1プロジェクト = 1ページ（スクロールで完結）
3. **明快な構造**: 迷わない、戻る必要がない
4. **技術力の可視化**: コード例、アーキテクチャ図を効果的に配置

### スコープ
- ❌ Agent Showcase UIは今回対象外（複雑化を避ける）
- ❌ Knowledge Base自動生成は今回対象外
- ✅ 職務経歴書の充実
- ✅ シンプルなWebポートフォリオ（プロジェクト詳細ページ）

## ディレクトリ構造
```text
packages/web/
├── src/
│   ├── content.config.ts          # specs コレクション定義（既存）
│   ├── pages/
│   │   ├── portfolio/
│   │   │   ├── index.astro        # ポートフォリオトップ
│   │   │   ├── project/
│   │   │   │   ├── [id].astro     # 個別プロジェクト詳細（1ページ完結）
│   │   │   ├── specs/             # （既存、直接見せない）
│   │   │   │   ├── [...slug].astro
```

## 主要プロジェクト（初期想定）
1. **Resume Review Agent** (`resume-review`)
   - LangGraph + StateGraph
   - Multi-model hybrid (OpenAI + Claude)
   - Auto design fix workflow
   
2. **Astro Migration** (`astro-migration`)
   - Legacy to Astro 5
   - Content Collections
   - Vercel deployment

3. **Monorepo Architecture** (`monorepo`)
   - pnpm workspace
   - TypeScript + Python hybrid
   - Package dependencies

## データフロー
1. Developer commits project details to `resume/resume-ja.qmd`
2. Developer creates project page at `packages/web/src/pages/portfolio/project/{id}.astro`
3. CI/CD runs `pnpm build` → Astro generates static pages
4. Vercel deploys
5. 採用担当者が `/portfolio` → プロジェクトカードをクリック → 詳細ページで技術力を確認

## タスク
1. `resume/resume-ja.qmd`: プロジェクト詳細セクションの追加
2. `packages/web`: プロジェクト詳細ページテンプレート作成
3. `packages/web`: ポートフォリオトップページの簡素化（プロジェクトカード表示）
