# 🌌 VibeGravityKit

> **The AI-Native Software House in a Box.**
> _Build enterprise-grade software with a team of AI Agents — with **parallel delegation** for maximum speed and minimum token costs._

---

## ⚡ Quick Start

```bash
# Install from PyPI
pip install gk

# Init in your project
cd /path/to/your-project
gk init            # Install for ALL IDEs (Antigravity, Cursor, Windsurf, Cline)
gk init cursor     # Or install for a specific IDE only
```

> **Requirements:** Python 3.9+, Node.js 18+

**For development / contributing:**

```bash
git clone https://github.com/OrgGem/VibeGravityKit.git
cd VibeGravityKit
pip install -e .   # Editable install
```

---

## 🛠️ CLI Commands

| Command                    | Description                                                                       |
| -------------------------- | --------------------------------------------------------------------------------- |
| `gk init [ide]`            | Install agents for your IDE (`all`, `antigravity`, `cursor`, `windsurf`, `cline`) |
| `gk list`                  | List all available AI agents and their roles                                      |
| `gk doctor`                | Check environment health (Python, Node, Git, npm)                                 |
| `gk update`                | Update GravityKit to the latest version                                           |
| `gk version`               | Show current version                                                              |
| `gk brain`                 | Manage project brain — context, decisions, conventions                            |
| `gk journal`               | Knowledge journal — capture lessons, bugs, insights                               |
| `gk skills list [--all]`   | List active skills (or all including disabled)                                    |
| `gk skills search <query>` | Search skills by keyword                                                          |
| `gk skills enable <name>`  | Enable a disabled skill                                                           |
| `gk skills disable <name>` | Disable a skill                                                                   |
| `gk skills count`          | Show total skill count                                                            |
| `gk validate [--strict]`   | Validate all SKILL.md files                                                       |
| `gk generate-index`        | Regenerate `skills_index.json`                                                    |

> **Alias:** `gravitykit` works the same as `gk`.

---

## 🌐 Multi-IDE Support

| IDE             | Command               | Creates                        |
| --------------- | --------------------- | ------------------------------ |
| **Antigravity** | `gk init antigravity` | `.agent/` (workflows + skills) |
| **Cursor**      | `gk init cursor`      | `.cursor/rules/*.mdc`          |
| **Windsurf**    | `gk init windsurf`    | `.windsurf/rules/*.md`         |
| **Cline**       | `gk init cline`       | `.clinerules/*.md`             |

---

## 🚀 How It Works — Two Ways to Build

### Mode 1: `@[/leader]` — Smart Delegation (Recommended)

> **You are the Boss. The Leader is your right hand.**

```
You → Leader → Agents → Report back per phase → You approve → Next phase
```

**Flow:**

1. Tell the Leader what you want to build.
2. Leader analyzes, brainstorms, and presents a plan.
3. **You approve the plan** ✅
4. Leader **auto-delegates** to the right agents:

| Phase                       | Agent                                                  | Mode            |
| --------------------------- | ------------------------------------------------------ | --------------- |
| 📋 Planning                 | `@[/planner]`                                          | Sequential      |
| 🏗️ Architecture + 🎨 Design | `@[/architect]` + `@[/designer]`                       | ⚡ **PARALLEL** |
| 💻 Development              | `@[/frontend-dev]` + `@[/backend-dev]`                 | ⚡ **PARALLEL** |
| 🧪 QA & Fix                 | `@[/qa-engineer]`                                      | Sequential      |
| 🚀 Launch                   | `@[/devops]` + `@[/security]` + `@[/seo]` + `@[/docs]` | ⚡ **PARALLEL** |

5. After each phase, Leader reports results and waits for your approval.
6. **QA Smart Loop**: If a bug can't be fixed, Leader calls `@[/meta-thinker]` + `@[/planner]` to rethink. Max **3 retries**.

---

### Mode 2: `@[/quickstart]` — Full Autopilot

> **One command. Complete project. No approvals needed.**

```
You → Quickstart → [Auto-runs ALL agents] → Delivers complete project
```

