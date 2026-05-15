import * as vscode from 'vscode';
import * as path from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { getRpaSkillsConfigValue } from './config';

const execFileAsync = promisify(execFile);

const supportedExtensions = new Set([
    '.docx',
    '.docm',
    '.pptx',
    '.pptm',
    '.xlsx',
    '.xlsm',
    '.xls',
    '.xlsb'
]);

export async function previewDocumentAsMarkdown(input?: vscode.Uri): Promise<void> {
    const uri = await resolveDocumentUri(input);
    if (!uri) {
        return;
    }

    const extension = path.extname(uri.fsPath).toLowerCase();
    if (!supportedExtensions.has(extension)) {
        vscode.window.showErrorMessage('Please select a Word, PowerPoint, or Excel file.');
        return;
    }

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `Converting ${path.basename(uri.fsPath)} to Markdown...`,
        cancellable: false
    }, async () => {
        const markdown = await convertDocumentWithMarkItDown(uri.fsPath);
        showMarkdownPreview(uri, markdown);
    });
}

async function resolveDocumentUri(input?: vscode.Uri): Promise<vscode.Uri | undefined> {
    if (input?.scheme === 'file') {
        return input;
    }

    const activeUri = vscode.window.activeTextEditor?.document.uri;
    if (activeUri?.scheme === 'file' && supportedExtensions.has(path.extname(activeUri.fsPath).toLowerCase())) {
        return activeUri;
    }

    const picked = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: {
            'Office documents': ['docx', 'docm', 'pptx', 'pptm', 'xlsx', 'xlsm', 'xls', 'xlsb']
        },
        title: 'Select an Office document to preview as Markdown'
    });

    return picked?.[0];
}

async function convertDocumentWithMarkItDown(filePath: string): Promise<string> {
    const pythonPath = getRpaSkillsConfigValue<string>('markitdown.pythonPath') || 'python';
    const timeoutMs = getRpaSkillsConfigValue<number>('markitdown.timeoutMs') || 120000;

    try {
        const result = await execFileAsync(
            pythonPath,
            ['-m', 'markitdown', filePath],
            {
                encoding: 'utf8',
                maxBuffer: 20 * 1024 * 1024,
                timeout: timeoutMs,
                windowsHide: true
            }
        );

        const markdown = result.stdout.trim();
        if (!markdown) {
            return '_MarkItDown converted the file but returned no Markdown content._';
        }

        return markdown;
    } catch (error: any) {
        const detail = [
            error?.message,
            error?.stderr
        ].filter(Boolean).join('\n').trim();
        throw new Error(`MarkItDown conversion failed. Ensure MarkItDown is installed for ${pythonPath}.\n${detail}`);
    }
}

function showMarkdownPreview(uri: vscode.Uri, markdown: string): void {
    const basename = path.basename(uri.fsPath);
    const panel = vscode.window.createWebviewPanel(
        'rpaSkillsDocumentMarkdownPreview',
        `Markdown Preview: ${basename}`,
        vscode.ViewColumn.Active,
        {
            enableScripts: false,
            retainContextWhenHidden: true
        }
    );

    panel.webview.html = renderMarkdownPreviewHtml(basename, uri.fsPath, markdown);
}

