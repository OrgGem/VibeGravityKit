import * as vscode from 'vscode';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { getRpaSkillsConfigValue, getSkillsRoot, getWorkspaceRootOrUndefined, safeSkillDirectoryName } from './config';
import {
    InstalledSkillRecord,
    NormalizedGroup,
    NormalizedSkill,
    RegistryManifest,
    RegistrySkill,
    SkillStatus
} from './types';

export class SkillsProvider implements vscode.TreeDataProvider<SkillTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SkillTreeItem | undefined | null | void> = new vscode.EventEmitter<SkillTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SkillTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;
    private groups: NormalizedGroup[] = [];
    private installedSkills = new Map<string, InstalledSkillRecord>();
    private manifestLoaded = false;

    constructor(private readonly context: vscode.ExtensionContext) {}

    refresh(): void {
        this.manifestLoaded = false;
        this._onDidChangeTreeData.fire();
    }

    refreshLocalState(): void {
        this.installedSkills = this.scanInstalledSkills();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: SkillTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: SkillTreeItem): Promise<SkillTreeItem[]> {
        await this.ensureLoaded();

        if (!element) {
            return this.groups.map((group) => {
                const groupItem = new SkillTreeItem(
                    group.name,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'group'
                );
                groupItem.group = group;
                groupItem.description = `${group.skills.length} skills`;
                groupItem.tooltip = group.description || group.name;
                return groupItem;
            });
        } else if (element.contextValue === 'group') {
            return (element.group?.skills || []).map((skill) => this.createSkillItem(skill));
        }

        return [];
    }

    findSkillById(skillId: string): NormalizedSkill | undefined {
        return this.groups.flatMap((group) => group.skills).find((skill) => skill.id === skillId);
    }

    findGroupById(groupId: string): NormalizedGroup | undefined {
        return this.groups.find((group) => group.id === groupId);
    }

    getSkillStatus(skill: NormalizedSkill): SkillStatus {
        const installed = this.installedSkills.get(skill.id);
        if (!installed) {
            return { status: 'notInstalled' };
        }

        if (skill.version && installed.version && compareVersions(skill.version, installed.version) > 0) {
            return {
                status: 'updateAvailable',
                installedVersion: installed.version,
                installPath: installed.path
            };
        }

        return {
            status: 'installed',
            installedVersion: installed.version,
            installPath: installed.path
        };
    }

    async openSkillDetails(input: SkillTreeItem | NormalizedSkill | string): Promise<void> {
        await this.ensureLoaded();
        const skill = this.resolveSkillInput(input);

        if (!skill) {
            vscode.window.showErrorMessage('Skill not found in the loaded registry.');
            return;
        }

        const status = this.getSkillStatus(skill);
        const panel = vscode.window.createWebviewPanel(
            'rpaSkillsSkillDetails',
            `RPA Skills: ${skill.name}`,
            vscode.ViewColumn.Active,
            {
                enableCommandUris: true
            }
        );

        panel.webview.html = this.renderSkillDetails(panel.webview, skill, status);
    }

    private async ensureLoaded(): Promise<void> {
        if (this.manifestLoaded) {
            return;
        }

        this.installedSkills = this.scanInstalledSkills();
        this.groups = await this.fetchGroups();
        this.manifestLoaded = true;
    }

    private async fetchGroups(): Promise<NormalizedGroup[]> {
        const registryUrl = getRpaSkillsConfigValue<string>('registryUrl');

        if (!registryUrl) {
            vscode.window.showErrorMessage('RPA Skills registry URL is not configured.');
            return [];
        }

        try {
            const registry = await this.readManifest(registryUrl);
            return normalizeManifest(registry).groups;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to fetch RPA Skills registry: ${error.message}`);
        }

        return [];
    }

    private async readManifest(registryUrl: string): Promise<RegistryManifest> {
        if (/^https?:\/\//i.test(registryUrl)) {
            const response = await axios.get<RegistryManifest>(registryUrl, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            return response.data;
        }

        const workspaceRoot = getWorkspaceRootOrUndefined();
        const manifestPath = registryUrl.startsWith('file://')
            ? vscode.Uri.parse(registryUrl).fsPath
            : path.resolve(workspaceRoot || process.cwd(), registryUrl);
        const raw = await fs.promises.readFile(manifestPath, 'utf8');
        return JSON.parse(raw) as RegistryManifest;
    }

    private createSkillItem(skill: NormalizedSkill): SkillTreeItem {
        const status = this.getSkillStatus(skill);
        const contextValue = status.status === 'installed'
            ? 'skillInstalled'
            : status.status === 'updateAvailable'
                ? 'skillUpdateAvailable'
                : 'skillNotInstalled';
        const skillItem = new SkillTreeItem(
            skill.name,
            vscode.TreeItemCollapsibleState.None,
            contextValue
        );

        skillItem.skill = skill;
        skillItem.description = this.renderStatusDescription(skill, status);
        skillItem.tooltip = `${skill.name}\n${skill.description || ''}`.trim();
        skillItem.iconPath = status.status === 'installed'
            ? new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'))
            : status.status === 'updateAvailable'
                ? new vscode.ThemeIcon('warning', new vscode.ThemeColor('notificationsWarningIcon.foreground'))
                : new vscode.ThemeIcon('cloud-download');
        skillItem.command = {
            command: 'rpaSkills.openSkillDetails',
            title: 'Open Skill Details',
            arguments: [skill.id]
        };

        return skillItem;
    }

    private renderStatusDescription(skill: NormalizedSkill, status: SkillStatus): string {
        if (status.status === 'updateAvailable') {
            return `Update ${status.installedVersion || '?'} -> ${skill.version || '?'}`;
        }

        if (status.status === 'installed') {
            return status.installedVersion ? `Installed ${status.installedVersion}` : 'Installed';
        }

        return skill.version ? `Not installed ${skill.version}` : 'Not installed';
    }

    private scanInstalledSkills(): Map<string, InstalledSkillRecord> {
        const installed = new Map<string, InstalledSkillRecord>();

        let skillsRoot: string;
        try {
            skillsRoot = getSkillsRoot();
        } catch {
            return installed;
        }

        if (!fs.existsSync(skillsRoot)) {
            return installed;
        }

        for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
            if (!entry.isDirectory() || entry.name.startsWith('.')) {
                continue;
            }

            const skillPath = path.join(skillsRoot, entry.name);
            const metadata = readInstalledMetadata(skillPath);
            const skillId = metadata.id || entry.name;

            installed.set(skillId, {
                id: skillId,
                name: metadata.name,
                version: metadata.version,
                installedAt: metadata.installedAt,
                path: skillPath
            });
        }

        return installed;
    }

    private resolveSkillInput(input: SkillTreeItem | NormalizedSkill | string): NormalizedSkill | undefined {
        if (typeof input === 'string') {
            return this.findSkillById(input);
        }

        if (input instanceof SkillTreeItem) {
            return input.skill;
        }

        return input;
    }

    private renderSkillDetails(webview: vscode.Webview, skill: NormalizedSkill, status: SkillStatus): string {
        const installArgs = encodeURIComponent(JSON.stringify([skill.id]));
        const installUri = vscode.Uri.parse(`command:rpaSkills.installSkill?${installArgs}`).toString();
        const statusLabel = status.status === 'updateAvailable'
            ? `Update available (${status.installedVersion || 'installed'} -> ${skill.version || 'latest'})`
            : status.status === 'installed'
                ? `Installed${status.installedVersion ? ` ${status.installedVersion}` : ''}`
                : 'Not installed';
        const actionLabel = status.status === 'installed' ? 'Reinstall' : status.status === 'updateAvailable' ? 'Update' : 'Install';
        const bodyMarkdown = skill.markdown || skill.usage || skill.description || 'No description provided.';
        const dependencies = skill.dependencies.length
            ? `<ul>${skill.dependencies.map((dependency) => `<li><code>${escapeHtml(dependency)}</code></li>`).join('')}</ul>`
            : '<p class="muted">No dependencies declared.</p>';
        const tags = skill.tags.length
            ? skill.tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')
            : '<span class="muted">No tags</span>';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${escapeHtml(skill.name)}</title>
    <style>
        body {
            color: var(--vscode-editor-foreground);
            background: var(--vscode-editor-background);
            font-family: var(--vscode-font-family);
            line-height: 1.55;
            padding: 24px;
        }
        h1 { margin: 0 0 8px; font-size: 26px; }
        h2 { margin-top: 28px; font-size: 18px; }
        a.button {
            display: inline-block;
            margin-top: 18px;
            padding: 8px 12px;
            color: var(--vscode-button-foreground);
            background: var(--vscode-button-background);
            text-decoration: none;
            border-radius: 4px;
        }
        a.button:hover { background: var(--vscode-button-hoverBackground); }
        code {
            background: var(--vscode-textCodeBlock-background);
            padding: 1px 4px;
            border-radius: 3px;
        }
        .meta {
            display: grid;
            grid-template-columns: minmax(100px, max-content) 1fr;
            gap: 8px 16px;
            margin-top: 18px;
        }
        .label, .muted { color: var(--vscode-descriptionForeground); }
        .badge, .tag {
            display: inline-block;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 2px 6px;
            margin: 2px 4px 2px 0;
        }
        .description {
            max-width: 920px;
        }
    </style>
</head>
<body>
    <h1>${escapeHtml(skill.name)}</h1>
    <div class="badge">${escapeHtml(statusLabel)}</div>
    <a class="button" href="${installUri}">${escapeHtml(actionLabel)}</a>

    <div class="meta">
        <div class="label">ID</div><div><code>${escapeHtml(skill.id)}</code></div>
        <div class="label">Version</div><div>${escapeHtml(skill.version || 'Not specified')}</div>
        <div class="label">Author</div><div>${escapeHtml(skill.author || 'Not specified')}</div>
        <div class="label">Install path</div><div>${status.installPath ? `<code>${escapeHtml(status.installPath)}</code>` : '<span class="muted">Not installed</span>'}</div>
        <div class="label">Download</div><div>${skill.downloadUrl ? `<code>${escapeHtml(skill.downloadUrl)}</code>` : '<span class="muted">No download URL</span>'}</div>
    </div>

    <h2>Description</h2>
    <div class="description">${markdownToHtml(bodyMarkdown)}</div>

    <h2>Tags</h2>
    <div>${tags}</div>

    <h2>Dependencies</h2>
    ${dependencies}
</body>
</html>`;
    }
}

