#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// MDXファイルのパス
const mdxFilePath = path.join(__dirname, '../pages/ja/index.mdx');
const tempMdPath = path.join(__dirname, '../temp_resume.md');
const outputDocxPath = path.join(__dirname, '../resume.docx');

console.log('📝 職務経歴書のWord(docx)生成を開始します...');

// MDXファイルを読み込み
if (!fs.existsSync(mdxFilePath)) {
  console.error('❌ MDXファイルが見つかりません:', mdxFilePath);
  process.exit(1);
}

const mdxContent = fs.readFileSync(mdxFilePath, 'utf8');

// MDXからMarkdownに変換（ReactコンポーネントとJSXを除去）
function convertMdxToMarkdown(content) {
  const lines = content.split('\n');
  const markdownLines = [];

  let inCodeBlock = false;

  for (const line of lines) {
    // コードブロックの開始/終了を追跡
    if (line.startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      markdownLines.push(line);
      continue;
    }

    // コードブロック内ではそのまま保持
    if (inCodeBlock) {
      markdownLines.push(line);
      continue;
    }

    // import文をスキップ
    if (line.startsWith('import ')) {
      continue;
    }

    // JSXコンポーネント（<.../>）をスキップ
    if (line.trim().startsWith('<') && line.trim().endsWith('/>')) {
      continue;
    }

    // その他のJSXタグをスキップ
    if (line.trim().startsWith('<') && line.trim().endsWith('>')) {
      continue;
    }

    // ネストの深いリストを平坦化
    if (line.match(/^(\s{8,}|\t{2,})-/)) {
      const flattenedLine = line.replace(/^(\s{8,}|\t{2,})/, '    ');
      markdownLines.push(flattenedLine);
      continue;
    }

    markdownLines.push(line);
  }

  return markdownLines.join('\n');
}

// Markdownに変換
const markdownContent = convertMdxToMarkdown(mdxContent);

// 一時Markdownファイルを作成
fs.writeFileSync(tempMdPath, markdownContent, 'utf8');

console.log('✅ MDXからMarkdownへの変換が完了しました');

// Pandocを使用してWord(docx)を生成
const pandocCommand = `pandoc "${tempMdPath}" -o "${outputDocxPath}" --metadata title="職務経歴書"`;

console.log('🔄 PandocでWord(docx)生成中...');

exec(pandocCommand, (error, stdout, stderr) => {
  // 一時ファイルを削除
  if (fs.existsSync(tempMdPath)) {
    fs.unlinkSync(tempMdPath);
  }

  if (error) {
    console.error('❌ Word(docx)生成でエラーが発生しました:', error.message);
    console.error('stderr:', stderr);
    process.exit(1);
  }

  if (stderr) {
    console.warn('⚠️  警告:', stderr);
  }

  if (fs.existsSync(outputDocxPath)) {
    const stats = fs.statSync(outputDocxPath);
    const fileSizeKB = Math.round(stats.size / 1024);
    console.log('🎉 Word(docx)生成が完了しました!');
    console.log(`📄 ファイル: ${outputDocxPath}`);
    console.log(`📏 サイズ: ${fileSizeKB}KB`);
    console.log(`🕐 更新日時: ${stats.mtime.toLocaleString('ja-JP')}`);
  } else {
    console.error('❌ Word(docx)ファイルが生成されませんでした');
    process.exit(1);
  }
});
