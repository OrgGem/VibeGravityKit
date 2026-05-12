'use strict';

const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { loadConfig } = require('../src/config');
const { buildRegistryState } = require('../src/manifest');
const { createZipFromDirectory } = require('../src/zip');

const config = loadConfig();
config.source.repoUrl = '';

const state = buildRegistryState(config, config.source.localPath);
assert(state.manifest.groups.length > 0, 'Expected at least one group in manifest.');
assert(state.skillsById.size > 0, 'Expected at least one skill in manifest.');

const firstSkill = state.skillsById.values().next().value;
const archive = createZipFromDirectory(firstSkill.dir, { rootName: firstSkill.id });
assert(archive.length > 22, 'Expected ZIP archive content.');
assert.strictEqual(archive.readUInt32LE(0), 0x04034b50, 'Expected ZIP local file header.');

fs.mkdirSync(config.cacheDir, { recursive: true });
fs.writeFileSync(
  path.join(config.cacheDir, 'smoke-manifest.json'),
  `${JSON.stringify(state.manifest, null, 2)}\n`,
  'utf8'
);

console.log(`Smoke OK: ${state.manifest.groups.length} groups, ${state.skillsById.size} skills, first ZIP ${archive.length} bytes.`);