export class SkillTreeItem extends vscode.TreeItem {
    public group?: NormalizedGroup;
    public skill?: NormalizedSkill;

    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string
    ) {
        super(label, collapsibleState);
        this.tooltip = this.label;
        if (contextValue === 'group') {
            this.iconPath = new vscode.ThemeIcon('folder');
        } else {
            this.iconPath = new vscode.ThemeIcon('symbol-property');
        }
    }
}

function normalizeManifest(registry: RegistryManifest): { groups: NormalizedGroup[] } {
    if (!registry || !Array.isArray(registry.groups)) {
        throw new Error('Registry manifest must include a groups array.');
    }

    return {
        groups: registry.groups.map((group) => ({
            id: group.id || slugify(group.name),
            name: group.name || group.id,
            description: group.description,
            skills: (group.skills || []).map(normalizeSkill)
        }))
    };
}

function normalizeSkill(skill: RegistrySkill): NormalizedSkill {
    const id = skill.id || slugify(skill.name);
    const rawDependencies = Array.isArray(skill.dependencies) ? skill.dependencies : [];
    const rawTags = Array.isArray(skill.tags) ? skill.tags : [];

    return {
        id,
        name: skill.name || id,
        version: typeof skill.version === 'string' ? skill.version : undefined,
        description: typeof skill.description === 'string' ? skill.description : '',
        downloadUrl: pickString(skill.downloadUrl, skill.download_url, skill.url),
        dependencies: rawDependencies.filter((dependency): dependency is string => typeof dependency === 'string'),
        author: typeof skill.author === 'string' ? skill.author : undefined,
        tags: rawTags.filter((tag): tag is string => typeof tag === 'string'),
        usage: typeof skill.usage === 'string' ? skill.usage : undefined,
        markdown: typeof skill.markdown === 'string' ? skill.markdown : undefined,
        raw: skill
    };
}

