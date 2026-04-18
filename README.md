# 🌌 Anti-Gravity Kit

> **The AI-Native Software House in a Box.**  
> _Build enterprise-grade software with a team of 893+ AI Skills organized into 21 focused groups — each powered by 18 specialist agents, 46 workflows, and a persistent brain that remembers decisions across sessions._

---

## ⚡ Quick Start

```bash
# Install from PyPI
pip install gkt

# Init in your project (all skills)
cd /path/to/your-project
gkt init antigravity

# Or install only the skills you need
gkt init general-dev     # 30 core dev skills
gkt init uipath          # UiPath RPA automation skills
gkt init ai-agent        # 28 AI/LLM/RAG skills
```

> **Requirements:** Python 3.9+

**For development / contributing:**

```bash
git clone https://github.com/OrgGem/VibeGravityKit.git
cd VibeGravityKit
pip install -e .
```

---

## 📦 Skill Groups

Install only the skills your project needs:

```bash
gkt groups   # List all available groups
```

| Group                  | Skills | +Default | Description                                     |
| ---------------------- | ------ | -------- | ----------------------------------------------- |
| `general-dev`          | 31     | +9       | Backend, Frontend, Full-stack development       |
| `n8n-dev`              | 18     | +10      | n8n workflow automations                        |
| `nocobase-dev`         | 26     | +11      | NocoBase plugin development                     |
| `general-doc`          | 20     | +11      | Technical docs, RFC, ADR, wiki                  |
| `research`             | 18     | +12      | Deep research, market analysis                  |
| `cloud-deploy`         | 26     | +12      | Cloud, DevOps, CI/CD, Kubernetes                |
| `security-audit`       | 14     | +13      | Threat modeling, SAST, vulnerability analysis   |
| `security-pentest`     | 14     | +13      | Offensive security, red team, exploitation      |
| `seo-marketing`        | 28     | +13      | SEO, CRO, content marketing                     |
| `ai-agent`             | 28     | +13      | LLM apps, RAG, multi-agent                      |
| `saas-crm`             | 8      | +13      | HubSpot, Salesforce, Stripe connectors          |
| `saas-comms`           | 6      | +13      | Slack, Discord, WhatsApp, Gmail connectors      |
| `saas-project`         | 8      | +13      | Jira, Asana, Trello, Notion connectors          |
| `saas-marketing`       | 6      | +13      | Twitter, LinkedIn, Google Suite connectors      |
| `startup-biz`          | 26     | +13      | Market analysis, financial modeling             |
| `api-graphql`          | 24     | +12      | API design, GraphQL, REST, OpenAPI, FastAPI     |
| `claude-code`          | 22     | +11      | Claude Code skills, prompt engineering, MCP     |
| `context-data-rag`     | 28     | +12      | Context engineering, RAG, data pipelines        |
| `database`             | 26     | +11      | SQL/NoSQL, Postgres, migrations, CQRS           |
| `observability-report` | 22     | +13      | Monitoring, Grafana, Prometheus, SLO, incidents |
| `uipath`               | 6      | +13      | UiPath RPA — XAML generation, REFramework, Orchestrator, coded workflows, AI agents |
| `gen-doc` ⭐ **New**    | 4      | +13      | Document Generation — Word, Excel, PDF, and PPTX pipelines |

> **+Default**: Each group automatically includes 13 base skills for memory management, lifecycle, error handling, and cross-platform compatibility.

**Usage:**

```bash
gkt init general-dev                    # Install group (default: Antigravity IDE)
gkt init antigravity --group uipath     # UiPath skills for Claude Code
gkt init kiro --group uipath            # UiPath skills for Kiro IDE
gkt init antigravity                    # Install ALL skills
```

---

## 🛠️ CLI Commands

