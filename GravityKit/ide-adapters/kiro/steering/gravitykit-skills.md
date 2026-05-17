---
inclusion: always
---

# GravityKit Skill Usage

GravityKit installs workspace skills in `.kiro/skills/`. Treat these installed
workspace skills as the primary source of task-specific guidance before relying
on generic model knowledge.

## Skill discovery protocol

At the start of every non-trivial task:

1. Identify the likely task domains from the user's request, referenced files,
   active workflow, and project context.
2. Check for relevant installed workspace skills before planning or editing.
   Prefer Kiro's automatic skill activation or slash-command skill activation
   when a matching skill is available.
3. If no skill auto-activates, search installed skills manually by inspecting
   `.kiro/skills/*/SKILL.md` frontmatter and descriptions, or use the
   `skill-router` MCP tools when they are configured by `gkt mcp`.
4. Read the full `SKILL.md` for each relevant skill before applying that
   domain guidance. Load `references/`, `scripts/`, or `assets/` only when the
   skill instructions or task require them.
5. Prefer workspace skills in `.kiro/skills/` over global skills in
   `~/.kiro/skills/` and over ad-hoc approaches.
6. Do not load every installed skill into context. Use progressive disclosure:
   discover by name and description first, then load only the skills needed for
   the current task.

## Workflow requests

When the user invokes a GravityKit workflow such as `/wf-planner` or
`/wf-backend-dev`, first read the matching file from `.kiro/specs/<workflow>.md`.
Then select and load any installed skills that the workflow or task requires.

## Fallbacks

If `.kiro/skills/` is absent because the project was initialized in minimal
mode, use the `skill-router` MCP server when available. If neither local skills
nor `skill-router` are available, continue with the installed brain and steering
context, and state briefly that no matching installed skill was available.
