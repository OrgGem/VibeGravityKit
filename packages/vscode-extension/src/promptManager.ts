import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { getSkillsRoot, getWorkspaceRoot, safeSkillDirectoryName } from './config';
import { IDE_TARGETS, resolveWorkspacePath } from './ideTargets';

export interface PromptFile {
    label: string;
    relativePath: string;
    absolutePath: string;
    category: 'agent' | 'skill' | 'mcp' | 'ide';
    exists: boolean;
    size: number;
    preview: string;
}

const MAX_PROMPT_FILES = 120;
const MAX_PREVIEW_LENGTH = 6000;

export function collectPromptFiles(): PromptFile[] {
    const workspaceRoot = getWorkspaceRoot();
    const files = new Map<string, PromptFile>();

    for (const target of IDE_TARGETS) {
        for (const promptPath of target.promptPaths) {
            addPromptFile(files, workspaceRoot, promptPath, inferCategory(promptPath));
        }

        for (const promptDir of target.promptDirs) {
            addMarkdownFilesFromDirectory(files, workspaceRoot, promptDir, target.id === 'agent' ? 'agent' : 'ide');
        }

        if (target.mcpConfigPath) {
            addPromptFile(files, workspaceRoot, target.mcpConfigPath, 'mcp');
        }
    }

    addSkillMarkdownFiles(files);

    return [...files.values()]
        .sort((left, right) => {
            const categoryOrder = categoryRank(left.category) - categoryRank(right.category);
            return categoryOrder !== 0
                ? categoryOrder
                : left.relativePath.localeCompare(right.relativePath);
        })
        .slice(0, MAX_PROMPT_FILES);
}

export async function openPromptFile(relativePath?: string): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    let selectedPath = relativePath;

    if (!selectedPath) {
        const promptFiles = collectPromptFiles();
        const picked = await vscode.window.showQuickPick(
            promptFiles.map((file) => ({
                label: file.label,
                description: file.relativePath,
                detail: file.exists ? `${file.category} prompt` : 'Missing file',
                file
            })),
            {
                title: 'Open prompt or instruction file',
                placeHolder: 'Select a SKILL.md, agent prompt, rule, or MCP config'
            }
        );

        selectedPath = picked?.file.relativePath;
    }

    if (!selectedPath) {
        return;
    }

    const absolutePath = resolveWorkspacePath(workspaceRoot, selectedPath);
    fs.mkdirSync(path.dirname(absolutePath), { recursive: true });

    if (!fs.existsSync(absolutePath)) {
        fs.writeFileSync(absolutePath, createPromptTemplate(selectedPath), 'utf8');
    }

    const document = await vscode.workspace.openTextDocument(vscode.Uri.file(absolutePath));
    await vscode.window.showTextDocument(document, { preview: false });
}

export async function createMainInstructionFile(): Promise<void> {
    const workspaceRoot = getWorkspaceRoot();
    const relativePath = 'AGENTS.md';
    const absolutePath = resolveWorkspacePath(workspaceRoot, relativePath);

    if (fs.existsSync(absolutePath)) {
        await openPromptFile(relativePath);
        return;
    }

    fs.writeFileSync(absolutePath, createPromptTemplate(relativePath), 'utf8');
    await openPromptFile(relativePath);
}

function addSkillMarkdownFiles(files: Map<string, PromptFile>): void {
    let skillsRoot: string;
    try {
        skillsRoot = getSkillsRoot();
    } catch {
        return;
    }

    if (!fs.existsSync(skillsRoot)) {
        return;
    }

    for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
        if (!entry.isDirectory() || entry.name.startsWith('.')) {
            continue;
        }

        const skillMarkdownPath = path.join(skillsRoot, entry.name, 'SKILL.md');
        if (!fs.existsSync(skillMarkdownPath)) {
            continue;
        }

        const workspaceRoot = getWorkspaceRoot();
        const relativePath = normalizeRelativePath(path.relative(workspaceRoot, skillMarkdownPath));
        addPromptFile(files, workspaceRoot, relativePath, 'skill');
    }
}

function addMarkdownFilesFromDirectory(
    files: Map<string, PromptFile>,
    workspaceRoot: string,
    relativeDir: string,
    category: PromptFile['category']
): void {
    const absoluteDir = resolveWorkspacePath(workspaceRoot, relativeDir);
    if (!fs.existsSync(absoluteDir)) {
        return;
    }

    const entries = fs.readdirSync(absoluteDir, { withFileTypes: true });
    for (const entry of entries) {
        if (!entry.isFile() || entry.name.startsWith('.')) {
            continue;
        }

        if (!/\.(md|mdc|toml|json)$/i.test(entry.name)) {
            continue;
        }

        addPromptFile(files, workspaceRoot, normalizeRelativePath(path.join(relativeDir, entry.name)), category);
    }
}

function addPromptFile(
    files: Map<string, PromptFile>,
    workspaceRoot: string,
    relativePath: string,
    category: PromptFile['category']
): void {
    const normalizedRelativePath = normalizeRelativePath(relativePath);
    if (files.has(normalizedRelativePath)) {
        return;
    }

    const absolutePath = resolveWorkspacePath(workspaceRoot, normalizedRelativePath);
    const exists = fs.existsSync(absolutePath);
    const stat = exists ? fs.statSync(absolutePath) : undefined;

    files.set(normalizedRelativePath, {
        label: path.basename(normalizedRelativePath),
        relativePath: normalizedRelativePath,
        absolutePath,
        category,
        exists,
        size: stat?.size || 0,
        preview: exists && stat?.isFile() ? readPreview(absolutePath) : ''
    });
}

function inferCategory(relativePath: string): PromptFile['category'] {
    if (/mcp\.json$|config\.toml$/i.test(relativePath)) {
        return 'mcp';
    }

    if (/skill\.md$/i.test(relativePath)) {
        return 'skill';
    }

    return 'agent';
}

function readPreview(filePath: string): string {
    try {
        const raw = fs.readFileSync(filePath, 'utf8');
        if (raw.length <= MAX_PREVIEW_LENGTH) {
            return raw;
        }

        return `${raw.slice(0, MAX_PREVIEW_LENGTH)}\n\n...`;
    } catch {
        return '';
    }
}

function createPromptTemplate(relativePath: string): string {
    if (/AGENTS\.md$/i.test(relativePath)) {
        return [
            '# Agent Instructions',
            '',
            'Use this file for workspace-wide agent behavior, coding standards, and project-specific constraints.',
            '',
            '## Project Rules',
            '',
            '- Keep changes scoped to the requested task.',
            '- Preserve existing user changes.',
            ''
        ].join('\n');
    }

    if (/SKILL\.md$/i.test(relativePath)) {
        const skillName = safeSkillDirectoryName(path.basename(path.dirname(relativePath)) || 'new-skill');
        return [
            '---',
            `name: ${skillName}`,
            'description: Describe when this skill should be used.',
            '---',
            '',
            `# ${skillName}`,
            '',
            'Add concise activation guidance and the workflow the agent should follow.',
            ''
        ].join('\n');
    }

    return '';
}

function normalizeRelativePath(value: string): string {
    return value.replace(/\\/g, '/');
}

function categoryRank(category: PromptFile['category']): number {
    switch (category) {
        case 'agent':
            return 0;
        case 'skill':
            return 1;
        case 'mcp':
            return 2;
        case 'ide':
            return 3;
    }
}
