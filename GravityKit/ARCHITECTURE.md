# GravityKit Architecture

GravityKit is a CLI-based AI agent toolkit. It packages agents, workflows,
skills, project memory, IDE adapters, and local MCP setup scripts, then
materializes the right subset into a user project.

This document describes the architecture implemented by the current
`GravityKit/` package and its NPX distribution. For command examples intended
for end users, see the root `README.md`.

Current Python package version: `3.13.4`

## System Overview

GravityKit has six main layers:

| Layer | Responsibility |
| --- | --- |
| Python CLI | Canonical `gkt` / `gravitykit` command surface. Handles init, group install, validation, index generation, MCP scoping, brain, journal, graph, watch, and skill management. |
| Runtime templates | Canonical `.agent/` content: agents, workflows, skills, brain templates, and runtime indexes. |
| Catalog data | Defines group membership and distribution/catalog metadata. `skill_groups.json` is the group install source of truth. |
| IDE adapters | Thin IDE-specific instruction/rule templates for Cursor, Windsurf, Cline, Kilo Code, GitHub Copilot, and Kiro. |
| MCP and indexes | Project-local code graph, FAISS code search, document reader, brain manager, and skill router servers. |
| NPX package | Node-first installer that bundles generated assets and delegates graph/MCP setup to the installed Python scripts. |

The central boundary is:

```text
Package source templates
  -> gkt init / npx gkt init
  -> Generated project-local agent, IDE, and MCP files
```

GravityKit source files live in the package. `gkt init` copies or maps those
files into the current working project. Runtime state such as `.gkt/state.json`,
`.code-graph-index/`, `.mcp.json`, and workflow checkpoints belongs to the user
project, not to the package source.

## Repository Layout

```text
GravityKit/
  cli.py                         # Canonical Python CLI implementation
  VERSION                        # Python package version
  ARCHITECTURE.md                # This document
  skills_index.json              # Generated flat index of installable skills
  data/
    skill_groups.json            # Canonical group -> skills/workflows mapping
    catalog.json                 # Generated catalog surface, not init source of truth
    bundles.json                 # Generated bundle metadata
    aliases.json                 # Generated skill alias metadata
    workflows.json               # Higher-level workflow metadata for catalog surfaces
  .agent/
    agents/                      # Universal specialist agent definitions
    workflows/                   # Slash-command workflow files
    skills/                      # Installable skills, one folder per skill
    brain/                       # Brain templates and runtime indexes
  ide-adapters/
    cursor/                      # Cursor .mdc rule files
    windsurf/                    # Windsurf rule files
    cline/                       # Cline rule files
    kilocode/                    # Kilo Code rule files
    copilot/                     # GitHub Copilot instruction files
    kiro/                        # Kiro steering, hook, skill-priority, and specs templates
  scripts/
    validate_skills.py           # Python skill validation
    validate-skills.js           # JS skill validation helper
    skills_manager.py            # enable/disable/list/search/count
    generate_index.py            # Generates skills_index.json
    generate_adapters.py         # Adapter generation helper
    build-catalog.js             # Generates catalog, bundle, alias surfaces
  lib/
    skill-utils.js               # Shared JS utility code for catalog generation

packages/npx/
  bin/cli.js                     # NPX CLI entry point
  lib/
    constants.js                 # NPX version, repo, and target mappings
    commands.js                  # version, doctor, list, groups, mcp wrappers
    init.js                      # NPX init implementation
    download.js                  # GitHub release tarball fallback
  assets/                        # Built copy of GravityKit templates for NPX
  scripts/build-assets.js        # Syncs GravityKit source/templates into assets/
```

## Current Snapshot

These counts are derived from the current `GravityKit/` folder.

| Item | Count |
| --- | ---: |
| Python package version | `3.13.4` |
| NPX package version | `3.13.4` |
| Skill groups excluding `_default` | 23 |
| Default skills | 16 |
| Installable skill folders in `.agent/skills/` | 340 |
| Entries in `skills_index.json` | 340 |
| Workflow files in `.agent/workflows/` | 51 |
| Agent files in `.agent/agents/` | 18 |
| IDE adapter families | 6 |

Current groups:

```text
general-dev, n8n-dev, nocobase-dev, general-doc, research,
cloud-deploy, security-audit, security-pentest, seo-marketing,
ai-agent, saas-crm, saas-comms, saas-project, saas-marketing,
startup-biz, api-graphql, claude-code, context-data-rag, database,
observability-report, uipath, gen-doc, finance
```

