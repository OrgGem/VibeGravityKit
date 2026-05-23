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
    '.xlsb',
    '.pdf',
    '.html',
    '.htm'
]);

const openWebviewPanels = new Map<string, vscode.WebviewPanel>();

function isDocumentCurrentlyPreviewed(uri: vscode.Uri): boolean {
    const uriStr = uri.toString();
    
    // Check if open as Webview Panel
    if (openWebviewPanels.has(uriStr)) {
        return true;
    }

    // Check if open as Custom Editor in active/visible tabs
    for (const group of vscode.window.tabGroups.all) {
        for (const tab of group.tabs) {
            if (tab.input instanceof vscode.TabInputCustom && tab.input.viewType === 'rpaSkills.documentMarkdownPreview') {
                if (tab.input.uri.toString() === uriStr) {
                    return true;
                }
            }
        }
    }

    return false;
}

async function switchToSourceEditor(uri: vscode.Uri): Promise<void> {
    const uriStr = uri.toString();

    // If it's open as Webview Panel, close the panel and show as text document
    const panel = openWebviewPanels.get(uriStr);
    if (panel) {
        panel.dispose();
        await vscode.window.showTextDocument(uri, {
            viewColumn: vscode.ViewColumn.Active,
            preview: false
        });
        return;
    }

    // If it's a Custom Editor, open it with default editor to swap back
    await vscode.commands.executeCommand(
        'vscode.openWith',
        uri,
        'default',
        vscode.ViewColumn.Active
    );
}

