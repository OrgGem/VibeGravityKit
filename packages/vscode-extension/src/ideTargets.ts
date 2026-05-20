import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { ensureInside, getRpaSkillsConfigValue, getWorkspaceRoot } from './config';

export type IdeTargetId =
    | 'agent'
    | 'codex'
    | 'cursor'
    | 'windsurf'
    | 'kilocode'
    | 'cline'
    | 'kiro'
    | 'claude'
    | 'copilot';

export type McpConfigFormat = 'json' | 'codexToml';
export type SkillInstallMode = 'skillDirectory' | 'markdownRule';

export interface IdeTargetDefinition {
    id: IdeTargetId;
    name: string;
    description: string;
    skillPath: string;
    installMode: SkillInstallMode;
    ruleFileExtension?: string;
    mcpConfigPath?: string;
    mcpFormat?: McpConfigFormat;
    promptPaths: string[];
    promptDirs: string[];
}

export interface IdeTargetStatus extends IdeTargetDefinition {
    detected: boolean;
    currentIde: boolean;
    absoluteSkillPath: string;
    absoluteMcpConfigPath?: string;
    skillEntryCount: number;
    mcpConfigured: boolean;
    activeMcpServers: number;
    disabledMcpServers: number;
}

export interface McpServerConfig {
    command?: string;
    args?: string[];
    env?: Record<string, string>;
    cwd?: string;
    disabled?: boolean;
    [key: string]: unknown;
}

export interface McpServerMap {
    [serverName: string]: McpServerConfig;
}

export const IDE_TARGETS: IdeTargetDefinition[] = [
    {
        id: 'agent',
        name: 'GravityKit Agent',
        description: 'Canonical workspace skills and agent prompts.',
        skillPath: '.agent/skills',
        installMode: 'skillDirectory',
        mcpConfigPath: '.mcp.json',
        mcpFormat: 'json',
        promptPaths: ['AGENTS.md', '.agent/brain/default_skills.md', '.agent/brain/platform_notes.md'],
        promptDirs: ['.agent/agents', '.agent/workflows']
    },
    {
        id: 'codex',
        name: 'Codex',
        description: 'Codex workspace config and optional skill mirror.',
        skillPath: '.codex/skills',
        installMode: 'skillDirectory',
        mcpConfigPath: '.codex/config.toml',
        mcpFormat: 'codexToml',
        promptPaths: ['AGENTS.md', '.codex/config.toml'],
        promptDirs: ['.codex/skills']
    },
    {
        id: 'cursor',
        name: 'Cursor',
        description: 'Cursor rules and workspace MCP config.',
        skillPath: '.cursor/rules',
        installMode: 'markdownRule',
        ruleFileExtension: 'mdc',
        mcpConfigPath: '.cursor/mcp.json',
        mcpFormat: 'json',
        promptPaths: ['.cursor/mcp.json'],
        promptDirs: ['.cursor/rules']
    },
    {
        id: 'windsurf',
        name: 'Windsurf',
        description: 'Windsurf rule markdown files.',
        skillPath: '.windsurf/rules',
        installMode: 'markdownRule',
        ruleFileExtension: 'md',
        promptPaths: [],
        promptDirs: ['.windsurf/rules']
    },
    {
        id: 'kilocode',
        name: 'Kilo Code',
        description: 'Kilo Code rule markdown files.',
        skillPath: '.kilocode/rules',
        installMode: 'markdownRule',
        ruleFileExtension: 'md',
        promptPaths: [],
        promptDirs: ['.kilocode/rules']
    },
    {
        id: 'cline',
        name: 'Cline',
        description: 'Cline rules in .cline/rules.',
        skillPath: '.cline/rules',
        installMode: 'markdownRule',
        ruleFileExtension: 'md',
        promptPaths: [],
        promptDirs: ['.cline/rules']
    },
    {
        id: 'kiro',
        name: 'Kiro',
        description: 'Kiro skill folders, agents, specs, steering files and MCP config.',
        skillPath: '.kiro/skills',
        installMode: 'skillDirectory',
        mcpConfigPath: '.kiro/mcp.json',
        mcpFormat: 'json',
        promptPaths: ['.kiro/mcp.json', '.kiro/steering/product.md', '.kiro/steering/tech.md', '.kiro/steering/structure.md'],
        promptDirs: ['.kiro/skills', '.kiro/agents', '.kiro/specs', '.kiro/steering']
    },
    {
        id: 'claude',
        name: 'Claude',
        description: 'Claude skill folder when present in the workspace.',
        skillPath: '.claude/skills',
        installMode: 'skillDirectory',
        promptPaths: ['CLAUDE.md'],
        promptDirs: ['.claude/skills']
    },
    {
        id: 'copilot',
        name: 'GitHub Copilot',
        description: 'Copilot instructions and workspace skills.',
        skillPath: '.github/skills',
        installMode: 'skillDirectory',
        promptPaths: ['.github/copilot-instructions.md'],
        promptDirs: ['.github/skills']
    }
];

