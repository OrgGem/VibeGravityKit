---
description: How to build a NocoBase plugin (standalone or as part of the monorepo)
---

# NocoBase Plugin Build Guide

## Prerequisites

1. **Yarn workspaces** — Plugin must be in a path matching `packages/*/*` or `packages/*/*/*` in root `package.json` workspaces
2. **`@nocobase/build`** — Must be installed (part of NocoBase core at `packages/core/build`)
3. **`yarn install`** — Must have been run after creating a new plugin so workspaces recognize it

---

## Scaffold a New Plugin

```bash
# From NocoBase root — generates boilerplate in packages/plugins/@nocobase/
yarn nocobase create-plugin @nocobase/plugin-<name>

# Then register in workspace and install deps
yarn install
```

The scaffold creates all required files (`package.json`, `client.js`, `server.js`, `src/`).

---

## Build Command

### From NocoBase root directory:

// turbo-all

```bash
# Standard build (may fail on declarations if core packages aren't built)
npx nocobase-build @nocobase/plugin-<name>

# Skip declaration generation (use when core lib/ folders don't exist)
npx nocobase-build @nocobase/plugin-<name> --no-dts

# Via yarn script (equivalent)
yarn nocobase build @nocobase/plugin-<name>
yarn nocobase build @nocobase/plugin-<name> --no-dts
```

### What the build does (3 phases):

1. **Client** — Rspack bundles `src/client/index.tsx` → `dist/client/index.js` (externals: react, antd, @nocobase/\*)
2. **Server** — NCC compiles `src/server/index.ts` → `dist/server/index.js` + bundled deps (externals: @nocobase/\*)
3. **Declarations** (optional) — TypeScript `tsc` generates `.d.ts` files. **Requires** all `@nocobase/*` peer deps to have pre-built `lib/` folders

---

## When to use `--no-dts`

Use `--no-dts` when:

- You're in a **dev environment** where core packages haven't been fully built yet
- Core packages like `@nocobase/server`, `@nocobase/client` don't have `lib/` directories
- You just need a working runtime build for testing

The `--no-dts` flag is **safe** — declarations are only needed for TypeScript consumers, not for NocoBase runtime.

---

## Development Mode (Hot Reload)

```bash
# Watch mode — rebuilds on file change (server only)
yarn nocobase build @nocobase/plugin-<name> --watch

# Full dev server with hot reload (requires NocoBase dev setup)
yarn dev
```

> ⚠️ Client changes require a full browser refresh even in watch mode. Server changes require restarting the NocoBase process.

---

## Plugin `package.json` Requirements

```json
{
  "name": "@nocobase/plugin-<name>",
  "version": "1.0.0",
  "main": "./dist/server/index.js",
  "dependencies": {
    "pg": "^8.x"
  },
  "peerDependencies": {
    "@nocobase/client": "2.x",
    "@nocobase/server": "2.x",
    "@nocobase/database": "2.x"
  },
  "devDependencies": {
    "@nocobase/test": "2.x"
  }
}
```

### Key rules:

- **`main`** must point to `./dist/server/index.js`
- **`dependencies`** — Runtime packages bundled INTO dist/ (e.g., `pg`, `lodash`)
- **`peerDependencies`** — NocoBase packages (externalized, NOT bundled). Also determines plugin load order via `@hapi/topo` topological sort
- **`devDependencies`** — Only for development/testing, never bundled

> ⚠️ The build tool warns if packages are in `devDependencies` that should be in `dependencies`. This means: if the plugin NEEDS a package at runtime, put it in `dependencies`.

---

## Required File Structure

```
plugin-<name>/
├── package.json              # REQUIRED - see above
├── client.js                 # module.exports = require('./dist/client');
├── client.d.ts               # export * from './dist/client';
├── server.js                 # module.exports = require('./dist/server');
├── server.d.ts               # export * from './dist/server';
├── src/
│   ├── index.ts              # export * from './server'; export { default } from './server';
│   ├── server/
│   │   ├── index.ts          # import { name } from '../../package.json'; export { default } from './plugin'; export const namespace = name;
│   │   └── plugin.ts         # Plugin class
│   ├── client/
│   │   └── index.tsx         # Client plugin class
│   └── locale/
│       ├── en-US.json
│       └── zh-CN.json
```

---

## Plugin Class Skeleton

### Server (`src/server/plugin.ts`):

