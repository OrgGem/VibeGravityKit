# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.7.0] - 2026-03-30

### Added

- **Post-init Workflow Guide** — After `gkt init <group>`, displays a formatted table of all installed workflows with descriptions and sample prompts to help new users get started immediately.
- Sample prompt database for all 41 workflows (used in post-init display)

### Changed

- **Workflow `wf-` Prefix** — All 41 workflow files renamed with `wf-` prefix (e.g., `leader.md` → `wf-leader.md`) to enable easy filtering in IDE command menus. Type `/wf-` to filter only workflows.
- Updated all cross-references (`@[/xxx]` → `@[/wf-xxx]`) across 7 workflow files, 12 IDE adapter files, and 1 skill file
- Updated `skill_groups.json` — all 21 groups now reference `wf-` prefixed workflow names
- Updated CLI and NPX init output hints to use `wf-` prefixed names
- Bumped NPX package version to 3.7.0

## [3.6.0] - 2026-03-30

### Added

- **Gravity Requirement Analysis** (`gravity-requirement-analysis`) — Toggleable BMAD-inspired requirement analysis with auto-complexity detection, targeted elicitation, structured plan creation, and task tracking. Configurable via `project_context.json` to save tokens when not needed.
- **Gravity Adversarial Review** (`gravity-adversarial-review`) — Dual-mode quality review combining cynical adversarial analysis (10+ issue categories) with exhaustive edge-case path enumeration. Adapted from BMAD's review skills.
- **Gravity Implementation Readiness** (`gravity-implementation-readiness`) — Pre-implementation gate that validates requirement completeness, plan coverage, dependency order, and architecture decisions before coding begins.
- Requirement analysis templates: `requirement.md`, `plan.md`, `complexity-matrix.md`
- `requirement_analysis` toggle config in `project_context.json` with `enabled`, `auto_detect`, `complexity_threshold` settings
- New Requirement Analysis Phase and Quality Gate Phase in session lifecycle
- Added `user-story-generator`, `task-estimator`, `strategic-planning-advisor`, `architecture` to `general-dev` group
- Added `competitor-analyzer`, `market-trend-analyst`, `product-manager-toolkit`, `pricing-strategy`, `app-store-optimization` to `research` group
- Added `planner`, `qa-engineer`, `code-reviewer` workflows to `nocobase-dev` group
- Added `solution-architect` workflow to `general-dev` group
- Added `planner`, `meta-thinker` workflows to `research` group

### Changed

- Updated `lifecycle.md` with Requirement Analysis Phase (toggleable) and Quality Gate Phase
- Updated `default_skills.md` with documentation for 3 new gravity skills and toggle guide
- Updated skill counts: `general-dev` (27→34), `research` (18→25), `nocobase-dev` (24→30)

## [3.1.0] - 2026-02-18

### Added

- n8n Automator workflow for building n8n workflows with Code nodes and 70+ SaaS connectors
- NocoBase Plugin Expert workflow for full-stack plugin development
- NocoBase Plugin Build workflow for compiling and packaging plugins
- Translator workflow for multi-language translation and i18n
- Image Creator workflow for AI image generation and visual content
- Doc Writer workflow for professional technical documentation
- Research Analyst workflow for deep research with file I/O and image generation
- Deep Researcher workflow for comprehensive research and report writing
- Prompt Engineer workflow for creating optimized prompts
- Release Manager workflow for changelog generation and version management
- 886 skills across 17 categories (Azure, AI/LLM, Security, DevOps, Frontend, etc.)
- `pyproject.toml` for modern PEP 517/518 packaging (installable via `pip install gk`)
- GitHub Actions workflow for automated PyPI publishing

### Changed

- Modernized package structure from `setup.py` to `pyproject.toml`
- Updated `.gitignore` with proper Python packaging ignores

## [3.0.0] - 2025-12-01

### Added

- Initial public release
- 29 agent workflows (leader, quickstart, planner, architect, designer, etc.)
- Multi-IDE support: Antigravity, Cursor, Windsurf, Cline
- CLI commands: `gk init`, `gk list`, `gk doctor`, `gk update`, `gk version`
- Skills management: `gk skills list/search/enable/disable/count`
- Brain and journal management commands
