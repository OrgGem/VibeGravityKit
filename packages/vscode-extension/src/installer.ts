import * as vscode from 'vscode';
import axios from 'axios';
import AdmZip = require('adm-zip');
import * as fs from 'fs';
import * as path from 'path';
import { ensureInside, getSkillsRoot, getWorkspaceRootOrUndefined, safeSkillDirectoryName, getRpaSkillsConfigValue } from './config';
import { NormalizedSkill, SkillStatus } from './types';

export interface SkillRegistryLookup {
    findSkillById(skillId: string): NormalizedSkill | undefined;
    getSkillStatus(skill: NormalizedSkill): SkillStatus;
    refreshLocalState(): void;
}

export interface SkillInstallTarget {
    id?: string;
    label: string;
    rootPath: string;
    mode: 'skillDirectory' | 'markdownRule';
    ruleFileExtension?: string;
}

export async function installSkill(skill: NormalizedSkill, registry?: SkillRegistryLookup): Promise<void> {
    const plan = await buildInstallPlan(skill, registry);
    await installPlan(`Installing ${skill.name}...`, plan, registry);
}

export async function installSkillToTarget(
    skill: NormalizedSkill,
    target: SkillInstallTarget,
    registry?: SkillRegistryLookup
): Promise<void> {
    const plan = await buildInstallPlan(skill, registry, true);
    await installPlan(`Installing ${skill.name} for ${target.label}...`, plan, registry, target);
}

export async function installSkillsToTarget(
    skills: NormalizedSkill[],
    target: SkillInstallTarget,
    registry?: SkillRegistryLookup
): Promise<void> {
    await installPlan(`Installing selected skills for ${target.label}...`, uniqueSkills(skills), registry, target);
}

export async function installGroup(groupName: string, skills: NormalizedSkill[], registry?: SkillRegistryLookup): Promise<void> {
    if (skills.length === 0) {
        vscode.window.showInformationMessage(`Group ${groupName} does not contain any skills.`);
        return;
    }

    const answer = await vscode.window.showInformationMessage(
        `Install ${skills.length} skills from ${groupName}?`,
        { modal: true },
        'Install'
    );

    if (answer !== 'Install') {
        return;
    }

    await installPlan(`Installing ${groupName} skills...`, uniqueSkills(skills), registry);
}

async function installPlan(
    title: string,
    skills: NormalizedSkill[],
    registry?: SkillRegistryLookup,
    target?: SkillInstallTarget
): Promise<void> {
    if (skills.length === 0) {
        return;
    }

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title,
        cancellable: false
    }, async (progress) => {
        try {
            const increment = 100 / skills.length;
            for (const skill of skills) {
                progress.report({ message: skill.name });
                await installSingleSkill(skill, target);
                progress.report({ increment });
            }

            registry?.refreshLocalState();
            const installLocation = target ? ` for ${target.label} at ${path.relative(getWorkspaceRootOrUndefined() || process.cwd(), target.rootPath).replace(/\\/g, '/')}` : '';
            vscode.window.showInformationMessage(
                skills.length === 1
                    ? `Successfully installed skill: ${skills[0].name}${installLocation}`
                    : `Successfully installed ${skills.length} skills${installLocation}.`
            );
        } catch (error: any) {
            vscode.window.showErrorMessage(`Installation failed: ${error.message}`);
        }
    });
}

async function buildInstallPlan(
    skill: NormalizedSkill,
    registry?: SkillRegistryLookup,
    includeInstalledDependencies = false
): Promise<NormalizedSkill[]> {
    if (!registry || skill.dependencies.length === 0) {
        return [skill];
    }

    const dependencies = skill.dependencies
        .map((dependencyId) => registry.findSkillById(dependencyId))
        .filter((dependency): dependency is NormalizedSkill => Boolean(dependency))
        .filter((dependency) => includeInstalledDependencies || registry.getSkillStatus(dependency).status === 'notInstalled');

    if (dependencies.length === 0) {
        return [skill];
    }

    const answer = await vscode.window.showWarningMessage(
        `${skill.name} requires ${dependencies.length} dependencies. Install them now?`,
        { modal: true },
        'Install dependencies',
        'Skip dependencies'
    );

    if (answer !== 'Install dependencies') {
        return [skill];
    }

    return uniqueSkills([...dependencies, skill]);
}

