# gkt-node — GravityKit CLI (npx)

> The AI-Native Software House in a Box — install via `npx`, no Python required.

## Quick Start

```bash
# Install all skills for all supported IDEs
npx gkt-node init

# Install for a specific IDE
npx gkt-node init antigravity
npx gkt-node init cursor
npx gkt-node init windsurf
npx gkt-node init cline
npx gkt-node init kilocode
npx gkt-node init copilot
npx gkt-node init kiro
```
> **Tip:** After global install (`npm i -g gkt-node`), you can use either `gkt` or `gkt-node` as the command.

### Step 2: Enable Semantic Code Graph (Optional but Recommended)

GravityKit includes a powerful offline-first semantic search engine. After initializing the skills, build the index and register the MCP servers (requires Python 3.9+):

```bash
npx gkt mcp
```

This will:
1. Auto-install required dependencies (`faiss-cpu`, `onnxruntime`) if missing.
2. Extract the bundled ONNX model (`all-MiniLM-L6-v2`) locally — zero network needed.
3. Build a structural code graph and a FAISS semantic index of your codebase.
4. Auto-configure the `code-graph` and `faiss-code-index` MCP servers for your IDE.

## Commands

| Command | Description |
|---------|-------------|
| `npx gkt-node init [target]` | Install GravityKit skills & workflows into current directory |
| `npx gkt-node init [target] --group <name>` | Install a specific skill group |
| `npx gkt-node mcp` | Setup Semantic Code Graph & MCP (aliases: `graph`) |
| `npx gkt-node groups` | List available skill groups |
| `npx gkt-node list` | List installed AI Agents (requires `gkt-node init` first) |
| `npx gkt-node doctor` | Check environment health (Python, Node, Git, npm) |
| `npx gkt-node version` | Show current version |
| `npx gkt-node help` | Show help message |

## Init Targets

### By IDE

| Target | Output Directory | IDE |
|--------|-----------------|-----|
| `all` (default) | All below | All supported IDEs |
| `antigravity` | `.agent/` | Antigravity (Gemini) |
| `cursor` | `.cursor/rules/` | Cursor |
| `windsurf` | `.windsurf/rules/` | Windsurf |
| `cline` | `.clinerules/` | Cline |
| `kilocode` | `.kilocode/rules/` | Kilo Code |
| `copilot` | `.github/instructions/` | GitHub Copilot |
| `kiro` | `.kiro/` | Kiro (skills, hooks, steering, specs) |

### By Skill Group

Instead of installing all 500+ skills, pick a focused group:

```bash
npx gkt-node init general-dev           # General development
npx gkt-node init n8n-dev               # n8n workflow development
npx gkt-node init nocobase-dev          # NocoBase plugin development
npx gkt-node init security-audit        # Security & pentesting
npx gkt-node init seo-marketing         # SEO & content marketing

# Combine IDE + group
npx gkt-node init antigravity --group n8n-dev
npx gkt-node init all --group general-dev
```

Run `npx gkt-node groups` to see all available groups with skill/workflow counts.

## How It Works

1. **Bundled assets** — skills, workflows, and IDE configs are included in the package (offline-capable)
2. **Fallback download** — if bundled assets are missing, downloads from GitHub automatically
3. **Copies** them into the appropriate directories in your project

No external npm dependencies — uses only Node.js built-ins.

## Requirements

- **Node.js** ≥ 16

## Also Available via pip

```bash
pip install gkt
gkt init
```

## License

MIT
