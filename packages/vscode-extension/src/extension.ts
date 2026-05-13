import * as vscode from 'vscode';
import { SkillTreeItem, SkillsProvider } from './skillsProvider';
import { installGroup, installSkill, installSkillToTarget } from './installer';
import { AssistantDashboard } from './dashboard';
import {
    getIdeTarget,
    getMcpCapableTargets,
    IdeTargetDefinition,
    installMcpForTarget,
    resolveTargetInstallRoot
} from './ideTargets';
import { createMainInstructionFile, openPromptFile } from './promptManager';
import { WatchController } from './watchController';

export function activate(context: vscode.ExtensionContext) {
    console.log('RPA Skills extension is now active!');

    const skillsProvider = new SkillsProvider(context);
    let dashboard: AssistantDashboard | undefined;
    const watchController = new WatchController(() => {
        skillsProvider.refreshLocalState();
        dashboard?.refresh();
    });
    dashboard = new AssistantDashboard(watchController);
    const skillsView = vscode.window.createTreeView('rpaSkills.skillsView', {
        treeDataProvider: skillsProvider,
        showCollapseAll: true
    });

    let refreshDisposable = vscode.commands.registerCommand('rpaSkills.refreshSkills', async () => {
        skillsProvider.refresh();
        await dashboard?.refresh();
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
        openDetailsDisposable,
        installDisposable,
        installGroupDisposable,
        installToIdeDisposable,
        openDashboardDisposable,
        activateMcpDisposable,
        deactivateMcpDisposable,
        openPromptDisposable,
        createMainInstructionDisposable,
        startWatchDisposable,
        stopWatchDisposable,
        toggleWatchDisposable,
        openSettingsDisposable,
        configDisposable
    );
}

export function deactivate() {}

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
