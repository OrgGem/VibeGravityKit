# 🌌 VibeGravityKit

> **The AI-Native Software House in a Box.**
> _Build enterprise-grade software with a team of 887 AI Skills — organized into 16 focused groups for fast, token-efficient development._

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
gkt init n8n-dev         # 18 n8n automation skills
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

Instead of loading all 887 skills, install only the group you need:

```bash
gkt groups   # List all available groups
```

| Group                  | Skills | Description                                     |
| ---------------------- | ------ | ----------------------------------------------- |
| `general-dev`          | 30     | Backend, Frontend, Full-stack development       |
| `n8n-dev`              | 18     | n8n workflow automations                        |
| `nocobase-dev`         | 25     | NocoBase plugin development                     |
| `general-doc`          | 20     | Technical docs, RFC, ADR, wiki                  |
| `research`             | 18     | Deep research, market analysis                  |
| `cloud-deploy`         | 26     | Cloud, DevOps, CI/CD, Kubernetes                |
| `security-audit`       | 28     | Pentest, vulnerability assessment               |
| `seo-marketing`        | 28     | SEO, CRO, content marketing                     |
| `ai-agent`             | 28     | LLM apps, RAG, multi-agent                      |
| `saas-integrate`       | 28     | 28+ SaaS platform connectors                    |
| `startup-biz`          | 26     | Market analysis, financial modeling             |
| `api-graphql`          | 24     | API design, GraphQL, REST, OpenAPI, FastAPI     |
| `claude-code`          | 22     | Claude Code skills, prompt engineering, MCP     |
| `context-data-rag`     | 28     | Context engineering, RAG, data pipelines        |
| `database`             | 26     | SQL/NoSQL, Postgres, migrations, CQRS           |
| `observability-report` | 22     | Monitoring, Grafana, Prometheus, SLO, incidents |

**Usage:**