```typescript
import { Plugin } from "@nocobase/server";

export class PluginMyNameServer extends Plugin {
  async afterAdd() {}
  async beforeLoad() {}

  async load() {
    // Register collections, routes, actions here
    this.db.collection({ name: "my_table", fields: [] });
    this.app.resource({ name: "my-resource", actions: {} });
  }

  async install() {}
  async afterEnable() {}
  async afterDisable() {}
  async remove() {}
}

export default PluginMyNameServer;
```

### Client (`src/client/index.tsx`):

```typescript
import { Plugin } from "@nocobase/client";

export class PluginMyNameClient extends Plugin {
  async load() {
    // Register UI components, routes, schema initializers here
  }
}

export default PluginMyNameClient;
```

---

## Build Output Verification

After successful build, `dist/` should contain:

```
dist/
├── client/
│   └── index.js              # Rspack bundle (~5-10KB)
├── server/
│   ├── index.js              # Server entry
│   ├── plugin.js             # Plugin class
│   └── <other-modules>.js    # Additional server modules
├── locale/
│   ├── en-US.json
│   └── zh-CN.json
├── index.js                  # Main entry (re-export of server)
└── externalVersion.js        # Tracks bundled dependency versions
```

---

## Common Build Errors & Solutions

| Error                                           | Cause                                           | Fix                                                                 |
| ----------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| `TS2307: Cannot find module '@nocobase/server'` | Core packages not built (no `lib/` folder)      | Use `--no-dts` flag                                                 |
| `TS2339: Property 'X' does not exist`           | Wrong API usage or missing type declarations    | Fix source code or use `--no-dts`                                   |
| `The build tool will package all dependencies`  | Warning about `devDependencies`                 | Move runtime deps to `dependencies`                                 |
| `yarn install` doesn't find new plugin          | Plugin path doesn't match workspace pattern     | Ensure plugin is under `packages/*/*/*`                             |
| Declaration build failure only                  | `tsc` can't resolve peer deps                   | Run `yarn nocobase build` for ALL packages first, or use `--no-dts` |
| `Cannot find module './plugin'` at runtime      | `dist/` missing or stale                        | Re-run build before installing                                      |
| `resource does not exist` on plugin load        | Collection not registered or plugin not enabled | Check `yarn pm enable` and restart app                              |
| Plugin loads but UI doesn't appear              | Client bundle not built or wrong export         | Verify `dist/client/index.js` exists and exports Plugin class       |
| `SyntaxError` in dist/server                    | NCC bundled incompatible ESM module             | Add problematic package to `externals` in build config              |

---

## Packaging for Distribution

```bash
cd packages/plugins/@nocobase/plugin-<name>
npm pack
# Creates @nocobase-plugin-<name>-1.0.0.tgz
```

---

## Installing in Production

### From .tgz file (recommended for custom plugins):

```bash
# 1. Copy .tgz to the server/container
# 2. Install via NocoBase plugin manager
yarn pm add /path/to/@nocobase-plugin-<name>-1.0.0.tgz

# 3. Enable the plugin
yarn pm enable @nocobase/plugin-<name>

# 4. Restart the app
yarn start
```

### From npm registry:

```bash
yarn pm add @nocobase/plugin-<name>
yarn pm enable @nocobase/plugin-<name>
```

---

## Docker Container Workflow

When NocoBase runs inside Docker:

```bash
# 1. Build .tgz on host machine
cd packages/plugins/@nocobase/plugin-<name>
npm pack
# → @nocobase-plugin-<name>-1.0.0.tgz

# 2. Copy into container
docker cp @nocobase-plugin-<name>-1.0.0.tgz <container_name>:/tmp/

# 3. Install inside container
docker exec -it <container_name> bash
cd /app
yarn pm add /tmp/@nocobase-plugin-<name>-1.0.0.tgz
yarn pm enable @nocobase/plugin-<name>

# 4. Restart container (or just the app process)
docker restart <container_name>
```

### Updating an existing plugin in Docker:

```bash
# Re-build, re-pack, re-copy, then:
docker exec -it <container_name> bash -c "
  cd /app &&
  yarn pm remove @nocobase/plugin-<name> &&
  yarn pm add /tmp/@nocobase-plugin-<name>-1.0.0.tgz &&
  yarn pm enable @nocobase/plugin-<name>
"
docker restart <container_name>
```

### Check container logs after install:

```bash
docker logs <container_name> --tail 100 -f
# Look for: "Plugin <name> loaded" or error stack traces
```