| Command                            | Description                                            |
| ---------------------------------- | ------------------------------------------------------ |
| `gkt init [target]`                | Install skills for an IDE or a skill group             |
| `gkt init [target] --group <name>` | Install a specific skill group for an IDE              |
| `gkt groups`                       | List all available skill groups                        |
| `gkt list`                         | List all available AI agents and their roles           |
| `gkt doctor`                       | Check environment health (Python, Node, Git, npm)      |
| `gkt update`                       | Update GravityKit to the latest version                |
| `gkt version`                      | Show current version                                   |
| `gkt brain`                        | Manage project brain — context, decisions, conventions |
| `gkt journal`                      | Knowledge journal — capture lessons, bugs, insights    |
| `gkt skills list [--all]`          | List active skills (or all including disabled)         |
| `gkt skills search <query>`        | Search skills by keyword                               |
| `gkt skills enable <name>`         | Enable a disabled skill                                |
| `gkt skills disable <name>`        | Disable a skill                                        |
| `gkt skills count`                 | Show total skill count                                 |
| `gkt validate [--strict]`          | Validate all SKILL.md files                            |
| `gkt generate-index`               | Regenerate `skills_index.json`                         |

> **Alias:** `gravitykit` works the same as `gkt`.

---

## 🌐 Multi-IDE Support

GravityKit installs into **7 AI IDEs** from a single CLI command:

| IDE                | Command                | Creates                                                           |
| ------------------ | ---------------------- | ----------------------------------------------------------------- |
| **Antigravity**    | `gkt init antigravity` | `.agent/` — agents, workflows, skills, brain                      |
| **Kiro**           | `gkt init kiro`        | `.kiro/` — skills, steering (always-loaded), hooks, specs, agents, brain |
| **Cursor**         | `gkt init cursor`      | `.cursor/rules/*.mdc`                                             |
| **Windsurf**       | `gkt init windsurf`    | `.windsurf/rules/*.md`                                            |
| **Cline**          | `gkt init cline`       | `.clinerules/*.md`                                                |
| **Kilo Code**      | `gkt init kilocode`    | `.kilocode/rules/*.md`                                            |
| **GitHub Copilot** | `gkt init copilot`     | `.github/instructions/*.instructions.md`                          |
| **All**            | `gkt init`             | All of the above                                                  |

### IDE-specific features

**Kiro** receives the full agent toolkit:
- `.kiro/steering/brain.md` — always-loaded; instructs Kiro to load brain context and check in-progress workflow sessions at every session start
- `.kiro/steering/product.md`, `structure.md`, `tech.md` — project context templates
- `.kiro/brain/` — full brain directory including `workflow_sessions/` for session continuity
- `.kiro/specs/` — workflow files for Kiro spec execution
- `.kiro/agents/` — 18 specialist agent definitions

**GitHub Copilot** receives per-role instruction files (`.github/instructions/*.instructions.md`) covering all 14 specialist roles. Each role file includes a **Session Init** block that loads brain context before starting work.

---

## 🤖 Agent Team (18 Specialists)

GravityKit ships 18 specialist agents as native sub-agent definitions (`.agent/agents/*.md`), compatible with Claude Code's sub-agent format:

| Agent               | Role                                                         |
| ------------------- | ------------------------------------------------------------ |
| `leader`            | Orchestrates the full team; delegates to specialists via sub-agents |
| `quickstart`        | Fully automated project build — no approvals needed          |
| `planner`           | Requirements analysis, PRD, task breakdown                   |
| `architect`         | System design, database schema, API spec, diagrams           |
| `designer`          | UI/UX design system, wireframes, design tokens               |
| `frontend-dev`      | React/Vue/Tailwind — components, layouts, state              |
| `backend-dev`       | Node/Python/Go — APIs, DB queries, auth                      |
| `mobile-dev`        | React Native/Expo — iOS and Android                          |
| `devops`            | Docker, CI/CD, Kubernetes, cloud deployment                  |
| `qa-engineer`       | Test cases, API tests, performance, automation               |
| `code-reviewer`     | Code quality, design patterns, security, performance         |
| `security-engineer` | Threat modeling, SAST, pen-test, incident response           |
| `tech-writer`       | Docs, API references, ADR, RFC, tutorials                    |
| `researcher`        | Market analysis, web search, competitive intelligence        |
| `meta-thinker`      | Creative advisor, brainstorming, vision expansion            |
| `knowledge-guide`   | Codebase onboarding, session handoffs, knowledge transfer    |
| `release-manager`   | Version bumps, changelog, git tagging, release notes         |
| `seo-specialist`    | Meta tags, schema markup, Core Web Vitals, sitemap           |

