# RPA Skills VS Code Extension

MVP client for browsing and installing RPA skills from a registry server.

## MVP Plan

1. Skill Explorer in the Activity Bar.
2. Registry-backed group and skill tree.
3. Local scan of `.agent/skills` with installed and update states.
4. Skill details webview with metadata, tags, dependencies, and install action.
5. ZIP download and extraction into the configured workspace skill path.
6. Group install command.
7. VS Code settings for registry URL, skill path, brain path, and MCP config paths.

## Settings

- `rpaSkills.registryUrl`: registry manifest URL. Default: `http://localhost:7077/manifest.json`.
- `rpaSkills.skills.path`: install directory relative to the workspace. Default: `.agent/skills`.
- `rpaSkills.brain.path`: brain directory relative to the workspace. Default: `.agent/brain`.
- `rpaSkills.mcp.configPaths`: MCP config files relative to the workspace.
- `rpaSkills.mcp.servers`: inline MCP server configuration object.

## Development

```bash
cd packages/vscode-extension
npm install
npm run compile
```

Start `packages/registry-server` first if you use the default registry URL.

## Next Phases

- Rollback support using archived previous installs.
- Full dependency graph install with cycle detection.
- Search and filter inside the explorer.
- Local skill creator wizard.
- Multiple public/private registries.
