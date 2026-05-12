import * as vscode from 'vscode';
import { SkillTreeItem, SkillsProvider } from './skillsProvider';
import { installGroup, installSkill } from './installer';

export function activate(context: vscode.ExtensionContext) {
    console.log('RPA Skills extension is now active!');

    const skillsProvider = new SkillsProvider(context);
    const skillsView = vscode.window.createTreeView('rpaSkills.skillsView', {
        treeDataProvider: skillsProvider,
        showCollapseAll: true
    });

    let refreshDisposable = vscode.commands.registerCommand('rpaSkills.refreshSkills', () => {
        skillsProvider.refresh();
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

    const configDisposable = vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('rpaSkills') || event.affectsConfiguration('gravitykit')) {
            skillsProvider.refresh();
        }
    });

    context.subscriptions.push(
        skillsView,
        refreshDisposable,
        openDetailsDisposable,
        installDisposable,
        installGroupDisposable,
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
