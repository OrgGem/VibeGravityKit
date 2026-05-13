import * as vscode from 'vscode';
import { getRpaSkillsConfigValue, getWorkspaceRootOrUndefined } from './config';

export class WatchController implements vscode.Disposable {
    private disposables: vscode.Disposable[] = [];
    private refreshTimer?: NodeJS.Timeout;
    private readonly _onDidChangeWatchedFiles = new vscode.EventEmitter<void>();
    readonly onDidChangeWatchedFiles = this._onDidChangeWatchedFiles.event;

    constructor(private readonly onRefreshRequested: () => void) {}

    start(showMessage = true): void {
        if (this.isRunning) {
            if (showMessage) {
                vscode.window.showInformationMessage('RPA Skills watch is already running.');
            }
            return;
        }

        if (!getWorkspaceRootOrUndefined()) {
            vscode.window.showErrorMessage('Open a workspace before starting RPA Skills watch.');
            return;
        }

        for (const pattern of WATCH_PATTERNS) {
            const watcher = vscode.workspace.createFileSystemWatcher(pattern);
            const listener = () => this.scheduleRefresh();
            watcher.onDidCreate(listener, undefined, this.disposables);
            watcher.onDidChange(listener, undefined, this.disposables);
            watcher.onDidDelete(listener, undefined, this.disposables);
            this.disposables.push(watcher);
        }

        if (showMessage) {
            vscode.window.showInformationMessage('RPA Skills watch started.');
        }
    }

    stop(showMessage = true): void {
        if (!this.isRunning) {
            if (showMessage) {
                vscode.window.showInformationMessage('RPA Skills watch is not running.');
            }
            return;
        }

        for (const disposable of this.disposables) {
            disposable.dispose();
        }

        this.disposables = [];

        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = undefined;
        }

        if (showMessage) {
            vscode.window.showInformationMessage('RPA Skills watch stopped.');
        }
    }

    toggle(): void {
        if (this.isRunning) {
            this.stop();
        } else {
            this.start();
        }
    }

    startFromConfiguration(): void {
        this.syncFromConfiguration(false);
    }

    syncFromConfiguration(showMessage = false): void {
        const enabled = getRpaSkillsConfigValue<boolean>('watch.enabled');
        if (enabled !== false) {
            this.start(showMessage);
        } else {
            this.stop(showMessage);
        }
    }

    get isRunning(): boolean {
        return this.disposables.length > 0;
    }

    dispose(): void {
        this.stop(false);
        this._onDidChangeWatchedFiles.dispose();
    }

    private scheduleRefresh(): void {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }

        this.refreshTimer = setTimeout(() => {
            this.refreshTimer = undefined;
            this.onRefreshRequested();
            this._onDidChangeWatchedFiles.fire();
        }, 250);
    }
}

const WATCH_PATTERNS = [
    '**/.agent/skills/**/SKILL.md',
    '**/.agent/agents/**/*.md',
    '**/.agent/workflows/**/*.md',
    '**/.agent/brain/**/*.md',
    '**/.cursor/rules/**/*.{md,mdc}',
    '**/.windsurf/rules/**/*.md',
    '**/.kilocode/rules/**/*.md',
    '**/.clinerules/**/*.md',
    '**/.kiro/agents/**/*.md',
    '**/.kiro/skills/**/SKILL.md',
    '**/.kiro/specs/**/*.md',
    '**/.kiro/steering/**/*.md',
    '**/.github/copilot-instructions.md',
    '**/.github/skills/**/SKILL.md',
    '**/.claude/skills/**/SKILL.md',
    '**/AGENTS.md',
    '**/CLAUDE.md',
    '**/.mcp.json',
    '**/.cursor/mcp.json',
    '**/.codex/config.toml'
];
