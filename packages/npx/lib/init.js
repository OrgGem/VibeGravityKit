/**
 * GravityKit init command — download and install skills/workflows.
 *
 * Strategy:
 *  1. Try bundled assets (packages/npx/assets/) — offline-capable
 *  2. Fall back to remote download from GitHub if bundled assets are missing
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { IDE_NAMES, IDE_CONFIG, VERSION } = require('./constants');
const { downloadRelease } = require('./download');

// Path to bundled assets (relative to this file)
const BUNDLED_ASSETS = path.join(__dirname, '..', 'assets');

// Sample prompts for post-init display
const WORKFLOW_SAMPLE_PROMPTS = {
  'wf-leader': 'Build a SaaS app for task management with auth and billing',
  'wf-quickstart': 'I want to create a landing page for my startup',
  'wf-planner': 'Analyze requirements and create PRD for an e-commerce platform',
  'wf-architect': 'Design the database schema and API for a booking system',
  'wf-designer': 'Create a modern design system with dark mode support',
  'wf-frontend-dev': 'Build the React dashboard with charts and user settings',
  'wf-backend-dev': 'Implement REST API with auth, CRUD, and file upload',
  'wf-fullstack-coder': 'Build a full-stack todo app with Next.js and PostgreSQL',
  'wf-mobile-dev': 'Create a React Native app with push notifications',
  'wf-qa-engineer': 'Write test cases and run E2E tests for the login flow',
  'wf-code-reviewer': 'Review my latest changes for security and best practices',
  'wf-security-engineer': 'Run a security audit on the authentication module',
  'wf-security-auditor': 'Audit the codebase for OWASP top 10 vulnerabilities',
  'wf-devops': 'Setup Docker and CI/CD pipeline for production deployment',
  'wf-cloud-deployer': 'Deploy the app to AWS with auto-scaling and monitoring',
  'wf-doc-writer': 'Generate API documentation and developer guides',
  'wf-tech-writer': 'Write technical docs for the SDK integration',
  'wf-deep-researcher': 'Research the latest trends in AI agent frameworks',
  'wf-researcher': 'Analyze the competitive landscape for project management tools',
  'wf-research-analyst': 'Create a market analysis report for fintech in SEA',
  'wf-meta-thinker': 'I have a vague idea about a social app \u2014 help me shape it',
  'wf-prompt-engineer': 'Optimize this prompt for better code generation results',
  'wf-n8n-automator': 'Build an n8n workflow to sync Slack messages to Notion',
  'wf-nocobase-plugin-expert': 'Create a NocoBase plugin for document management',
  'wf-nocobase-plugin-build': 'Build and deploy my NocoBase plugin to production',
  'wf-seo-specialist': 'Optimize my website for search engines',
  'wf-seo-marketer': 'Create an SEO content strategy for my blog',
  'wf-solution-architect': 'Design a microservices architecture for our platform',
  'wf-image-creator': 'Generate marketing screenshots and visual assets',
  'wf-release-manager': 'Generate changelog and prepare v2.0 release',
  'wf-quality-guardian': 'Run a comprehensive quality check on the codebase',
  'wf-knowledge-guide': 'Explain how the authentication module works',
  'wf-translator': 'Translate the app UI to Vietnamese and Japanese',
  'wf-observability-eng': 'Setup monitoring with Grafana and Prometheus',
  'wf-api-graphql-dev': 'Design and implement a GraphQL API with subscriptions',
  'wf-claude-code-dev': 'Build a custom MCP tool for database queries',
  'wf-context-data-eng': 'Build a RAG pipeline with vector search',
  'wf-database-eng': 'Design a PostgreSQL schema with migrations and CQRS',
  'wf-startup-advisor': 'Create a business plan for my SaaS startup',
  'wf-saas-connector': 'Integrate HubSpot CRM with our backend via API',
  'wf-ai-agent-builder': 'Build an AI agent with tool calling and memory',
};

/**
 * Show workflow info table after group init.
 */
function showGroupWorkflows(sourceAgentDir, workflowNames) {
  if (!workflowNames || workflowNames.length === 0) return;

  const wfDir = path.join(sourceAgentDir, 'workflows');
  const infos = [];

  for (const wfName of workflowNames) {
    const filePath = path.join(wfDir, `${wfName}.md`);
    let description = 'No description available.';
    try {
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8').slice(0, 500);
        const match = content.match(/description:\s*(.+)/);
        if (match) description = match[1].trim();
      }
    } catch (_) { /* ignore */ }
    const sample = WORKFLOW_SAMPLE_PROMPTS[wfName] || 'Help me with this task';
    infos.push({ name: wfName, description, sample });
  }

  console.log(`\n\ud83d\udccb Available Workflows (${infos.length}):\n`);
  console.log(`${'Workflow'.padEnd(30)} ${'Purpose & Features'}`);
  console.log('\u2500'.repeat(90));

  for (const info of infos) {
    const slash = `/${info.name}`;
    console.log(`  ${slash.padEnd(28)} ${info.description.slice(0, 80)}`);
  }

  console.log(`\n\ud83d\udca1 How to use \u2014 type the workflow name in your AI chat:\n`);
  const samples = infos.slice(0, 3);
  for (const info of samples) {
    console.log(`  \ud83d\udcce ${info.name}`);
    console.log(`     Prompt: "${info.sample}"`);
    console.log('');
  }
  console.log(`  \ud83d\udcac Tip: Type /wf- to filter only workflows in the / menu.`);
}