The validation gate currently treats missing group skill references as
warnings. `gkt init` also warns and copies only skill folders that exist and
contain `SKILL.md`.

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

Only folders with `SKILL.md` are installable skills. The generated
`skills_index.json` is a flat search/catalog index built directly from these
folders by `scripts/generate_index.py`.

Current optional-folder usage:

| Optional folder | Skill folders using it |
| --- | ---: |
| `references/` | 53 |
| `scripts/` | 64 |
| `assets/` | 5 |
| `evals/` | 1 |

### Agents

Agents are universal role definitions in `.agent/agents/*.md`. Each file
defines a specialist role and operating contract. Agents are copied as a full
set for Antigravity-style installs and Kiro installs because workflows can hand
off across roles regardless of group.

Current agents:

```text
architect, backend-dev, code-reviewer, designer, devops, frontend-dev,
knowledge-guide, leader, meta-thinker, mobile-dev, planner, qa-engineer,
quickstart, release-manager, researcher, security-engineer, seo-specialist,
tech-writer
```

Agents are also represented in `.agent/brain/agent_index.json`.

### Workflows

Workflows are slash-command instructions in `.agent/workflows/wf-<name>.md`.
Each workflow uses YAML frontmatter with a `description` field and a body that
defines phases, checkpoints, outputs, and handoffs.

The `wf-` prefix is intentional. It keeps workflow discovery predictable in IDE
slash-command menus.

### Brain

The brain is the persistent project memory layer installed into `.agent/brain/`
or `.kiro/brain/`.

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

| File | Responsibility |
| --- | --- |
| `project_context.json` | Project metadata, conventions, decisions, sprint state, and requirement-analysis settings. |
| `lifecycle.md` | Session lifecycle: init, optional requirement analysis, planning, work, quality gate, checkpoint, handoff. |
| `default_skills.md` | Always-installed skill reference and usage rules. |
| `skills_manifest.json` | Lightweight skill map for lazy loading. |
| `agent_index.json` | Agent registry and handoff semantics. |
| `platform_notes.md` | Cross-platform shell, path, and encoding guidance. |
| `workflow_sessions/` | Per-workflow checkpoint files for resume across sessions. |

## Catalog And Group Data

`GravityKit/data/skill_groups.json` is the canonical file for group installs.

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

The special `_default` group is merged into every group. This keeps memory,
planning, debugging, git, document reading, skill routing, code graph, and
platform compatibility skills available everywhere.

Default skills:

```text
brain-manager, journal-manager, context-manager, concise-planning,
writing-plans, git-manager, commit, powershell-windows, bash-linux,
debugger, clean-code, codebase-navigator, code-graph-index,
error-handling-patterns, document-reader, skill-router
```

The other files under `data/` are generated discovery/catalog surfaces:

| File | Role |
| --- | --- |
| `catalog.json` | Large skill catalog surface with categories, tags, triggers, and paths. |
| `bundles.json` | Generated bundle groupings such as `core-dev`, `security-core`, and `ops-core`. |
| `aliases.json` | Generated alternate names for skill lookup. |
| `workflows.json` | Higher-level workflow catalog entries, separate from `.agent/workflows/*.md`. |

Do not treat `data/catalog.json` as the source of truth for installed skills.
It is a generated catalog surface. For install behavior, use
`skill_groups.json` plus actual folders under `.agent/skills/`.

## Python CLI

Python entry points are defined in `pyproject.toml`:

```toml
[project.scripts]
gkt = "GravityKit.cli:main"
gravitykit = "GravityKit.cli:main"
```

Core commands:

