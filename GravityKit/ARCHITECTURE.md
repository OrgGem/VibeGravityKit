# GravityKit Architecture

GravityKit is a CLI-based AI agent toolkit that installs curated **skills**, **agents**, and **workflows** into project directories, enabling AI assistants (Claude Code, Kiro, Cursor, etc.) to operate as specialized domain experts.

---

## High-Level Structure

```
GravityKit/
├── cli.py                     ← Entry point: `gkt` CLI (Click)
├── data/
│   └── skill_groups.json      ← Group definitions: which skills + workflows per group
├── .agent/                    ← The toolkit source (installed into user projects)
│   ├── agents/                ← Sub-agent definitions (one .md per agent role)
│   ├── brain/                 ← Session memory, lifecycle, agent index, skill manifest
│   ├── skills/                ← 194 skill modules (each with SKILL.md + references/)
│   └── workflows/             ← 46 workflow files (slash-command invocable)
├── ide-adapters/              ← IDE-specific config templates
│   ├── kiro/                  ← Kiro IDE: steering/, hooks/, specs/
│   ├── cursor/                ← Cursor: .cursorrules
│   ├── cline/                 ← Cline: leader.md system prompt
│   ├── copilot/               ← GitHub Copilot: .github/copilot-instructions.md
│   ├── windsurf/              ← Windsurf: .windsurfrules
│   └── kilocode/              ← Kilocode: system prompts
└── lib/                       ← Shared Python utilities for CLI
```

---

## Core Concepts

### Skills
A **skill** is a folder in `.agent/skills/<skill-name>/` containing:
- `SKILL.md` — the main skill document (loaded into agent context). **Required** — folders without it are skipped during full install.
- `references/` — supplementary reference docs the agent reads on demand
- `scripts/` — executable tools the agent can invoke (Python, PowerShell, bash)
- `assets/` — templates, examples, fixtures
- `evals/` — evaluation test cases

Skills are loaded by name from `skills_manifest.json` which maps each skill to a description and size estimate.

### Agents
An **agent** is a file in `.agent/agents/<agent-name>.md` defining a specialist sub-agent:
- **Frontmatter**: `name`, `description`, `tools` (allowed tool list)
- **Body**: system prompt — role definition, skills to use, output format, rules

Agents map to the entries in `brain/agent_index.json`. The `.md` format aligns with Claude Code's native sub-agents spec so they can be invoked as isolated sub-processes.

Current agents (18):
`leader`, `quickstart`, `planner`, `architect`, `designer`, `frontend-dev`, `backend-dev`, `mobile-dev`, `devops`, `qa-engineer`, `code-reviewer`, `security-engineer`, `tech-writer`, `researcher`, `meta-thinker`, `knowledge-guide`, `release-manager`, `seo-specialist`

### Workflows
A **workflow** is a file in `.agent/workflows/wf-<name>.md`:
- **Frontmatter**: `description` (quoted string — YAML safe)
- **Body**: role prompt + phased instructions the agent follows step by step

Workflows are invoked via slash commands (`/wf-architect`, `/wf-uipath-project`, etc.). They define **how** to do work; agents define **who** does it.

### Brain
`.agent/brain/` contains cross-session memory and metadata:
- `agent_index.json` — canonical registry of all agents with roles and skills
- `skills_manifest.json` — index of all 194 skills with descriptions and sizes
- `lifecycle.md` — session phases: Init → Analysis → Planning → Work → Quality Gate → Checkpoint → Handoff
- `default_skills.md` — skills always loaded regardless of group
- `platform_notes.md` — OS-specific behavior notes
- `project_context.json` — per-project state (current sprint, decisions, conventions)

---

## Skill Groups

Groups are defined in `data/skill_groups.json`. Each group specifies:
- `skills[]` — skill names to install
- `workflows[]` — workflow files to install
- `description` — human-readable summary

The `_default` group is merged into every other group automatically.

