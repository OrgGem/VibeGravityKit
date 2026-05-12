export interface RegistryManifest {
    version?: string;
    last_updated?: string;
    lastUpdated?: string;
    groups: RegistryGroup[];
}

export interface RegistryGroup {
    id: string;
    name: string;
    description?: string;
    skills: RegistrySkill[];
}

export interface RegistrySkill {
    id: string;
    name: string;
    version?: string;
    description?: string;
    downloadUrl?: string;
    download_url?: string;
    url?: string;
    dependencies?: string[];
    author?: string;
    tags?: string[];
    usage?: string;
    markdown?: string;
    [key: string]: unknown;
}

export interface NormalizedSkill {
    id: string;
    name: string;
    version?: string;
    description: string;
    downloadUrl?: string;
    dependencies: string[];
    author?: string;
    tags: string[];
    usage?: string;
    markdown?: string;
    raw: RegistrySkill;
}

export interface NormalizedGroup {
    id: string;
    name: string;
    description?: string;
    skills: NormalizedSkill[];
}

export interface InstalledSkillRecord {
    id: string;
    name?: string;
    version?: string;
    path: string;
    installedAt?: string;
}

export type SkillInstallStatus = 'notInstalled' | 'installed' | 'updateAvailable';

export interface SkillStatus {
    status: SkillInstallStatus;
    installedVersion?: string;
    installPath?: string;
}