| Command | Implementation responsibility |
| --- | --- |
| `init` | Materialize toolkit/adapters into a project. Supports target detection, groups, and `--minimal`. |
| `load` | Scan a project and populate generated instruction files. Currently supports Kiro foundation steering docs. |
| `groups` | Read and display `data/skill_groups.json` with availability counts. |
| `list` | Read packaged workflow files and print slash-command descriptions. |
| `doctor` | Check Python, Node.js, Git, npm, and local `.agent/`. |
| `update` | Update from Git checkout or pip Git source. |
| `version` | Print `GravityKit/VERSION`. |
| `brain` | Dispatch to `brain-manager/scripts/brain.py`. |
| `journal` | Dispatch to `journal-manager/scripts/journal.py`. |
| `graph` | Dispatch directly to `code-graph-index/scripts/setup_mcp.py`. |
| `mcp` | Scope-aware MCP setup wrapper around `setup_mcp.py`. |
| `watch` | Dispatch to `code-graph-index/scripts/watcher.py`. |
| `skills list/enable/disable/search/count` | Dispatch to `scripts/skills_manager.py`. |
| `validate` | Dispatch to `scripts/validate_skills.py`. |
| `generate-index` | Dispatch to `scripts/generate_index.py`. |

Valid Python `gkt init` targets:

```text
all, antigravity, cursor, windsurf, cline, kilocode, copilot, kiro, codex
```

`codex` is an MCP-only init target. It copies no skill files, but it is recorded
in `.gkt/state.json` so `gkt mcp` can configure Codex.

## Install Flow

Primary command:

```bash
gkt init [target] [--group <name>] [--minimal]
```

`target` can be an IDE target or a group shortcut:

| Target type | Examples | Meaning |
| --- | --- | --- |
| IDE target | `antigravity`, `kiro`, `cursor`, `windsurf`, `cline`, `kilocode`, `copilot`, `codex`, `all` | Install for one or more tool surfaces. |
| Group name | `general-dev`, `uipath`, `finance` | Shortcut for `antigravity --group <name>`. |

High-level algorithm:

1. Load `data/skill_groups.json`.
2. Decide whether `target` is an IDE target or a group shortcut.
3. Validate group name if one was provided.
4. Resolve the target IDE list.
5. Copy or map templates into the current project.
6. Register MCP-only targets such as `codex` without copying templates.
7. Write `.gkt/state.json` with initialized target scope.
8. Update `.gitignore` for generated local folders/files.
9. Add local MCP priority rules to supported instruction files.
10. Print installed workflow suggestions.

### Full And Selective Installs

For full Antigravity-style install:

```text
GravityKit/.agent/ -> <project>/.agent/
```

For group install, `copy_group_selective()`:

1. Removes the existing target `.agent/`.
2. Copies `brain/`.
3. Copies group skills plus `_default` skills unless `--minimal` is used.
4. Copies group workflows.
5. Copies all agents.
6. Warns about configured skills or workflows that are missing.

Agents are universal and are not filtered by group.

### Minimal Mode

Python `gkt init --minimal` skips copying the `skills/` folder to reduce local
project size. It still copies brain, workflows, agents, and adapter files as
applicable.

When minimal mode is used, local instruction files receive an additional note
that agents must use the `skill-router` MCP server to resolve globally installed
skills instead of reading local `.agent/skills`.

NPX `gkt init` does not currently expose a `--minimal` option.

### Kiro

`install_kiro()` maps the canonical `.agent/` model into Kiro's structure:

```text
.agent/skills/                 -> .kiro/skills/
ide-adapters/kiro/steering/    -> .kiro/steering/
ide-adapters/kiro/hooks/       -> .kiro/hooks/
.agent/workflows/*.md          -> .kiro/specs/
.agent/agents/                 -> .kiro/agents/
.agent/brain/                  -> .kiro/brain/
```

For group install, only group workflows and group plus default skills are
copied. Steering, hooks, agents, and brain are common runtime support.

Kiro steering files under `.kiro/steering/` use `inclusion: always` for
baseline context. GravityKit includes `gravitykit-skills.md` there so Kiro
agents are instructed to search and prioritize installed workspace skills in
`.kiro/skills/` before using generic model knowledge. This complements Kiro's
native Agent Skills behavior, where workspace skills are discovered from
`.kiro/skills/` and progressively loaded on demand.

GravityKit also populates Kiro's foundation steering files:

```text
.kiro/steering/product.md
.kiro/steering/tech.md
.kiro/steering/structure.md
```

`gkt init kiro` runs the same loader after copying templates, but only replaces
files that are missing or still contain placeholder comments. Users can refresh
them later with:

```bash
gkt load --target kiro
gkt load --target kiro --force
```

The loader is deterministic: it scans local files such as `README.md`,
`pyproject.toml`, `package.json`, top-level directories, language extensions,
framework dependencies, and deployment/config files. It does not call an LLM,
so the generated content should be treated as a baseline for the user or Kiro
agent to refine.

