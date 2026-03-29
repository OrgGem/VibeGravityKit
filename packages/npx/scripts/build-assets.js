#!/usr/bin/env node

/**
 * Build script — copies workflow files and their associated skills
 * from GravityKit source into packages/npx/assets/ for bundling.
 *
 * Run from repo root:
 *   node packages/npx/scripts/build-assets.js
 */

'use strict';

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..');
const ASSETS_DIR = path.resolve(__dirname, '..', 'assets');

// Primary source: .agent/ at repo root (where workflows & skills actually live)
const ROOT_AGENT_DIR = path.join(REPO_ROOT, '.agent');
// Secondary source: GravityKit/.agent/ (legacy/alternate location)
const GK_AGENT_DIR = path.join(REPO_ROOT, 'GravityKit', '.agent');

const DATA_DIR = path.join(REPO_ROOT, 'GravityKit', 'data');
const IDE_ADAPTERS_DIR = path.join(REPO_ROOT, 'GravityKit', 'ide-adapters');

/**
 * Recursively copy a directory.
 */
function copyDir(src, dest) {
  if (!fs.existsSync(src)) return 0;
  fs.mkdirSync(dest, { recursive: true });
  let count = 0;
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      count += copyDir(s, d);
    } else {
      fs.copyFileSync(s, d);
      count++;
    }
  }
  return count;
}

/**
 * Remove directory recursively.
 */
function rmDir(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function main() {
  console.log('🔨 Building GravityKit npx assets...\n');

  // Clean previous build
  rmDir(ASSETS_DIR);
  fs.mkdirSync(ASSETS_DIR, { recursive: true });

  // 1. Read skill_groups.json to collect all workflow-referenced skills
  const groupsFile = path.join(DATA_DIR, 'skill_groups.json');
  if (!fs.existsSync(groupsFile)) {
    console.error('❌ skill_groups.json not found at:', groupsFile);
    process.exit(1);
  }

  const groups = JSON.parse(fs.readFileSync(groupsFile, 'utf8'));

  // Load aliases for skill name resolution (e.g. "supabase-postgres-best-practices" → "postgres-best-practices")
  const aliasesFile = path.join(DATA_DIR, 'aliases.json');
  const aliases = fs.existsSync(aliasesFile)
    ? JSON.parse(fs.readFileSync(aliasesFile, 'utf8')).aliases || {}
    : {};
  const allSkills = new Set();
  const allWorkflows = new Set();

  for (const [groupName, config] of Object.entries(groups)) {
    for (const s of (config.skills || [])) allSkills.add(s);
    for (const w of (config.workflows || [])) allWorkflows.add(w);
  }

  console.log(`📊 Found ${Object.keys(groups).length} groups`);
  console.log(`   → ${allSkills.size} unique skills`);
  console.log(`   → ${allWorkflows.size} unique workflows\n`);

  // 2. Copy workflows (search root .agent/ first, then GravityKit/.agent/)
  const wfSrcDirs = [
    path.join(ROOT_AGENT_DIR, 'workflows'),
    path.join(GK_AGENT_DIR, 'workflows'),
  ];
  const wfDestDir = path.join(ASSETS_DIR, '.agent', 'workflows');
  fs.mkdirSync(wfDestDir, { recursive: true });

  let wfCopied = 0;
  for (const wfName of allWorkflows) {
    const filename = `${wfName}.md`;
    const found = wfSrcDirs.find(d => fs.existsSync(path.join(d, filename)));
    if (found) {
      fs.copyFileSync(path.join(found, filename), path.join(wfDestDir, filename));
      wfCopied++;
    } else {
      console.log(`   ⚠️  Workflow not found: ${filename}`);
    }
  }
  console.log(`✅ Workflows: ${wfCopied}/${allWorkflows.size} copied`);

  // 3. Copy skills (search root .agent/ first, then GravityKit/.agent/)
  const skillSrcDirs = [
    path.join(ROOT_AGENT_DIR, 'skills'),
    path.join(GK_AGENT_DIR, 'skills'),
  ];
  const skillsDestDir = path.join(ASSETS_DIR, '.agent', 'skills');
  fs.mkdirSync(skillsDestDir, { recursive: true });

  let skillsCopied = 0;
  let skillsMissing = 0;
  for (const skillName of allSkills) {
    // Resolve alias if the skill name doesn't exist directly
    const realName = aliases[skillName] || skillName;
    const found = skillSrcDirs.find(d => fs.existsSync(path.join(d, realName)));
    if (found) {
      // Copy using the original name so group references work
      copyDir(path.join(found, realName), path.join(skillsDestDir, skillName));
      skillsCopied++;
    } else {
      console.log(`   ⚠️  Skill not found: ${skillName}${realName !== skillName ? ` (alias: ${realName})` : ''}`);
      skillsMissing++;
    }
  }
  console.log(`✅ Skills: ${skillsCopied}/${allSkills.size} copied (${skillsMissing} missing)`);

  // 4. Copy brain/ directory (search both locations)
  const brainDest = path.join(ASSETS_DIR, '.agent', 'brain');
  let brainCount = 0;
  for (const agentDir of [ROOT_AGENT_DIR, GK_AGENT_DIR]) {
    const brainSrc = path.join(agentDir, 'brain');
    if (fs.existsSync(brainSrc)) {
      brainCount += copyDir(brainSrc, brainDest);
    }
  }
  if (brainCount) console.log(`✅ Brain: ${brainCount} files copied`);

  // 5. Copy skill_groups.json
  fs.copyFileSync(groupsFile, path.join(ASSETS_DIR, 'skill_groups.json'));
  console.log(`✅ skill_groups.json copied`);

  // 6. Copy IDE adapters
  const ideDestDir = path.join(ASSETS_DIR, 'ide-adapters');
  if (fs.existsSync(IDE_ADAPTERS_DIR)) {
    const ideCount = copyDir(IDE_ADAPTERS_DIR, ideDestDir);
    console.log(`✅ IDE adapters: ${ideCount} files copied`);
  }

  // 7. Summary — calculate total size
  let totalSize = 0;
  function calcSize(dir) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        calcSize(p);
      } else {
        totalSize += fs.statSync(p).size;
      }
    }
  }
  calcSize(ASSETS_DIR);

  const sizeMB = (totalSize / 1024 / 1024).toFixed(1);
  console.log(`\n📦 Total assets size: ${sizeMB} MB`);
  console.log(`✨ Assets built successfully in: ${path.relative(REPO_ROOT, ASSETS_DIR)}`);
}

main();