**Perfect for:** MVPs, prototypes, hackathons.

- Built-in **QA Auto-Fix Loop** with max **5 retries** per bug.
- Delivers a **complete report**: features built, test results, unresolved issues, and how to run it.

---

### Mode Comparison

|                      | `@[/leader]`             | `@[/quickstart]`  |
| -------------------- | ------------------------ | ----------------- |
| **User involvement** | Approve each phase       | None (fully auto) |
| **Parallel agents**  | ⚡ Yes (up to 4x faster) | ⚡ Yes            |
| **Bug fix retries**  | 3 max                    | 5 max             |
| **Best for**         | Production apps          | MVPs, prototypes  |

---

## 🎮 The Agents

In VibeGravityKit, **You are the Boss.** Chat with your agents using `@` mentions.

### Strategy & Vision 🧠

| Agent                    | Role                                       |
| ------------------------ | ------------------------------------------ |
| `@[/leader]`             | Orchestrates all agents, reports per phase |
| `@[/quickstart]`         | Full autopilot — end-to-end project build  |
| `@[/meta-thinker]`       | Creative advisor, brainstorming            |
| `@[/planner]`            | PRD, user stories, timeline                |
| `@[/researcher]`         | Web search & market analysis               |
| `@[/tech-stack-advisor]` | Tech stack recommendations                 |

### Design & Product 🎨

| Agent               | Role                                  |
| ------------------- | ------------------------------------- |
| `@[/architect]`     | System architecture, DB schema        |
| `@[/designer]`      | UI/UX design system                   |
| `@[/mobile-wizard]` | Mobile app scaffolding (Expo/Flutter) |

### Engineering 💻

| Agent              | Role                              |
| ------------------ | --------------------------------- |
| `@[/frontend-dev]` | Web development (React, Next.js)  |
| `@[/backend-dev]`  | API development (Node.js, Python) |
| `@[/devops]`       | Docker, CI/CD, infrastructure     |

### Quality & Support 🛡️

| Agent                   | Role                           |
| ----------------------- | ------------------------------ |
| `@[/knowledge-guide]`   | Code explainer, note taker     |
| `@[/qa-engineer]`       | Testing & quality assurance    |
| `@[/security-engineer]` | Security scanning & audits     |
| `@[/tech-writer]`       | Documentation & release notes  |
| `@[/seo-specialist]`    | SEO optimization               |
| `@[/code-reviewer]`     | Code quality scanner           |
| `@[/release-manager]`   | Changelog & version management |

---

## 📂 Project Structure

```
.agent/
├── workflows/       # Instructions for each agent role
├── skills/          # 886 skills across 17 categories
└── brain/           # Project context & memory
```

---

## 🔄 Workflows (29)

| Workflow              | Description                                                              |
| --------------------- | ------------------------------------------------------------------------ |
| `/leader`             | Team Lead — Orchestrates the entire team from concept to production      |
| `/quickstart`         | Fully automated project build from idea to production                    |
| `/planner`            | Analyzes requirements, writes PRD, breaks down tasks                     |
| `/meta-thinker`       | Idea Consultant, Creative Advisor, Vision Development                    |
| `/architect`          | Systems Design, Database, API                                            |
| `/solution-architect` | Strategic technical planning, trade-off analysis, roadmap design         |
| `/designer`           | UI/UX Design System and Assets                                           |
| `/frontend-dev`       | Component, Layout, State Management (React/Vue/Tailwind)                 |
| `/backend-dev`        | API Implementation, DB Queries (Node/Python/Go)                          |
| `/fullstack-coder`    | Architecture, Backend, Frontend, Testing in one workflow                 |
| `/mobile-dev`         | iOS/Android (React Native/Expo)                                          |
| `/devops`             | Docker, CI/CD, Cloud Deployment                                          |
| `/cloud-deployer`     | AWS deployment, CI/CD pipelines, Docker, Kubernetes, serverless          |
| `/n8n-automator`      | n8n workflow builder — Code nodes, API integrations, 70+ SaaS connectors |
| `/qa-engineer`        | Test Case, API, SQL, Automation, Performance, Bug Reporting              |
| `/quality-guardian`   | Code review, testing, security audit in one comprehensive pass           |
| `/code-reviewer`      | Automated code quality review with pattern-based analysis                |
| `/security-engineer`  | Security Workflow (Audit/Pen-Test/Incident)                              |
| `/seo-specialist`     | Search Engine Optimization                                               |
| `/tech-writer`        | Documentation & API Refs                                                 |
| `/doc-writer`         | Professional technical documentation, reports, RFC, ADR                  |
| `/knowledge-guide`    | Code Explainer, Note Taker, Handoff Specialist                           |
| `/researcher`         | Market Analysis, Web Search, Trend Discovery                             |
| `/research-analyst`   | Deep research, analysis, file I/O, image generation, translation         |
| `/deep-researcher`    | Comprehensive research, analysis, and professional report writing        |
| `/release-manager`    | Changelog generation, version bumping, and release notes                 |
| `/prompt-engineer`    | Create optimized prompts from user input for any AI model                |
| `/image-creator`      | AI image generation, design assets, diagrams, visual content             |
| `/translator`         | Multi-language translation, i18n setup, and localization management      |