### Adapter IDEs

Adapter IDEs receive IDE-specific rule or instruction files. Python `gkt init`
also installs `.agent/` for a single adapter target when the adapter references
`.agent/skills/` and `.agent/` is not already present.

| Target | Source | Project output |
| --- | --- | --- |
| `cursor` | `ide-adapters/cursor/` | `.cursor/rules/` |
| `windsurf` | `ide-adapters/windsurf/` | `.windsurf/rules/` |
| `cline` | `ide-adapters/cline/` | `.clinerules/` |
| `kilocode` | `ide-adapters/kilocode/` | `.kilocode/rules/` |
| `copilot` | `ide-adapters/copilot/` | `.github/instructions/` |

Adapter rule files are role-level instructions and are not filtered by group.
The `.agent/` payload installed alongside them can be group-filtered.

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

Target-to-MCP mapping:

| Init target | MCP target written to state |
| --- | --- |
| `antigravity` | `antigravity` |
| `kiro` | `kiro` |
| `cursor` | `cursor` |
| `windsurf` | `windsurf` |
| `cline` | `antigravity` |
| `kilocode` | `antigravity` |
| `copilot` | `antigravity` |
| `codex` | `codex` |

Cline, Kilo Code, and Copilot do not have native MCP config writers in the
current setup script, so they use the Antigravity-style project `.mcp.json`.

### Local Instruction Files

After install, `setup_agent_instructions()` adds a local MCP priority rule to
the appropriate instruction file when possible:

| Target | Instruction file |
| --- | --- |
| `antigravity` | `.agent/brain/conventions.md` |
| `cursor` | `.cursorrules` |
| `windsurf` | `.windsurfrules` |
| `cline` | `.clinerules` |
| `kilocode` | `.kilocoderules` |
| `copilot` | `.github/copilot-instructions.md` |
| `kiro` | `.kiro/steering/brain.md` |

It also removes legacy top-level files named `Antigravity.md`, `Codex.md`, and
`Kiro.md` if they exist.

## MCP And Code Indexing

The `code-graph-index` skill provides the setup script used by:

```bash
gkt graph
gkt mcp
gkt watch
```

Important runtime artifacts:

```text
.code-graph-index/       # Structural graph and FAISS artifacts
.mcp.json                # Project-local MCP config for Antigravity/Claude style clients
.gkt/state.json          # Init scope consumed by gkt mcp
.codex/config.toml       # Project-local Codex MCP config when codex is targeted
```

MCP servers owned by GravityKit:

| Server | Scope | Purpose |
| --- | --- | --- |
| `document-reader` | Global/universal | Reads PDF, DOCX, XLSX, HTML, CSV, JSON, XML, images, audio, and other supported formats. |
| `code-graph` | Project-local | Structural graph over files, imports, symbols, callers, and dependencies. |
| `faiss-code-index` | Project-local | Semantic code chunk search using `.code-graph-index/faiss-index/`. |
| `brain-manager` | Project-local | Reads and writes project context, decisions, conventions, and workflow checkpoints. |
| `skill-router` | Project-local | Routes tasks to relevant skills, workflows, groups, and active workflow sessions. |

Supported MCP config targets in `setup_mcp.py`:

| IDE/CLI | Config files |
| --- | --- |
| `antigravity` | `~/.gemini/antigravity/mcp_config.json` for universal servers plus `<project>/.mcp.json` for project-local servers |
| `claude` | `<project>/.mcp.json` |
| `kiro` | `<project>/.kiro/settings/mcp.json` |
| `cursor` | `<project>/.cursor/mcp.json` |
| `windsurf` | `<project>/.windsurf/mcp.json` |
| `codex` | `~/.codex/config.toml` for universal servers plus `<project>/.codex/config.toml` for project-local servers |

`setup_mcp.py` merges GravityKit-owned server entries into existing config
files and preserves unrelated third-party MCP servers.

`gkt mcp` behavior:

1. If the user passed `--all`, `--auto`, or `--ides`, forward that explicit
   scope.
2. Otherwise read `.gkt/state.json`.
3. If state contains `mcp_ides`, pass those to `setup_mcp.py`.
4. If state is missing, fall back to `--all`.
5. Ensure `--ensure-model` is included.

