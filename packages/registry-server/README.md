# GravityKit Registry Server

Static Skill Registry proxy for the GravityKit VS Code extension.

It serves:

- `GET /manifest.json` - grouped skill manifest for the extension.
- `GET /skills/:skillId/download` - ZIP archive for one skill.
- `POST /-/refresh` - force a repo sync and manifest rebuild.
- `GET /healthz` - liveness check.

The server can read from a local checkout or clone/pull a private GitHub/GitLab repo using a PAT.

## Local Run

```bash
cd packages/registry-server
npm start
```

By default it reads the repository two directories above this package and serves the registry on `http://localhost:7077/manifest.json`.

## Config

Copy `config.example.json` to `config.json` or set `REGISTRY_CONFIG` to a custom path.

Important environment overrides:

- `PORT`
- `REGISTRY_BASE_URL`
- `GRAVITYKIT_LOCAL_REPO`
- `GRAVITYKIT_REPO_URL`
- `GRAVITYKIT_REPO_BRANCH`
- `GRAVITYKIT_REPO_USERNAME`
- `GRAVITYKIT_REPO_PAT`
- `GRAVITYKIT_SYNC_INTERVAL_MINUTES`

For GitLab PAT auth, set `GRAVITYKIT_REPO_USERNAME=oauth2` unless your GitLab instance requires a real username. For GitHub, set `GRAVITYKIT_REPO_USERNAME=x-access-token`.

## Docker

```bash
docker build -t gravitykit-registry packages/registry-server
docker run --rm -p 7077:7077 \
  -e REGISTRY_BASE_URL=http://localhost:7077 \
  -e GRAVITYKIT_REPO_URL=https://gitlab.example.com/team/gravitykit.git \
  -e GRAVITYKIT_REPO_USERNAME=oauth2 \
  -e GRAVITYKIT_REPO_PAT=your_pat \
  gravitykit-registry
```

If you mount a repo instead of cloning:

```bash
docker run --rm -p 7077:7077 \
  -e GRAVITYKIT_LOCAL_REPO=/repo \
  -v /path/to/VibeGravityKit:/repo:ro \
  gravitykit-registry
```