async function installSingleSkill(skill: NormalizedSkill, target?: SkillInstallTarget): Promise<void> {
    if (!skill.downloadUrl) {
        throw new Error(`Skill ${skill.name} does not define a download URL.`);
    }

    const installTarget = target || {
        label: 'workspace',
        rootPath: getSkillsRoot(),
        mode: 'skillDirectory' as const
    };
    const skillsRoot = installTarget.rootPath;
    fs.mkdirSync(skillsRoot, { recursive: true });

    const safeSkillId = safeSkillDirectoryName(skill.id);
    const targetDir = installTarget.mode === 'skillDirectory'
        ? path.resolve(skillsRoot, safeSkillId)
        : path.resolve(skillsRoot, `${safeSkillId}.${installTarget.ruleFileExtension || 'md'}`);
    const tempDir = path.resolve(skillsRoot, `.${safeSkillId}.tmp-${Date.now()}`);
    ensureInside(skillsRoot, targetDir, `Install target for ${skill.id} escapes the configured skills directory.`);
    ensureInside(skillsRoot, tempDir, `Temporary install target for ${skill.id} escapes the configured skills directory.`);

    try {
        const archive = await downloadArchive(skill.downloadUrl);
        fs.rmSync(tempDir, { recursive: true, force: true });
        fs.mkdirSync(tempDir, { recursive: true });
        extractZip(archive, tempDir);

        if (!fs.existsSync(path.join(tempDir, 'SKILL.md'))) {
            throw new Error(`Archive for ${skill.name} does not contain SKILL.md at its root.`);
        }

        if (installTarget.mode === 'skillDirectory') {
            fs.rmSync(targetDir, { recursive: true, force: true });
            fs.renameSync(tempDir, targetDir);
            writeInstallMetadata(skill, targetDir);
        } else {
            fs.writeFileSync(targetDir, renderRuleFile(skill, fs.readFileSync(path.join(tempDir, 'SKILL.md'), 'utf8'), installTarget), 'utf8');
            fs.rmSync(tempDir, { recursive: true, force: true });
        }
        
        updateSkillsIndex(skill, targetDir);
    } catch (error) {
        fs.rmSync(tempDir, { recursive: true, force: true });
        throw error;
    }
}

async function downloadArchive(downloadUrl: string): Promise<Buffer> {
    if (/^https?:\/\//i.test(downloadUrl)) {
        const response = await axios.get<ArrayBuffer>(downloadUrl, {
            responseType: 'arraybuffer'
        });
        return Buffer.from(response.data);
    }

    const workspaceRoot = getWorkspaceRootOrUndefined();
    const archivePath = downloadUrl.startsWith('file://')
        ? vscode.Uri.parse(downloadUrl).fsPath
        : path.resolve(workspaceRoot || process.cwd(), downloadUrl);

    return fs.promises.readFile(archivePath);
}

function extractZip(archive: Buffer, targetDir: string): void {
    const zip = new AdmZip(archive);
    const entries = zip.getEntries();
    const stripRoot = findCommonRoot(entries.map((entry) => normalizeZipPath(entry.entryName)));

    for (const entry of entries) {
        if (entry.isDirectory) {
            continue;
        }

        const normalizedName = normalizeZipPath(entry.entryName);
        const relativeName = stripRoot && normalizedName.startsWith(`${stripRoot}/`)
            ? normalizedName.slice(stripRoot.length + 1)
            : normalizedName;

        if (!relativeName) {
            continue;
        }

        const destination = path.resolve(targetDir, relativeName);
        ensureInside(targetDir, destination, `Blocked unsafe ZIP entry: ${entry.entryName}`);
        fs.mkdirSync(path.dirname(destination), { recursive: true });
        fs.writeFileSync(destination, entry.getData());
    }
}

