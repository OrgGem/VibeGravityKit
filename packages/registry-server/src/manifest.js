'use strict';

const fs = require('fs');
const path = require('path');

function buildRegistryState(config, sourceRoot) {
  const skillsRoot = findSkillsRoot(config, sourceRoot);
  const catalog = readJsonIfExists(path.join(sourceRoot, config.paths.catalog));
  const groupsConfig = readJsonIfExists(path.join(sourceRoot, config.paths.skillGroups));
  const catalogSkills = catalog ? (catalog.skills || catalog) : [];
  const catalogById = new Map(catalogSkills.map((skill) => [skill.id, skill]));
  const availableSkillIds = listSkillIds(skillsRoot);
  const skillsById = new Map();
  const groups = groupsConfig
    ? buildConfiguredGroups(config, groupsConfig, catalogById, availableSkillIds, skillsRoot, skillsById)
    : buildCategoryGroups(config, catalogById, availableSkillIds, skillsRoot, skillsById);

  const manifest = {
    version: '1.0',
    last_updated: new Date().toISOString(),
    groups
  };

  return {
    manifest,
    skillsById,
    sourceRoot,
    skillsRoot
  };
}

function findSkillsRoot(config, sourceRoot) {
  const primary = path.join(sourceRoot, config.paths.skillsDir);
  if (fs.existsSync(primary)) {
    return primary;
  }

  const fallback = path.join(sourceRoot, config.paths.fallbackSkillsDir);
  if (fs.existsSync(fallback)) {
    return fallback;
  }

  throw new Error(`No skills directory found at ${primary} or ${fallback}`);
}

function buildConfiguredGroups(config, groupsConfig, catalogById, availableSkillIds, skillsRoot, skillsById) {
  const groups = [];

  for (const [groupId, groupConfig] of Object.entries(groupsConfig)) {
    const skillIds = Array.isArray(groupConfig.skills) ? groupConfig.skills : [];
    const skills = skillIds
      .filter((skillId) => availableSkillIds.has(skillId))
      .map((skillId) => getOrCreateSkill(config, skillId, catalogById, skillsRoot, skillsById));

    if (skills.length === 0) {
      continue;
    }

    groups.push({
      id: groupId === '_default' ? 'default' : groupId,
      name: groupId === '_default' ? 'Default Base Skills' : titleFromId(groupId),
      description: groupConfig.description || '',
      skills
    });
  }

  return groups;
}

function buildCategoryGroups(config, catalogById, availableSkillIds, skillsRoot, skillsById) {
  const categories = new Map();

  for (const skillId of availableSkillIds) {
    const catalogSkill = catalogById.get(skillId);
    const category = catalogSkill?.category || 'general';
    if (!categories.has(category)) {
      categories.set(category, []);
    }
    categories.get(category).push(getOrCreateSkill(config, skillId, catalogById, skillsRoot, skillsById));
  }

  return Array.from(categories.entries()).map(([category, skills]) => ({
    id: category,
    name: titleFromId(category),
    description: '',
    skills: skills.sort((left, right) => left.id.localeCompare(right.id))
  }));
}

function getOrCreateSkill(config, skillId, catalogById, skillsRoot, skillsById) {
  if (skillsById.has(skillId)) {
    return skillsById.get(skillId).manifestSkill;
  }

  const skillDir = path.join(skillsRoot, skillId);
  const frontmatter = readSkillFrontmatter(skillDir);
  const catalogSkill = catalogById.get(skillId) || {};
  const manifestSkill = {
    id: skillId,
    name: frontmatter.name || catalogSkill.name || skillId,
    version: frontmatter.version || catalogSkill.version || '0.1.0',
    description: frontmatter.description || catalogSkill.description || '',
    author: frontmatter.author || frontmatter.source || catalogSkill.author || '',
    tags: Array.isArray(catalogSkill.tags) ? catalogSkill.tags : [],
    dependencies: parseList(frontmatter.dependencies || catalogSkill.dependencies),
    download_url: `${config.baseUrl}/skills/${encodeURIComponent(skillId)}/download`
  };

  skillsById.set(skillId, {
    id: skillId,
    dir: skillDir,
    manifestSkill
  });

  return manifestSkill;
}

function listSkillIds(skillsRoot) {
  const result = new Set();

  for (const entry of fs.readdirSync(skillsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) {
      continue;
    }

    if (fs.existsSync(path.join(skillsRoot, entry.name, 'SKILL.md'))) {
      result.add(entry.name);
    }
  }

  return result;
}

function readSkillFrontmatter(skillDir) {
  const skillFile = path.join(skillDir, 'SKILL.md');
  if (!fs.existsSync(skillFile)) {
    return {};
  }

  const content = fs.readFileSync(skillFile, 'utf8');
  const match = content.match(/^---\s*([\s\S]*?)\s*---/);
  if (!match) {
    return {};
  }

  const result = {};
  for (const line of match[1].split(/\r?\n/)) {
    const parsed = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!parsed) {
      continue;
    }

    const key = parsed[1];
    let value = parsed[2].trim();
    value = value.replace(/^['"]|['"]$/g, '');
    result[key] = value;
  }

  return result;
}

function parseList(value) {
  if (Array.isArray(value)) {
    return value.filter((item) => typeof item === 'string');
  }

  if (typeof value !== 'string' || !value.trim()) {
    return [];
  }

  if (value.startsWith('[') && value.endsWith(']')) {
    return value
      .slice(1, -1)
      .split(',')
      .map((item) => item.trim().replace(/^['"]|['"]$/g, ''))
      .filter(Boolean);
  }

  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function readJsonIfExists(filePath) {
  if (!fs.existsSync(filePath)) {
    return undefined;
  }

  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function titleFromId(id) {
  return id
    .replace(/^_+/, '')
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

module.exports = {
  buildRegistryState
};
