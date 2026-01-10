# Design Auto-Fix 機能使用ガイド

**実装日**: 2026-01-09
**ブランチ**: 013-design-auto-fix
**ステータス**: ✅ MVP完成 (Phase 3)

---

## 🎯 機能概要

デザインエージェント（UX Designer / Visual Designer）からのフィードバックを基に、自動的にCSSを生成してデザイン問題を修正します。

### 主な機能

- ✅ **自動CSS生成**: デザインフィードバック → LLM → CSS rules
- ✅ **安全なファイル操作**: バックアップ作成 → 検証 → atomic write
- ✅ **CSSバリデーション**: cssutilsによる構文チェック + 禁止ルール検出
- ✅ **プレビューモード**: ファイルを変更せずに変更内容を確認
- ✅ **カスタムCSS出力**: 出力先を自由に指定可能

---

## 🚀 クイックスタート

### 0. 初回セットアップ

**重要**: 初めて実行する場合、API KEYの設定が必要です。

```bash
# 1. .envファイルを作成
cd packages/resume-review
cp .env.example .env

# 2. .envファイルを編集してAPI KEYを設定
# ANTHROPIC_API_KEY=your_actual_api_key_here
```

`.env`ファイルの例:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 1. 基本的な自動デザイン適用

```bash
pnpm review:full --auto-design
# または
cd packages/resume-review
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja \
  --auto-design \
  --save-iterations
```

**動作フロー:**
1. 通常のレビューワークフロー実行（5エージェント評価）
2. デザインエージェントからフィードバック取得
3. LLMがCSS生成（spacing, typography, hierarchy等）
4. cssutilsでバリデーション
5. `styles/resume-custom.css` に自動保存（バックアップ付き）

**結果:**
- `styles/resume-custom.css` - 生成されたCSS
- `backups/resume-custom_YYYYMMDD_HHMMSS.css` - バックアップ（存在した場合）

---

### 2. プレビューモード（ファイルを変更しない）

```bash
cd packages/resume-review
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja \
  --design-preview
```

**用途:** CSS生成内容を確認してから適用するか判断したい場合

**動作:**
- CSSは生成されますが、ファイルには書き込まれません
- ログに変更内容が表示されます
- 問題なければ `--auto-design` で再実行

---

### 3. カスタムCSS出力パス

```bash
cd packages/resume-review
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --auto-design \
  --css-output custom/my-theme.css
```

**用途:** デフォルトの `styles/resume-custom.css` 以外に保存したい場合

---

## 📋 CLIオプション詳細

### `--auto-design`

自動的にデザイン修正を適用します。

- **タイプ**: Boolean flag
- **デフォルト**: False
- **相互排他**: `--design-preview` とは同時に使用不可
- **動作**: CSSファイルを実際に作成・更新
- **バックアップ**: 既存ファイルがある場合、`backups/` に自動保存

**例:**
```bash
python -m src.cli review --input resume.qmd --auto-design
```

### `--design-preview`

変更内容をプレビューのみ（ファイルは変更しない）。

- **タイプ**: Boolean flag
- **デフォルト**: False
- **相互排他**: `--auto-design` とは同時に使用不可
- **動作**: CSS生成して内容確認のみ、ファイル書き込みなし
- **推奨**: `--screenshot-url` と併用（将来的にビジュアルプレビュー対応）

**例:**
```bash
python -m src.cli review --input resume.qmd --design-preview --screenshot-url http://localhost:3000/ja
```

### `--css-output PATH`

CSS出力先のカスタマイズ。

- **タイプ**: File path
- **デフォルト**: `styles/resume-custom.css`
- **必須条件**: `--auto-design` または `--design-preview` が必要
- **動作**: 指定したパスにCSSを出力（ディレクトリは自動作成）

**例:**
```bash
python -m src.cli review --input resume.qmd --auto-design --css-output themes/custom.css
```

---

## ⚠️ 制約と注意事項

### 1. 相互排他性エラー

```bash
# ❌ エラー
python -m src.cli review --input resume.qmd --auto-design --design-preview

# Error: --auto-design and --design-preview are mutually exclusive.
# Use --design-preview to review changes first, then run with --auto-design to apply.
```

