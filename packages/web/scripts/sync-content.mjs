import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Paths
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const QMD_FILE = path.join(PROJECT_ROOT, 'resume/resume-ja.qmd');
const MDX_FILE = path.join(PROJECT_ROOT, 'packages/web/src/pages/index.mdx');

// Astro Header
const MDX_HEADER_TOP = `---
layout: ../layouts/Layout.astro
title: "職務経歴書"
---
`;

const MDX_FOOTER = `
`;

function extractContentFromQmd(qmdPath) {
    const content = fs.readFileSync(qmdPath, 'utf-8');

    // Strip YAML frontmatter
    // Remove from start of file until second ---
    const frontmatterPattern = /^---\n[\s\S]*?\n---\n/;
    let cleanContent = content.replace(frontmatterPattern, '');

    // Remove Quarto callout blocks
    // ::: {.callout-note ...} ... :::
    const calloutPattern = /::: \{\.callout-note.*?\}\n[\s\S]*?\n:::\n/g;
    cleanContent = cleanContent.replace(calloutPattern, '');

    return cleanContent.trim();
}

function main() {
    if (!fs.existsSync(QMD_FILE)) {
        console.error(`❌ Error: ${QMD_FILE} not found`);
        process.exit(1);
    }

    try {
        const content = extractContentFromQmd(QMD_FILE);
        const mdxContent = `${MDX_HEADER_TOP}\n${content}\n\n${MDX_FOOTER}`;

        // Ensure dir exists
        const mdxDir = path.dirname(MDX_FILE);
        if (!fs.existsSync(mdxDir)) {
            fs.mkdirSync(mdxDir, { recursive: true });
        }

        fs.writeFileSync(MDX_FILE, mdxContent, 'utf-8');
        console.log(`✅ Synced: ${path.basename(QMD_FILE)} -> ${path.basename(MDX_FILE)}`);
    } catch (err) {
        console.error('❌ Sync failed:', err);
        process.exit(1);
    }
}

main();