export async function previewDocumentAsMarkdown(input?: vscode.Uri): Promise<void> {
    const uri = await resolveDocumentUri(input);
    if (!uri) {
        return;
    }

    const extension = path.extname(uri.fsPath).toLowerCase();
    if (!supportedExtensions.has(extension)) {
        vscode.window.showErrorMessage('Please select a supported document (Word, Excel, PowerPoint, PDF, or HTML).');
        return;
    }

    // Toggle: if already in preview, switch back to editor
    if (isDocumentCurrentlyPreviewed(uri)) {
        await switchToSourceEditor(uri);
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

    // Try active Custom Editor tab
    const activeTab = vscode.window.tabGroups.activeTabGroup.activeTab;
    if (activeTab && activeTab.input instanceof vscode.TabInputCustom && activeTab.input.viewType === 'rpaSkills.documentMarkdownPreview') {
        return activeTab.input.uri;
    }

    // Try active Webview Panel
    for (const [uriStr, panel] of openWebviewPanels.entries()) {
        if (panel.active) {
            return vscode.Uri.parse(uriStr);
        }
    }

    const picked = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: {
            'Supported Documents': ['docx', 'docm', 'pptx', 'pptm', 'xlsx', 'xlsm', 'xls', 'xlsb', 'pdf', 'html', 'htm']
        },
        title: 'Select a document to preview as Markdown'
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
                windowsHide: true,
                env: {
                    ...process.env,
                    PYTHONIOENCODING: 'utf-8'
                }
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
    
    // If a panel is already open for this uri, reveal it
    const existingPanel = openWebviewPanels.get(uri.toString());
    if (existingPanel) {
        existingPanel.reveal(vscode.ViewColumn.Active);
        return;
    }

    const panel = vscode.window.createWebviewPanel(
        'rpaSkillsDocumentMarkdownPreview',
        `Markdown Preview: ${basename}`,
        vscode.ViewColumn.Active,
        {
            enableScripts: true,
            retainContextWhenHidden: true
        }
    );

    openWebviewPanels.set(uri.toString(), panel);

    panel.webview.html = renderMarkdownPreviewHtml(basename, uri.fsPath, markdown);

    panel.webview.onDidReceiveMessage(async (message) => {
        if (message.type === 'switchToSource') {
            panel.dispose();
            await vscode.window.showTextDocument(uri, {
                viewColumn: vscode.ViewColumn.Active,
                preview: false
            });
        }
    });

    panel.onDidDispose(() => {
        openWebviewPanels.delete(uri.toString());
    });
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
        .preview-header-bar {
            position: sticky;
            top: 0;
            z-index: 100;
            background: var(--vscode-editor-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 16px;
            margin: -22px -22px 20px -22px;
        }
        .toolbar-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--vscode-descriptionForeground);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding-right: 12px;
        }
        .toolbar-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            padding: 5px 11px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
            transition: background 0.15s ease;
        }
        .toolbar-btn:hover {
            background: var(--vscode-button-hoverBackground);
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
    <div class="preview-header-bar">
        <span class="toolbar-title">${escapeHtml(title)}</span>
        <button class="toolbar-btn" onclick="switchToSource()" title="Switch back to standard editor / Quay về mã nguồn">
            <svg viewBox="0 0 16 16" fill="currentColor" style="width: 13px; height: 13px;">
                <path fill-rule="evenodd" d="M4.72 3.22a.75.75 0 0 1 1.06 0L9.47 6.97a.75.75 0 0 1 0 1.06l-3.69 3.69a.75.75 0 1 1-1.06-1.06L7.88 7.5 4.72 4.34a.75.75 0 0 1 0-1.06zm4.5 0a.75.75 0 0 1 1.06 0l3.69 3.69a.75.75 0 0 1 0 1.06l-3.69 3.69a.75.75 0 1 1-1.06-1.06l3.16-3.16-3.16-3.16a.75.75 0 0 1 0-1.06z"/>
            </svg>
            Switch to Editor / Quay về mã nguồn
        </button>
    </div>
    <h1>${escapeHtml(title)}</h1>
    <div class="meta">${escapeHtml(filePath)}</div>
    <main class="preview">
        ${markdownToHtml(markdown)}
    </main>
    <details>
        <summary>Raw Markdown</summary>
        <pre>${escapeHtml(markdown)}</pre>
    </details>
    <script>
        const vscode = acquireVsCodeApi();
        function switchToSource() {
            vscode.postMessage({ type: 'switchToSource' });
        }
    </script>
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

export class DocumentMarkdownPreviewProvider implements vscode.CustomReadonlyEditorProvider {
    public static register(context: vscode.ExtensionContext): vscode.Disposable {
        return vscode.window.registerCustomEditorProvider(
            'rpaSkills.documentMarkdownPreview',
            new DocumentMarkdownPreviewProvider(context),
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                },
                supportsMultipleEditorsPerDocument: false
            }
        );
    }

    constructor(private readonly context: vscode.ExtensionContext) {}

    openCustomDocument(
        uri: vscode.Uri,
        openContext: vscode.CustomDocumentOpenContext,
        token: vscode.CancellationToken
    ): vscode.CustomDocument {
        return {
            uri,
            dispose: () => {}
        };
    }

    async resolveCustomEditor(
        document: vscode.CustomDocument,
        webviewPanel: vscode.WebviewPanel,
        token: vscode.CancellationToken
    ): Promise<void> {
        webviewPanel.webview.options = {
            enableScripts: true
        };

        const uri = document.uri;
        const basename = path.basename(uri.fsPath);
        webviewPanel.title = `Markdown Preview: ${basename}`;

        webviewPanel.webview.onDidReceiveMessage(async (message) => {
            if (message.type === 'switchToSource') {
                await vscode.commands.executeCommand(
                    'vscode.openWith',
                    uri,
                    'default',
                    vscode.ViewColumn.Active
                );
            }
        });

        const updateWebview = async () => {
            if (token.isCancellationRequested) {
                return;
            }
            try {
                const markdown = await convertDocumentWithMarkItDown(uri.fsPath);
                webviewPanel.webview.html = renderMarkdownPreviewHtml(basename, uri.fsPath, markdown);
            } catch (error: any) {
                webviewPanel.webview.html = renderMarkdownPreviewHtml(
                    basename,
                    uri.fsPath,
                    `### Conversion Failed\n\n${error.message}`
                );
            }
        };

        await updateWebview();
    }
}