Agents are installed to `.agent/agents/` (antigravity) or `.kiro/agents/` (kiro) during `gkt init`.

---

## 🚀 How It Works

### Mode 1: `/wf-leader` — Smart Delegation

```
You → Leader → Agents → Report per phase → You approve → Next phase
```

| Phase                       | Agent(s)                                                              | Mode        |
| --------------------------- | --------------------------------------------------------------------- | ----------- |
| 📋 Planning                 | `@[/wf-planner]`                                                      | Sequential  |
| 🏗️ Architecture + 🎨 Design | `@[/wf-architect]` + `@[/wf-designer]`                                | ⚡ PARALLEL |
| 💻 Development              | `@[/wf-frontend-dev]` + `@[/wf-backend-dev]`                          | ⚡ PARALLEL |
| 🧪 QA & Fix                 | `@[/wf-qa-engineer]`                                                  | Sequential  |
| 🚀 Launch                   | `@[/wf-devops]` + `@[/wf-security-engineer]` + `@[/wf-seo-specialist]` + `@[/wf-tech-writer]` | ⚡ PARALLEL |

### Mode 2: `/wf-quickstart` — Full Autopilot

One command, complete project. No approvals needed. Best for MVPs and prototypes.

> 💡 **Tip:** After `gkt init <group>`, a workflow guide is displayed showing all available workflows with descriptions and sample prompts.

---

## 🔄 Workflows (46)

> **Naming convention:** All workflows use the `wf-` prefix. Type `/wf-` in your AI chat to filter only workflows.

### General Development

| Workflow                     | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| `/wf-leader`                 | Orchestrates the entire team from concept to production  |
| `/wf-quickstart`             | Fully automated project build from idea to production    |
| `/wf-planner`                | Analyzes requirements, writes PRD, breaks down tasks     |
| `/wf-meta-thinker`           | Creative advisor, brainstorming, vision development      |
| `/wf-architect`              | Systems design, database, API                            |
| `/wf-solution-architect`     | Strategic technical planning, trade-off analysis         |
| `/wf-designer`               | UI/UX design system and assets                           |
| `/wf-frontend-dev`           | Component, layout, state management (React/Vue/Tailwind) |
| `/wf-backend-dev`            | API implementation, DB queries (Node/Python/Go)          |
| `/wf-fullstack-coder`        | Architecture, backend, frontend, testing in one workflow |
| `/wf-mobile-dev`             | iOS/Android (React Native/Expo)                          |
| `/wf-devops`                 | Docker, CI/CD, cloud deployment                          |
| `/wf-cloud-deployer`         | AWS deployment, CI/CD, Docker, Kubernetes, serverless    |
| `/wf-qa-engineer`            | Test case, API, SQL, automation, performance             |
| `/wf-quality-guardian`       | Code review, testing, security audit in one pass         |
| `/wf-code-reviewer`          | Automated code quality review                            |
| `/wf-security-engineer`      | Security workflow (Audit/Pen-Test/Incident)              |
| `/wf-security-auditor`       | Penetration testing, vulnerability assessment            |
| `/wf-release-manager`        | Changelog generation, version bumping                    |
| `/wf-tech-writer`            | Documentation & API refs                                 |
| `/wf-doc-writer`             | Professional technical documentation, reports, RFC, ADR  |
| `/wf-knowledge-guide`        | Code explainer, note taker, handoff specialist           |