```bash
gkt init general-dev                    # Install group (default: Antigravity IDE)
gkt init antigravity --group n8n-dev    # Specify IDE + group
gkt init antigravity                    # Install ALL skills (legacy behavior)
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

| IDE                | Command                | Creates                                  |
| ------------------ | ---------------------- | ---------------------------------------- |
| **Antigravity**    | `gkt init antigravity` | `.agent/` (workflows + skills)           |
| **Cursor**         | `gkt init cursor`      | `.cursor/rules/*.mdc`                    |
| **Windsurf**       | `gkt init windsurf`    | `.windsurf/rules/*.md`                   |
| **Cline**          | `gkt init cline`       | `.clinerules/*.md`                       |
| **Kilo Code**      | `gkt init kilocode`    | `.kilocode/rules/*.md`                   |
| **GitHub Copilot** | `gkt init copilot`     | `.github/instructions/*.instructions.md` |
| **All**            | `gkt init`             | All of the above                         |

---

## 🚀 How It Works

### Mode 1: `@[/leader]` — Smart Delegation

```
You → Leader → Agents → Report per phase → You approve → Next phase
```

| Phase                       | Agent                                                  | Mode        |
| --------------------------- | ------------------------------------------------------ | ----------- |
| 📋 Planning                 | `@[/planner]`                                          | Sequential  |
| 🏗️ Architecture + 🎨 Design | `@[/architect]` + `@[/designer]`                       | ⚡ PARALLEL |
| 💻 Development              | `@[/frontend-dev]` + `@[/backend-dev]`                 | ⚡ PARALLEL |
| 🧪 QA & Fix                 | `@[/qa-engineer]`                                      | Sequential  |
| 🚀 Launch                   | `@[/devops]` + `@[/security]` + `@[/seo]` + `@[/docs]` | ⚡ PARALLEL |

### Mode 2: `@[/quickstart]` — Full Autopilot

One command, complete project. No approvals needed. Best for MVPs and prototypes.

---

## 🔄 Workflows (40)

| Workflow                  | Description                                              |
| ------------------------- | -------------------------------------------------------- |
| `/leader`                 | Orchestrates the entire team from concept to production  |
| `/quickstart`             | Fully automated project build from idea to production    |
| `/planner`                | Analyzes requirements, writes PRD, breaks down tasks     |
| `/meta-thinker`           | Creative advisor, brainstorming, vision development      |
| `/architect`              | Systems design, database, API                            |
| `/solution-architect`     | Strategic technical planning, trade-off analysis         |
| `/designer`               | UI/UX design system and assets                           |
| `/frontend-dev`           | Component, layout, state management (React/Vue/Tailwind) |
| `/backend-dev`            | API implementation, DB queries (Node/Python/Go)          |
| `/fullstack-coder`        | Architecture, backend, frontend, testing in one workflow |
| `/mobile-dev`             | iOS/Android (React Native/Expo)                          |
| `/devops`                 | Docker, CI/CD, cloud deployment                          |
| `/cloud-deployer`         | AWS deployment, CI/CD, Docker, Kubernetes, serverless    |
| `/n8n-automator`          | n8n workflow builder with 70+ SaaS connectors            |
| `/nocobase-plugin-expert` | NocoBase plugin development (Server, Client, DB, API)    |
| `/nocobase-plugin-build`  | Build NocoBase plugins                                   |
| `/qa-engineer`            | Test case, API, SQL, automation, performance             |
| `/quality-guardian`       | Code review, testing, security audit in one pass         |
| `/code-reviewer`          | Automated code quality review                            |
| `/security-engineer`      | Security workflow (Audit/Pen-Test/Incident)              |
| `/security-auditor`       | Penetration testing, vulnerability assessment            |
| `/seo-specialist`         | Search engine optimization                               |
| `/seo-marketer`           | SEO optimization, content strategy, CRO                  |
| `/ai-agent-builder`       | Build LLM apps, RAG systems, multi-agent architectures   |
| `/saas-connector`         | Automate 20+ SaaS platforms via API integrations         |
| `/startup-advisor`        | Market analysis, financial modeling, GTM planning        |
| `/tech-writer`            | Documentation & API refs                                 |
| `/doc-writer`             | Professional technical documentation, reports, RFC, ADR  |
| `/knowledge-guide`        | Code explainer, note taker, handoff specialist           |
| `/researcher`             | Market analysis, web search, trend discovery             |
| `/research-analyst`       | Deep research, analysis, file I/O, translation           |
| `/deep-researcher`        | Comprehensive research and professional reports          |
| `/release-manager`        | Changelog generation, version bumping                    |
| `/prompt-engineer`        | Create optimized prompts for any AI model                |
| `/image-creator`          | AI image generation, design assets, diagrams             |
| `/api-graphql-dev`        | API & GraphQL development workflow                       |
| `/claude-code-dev`        | Claude Code skills, prompt engineering, MCP              |
| `/context-data-eng`       | Context engineering, RAG, data pipelines                 |
| `/database-eng`           | Database design, optimization, migrations, CQRS          |
| `/observability-eng`      | Monitoring, tracing, Grafana, Prometheus, SLO            |

---

## 📂 Project Structure

```
.agent/
├── workflows/       # Instructions for each agent role (40 workflows)
├── skills/          # 887 skills across 16 groups
└── brain/           # Project context & memory
```

---

## 🧰 Token Optimization

| Tool                | What it does                                  | Savings     |
| ------------------- | --------------------------------------------- | ----------- |
| **Context Manager** | Minifies code before AI sees it               | ~50% tokens |
| **Context Router**  | Queries only relevant data from 34+ sources   | ~70% tokens |
| **Diff Applier**    | Applies surgical patches instead of rewriting | ~90% tokens |

---

## 🚢 Publishing to PyPI

This package is published as `gkt` on [PyPI](https://pypi.org/project/gkt/). Publishing is automated via GitHub Actions.

### Auto-Publish on Tag Push

1. Update the version in `GravityKit/VERSION`
2. Commit and push changes
3. Create and push a version tag:

```bash
git tag v3.2.1
git push origin v3.2.1
```

The GitHub Actions workflow (`.github/workflows/publish.yml`) will:

- Build the package (`python -m build`)
- Check with Twine (`twine check dist/*`)
- Publish to PyPI via OIDC trusted publishing

> **Note:** OIDC trusted publishing is configured. No API token needed if the PyPI project is linked to this GitHub repo.

---

## 📄 License

MIT
