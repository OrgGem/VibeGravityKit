'use strict';

const http = require('http');
const { loadConfig } = require('./config');
const { resolveSource } = require('./git');
const { buildRegistryState } = require('./manifest');
const { createZipFromDirectory } = require('./zip');

const config = loadConfig();
let state;
let lastError;

async function rebuildRegistry() {
  try {
    const sourceRoot = resolveSource(config);
    state = buildRegistryState(config, sourceRoot);
    lastError = undefined;
    console.log(`Registry ready: ${state.manifest.groups.length} groups, ${state.skillsById.size} skills`);
  } catch (error) {
    lastError = error;
    console.error(`Registry rebuild failed: ${error.message}`);
  }
}

function createServer() {
  return http.createServer(async (request, response) => {
    try {
      const requestUrl = new URL(request.url || '/', config.baseUrl);

      if (request.method === 'GET' && requestUrl.pathname === '/healthz') {
        sendJson(response, lastError ? 503 : 200, {
          ok: !lastError,
          error: lastError?.message
        });
        return;
      }

      if (request.method === 'POST' && requestUrl.pathname === '/-/refresh') {
        await rebuildRegistry();
        sendJson(response, lastError ? 500 : 200, {
          ok: !lastError,
          error: lastError?.message,
          last_updated: state?.manifest.last_updated
        });
        return;
      }

      if (request.method === 'GET' && requestUrl.pathname === '/manifest.json') {
        if (!state) {
          sendJson(response, 503, { error: 'Registry is not ready.' });
          return;
        }

        sendJson(response, 200, state.manifest);
        return;
      }

      const downloadMatch = requestUrl.pathname.match(/^\/skills\/([^/]+)\/download$/);
      if (request.method === 'GET' && downloadMatch) {
        if (!state) {
          sendJson(response, 503, { error: 'Registry is not ready.' });
          return;
        }

        const skillId = decodeURIComponent(downloadMatch[1]);
        const skill = state.skillsById.get(skillId);
        if (!skill) {
          sendJson(response, 404, { error: `Skill not found: ${skillId}` });
          return;
        }

        const archive = createZipFromDirectory(skill.dir, { rootName: skill.id });
        response.writeHead(200, {
          'Content-Type': 'application/zip',
          'Content-Length': archive.length,
          'Content-Disposition': `attachment; filename="${skill.id}-${skill.manifestSkill.version}.zip"`
        });
        response.end(archive);
        return;
      }

      sendJson(response, 404, { error: 'Not found.' });
    } catch (error) {
      sendJson(response, 500, { error: error.message });
    }
  });
}

function sendJson(response, statusCode, body) {
  const payload = Buffer.from(`${JSON.stringify(body, null, 2)}\n`, 'utf8');
  response.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': payload.length,
    'Cache-Control': 'no-store'
  });
  response.end(payload);
}

async function main() {
  await rebuildRegistry();

  const intervalMs = Math.max(1, config.syncIntervalMinutes) * 60 * 1000;
  setInterval(rebuildRegistry, intervalMs).unref();

  createServer().listen(config.port, () => {
    console.log(`GravityKit registry server listening on ${config.baseUrl}`);
  });
}

if (require.main === module) {
  main();
}

module.exports = {
  createServer,
  rebuildRegistry
};
