# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