**理由**: プレビューか適用かを明確にするため

### 2. CSS出力要件エラー

```bash
# ❌ エラー
python -m src.cli review --input resume.qmd --css-output custom.css

# Error: --css-output requires either --auto-design or --design-preview
```

**理由**: CSS出力はデザイン機能が有効な時のみ意味がある

### 3. Dry-run優先

```bash
# ⚠️ 警告が出て、auto-designが無効化される
python -m src.cli review --input resume.qmd --dry-run --auto-design

# Note: --dry-run enabled. Design modifications will be generated but not applied.
```

**理由**: `--dry-run` はすべての書き込み操作を無効化する

### 4. Screenshot URL推奨

```bash
# ⚠️ 警告が出るが実行は続行
python -m src.cli review --input resume.qmd --design-preview

# Warning: --design-preview works best with --screenshot-url.
# Preview will be text-only without screenshots.
```

**理由**: 将来のビジュアルプレビュー機能のため（現在は未実装）

---

## 🔍 CSS生成の仕組み

### 1. デザインフィードバックの収集

UX Designer と Visual Designer からのフィードバックを抽出：

```python
design_feedback = [
    f for f in current_feedback
    if f.agent_name in ["ux_designer", "visual_designer"]
]
```

### 2. Issue分類

フィードバックを5つのカテゴリに自動分類：

- **SPACING**: margin, padding, gap
- **TYPOGRAPHY**: font-size, font-weight, line-height
- **COLOR**: color, contrast, accessibility
- **HIERARCHY**: visual hierarchy, emphasis
- **LAYOUT**: alignment, balance, arrangement

### 3. CSS生成プロンプト

LLMに送信されるプロンプト例：

```
Based on the following design feedback, generate CSS modifications...

## Feedback from ux_designer:
- **SPACING**: Sections feel cramped, need more breathing room (severity: high)
- **HIERARCHY**: Headings lack visual hierarchy (severity: medium)

Current CSS:
/* No existing CSS */

Please generate CSS rules that address these specific issues.
```

### 4. CSS抽出とバリデーション

```python
# LLM応答から```css ... ```ブロックを抽出
css_content = extract_css_from_response(response)

# cssutilsでバリデーション
passed, errors = css_service.validate_css(css_content)

# 禁止ルールチェック
# - @media print {} は禁止（PDF/HTML両対応のため）
# - 構文エラーチェック
```

### 5. 安全な適用

```python
# 1. 既存ファイルのバックアップ作成
backup_path = create_backup(target_file)  # backups/resume-custom_20260109_143022.css

# 2. tempファイルに書き込み
temp_file.write(css_content)

# 3. 検証OK → atomic rename
temp_file.replace(target_file)  # アトミック操作
```

---

## 🧪 テスト方法

### ユニットテスト

```bash
# CSSバリデーションテスト
cd packages/resume-review
python -c "
from src.services.css_service import CSSService
service = CSSService()

# Valid CSS
passed, _ = service.validate_css('h2 { font-size: 1.4rem; }')
assert passed

# Invalid CSS with @media print
passed, errors = service.validate_css('@media print { h2 { color: red; } }')
assert not passed
assert any('print' in str(e).lower() for e in errors)

print('✅ CSS validation tests passed')
"
```

### CLIバリデーションテスト

```bash
cd packages/resume-review

# Mutual exclusivity
python -m src.cli review --input ../../resume/resume-ja.qmd --auto-design --design-preview 2>&1 | grep "mutually exclusive"

# CSS output requirement
python -m src.cli review --input ../../resume/resume-ja.qmd --css-output custom.css 2>&1 | grep "requires either"

echo "✅ CLI tests passed"
```

### 統合テスト（実際のワークフロー）

```bash
# 注意: これは実際にLLM APIを呼び出します（課金発生）
cd packages/resume-review

# Dry-run + design-preview（ファイル変更なし）
python -m src.cli review \
  --input ../../resume/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja \
  --design-preview \
  --dry-run \
  --verbose
```

---

## 📊 実装ステータス

### ✅ 完了（MVP - Phase 3）