### Specialized

| Workflow                     | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| `/wf-n8n-automator`          | n8n workflow builder with 70+ SaaS connectors            |
| `/wf-nocobase-plugin-expert` | NocoBase plugin development (Server, Client, DB, API)    |
| `/wf-nocobase-plugin-build`  | Build NocoBase plugins                                   |
| `/wf-seo-specialist`         | SEO audit, meta tags, schema markup, Core Web Vitals     |
| `/wf-seo-marketer`           | SEO optimization, content strategy, CRO                  |
| `/wf-ai-agent-builder`       | Build LLM apps, RAG systems, multi-agent architectures   |
| `/wf-saas-connector`         | Automate 20+ SaaS platforms via API integrations         |
| `/wf-startup-advisor`        | Market analysis, financial modeling, GTM planning        |
| `/wf-researcher`             | Market analysis, web search, trend discovery             |
| `/wf-research-analyst`       | Deep research, analysis, file I/O, translation           |
| `/wf-deep-researcher`        | Comprehensive research and professional reports          |
| `/wf-prompt-engineer`        | Create optimized prompts for any AI model                |
| `/wf-image-creator`          | AI image generation, design assets, diagrams             |
| `/wf-translator`             | Multi-language translation and i18n management           |
| `/wf-api-graphql-dev`        | API & GraphQL development workflow                       |
| `/wf-claude-code-dev`        | Claude Code skills, prompt engineering, MCP              |
| `/wf-context-data-eng`       | Context engineering, RAG, data pipelines                 |
| `/wf-database-eng`           | Database design, optimization, migrations, CQRS          |
| `/wf-observability-eng`      | Monitoring, tracing, Grafana, Prometheus, SLO            |
| `/wf-doc-generator` ⭐ **New** | Document Generator — Orchestrates Word, Excel, PDF, and PPTX|

### UiPath RPA ⭐ New

| Workflow                | Description                                                                      |
| ----------------------- | -------------------------------------------------------------------------------- |
| `/wf-uipath-project` ⭐ | **All-in-one**: business analysis → brainstorm → plan → XAML implementation      |
| `/wf-uipath-analyst`    | Business analysis, process decomposition, architecture selection                 |
| `/wf-uipath-developer`  | XAML generation, REFramework wiring, UI inspection, validate-and-fix loop        |
| `/wf-uipath-reviewer`   | Code review for XAML quality, rule compliance, security, naming conventions      |
| `/wf-uipath-deploy`     | Package, publish to Orchestrator, schedule, monitor                              |

---

## 🤖 UiPath RPA Group

The `uipath` skill group provides end-to-end RPA project automation using UiPath Studio. Use `gkt init antigravity --group uipath` or `gkt init kiro --group uipath`.

### Skills included

| Skill                    | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| `uipath-core`            | XAML generation scripts, scaffold, validate, lint, decomposition rules      |
| `uipath-rpa-workflows`   | REFramework patterns, Dispatcher+Performer, Simple Sequence templates       |
| `uipath-shared`          | CLI reference, UI Automation prerequisites, selectors, debugging guide      |
| `uipath-platform`        | Orchestrator queues, assets, processes, folder management                   |
| `uipath-coded-workflows` | C# coded workflows, unit testing, OOP patterns in UiPath Studio             |
| `uipath-agents`          | UiPath AI agents with LLM reasoning and dynamic decision making             |

### `/wf-uipath-project` — All-in-One Workflow

The flagship UiPath workflow covers the full project lifecycle in one command:

