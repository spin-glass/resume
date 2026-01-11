---
description: 完了したGit worktreeの変更を確認し、mainへマージした後にworktreeとブランチを削除する
---

// turbo-all
1. ブランチの変更内容を確認します。
```bash
git diff main..[branch_name]
```

2. ユーザーに変更内容の確認を依頼します。

3. `main` ブランチにマージします。
```bash
git checkout main
git merge [branch_name]
```

4. worktree とブランチを削除してクリーンアップします。
```bash
git worktree remove ../[worktree_dir_name]
git branch -d [branch_name]
```

5. ロードマップのステータスを更新します。