/**
 * Recursively copy a directory, optionally skipping existing files.
 */
function copyDir(src, dest, { skipExisting = false } = {}) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath, { skipExisting });
    } else {
      if (skipExisting && fs.existsSync(destPath)) continue;
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * Remove a directory recursively.
 */
function rmDir(dir) {
  if (!fs.existsSync(dir)) return;
  fs.rmSync(dir, { recursive: true, force: true });
}

/**
 * Load skill groups — from bundled assets or extracted source.
 */
function loadSkillGroups(sourceRoot) {
  // Try bundled first
  const bundledGroups = path.join(BUNDLED_ASSETS, 'skill_groups.json');
  if (fs.existsSync(bundledGroups)) {
    return JSON.parse(fs.readFileSync(bundledGroups, 'utf8'));
  }
  // Fall back to extracted source
  const groupsFile = path.join(sourceRoot, 'GravityKit', 'data', 'skill_groups.json');
  if (!fs.existsSync(groupsFile)) return {};
  return JSON.parse(fs.readFileSync(groupsFile, 'utf8'));
}

function getDefaultSkills(skillGroups) {
  return ((skillGroups && skillGroups._default && skillGroups._default.skills) || []);
}

function mergeGroupSkills(groupConfig, defaultSkills = []) {
  const merged = [];
  for (const skillName of ((groupConfig && groupConfig.skills) || [])) {
    if (!merged.includes(skillName)) merged.push(skillName);
  }
  for (const skillName of defaultSkills) {
    if (!merged.includes(skillName)) merged.push(skillName);
  }
  return merged;
}

function splitExistingSkills(skillsSrc, skillNames) {
  const existing = [];
  const missing = [];
  for (const skillName of skillNames) {
    const skillPath = path.join(skillsSrc, skillName, 'SKILL.md');
    if (fs.existsSync(skillPath)) {
      existing.push(skillName);
    } else {
      missing.push(skillName);
    }
  }
  return { existing, missing };
}

function warnMissing(label, names, limit = 10) {
  if (!names.length) return;
  const shown = names.slice(0, limit).join(', ');
  const suffix = names.length > limit ? `, ... +${names.length - limit} more` : '';
  console.log(`  Warning: ${names.length} configured ${label} not found: ${shown}${suffix}`);
}

/**
 * Check if bundled assets exist and contain the needed source dirs.
 */
function hasBundledAssets() {
  return fs.existsSync(path.join(BUNDLED_ASSETS, '.agent', 'skills'))
    && fs.existsSync(path.join(BUNDLED_ASSETS, '.agent', 'workflows'));
}

/**
 * Build a "sourceRoot" object from bundled assets that looks like
 * the extracted GitHub tarball structure.
 */
function getBundledSourceRoot() {
  // Return a virtual path object — we'll remap IDE_CONFIG paths to bundled assets
  return BUNDLED_ASSETS;
}

/**
 * Merge only the skills and workflows defined in a group config.
 * Only creates folders/files that don't already exist.
 */
function copyGroupSelective(sourceAgentDir, targetAgentDir, groupConfig, defaultSkills = []) {
  fs.mkdirSync(targetAgentDir, { recursive: true });

  // Copy brain/ only if it doesn't exist yet
  const brainSrc = path.join(sourceAgentDir, 'brain');
  const brainDst = path.join(targetAgentDir, 'brain');
  if (fs.existsSync(brainSrc) && !fs.existsSync(brainDst)) {
    copyDir(brainSrc, brainDst);
  }

  // Copy selected skills — skip if already exists
  const skillsTarget = path.join(targetAgentDir, 'skills');
  fs.mkdirSync(skillsTarget, { recursive: true });
  const skillsSrc = path.join(sourceAgentDir, 'skills');
  let copiedSkills = 0;
  const missingSkills = [];
  for (const skillName of mergeGroupSkills(groupConfig, defaultSkills)) {
    const src = path.join(skillsSrc, skillName);
    const dst = path.join(skillsTarget, skillName);
    if (fs.existsSync(path.join(src, 'SKILL.md')) && !fs.existsSync(dst)) {
      copyDir(src, dst);
      copiedSkills++;
    } else if (!fs.existsSync(path.join(src, 'SKILL.md'))) {
      missingSkills.push(skillName);
    }
  }
  warnMissing('skills', missingSkills);

  // Copy selected workflows — skip if already exists
  const wfTarget = path.join(targetAgentDir, 'workflows');
  fs.mkdirSync(wfTarget, { recursive: true });
  for (const wfName of (groupConfig.workflows || [])) {
    const src = path.join(sourceAgentDir, 'workflows', `${wfName}.md`);
    const dst = path.join(wfTarget, `${wfName}.md`);
    if (fs.existsSync(src) && !fs.existsSync(dst)) {
      fs.copyFileSync(src, dst);
    }
  }

  return copiedSkills;
}

/**
 * Install for Kiro IDE — merges .agent/ → .kiro/ structure.
 * Only creates folders/files that don't already exist.
 */
function installKiro(sourceRoot, cwd, groupConfig, useBundled, defaultSkills = []) {
  const kiroDir = path.join(cwd, '.kiro');
  const agentDir = useBundled
    ? path.join(sourceRoot, '.agent')
    : path.join(sourceRoot, 'GravityKit', '.agent');
  const templatesDir = useBundled
    ? path.join(sourceRoot, 'ide-adapters', 'kiro')
    : path.join(sourceRoot, 'GravityKit', 'ide-adapters', 'kiro');

  fs.mkdirSync(kiroDir, { recursive: true });

  // 1. Copy skills (skip existing)
  const skillsSrc = path.join(agentDir, 'skills');
  const skillsTarget = path.join(kiroDir, 'skills');
  fs.mkdirSync(skillsTarget, { recursive: true });
  let copiedSkills = 0;

  if (fs.existsSync(skillsSrc)) {
    if (groupConfig) {
      const missingSkills = [];
      for (const skillName of mergeGroupSkills(groupConfig, defaultSkills)) {
        const src = path.join(skillsSrc, skillName);
        const dst = path.join(skillsTarget, skillName);
        if (fs.existsSync(path.join(src, 'SKILL.md')) && !fs.existsSync(dst)) {
          copyDir(src, dst);
          copiedSkills++;
        } else if (!fs.existsSync(path.join(src, 'SKILL.md'))) {
          missingSkills.push(skillName);
        }
      }
      warnMissing('skills', missingSkills);
    } else {
      for (const entry of fs.readdirSync(skillsSrc, { withFileTypes: true })) {
        const dst = path.join(skillsTarget, entry.name);
        if (entry.isDirectory() && fs.existsSync(path.join(skillsSrc, entry.name, 'SKILL.md')) && !fs.existsSync(dst)) {
          copyDir(path.join(skillsSrc, entry.name), dst);
          copiedSkills++;
        }
      }
    }
  }

  // 2. Copy steering (skip if exists)
  const steeringSrc = path.join(templatesDir, 'steering');
  const steeringDst = path.join(kiroDir, 'steering');
  if (fs.existsSync(steeringSrc) && !fs.existsSync(steeringDst)) {
    copyDir(steeringSrc, steeringDst);
  }

  // 3. Copy hooks (skip if exists)
  const hooksSrc = path.join(templatesDir, 'hooks');
  const hooksDst = path.join(kiroDir, 'hooks');
  if (fs.existsSync(hooksSrc) && !fs.existsSync(hooksDst)) {
    copyDir(hooksSrc, hooksDst);
  }

  // 4. Create specs/
  fs.mkdirSync(path.join(kiroDir, 'specs'), { recursive: true });

  return copiedSkills;
}

/**
 * Resolve IDE source/target paths for bundled vs remote mode.
 */
function resolveSourceDir(sourceRoot, ide, useBundled) {
  const config = IDE_CONFIG[ide];
  if (!config) return null;

  if (useBundled) {
    // Bundled paths: assets/.agent or assets/ide-adapters/xxx
    if (ide === 'antigravity') {
      return path.join(sourceRoot, '.agent');
    }
    return path.join(sourceRoot, 'ide-adapters', ide);
  }
  // Remote paths use the original sourceRel (relative to extracted tarball)
  return path.join(sourceRoot, config.sourceRel);
}

/**
 * Main init command handler.
 *
 * @param {string} target  IDE name or group name
 * @param {string|null} group  Optional group filter
 */
async function initCommand(target = 'all', group = null) {
  const cwd = process.cwd();
  const useBundled = hasBundledAssets();
  let sourceRoot;
  let tmpDir = null;

  if (useBundled) {
    console.log(`📦 Using bundled assets (v${VERSION})...`);
    sourceRoot = BUNDLED_ASSETS;
  } else {
    console.log(`🌐 No bundled assets — downloading from GitHub...`);
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gkt-'));
    sourceRoot = await downloadRelease(VERSION, tmpDir);
  }

  try {
    const skillGroups = loadSkillGroups(sourceRoot);

    // Auto-detect: IDE name or group name?
    let ideTarget, groupName;
    if (IDE_NAMES.has(target)) {
      ideTarget = target;
      groupName = group;
    } else if (skillGroups[target]) {
      ideTarget = 'antigravity';
      groupName = target;
    } else {
      console.log(`❌ Unknown target: '${target}'`);
      console.log(`   IDE names: all, antigravity, cursor, windsurf, cline, kilocode, copilot, kiro`);
      console.log(`   Group names: ${Object.keys(skillGroups).join(', ')}`);
      return;
    }

    // Validate group
    if (groupName && !skillGroups[groupName]) {
      console.log(`❌ Unknown skill group: '${groupName}'`);
      console.log(`   Available groups: ${Object.keys(skillGroups).join(', ')}`);
      return;
    }

    // Determine which IDEs to install
    const targets = ideTarget === 'all'
      ? Object.keys(IDE_CONFIG)
      : [ideTarget];

    if (groupName) {
      const grp = skillGroups[groupName];
      const defaultSkills = getDefaultSkills(skillGroups);
      const allSkills = mergeGroupSkills(grp, defaultSkills);
      const agentDir = useBundled
        ? path.join(sourceRoot, '.agent')
        : path.join(sourceRoot, 'GravityKit', '.agent');
      const { existing } = splitExistingSkills(path.join(agentDir, 'skills'), allSkills);
      const extra = defaultSkills.filter(skillName => !(grp.skills || []).includes(skillName)).length;
      console.log(`🚀 Installing group '${groupName}' (${grp.description})...`);
      console.log(
        `   Skills: ${(grp.skills || []).length} + ${extra} default ` +
        `(${existing.length}/${allSkills.length} available) | ` +
        `Workflows: ${(grp.workflows || []).length}`,
      );
    } else {
      console.log(`🚀 Installing GravityKit (all skills)...`);
    }

    let installed = 0;
    for (const ide of targets) {
      const config = IDE_CONFIG[ide];
      if (!config) continue;

      const sourceDir = resolveSourceDir(sourceRoot, ide, useBundled);
      const targetDir = path.join(cwd, config.targetRel);

      if (!sourceDir || !fs.existsSync(sourceDir)) {
        console.log(`  ⚠️  Skipped ${ide}: source not found`);
        continue;
      }

      try {
        if (ide === 'kiro') {
          const grp = groupName ? skillGroups[groupName] : null;
          const copied = installKiro(sourceRoot, cwd, grp, useBundled, getDefaultSkills(skillGroups));
          console.log(`  ✅ ${config.label} (${copied} skills)`);
        } else if (groupName && ide === 'antigravity') {
          const copied = copyGroupSelective(sourceDir, targetDir, skillGroups[groupName], getDefaultSkills(skillGroups));
          console.log(`  ✅ ${config.label} (${copied} skills)`);
        } else {
          // Full copy — merge into existing directory
          fs.mkdirSync(path.dirname(targetDir), { recursive: true });
          copyDir(sourceDir, targetDir, { skipExisting: true });
          console.log(`  ✅ ${config.label}`);
        }
        installed++;
      } catch (err) {
        console.log(`  ❌ ${ide}: ${err.message}`);
      }
    }

    console.log(`\n✨ Done! Installed for ${installed} IDE(s).`);
    if (groupName) {
      const grp = skillGroups[groupName];
      const agentDir = useBundled
        ? path.join(sourceRoot, '.agent')
        : path.join(sourceRoot, 'GravityKit', '.agent');
      showGroupWorkflows(agentDir, grp.workflows || []);
    } else {
      console.log('\n💡 Suggestions for your next steps (Type these in your AI chat):');
      console.log('  👉 @[/wf-leader]       : Orchestrate the entire team from concept to production');
      console.log('  👉 @[/wf-quickstart]   : Build an entire project automatically (no approvals needed)');
      console.log('  👉 @[/wf-planner]      : Analyze requirements and create detailed PRDs');
      console.log('  👉 @[/wf-gen-doc]      : Generate AI-designed PowerPoint presentations');
      console.log('  👉 @[/wf-uipath-project]: End-to-end UiPath RPA automation workflow');
      console.log('\n💬 Tip: Type /wf- to filter and view all available workflows.');

      console.log('\n🧠 Enable Semantic Code Graph Search (Requires Python 3.9+):');
      console.log('  Run this command to build the FAISS index and auto-configure MCP servers for your IDEs:');
      console.log('  👉 npx gkt mcp');
    }
  } finally {
    // Clean up temp directory if we downloaded
    if (tmpDir) rmDir(tmpDir);
  }
}

module.exports = { initCommand };
