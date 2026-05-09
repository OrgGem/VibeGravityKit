# Changelog

All notable changes to GravityKit are documented here.

The format follows Keep a Changelog, and the project uses Semantic Versioning.

## [Unreleased]

### Changed

- Rewrote the root `README.md` into a system usage guide focused on installation, skill flow, agent/workflow behavior, brain continuity, MCP usage, CLI reference, and common operating scenarios.
- Simplified `CHANGELOG.md` so it records release history only, avoiding duplicated usage documentation already covered by the README.

## [3.12.7] - 2026-05-09

### Changed

- Current package version recorded in `GravityKit/VERSION`.

## [3.9.1] - 2026-04-17

### Changed

- Improved `gkt init` help output with clearer IDE and group use cases.
- Added post-init workflow suggestions so users can see relevant `/wf-*` commands immediately after setup.

## [3.9.0] - 2026-04-16

### Added

- Added the `gen-doc` skill group for AI-assisted Markdown/source-material to PPTX generation.
- Added `/wf-gen-doc` as the workflow entry point for document generation.
- Added dependency-resolution guidance for the document generation pipeline.

## [3.8.1] - 2026-04-05

### Added

- Added `/wf-uipath-project` as the end-to-end UiPath RPA project workflow.
- Added `ARCHITECTURE.md` with a high-level explanation of GravityKit components and install flow.
- Refined Copilot and Kiro adapter instructions for better agent coordination.

### Changed

- Updated the `uipath` group to include the new project workflow.
- Regenerated skill indexes for the updated workflow set.

## [3.8.0] - 2026-04-05

### Added

- Added the UiPath RPA suite:
  - `/wf-uipath-analyst`
  - `/wf-uipath-developer`
  - `/wf-uipath-reviewer`
  - `/wf-uipath-deploy`
- Added UiPath skills for XAML generation, REFramework, coded workflows, Orchestrator, AI agents, and shared UiPath guidance.
- Added additional development, observability, frontend, security, and web-search skills.

### Changed

- Updated skill indexes and NPX assets for the UiPath group.

## [3.7.1] - 2026-04-04

### Changed

- Maintenance release and dependency updates.

## [3.7.0] - 2026-03-30

### Added

- Added post-init workflow guide showing installed workflows, descriptions, and sample prompts.
- Added sample prompt metadata for workflow display.

### Changed

- Standardized workflow filenames and slash commands with the `wf-` prefix.
- Updated workflow references across group definitions, adapter files, and CLI/NPX hints.
- Bumped NPX package version to `3.7.0`.

## [3.6.0] - 2026-03-30

### Added

- Added `gravity-requirement-analysis` for structured requirement analysis, complexity detection, planning, and task tracking.
- Added `gravity-adversarial-review` for quality review and edge-case analysis.
- Added `gravity-implementation-readiness` as a pre-implementation gate for complex work.
- Added requirement analysis templates and lifecycle support.
- Expanded `general-dev`, `research`, and `nocobase-dev` with additional planning, analysis, architecture, and QA skills/workflows.

### Changed

- Updated lifecycle guidance with requirement analysis and quality gate phases.
- Updated default skill documentation with the new Gravity planning/review skills.

## [3.1.0] - 2026-02-18

### Added

- Added workflows for n8n, NocoBase, translation, image generation, documentation, research, prompt engineering, and release management.
- Added a broad skill library across AI/LLM, security, DevOps, frontend, backend, docs, and automation categories.
- Migrated packaging to modern `pyproject.toml`.
- Added GitHub Actions publishing workflow.

### Changed

- Modernized package structure from `setup.py` to `pyproject.toml`.
- Updated `.gitignore` for Python packaging outputs.

## [3.0.0] - 2025-12-01

### Added

- Initial public release.
- Added the first workflow set for planning, architecture, design, development, QA, security, docs, and release operations.
- Added multi-IDE support for Antigravity, Cursor, Windsurf, and Cline.
- Added core CLI commands for init, listing, doctor, update, version, skill management, brain, and journal operations.