`gkt graph` is a thinner wrapper that forwards arguments directly to
`setup_mcp.py`. Use it for explicit graph/index rebuild flags such as
`--incremental`, `--rebuild`, `--skip-graph`, or `--skip-faiss`.

`setup_mcp.py` can auto-install missing Python dependencies for graph, FAISS,
and document reading (`numpy`, `faiss-cpu`, `onnxruntime`, `pypdf`,
`python-docx`, `openpyxl`).

## Skill Router

`skill-router` is registered as a project-local MCP server by `gkt mcp`. It
loads `skills_index.json`, `skill_groups.json`, workflow files, and active
workflow sessions to guide runtime skill usage.

Tools exposed by the current server:

| Tool | Purpose |
| --- | --- |
| `route_task` | Score a natural-language task against workflows and skills. |
| `get_skill_info` | Return details and group memberships for one skill. |
| `get_group_skills` | Return configured skills and workflows for one group. |
| `list_groups` | List available groups and counts. |
| `list_active_sessions` | Find resumable workflow checkpoints. |
| `search_skills` | Keyword search over skill names and descriptions. |

## Agent Runtime Data Flow

```text
User request
  -> AI IDE loads local instructions
  -> Workflow command /wf-* is selected or implied
  -> lifecycle.md defines session phases
  -> brain/project_context.json and workflow_sessions are checked
  -> agent role is selected or implied
  -> skill-router or skills_manifest.json identifies relevant skills
  -> relevant SKILL.md files are loaded on demand
  -> MCP tools provide code, document, skill, and brain access
  -> workflow phase output is produced
  -> brain/journal/checkpoint files are updated when required
```

The design separates responsibilities:

| Concern | Owner |
| --- | --- |
| What knowledge exists | Skills |
| Who performs the work | Agents |
| How the work proceeds | Workflows |
| What must be remembered | Brain |
| How IDEs receive instructions | Adapters |
| How code and docs are queried | MCP servers |
| How groups are selected | `skill_groups.json` and `skill-router` |

## NPX CLI

The NPX package lives in `packages/npx`.

Current package:

```text
name: gkt-node
version: 3.10.5
bin: gkt, gkt-node
node: >=16.0.0
```

Build flow:

```text
GravityKit source templates
  -> packages/npx/scripts/build-assets.js
  -> packages/npx/assets/
  -> published gkt-node package
```

Runtime strategy:

1. Prefer bundled assets from `packages/npx/assets/`.
2. Fall back to downloading the tagged GitHub release tarball if bundled assets
   are missing.
3. Copy templates into the current project using Node.js built-ins.

NPX command surface:

| Command | Behavior |
| --- | --- |
| `npx gkt init [target] [--group <name>]` | Install bundled/downloaded assets. |
| `npx gkt mcp` / `npx gkt graph` | Run installed `.agent/skills/code-graph-index/scripts/setup_mcp.py --all --ensure-model`. |
| `npx gkt list` | List workflows from the current project's `.agent/workflows/`. |
| `npx gkt groups` | Fetch group data from the GitHub tag matching the NPX version. |
| `npx gkt doctor` | Check Python, Node.js, Git, npm, and local `.agent/`. |
| `npx gkt version` | Print the NPX package version. |

Important NPX differences from Python CLI:

| Area | Python CLI | NPX CLI |
| --- | --- | --- |
| Canonical command surface | Complete | Installer-oriented subset |
| `codex` init target | Supported | Not currently supported |
| `--minimal` | Supported | Not currently supported |
| `load` command | Supports Kiro steering generation | Not currently supported |
| MCP scoping | Reads `.gkt/state.json` unless explicitly overridden | Runs setup with `--all --ensure-model` |
| Install behavior | Replaces target dirs for many paths | Merges/copies while skipping existing files |

The Python CLI remains canonical for full target coverage and state-aware MCP
scoping.

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
  .code-graph-index/
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
    settings/
      mcp.json
  .gkt/
    state.json
```

### Adapter project

```text
project/
  .agent/                       # Installed when adapter needs skill references
  .cursor/rules/                # Or .windsurf/rules/, .clinerules/, etc.
  .gkt/state.json
```

### Codex project

```text
project/
  .gkt/
    state.json                  # Written by gkt init codex
  .codex/
    config.toml                 # Written by gkt mcp