function renderMarkdownPreviewHtml(title: string, filePath: string, markdown: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${escapeHtml(title)}</title>
    <style>
        :root {
            color-scheme: light dark;
        }
        body {
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            line-height: 1.55;
            margin: 0;
            padding: 22px;
        }
        h1 {
            font-size: 24px;
            margin: 0 0 4px;
        }
        h2 {
            border-top: 1px solid var(--vscode-panel-border);
            font-size: 18px;
            margin: 24px 0 10px;
            padding-top: 14px;
        }
        h3 {
            font-size: 15px;
            margin: 18px 0 8px;
        }
        h4, h5, h6 {
            font-size: 13px;
            margin: 14px 0 8px;
        }
        a {
            color: var(--vscode-textLink-foreground);
        }
        code {
            background: var(--vscode-textCodeBlock-background);
            border-radius: 3px;
            padding: 1px 4px;
        }
        pre {
            background: var(--vscode-textCodeBlock-background);
            border-radius: 4px;
            margin: 10px 0;
            overflow: auto;
            padding: 10px;
            white-space: pre-wrap;
        }
        blockquote {
            border-left: 3px solid var(--vscode-panel-border);
            color: var(--vscode-descriptionForeground);
            margin: 8px 0;
            padding-left: 12px;
        }
        table {
            border-collapse: collapse;
            margin: 10px 0;
            max-width: 100%;
            overflow-x: auto;
        }
        th, td {
            border: 1px solid var(--vscode-panel-border);
            padding: 5px 8px;
            text-align: left;
            vertical-align: top;
        }
        th {
            color: var(--vscode-descriptionForeground);
            font-weight: 600;
        }
        .meta {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            margin-bottom: 18px;
            overflow-wrap: anywhere;
        }
        .preview {
            max-width: 980px;
        }
        details {
            border-top: 1px solid var(--vscode-panel-border);
            margin-top: 26px;
            padding-top: 14px;
        }
        summary {
            cursor: pointer;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <h1>${escapeHtml(title)}</h1>
    <div class="meta">${escapeHtml(filePath)}</div>
    <main class="preview">
        ${markdownToHtml(markdown)}
    </main>
    <details>
        <summary>Raw Markdown</summary>
        <pre>${escapeHtml(markdown)}</pre>
    </details>
</body>
</html>`;
}

function markdownToHtml(markdown: string): string {
    const lines = markdown.replace(/\r\n/g, '\n').split('\n');
    const html: string[] = [];
    let paragraph: string[] = [];
    let inCodeFence = false;
    let codeLines: string[] = [];
    let listType: 'ul' | 'ol' | undefined;
    let tableRows: string[][] = [];

    const flushParagraph = () => {
        if (paragraph.length === 0) {
            return;
        }
        html.push(`<p>${inlineMarkdown(escapeHtml(paragraph.join(' ')))}</p>`);
        paragraph = [];
    };

    const flushList = () => {
        if (listType) {
            html.push(`</${listType}>`);
            listType = undefined;
        }
    };

    const flushTable = () => {
        if (tableRows.length === 0) {
            return;
        }

        const [header, ...bodyRows] = tableRows;
        html.push('<table>');
        html.push(`<thead><tr>${header.map((cell) => `<th>${inlineMarkdown(escapeHtml(cell.trim()))}</th>`).join('')}</tr></thead>`);
        if (bodyRows.length > 0) {
            html.push('<tbody>');
            for (const row of bodyRows) {
                html.push(`<tr>${row.map((cell) => `<td>${inlineMarkdown(escapeHtml(cell.trim()))}</td>`).join('')}</tr>`);
            }
            html.push('</tbody>');
        }
        html.push('</table>');
        tableRows = [];
    };

    const flushBlocks = () => {
        flushParagraph();
        flushList();
        flushTable();
    };

    for (const line of lines) {
        if (line.trim().startsWith('```')) {
            if (inCodeFence) {
                html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
                codeLines = [];
                inCodeFence = false;
            } else {
                flushBlocks();
                inCodeFence = true;
            }
            continue;
        }

        if (inCodeFence) {
            codeLines.push(line);
            continue;
        }

        const trimmed = line.trim();
        if (!trimmed) {
            flushBlocks();
            continue;
        }

        const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
        if (heading) {
            flushBlocks();
            const level = Math.min(heading[1].length, 6);
            html.push(`<h${level}>${inlineMarkdown(escapeHtml(heading[2]))}</h${level}>`);
            continue;
        }

        if (isMarkdownTableRow(trimmed)) {
            flushParagraph();
            flushList();
            const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|');
            if (!isMarkdownTableDivider(cells)) {
                tableRows.push(cells);
            }
            continue;
        }

        flushTable();

        const unordered = trimmed.match(/^[-*+]\s+(.+)$/);
        if (unordered) {
            flushParagraph();
            if (listType !== 'ul') {
                flushList();
                listType = 'ul';
                html.push('<ul>');
            }
            html.push(`<li>${inlineMarkdown(escapeHtml(unordered[1]))}</li>`);
            continue;
        }

        const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
        if (ordered) {
            flushParagraph();
            if (listType !== 'ol') {
                flushList();
                listType = 'ol';
                html.push('<ol>');
            }
            html.push(`<li>${inlineMarkdown(escapeHtml(ordered[1]))}</li>`);
            continue;
        }

        if (trimmed.startsWith('> ')) {
            flushBlocks();
            html.push(`<blockquote>${inlineMarkdown(escapeHtml(trimmed.slice(2)))}</blockquote>`);
            continue;
        }

        flushList();
        paragraph.push(trimmed);
    }

    if (inCodeFence) {
        html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
    }
    flushBlocks();

    return html.join('\n');
}

function isMarkdownTableRow(line: string): boolean {
    return line.includes('|') && line.split('|').length >= 3;
}

function isMarkdownTableDivider(cells: string[]): boolean {
    return cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function inlineMarkdown(value: string): string {
    return value
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
