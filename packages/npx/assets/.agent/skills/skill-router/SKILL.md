---
name: skill-router
description: "MCP server that intelligently routes agent requests to the correct skills and workflows. Install all skills without group separation — the router guides which skill to use."
---

# Skill Router — Intelligent Skill Dispatch MCP

## Purpose
When **all skills** are installed without group separation, agents face ~210+ skills with no guidance on which to use. The Skill Router MCP server solves this by providing:

1. **Intent-based routing** — Agent describes a task, router returns the most relevant skills + workflows
2. **Cross-group awareness** — Knows which skills belong to which groups and suggests complementary skills
3. **Workflow suggestion** — Recommends the right `/wf-*` workflow to orchestrate the task
4. **Execution plan** — Returns an ordered list of skills with rationale

## MCP Tools Provided

### `route_task`
Given a natural-language task description, returns the top matching skills and workflows.

### `get_skill_info`
Returns detailed info about a specific skill (description, category, group memberships).

### `get_group_skills`
Returns all skills and workflows for a named group.

### `suggest_workflow`
Given a task type, suggests the best workflow to use.

### `list_groups`
Lists all available skill groups with descriptions.

## Setup
The MCP server is automatically registered by `gkt mcp` or can be manually added to `.mcp.json`:

```json
{
  "skill-router": {
    "command": "python",
    "args": [".agent/skills/skill-router/scripts/skill_router_mcp.py"],
    "env": {},
    "disabled": false
  }
}
```

## When to Use
- **Always at conversation start** — Agent should call `route_task` to determine which skills are relevant
- **Before reading any SKILL.md** — Check if a skill is actually needed
- **When switching context** — Re-route if the task changes mid-conversation
