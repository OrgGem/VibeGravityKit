import * as path from 'path';
import * as vscode from 'vscode';

export function getWorkspaceRoot(): string {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        throw new Error('No workspace folder found. Please open a project first.');
    }

    return workspaceFolders[0].uri.fsPath;
}

export function getWorkspaceRootOrUndefined(): string | undefined {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    return workspaceFolders && workspaceFolders.length > 0 ? workspaceFolders[0].uri.fsPath : undefined;
}

export function getSkillsRoot(): string {
    const rootPath = getWorkspaceRoot();
    const configuredPath = getRpaSkillsConfigValue<string>('skills.path') || '.agent/skills';
    const skillsRoot = path.resolve(rootPath, configuredPath);

    ensureInside(rootPath, skillsRoot, 'Configured skills path must stay inside the workspace.');
    return skillsRoot;
}

export function getRpaSkillsConfigValue<T>(key: string): T | undefined {
    const config = vscode.workspace.getConfiguration('rpaSkills');
    const configValue = config.get<T>(key);

    if (hasExplicitValue(config.inspect<T>(key))) {
        return configValue;
    }

    const legacyConfig = vscode.workspace.getConfiguration('gravitykit');
    if (hasExplicitValue(legacyConfig.inspect<T>(key))) {
        return legacyConfig.get<T>(key);
    }

    return configValue;
}

function hasExplicitValue(inspected: any): boolean {
    if (!inspected) {
        return false;
    }

    return inspected.globalValue !== undefined
        || inspected.workspaceValue !== undefined
        || inspected.workspaceFolderValue !== undefined
        || inspected.globalLanguageValue !== undefined
        || inspected.workspaceLanguageValue !== undefined
        || inspected.workspaceFolderLanguageValue !== undefined;
}

export function ensureInside(parentPath: string, childPath: string, message?: string): void {
    const parent = path.resolve(parentPath);
    const child = path.resolve(childPath);
    const relative = path.relative(parent, child);

    if (relative.startsWith('..') || path.isAbsolute(relative)) {
        throw new Error(message || `Path escapes expected directory: ${child}`);
    }
}

export function safeSkillDirectoryName(skillId: string): string {
    const safe = skillId
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9._-]+/g, '-')
        .replace(/^-+|-+$/g, '');

    if (!safe || safe === '.' || safe === '..') {
        throw new Error(`Invalid skill id: ${skillId}`);
    }

    return safe;
}
