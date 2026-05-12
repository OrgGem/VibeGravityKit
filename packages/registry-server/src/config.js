'use strict';

const fs = require('fs');
const path = require('path');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const REPO_ROOT = path.resolve(PACKAGE_ROOT, '..', '..');

function loadConfig() {
  const explicitConfigPath = process.env.REGISTRY_CONFIG;
  const configPath = explicitConfigPath
    ? path.resolve(explicitConfigPath)
    : path.join(PACKAGE_ROOT, fs.existsSync(path.join(PACKAGE_ROOT, 'config.json')) ? 'config.json' : 'config.example.json');
  const fileConfig = fs.existsSync(configPath)
    ? JSON.parse(fs.readFileSync(configPath, 'utf8'))
    : {};
  const configDir = path.dirname(configPath);
  const defaults = {
    port: 7077,
    baseUrl: '',
    syncIntervalMinutes: 60,
    cacheDir: path.join(PACKAGE_ROOT, '.cache'),
    source: {
      localPath: REPO_ROOT,
      repoUrl: '',
      branch: 'main',
      username: '',
      patEnv: 'GRAVITYKIT_REPO_PAT'
    },
    paths: {
      skillsDir: '.agent/skills',
      fallbackSkillsDir: 'GravityKit/.agent/skills',
      skillGroups: 'GravityKit/data/skill_groups.json',
      catalog: 'GravityKit/data/catalog.json'
    }
  };
  const config = deepMerge(defaults, fileConfig);

  config.port = Number(process.env.PORT || config.port || 7077);
  config.baseUrl = trimTrailingSlash(process.env.REGISTRY_BASE_URL || config.baseUrl || `http://localhost:${config.port}`);
  config.syncIntervalMinutes = Number(process.env.GRAVITYKIT_SYNC_INTERVAL_MINUTES || config.syncIntervalMinutes || 60);
  config.cacheDir = resolveMaybeRelative(process.env.GRAVITYKIT_CACHE_DIR || config.cacheDir, configDir);

  config.source = config.source || {};
  config.source.localPath = resolveMaybeRelative(process.env.GRAVITYKIT_LOCAL_REPO || config.source.localPath || REPO_ROOT, configDir);
  config.source.repoUrl = process.env.GRAVITYKIT_REPO_URL || config.source.repoUrl || '';
  config.source.branch = process.env.GRAVITYKIT_REPO_BRANCH || config.source.branch || 'main';
  config.source.username = process.env.GRAVITYKIT_REPO_USERNAME || config.source.username || '';
  config.source.patEnv = config.source.patEnv || 'GRAVITYKIT_REPO_PAT';

  config.paths = config.paths || {};
  config.paths.skillsDir = config.paths.skillsDir || '.agent/skills';
  config.paths.fallbackSkillsDir = config.paths.fallbackSkillsDir || 'GravityKit/.agent/skills';
  config.paths.skillGroups = config.paths.skillGroups || 'GravityKit/data/skill_groups.json';
  config.paths.catalog = config.paths.catalog || 'GravityKit/data/catalog.json';

  return config;
}

function deepMerge(base, override) {
  const result = { ...base };
  for (const [key, value] of Object.entries(override || {})) {
    if (value && typeof value === 'object' && !Array.isArray(value) && base[key] && typeof base[key] === 'object') {
      result[key] = deepMerge(base[key], value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

function resolveMaybeRelative(value, baseDir) {
  if (!value || path.isAbsolute(value)) {
    return value;
  }
  return path.resolve(baseDir, value);
}

function trimTrailingSlash(value) {
  return String(value).replace(/\/+$/, '');
}

module.exports = {
  PACKAGE_ROOT,
  REPO_ROOT,
  loadConfig
};