export function getIdeTarget(targetId: string): IdeTargetDefinition | undefined {
    return IDE_TARGETS.find((target) => target.id === targetId);
}

export function getMcpCapableTargets(): IdeTargetDefinition[] {
    return IDE_TARGETS.filter((target) => Boolean(target.mcpConfigPath && target.mcpFormat));
}

export function getTargetStatuses(): IdeTargetStatus[] {
    const root = getWorkspaceRoot();
    const currentIdeTargetId = detectCurrentIdeTargetId();

    return IDE_TARGETS.map((target) => {
        const absoluteSkillPath = resolveWorkspacePath(root, target.skillPath);
        const absoluteMcpConfigPath = target.mcpConfigPath
            ? resolveWorkspacePath(root, target.mcpConfigPath)
            : undefined;
        const mcpStatus = absoluteMcpConfigPath && target.mcpFormat
            ? readMcpStatus(absoluteMcpConfigPath, target.mcpFormat)
            : { configured: false, active: 0, disabled: 0 };

        return {
            ...target,
            detected: targetExists(root, target),
            currentIde: target.id === currentIdeTargetId,
            absoluteSkillPath,
            absoluteMcpConfigPath,
            skillEntryCount: countDirectoryEntries(absoluteSkillPath),
            mcpConfigured: mcpStatus.configured,
            activeMcpServers: mcpStatus.active,
            disabledMcpServers: mcpStatus.disabled
        };
    });
}

export function detectCurrentIdeTargetId(appName = vscode.env.appName): IdeTargetId | undefined {
    const normalized = appName.toLowerCase();

    if (normalized.includes('cursor')) {
        return 'cursor';
    }
    if (normalized.includes('windsurf')) {
        return 'windsurf';
    }
    if (normalized.includes('kiro')) {
        return 'kiro';
    }
    if (normalized.includes('codex')) {
        return 'codex';
    }
    if (normalized.includes('claude')) {
        return 'claude';
    }
    if (normalized.includes('kilo')) {
        return 'kilocode';
    }
    if (normalized.includes('cline')) {
        return 'cline';
    }
    if (
        normalized.includes('visual studio code')
        || normalized.includes('vscode')
        || normalized.includes('vscodium')
        || normalized.includes('code - oss')
    ) {
        return 'copilot';
    }

    return undefined;
}

export function getQuickSetupDefaultTargetId(targets: IdeTargetStatus[]): IdeTargetId {
    const currentTarget = targets.find((target) => target.currentIde);
    if (currentTarget) {
        return currentTarget.id;
    }

    const detectedTarget = targets.find((target) => target.detected && target.id !== 'agent')
        || targets.find((target) => target.detected);

    return detectedTarget?.id || 'agent';
}

export function resolveTargetInstallRoot(target: IdeTargetDefinition): string {
    const workspaceRoot = getWorkspaceRoot();
    const installRoot = resolveWorkspacePath(workspaceRoot, target.skillPath);
    ensureInside(workspaceRoot, installRoot, `${target.name} install path must stay inside the workspace.`);
    return installRoot;
}

export function resolveWorkspacePath(workspaceRoot: string, relativePath: string): string {
    const normalized = relativePath.replace(/[\\/]+/g, path.sep);
    const resolved = path.resolve(workspaceRoot, normalized);
    ensureInside(workspaceRoot, resolved, `Path escapes workspace: ${relativePath}`);
    return resolved;
}

