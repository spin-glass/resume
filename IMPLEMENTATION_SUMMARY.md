# Feature 022: Interview Preparation (Gap Analysis)

**実装日**: 2026-01-11
**ブランチ**: feature/022-interview-preparation
**ステータス**: ✅ 実装完了

---

## 📊 実装統計

- **新規機能**: Gap Analysis (スキルギャップ分析)
- **Agent**: `GapAnalyzerAgent` (Resume vs JD)
- **CLI**: `gap-analyze` コマンド追加

## 🎯 実装機能

### Gap Analysis Agent
- OpenAI/Gemini/Claudeを用いたスキルギャップ分析
- 履歴書と募集要項(JD)の比較
- 不足スキルの特定と具体的なアクションプランの提示
- 総合評価 (10段階)

### CLI Integration
- `pnpm gap-analyze` コマンド
- オプション:
  - `--resume`: 履歴書ファイル (必須)
  - `--job-posting`: JDファイル (テキスト/Markdown)
  - `--job-url`: JDのWebページURL (スクレイピング対応)
  - `--save`: 結果を保存
  - `--model`: 使用モデル指定

### 出力管理
- デフォルト保存先: `resume/gap_analysis_{job_name}_{timestamp}/`
- 出力ファイル:
  - `analysis_report.md`: 分析レポート
  - `job_description.txt`: 使用したJDテキスト
  - `resume_original.qmd`: 元の履歴書
  - `analysis.json`: 生データ
- Git管理: `.gitignore` により自動除外

## 📝 使用例

```bash
# 基本的な使用法
pnpm gap-analyze --resume resume/resume-ja.qmd --job-url https://example.com/job

# ファイル入力と保存
pnpm gap-analyze --resume resume/resume-ja.qmd --job-posting job.txt --save
```