function normalizeZipPath(entryName: string): string {
    return entryName.replace(/\\/g, '/').replace(/^\/+/, '');
}

function findCommonRoot(entryNames: string[]): string | undefined {
    const fileNames = entryNames.filter(Boolean);
    if (fileNames.length === 0 || fileNames.some((entryName) => !entryName.includes('/'))) {
        return undefined;
    }

    const [firstRoot] = fileNames[0].split('/');
    return fileNames.every((entryName) => entryName.split('/')[0] === firstRoot) ? firstRoot : undefined;
}

function writeInstallMetadata(skill: NormalizedSkill, targetDir: string): void {
    const metadata = {
        id: skill.id,
        name: skill.name,
        version: skill.version,
        dependencies: skill.dependencies,
        downloadUrl: skill.downloadUrl,
        installedAt: new Date().toISOString()
    };

    fs.writeFileSync(
        path.join(targetDir, '.gravitykit-skill.json'),
        `${JSON.stringify(metadata, null, 2)}\n`,
        'utf8'
    );
}

function updateSkillsIndex(skill: NormalizedSkill, targetDir: string): void {
    const workspaceRoot = getWorkspaceRootOrUndefined();
    if (!workspaceRoot) {
        return;
    }

    const brainPathConfig = getRpaSkillsConfigValue<string>('brain.path') || '.agent/brain';
    const brainDir = path.resolve(workspaceRoot, brainPathConfig);
    const indexPath = path.join(brainDir, 'skills_index.json');

    if (!fs.existsSync(brainDir)) {
        fs.mkdirSync(brainDir, { recursive: true });
    }

    let indexData: any[] = [];
    if (fs.existsSync(indexPath)) {
        try {
            const content = fs.readFileSync(indexPath, 'utf8');
            if (content.trim()) {
                indexData = JSON.parse(content);
            }
        } catch (e) {
            console.error('Failed to parse skills_index.json', e);
        }
    }

    let relPath = path.relative(workspaceRoot, targetDir).replace(/\\/g, '/');
    if (!targetDir.endsWith('.md') && !targetDir.endsWith('.mdc')) {
        relPath = relPath + '/SKILL.md';
    }

    indexData = indexData.filter((s: any) => s.name !== skill.name);

    indexData.push({
        name: skill.name,
        description: skill.description || skill.name,
        path: relPath
    });

    fs.writeFileSync(indexPath, JSON.stringify(indexData, null, 2), 'utf8');
}

function renderRuleFile(skill: NormalizedSkill, skillMarkdown: string, target: SkillInstallTarget): string {
    const body = stripFrontmatter(skillMarkdown).trim();
    const description = (skill.description || skill.name).replace(/\r?\n/g, ' ').trim();

    if (target.ruleFileExtension === 'mdc') {
        return [
            '---',
            `description: ${JSON.stringify(description)}`,
            'alwaysApply: false',
            '---',
            '',
            `# ${skill.name}`,
            '',
            body,
            ''
        ].join('\n');
    }

    return [
        '---',
        `description: ${JSON.stringify(description)}`,
        '---',
        '',
        `# ${skill.name}`,
        '',
        body,
        ''
    ].join('\n');
}

function stripFrontmatter(markdown: string): string {
    return markdown.replace(/^---\s*[\s\S]*?\s*---\s*/, '');
}

function uniqueSkills(skills: NormalizedSkill[]): NormalizedSkill[] {
    const seen = new Set<string>();
    const result: NormalizedSkill[] = [];

    for (const skill of skills) {
        if (seen.has(skill.id)) {
            continue;
        }

        seen.add(skill.id);
        result.push(skill);
    }

    return result;
}
