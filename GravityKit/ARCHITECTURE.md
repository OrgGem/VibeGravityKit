# GravityKit Architecture

GravityKit is a CLI-based AI agent toolkit. It packages skills, agents, workflows, project memory, and IDE adapters, then installs the right subset into a user project.

This document explains the internal structure and data flow. For user-facing commands and examples, see the root `README.md`.

Current package version: `3.12.7`

## System Overview

GravityKit has five main layers:

| Layer | Responsibility |
| --- | --- |
| CLI | Entry points for install, validation, skill management, brain/journal scripts, code graph, and MCP setup. |
| Catalog data | Defines which skills and workflows belong to each group. |
| Toolkit source | Canonical `.agent/` content: agents, workflows, skills, brain templates. |
| IDE adapters | Thin rule/instruction files that adapt the toolkit to each AI IDE. |
| Project install | Generated `.agent/`, `.kiro/`, `.cursor/`, `.windsurf/`, `.clinerules/`, `.kilocode/`, `.github/`, `.gkt/`, and MCP files inside the user's repository. |

The important architectural boundary is that GravityKit stores source templates inside the Python/NPX package, while `gkt init` materializes those templates into the current working project.

## Repository Layout

```text
GravityKit/
  cli.py                         # Python CLI entry point: gkt / gravitykit
  VERSION                        # Python package version
  ARCHITECTURE.md                # This document
  skills_index.json              # Generated skill index
  data/
    skill_groups.json            # Canonical group -> skills/workflows mapping
    catalog.json                 # Catalog metadata
    bundles.json                 # Bundle metadata
    aliases.json                 # Alias metadata
    workflows.json               # Workflow metadata used by catalog surfaces
  .agent/
    agents/                      # 18 specialist agent definitions
    workflows/                   # 51 wf-* workflow files
    skills/                      # 244 skill folders with SKILL.md
    brain/                       # Brain templates and indexes
  ide-adapters/
    cursor/                      # Cursor rules
    windsurf/                    # Windsurf rules
    cline/                       # Cline rules
    kilocode/                    # Kilo Code rules
    copilot/                     # GitHub Copilot instructions
    kiro/                        # Kiro steering, hooks, specs templates
  scripts/
    validate_skills.py           # SKILL.md validation
    skills_manager.py            # enable/disable/list/search/count
    generate_index.py            # skills_index.json generator
    generate_adapters.py         # adapter generation helper
    build-catalog.js             # catalog builder
  lib/
    skill-utils.js               # shared JS utility code

packages/npx/
  bin/cli.js                     # NPX CLI entry point
  lib/                           # Node command implementation
  assets/                        # Built copy of GravityKit source/templates
  scripts/build-assets.js        # Syncs Python package assets into NPX package
```

## Runtime Concepts

### Skills

A skill is a folder under `.agent/skills/<skill-name>/`.

Required:

```text
SKILL.md
```

Optional:

```text
references/     # Deep reference docs loaded on demand
scripts/        # Executable helpers used by agents or CLI wrappers
assets/         # Templates, examples, fixtures
evals/          # Evaluation material
```

Only folders with `SKILL.md` are treated as installable skills. Skills are indexed in `brain/skills_manifest.json` for lazy loading and in `skills_index.json` for package-level search/catalog behavior.

### Agents

Agents are role definitions in `.agent/agents/*.md`.

Each file contains frontmatter such as:

```yaml
name: architect
description: System architecture, API design, database modeling
tools: ...
```

The body defines behavior, operating rules, output format, and which skills to use. Agents are also represented in `brain/agent_index.json` so workflows and handoff protocols can refer to them consistently.

Current agent count: 18.

### Workflows

Workflows are slash-command instructions in `.agent/workflows/wf-<name>.md`.

Each workflow has:

```yaml
description: "Short YAML-safe description"
```

The body defines phases, checkpoints, expected outputs, and specialist handoffs. The `wf-` prefix is intentional: it makes workflow discovery predictable in IDE slash-command menus.

