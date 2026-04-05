# Workflow Session Index

This directory stores **workflow session artifacts** — structured summaries saved at the end of each workflow phase. They act like compacted conversation context: a new AI session reads them to resume where the previous one left off.

## How it works

1. **First run**: Workflow creates `{workflow}-{YYYY-MM-DD}.md` at session start
2. **Each phase end**: Agent appends/updates the phase section with key outputs
3. **New session**: lifecycle.md instructs agent to check this directory first
4. **Resume**: Agent reads the latest session file, reports current phase, asks user "Continue or restart?"

## Session File Naming

```
{workflow-name}-{YYYY-MM-DD}.md        ← daily session file
{workflow-name}-latest.md              ← copy of the most recent session (always overwrite)
```

When multiple runs exist for the same workflow, `{workflow-name}-latest.md` always reflects the most recent.

## Session Artifact Format

```markdown
---
workflow: wf-{name}
project: {ProjectName}
session_date: YYYY-MM-DD
last_phase: "Phase N — {Phase Title}"
status: in_progress | completed | paused
---

# Session: wf-{name} — {ProjectName}
**Date:** YYYY-MM-DD  
**Status:** {In Progress (paused at Phase N) | Completed}

## Project Summary
{2–3 sentences: what is being built/automated and why}

## Key Decisions
- {decision 1}: {brief rationale}
- {decision 2}: {brief rationale}

## Phase 0 — {Title} {✅ | 🔄 | ⬜}
**Input:** {what the user requested}
**Output:** {what was clarified/decided}

## Phase 1 — {Title} {✅ | 🔄 | ⬜}
**Key outputs:** {bullet summary of artifacts produced}
**Decisions:** {architecture/approach chosen + reason}

## Phase N — {Title} {✅ | 🔄 | ⬜}
**Progress:**
- [x] {completed sub-task}
- [ ] {in-progress sub-task} ← current
**Artifacts created:** {file paths}
**Open issues:** {list}

## Open Questions
- [ ] {unanswered question for user/stakeholder}

## Next Steps
- {immediate next action to take when resuming}
- {follow-up}
```

## Status Icons
- `✅` Phase complete
- `🔄` Phase in progress (current)
- `⬜` Phase not started

## Active Sessions

<!-- Agent: update this table when creating or completing sessions -->

| Workflow | Project | Date | Phase | Status |
|---|---|---|---|---|
| _(none yet)_ | | | | |