**21 groups available:**
`general-dev`, `n8n-dev`, `nocobase-dev`, `general-doc`, `research`, `cloud-deploy`, `security-audit`, `security-pentest`, `seo-marketing`, `ai-agent`, `saas-crm`, `saas-comms`, `saas-project`, `saas-marketing`, `startup-biz`, `api-graphql`, `claude-code`, `context-data-rag`, `database`, `observability-report`, `uipath`

---

## Install Flow

```
gkt init <ide> [--group <name>] [--path <dir>]
```

### antigravity (Claude Code)
Calls `copy_group_selective()`:
1. Always copies `brain/` → `.agent/brain/`
2. Copies group skills + `_default` skills → `.agent/skills/`
3. Copies group workflows → `.agent/workflows/`
4. Copies group agents → `.agent/agents/`

### kiro (Kiro IDE)
Calls `install_kiro()`:
1. Skills → `.kiro/skills/`
2. Steering templates → `.kiro/steering/`
3. Hooks → `.kiro/hooks/`
4. Workflows → `.kiro/specs/`
5. Agents → `.kiro/agents/`

### Other IDEs
- **cursor** → writes `.cursorrules`
- **windsurf** → writes `.windsurfrules`
- **cline** → writes `.clinerules` + `leader.md`
- **copilot** → writes `.github/copilot-instructions.md`
- **kilocode** → writes system prompt file

---

## Data Flow: How an Agent Uses GravityKit

```
User request
    │
    ▼
lifecycle.md         ← defines session phases
    │
    ├─ brain/         ← load project context + past decisions
    │
    ├─ agents/        ← select specialist agent for this task
    │      └─ agent-name.md  ← system prompt + tool list
    │
    ├─ skills/        ← agent reads relevant SKILL.md files
    │      └─ skill-name/
    │             ├─ SKILL.md          ← main reference
    │             └─ references/*.md   ← deep-dive docs
    │
    └─ workflows/     ← agent follows phased workflow instructions
           └─ wf-name.md
```

---

## Adding a New Skill

1. Create `.agent/skills/<skill-name>/SKILL.md` (with `name` + `description` frontmatter)
2. Add reference docs to `.agent/skills/<skill-name>/references/` as needed
3. Add entry to `.agent/brain/skills_manifest.json`
4. Add the skill name to the relevant group(s) in `data/skill_groups.json`

## Adding a New Agent

1. Create `.agent/agents/<agent-name>.md` with frontmatter: `name`, `description`, `tools`
2. Write the system prompt body: role, skills to use, output format
3. Add entry to `.agent/brain/agent_index.json`

## Adding a New Workflow

1. Create `.agent/workflows/wf-<name>.md`
2. Frontmatter: `description: "..."` (always quote — avoid YAML colon parse errors)
3. Body: role + phased instructions
4. Add the workflow name to the relevant group(s) in `data/skill_groups.json`

---

## CLI Reference

```bash
gkt init <ide>                    # Full install (all skills + workflows)
gkt init <ide> --group <name>     # Selective install for a group
gkt init <ide> --path <dir>       # Install to specific directory
gkt list-groups                   # Show all available groups
gkt list-skills                   # Show all skills with descriptions
gkt list-agents                   # Show all agent definitions
gkt validate                      # Validate all SKILL.md frontmatter
```

**Supported IDEs:** `antigravity`, `kiro`, `cursor`, `windsurf`, `cline`, `kilocode`, `copilot`

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Skills as folders (not single files) | Enables references/, scripts/, assets/ alongside the main SKILL.md |
| Agents as .md files (not JSON) | Aligns with Claude Code native sub-agents format; human-readable |
| `_default` group auto-merged | Core skills (memory, git, debugging) always available regardless of group |
| `brain/` always copied | Session continuity — memory and lifecycle must always be present |
| YAML descriptions must be quoted | Colons in unquoted YAML values break frontmatter parsers |
| Workflows named `wf-*` | Consistent prefix makes slash-command discovery predictable |