- [x] データモデル（CSSModification, DesignIssueType等）
- [x] CSSService（バリデーション、バックアップ、atomic write）
- [x] CSSGeneratorAgent（LLMベースCSS生成）
- [x] design_applier_node（ワークフローノード）
- [x] ワークフローグラフ統合
- [x] CLI統合（--auto-design, --design-preview, --css-output）
- [x] バリデーション（相互排他性、要件チェック）
- [x] 基本テスト（ユニット、CLI）

### ⏳ 未実装（将来拡張）

- [ ] プレビュースクリーンショット生成（before/after/diff画像）
- [ ] セクション並び替え（SectionReorder）
- [ ] テーマ推薦（ThemeRecommendation）
- [ ] 統合テスト（エンドツーエンド）
- [ ] パフォーマンス最適化

---

## 🐛 トラブルシューティング

### CSS validation failed

**症状:**
```
CSS validation failed: ['CSS parsing error: ...']
```

**原因:**
- LLMが不正なCSS構文を生成
- 禁止された@media printルールを含む

**対処:**
- ログを確認してLLM応答を確認
- 必要に応じてプロンプト調整（`src/config/prompts.py`）
- 手動でCSSを修正

### No design feedback

**症状:**
```
Design Applier: No design feedback, skipping
```

**原因:**
- UX/Visual Designerエージェントが実行されていない
- `--screenshot-url` が指定されていない

**対処:**
```bash
# screenshot-urlを指定してデザインレビューを有効化
python -m src.cli review \
  --input resume.qmd \
  --screenshot-url http://localhost:3000/ja \
  --auto-design
```

### Import errors

**症状:**
```
ImportError: attempted relative import beyond top-level package
```

**原因:** パッケージとして実行していない

**対処:**
```bash
# ❌ 直接実行
python src/cli.py

# ✅ モジュールとして実行
python -m src.cli
```

---

## 📚 関連ファイル

### 実装ファイル

| ファイル | 説明 | 行数 |
|---------|------|-----|
| `src/models/design.py` | データモデル定義 | 252 |
| `src/services/css_service.py` | CSS操作サービス | 218 |
| `src/agents/css_generator.py` | CSS生成エージェント | 255 |
| `src/workflow/nodes/design_applier.py` | ワークフローノード | 169 |
| `src/workflow/graph.py` | グラフ統合 | 83 |
| `src/workflow/conditions.py` | 条件分岐 | 72 |
| `src/cli.py` | CLI統合 | 395+ |

### ドキュメント

| ファイル | 説明 |
|---------|------|
| `specs/013-design-auto-fix/spec.md` | 機能仕様 |
| `specs/013-design-auto-fix/plan.md` | 実装計画 |
| `specs/013-design-auto-fix/tasks.md` | タスク一覧 |
| `specs/013-design-auto-fix/quickstart.md` | クイックスタート |
| `specs/013-design-auto-fix/research.md` | 技術調査 |

---

## 💡 ベストプラクティス

### 1. プレビューファースト

```bash
# ステップ1: プレビューで確認
python -m src.cli review --input resume.qmd --design-preview

# ステップ2: 問題なければ適用
python -m src.cli review --input resume.qmd --auto-design
```

### 2. バックアップ確認

```bash
# CSSを適用した後、バックアップを確認
ls -la backups/

# 問題があれば復元
cp backups/resume-custom_YYYYMMDD_HHMMSS.css styles/resume-custom.css
```

### 3. Gitコミット前確認

```bash
# 1. デザイン適用
pnpm review:full --auto-design

# 2. CSSを確認
cat styles/resume-custom.css

# 3. PDFを生成してビジュアル確認
pnpm quarto:pdf

# 4. 問題なければコミット
git add styles/resume-custom.css
git commit -m "feat: apply auto-generated design improvements"
```

---

## 🎓 次のステップ

MVP完成後の拡張機能：

1. **Phase 4**: プレビュースクリーンショット（before/after/diff）
2. **Phase 5**: セクション並び替え（QMD section reordering）
3. **Phase 6**: テーマ推薦（Quarto theme recommendations）
4. **Phase 7**: ポリッシュ（統合テスト、ドキュメント、最適化）

---

**最終更新**: 2026-01-09
**実装者**: Claude Sonnet 4.5 (with Toshi)
**ライセンス**: MIT
