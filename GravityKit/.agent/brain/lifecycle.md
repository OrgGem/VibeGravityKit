# Session Lifecycle

> Reference: See `default_skills.md` for the full list of 12 default skills always available.

## Init Phase
- Detect platform (Windows/Linux/macOS) → use `powershell-windows` or `bash-linux`
- Load `project_context.json` via `brain-manager` for project awareness
- Check `journal-manager` for recent decisions, lessons, and known issues
- Build codebase index via `codebase-navigator` if not cached

## Planning Phase
- Use `concise-planning` to break user request into atomic checklist
- For complex multi-step tasks, use `writing-plans` to create implementation plan
- Cross-reference `default_skills.md` to identify which skills to leverage
- Check platform compatibility via `platform_notes.md`

## Work Phase
- Follow `clean-code` principles throughout all code changes
- Use `codebase-navigator` to find relevant code without reading entire files
- Use `context-manager` to compress context when approaching token limits
- Use `debugger` proactively when encountering any error or unexpected behavior

## Checkpoint (after each significant change)
- Save decisions to `brain-manager`
- Log new lessons and insights to `journal-manager`
- Update `project_context.json` if architecture or conventions changed
- Commit with `git-manager` + `commit` (semantic commits)

## Handoff (session end)
- Export full context via `brain-manager`
- Write handoff notes in `journal-manager` with session summary
- Update `project_context.json` current_sprint status
- Create summary: work completed, known issues, next steps
