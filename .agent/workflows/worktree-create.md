---
description: 新しい機能開発用のGit worktreeを作成する
---

// turbo-all
1. ロードマップアイテムの番号と名前を確認します。

2. ブランチ名とworktree名を決定します。
   - フォーマット: `feature/[NNN]-[feature-name]`
   - 例: `feature/020-ux-improvements`, `feature/019-meta-portfolio`

3. 新しいworktreeを作成します。
```bash
git worktree add ../[worktree_dir_name] -b [branch_name]
```

4. worktreeが正常に作成されたことを確認します。
```bash
git worktree list
```

5. ユーザーに作成結果を報告します。