export async function installMcpForTarget(target: IdeTargetDefinition, disabled: boolean): Promise<string> {
    if (!target.mcpConfigPath || !target.mcpFormat) {
        throw new Error(`${target.name} does not have a supported MCP config path.`);
    }

    const workspaceRoot = getWorkspaceRoot();
    const configPath = resolveWorkspacePath(workspaceRoot, target.mcpConfigPath);
    const servers = await loadConfiguredMcpServers();
    const serverNames = Object.keys(servers);

    if (serverNames.length === 0) {
        throw new Error('No MCP servers found. Configure rpaSkills.mcp.servers or an existing MCP config file first.');
    }

    fs.mkdirSync(path.dirname(configPath), { recursive: true });

    if (target.mcpFormat === 'json') {
        writeJsonMcpConfig(configPath, servers, disabled);
    } else {
        writeCodexTomlMcpConfig(configPath, servers, disabled);
    }

    return configPath;
}

export async function loadConfiguredMcpServers(): Promise<McpServerMap> {
    const configuredServers = getRpaSkillsConfigValue<McpServerMap>('mcp.servers') || {};
    if (Object.keys(configuredServers).length > 0) {
        return configuredServers;
    }

    const configPaths = getRpaSkillsConfigValue<string[]>('mcp.configPaths') || ['.mcp.json'];
    const workspaceRoot = getWorkspaceRoot();

    for (const configPath of configPaths) {
        const absolutePath = resolveWorkspacePath(workspaceRoot, configPath);
        if (!fs.existsSync(absolutePath)) {
            continue;
        }

        const servers = readJsonMcpServers(absolutePath);
        if (Object.keys(servers).length > 0) {
            return servers;
        }
    }

    return {};
}

function targetExists(workspaceRoot: string, target: IdeTargetDefinition): boolean {
    if (fs.existsSync(resolveWorkspacePath(workspaceRoot, target.skillPath))) {
        return true;
    }

    if (target.mcpConfigPath && fs.existsSync(resolveWorkspacePath(workspaceRoot, target.mcpConfigPath))) {
        return true;
    }

    return target.promptPaths.some((promptPath) => fs.existsSync(resolveWorkspacePath(workspaceRoot, promptPath)))
        || target.promptDirs.some((promptDir) => fs.existsSync(resolveWorkspacePath(workspaceRoot, promptDir)));
}

function countDirectoryEntries(directoryPath: string): number {
    if (!fs.existsSync(directoryPath)) {
        return 0;
    }

    try {
        return fs.readdirSync(directoryPath, { withFileTypes: true })
            .filter((entry) => !entry.name.startsWith('.'))
            .length;
    } catch {
        return 0;
    }
}

function readMcpStatus(configPath: string, format: McpConfigFormat): { configured: boolean; active: number; disabled: number } {
    if (!fs.existsSync(configPath)) {
        return { configured: false, active: 0, disabled: 0 };
    }

    if (format === 'json') {
        const servers = readJsonMcpServers(configPath);
        const values = Object.values(servers);
        return {
            configured: values.length > 0,
            active: values.filter((server) => server.disabled !== true).length,
            disabled: values.filter((server) => server.disabled === true).length
        };
    }

    const raw = fs.readFileSync(configPath, 'utf8');
    const sections = raw.match(/^\[mcp_servers[.\]]/gm) || [];
    const disabled = raw.match(/^\s*disabled\s*=\s*true\s*$/gm) || [];
    return {
        configured: sections.length > 0,
        active: Math.max(sections.length - disabled.length, 0),
        disabled: disabled.length
    };
}

function readJsonMcpServers(configPath: string): McpServerMap {
    try {
        const parsed = JSON.parse(fs.readFileSync(configPath, 'utf8')) as { mcpServers?: McpServerMap };
        return isObject(parsed.mcpServers) ? parsed.mcpServers : {};
    } catch {
        return {};
    }
}

