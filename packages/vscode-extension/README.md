# RPA Skills VS Code Extension

MVP client for browsing and installing RPA skills from a registry server.

## Features

1. Skill Explorer in the Activity Bar.
2. Registry-backed group and skill tree.
3. Local scan of `.agent/skills` with installed and update states.
4. Skill details webview with metadata, tags, dependencies, and install action.
5. ZIP download and extraction into the configured workspace skill path.
6. Group install command.
7. VS Code settings for registry URL, skill path, brain path, and MCP config paths.
8. Assistant Setup dashboard for IDE target status, MCP activation, watch state, and prompt editing.
9. Install a skill into IDE-specific targets:
   - GravityKit Agent: `.agent/skills/<skill>/SKILL.md`
   - Codex: `.codex/skills/<skill>/SKILL.md`
   - Cursor: `.cursor/rules/<skill>.mdc`
   - Windsurf: `.windsurf/rules/<skill>.md`
   - Kilo Code: `.kilocode/rules/<skill>.md`
   - Cline: `.clinerules/<skill>.md`
   - Kiro: `.kiro/skills/<skill>/SKILL.md`
   - Claude: `.claude/skills/<skill>/SKILL.md`
   - GitHub Copilot: `.github/skills/<skill>/SKILL.md`
10. Activate or disable MCP servers for supported IDE config files (`.mcp.json`, `.cursor/mcp.json`, `.codex/config.toml`).
11. Watch local skill, prompt, rule, and MCP files so the extension refreshes when files change.
12. Open or create prompt files including `AGENTS.md`, `SKILL.md`, IDE rules, and MCP configs.
13. Preview HTML, Word, Excel, PowerPoint, and PDF documents as Markdown using MarkItDown.

## Settings

- `rpaSkills.registryUrl`: registry manifest URL. Default: `http://localhost:7077/manifest.json`.
- `rpaSkills.skills.path`: install directory relative to the workspace. Default: `.agent/skills`.
- `rpaSkills.brain.path`: brain directory relative to the workspace. Default: `.agent/brain`.
- `rpaSkills.mcp.configPaths`: MCP config files relative to the workspace.
- `rpaSkills.mcp.servers`: inline MCP server configuration object.
- `rpaSkills.watch.enabled`: start the local watcher automatically. Default: `true`.
- `rpaSkills.markitdown.pythonPath`: Python executable used to run `python -m markitdown`. Default: `python`.
- `rpaSkills.markitdown.timeoutMs`: conversion timeout in milliseconds. Default: `120000`.

## Commands

- `RPA Skills: Assistant Setup`: open the dashboard for IDE targets, MCP, watch, and prompt files.
- `RPA Skills: Install Skill to IDE`: install a registry skill into a selected IDE target.
- `RPA Skills: Activate MCP for IDE`: write enabled MCP server config for the selected target.
- `RPA Skills: Disable MCP for IDE`: keep MCP config installed but mark servers disabled.
- `RPA Skills: Open Prompt or Instruction`: open a prompt, rule, `SKILL.md`, or MCP config for editing.
- `RPA Skills: Preview Office File as Markdown`: convert `.docx`, `.pptx`, `.xlsx`, `.xlsm`, `.xls`, `.xlsb`, `.pdf`, `.html`, and `.htm` files with MarkItDown and show a basic Markdown preview.
- `RPA Skills: Start Watch` / `RPA Skills: Stop Watch`: control the workspace watcher.

## Development

```bash
cd packages/vscode-extension
npm install
npm run compile
```

Install MarkItDown in the Python environment used by the extension:

```bash
python -m pip install markitdown
```

Start `packages/registry-server` first if you use the default registry URL.

## Next Phases

- Rollback support using archived previous installs.
- Full dependency graph install with cycle detection.
- Search and filter inside the explorer.
- Local skill creator wizard.
- Multiple public/private registries.
