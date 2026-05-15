import * as vscode from 'vscode';
import { SkillTreeItem, SkillsProvider } from './skillsProvider';
import { installGroup, installSkill, installSkillsToTarget, installSkillToTarget } from './installer';
import { AssistantDashboard, QuickSetupRequest } from './dashboard';
import {
    getIdeTarget,
    getMcpCapableTargets,
    IdeTargetDefinition,
    installMcpForTarget,
    resolveTargetInstallRoot
} from './ideTargets';
import { createMainInstructionFile, openPromptFile, toggleInstructionInPromptFiles } from './promptManager';
import { WatchController } from './watchController';
import { previewDocumentAsMarkdown } from './documentMarkdownPreview';

export function activate(context: vscode.ExtensionContext) {
    console.log('RPA Skills extension is now active!');

    const skillsProvider = new SkillsProvider(context);
    let dashboard: AssistantDashboard | undefined;
    const watchController = new WatchController(() => {
        skillsProvider.refreshLocalState();
        dashboard?.refresh();
    });
    dashboard = new AssistantDashboard(
        watchController,
        () => skillsProvider.listGroups(),
        (request) => runQuickSetup(request, skillsProvider, dashboard)
    );
    const skillsView = vscode.window.createTreeView('rpaSkills.skillsView', {
        treeDataProvider: skillsProvider,
        showCollapseAll: true
    });
    updateSkillSearchState(skillsProvider, skillsView);

    let refreshDisposable = vscode.commands.registerCommand('rpaSkills.refreshSkills', async () => {
        skillsProvider.refresh();
        await dashboard?.refresh();
    });

    let searchSkillsDisposable = vscode.commands.registerCommand('rpaSkills.searchSkills', async () => {
        const value = await vscode.window.showInputBox({
            title: 'Search RPA Skills',
            placeHolder: 'Search by skill, group, tag, dependency, author, or description',
            prompt: 'Filter the Skills tree by keyword.',
            value: skillsProvider.getSearchQuery()
        });

        if (value === undefined) {
            return;
        }

        skillsProvider.setSearchQuery(value);
        await updateSkillSearchState(skillsProvider, skillsView);
    });

    let clearSkillSearchDisposable = vscode.commands.registerCommand('rpaSkills.clearSkillSearch', async () => {
        skillsProvider.clearSearchQuery();
        await updateSkillSearchState(skillsProvider, skillsView);
    });

    let openDetailsDisposable = vscode.commands.registerCommand('rpaSkills.openSkillDetails', async (input) => {
        await skillsProvider.openSkillDetails(input);
    });

    let installDisposable = vscode.commands.registerCommand('rpaSkills.installSkill', async (input) => {
        const skill = resolveSkillInput(input, skillsProvider);

        if (skill) {
            await installSkill(skill, skillsProvider);
        } else {
            vscode.window.showErrorMessage('Skill not found in the loaded registry.');
        }
    });

    let installGroupDisposable = vscode.commands.registerCommand('rpaSkills.installGroup', async (input) => {
        const group = input instanceof SkillTreeItem
            ? input.group
            : typeof input === 'string'
                ? skillsProvider.findGroupById(input)
                : undefined;

        if (!group) {
            vscode.window.showErrorMessage('Group not found in the loaded registry.');
            return;
        }

        await installGroup(group.name, group.skills, skillsProvider);
    });

    let installToIdeDisposable = vscode.commands.registerCommand('rpaSkills.installSkillToIde', async (input, explicitTargetId?: string) => {
        const skill = await resolveSkillForIdeInstall(input, skillsProvider);
        const targetId = resolveTargetId(input, explicitTargetId);
        const target = await pickIdeTarget(targetId);

        if (!skill || !target) {
            return;
        }

        await installSkillToTarget(skill, {
            id: target.id,
            label: target.name,
            rootPath: resolveTargetInstallRoot(target),
            mode: target.installMode,
            ruleFileExtension: target.ruleFileExtension
        }, skillsProvider);
        await dashboard?.refresh();
    });

    let openDashboardDisposable = vscode.commands.registerCommand('rpaSkills.openAssistantDashboard', async () => {
        await dashboard?.show();
    });

    let previewDocumentDisposable = vscode.commands.registerCommand('rpaSkills.previewDocumentAsMarkdown', async (input?: vscode.Uri) => {
        await previewDocumentAsMarkdown(input);
    });

    let activateMcpDisposable = vscode.commands.registerCommand('rpaSkills.activateMcpForIde', async (targetId?: string) => {
        await configureMcpForIde(targetId, false, dashboard);
    });

    let deactivateMcpDisposable = vscode.commands.registerCommand('rpaSkills.deactivateMcpForIde', async (targetId?: string) => {
        await configureMcpForIde(targetId, true, dashboard);
    });

    let openPromptDisposable = vscode.commands.registerCommand('rpaSkills.openPromptFile', async (relativePath?: string) => {
        await openPromptFile(relativePath);
    });

    let createMainInstructionDisposable = vscode.commands.registerCommand('rpaSkills.createMainInstruction', async () => {
        await createMainInstructionFile();
        await dashboard?.refresh();
    });

    let startWatchDisposable = vscode.commands.registerCommand('rpaSkills.startWatch', async () => {
        watchController.start();
        await dashboard?.refresh();
    });

    let stopWatchDisposable = vscode.commands.registerCommand('rpaSkills.stopWatch', async () => {
        watchController.stop();
        await dashboard?.refresh();
    });

    let toggleWatchDisposable = vscode.commands.registerCommand('rpaSkills.toggleWatch', async () => {
        watchController.toggle();
        await dashboard?.refresh();
    });

    let toggleMcpSkillRouterDisposable = vscode.commands.registerCommand('rpaSkills.toggleMcpSkillRouter', async () => {
        const config = vscode.workspace.getConfiguration('rpaSkills');
        const currentValue = config.get<boolean>('mcp.enableSkillRouter') ?? true;
        const newValue = !currentValue;
        await config.update('mcp.enableSkillRouter', newValue, vscode.ConfigurationTarget.Workspace);
        
        await toggleInstructionInPromptFiles(newValue);
        
        vscode.window.showInformationMessage(`MCP Skill Router has been ${newValue ? 'enabled' : 'disabled'}.`);
        await dashboard?.refresh();
    });

    let openSettingsDisposable = vscode.commands.registerCommand('rpaSkills.openSettings', () => {
        vscode.commands.executeCommand('workbench.action.openSettings', 'rpaSkills.registryUrl');
    });

    const configDisposable = vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('rpaSkills') || event.affectsConfiguration('gravitykit')) {
            if (event.affectsConfiguration('rpaSkills.watch.enabled') || event.affectsConfiguration('gravitykit.watch.enabled')) {
                watchController.syncFromConfiguration();
            }
            skillsProvider.refresh();
            dashboard?.refresh();
        }
    });

    watchController.startFromConfiguration();

    context.subscriptions.push(
        skillsView,
        dashboard,
        watchController,
        refreshDisposable,
        searchSkillsDisposable,
        clearSkillSearchDisposable,
        openDetailsDisposable,
        installDisposable,
        installGroupDisposable,
        installToIdeDisposable,
        openDashboardDisposable,
        previewDocumentDisposable,
        activateMcpDisposable,
        deactivateMcpDisposable,
        openPromptDisposable,
        createMainInstructionDisposable,
        startWatchDisposable,
        stopWatchDisposable,
        toggleWatchDisposable,
        toggleMcpSkillRouterDisposable,
        openSettingsDisposable,
        configDisposable
    );
}

