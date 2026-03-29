/**
 * Shared constants for the GravityKit npx CLI.
 */

const path = require('path');
const fs = require('fs');

// Read version from package.json
const PKG = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8')
);

const VERSION = PKG.version;
const REPO_OWNER = 'OrgGem';
const REPO_NAME = 'VibeGravityKit';
const GITHUB_API = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}`;
const GITHUB_RAW = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}`;
const TARBALL_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/tags`;

const IDE_NAMES = new Set([
  'antigravity', 'cursor', 'windsurf', 'cline',
  'kilocode', 'copilot', 'kiro', 'all'
]);

/**
 * IDE target → directory mapping.
 * source / target paths are relative to repo root / cwd respectively.
 */
const IDE_CONFIG = {
  antigravity: {
    sourceRel: 'GravityKit/.agent',
    targetRel: '.agent',
    label: '.agent/ (workflows + skills)',
  },
  cursor: {
    sourceRel: 'GravityKit/ide-adapters/cursor',
    targetRel: '.cursor/rules',
    label: '.cursor/rules/ (Cursor IDE)',
  },
  windsurf: {
    sourceRel: 'GravityKit/ide-adapters/windsurf',
    targetRel: '.windsurf/rules',
    label: '.windsurf/rules/ (Windsurf IDE)',
  },
  cline: {
    sourceRel: 'GravityKit/ide-adapters/cline',
    targetRel: '.clinerules',
    label: '.clinerules/ (Cline IDE)',
  },
  kilocode: {
    sourceRel: 'GravityKit/ide-adapters/kilocode',
    targetRel: '.kilocode/rules',
    label: '.kilocode/rules/ (Kilo Code)',
  },
  copilot: {
    sourceRel: 'GravityKit/ide-adapters/copilot',
    targetRel: '.github/instructions',
    label: '.github/instructions/ (GitHub Copilot)',
  },
  kiro: {
    sourceRel: 'GravityKit/.agent',
    targetRel: '.kiro',
    label: '.kiro/ (Kiro IDE - skills, hooks, steering, specs)',
  },
};

module.exports = {
  VERSION,
  REPO_OWNER,
  REPO_NAME,
  GITHUB_API,
  GITHUB_RAW,
  TARBALL_URL,
  IDE_NAMES,
  IDE_CONFIG,
};