---

## 📊 Skill Categories (886 total)

| Category                   | Skills | Description                                                                 |
| -------------------------- | -----: | --------------------------------------------------------------------------- |
| 🔷 Azure & Microsoft SDK   |    121 | Azure AI, Storage, Cosmos DB, Event Hubs, Service Bus, Identity, etc.       |
| 🔧 Workflow & Utilities    |    176 | Git, shell scripting, project scaffolding, memory, i18n, file tools         |
| 💻 Backend & Languages     |     93 | Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP, FastAPI, Django, etc.    |
| 🤖 AI, LLM & Agents        |     74 | RAG, LangChain, LangGraph, CrewAI, prompt engineering, voice AI, embeddings |
| 🔌 SaaS Automation         |     89 | Slack, Jira, Notion, HubSpot, Salesforce, GitHub, Gmail, 70+ integrations   |
| 📈 Marketing & Business    |     63 | SEO, content marketing, pricing, email, analytics, startup tools            |
| 🛡️ Security & Pentesting   |     61 | OWASP, Burp Suite, Metasploit, red team, vulnerability scanning             |
| ☁️ DevOps, Cloud & Infra   |     52 | Docker, Kubernetes, Terraform, CI/CD, monitoring, incident response         |
| 🎨 Frontend & UI           |     44 | React, Angular, Next.js, Tailwind, Three.js, design systems                 |
| ✅ Testing & Quality       |     41 | TDD, Playwright, Jest, code review, debugging, linting                      |
| 🏛️ Architecture & Patterns |     19 | C4 diagrams, microservices, clean architecture, system design               |
| 📚 Documentation           |     17 | Wiki, README, API docs, changelogs, tutorials                               |
| 🗄️ Database                |     13 | PostgreSQL, MySQL, MongoDB, Redis, SQL optimization                         |
| 📊 Data Engineering        |      8 | Spark, dbt, Airflow, data pipelines, data quality                           |
| 📱 Mobile Development      |      6 | React Native, Flutter, Expo, iOS, SwiftUI                                   |
| 🎮 Game Development        |      6 | Unity, Unreal Engine, Godot, Minecraft plugins                              |
| ⛓️ Blockchain & Web3       |      3 | Solidity, DeFi, NFT standards                                               |

---

## 🧰 Token Optimization

| Tool                | What it does                                  | Savings     |
| ------------------- | --------------------------------------------- | ----------- |
| **Context Manager** | Minifies code before AI sees it               | ~50% tokens |
| **Context Router**  | Queries only relevant data from 34+ sources   | ~70% tokens |
| **Diff Applier**    | Applies surgical patches instead of rewriting | ~90% tokens |

---

## ❤️ Credits

Special thanks to **[ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)** for pioneering the data-driven approach to UI/UX generation.

## 📄 License

MIT © [Nhqvu2005](https://github.com/Nhqvu2005)
