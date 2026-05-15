import * as vscode from 'vscode';
import { getRpaSkillsConfigValue, getWorkspaceRoot } from './config';
import { getQuickSetupDefaultTargetId, getTargetStatuses, IdeTargetStatus, loadConfiguredMcpServers } from './ideTargets';
import { collectPromptFiles, PromptFile } from './promptManager';
import { WatchController } from './watchController';
import { NormalizedGroup } from './types';

export interface QuickSetupRequest {
    targetId: string;
    groupIds: string[];
}

export class AssistantDashboard implements vscode.Disposable {
    private panel?: vscode.WebviewPanel;
    private readonly disposables: vscode.Disposable[] = [];

    constructor(
        private readonly watchController: WatchController,
        private readonly listSkillGroups: () => Promise<NormalizedGroup[]>,
        private readonly runQuickSetup: (request: QuickSetupRequest) => Promise<void>
    ) {
        this.watchController.onDidChangeWatchedFiles(() => {
            this.refresh();
        }, undefined, this.disposables);
    }

    async show(): Promise<void> {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.Active);
            await this.refresh();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'rpaSkillsAssistantDashboard',
            'RPA Skills: Assistant Setup',
            vscode.ViewColumn.Active,
            {
                enableCommandUris: true,
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.panel.onDidDispose(() => {
            this.panel = undefined;
        }, undefined, this.disposables);

        this.panel.webview.onDidReceiveMessage(async (message) => {
            if (!isQuickSetupMessage(message)) {
                return;
            }

            try {
                await this.runQuickSetup({
                    targetId: message.targetId,
                    groupIds: message.groupIds
                });
                await this.refresh();
            } catch (error: any) {
                vscode.window.showErrorMessage(`Quick setup failed: ${error.message || String(error)}`);
            }
        }, undefined, this.disposables);

        await this.refresh();
    }

    async refresh(): Promise<void> {
        if (!this.panel) {
            return;
        }

        try {
            this.panel.webview.html = await this.renderHtml();
        } catch (error: any) {
            this.panel.webview.html = renderErrorHtml(error.message || String(error));
        }
    }

    dispose(): void {
        this.panel?.dispose();
        for (const disposable of this.disposables) {
            disposable.dispose();
        }
    }

