---
name: brain-manager
description: Manage your project's brain — export/import decisions, architecture notes, and project context.
---

# Brain Manager

Manages the `.agent/brain/` directory — your project's persistent memory. It stores architecture decisions, tech stack choices, conventions, and lessons learned so AI agents always have context.

## Usage

This skill provides an **MCP Server** that exposes tools directly to the agent. You do not need to run CLI commands anymore. Simply call these tools when managing project context:

1. `get_brain_context()`: Reads the current project stack, decisions, and conventions.
2. `add_architecture_decision(decision, rationale, category)`: Logs a new decision.
3. `update_project_context(key_path, value)`: Updates project metadata (e.g., `project.description` or `architecture.database`).
4. `save_workflow_checkpoint(workflow_name, phase, content)`: Saves a complex workflow session so you can resume later.
5. `load_workflow_checkpoint(workflow_name)`: Loads the latest session artifact to resume work.

## Files

| File | Purpose |
|------|---------|
| `brain/project_context.json` | Core project metadata and settings |
| `brain/decisions.jsonl` | Architecture Decision Records (ADR) |
| `brain/conventions.md` | Coding conventions and style guide |

## How AI Agents Use It

When an agent starts working, it reads `project_context.json` to understand:
- What tech stack is used
- What patterns/conventions to follow
- Past decisions and their rationale
- Known issues to avoid

---

## Workflow Session Checkpoints

Workflows save structured session artifacts to `brain/workflow_sessions/` so work can be resumed across sessions. This is the primary mechanism for **cross-session continuity** in GravityKit.

### Checkpoint Protocol — How to save

At the end of each workflow phase, the agent writes or updates two files:

**1. Dated session file** — `brain/workflow_sessions/{workflow-name}-{YYYY-MM-DD}.md`  
**2. Latest pointer** — `brain/workflow_sessions/{workflow-name}-latest.md` (overwrite each time)

The session artifact format is defined in `brain/workflow_sessions/SESSIONS.md`.

### Checkpoint Protocol — Minimal example

```markdown
---
workflow: wf-uipath-project
project: InvoiceAutomation
session_date: 2024-01-15
last_phase: "Phase 2 — Kế hoạch triển khai"
status: in_progress
---

# Session: wf-uipath-project — InvoiceAutomation
**Date:** 2024-01-15  
**Status:** In Progress (Phase 2 complete, Phase 3 not started)

## Project Summary
Automate invoice extraction from email and entry into SAP. Runs daily at 08:00.
Uses REFramework Performer with Orchestrator queue.

## Key Decisions
- Architecture: REFramework Performer — high volume (200+ invoices/day), needs per-item retry
- Apps: Outlook (email), SAP (ERP entry)

## Phase 1 — Business Analysis ✅
**Key Business Points:** 200 invoices/day, 3 clerks, 2h manual effort → target 15min automated
**Architecture selected:** REFramework Performer (1 project)

## Phase 2 — Plan ✅
**Workflow tree:** see `/tmp/project-tree.md`
**Dev Sequence:** A→E planned, A1–A2 complete

## Open Questions
- [ ] SAP credentials: stored in Orchestrator Assets or Config.xlsx?

## Next Steps
- Start Phase 3: scaffold project with `scaffold_project.py --variant performer`
```

### Checkpoint Protocol — Resume check

At session start, before running any phase:

```
1. Check: does brain/workflow_sessions/{workflow-name}-latest.md exist?
2. If YES → read it → output:
   "📋 Found session: [ProjectName] — paused at [last_phase]
    Resume from that point, or restart from Phase 0? (resume/restart)"
3. If user says resume → skip completed phases (✅), start from 🔄
4. If user says restart → rename existing file to {workflow}-{date}-archived.md
```

### Update SESSIONS.md index

After creating or completing a session, update the Active Sessions table in `brain/workflow_sessions/SESSIONS.md`.

## IDE Configuration

This MCP Server is automatically configured by `gkt mcp`. If you need to manually register it:

```json
{
  "mcpServers": {
    "brain-manager": {
      "command": "python",
      "args": [
        ".agent/skills/brain-manager/scripts/brain_mcp_server.py"
      ]
    }
  }
}
```