Current workflow count: 51.

### Brain

The brain is the persistent project memory layer installed into `.agent/brain/` or `.kiro/brain/`.

```text
brain/
  agent_index.json
  default_skills.md
  lifecycle.md
  platform_notes.md
  project_context.json
  skills_manifest.json
  workflow_sessions/
```

Responsibilities:

| File | Responsibility |
| --- | --- |
| `project_context.json` | Project metadata, conventions, decisions, sprint state, requirement-analysis settings. |
| `lifecycle.md` | Session lifecycle: init, optional requirement analysis, planning, work, quality gate, checkpoint, handoff. |
| `default_skills.md` | Always-installed skill reference and usage rules. |
| `skills_manifest.json` | Lightweight skill map for lazy loading. |
| `agent_index.json` | Agent registry and handoff semantics. |
| `platform_notes.md` | Cross-platform shell/path/encoding guidance. |
| `workflow_sessions/` | Per-workflow checkpoint files for resume across sessions. |

## Skill Groups

Groups are defined in `GravityKit/data/skill_groups.json`.

Schema:

```json
{
  "group-name": {
    "description": "Human-readable summary",
    "skills": ["skill-a", "skill-b"],
    "workflows": ["wf-planner", "wf-architect"]
  }
}
```

The special `_default` group is merged into every group. This keeps memory, planning, debugging, git, document reading, skill routing, code graph, and platform compatibility skills available everywhere.

Current counts:

| Item | Count |
| --- | ---: |
| Skill groups excluding `_default` | 23 |
| Default skills | 16 |
| Installable skills in `.agent/skills/` | 244 |
| Workflows | 51 |
| Agents | 18 |

Current groups:

```text
general-dev, n8n-dev, nocobase-dev, general-doc, research,
cloud-deploy, security-audit, security-pentest, seo-marketing,
ai-agent, saas-crm, saas-comms, saas-project, saas-marketing,
startup-biz, api-graphql, claude-code, context-data-rag, database,
observability-report, uipath, gen-doc, finance
```

## Install Flow

Primary command:

```bash
gkt init [target] [--group <name>]
```

`target` can be:

| Target type | Examples | Meaning |
| --- | --- | --- |
| IDE target | `antigravity`, `kiro`, `cursor`, `windsurf`, `cline`, `kilocode`, `copilot`, `codex`, `all` | Install for one or more tool surfaces. |
| Group name | `general-dev`, `uipath`, `finance` | Shortcut for `antigravity --group <name>`. |

High-level algorithm:

1. Load `data/skill_groups.json`.
2. Decide whether `target` is an IDE target or a group shortcut.
3. Validate group name if provided.
4. Resolve target IDE list.
5. Copy source templates into the current project.
6. Write `.gkt/state.json` with initialized target scope.
7. Update `.gitignore` for generated local folders/files.
8. Add local MCP priority rules to supported instruction files.
9. Print installed workflow suggestions.

### Antigravity / `.agent/`

For full install:

```text
GravityKit/.agent/ -> <project>/.agent/
```

For selective group install, `copy_group_selective()`:

1. Removes existing target `.agent/`.
2. Copies `brain/`.
3. Copies group skills plus `_default` skills.
4. Copies group workflows.
5. Copies all agents.

Agents are universal and are not filtered by group.

### Kiro / `.kiro/`

`install_kiro()` maps the canonical `.agent/` model into Kiro's structure:

```text
.agent/skills/                 -> .kiro/skills/
ide-adapters/kiro/steering/    -> .kiro/steering/
ide-adapters/kiro/hooks/       -> .kiro/hooks/
.agent/workflows/*.md          -> .kiro/specs/
.agent/agents/                 -> .kiro/agents/
.agent/brain/                  -> .kiro/brain/
```

For group install, only group workflows and group plus default skills are copied. Steering, hooks, agents, and brain are copied as common runtime support.