    private async renderHtml(): Promise<string> {
        const workspaceRoot = getWorkspaceRoot();
        const targets = getTargetStatuses();
        const skillGroups = await this.listSkillGroups();
        const quickSetupDefaultTargetId = getQuickSetupDefaultTargetId(targets);
        const promptFiles = collectPromptFiles();
        const mcpServers = await loadConfiguredMcpServers();
        const mcpServerNames = Object.keys(mcpServers);
        const registryUrl = getRpaSkillsConfigValue<string>('registryUrl') || '';
        const skillsPath = getRpaSkillsConfigValue<string>('skills.path') || '.agent/skills';
        const watchLabel = this.watchController.isRunning ? 'Running' : 'Stopped';
        const watchCommand = this.watchController.isRunning ? 'rpaSkills.stopWatch' : 'rpaSkills.startWatch';
        const watchAction = this.watchController.isRunning ? 'Stop Watch' : 'Start Watch';
        const mcpSkillRouterEnabled = getRpaSkillsConfigValue<boolean>('mcp.enableSkillRouter') ?? true;
        const targetCounts = {
            all: targets.length,
            detected: targets.filter((target) => target.detected).length,
            skills: targets.filter((target) => target.installMode === 'skillDirectory').length,
            rules: targets.filter((target) => target.installMode === 'markdownRule').length,
            mcp: targets.filter((target) => target.mcpConfigPath).length
        };
        const promptCounts = {
            all: promptFiles.length,
            agent: promptFiles.filter((file) => file.category === 'agent').length,
            skill: promptFiles.filter((file) => file.category === 'skill').length,
            mcp: promptFiles.filter((file) => file.category === 'mcp').length,
            ide: promptFiles.filter((file) => file.category === 'ide').length
        };
        const nonce = createNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPA Skills Assistant Setup</title>
    <style>
        :root {
            color-scheme: light dark;
        }
        body {
            color: var(--vscode-editor-foreground);
            background: var(--vscode-editor-background);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            line-height: 1.45;
            margin: 0;
            padding: 22px;
        }
        h1 {
            font-size: 24px;
            margin: 0 0 6px;
        }
        h2 {
            font-size: 17px;
            margin: 0;
        }
        h3 {
            font-size: 14px;
            margin: 0 0 4px;
        }
        a {
            color: var(--vscode-textLink-foreground);
        }
        .toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }
        .quick-setup {
            border: 1px solid var(--vscode-focusBorder);
            border-radius: 6px;
            margin: 0 0 18px;
            padding: 12px;
        }
        .quick-setup-header {
            align-items: flex-start;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .quick-setup-title {
            min-width: 220px;
        }
        .quick-setup-controls {
            align-items: flex-end;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .field {
            display: grid;
            gap: 4px;
        }
        .field label {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
        }
        .select-input {
            background: var(--vscode-dropdown-background);
            border: 1px solid var(--vscode-dropdown-border, var(--vscode-panel-border));
            border-radius: 4px;
            color: var(--vscode-dropdown-foreground);
            min-height: 28px;
            min-width: 240px;
            padding: 3px 8px;
        }
        .table-wrap {
            overflow-x: auto;
        }
        .group-table {
            border-collapse: collapse;
            min-width: 620px;
            width: 100%;
        }
        .group-table th,
        .group-table td {
            border-top: 1px solid var(--vscode-panel-border);
            padding: 7px 8px;
            text-align: left;
            vertical-align: top;
        }
        .group-table th {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            font-weight: 600;
        }
        .group-check {
            width: 1%;
            white-space: nowrap;
        }
        .button {
            align-items: center;
            background: var(--vscode-button-background);
            border: 0;
            border-radius: 4px;
            color: var(--vscode-button-foreground);
            cursor: pointer;
            display: inline-flex;
            min-height: 28px;
            padding: 4px 10px;
            text-decoration: none;
        }
        .button.secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        .button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .grid {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        }
        .panel {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 12px;
        }
        .section {
            border-top: 1px solid var(--vscode-panel-border);
            margin-top: 22px;
            padding-top: 14px;
        }
        .section-header {
            align-items: center;
            display: flex;
            gap: 12px;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .section-title {
            min-width: 0;
        }
        .section-actions {
            display: flex;
            flex: 0 0 auto;
            gap: 6px;
        }
        .section.is-collapsed .section-body {
            display: none;
        }
        .icon-button {
            background: var(--vscode-button-secondaryBackground);
            border: 0;
            border-radius: 4px;
            color: var(--vscode-button-secondaryForeground);
            cursor: pointer;
            min-height: 28px;
            padding: 4px 9px;
        }
        .icon-button:hover {
            background: var(--vscode-button-hoverBackground);
            color: var(--vscode-button-foreground);
        }
        .meta {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            overflow-wrap: anywhere;
        }
        .hint {
            color: var(--vscode-descriptionForeground);
            margin: 0 0 12px;
            max-width: 920px;
        }
        .flow {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0 16px;
        }
        .step {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            padding: 3px 8px;
        }
        .status {
            display: inline-block;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 999px;
            font-size: 12px;
            margin: 2px 4px 2px 0;
            padding: 1px 7px;
        }
        .status.good {
            border-color: var(--vscode-testing-iconPassed);
            color: var(--vscode-testing-iconPassed);
        }
        .status.warn {
            border-color: var(--vscode-notificationsWarningIcon-foreground);
            color: var(--vscode-notificationsWarningIcon-foreground);
        }
        .tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin: 8px 0 10px;
        }
        .tab {
            background: transparent;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            color: var(--vscode-editor-foreground);
            cursor: pointer;
            min-height: 28px;
            padding: 3px 9px;
        }
        .tab:hover {
            background: var(--vscode-toolbar-hoverBackground);
        }
        .tab.is-active {
            background: var(--vscode-button-secondaryBackground);
            border-color: var(--vscode-focusBorder);
            color: var(--vscode-button-secondaryForeground);
        }
        .search-row {
            align-items: center;
            display: flex;
            gap: 8px;
            margin: 8px 0 12px;
        }
        .search-input {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border, var(--vscode-panel-border));
            border-radius: 4px;
            color: var(--vscode-input-foreground);
            min-height: 28px;
            padding: 4px 8px;
            width: min(520px, 100%);
        }
        .search-input:focus {
            border-color: var(--vscode-focusBorder);
            outline: 0;
        }
        .result-count {
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            white-space: nowrap;
        }
        .row-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        code {
            background: var(--vscode-textCodeBlock-background);
            border-radius: 3px;
            padding: 1px 4px;
        }
        details {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            margin-bottom: 8px;
            padding: 8px 10px;
        }
        summary {
            cursor: pointer;
            display: flex;
            gap: 8px;
            justify-content: space-between;
        }
        pre {
            background: var(--vscode-textCodeBlock-background);
            border-radius: 4px;
            margin: 8px 0 0;
            max-height: 360px;
            overflow: auto;
            padding: 10px;
            white-space: pre-wrap;
        }
        .empty {
            color: var(--vscode-descriptionForeground);
            margin: 8px 0;
        }
        .is-hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <h1>Assistant Setup</h1>
    <p class="hint">Start with the registry skills, install the selected skill into your workspace, then mirror it to the IDEs that should load it.</p>
    <div class="flow">
        <span class="step">1. Check registry</span>
        <span class="step">2. Install skill</span>
        <span class="step">3. Install to IDE</span>
        <span class="step">4. Activate MCP if needed</span>
        <span class="step">5. Edit prompts</span>
    </div>
    ${renderQuickSetupPanel(targets, skillGroups, quickSetupDefaultTargetId)}
    <div class="toolbar">
        ${button('Refresh', 'rpaSkills.refreshSkills', [], false, 'Reload registry data and rescan installed workspace skills.')}
        ${button('Settings', 'rpaSkills.openSettings', [], true, 'Open extension settings such as registry URL, skills path, and MCP source config.')}
        ${button(watchAction, watchCommand, [], true, 'Watch prompt, skill, rule, and MCP files so the dashboard refreshes after local edits.')}
        ${button('New AGENTS.md', 'rpaSkills.createMainInstruction', [], true, 'Create or open the workspace-wide agent instruction file.')}
        ${button(mcpSkillRouterEnabled ? 'Disable Skill Router' : 'Enable Skill Router', 'rpaSkills.toggleMcpSkillRouter', [], true, 'Toggle MCP skill routing capability for IDEs')}
        <button class="icon-button" type="button" data-expand-all title="Expand all dashboard sections">Expand All</button>
        <button class="icon-button" type="button" data-collapse-all title="Collapse all dashboard sections">Collapse All</button>
    </div>

    <section class="section" data-section="workspace">
        ${renderSectionHeader('Workspace', 'Active workspace, registry source, canonical skill folder, and loaded MCP server count.')}
        <div class="section-body">
            <div class="panel">
                <div class="meta"><code>${escapeHtml(workspaceRoot)}</code></div>
                <div>
                    <span class="status ${this.watchController.isRunning ? 'good' : 'warn'}" title="Local file watch keeps the dashboard and tree state fresh after edits.">Watch ${escapeHtml(watchLabel)}</span>
                    <span class="status ${mcpSkillRouterEnabled ? 'good' : 'warn'}" title="When enabled, the skill router is registered in MCP files so agents can search installed skills dynamically.">Skill Router ${mcpSkillRouterEnabled ? 'Enabled' : 'Disabled'}</span>
                    <span class="status" title="The manifest URL used to load skill groups.">Registry ${escapeHtml(registryUrl || 'not set')}</span>
                    <span class="status" title="Canonical workspace install folder used by the normal Install action.">Skills ${escapeHtml(skillsPath)}</span>
                    <span class="status" title="MCP servers loaded from rpaSkills.mcp.servers or configured MCP files.">MCP ${mcpServerNames.length} servers</span>
                </div>
            </div>
        </div>
    </section>

    <section class="section" data-section="targets">
        ${renderSectionHeader('IDE Targets', 'Install a registry skill into each IDE format. Use tabs to separate installed targets, skill-folder targets, rule-file targets, and MCP-capable targets.')}
        <div class="section-body">
            <p class="hint">Rule-based IDEs receive a generated markdown rule file; skill-based IDEs receive a full skill folder.</p>
            <div class="tabs" role="tablist" aria-label="IDE target groups">
                ${renderTab('target', 'all', `All ${targetCounts.all}`, true)}
                ${renderTab('target', 'detected', `Detected ${targetCounts.detected}`)}
                ${renderTab('target', 'skills', `Skill folders ${targetCounts.skills}`)}
                ${renderTab('target', 'rules', `Rule files ${targetCounts.rules}`)}
                ${renderTab('target', 'mcp', `MCP ${targetCounts.mcp}`)}
            </div>
            <div class="search-row">
                <input class="search-input" data-search="target" type="search" placeholder="Search IDE target, path, or status">
                <span class="result-count" data-result-count="target"></span>
            </div>
            <div class="grid" data-list="target">
                ${targets.map(renderTargetCard).join('')}
            </div>
            <div class="empty is-hidden" data-empty="target">No IDE targets match this tab or search.</div>
        </div>
    </section>

    <section class="section" data-section="mcp">
        ${renderSectionHeader('MCP Source', 'Source servers used when activating MCP for an IDE.')}
        <div class="section-body">
            <p class="hint">These servers come from extension settings first, then from configured MCP files such as <code>.mcp.json</code>.</p>
            <div class="panel">
                ${mcpServerNames.length
                    ? mcpServerNames.map((name) => `<span class="status">${escapeHtml(name)}</span>`).join('')
                    : '<div class="empty">No MCP servers loaded. Add servers in rpaSkills.mcp.servers or point rpaSkills.mcp.configPaths to an existing config file.</div>'}
            </div>
        </div>
    </section>

    <section class="section" data-section="prompts">
        ${renderSectionHeader('Prompts', 'Search and manage agent instructions, SKILL.md files, MCP configs, and IDE rule files by group.')}
        <div class="section-body">
            <p class="hint">The preview is read-only. Use Edit to open the real file.</p>
            <div class="tabs" role="tablist" aria-label="Prompt groups">
                ${renderTab('prompt', 'all', `All ${promptCounts.all}`, true)}
                ${renderTab('prompt', 'agent', `Agent Instructions ${promptCounts.agent}`)}
                ${renderTab('prompt', 'skill', `Skill Markdown ${promptCounts.skill}`)}
                ${renderTab('prompt', 'mcp', `MCP Config ${promptCounts.mcp}`)}
                ${renderTab('prompt', 'ide', `IDE Rules ${promptCounts.ide}`)}
            </div>
            <div class="search-row">
                <input class="search-input" data-search="prompt" type="search" placeholder="Search prompt file path or preview text">
                <span class="result-count" data-result-count="prompt"></span>
            </div>
            <div data-list="prompt">
                ${promptFiles.map(renderPromptFile).join('')}
            </div>
            <div class="empty is-hidden" data-empty="prompt">No prompt files match this tab or search.</div>
        </div>
    </section>
    <script nonce="${nonce}">
        ${renderDashboardScript()}
    </script>
</body>
</html>`;
    }
}

function renderSectionHeader(title: string, hint: string): string {
    return `<div class="section-header">
    <div class="section-title">
        <h2>${escapeHtml(title)}</h2>
        <p class="hint">${escapeHtml(hint)}</p>
    </div>
    <div class="section-actions">
        <button class="icon-button" type="button" data-section-toggle title="Collapse or expand this section">Collapse</button>
    </div>
</div>`;
}

function renderQuickSetupPanel(
    targets: IdeTargetStatus[],
    skillGroups: NormalizedGroup[],
    defaultTargetId: string
): string {
    const selectedTarget = targets.find((target) => target.id === defaultTargetId);
    const mcpHint = selectedTarget?.mcpConfigPath
        ? `MCP will be activated in ${selectedTarget.mcpConfigPath}.`
        : 'This target has no MCP config path, so quick setup will only install selected skills.';

    return `<section class="quick-setup" aria-label="Quick setup">
    <div class="quick-setup-header">
        <div class="quick-setup-title">
            <h2>Quick Setup</h2>
            <p class="hint">Auto-detect the current IDE target, install selected skill groups, and activate MCP when the target supports it.</p>
            <div class="meta" data-quick-target-hint>${escapeHtml(mcpHint)}</div>
        </div>
        <div class="quick-setup-controls">
            <div class="field">
                <label for="quick-setup-target">IDE selection</label>
                <select id="quick-setup-target" class="select-input" data-quick-target>
                    ${targets.map((target) => renderQuickSetupTargetOption(target, defaultTargetId)).join('')}
                </select>
            </div>
            <button class="button" type="button" data-quick-setup-run title="Install selected groups and IDE settings">Quick Setup</button>
        </div>
    </div>
    <div class="table-wrap">
        <table class="group-table">
            <thead>
                <tr>
                    <th class="group-check">
                        <label title="Select or clear all skill groups">
                            <input type="checkbox" data-quick-check-all checked>
                            All
                        </label>
                    </th>
                    <th>Skill group</th>
                    <th>Detail</th>
                    <th>Skills</th>
                </tr>
            </thead>
            <tbody>
                ${skillGroups.length
                    ? skillGroups.map(renderQuickSetupGroupRow).join('')
                    : '<tr><td colspan="4" class="empty">No registry groups loaded. Configure the registry URL, then refresh.</td></tr>'}
            </tbody>
        </table>
    </div>
</section>`;
}

function renderQuickSetupTargetOption(target: IdeTargetStatus, defaultTargetId: string): string {
    const badges = [
        target.currentIde ? 'current IDE' : '',
        target.detected ? 'detected' : 'not created',
        target.installMode === 'markdownRule' ? 'rule file' : 'skill folder',
        target.mcpConfigPath ? 'MCP' : ''
    ].filter(Boolean).join(', ');

    return `<option value="${escapeHtml(target.id)}" data-mcp-path="${escapeHtml(target.mcpConfigPath || '')}"${target.id === defaultTargetId ? ' selected' : ''}>${escapeHtml(target.name)} - ${escapeHtml(badges)}</option>`;
}

function renderQuickSetupGroupRow(group: NormalizedGroup): string {
    const detail = group.description || group.name;

    return `<tr>
    <td class="group-check"><input type="checkbox" data-quick-group value="${escapeHtml(group.id)}" checked></td>
    <td><strong>${escapeHtml(group.name)}</strong><div class="meta"><code>${escapeHtml(group.id)}</code></div></td>
    <td>${escapeHtml(detail)}</td>
    <td>${group.skills.length}</td>
</tr>`;
}

function renderTab(scope: 'target' | 'prompt', group: string, label: string, active = false): string {
    return `<button class="tab${active ? ' is-active' : ''}" type="button" role="tab" data-tab-scope="${scope}" data-tab="${group}">${escapeHtml(label)}</button>`;
}

function renderTargetCard(target: IdeTargetStatus): string {
    const groups = [
        'all',
        target.detected ? 'detected' : 'missing',
        target.installMode === 'markdownRule' ? 'rules' : 'skills',
        target.mcpConfigPath ? 'mcp' : ''
    ].filter(Boolean).join(' ');
    const searchText = [
        target.name,
        target.description,
        target.skillPath,
        target.mcpConfigPath || '',
        target.detected ? 'detected' : 'not created',
        target.installMode === 'markdownRule' ? 'rule markdown' : 'skill folder'
    ].join(' ');

    return `<div class="panel" data-item="target" data-groups="${escapeHtml(groups)}" data-search-text="${escapeHtml(searchText.toLowerCase())}">
    <h3>${escapeHtml(target.name)}</h3>
    <div class="meta">${escapeHtml(target.description)}</div>
    <div>
        <span class="status ${target.detected ? 'good' : 'warn'}" title="Detected means this workspace already has a folder or config for the target.">${target.detected ? 'Detected' : 'Not created'}</span>
        ${target.currentIde ? '<span class="status good" title="Matched from the VS Code-compatible host app name.">Current IDE</span>' : ''}
        <span class="status" title="Current number of installed skill or rule entries for this target.">${target.installMode === 'markdownRule' ? 'Rules' : 'Skills'} ${target.skillEntryCount}</span>
        ${target.mcpConfigPath ? `<span class="status ${target.mcpConfigured ? 'good' : 'warn'}" title="MCP status for the target config file.">MCP ${target.activeMcpServers} active / ${target.disabledMcpServers} disabled</span>` : ''}
    </div>
    <div class="meta"><code>${escapeHtml(target.skillPath)}</code></div>
    <div class="row-actions">
        ${button('Install Skill', 'rpaSkills.installSkillToIde', [{ targetId: target.id }], false, `Install a selected skill into ${target.name}'s expected folder or rule format.`)}
        ${target.mcpConfigPath ? button('Activate MCP', 'rpaSkills.activateMcpForIde', [target.id], true, `Write enabled MCP servers into ${target.mcpConfigPath}. Restart ${target.name} if it does not reload MCP automatically.`) : ''}
        ${target.mcpConfigPath ? button('Disable MCP', 'rpaSkills.deactivateMcpForIde', [target.id], true, `Keep MCP config in ${target.mcpConfigPath} but mark managed servers disabled.`) : ''}
        ${target.mcpConfigPath ? button('Edit MCP', 'rpaSkills.openPromptFile', [target.mcpConfigPath], true, `Open ${target.mcpConfigPath} for manual review or edits.`) : ''}
    </div>
</div>`;
}

function renderPromptFile(file: PromptFile): string {
    const searchText = [file.relativePath, file.category, file.preview].join(' ').toLowerCase();
    return `<details data-item="prompt" data-groups="all ${escapeHtml(file.category)}" data-search-text="${escapeHtml(searchText)}">
    <summary>
        <span>${escapeHtml(file.relativePath)} <span class="status">${escapeHtml(promptCategoryLabel(file.category))}</span></span>
        <span>${button('Edit', 'rpaSkills.openPromptFile', [file.relativePath], false, `Open ${file.relativePath} in the editor.`)}</span>
    </summary>
    ${file.exists
        ? `<pre>${escapeHtml(file.preview)}</pre>`
        : '<div class="empty">Missing file.</div>'}
</details>`;
}

function button(label: string, command: string, args: unknown[] = [], secondary = false, tooltip?: string): string {
    const href = vscode.Uri.parse(`command:${command}?${encodeURIComponent(JSON.stringify(args))}`).toString();
    const title = tooltip ? ` title="${escapeHtml(tooltip)}"` : '';
    return `<a class="button${secondary ? ' secondary' : ''}" href="${href}"${title}>${escapeHtml(label)}</a>`;
}

function promptCategoryLabel(category: PromptFile['category']): string {
    switch (category) {
        case 'agent':
            return 'Agent';
        case 'skill':
            return 'Skill';
        case 'mcp':
            return 'MCP';
        case 'ide':
            return 'IDE';
    }
}

function renderDashboardScript(): string {
    return `
(function () {
    const vscodeApi = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : undefined;
    const state = {
        target: { tab: 'all', query: '' },
        prompt: { tab: 'all', query: '' }
    };

    function closestSection(element) {
        return element.closest('[data-section]');
    }

    function updateSectionButton(section) {
        const button = section.querySelector('[data-section-toggle]');
        if (!button) {
            return;
        }
        button.textContent = section.classList.contains('is-collapsed') ? 'Expand' : 'Collapse';
    }

    function itemMatches(item, scope) {
        const groups = (item.dataset.groups || '').split(/\\s+/);
        const tab = state[scope].tab;
        const query = state[scope].query;
        const groupMatches = tab === 'all' || groups.includes(tab);
        const searchText = item.dataset.searchText || '';
        const queryMatches = !query || searchText.includes(query);
        return groupMatches && queryMatches;
    }

    function applyFilter(scope) {
        const items = Array.from(document.querySelectorAll('[data-item="' + scope + '"]'));
        let visible = 0;
        for (const item of items) {
            const matches = itemMatches(item, scope);
            item.classList.toggle('is-hidden', !matches);
            if (matches) {
                visible++;
            }
        }

        const count = document.querySelector('[data-result-count="' + scope + '"]');
        if (count) {
            count.textContent = visible + ' shown';
        }

        const empty = document.querySelector('[data-empty="' + scope + '"]');
        if (empty) {
            empty.classList.toggle('is-hidden', visible !== 0);
        }
    }

    document.querySelectorAll('[data-section-toggle]').forEach((button) => {
        const section = closestSection(button);
        if (!section) {
            return;
        }
        updateSectionButton(section);
        button.addEventListener('click', () => {
            section.classList.toggle('is-collapsed');
            updateSectionButton(section);
        });
    });

    document.querySelector('[data-collapse-all]')?.addEventListener('click', () => {
        document.querySelectorAll('[data-section]').forEach((section) => {
            section.classList.add('is-collapsed');
            updateSectionButton(section);
        });
    });

    document.querySelector('[data-expand-all]')?.addEventListener('click', () => {
        document.querySelectorAll('[data-section]').forEach((section) => {
            section.classList.remove('is-collapsed');
            updateSectionButton(section);
        });
    });

    document.querySelectorAll('[data-tab-scope]').forEach((tabButton) => {
        tabButton.addEventListener('click', () => {
            const scope = tabButton.dataset.tabScope;
            const tab = tabButton.dataset.tab || 'all';
            state[scope].tab = tab;
            document.querySelectorAll('[data-tab-scope="' + scope + '"]').forEach((other) => {
                other.classList.toggle('is-active', other === tabButton);
            });
            applyFilter(scope);
        });
    });

    document.querySelectorAll('[data-search]').forEach((input) => {
        input.addEventListener('input', () => {
            const scope = input.dataset.search;
            state[scope].query = (input.value || '').trim().toLowerCase();
            applyFilter(scope);
        });
    });

    function quickGroupChecks() {
        return Array.from(document.querySelectorAll('[data-quick-group]'));
    }

    function updateQuickCheckAll() {
        const checkAll = document.querySelector('[data-quick-check-all]');
        if (!checkAll) {
            return;
        }

        const checks = quickGroupChecks();
        const checked = checks.filter((checkbox) => checkbox.checked);
        checkAll.checked = checks.length > 0 && checked.length === checks.length;
        checkAll.indeterminate = checked.length > 0 && checked.length < checks.length;
    }

    document.querySelector('[data-quick-check-all]')?.addEventListener('change', (event) => {
        const checked = event.target.checked;
        quickGroupChecks().forEach((checkbox) => {
            checkbox.checked = checked;
        });
        updateQuickCheckAll();
    });

    quickGroupChecks().forEach((checkbox) => {
        checkbox.addEventListener('change', updateQuickCheckAll);
    });

    document.querySelector('[data-quick-target]')?.addEventListener('change', (event) => {
        const selected = event.target.selectedOptions[0];
        const mcpPath = selected?.dataset.mcpPath || '';
        const hint = document.querySelector('[data-quick-target-hint]');
        if (hint) {
            hint.textContent = mcpPath
                ? 'MCP will be activated in ' + mcpPath + '.'
                : 'This target has no MCP config path, so quick setup will only install selected skills.';
        }
    });

    document.querySelector('[data-quick-setup-run]')?.addEventListener('click', () => {
        const target = document.querySelector('[data-quick-target]');
        const targetId = target?.value || '';
        const groupIds = quickGroupChecks()
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value);

        vscodeApi?.postMessage({
            type: 'quickSetup',
            targetId,
            groupIds
        });
    });

    applyFilter('target');
    applyFilter('prompt');
    updateQuickCheckAll();
}());
`;
}

function isQuickSetupMessage(message: unknown): message is QuickSetupRequest & { type: 'quickSetup' } {
    if (typeof message !== 'object' || message === null) {
        return false;
    }

    const candidate = message as { type?: unknown; targetId?: unknown; groupIds?: unknown };
    return candidate.type === 'quickSetup'
        && typeof candidate.targetId === 'string'
        && Array.isArray(candidate.groupIds)
        && candidate.groupIds.every((groupId) => typeof groupId === 'string');
}

function createNonce(): string {
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let index = 0; index < 16; index++) {
        nonce += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return nonce;
}

function renderErrorHtml(message: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>RPA Skills</title></head>
<body>
    <h1>Assistant Setup</h1>
    <p>${escapeHtml(message)}</p>
</body>
</html>`;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}
