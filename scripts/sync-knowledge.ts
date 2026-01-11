
import fs from 'node:fs/promises';
import path from 'node:path';
import { glob } from 'glob';

interface KnowledgeItem {
    id: string;
    type: 'doc' | 'spec' | 'package';
    path: string;
    content: string;
    metadata: Record<string, any>;
}

const ROOT_DIR = path.resolve(__dirname, '..');
const OUTPUT_FILE = path.join(ROOT_DIR, 'packages/resume-review/data/knowledge_base.json');

async function syncKnowledge() {
    console.log('Syncing knowledge base...');

    const items: KnowledgeItem[] = [];

    // Specs
    const specFiles = await glob('specs/**/*.md', { cwd: ROOT_DIR });
    for (const file of specFiles) {
        const content = await fs.readFile(path.join(ROOT_DIR, file), 'utf-8');
        items.push({
            id: file,
            type: 'spec',
            path: file,
            content,
            metadata: {},
        });
    }

    // Docs
    const docFiles = await glob('docs/**/*.md', { cwd: ROOT_DIR });
    for (const file of docFiles) {
        const content = await fs.readFile(path.join(ROOT_DIR, file), 'utf-8');
        items.push({
            id: file,
            type: 'doc',
            path: file,
            content,
            metadata: {},
        });
    }

    // Packages README
    const packageReadmes = await glob('packages/*/README.md', { cwd: ROOT_DIR });
    for (const file of packageReadmes) {
        const content = await fs.readFile(path.join(ROOT_DIR, file), 'utf-8');
        items.push({
            id: file,
            type: 'package',
            path: file,
            content,
            metadata: {},
        });
    }

    // Ensure output dir exists
    await fs.mkdir(path.dirname(OUTPUT_FILE), { recursive: true });

    await fs.writeFile(OUTPUT_FILE, JSON.stringify(items, null, 2));
    console.log(`Knowledge base synced: ${items.length} items written to ${OUTPUT_FILE}`);
}

syncKnowledge().catch(console.error);