### Adapter IDEs

Adapter IDEs receive IDE-specific rule or instruction files. If the adapter references `.agent/skills/` and `.agent/` is missing, Python `gkt init` also installs `.agent/`.

| Target | Source | Project output |
| --- | --- | --- |
| `cursor` | `ide-adapters/cursor/` | `.cursor/rules/` |
| `windsurf` | `ide-adapters/windsurf/` | `.windsurf/rules/` |
| `cline` | `ide-adapters/cline/` | `.clinerules/` |
| `kilocode` | `ide-adapters/kilocode/` | `.kilocode/rules/` |
| `copilot` | `ide-adapters/copilot/` | `.github/instructions/` |

### Codex CLI

`codex` is an MCP-only target in the Python CLI. It does not copy skill files. It records scope in `.gkt/state.json` so `gkt mcp` can configure Codex-related MCP targets.

### Init State

`gkt init` writes:

```text
.gkt/state.json
```

Example:

```json
{
  "init_targets": ["cursor"],
  "group": "general-dev",
  "mcp_ides": ["cursor"]
}
```

`gkt mcp` reads this state to avoid configuring IDEs the user did not initialize.

## MCP And Code Indexing

The `code-graph-index` skill provides the setup script used by:

```bash
gkt graph
gkt mcp
gkt watch
```

Important runtime artifacts:

```text
.code-graph-index/       # structural and semantic index artifacts
.mcp.json                # local MCP config where applicable
.gkt/state.json          # init scope consumed by gkt mcp
```

MCP components exposed to agents:

| Component | Purpose |
| --- | --- |
| `code-graph` | Structural graph over files, imports, symbols, callers, and dependencies. |
| `faiss-code-index` | Semantic code chunk search using a local FAISS index. |
| `document-reader` | Reads PDF, DOCX, XLSX, HTML, CSV, JSON, XML, images, audio, and other supported formats. |
| `brain-manager` | Reads and writes project context, decisions, conventions, and workflow checkpoints. |

`gkt mcp` behavior:

1. If the user passed `--all`, `--auto`, or `--ides`, forward that explicit scope.
2. Otherwise read `.gkt/state.json`.
3. If state contains `mcp_ides`, pass those to the setup script.
4. If state is missing, fall back to `--all`.
5. Ensure `--ensure-model` is included.

## Agent Runtime Data Flow

```text
User request
  -> AI IDE loads local instructions
  -> Workflow command /wf-* is selected
  -> lifecycle.md sets session phases
  -> brain/project_context.json and workflow_sessions are checked
  -> agent role is selected or implied
  -> skills_manifest.json is searched
  -> relevant SKILL.md files are loaded on demand
  -> MCP tools provide code/document/brain access
  -> workflow phase output is produced
  -> brain/journal/checkpoint files are updated when the workflow requires it
```

The design intentionally separates:

| Concern | Owner |
| --- | --- |
| What knowledge exists | Skills |
| Who performs the work | Agents |
| How the work proceeds | Workflows |
| What must be remembered | Brain |
| How IDEs receive instructions | Adapters |
| How code and docs are queried | MCP servers |

## Python CLI

Python entry points are defined in `pyproject.toml`:

```toml
[project.scripts]
gkt = "GravityKit.cli:main"
gravitykit = "GravityKit.cli:main"
```

Core command groups:

| Command | Implementation responsibility |
| --- | --- |
| `init` | Materialize toolkit/adapters into a project. |
| `groups` | Read and display `data/skill_groups.json`. |
| `list` | Read packaged workflows and print command descriptions. |
| `doctor` | Check Python, Node.js, Git, npm, and local `.agent/`. |
| `update` | Update from Git or pip source. |
| `brain` | Dispatch to `brain-manager/scripts/brain.py`. |
| `journal` | Dispatch to `journal-manager/scripts/journal.py`. |
| `graph` | Dispatch to `code-graph-index/scripts/setup_mcp.py`. |
| `mcp` | Scope-aware MCP setup wrapper around `setup_mcp.py`. |
| `watch` | Dispatch to `code-graph-index/scripts/watcher.py`. |
| `skills ...` | Dispatch to `scripts/skills_manager.py`. |
| `validate` | Dispatch to `scripts/validate_skills.py`. |
| `generate-index` | Dispatch to `scripts/generate_index.py`. |