export function deactivate() {}

async function updateSkillSearchState(
    skillsProvider: SkillsProvider,
    skillsView: vscode.TreeView<SkillTreeItem>
): Promise<void> {
    const query = skillsProvider.getSearchQuery();
    skillsView.message = query ? `Search: ${query}` : undefined;
    await vscode.commands.executeCommand('setContext', 'rpaSkills.hasSkillSearch', Boolean(query));
}

function resolveSkillInput(input: unknown, skillsProvider: SkillsProvider) {
    if (input instanceof SkillTreeItem) {
        return input.skill;
    }

    if (typeof input === 'string') {
        return skillsProvider.findSkillById(input);
    }

    return undefined;
}

async function resolveSkillForIdeInstall(input: unknown, skillsProvider: SkillsProvider) {
    const directSkill = resolveSkillInput(input, skillsProvider);
    if (directSkill) {
        return directSkill;
    }

    const skills = await skillsProvider.listSkills();
    const picked = await vscode.window.showQuickPick(
        skills.map((skill) => ({
            label: skill.name,
            description: skill.id,
            detail: `${skill.description || 'No description provided.'} This selection only chooses the skill; the next step chooses the IDE target.`,
            skill
        })),
        {
            title: 'Install skill to IDE',
            placeHolder: 'Select the skill to mirror into an IDE-specific folder or rule file'
        }
    );

    return picked?.skill;
}

async function pickIdeTarget(targetId?: string): Promise<IdeTargetDefinition | undefined> {
    if (targetId) {
        const directTarget = getIdeTarget(targetId);
        if (directTarget) {
            return directTarget;
        }
    }

    const picked = await vscode.window.showQuickPick(
        getInstallTargets().map((target) => ({
            label: target.name,
            description: target.skillPath,
            detail: `${target.description} ${
                target.installMode === 'markdownRule'
                    ? 'This target receives a generated markdown rule file.'
                    : 'This target receives a full skill folder.'
            }`,
            target
        })),
        {
            title: 'IDE target',
            placeHolder: 'Select where this skill should be installed for the IDE to load'
        }
    );

    return picked?.target;
}