function pickString(...values: unknown[]): string | undefined {
    for (const value of values) {
        if (typeof value === 'string' && value.trim()) {
            return value;
        }
    }

    return undefined;
}

function slugify(value: string | undefined): string {
    return safeSkillDirectoryName(value || 'skill');
}

function readInstalledMetadata(skillPath: string): Partial<InstalledSkillRecord> {
    for (const filename of ['.gravitykit-skill.json', 'skill.json']) {
        const metadataPath = path.join(skillPath, filename);
        if (fs.existsSync(metadataPath)) {
            try {
                return JSON.parse(fs.readFileSync(metadataPath, 'utf8')) as Partial<InstalledSkillRecord>;
            } catch {
                return {};
            }
        }
    }

    const skillMarkdownPath = path.join(skillPath, 'SKILL.md');
    if (!fs.existsSync(skillMarkdownPath)) {
        return {};
    }

    try {
        const content = fs.readFileSync(skillMarkdownPath, 'utf8');
        const frontmatter = content.match(/^---\s*([\s\S]*?)\s*---/);
        if (!frontmatter) {
            return {};
        }

        const version = frontmatter[1].match(/^version:\s*["']?([^"'\r\n]+)["']?/m)?.[1]?.trim();
        const name = frontmatter[1].match(/^name:\s*["']?([^"'\r\n]+)["']?/m)?.[1]?.trim();
        return { version, name };
    } catch {
        return {};
    }
}

function compareVersions(remoteVersion: string, installedVersion: string): number {
    const remote = remoteVersion.split(/[.+-]/).map(toVersionPart);
    const installed = installedVersion.split(/[.+-]/).map(toVersionPart);
    const length = Math.max(remote.length, installed.length);

    for (let index = 0; index < length; index++) {
        const left = remote[index] ?? 0;
        const right = installed[index] ?? 0;
        if (left > right) {
            return 1;
        }
        if (left < right) {
            return -1;
        }
    }

    return 0;
}

function toVersionPart(value: string): number {
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : 0;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function markdownToHtml(markdown: string): string {
    const lines = escapeHtml(markdown).split(/\r?\n/);
    const html: string[] = [];

    for (const line of lines) {
        if (line.startsWith('### ')) {
            html.push(`<h3>${inlineMarkdown(line.slice(4))}</h3>`);
        } else if (line.startsWith('## ')) {
            html.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`);
        } else if (line.startsWith('# ')) {
            html.push(`<h2>${inlineMarkdown(line.slice(2))}</h2>`);
        } else if (line.startsWith('- ')) {
            html.push(`<p>&bull; ${inlineMarkdown(line.slice(2))}</p>`);
        } else if (line.trim() === '') {
            html.push('');
        } else {
            html.push(`<p>${inlineMarkdown(line)}</p>`);
        }
    }

    return html.join('\n');
}

function inlineMarkdown(value: string): string {
    return value
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
}