## NPX CLI

The NPX package lives in `packages/npx`.

Build flow:

```text
GravityKit source templates
  -> packages/npx/scripts/build-assets.js
  -> packages/npx/assets/
  -> published gkt-node package
```

Runtime strategy:

1. Prefer bundled assets from `packages/npx/assets/`.
2. Fall back to downloading release assets from GitHub if bundled assets are missing.
3. Copy templates into the current project using Node.js built-ins.

The Python CLI is the canonical implementation for the full target list and MCP scoping behavior. NPX is an installer-friendly distribution path for Node-first users.

## Generated Project Layouts

### Antigravity-style project

```text
project/
  .agent/
    agents/
    workflows/
    skills/
    brain/
  .gkt/
    state.json
  .mcp.json
```

### Kiro project

```text
project/
  .kiro/
    agents/
    brain/
    hooks/
    skills/
    specs/
    steering/
  .gkt/
    state.json
```

### Adapter project

```text
project/
  .agent/                       # installed when adapter needs skill references
  .cursor/rules/                # or .windsurf/rules/, .clinerules/, etc.
  .gkt/state.json
```

## Extension Points

### Add a skill

1. Create `GravityKit/.agent/skills/<skill-name>/SKILL.md`.
2. Add optional `references/`, `scripts/`, `assets/`, or `evals/`.
3. Add the skill to one or more groups in `GravityKit/data/skill_groups.json`.
4. Run validation and regenerate indexes.
5. Sync NPX assets before publishing Node package changes.

### Add a workflow

1. Create `GravityKit/.agent/workflows/wf-<name>.md`.
2. Quote the `description` frontmatter value.
3. Add the workflow name to relevant group `workflows[]`.
4. Verify `gkt init <group>` shows the workflow in post-init suggestions.
5. Sync NPX assets if needed.

### Add an agent

1. Create `GravityKit/.agent/agents/<agent-name>.md`.
2. Add role, description, tools, behavior, and output contract.
3. Update `GravityKit/.agent/brain/agent_index.json`.
4. Confirm all relevant workflows reference the new role consistently.

### Add an IDE adapter

1. Add templates under `GravityKit/ide-adapters/<target>/`.
2. Add target metadata in `GravityKit/cli.py`.
3. Decide whether the target needs `.agent/` copied or is MCP-only.
4. Add target mapping for MCP if applicable.
5. Add NPX support separately if the Node installer should support it.

## Design Decisions

| Decision | Rationale |
| --- | --- |
| Skills are folders, not single files | Keeps core guidance, references, scripts, assets, and evals together. |
| `SKILL.md` is required | Makes install validation simple and prevents copying incomplete skill folders. |
| Workflows use the `wf-` prefix | Slash-command discovery is easier and workflow files are visually distinct. |
| `_default` is auto-merged | Core memory, planning, debugging, git, code graph, document, and platform skills are always available. |
| Brain is always copied for `.agent/` and `.kiro/` | Session continuity and project context are runtime requirements, not optional extras. |
| Agents are copied as a complete set | Specialist roles are lightweight and workflows can hand off across groups. |
| `gkt mcp` reads `.gkt/state.json` | MCP setup should match the IDEs the user initialized. |
| YAML descriptions must be quoted | Colons and punctuation in descriptions can break frontmatter parsing. |
| Python package remains canonical | The Python CLI has the complete command surface and direct access to all packaged scripts. |
| NPX bundles generated assets | Node users get a low-friction installer without requiring a Python package install first. |
