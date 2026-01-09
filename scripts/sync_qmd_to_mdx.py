#!/usr/bin/env python3
"""
QMDファイルからMDXファイルへの変換スクリプト

resume/resume-ja.qmd → packages/web/pages/ja/index.mdx
- YAMLフロントマターを除去
- MDX用のヘッダーを追加
"""

import re
from pathlib import Path

# パス設定
PROJECT_ROOT = Path(__file__).parent.parent
QMD_FILE = PROJECT_ROOT / "resume/resume-ja.qmd"
MDX_FILE = PROJECT_ROOT / "packages/web/pages/ja/index.mdx"

# MDXヘッダーテンプレート
MDX_HEADER = '''import CurrentDate from "../../components/CurrentDate";

<CurrentDate/>

'''


def extract_content_from_qmd(qmd_path: Path) -> str:
    """QMDファイルからYAMLフロントマターを除去してコンテンツを抽出"""
    content = qmd_path.read_text(encoding="utf-8")
    
    # YAMLフロントマター（---で囲まれた部分）を除去
    # 最初の---から次の---までを削除
    pattern = r"^---\n.*?\n---\n"
    content = re.sub(pattern, "", content, count=1, flags=re.DOTALL)
    
    return content.strip()


def convert_qmd_to_mdx(qmd_path: Path, mdx_path: Path) -> None:
    """QMDファイルをMDXファイルに変換"""
    # QMDからコンテンツを抽出
    content = extract_content_from_qmd(qmd_path)
    
    # MDXヘッダーを追加して保存
    mdx_content = MDX_HEADER + content + "\n"
    mdx_path.write_text(mdx_content, encoding="utf-8")
    
    print(f"✅ 変換完了: {qmd_path.name} → {mdx_path.name}")


def main():
    if not QMD_FILE.exists():
        print(f"❌ エラー: {QMD_FILE} が見つかりません")
        return 1
    
    convert_qmd_to_mdx(QMD_FILE, MDX_FILE)
    return 0


if __name__ == "__main__":
    exit(main())

