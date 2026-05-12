'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

function resolveSource(config) {
  if (!config.source.repoUrl) {
    return config.source.localPath;
  }

  return syncGitRepo(config);
}

function syncGitRepo(config) {
  fs.mkdirSync(config.cacheDir, { recursive: true });
  const repoDir = path.join(config.cacheDir, 'repo');
  const branch = config.source.branch || 'main';
  const authUrl = withPatAuth(config.source.repoUrl, {
    username: config.source.username,
    token: process.env[config.source.patEnv || 'GRAVITYKIT_REPO_PAT']
  });

  if (fs.existsSync(path.join(repoDir, '.git'))) {
    runGit(['-C', repoDir, 'fetch', '--depth=1', 'origin', branch]);
    runGit(['-C', repoDir, 'checkout', branch]);
    runGit(['-C', repoDir, 'reset', '--hard', 'FETCH_HEAD']);
    return repoDir;
  }

  fs.rmSync(repoDir, { recursive: true, force: true });
  runGit(['clone', '--depth=1', '--branch', branch, authUrl, repoDir]);
  return repoDir;
}

function withPatAuth(repoUrl, auth) {
  if (!auth.token || !/^https:\/\//i.test(repoUrl)) {
    return repoUrl;
  }

  const url = new URL(repoUrl);
  url.username = auth.username || 'oauth2';
  url.password = auth.token;
  return url.toString();
}

function runGit(args) {
  childProcess.execFileSync('git', args, {
    stdio: ['ignore', 'ignore', 'pipe']
  });
}

module.exports = {
  resolveSource
};