```
Phase 0: Session Resume Check
    ↓ (loads brain/workflow_sessions/ if previous session exists)
Phase 1: Business Analysis & Brainstorm
    → 10 elicitation questions
    → Key Business Points: value, complexity, constraints
    → Architecture selection: REFramework / Simple Sequence / Dispatcher+Performer
    ↓ [Checkpoint saved to brain]
Phase 2: Plan & Task Breakdown
    → Workflow tree decomposition
    → Argument map (In/Out per workflow)
    → Config.xlsx keys
    → Dev Sequence A→E
    ↓ [Checkpoint saved to brain]
Phase 3: Implement XAML
    → Scaffold project (scaffold_project.py)
    → UI Inspection — MANDATORY before any generation
    → Generate workflows (generate_workflow.py) + validate loop
    → Wire Main.xaml / Process.xaml
    ↓ [Checkpoint saved to brain per sub-phase]
Phase 4: Final Validation & Handoff
    → XAML quality checklist
    → Handoff document
    ↓ [Session marked complete in brain]
```

---

## 📝 Gen-Doc Group ⭐ New

The `gen-doc` skill group provides an automated pipeline for generating AI-designed and properly formatted Documents. Use `gkt init antigravity --group gen-doc` or `gkt init kiro --group gen-doc`.

### Skills included

| Skill                    | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| `gen-doc-docx`           | Word generation and MS Office XSD Gate check validation                     |
| `gen-doc-xlsx`           | Safe Excel tabular data editing + Formula persistence via precise XML       |
| `gen-doc-pdf`            | Vectorized PDF Design System using NodeJS and Python                        |
| `gen-doc-ppt-master`     | Core document presentation skill: SVG templating and PPTX export            |

### `/wf-doc-generator` — Document Generator Workflow

The document generator workflow takes you from requirements to a fully editable artifact:

```text
Phase 0: Environment Validation
    ↓ Auto-installs required environment dependencies
Phase 1: Source Material Assimilation
    → Import and convert PDF/DOCX/URL/TEXT into Markdown
Phase 2: Template Selection & Strategy
    → Determine layouts, styling, and compile a design blueprint
Phase 3: Visual & Content Execution
    → Generate AI imagery and bind content into vector pages
Phase 4: Finalize & Export
    → Post-process SVG layers and export directly to native PPTX
```

---

## 📂 Project Structure

```
.agent/
├── agents/              # 18 specialist agent definitions (Claude Code native format)
│   ├── leader.md
│   ├── architect.md
│   └── ... (16 more)
├── workflows/           # 46 workflows (wf-* prefix)
│   ├── wf-leader.md
│   ├── wf-uipath-project.md
│   └── ...
├── skills/              # 893+ skills across 21 groups + 13 default
│   ├── uipath-core/
│   ├── brain-manager/
│   └── ...
└── brain/               # Persistent project memory
    ├── default_skills.md          # Default skill reference & integration guide
    ├── skills_manifest.json       # Lightweight index of all skills (lazy-loading)
    ├── lifecycle.md               # Session phases: init → plan → work → checkpoint → handoff
    ├── platform_notes.md          # Cross-platform compatibility (Windows/Linux/macOS)
    ├── project_context.json       # Project metadata, architecture, decisions, conventions
    ├── agent_index.json           # Agent role registry
    └── workflow_sessions/         # Cross-session workflow continuity ⭐ New
        ├── SESSIONS.md            # Active session index + checkpoint format spec
        ├── wf-uipath-project-latest.md   # Latest session state (always current)
        └── wf-{name}-{date}.md           # Per-run dated artifacts
```

---

## 🧠 Brain System

Every installation includes the **Brain** — persistent memory that agents read at session start and write to at each checkpoint.

### Core brain files

| Brain File               | Purpose                                                     |
| ------------------------ | ----------------------------------------------------------- |
| `default_skills.md`      | 13 default skills, usage guide, workflow wiring             |
| `skills_manifest.json`   | Lightweight index of ALL 893+ skills for lazy-loading       |
| `lifecycle.md`           | Session lifecycle: init, plan, work, checkpoint, handoff    |
| `platform_notes.md`      | Cross-platform guide: paths, shells, encoding, permissions  |
| `project_context.json`   | Project metadata template (tech stack, conventions, sprint) |
| `agent_index.json`       | Agent role definitions and handoff protocol                 |

