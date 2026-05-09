# GravityKit

GravityKit là bộ công cụ CLI để cài đặt skills, agents, workflows và bộ nhớ dự án vào một repository đang làm việc. Mục tiêu của hệ thống là biến AI IDE thành một nhóm chuyên gia có vai trò rõ ràng: biết đọc ngữ cảnh dự án, chọn workflow phù hợp, tải đúng skill khi cần, lưu quyết định qua nhiều phiên làm việc và dùng MCP để tìm kiếm code/tài liệu hiệu quả.

Phiên bản hiện tại: `3.12.7`

## Nội Dung

- [Cai Dat Nhanh](#cai-dat-nhanh)
- [GravityKit Hoat Dong Nhu The Nao](#gravitykit-hoat-dong-nhu-the-nao)
- [Cau Truc Duoc Cai Vao Project](#cau-truc-duoc-cai-vao-project)
- [Skill Groups](#skill-groups)
- [Agents Va Workflows](#agents-va-workflows)
- [Brain Va Session Continuity](#brain-va-session-continuity)
- [MCP Va Code Graph](#mcp-va-code-graph)
- [CLI Reference](#cli-reference)
- [Huong Dan Su Dung Theo Tinh Huong](#huong-dan-su-dung-theo-tinh-huong)
- [Phat Trien Va Dong Gop](#phat-trien-va-dong-gop)
- [Phat Hanh](#phat-hanh)

## Cai Dat Nhanh

GravityKit có hai cách dùng chính:

```bash
pip install gkt
```

Hoặc dùng qua Node.js:

```bash
npx gkt-node init
```

Yêu cầu khuyến nghị:

| Thanh phan | Yeu cau |
| --- | --- |
| Python | 3.9+ |
| Node.js | 16+ nếu dùng NPX hoặc các workflow JS |
| Git | Khuyến nghị để quản lý thay đổi và release |
| npm | Khuyến nghị cho NPX CLI và dự án frontend |

Khởi tạo trong thư mục dự án:

```bash
cd /path/to/your-project
gkt init antigravity --group general-dev
gkt mcp
```

Sau khi init, mở AI IDE và gọi workflow trong chat, ví dụ:

```text
/wf-planner Analyze requirements and create a PRD for the customer portal.
/wf-architect Design the database schema and API for this booking system.
/wf-code-reviewer Review my latest changes for security and maintainability.
```

## GravityKit Hoat Dong Nhu The Nao

GravityKit có bốn lớp chính:

| Lop | Chuc nang |
| --- | --- |
| Skill | Tài liệu năng lực chuyên môn. Mỗi skill là một thư mục có `SKILL.md`, có thể kèm `references/`, `scripts/`, `assets/`, `evals/`. |
| Agent | Vai trò chuyên gia như planner, architect, frontend-dev, security-engineer. Agent quyết định cách tiếp cận và skill cần dùng. |
| Workflow | Quy trình theo pha, gọi bằng slash command dạng `/wf-*`. Workflow hướng dẫn AI làm việc từng bước. |
| Brain | Bộ nhớ dự án: context, quyết định kiến trúc, lifecycle, manifest skill, checkpoint workflow. |

Luồng dùng phổ biến:

```text
User request
  -> Workflow /wf-*
  -> Agent role
  -> Brain: load context, decisions, session checkpoints
  -> Skills: load only SKILL.md relevant to task
  -> MCP: search code graph, semantic index, document files
  -> Work output
  -> Brain: save checkpoint, decisions, journal notes
```

Nguyên tắc quan trọng: workflow định nghĩa "làm theo quy trình nào", agent định nghĩa "ai chịu trách nhiệm", skill định nghĩa "kiến thức và công cụ cần dùng", brain giữ "những gì hệ thống cần nhớ".

## Cau Truc Duoc Cai Vao Project

Với Antigravity/Claude-style agent layout:

```text
.agent/
  agents/                 # 18 specialist agents
  workflows/              # 51 workflow files, prefix wf-*
  skills/                 # selected skills plus default skills
  brain/
    agent_index.json
    default_skills.md
    lifecycle.md
    platform_notes.md
    project_context.json
    skills_manifest.json
    workflow_sessions/
```

Với Kiro:

```text
.kiro/
  skills/
  steering/
  hooks/
  specs/                  # workflow files
  agents/
  brain/
```

Với IDE adapter khác:

| Target | Lenh | Thu muc duoc tao |
| --- | --- | --- |
| Antigravity | `gkt init antigravity` | `.agent/` |
| Kiro | `gkt init kiro` | `.kiro/` |
| Cursor | `gkt init cursor` | `.cursor/rules/` và `.agent/` nếu cần |
| Windsurf | `gkt init windsurf` | `.windsurf/rules/` và `.agent/` nếu cần |
| Cline | `gkt init cline` | `.clinerules/` và `.agent/` nếu cần |
| Kilo Code | `gkt init kilocode` | `.kilocode/rules/` và `.agent/` nếu cần |
| GitHub Copilot | `gkt init copilot` | `.github/instructions/` và `.agent/` nếu cần |
| Codex CLI | `gkt init codex` | không copy skill; ghi scope để `gkt mcp` cấu hình MCP |
| Tat ca | `gkt init` hoặc `gkt init all` | cài tất cả target Python CLI hỗ trợ |

Lưu ý: NPX CLI hiện hỗ trợ các adapter chính trong package `gkt-node`; Python CLI là nguồn tham chiếu đầy đủ nhất.

## Skill Groups

Skill group giúp cài đúng bộ năng lực cho dự án thay vì copy toàn bộ thư viện. Mỗi group được tự động merge thêm nhóm `_default`.

Default skills hiện có 16 skill nền:

- Memory/context: `brain-manager`, `journal-manager`, `context-manager`, `codebase-navigator`, `code-graph-index`, `document-reader`, `skill-router`
- Planning/quality: `concise-planning`, `writing-plans`, `clean-code`, `debugger`, `error-handling-patterns`
- Version control: `git-manager`, `commit`
- Cross-platform: `powershell-windows`, `bash-linux`

Xem danh sách group từ CLI:

```bash
gkt groups
```

Cài theo group:

```bash
gkt init general-dev
gkt init antigravity --group uipath
gkt init kiro --group gen-doc
gkt init all --group nocobase-dev
```

Các group hiện có:

| Group | Huong su dung |
| --- | --- |
| `general-dev` | Backend, frontend, full-stack, planning, QA, review. |
| `n8n-dev` | Xây dựng automation và workflow n8n. |
| `nocobase-dev` | Phát triển, build, review plugin NocoBase. |
| `general-doc` | README, API docs, RFC, ADR, wiki, onboarding docs. |
| `research` | Deep research, phân tích thị trường, research report. |
| `cloud-deploy` | Docker, CI/CD, Kubernetes, cloud deployment. |
| `security-audit` | Threat modeling, SAST, vulnerability review. |
| `security-pentest` | Pentest có kiểm soát, offensive security workflow. |
| `seo-marketing` | SEO audit, content strategy, schema markup, CRO. |
| `ai-agent` | LLM app, RAG, multi-agent, MCP, evaluation. |
| `saas-crm` | HubSpot, Salesforce, Pipedrive, Stripe, Shopify. |
| `saas-comms` | Slack, Discord, WhatsApp, Gmail, email automation. |
| `saas-project` | Jira, Asana, Trello, ClickUp, Monday, Notion, Airtable, GitHub. |
| `saas-marketing` | Twitter/X, LinkedIn, Instagram, Google Calendar/Drive/Sheets. |
| `startup-biz` | Market sizing, pricing, GTM, finance, business plan. |
| `api-graphql` | REST, GraphQL, OpenAPI, FastAPI, integration. |
| `claude-code` | Claude Code skills, prompt engineering, custom MCP. |
| `context-data-rag` | Context engineering, RAG, embeddings, data pipelines. |
| `database` | SQL/NoSQL, Postgres, migrations, CQRS, event sourcing. |
| `observability-report` | Monitoring, tracing, Grafana, Prometheus, SLO, incidents. |
| `uipath` | UiPath RPA, XAML, REFramework, Orchestrator, coded workflows. |
| `gen-doc` | Generate PPTX từ Markdown/source material bằng pipeline thiết kế. |
| `finance` | Valuation, market data, sentiment, quant research, VC analysis, finance reports. |

## Agents Va Workflows

GravityKit có 18 agent chuyên trách:

| Agent | Vai tro |
| --- | --- |
| `leader` | Điều phối nhiều workflow và specialist agent. |
| `quickstart` | Tạo nhanh MVP/prototype với ít vòng hỏi lại. |
| `planner` | Yêu cầu, PRD, task breakdown, acceptance criteria. |
| `architect` | Kiến trúc hệ thống, API, database, trade-off. |
| `designer` | UX/UI, design system, visual direction. |
| `frontend-dev` | React/Vue/Tailwind, component, state, layout. |
| `backend-dev` | API, database, auth, business logic. |
| `mobile-dev` | React Native/Expo, iOS/Android. |
| `devops` | Docker, CI/CD, cloud, Kubernetes. |
| `qa-engineer` | Test plan, automated test, regression, performance. |
| `code-reviewer` | Review chất lượng code, maintainability, risks. |
| `security-engineer` | Security audit, threat modeling, incident response. |
| `tech-writer` | Docs, ADR, RFC, API reference, tutorial. |
| `researcher` | Research, market intelligence, competitor analysis. |
| `meta-thinker` | Brainstorm, product direction, reframing. |
| `knowledge-guide` | Onboarding codebase, handoff, knowledge capture. |
| `release-manager` | Version bump, changelog, release notes, tags. |
| `seo-specialist` | SEO, schema, Core Web Vitals, sitemap. |

Workflow được gọi bằng prefix `/wf-`. Gõ `/wf-` trong AI chat để lọc danh sách.

Các workflow nền tảng:

| Workflow | Khi nao dung |
| --- | --- |
| `/wf-leader` | Muốn điều phối từ ý tưởng đến production qua nhiều vai trò. |
| `/wf-quickstart` | Muốn build nhanh prototype/MVP. |
| `/wf-planner` | Cần làm rõ yêu cầu, PRD, scope, task list. |
| `/wf-architect` | Cần thiết kế kiến trúc, database, API. |
| `/wf-fullstack-coder` | Cần một workflow build end-to-end full-stack. |
| `/wf-quality-guardian` | Cần review tổng hợp code, test, security. |
| `/wf-release-manager` | Cần chuẩn bị version, changelog, release notes. |

Workflow chuyên biệt tiêu biểu:

| Workflow | Chuc nang |
| --- | --- |
| `/wf-n8n-automator` | Thiết kế automation n8n và SaaS connector. |
| `/wf-nocobase-plugin-expert` | Phân tích và phát triển plugin NocoBase. |
| `/wf-nocobase-plugin-build` | Build, package, deploy plugin NocoBase. |
| `/wf-ai-agent-builder` | Thiết kế LLM app, RAG, tool calling, memory. |
| `/wf-api-graphql-dev` | Thiết kế và implement API/GraphQL. |
| `/wf-context-data-eng` | Context engineering, RAG, data pipeline. |
| `/wf-database-eng` | Database design, migration, optimization. |
| `/wf-observability-eng` | Monitoring, tracing, dashboard, incident workflow. |
| `/wf-uipath-project` | UiPath end-to-end: analysis, plan, XAML, validation, handoff. |
| `/wf-gen-doc` | Tạo presentation PPTX từ tài liệu nguồn. |
| `/wf-finance-investment-analyst` | Phân tích đầu tư, valuation, thesis, report. |
| `/wf-finance-quant-researcher` | Quant research, data, signal, backtest-oriented analysis. |
| `/wf-finance-vc-analyst` | Phân tích startup/VC, market, traction, financials. |
| `/wf-finance-market-monitor` | Theo dõi thị trường, tin tức, sentiment, signal. |

## Brain Va Session Continuity

Brain là phần giúp agent không bắt đầu từ số 0 ở mỗi phiên.

| File | Chuc nang |
| --- | --- |
| `brain/project_context.json` | Metadata, tech stack, conventions, decisions, sprint state. |
| `brain/lifecycle.md` | Quy trình session: init, analysis, planning, work, quality gate, checkpoint, handoff. |
| `brain/default_skills.md` | Hướng dẫn dùng default skills trong mọi group. |
| `brain/skills_manifest.json` | Index nhẹ để agent tìm skill rồi lazy-load `SKILL.md` cần thiết. |
| `brain/agent_index.json` | Registry vai trò agent và protocol handoff. |
| `brain/platform_notes.md` | Lưu ý Windows/Linux/macOS. |
| `brain/workflow_sessions/` | Checkpoint workflow để resume sau khi context/chat bị ngắt. |

Luồng checkpoint:

```text
Start workflow
  -> đọc project_context.json
  -> kiểm tra workflow_sessions/*-latest.md
  -> resume hoặc start fresh
  -> kết thúc mỗi phase thì ghi checkpoint
  -> handoff ghi summary, open questions, next steps
```

Dùng CLI để quản trị brain và journal:

```bash
gkt brain --help
gkt journal --help
```

## MCP Va Code Graph

`gkt mcp` cấu hình MCP theo scope đã ghi bởi `gkt init`. Nếu không có `.gkt/state.json`, lệnh sẽ fallback sang `--all`.

```bash
gkt init cursor --group general-dev
gkt mcp
```

Các MCP/công cụ chính:

| Thanh phan | Chuc nang |
| --- | --- |
| Code Graph | Index cấu trúc code bằng Tree-sitter: symbols, imports, callers, dependencies. |
| FAISS Code Index | Semantic search cục bộ trên codebase. |
| Document Reader | Đọc PDF, DOCX, XLSX và nhiều định dạng tài liệu khác. |
| Brain Manager | Cho agent đọc/ghi project context, decisions, checkpoints. |

Lệnh liên quan:

```bash
gkt mcp
gkt graph --incremental
gkt watch
```

`gkt watch` chạy watcher để cập nhật graph và FAISS khi file thay đổi.

## CLI Reference

| Lenh | Chuc nang |
| --- | --- |
| `gkt init [target]` | Cài GravityKit cho IDE hoặc group. Mặc định là `all`. |
| `gkt init [target] --group <name>` | Cài một skill group cho target cụ thể. |
| `gkt groups` | Liệt kê skill groups, số skill, workflow, mô tả. |
| `gkt list` | Liệt kê workflow/agent command có sẵn. |
| `gkt doctor` | Kiểm tra Python, Node.js, Git, npm và `.agent/`. |
| `gkt update` | Cập nhật GravityKit từ GitHub hoặc pip. |
| `gkt version` | In version hiện tại. |
| `gkt brain ...` | Gọi script brain-manager. |
| `gkt journal ...` | Gọi script journal-manager. |
| `gkt graph ...` | Build code graph/FAISS và cấu hình MCP theo tham số. |
| `gkt mcp ...` | Cấu hình MCP theo scope init, tự thêm `--ensure-model`. |
| `gkt watch` | Watch file thay đổi và rebuild index incremental. |
| `gkt skills list [--all]` | Liệt kê skills đang active. |
| `gkt skills search <query>` | Tìm skill theo keyword. |
| `gkt skills enable <name>` | Enable skill đã disable. |
| `gkt skills disable <name>` | Disable skill. |
| `gkt skills count` | Đếm skills. |
| `gkt validate [--strict]` | Validate `SKILL.md`. |
| `gkt generate-index` | Regenerate `skills_index.json`. |

Alias:

```bash
gravitykit version
```

NPX:

```bash
npx gkt-node init antigravity --group general-dev
npx gkt-node groups
npx gkt-node mcp
```

## Huong Dan Su Dung Theo Tinh Huong

### Tao project phan mem moi

```bash
gkt init antigravity --group general-dev
gkt mcp
```

Trong AI chat:

```text
/wf-planner Turn this idea into a scoped PRD and implementation plan.
/wf-architect Design the system architecture and database schema.
/wf-fullstack-coder Implement the first vertical slice.
/wf-quality-guardian Review the result before release.
```

### Lam viec voi codebase lon

```bash
gkt init cursor --group general-dev
gkt mcp
gkt watch
```

Trong AI chat:

```text
/wf-knowledge-guide Explain the authentication and billing modules.
/wf-code-reviewer Review the current diff and identify regression risks.
```

### Viet tai lieu ky thuat

```bash
gkt init antigravity --group general-doc
```

Trong AI chat:

```text
/wf-doc-writer Rewrite the README and API guide for the SDK.
/wf-tech-writer Create ADRs for the database and deployment decisions.
```

### Tao presentation PPTX

```bash
gkt init kiro --group gen-doc
gkt mcp
```

Trong AI chat:

```text
/wf-gen-doc Generate an investor deck from these notes and source files.
```

### UiPath RPA

```bash
gkt init antigravity --group uipath
```

Trong AI chat:

```text
/wf-uipath-project Build an invoice processing automation from Outlook to ERP.
```

Luồng `/wf-uipath-project` bao gồm:

1. Business analysis và chọn kiến trúc.
2. Plan workflow tree, argument map, config keys.
3. Scaffold project, inspect UI, generate XAML, validate loop.
4. Final validation và handoff.

### Finance Research

```bash
gkt init antigravity --group finance
gkt mcp
```

Trong AI chat:

```text
/wf-finance-market-monitor Monitor market events and summarize material signals.
/wf-finance-investment-analyst Build an investment memo for this public company.
/wf-finance-vc-analyst Analyze this startup from a VC perspective.
```

## Phat Trien Va Dong Gop

Cài local editable:

```bash
git clone https://github.com/OrgGem/VibeGravityKit.git
cd VibeGravityKit
pip install -e .
gkt version
```

Validate skills:

```bash
gkt validate
gkt validate --strict
```

Regenerate index:

```bash
gkt generate-index
```

Build NPX assets:

```bash
cd packages/npx
npm install
npm run build
```

Thêm skill mới:

1. Tạo `GravityKit/.agent/skills/<skill-name>/SKILL.md`.
2. Thêm `references/`, `scripts/`, `assets/` nếu skill cần tài liệu hoặc tool phụ.
3. Gắn skill vào group phù hợp trong `GravityKit/data/skill_groups.json`.
4. Chạy `gkt validate` và `gkt generate-index`.
5. Nếu phát hành NPX, đồng bộ assets trong `packages/npx/assets/`.

Thêm workflow mới:

1. Tạo `GravityKit/.agent/workflows/wf-<name>.md`.
2. Dùng frontmatter có `description: "..."`.
3. Gắn workflow vào group phù hợp trong `GravityKit/data/skill_groups.json`.
4. Kiểm tra init theo group để đảm bảo workflow xuất hiện trong post-init guide.

## Phat Hanh

Package Python được publish trên PyPI với tên `gkt`.

Quy trình release:

```bash
# 1. Cap nhat version
notepad GravityKit/VERSION

# 2. Cap nhat CHANGELOG.md

# 3. Commit va tag
git tag v3.12.8
git push origin v3.12.8
```

GitHub Actions sẽ build package, kiểm tra bằng Twine và publish qua PyPI trusted publishing nếu project đã cấu hình OIDC.

## License

MIT
