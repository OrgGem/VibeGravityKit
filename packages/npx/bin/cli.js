#!/usr/bin/env node

/**
 * GravityKit CLI — npx entry point.
 *
 * Usage:
 *   npx gkt init [target] [--group <name>]
 *   npx gkt list
 *   npx gkt groups
 *   npx gkt doctor
 *   npx gkt version
 */

'use strict';

const { initCommand } = require('../lib/init');
const {
  versionCommand,
  doctorCommand,
  listCommand,
  groupsCommand,
} = require('../lib/commands');

const HELP = `
  GravityKit CLI — The AI-Native Software House in a Box

  Usage:
    gkt init [target] [--group <name>]   Install GravityKit in the current directory
    gkt list                              List available AI Agents
    gkt groups                            List available skill groups
    gkt doctor                            Check environment health
    gkt version                           Show current version
    gkt help                              Show this help message

  Targets for init:
    all (default), antigravity, cursor, windsurf, cline, kilocode, copilot, kiro
    Or a group name (run 'gkt groups' to see available groups)

  Examples:
    npx gkt init                         Install all skills for all IDEs
    npx gkt init antigravity             Install all skills for Antigravity
    npx gkt init general-dev             Install general-dev group
    npx gkt init antigravity --group n8n-dev
`;

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'help';

  switch (command) {
    case 'init': {
      const target = args[1] || 'all';
      let group = null;
      const groupIdx = args.indexOf('--group');
      if (groupIdx !== -1 && args[groupIdx + 1]) {
        group = args[groupIdx + 1];
      }
      // Also support -g shorthand
      const gIdx = args.indexOf('-g');
      if (gIdx !== -1 && args[gIdx + 1]) {
        group = args[gIdx + 1];
      }
      await initCommand(target, group);
      break;
    }

    case 'list':
      listCommand();
      break;

    case 'groups':
      await groupsCommand();
      break;

    case 'doctor':
      doctorCommand();
      break;

    case 'version':
    case '--version':
    case '-v':
      versionCommand();
      break;

    case 'help':
    case '--help':
    case '-h':
      console.log(HELP);
      break;

    default:
      console.log(`❌ Unknown command: '${command}'`);
      console.log(HELP);
      process.exitCode = 1;
  }
}

main().catch((err) => {
  console.error('❌ Error:', err.message);
  process.exitCode = 1;
});
