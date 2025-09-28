#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// MDXファイルのパス
const mdxFilePath = path.join(__dirname, '../pages/ja/index.mdx');
const tempMdPath = path.join(__dirname, '../temp_resume.md');
const outputPdfPath = path.join(__dirname, '../resume.pdf');

console.log('📄 職務経歴書のPDF生成を開始します...');

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
    
    // ネストの深いリストを平坦化（LaTeXの制限回避）
    if (line.match(/^(\s{8,}|\t{2,})-/)) {
      // 深いネストは2レベルまでに制限
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

// Pandocを使用してPDFを生成
const pandocCommand = `pandoc "${tempMdPath}" -o "${outputPdfPath}" --pdf-engine=xelatex -V CJKmainfont="Hiragino Mincho Pro" -V geometry:margin=1in --metadata title="職務経歴書"`;

console.log('🔄 PandocでPDF生成中...');

exec(pandocCommand, (error, stdout, stderr) => {
  // 一時ファイルを削除
  if (fs.existsSync(tempMdPath)) {
    fs.unlinkSync(tempMdPath);
  }
  
  if (error) {
    console.error('❌ PDF生成でエラーが発生しました:', error.message);
    console.error('stderr:', stderr);
    process.exit(1);
  }
  
  if (stderr) {
    console.warn('⚠️  警告:', stderr);
  }
  
  if (fs.existsSync(outputPdfPath)) {
    const stats = fs.statSync(outputPdfPath);
    const fileSizeKB = Math.round(stats.size / 1024);
    console.log(`🎉 PDF生成が完了しました!`);
    console.log(`📄 ファイル: ${outputPdfPath}`);
    console.log(`📏 サイズ: ${fileSizeKB}KB`);
    console.log(`🕐 更新日時: ${stats.mtime.toLocaleString('ja-JP')}`);
  } else {
    console.error('❌ PDFファイルが生成されませんでした');
    process.exit(1);
  }
});