```

Codex also receives universal MCP servers in `~/.codex/config.toml`.

## Validation And Generated Data

Skill validation:

```bash
python GravityKit/scripts/validate_skills.py
```

Checks:

1. `SKILL.md` exists.
2. YAML frontmatter is present and parseable.
3. Required fields `name` and `description` exist.
4. `risk` uses a known value.
5. A "When to Use" section is present.
6. Offensive skills include the required security disclaimer.
7. `skill_groups.json` references existing skills and workflows.

Only validation errors fail strict mode. Missing group references are warnings.

Skill index generation:

```bash
python GravityKit/scripts/generate_index.py
```

This regenerates `GravityKit/skills_index.json` from actual skill folders.

Catalog generation:

```bash
node GravityKit/scripts/build-catalog.js
```

This regenerates `data/catalog.json`, `data/bundles.json`, `data/aliases.json`,
and `CATALOG.md` from the current skill tree.

NPX asset build:

```bash
node packages/npx/scripts/build-assets.js
```

This rebuilds `packages/npx/assets/` from GravityKit templates, group data, and
IDE adapters.

## Extension Points

### Add a skill

1. Create `GravityKit/.agent/skills/<skill-name>/SKILL.md`.
2. Add optional `references/`, `scripts/`, `assets/`, or `evals/`.
3. Add the skill to one or more groups in `GravityKit/data/skill_groups.json`
   if it should be included by group installs.
4. Run validation and regenerate `skills_index.json`.
5. Rebuild NPX assets before publishing Node package changes.
6. Regenerate catalog data if the catalog surfaces should include the skill.

### Add a workflow

1. Create `GravityKit/.agent/workflows/wf-<name>.md`.
2. Quote the `description` frontmatter value.
3. Add the workflow name to relevant group `workflows[]`.
4. Verify `gkt init <group>` shows the workflow in post-init suggestions.
5. Rebuild NPX assets before publishing Node package changes.

### Add an agent

1. Create `GravityKit/.agent/agents/<agent-name>.md`.
2. Add role, description, tools, behavior, and output contract.
3. Update `GravityKit/.agent/brain/agent_index.json`.
4. Confirm relevant workflows reference the new role consistently.

### Add an IDE adapter

1. Add templates under `GravityKit/ide-adapters/<target>/`.
2. Add target metadata in `GravityKit/cli.py`.
3. Decide whether the target needs `.agent/` copied or is MCP-only.
4. Add target mapping for MCP state if applicable.
5. Add `setup_mcp.py` writer support if the IDE has its own MCP config format.
6. Add NPX support separately if the Node installer should support it.

### Add an MCP server

1. Place server code under an appropriate skill `scripts/` directory.
2. Add the server name to the owned server set in `setup_mcp.py`.
3. Decide whether the server is global/universal or project-local.
4. Add entries to `build_server_entries()`.
5. Update per-IDE writers if the config shape differs.
6. Preserve unrelated MCP server entries during reconciliation.

## Design Decisions

| Decision | Rationale |
| --- | --- |
| Python CLI is canonical | It has the complete command surface, direct package access, `codex`, `--minimal`, and state-aware MCP scoping. |
| Skills are folders, not single files | Keeps guidance, references, scripts, assets, and evals together. |
| `SKILL.md` is required | Keeps validation and install filtering simple. |
| Workflows use the `wf-` prefix | Slash-command discovery is easier and workflow files are visually distinct. |
| `_default` is auto-merged | Core memory, planning, debugging, git, code graph, document, skill routing, and platform skills stay available everywhere. |
| Brain is always copied for `.agent/` and `.kiro/` | Session continuity and project context are runtime requirements. |
| Agents are copied as a complete set | Specialist roles are lightweight and workflows can hand off across groups. |
| Adapter files are universal | IDE role rules are generic; group selection applies to the `.agent/` payload. |
| Missing group skill refs are warnings | Group configs can be broader than the currently packaged skill folders; init copies available skills and reports gaps. |
| `gkt mcp` reads `.gkt/state.json` | MCP setup should match the IDEs or CLIs initialized by the user. |
| Universal and project-local MCP servers are split | Stateless servers can live in global config; project-specific servers must point at the current workspace. |
| Codex is MCP-only at init time | Codex needs MCP config, not copied rule files. |
| NPX bundles generated assets | Node users get a low-friction installer without requiring a Python package install first. |