### Workflow Session Continuity ⭐ New

`brain/workflow_sessions/` stores structured session artifacts — similar to how Claude Code compacts conversations. When a workflow saves a checkpoint, a new session can **resume exactly where the previous one left off**.

**How it works:**

1. **First run**: workflow creates `{wf-name}-{date}.md` + `{wf-name}-latest.md`
2. **Each phase end**: agent appends phase summary (decisions, outputs, open questions)
3. **New session**: `lifecycle.md` init phase checks `workflow_sessions/` automatically:
   ```
   📋 Found session: InvoiceAutomation — paused at Phase 2
   Resume from that point, or restart from Phase 0? (resume/restart)
   ```
4. **Resume**: skips completed phases (✅), continues from in-progress phase (🔄)

**Session artifact format:**
```markdown
---
workflow: wf-uipath-project
project: InvoiceAutomation
session_date: 2024-01-15
last_phase: "Phase 2 — Plan"
status: in_progress
---

## Phase 1 — Business Analysis ✅
**Architecture selected:** REFramework Performer — 200+ invoices/day, needs per-item retry
**Apps:** Outlook (email), SAP (ERP entry)

## Phase 2 — Plan ✅
**Workflow tree:** 8 workflows across Outlook/ and SAP/ folders
**Next steps:** Start Phase A scaffold
```

**IDE support:**

| IDE                | Session file location              | How it's loaded                              |
| ------------------ | ---------------------------------- | -------------------------------------------- |
| **Antigravity**    | `.agent/brain/workflow_sessions/`  | `lifecycle.md` Init Phase instruction        |
| **Kiro**           | `.kiro/brain/workflow_sessions/`   | `steering/brain.md` (always-loaded steering) |
| **GitHub Copilot** | `.agent/brain/workflow_sessions/`  | `leader.instructions.md` Session Init block  |

### 13 Default Skills (Always Installed)

| Category           | Skills                                                                               |
| ------------------ | ------------------------------------------------------------------------------------ |
| Memory & Context   | `brain-manager`, `journal-manager`, `context-manager`, `codebase-navigator`         |
| Planning & Quality | `concise-planning`, `writing-plans`, `clean-code`, `debugger`, `error-handling-patterns` |
| Version Control    | `git-manager`, `commit`                                                              |
| Cross-Platform     | `powershell-windows`, `bash-linux`                                                   |

---

## 🧰 Token Optimization

| Tool                   | What it does                                    | Savings     |
| ---------------------- | ----------------------------------------------- | ----------- |
| **Skills Manifest**    | Lightweight index — load full SKILL.md on demand | ~50% tokens |
| **Context Manager**    | Minifies code before AI sees it                 | ~50% tokens |
| **Context Router**     | Queries only relevant data from 34+ sources     | ~70% tokens |
| **Diff Applier**       | Applies surgical patches instead of rewriting   | ~90% tokens |

---

## 🚢 Publishing to PyPI

This package is published as `gkt` on [PyPI](https://pypi.org/project/gkt/). Publishing is automated via GitHub Actions.

### Auto-Publish on Tag Push

1. Update the version in `GravityKit/VERSION`
2. Commit and push changes
3. Create and push a version tag:

```bash
git tag v3.8.0
git push origin v3.8.0
```

The GitHub Actions workflow (`.github/workflows/publish.yml`) will:

- Build the package (`python -m build`)
- Check with Twine (`twine check dist/*`)
- Publish to PyPI via OIDC trusted publishing

> **Note:** OIDC trusted publishing is configured. No API token needed if the PyPI project is linked to this GitHub repo.

---

## 📄 License

MIT
