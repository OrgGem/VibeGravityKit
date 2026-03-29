# Default Skills Reference

This file documents the 12 default skills that are auto-installed with every GravityKit group.
Agents should use these skills proactively to maintain quality, consistency, and cross-platform compatibility.

## Memory & Context Skills

### brain-manager
- **Purpose**: Export/import decisions, architecture notes, and project context
- **Use when**: Starting a session (load context), ending a session (save context), making architecture decisions
- **Integration**: Reads/writes `project_context.json` and decisions log in `brain/`

### journal-manager
- **Purpose**: 2-tier knowledge journal for capturing lessons, bugs, and insights
- **Use when**: Discovering a bug pattern, learning a project convention, recording a workaround
- **Integration**: Maintains index + entries in `brain/journal/`

### context-manager
- **Purpose**: Minify and control context to save tokens
- **Use when**: Working with large codebases, long sessions, or hitting context limits
- **Integration**: Compresses context before handoff to other agents

### codebase-navigator
- **Purpose**: Index and search code quickly (Token Saver)
- **Use when**: Need to find functions, classes, or patterns without reading entire files
- **Integration**: Builds searchable index of the codebase

## Planning & Quality Skills

### concise-planning
- **Purpose**: Generate clear, actionable, atomic checklists for coding tasks
- **Use when**: Before starting any feature implementation or refactoring
- **Integration**: Creates structured task breakdown with verification criteria

### writing-plans
- **Purpose**: Structured task planning with dependencies and verification
- **Use when**: Multi-step work that requires spec-to-implementation mapping
- **Integration**: Produces implementation plans with clear phase gates

### clean-code
- **Purpose**: Enforce clean code principles and best practices
- **Use when**: Writing new code, refactoring, or reviewing PRs
- **Integration**: Applied as a continuous quality check during development

### debugger
- **Purpose**: Debugging specialist for errors, test failures, and unexpected behavior
- **Use when**: Any error, test failure, or unexpected behavior encountered
- **Integration**: Use proactively before proposing fixes

## Version Control Skills

### git-manager
- **Purpose**: Semantic commits and branch strategy
- **Use when**: Creating branches, writing commit messages, managing git workflow
- **Integration**: Enforces conventional commits format

### commit
- **Purpose**: Git commit best practices
- **Use when**: Staging and committing changes
- **Integration**: Validates commit message format and scope

## Cross-Platform Skills

### powershell-windows
- **Purpose**: PowerShell patterns, critical pitfalls, error handling
- **Use when**: Running commands on Windows, writing Windows-compatible scripts
- **Integration**: Prevents common PowerShell mistakes (operator syntax, path handling)

### bash-linux
- **Purpose**: Bash/Linux terminal patterns, piping, scripting
- **Use when**: Running commands on Linux/macOS, writing shell scripts
- **Integration**: Provides defensive scripting patterns

## Workflow Integration Guide

When building or optimizing workflows, agents should reference these default skills to:

1. **Session Start**: Use `brain-manager` to load previous context, check `journal-manager` for recent lessons
2. **Planning Phase**: Use `concise-planning` to break down the task, `writing-plans` for complex multi-step work
3. **Implementation**: Use `clean-code` as a quality gate, `codebase-navigator` to find relevant code quickly
4. **Debugging**: Use `debugger` proactively when any issue is encountered
5. **Commit**: Use `git-manager` + `commit` for semantic commits
6. **Platform**: Check `powershell-windows` or `bash-linux` before running platform-specific commands
7. **Session End**: Use `brain-manager` to export context, `journal-manager` to log lessons learned

## How to Reference in Workflows

Workflow files (.md) can reference default skills using:
```
@skill[brain-manager] - Load project context before starting
@skill[concise-planning] - Break down task into atomic checklist
@skill[debugger] - Debug any errors encountered
```

These skills are always available regardless of which group was installed.
