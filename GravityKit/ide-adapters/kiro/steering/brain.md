---
inclusion: always
---

# Brain & Session Context

## At the start of every session

1. **Load project context**: Read `.kiro/brain/project_context.json`
   - Understand the tech stack, architecture pattern, conventions, and known issues
   - If the file is empty (fresh project), ask the user to fill in key details

2. **Check for in-progress workflow sessions**: List files in `.kiro/brain/workflow_sessions/`
   - If any `{workflow-name}-latest.md` exists → read it and report:
     ```
     📋 Found session: [ProjectName] — paused at [last_phase]
     Resume from that point, or restart? (resume/restart)
     ```
   - User says **resume** → skip completed phases (✅), start from current phase (🔄)
   - User says **restart** → rename old file to `{name}-{date}-archived.md`

3. **Check journal**: Read `.kiro/brain/journal/` for recent lessons and known bugs

## Saving checkpoints during workflows

At the end of each workflow phase, write/update:
- `.kiro/brain/workflow_sessions/{workflow-name}-{YYYY-MM-DD}.md` — dated artifact
- `.kiro/brain/workflow_sessions/{workflow-name}-latest.md` — always overwrite with latest

See `.kiro/brain/workflow_sessions/SESSIONS.md` for the checkpoint format.

## Key brain files

| File | Purpose |
|------|---------|
| `.kiro/brain/project_context.json` | Project metadata, architecture decisions, conventions |
| `.kiro/brain/workflow_sessions/` | Per-workflow session artifacts for cross-session resume |
| `.kiro/brain/journal/` | Lessons learned, bug patterns, workarounds |
| `.kiro/brain/lifecycle.md` | Session phases and quality gates |