async function pickMcpTarget(targetId?: string): Promise<IdeTargetDefinition | undefined> {
    if (targetId) {
        const directTarget = getIdeTarget(targetId);
        if (directTarget?.mcpConfigPath) {
            return directTarget;
        }
    }

    const picked = await vscode.window.showQuickPick(
        getMcpCapableTargets().map((target) => ({
            label: target.name,
            description: target.mcpConfigPath,
            detail: `${target.description} MCP setup writes managed server entries; restart the IDE if it does not reload MCP automatically.`,
            target
        })),
        {
            title: 'MCP target',
            placeHolder: 'Select the IDE config file that should receive the MCP servers'
        }
    );

    return picked?.target;
}

async function configureMcpForIde(
    targetId: string | undefined,
    disabled: boolean,
    dashboard: AssistantDashboard | undefined
): Promise<void> {
    const target = await pickMcpTarget(targetId);
    if (!target) {
        return;
    }

    try {
        const configPath = await installMcpForTarget(target, disabled);
        vscode.window.showInformationMessage(`${disabled ? 'Disabled' : 'Activated'} MCP for ${target.name}: ${configPath}`);
        await dashboard?.refresh();
    } catch (error: any) {
        vscode.window.showErrorMessage(`MCP setup failed: ${error.message}`);
    }
}

function resolveTargetId(input: unknown, explicitTargetId?: string): string | undefined {
    if (explicitTargetId) {
        return explicitTargetId;
    }

    if (isTargetHint(input)) {
        return input.targetId;
    }

    return undefined;
}

function isTargetHint(input: unknown): input is { targetId: string } {
    return typeof input === 'object'
        && input !== null
        && 'targetId' in input
        && typeof (input as { targetId?: unknown }).targetId === 'string';
}

function getInstallTargets(): IdeTargetDefinition[] {
    return [
        'agent',
        'codex',
        'cursor',
        'windsurf',
        'kilocode',
        'cline',
        'kiro',
        'claude',
        'copilot'
    ]
        .map((targetId) => getIdeTarget(targetId))
        .filter((target): target is IdeTargetDefinition => Boolean(target));
}

async function runQuickSetup(
    request: QuickSetupRequest,
    skillsProvider: SkillsProvider,
    dashboard: AssistantDashboard | undefined
): Promise<void> {
    const target = getIdeTarget(request.targetId);
    if (!target) {
        vscode.window.showErrorMessage('Quick setup target was not found.');
        return;
    }

    const groups = await skillsProvider.listGroups();
    const selectedGroupIds = new Set(request.groupIds);
    const selectedSkills = uniqueSkills(
        groups
            .filter((group) => selectedGroupIds.has(group.id))
            .flatMap((group) => group.skills)
    );
    const notes: string[] = [];

    if (target.mcpConfigPath) {
        try {
            const configPath = await installMcpForTarget(target, false);
            notes.push(`MCP activated: ${configPath}`);
            await enableSkillRouterInstruction();
        } catch (error: any) {
            vscode.window.showWarningMessage(`Quick setup could not activate MCP for ${target.name}: ${error.message || String(error)}`);
        }
    }

    if (selectedSkills.length > 0) {
        await installSkillsToTarget(selectedSkills, {
            id: target.id,
            label: target.name,
            rootPath: resolveTargetInstallRoot(target),
            mode: target.installMode,
            ruleFileExtension: target.ruleFileExtension
        }, skillsProvider);
        notes.push(`${selectedSkills.length} skills installed for ${target.name}`);
    } else {
        notes.push(`No skill groups selected for ${target.name}`);
    }

    skillsProvider.refreshLocalState();
    await dashboard?.refresh();
    vscode.window.showInformationMessage(`Quick setup finished for ${target.name}. ${notes.join(' ')}`);
}

async function enableSkillRouterInstruction(): Promise<void> {
    const config = vscode.workspace.getConfiguration('rpaSkills');
    const currentValue = config.get<boolean>('mcp.enableSkillRouter') ?? true;

    if (!currentValue) {
        await config.update('mcp.enableSkillRouter', true, vscode.ConfigurationTarget.Workspace);
    }

    await toggleInstructionInPromptFiles(true);
}

function uniqueSkills<T extends { id: string }>(skills: T[]): T[] {
    const seen = new Set<string>();
    const result: T[] = [];

    for (const skill of skills) {
        if (seen.has(skill.id)) {
            continue;
        }

        seen.add(skill.id);
        result.push(skill);
    }

    return result;
}
