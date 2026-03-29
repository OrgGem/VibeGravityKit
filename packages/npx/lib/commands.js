/**
 * Supplementary commands: version, doctor, list, groups.
 */

const { execSync } = require('child_process');
const { VERSION } = require('./constants');

/**
 * Show current version.
 */
function versionCommand() {
  console.log(`v${VERSION}`);
}

/**
 * Check environment health.
 */
function doctorCommand() {
  console.log('\n🩺 GravityKit Doctor - Checking Environment...\n');

  const checks = [
    { cmd: 'python --version', name: 'Python' },
    { cmd: 'node --version', name: 'Node.js' },
    { cmd: 'git --version', name: 'Git' },
    { cmd: 'npm --version', name: 'npm' },
  ];

  let allGood = true;

  for (const { cmd, name } of checks) {
    try {
      const output = execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
      const version = output.split('\n')[0];
      console.log(`✅ ${name.padEnd(10)}: Found (${version})`);
    } catch {
      console.log(`❌ ${name.padEnd(10)}: NOT FOUND`);
      allGood = false;
    }
  }

  // Check .agent folder
  const fs = require('fs');
  const path = require('path');
  if (fs.existsSync(path.join(process.cwd(), '.agent'))) {
    console.log(`✅ .agent    : Found in current directory`);
  } else {
    console.log(`⚠️  .agent    : Not found (Run 'gkt init' to install)`);
  }

  console.log('');
  if (allGood) {
    console.log('🎉 Your environment is healthy and ready to go!');
  } else {
    console.log('🩹 Some tools are missing. Please install them to use full capabilities.');
  }
}

/**
 * List available agents from installed .agent/workflows/.
 */
function listCommand() {
  const fs = require('fs');
  const path = require('path');
  const workflowsDir = path.join(process.cwd(), '.agent', 'workflows');

  if (!fs.existsSync(workflowsDir)) {
    console.log('❌ .agent/workflows directory not found. Run \'gkt init\' first.');
    return;
  }

  console.log('\n🤖 Available GravityKit Agents:\n');
  console.log(`${'Agent'.padEnd(25)} ${'Role Description'.padEnd(50)}`);
  console.log('-'.repeat(75));

  const files = fs.readdirSync(workflowsDir).filter((f) => f.endsWith('.md')).sort();
  for (const file of files) {
    const name = file.replace('.md', '');
    let description = 'No description available.';
    try {
      const content = fs.readFileSync(path.join(workflowsDir, file), 'utf8');
      const match = content.match(/description:\s*(.+)/);
      if (match) description = match[1].trim();
    } catch { /* ignore */ }
    console.log(`@[/${name.padEnd(22)}] ${description}`);
  }
  console.log('');
}

/**
 * List available skill groups.
 * Since groups are in the source repo, we download the groups file.
 */
async function groupsCommand() {
  const https = require('https');
  const { GITHUB_RAW, VERSION } = require('./constants');

  const url = `${GITHUB_RAW}/v${VERSION}/GravityKit/data/skill_groups.json`;

  try {
    const data = await new Promise((resolve, reject) => {
      https.get(url, { headers: { 'User-Agent': 'gkt-npx' } }, (res) => {
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode}`));
        }
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => resolve(body));
      }).on('error', reject);
    });

    const skillGroups = JSON.parse(data);

    console.log('\n📦 Available Skill Groups:\n');
    console.log(`${'Group'.padEnd(18)} ${'Skills'.padStart(6)} ${'Workflows'.padStart(9)}   ${'Description'.padEnd(50)}`);
    console.log('-'.repeat(90));

    for (const [name, config] of Object.entries(skillGroups)) {
      const skillsCount = (config.skills || []).length;
      const wfCount = (config.workflows || []).length;
      const desc = config.description || 'No description';
      console.log(
        `${name.padEnd(18)} ${String(skillsCount).padStart(6)} ${String(wfCount).padStart(9)}   ${desc}`
      );
    }
    console.log(`\n💡 Usage: gkt init <group-name>  (e.g. gkt init general-dev)`);
    console.log('');
  } catch (err) {
    console.log(`❌ Failed to fetch skill groups: ${err.message}`);
    console.log('   Make sure you have internet access.');
  }
}

module.exports = { versionCommand, doctorCommand, listCommand, groupsCommand };