function writeJsonMcpConfig(configPath: string, servers: McpServerMap, disabled: boolean): void {
    const parsed = readJsonObject(configPath);
    const nextServers: McpServerMap = isObject(parsed.mcpServers) ? parsed.mcpServers as McpServerMap : {};

    for (const [serverName, server] of Object.entries(servers)) {
        nextServers[serverName] = {
            ...server,
            disabled
        };
    }

    parsed.mcpServers = nextServers;
    fs.writeFileSync(configPath, `${JSON.stringify(parsed, null, 2)}\n`, 'utf8');
}

function writeCodexTomlMcpConfig(configPath: string, servers: McpServerMap, disabled: boolean): void {
    const raw = fs.existsSync(configPath) ? fs.readFileSync(configPath, 'utf8') : '';
    const withoutManagedBlock = raw.replace(
        /\n?# <rpaSkills\.mcp>[\s\S]*?# <\/rpaSkills\.mcp>\n?/g,
        '\n'
    );
    const withoutDuplicateSections = removeTomlServerSections(withoutManagedBlock, Object.keys(servers));
    const block = [
        '# <rpaSkills.mcp>',
        ...Object.entries(servers).flatMap(([serverName, server]) => renderCodexMcpServer(serverName, server, disabled)),
        '# </rpaSkills.mcp>'
    ].join('\n');
    const prefix = withoutDuplicateSections.trimEnd();
    const next = `${prefix}${prefix ? '\n\n' : ''}${block}\n`;
    fs.writeFileSync(configPath, next, 'utf8');
}

function removeTomlServerSections(raw: string, serverNames: string[]): string {
    if (serverNames.length === 0) {
        return raw;
    }

    const names = new Set(serverNames);
    const lines = raw.split(/\r?\n/);
    const kept: string[] = [];
    let skipping = false;

    for (const line of lines) {
        const sectionName = parseCodexMcpSectionName(line);
        if (sectionName) {
            skipping = names.has(sectionName);
            if (skipping) {
                continue;
            }
        } else if (skipping && /^\s*\[/.test(line)) {
            skipping = false;
        }

        if (!skipping) {
            kept.push(line);
        }
    }

    return kept.join('\n');
}

function parseCodexMcpSectionName(line: string): string | undefined {
    const dotted = line.match(/^\s*\[mcp_servers\.([A-Za-z0-9_-]+)\]\s*$/);
    if (dotted) {
        return dotted[1];
    }

    const quoted = line.match(/^\s*\[mcp_servers\."([^"]+)"\]\s*$/);
    return quoted?.[1];
}

function renderCodexMcpServer(serverName: string, server: McpServerConfig, disabled: boolean): string[] {
    const lines = [
        '',
        `[mcp_servers.${tomlKey(serverName)}]`
    ];

    if (typeof server.command === 'string') {
        lines.push(`command = ${tomlString(server.command)}`);
    }

    if (Array.isArray(server.args)) {
        lines.push(`args = [${server.args.map(tomlString).join(', ')}]`);
    }

    if (isStringRecord(server.env)) {
        lines.push(`env = { ${Object.entries(server.env).map(([key, value]) => `${tomlKey(key)} = ${tomlString(value)}`).join(', ')} }`);
    }

    if (typeof server.cwd === 'string') {
        lines.push(`cwd = ${tomlString(server.cwd)}`);
    }

    lines.push(`disabled = ${disabled ? 'true' : 'false'}`);
    return lines;
}

function readJsonObject(filePath: string): Record<string, unknown> {
    if (!fs.existsSync(filePath)) {
        return {};
    }

    try {
        const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        return isObject(parsed) ? parsed : {};
    } catch (error: any) {
        vscode.window.showWarningMessage(`Could not parse ${path.basename(filePath)}. Replacing it with a managed MCP config. (${error.message})`);
        return {};
    }
}

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isStringRecord(value: unknown): value is Record<string, string> {
    return isObject(value) && Object.values(value).every((entry) => typeof entry === 'string');
}

function tomlString(value: string): string {
    return JSON.stringify(value);
}

function tomlKey(value: string): string {
    return /^[A-Za-z0-9_-]+$/.test(value) ? value : tomlString(value);
}
