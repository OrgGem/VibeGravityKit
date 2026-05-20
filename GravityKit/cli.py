#!/usr/bin/env python3
import click
import os
import sys
import re
import json
import shutil
import subprocess as sp
from collections import Counter
from pathlib import Path

# Fix Unicode encoding on Windows (cp1252 cannot render emoji)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # Fail silently if stream doesn't support reconfigure

# Get the absolute path to the GravityKit source directory
# This assumes cli.py is in the root of the repo
SOURCE_ROOT = Path(__file__).resolve().parent

# IDE names that are valid targets for init
IDE_NAMES = {"antigravity", "cursor", "windsurf", "cline", "kilocode", "copilot", "kiro", "codex", "all"}

# Map a `gkt init` target to the IDE names understood by setup_mcp.py.
# Cline / Kilocode / Copilot don't have native MCP config files; they ride on
# the .agent/.mcp.json that `gkt init` auto-installs alongside their adapter,
# so they map to the antigravity MCP entry.
INIT_TO_MCP_IDES = {
    "antigravity": ["antigravity"],
    "kiro": ["kiro"],
    "cursor": ["cursor"],
    "windsurf": ["windsurf"],
    "cline": ["antigravity"],
    "kilocode": ["antigravity"],
    "copilot": ["antigravity"],
    "codex": ["codex"],
    # `all` is expanded by reading the install targets actually used.
}

# Where init records its scope so `gkt mcp` can install MCP only for the
# IDE/CLI the user actually opted into.
INIT_STATE_FILE = Path(".gkt") / "state.json"


# Sample prompts for common workflow types (used in post-init display)
WORKFLOW_SAMPLE_PROMPTS = {
    "wf-leader": "Build a SaaS app for task management with auth and billing",
    "wf-quickstart": "I want to create a landing page for my startup",
    "wf-planner": "Analyze requirements and create PRD for an e-commerce platform",
    "wf-architect": "Design the database schema and API for a booking system",
    "wf-designer": "Create a modern design system with dark mode support",
    "wf-frontend-dev": "Build the React dashboard with charts and user settings",
    "wf-backend-dev": "Implement REST API with auth, CRUD, and file upload",
    "wf-fullstack-coder": "Build a full-stack todo app with Next.js and PostgreSQL",
    "wf-mobile-dev": "Create a React Native app with push notifications",
    "wf-qa-engineer": "Write test cases and run E2E tests for the login flow",
    "wf-code-reviewer": "Review my latest changes for security and best practices",
    "wf-security-engineer": "Run a security audit on the authentication module",
    "wf-security-auditor": "Audit the codebase for OWASP top 10 vulnerabilities",
    "wf-devops": "Setup Docker and CI/CD pipeline for production deployment",
    "wf-cloud-deployer": "Deploy the app to AWS with auto-scaling and monitoring",
    "wf-doc-writer": "Generate API documentation and developer guides",
    "wf-tech-writer": "Write technical docs for the SDK integration",
    "wf-deep-researcher": "Research the latest trends in AI agent frameworks",
    "wf-researcher": "Analyze the competitive landscape for project management tools",
    "wf-research-analyst": "Create a market analysis report for fintech in SEA",
    "wf-meta-thinker": "I have a vague idea about a social app — help me shape it",
    "wf-prompt-engineer": "Optimize this prompt for better code generation results",
    "wf-n8n-automator": "Build an n8n workflow to sync Slack messages to Notion",
    "wf-nocobase-plugin-expert": "Create a NocoBase plugin for document management",
    "wf-nocobase-plugin-build": "Build and deploy my NocoBase plugin to production",
    "wf-seo-specialist": "Optimize my website for search engines",
    "wf-seo-marketer": "Create an SEO content strategy for my blog",
    "wf-solution-architect": "Design a microservices architecture for our platform",
    "wf-image-creator": "Generate marketing screenshots and visual assets",
    "wf-release-manager": "Generate changelog and prepare v2.0 release",
    "wf-quality-guardian": "Run a comprehensive quality check on the codebase",
    "wf-knowledge-guide": "Explain how the authentication module works",
    "wf-translator": "Translate the app UI to Vietnamese and Japanese",
    "wf-observability-eng": "Setup monitoring with Grafana and Prometheus",
    "wf-api-graphql-dev": "Design and implement a GraphQL API with subscriptions",
    "wf-claude-code-dev": "Build a custom MCP tool for database queries",
    "wf-context-data-eng": "Build a RAG pipeline with vector search",
    "wf-database-eng": "Design a PostgreSQL schema with migrations and CQRS",
    "wf-startup-advisor": "Create a business plan for my SaaS startup",
    "wf-saas-connector": "Integrate HubSpot CRM with our backend via API",
    "wf-ai-agent-builder": "Build an AI agent with tool calling and memory",
}


def get_workflow_info(workflows_dir, workflow_names):
    """Read workflow .md files and extract description from frontmatter."""
    results = []
    for wf_name in workflow_names:
        wf_file = workflows_dir / f"{wf_name}.md"
        description = "No description available."
        if wf_file.exists():
            try:
                with open(wf_file, "r", encoding="utf-8") as f:
                    content = f.read(500)  # Only read first 500 chars for frontmatter
                match = re.search(r"description:\s*(.+)", content)
                if match:
                    description = match.group(1).strip()
            except Exception:
                pass
        sample = WORKFLOW_SAMPLE_PROMPTS.get(wf_name, "Help me with this task")
        # Extract short role from description (before the dash)
        parts = description.split(" - ", 1)
        role = parts[0] if len(parts) > 1 else description[:40]
        detail = parts[1] if len(parts) > 1 else ""
        results.append({
            "name": wf_name,
            "role": role,
            "detail": detail,
            "description": description,
            "sample": sample,
        })
    return results


def show_group_workflows(workflows_dir, workflow_names):
    """Display a formatted guide of workflows after init."""
    infos = get_workflow_info(workflows_dir, workflow_names)
    if not infos:
        return

    click.echo(f"\n📋 Available Workflows ({len(infos)}):\n")
    click.echo(f"{'Workflow':<30} {'Purpose & Features'}")
    click.echo("─" * 90)

    for info in infos:
        slash_name = f"/{info['name']}"
        # Print full description, wrapping or taking a larger slice
        click.echo(f"  {slash_name:<28} {info['description'][:80]}")

    click.echo(f"\n💡 How to use — type the workflow name in your AI chat:\n")
    # Show up to 3 sample prompts
    shown = 0
    for info in infos:
        if shown >= 3:
            break
        click.echo(f"  📎 {info['name']}")
        click.echo(f"     Prompt: \"{info['sample']}\"")
        click.echo("")
        shown += 1

    click.echo(f"  💬 Tip: Type /wf- to filter only workflows in the / menu.")


def get_default_skills(skill_groups):
    """Get the list of default skills from _default group."""
    default_group = skill_groups.get("_default", {})
    return default_group.get("skills", [])


def load_skill_groups():
    """Load skill group definitions from data/skill_groups.json."""
    groups_file = SOURCE_ROOT / "data" / "skill_groups.json"
    if not groups_file.exists():
        return {}
    with open(groups_file, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_group_skills(group_config, default_skills=None):
    """Return group skills plus defaults, preserving order and removing duplicates."""
    all_skills = []
    for skill_name in group_config.get("skills", []):
        if skill_name not in all_skills:
            all_skills.append(skill_name)
    for skill_name in default_skills or []:
        if skill_name not in all_skills:
            all_skills.append(skill_name)
    return all_skills


def split_existing_skills(skills_src, skill_names):
    existing = []
    missing = []
    for skill_name in skill_names:
        skill_dir = skills_src / skill_name
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            existing.append(skill_name)
        else:
            missing.append(skill_name)
    return existing, missing


def warn_missing(label, names, limit=10):
    if not names:
        return
    shown = ", ".join(names[:limit])
    suffix = f", ... +{len(names) - limit} more" if len(names) > limit else ""
    click.echo(f"  Warning: {len(names)} configured {label} not found: {shown}{suffix}")


def run_python_script(script, args=None):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = sp.run([sys.executable, str(script), *(args or [])], env=env)
    if result.returncode:
        sys.exit(result.returncode)


PROJECT_SCAN_EXCLUDE_DIRS = {
    ".git", ".agent", ".kiro", ".code-graph-index", ".gkt",
    ".venv", "venv", "env", "node_modules", "__pycache__",
    "dist", "build", ".next", ".nuxt", ".turbo", ".cache",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "coverage", ".coverage", "htmlcov", ".idea", ".vscode",
}

LANGUAGE_BY_EXT = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript/React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".md": "Markdown",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".sql": "SQL",
    ".xaml": "XAML",
}


def _safe_read_text(path: Path, limit: int = 80000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _strip_frontmatter(text: str) -> str:
    stripped = text.lstrip("\ufeff")
    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def _kiro_steering_needs_load(path: Path) -> bool:
    if not path.exists():
        return True
    body = _strip_frontmatter(_safe_read_text(path))
    if "<!--" in body and "-->" in body:
        return True
    visible = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    meaningful = [
        line.strip()
        for line in visible.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return not meaningful


def _first_existing(root: Path, names: list[str]):
    for name in names:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def _readme_summary(root: Path):
    readme = _first_existing(root, ["README.md", "readme.md", "Readme.md"])
    if not readme:
        return None, None
    text = _safe_read_text(readme)
    title = None
    paragraphs: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not title and line.startswith("# "):
            title = line[2:].strip(" #")
            continue
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if (
            line.startswith("#")
            or line.startswith("[!")
            or line.startswith("![")
            or line.startswith("<")
            or line.startswith("|")
            or line.startswith("```")
        ):
            continue
        current.append(re.sub(r"\s+", " ", line))
        if len(" ".join(current)) > 500:
            break
    if current:
        paragraphs.append(" ".join(current))
    summary = paragraphs[0] if paragraphs else None
    return title, summary


def _parse_pyproject_fields(path: Path) -> dict:
    text = _safe_read_text(path)
    if not text:
        return {}
    out = {}
    for key in ("name", "description"):
        match = re.search(rf"(?m)^\s*{key}\s*=\s*['\"]([^'\"]+)['\"]", text)
        if match:
            out[key] = match.group(1).strip()
    out["raw"] = text.lower()
    return out


def _walk_project_files(root: Path, max_files: int = 2500) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [
            d for d in dirnames
            if d not in PROJECT_SCAN_EXCLUDE_DIRS
            and not (d.startswith(".") and d not in {".github"})
        ]
        for filename in filenames:
            if filename.endswith((".pyc", ".pyo", ".lock")):
                continue
            try:
                files.append((current / filename).relative_to(root))
            except ValueError:
                continue
            if len(files) >= max_files:
                return files
    return files


def _top_level_dirs(root: Path) -> list[Path]:
    out = []
    try:
        for item in root.iterdir():
            if not item.is_dir():
                continue
            if item.name in PROJECT_SCAN_EXCLUDE_DIRS:
                continue
            if item.name.startswith(".") and item.name != ".github":
                continue
            out.append(item.relative_to(root))
    except OSError:
        return []
    return sorted(out, key=lambda p: p.as_posix().lower())


def _add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _detect_frameworks(root: Path, package_json: dict, pyproject: dict, files: list[Path]) -> list[str]:
    frameworks: list[str] = []
    deps = {}
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        value = package_json.get(key, {})
        if isinstance(value, dict):
            deps.update({str(k).lower(): v for k, v in value.items()})
    dep_names = set(deps)
    dep_map = {
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "svelte": "Svelte",
        "vite": "Vite",
        "tailwindcss": "Tailwind CSS",
        "express": "Express",
        "fastify": "Fastify",
        "@nestjs/core": "NestJS",
        "prisma": "Prisma",
        "drizzle-orm": "Drizzle ORM",
        "playwright": "Playwright",
        "vitest": "Vitest",
        "jest": "Jest",
    }
    for dep, label in dep_map.items():
        if dep in dep_names:
            _add_unique(frameworks, label)
    if any(name.startswith("@angular/") for name in dep_names):
        _add_unique(frameworks, "Angular")

    raw_pyproject = pyproject.get("raw", "")
    py_map = {
        "click": "Click CLI",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "sqlalchemy": "SQLAlchemy",
        "pydantic": "Pydantic",
        "pytest": "pytest",
        "pyyaml": "PyYAML",
        "requests": "Requests",
    }
    for token, label in py_map.items():
        if token in raw_pyproject:
            _add_unique(frameworks, label)

    file_names = {p.name.lower() for p in files}
    if "pyproject.toml" in file_names:
        _add_unique(frameworks, "Python packaging")
    if "package.json" in file_names:
        _add_unique(frameworks, "Node.js package")
    if any(p.name.lower().startswith("next.config") for p in files):
        _add_unique(frameworks, "Next.js")
    if any(p.name.lower().startswith("vite.config") for p in files):
        _add_unique(frameworks, "Vite")
    if any(p.name.lower().startswith("tailwind.config") for p in files):
        _add_unique(frameworks, "Tailwind CSS")
    if (root / "GravityKit" / "cli.py").exists():
        _add_unique(frameworks, "Click CLI")
    return frameworks


def _detect_infrastructure(files: list[Path]) -> list[str]:
    infra: list[str] = []
    names = {p.name.lower() for p in files}
    if any(name == "dockerfile" or name.startswith("dockerfile.") for name in names):
        _add_unique(infra, "Docker")
    if any(name.startswith("docker-compose") for name in names):
        _add_unique(infra, "Docker Compose")
    if any(p.parts[:2] == (".github", "workflows") for p in files if len(p.parts) >= 2):
        _add_unique(infra, "GitHub Actions")
    if "vercel.json" in names:
        _add_unique(infra, "Vercel")
    if "netlify.toml" in names:
        _add_unique(infra, "Netlify")
    if any(p.suffix == ".tf" for p in files):
        _add_unique(infra, "Terraform")
    if any(part in {"k8s", "kubernetes"} for p in files for part in p.parts):
        _add_unique(infra, "Kubernetes manifests")
    return infra


def _directory_purpose(path: Path) -> str:
    name = path.name
    known = {
        "src": "Application source code",
        "app": "Application source or route tree",
        "pages": "Page routes",
        "components": "Reusable UI components",
        "tests": "Automated tests",
        "test": "Automated tests",
        "docs": "Documentation",
        "scripts": "Automation and helper scripts",
        "data": "Structured data and catalog metadata",
        "lib": "Shared library code",
        "packages": "Workspace packages or distributable subpackages",
        "public": "Static public assets",
        "assets": "Static assets and templates",
        "GravityKit": "GravityKit Python package source",
        "build": "Build artifacts",
        "dist": "Distribution artifacts",
    }
    return known.get(name, "Project directory")


def _collect_project_profile(root: Path) -> dict:
    files = _walk_project_files(root)
    language_counts = Counter()
    for rel in files:
        language = LANGUAGE_BY_EXT.get(rel.suffix.lower())
        if language:
            language_counts[language] += 1

    package_json = _safe_read_json(root / "package.json")
    pyproject = _parse_pyproject_fields(root / "pyproject.toml")
    readme_title, readme_summary = _readme_summary(root)

    project_name = (
        pyproject.get("name")
        or package_json.get("name")
        or readme_title
        or root.name
    )
    description = (
        pyproject.get("description")
        or package_json.get("description")
        or readme_summary
        or f"{project_name} project workspace."
    )

    top_dirs = _top_level_dirs(root)
    frameworks = _detect_frameworks(root, package_json, pyproject, files)
    infrastructure = _detect_infrastructure(files)

    features: list[str] = []
    if (root / "GravityKit" / "cli.py").exists():
        _add_unique(features, "Python CLI commands for installing and managing agent tooling")
    if (root / "GravityKit" / ".agent" / "skills").exists():
        _add_unique(features, "Packaged Agent Skills, workflows, agents, and brain templates")
    if (root / "GravityKit" / "ide-adapters").exists():
        _add_unique(features, "IDE adapter templates for agent-aware development environments")
    if (root / "packages" / "npx").exists():
        _add_unique(features, "NPX distribution path for Node-first users")
    if (root / "data").exists() or (root / "GravityKit" / "data").exists():
        _add_unique(features, "Catalog and group metadata for selecting installed capabilities")
    if not features:
        _add_unique(features, "Project source code and configuration")
        if readme_summary:
            _add_unique(features, readme_summary[:180])

    return {
        "root": root,
        "name": str(project_name),
        "description": str(description),
        "languages": language_counts.most_common(8),
        "frameworks": frameworks,
        "infrastructure": infrastructure,
        "top_dirs": top_dirs[:16],
        "files": files,
        "package_json": package_json,
        "pyproject": pyproject,
        "features": features[:8],
    }


def _bullet_lines(items: list[str], fallback: str) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def _render_product_md(profile: dict) -> str:
    name = profile["name"]
    desc = profile["description"]
    target_users = [
        "Developers and teams working in this repository.",
        "AI IDE agents that need project purpose, boundaries, and expected outcomes.",
    ]
    lower_desc = desc.lower()
    if "agent" in lower_desc or "gravitykit" in lower_desc:
        target_users.insert(0, "Developers adopting AI-agent workflows across IDEs.")
    objectives = [
        "Keep project purpose and expected behavior visible to Kiro in every session.",
        "Make implementation choices align with the existing repository structure and tooling.",
        "Reduce repeated context gathering by maintaining accurate steering files.",
    ]
    return f"""---
inclusion: always
---

# Product Overview

Generated by `gkt load` from repository metadata. Review and refine these notes
as the product direction evolves.

## Purpose

- {name}: {desc}

## Target Users

{_bullet_lines(target_users, "Developers working in this repository.")}

## Key Features

{_bullet_lines(profile["features"], "Project source code, configuration, and documentation.")}

## Business Objectives

{_bullet_lines(objectives, "Keep project context accurate for Kiro.")}
"""


def _render_tech_md(profile: dict) -> str:
    languages = [
        f"{language} ({count} files)"
        for language, count in profile["languages"]
    ]
    frameworks = profile["frameworks"]
    infrastructure = profile["infrastructure"]
    tools: list[str] = []
    if profile["package_json"].get("scripts"):
        _add_unique(tools, "npm scripts from `package.json`")
    if profile["pyproject"]:
        _add_unique(tools, "Python project metadata from `pyproject.toml`")
    if any(p.name == "README.md" for p in profile["files"]):
        _add_unique(tools, "Repository README documentation")
    constraints = [
        "Prefer the frameworks, scripts, and package managers already present in this repository.",
        "Do not introduce new runtime dependencies unless the task requires them.",
        "Keep generated Kiro steering files concise enough to load on every interaction.",
    ]
    return f"""---
inclusion: always
---

# Technology Stack

Generated by `gkt load` from repository files and package metadata.

## Languages

{_bullet_lines(languages, "No dominant language detected yet.")}

## Frameworks

{_bullet_lines(frameworks, "No major framework detected from package metadata yet.")}

## Libraries & Tools

{_bullet_lines(tools, "Use the tooling already documented in this repository.")}

## Infrastructure

{_bullet_lines(infrastructure, "No deployment or infrastructure files detected yet.")}

## Constraints

{_bullet_lines(constraints, "Follow existing project constraints and conventions.")}
"""


def _render_structure_md(profile: dict) -> str:
    layout_rows = []
    for directory in profile["top_dirs"]:
        layout_rows.append(f"| `{directory.as_posix()}/` | {_directory_purpose(directory)} |")
    if not layout_rows:
        layout_rows.append("| `./` | Project root |")

    file_names = {p.name for p in profile["files"]}
    naming = ["Follow naming patterns already established in each directory."]
    if "SKILL.md" in file_names:
        naming.append("Agent skills live in folders with a required `SKILL.md` file.")
    if any(p.name.startswith("wf-") and p.suffix == ".md" for p in profile["files"]):
        naming.append("GravityKit workflow files use the `wf-` prefix.")
    if any(p.suffix == ".py" for p in profile["files"]):
        naming.append("Python modules should use snake_case filenames.")
    if any(p.suffix in {".ts", ".tsx", ".js", ".jsx"} for p in profile["files"]):
        naming.append("JavaScript and TypeScript files should follow local framework conventions.")

    imports = ["Prefer local helpers and existing module boundaries over new abstractions."]
    if any(p.suffix == ".py" for p in profile["files"]):
        imports.append("For Python, keep imports explicit and package-relative where appropriate.")
    if any(p.suffix in {".ts", ".tsx", ".js", ".jsx"} for p in profile["files"]):
        imports.append("For JavaScript/TypeScript, follow existing package and path alias conventions.")

    decisions = []
    root = profile["root"]
    if (root / "GravityKit" / "cli.py").exists():
        decisions.append("The Python CLI is the canonical implementation for full GravityKit behavior.")
    if (root / "packages" / "npx").exists():
        decisions.append("The NPX package is a distribution and installer layer.")
    if (root / "GravityKit" / ".agent").exists():
        decisions.append("Canonical agent templates are stored under `GravityKit/.agent/` before install.")
    if (root / "GravityKit" / "ide-adapters" / "kiro").exists():
        decisions.append("Kiro-specific instructions are installed from `GravityKit/ide-adapters/kiro/`.")
    if not decisions:
        decisions.append("Keep architecture decisions aligned with the existing directory layout.")

    return f"""---
inclusion: always
---

# Project Structure

Generated by `gkt load` from the current repository layout.

## Directory Layout

| Path | Purpose |
| --- | --- |
{chr(10).join(layout_rows)}

## Naming Conventions

{_bullet_lines(naming, "Follow existing repository naming conventions.")}

## Import Patterns

{_bullet_lines(imports, "Follow existing import patterns.")}

## Architecture Decisions

{_bullet_lines(decisions, "Keep architecture decisions consistent with existing code.")}
"""


def load_kiro_foundation_docs(project_root: Path, force: bool = False) -> list[str]:
    """Populate Kiro foundation steering docs from local project metadata."""
    project_root = project_root.resolve()
    steering_dir = project_root / ".kiro" / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    profile = _collect_project_profile(project_root)
    docs = {
        "product.md": _render_product_md(profile),
        "tech.md": _render_tech_md(profile),
        "structure.md": _render_structure_md(profile),
    }
    written = []
    for filename, content in docs.items():
        target = steering_dir / filename
        if force or _kiro_steering_needs_load(target):
            target.write_text(content.rstrip() + "\n", encoding="utf-8")
            written.append(filename)
    return written


def safe_copy_rules(source_dir: Path, target_dir: Path):
    """Copy files and subdirectories from source to target without deleting target root or other files.
    
    Only overwrites files that exist in the source, preserving user's other files.
    """
    if not source_dir.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for item in source_dir.iterdir():
        target_item = target_dir / item.name
        if item.is_file():
            shutil.copy2(item, target_item)
        elif item.is_dir():
            safe_copy_rules(item, target_item)


def safe_clean_agent_dir(target_dir: Path, preserve_brain=True, keep_folders=None):
    """Clean only specific GravityKit folders instead of blowing away the entire directory.
    
    Avoids deleting user's other folders/files inside the root target directory.
    """
    if not target_dir.exists():
        return
    
    gkt_folders = {"skills", "workflows", "agents", "specs", "steering", "hooks"}
    if not preserve_brain:
        gkt_folders.add("brain")
        
    for item in target_dir.iterdir():
        if item.is_dir() and item.name in gkt_folders:
            if keep_folders and item.name in keep_folders:
                continue
            try:
                shutil.rmtree(item)
            except OSError:
                pass


def copy_group_selective(source_agent_dir, target_agent_dir, group_config, default_skills=None, minimal=False):
    """Copy only the skills and workflows defined in a group config.
    
    Always copies: brain/
    Selectively copies: skills/<name>/, workflows/<name>.md
    """
    if target_agent_dir.exists():
        safe_clean_agent_dir(target_agent_dir, preserve_brain=True)
    else:
        target_agent_dir.mkdir(parents=True, exist_ok=True)

    # Always copy brain/
    brain_src = source_agent_dir / "brain"
    if brain_src.exists():
        shutil.copytree(brain_src, target_agent_dir / "brain", dirs_exist_ok=True)

    all_skills = merge_group_skills(group_config, default_skills)

    # Copy selected skills
    copied_skills = 0
    if not minimal:
        skills_target = target_agent_dir / "skills"
        skills_target.mkdir(parents=True, exist_ok=True)
        skills_src = source_agent_dir / "skills"
        missing_skills = []
        for skill_name in all_skills:
            src = skills_src / skill_name
            if src.is_dir() and (src / "SKILL.md").exists():
                shutil.copytree(src, skills_target / skill_name, dirs_exist_ok=True)
                copied_skills += 1
            else:
                missing_skills.append(skill_name)
        warn_missing("skills", missing_skills)

    # Copy selected workflows
    workflows_target = target_agent_dir / "workflows"
    workflows_target.mkdir(parents=True, exist_ok=True)
    missing_workflows = []
    for wf_name in group_config.get("workflows", []):
        src = source_agent_dir / "workflows" / f"{wf_name}.md"
        if src.exists():
            shutil.copy2(src, workflows_target / f"{wf_name}.md")
        else:
            missing_workflows.append(wf_name)
    warn_missing("workflows", missing_workflows)

    # Copy all agents (agents are universal — not filtered by group)
    agents_src = source_agent_dir / "agents"
    if agents_src.exists():
        shutil.copytree(agents_src, target_agent_dir / "agents", dirs_exist_ok=True)

    return copied_skills


def install_kiro(package_dir, group_config=None, skill_groups=None, minimal=False):
    """Install GravityKit for Kiro IDE.

    Maps .agent/ structure to Kiro's .kiro/ structure:
      .agent/skills/ → .kiro/skills/
      ide-adapters/kiro/steering/ → .kiro/steering/
      ide-adapters/kiro/hooks/ → .kiro/hooks/
      Creates empty .kiro/specs/
    """
    kiro_dir = Path.cwd() / ".kiro"
    agent_dir = package_dir / ".agent"
    templates_dir = package_dir / "ide-adapters" / "kiro"

    # Clean existing .kiro/ directory safely
    if kiro_dir.exists():
        safe_clean_agent_dir(kiro_dir, preserve_brain=True)
    else:
        kiro_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy skills: .agent/skills/ → .kiro/skills/
    skills_src = agent_dir / "skills"
    copied_skills = 0
    if not minimal and skills_src.exists():
        skills_target = kiro_dir / "skills"
        skills_target.mkdir(parents=True, exist_ok=True)
        if group_config:
            # Selective: copy group skills + _default skills
            resolved_groups = skill_groups if skill_groups is not None else load_skill_groups()
            all_skills = merge_group_skills(
                group_config,
                resolved_groups.get("_default", {}).get("skills", []),
            )
            missing_skills = []
            for skill_name in all_skills:
                src = skills_src / skill_name
                if src.is_dir() and (src / "SKILL.md").exists():
                    shutil.copytree(src, skills_target / skill_name, dirs_exist_ok=True)
                    copied_skills += 1
                else:
                    missing_skills.append(skill_name)
            warn_missing("skills", missing_skills)
        else:
            # Full: copy all skills
            for skill_folder in skills_src.iterdir():
                if skill_folder.is_dir() and (skill_folder / "SKILL.md").exists():
                    shutil.copytree(skill_folder, skills_target / skill_folder.name, dirs_exist_ok=True)
                    copied_skills += 1

    # 2. Copy steering: ide-adapters/kiro/steering/ → .kiro/steering/
    steering_src = templates_dir / "steering"
    steering_target = kiro_dir / "steering"
    if steering_src.exists():
        shutil.copytree(steering_src, steering_target, dirs_exist_ok=True)

    # 3. Copy hooks: ide-adapters/kiro/hooks/ → .kiro/hooks/
    hooks_src = templates_dir / "hooks"
    hooks_target = kiro_dir / "hooks"
    if hooks_src.exists():
        shutil.copytree(hooks_src, hooks_target, dirs_exist_ok=True)

    # 4. Copy workflows → .kiro/specs/
    specs_dir = kiro_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    workflows_src = agent_dir / "workflows"
    if workflows_src.exists():
        if group_config:
            # Selective: only workflows listed in the group
            for wf_name in group_config.get("workflows", []):
                src = workflows_src / f"{wf_name}.md"
                if src.exists():
                    shutil.copy2(src, specs_dir / f"{wf_name}.md")
        else:
            # Full: copy all workflow files
            for wf_file in workflows_src.glob("*.md"):
                shutil.copy2(wf_file, specs_dir / wf_file.name)

    # 5. Copy agents → .kiro/agents/
    agents_src = agent_dir / "agents"
    if agents_src.exists():
        shutil.copytree(agents_src, kiro_dir / "agents", dirs_exist_ok=True)

    # 6. Copy brain/ → .kiro/brain/ (session continuity + workflow checkpoints)
    brain_src = agent_dir / "brain"
    if brain_src.exists():
        shutil.copytree(brain_src, kiro_dir / "brain", dirs_exist_ok=True)

    load_kiro_foundation_docs(Path.cwd())

    return copied_skills


def _write_init_state(targets, group_name):
    """Record which IDEs/CLIs were init'd. Read by `gkt mcp` to scope the
    MCP install. Adapter-only targets (cline, kilocode, copilot) are mapped to
    `antigravity` because they ride on the .agent/.mcp.json that init drops in.
    """
    mcp_ides: list[str] = []
    for t in targets:
        for m in INIT_TO_MCP_IDES.get(t, []):
            if m not in mcp_ides:
                mcp_ides.append(m)
    if not mcp_ides:
        return None
    state = {
        "init_targets": list(targets),
        "group": group_name,
        "mcp_ides": mcp_ides,
    }
    state_path = Path.cwd() / INIT_STATE_FILE
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return state_path
    except OSError as exc:
        click.echo(f"  ⚠️  Could not write {INIT_STATE_FILE}: {exc}")
        return None


def _read_init_state():
    """Return the parsed `.gkt/state.json` or {} if absent / unreadable."""
    state_path = Path.cwd() / INIT_STATE_FILE
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def update_gitignore(cwd: Path, created_paths: list):
    """Update .gitignore with top-level dot folders/files created by init."""
    gitignore_path = cwd / ".gitignore"
    top_level_dots = set()
    
    for p in created_paths:
        if not p:
            continue
        try:
            rel = p.relative_to(cwd)
        except ValueError:
            rel = p
        parts = rel.parts
        if parts:
            top_level = parts[0]
            if top_level.startswith(".") and top_level != ".github":
                top_level_dots.add(top_level)
                
    # Also add .mcp.json and .gkt just in case mcp was/will be run
    top_level_dots.add(".mcp.json")
    top_level_dots.add(".gkt")
    
    if not top_level_dots:
        return
        
    content = ""
    if gitignore_path.exists():
        try:
            content = gitignore_path.read_text(encoding="utf-8")
        except Exception:
            pass
            
    existing_lines = {line.strip() for line in content.splitlines()}
    
    to_add = []
    for item in sorted(top_level_dots):
        if item not in existing_lines and f"{item}/" not in existing_lines:
            to_add.append(item)
            
    if to_add:
        if content and not content.endswith("\n"):
            content += "\n"
        content += "\n# GravityKit\n"
        for item in to_add:
            content += f"{item}\n"
        try:
            gitignore_path.write_text(content, encoding="utf-8")
            click.echo(f"  📝 Added {len(to_add)} entries to .gitignore")
        except Exception as e:
            click.echo(f"  ⚠️  Could not update .gitignore: {e}")


def setup_agent_instructions(cwd: Path, targets: list[str], minimal: bool = False):
    """Setup agent instruction files to enforce local MCP priority."""
    rule = (
        "# Local MCP Priority Rule\n"
        "CRITICAL: Always prioritize using the MCP tools and servers defined in this local project workspace. "
        "Do NOT fallback to global or user-level MCP configurations (e.g. in the user's home or gemini directory) "
        "if a local equivalent exists.\n\n"
        "# Zero-CLI Session/Brain & Guardrails\n"
        "1. CRITICAL: NEVER require the user to run CLI commands for managing tasks, git branches, or context compaction (e.g. `gkt brain start`, `git checkout -b`, `gkt brain compact`). The user's workflow must be 100% Zero-CLI Friction.\n"
        "2. TASK SESSION LIFECYCLE:\n"
        "   - When the user asks to start a new task/feature (or you are about to implement a plan), you MUST first call the `start_task_session` tool with a safe task name under the hood. This automatically switches git branch to 'gkt-task/<name>' and sets 'discussion_mode' to true in '.agent/brain/project_context.json'.\n"
        "   - When the user says they are done, finished, or triggers 'finito'/'hoàn thành'/'xong rồi', you MUST run checks and call the `complete_task_session` tool under the hood to automatically commit, merge back, and delete the branch. Do NOT tell the user to do it.\n"
        "3. DISCUSSION GUARDRAILS:\n"
        "   - Look at '.agent/brain/project_context.json'. If 'discussion_mode' is true, you are strictly FORBIDDEN from using write/edit tools ('write_to_file', 'replace_file_content', 'multi_replace_file_content'). You must only discuss, design, and plan with the user.\n"
        "   - To unlock editing capabilities, wait for the user's explicit approval or trigger word ('yert', 'duyệt', 'code đi'). Once approved, you must call the `update_project_context` tool under the hood to set 'discussion_mode' to false (or use key_path='discussion_mode', value='false') and only then proceed with editing files.\n"
        "4. CONTEXT COMPACTION:\n"
        "   - When the context gets too large, or the user triggers 'squish'/'compact'/'nén ngữ cảnh', you MUST call the `compact_context` tool under the hood, present the generated compact handoff summary located at '.agent/brain/workflow_sessions/compact-handoff.md', and explain how they can start a fresh chat to save tokens."
    )
    
    if minimal:
        rule += (
            "\n\n# Global Skills Architecture (Minimal Mode)\n"
            "Notice: This project was initialized with `--minimal`, meaning the `skills/` folder "
            "is NOT stored locally to save space. All skills are available in the global cache.\n"
            "CRITICAL: You MUST use the `skill-router` MCP tool (`route_task`) to discover skills and workflows. "
            "The router will return the absolute paths to the globally installed `SKILL.md` files. "
            "Do NOT attempt to read `.agent/skills` locally, as it does not exist."
        )
    
    target_files = {
        "cursor": ".cursorrules",
        "windsurf": ".windsurfrules",
        "cline": ".clinerules",
        "copilot": ".github/copilot-instructions.md",
        "kiro": ".kiro/steering/brain.md",
        "antigravity": ".agent/brain/conventions.md",
        "kilocode": ".kilocoderules"
    }
    
    # Clean up the previous incorrect files
    wrong_files = ["Antigravity.md", "Codex.md", "Kiro.md"]
    for wf in wrong_files:
        wp = cwd / wf
        if wp.exists():
            try:
                wp.unlink()
            except Exception:
                pass
    
    added = 0
    for target in targets:
        if target in target_files:
            file_path = cwd / target_files[target]
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if not file_path.exists():
                    file_path.write_text(rule + "\n", encoding="utf-8")
                    added += 1
                else:
                    content = file_path.read_text(encoding="utf-8")
                    if "Local MCP Priority Rule" not in content:
                        file_path.write_text(content + "\n\n" + rule + "\n", encoding="utf-8")
                        added += 1
            except Exception:
                pass
                
    if added > 0:
        click.echo("  📝 Setup local MCP priority rules in proper IDE instruction files")


@click.group()
def main():
    """GravityKit CLI - Manage your AI Agent Team."""
    pass

@main.command()
@click.argument('target', default='all', required=False)
@click.option('--group', '-g', default=None, help='Skill group to install (e.g. general-dev, n8n-dev)')
@click.option('--minimal', is_flag=True, help='Install brain configs only, skip copying skills folder (MCP will read global cache)')
def init(target, group, minimal):
    """Initialize GravityKit in the current directory.
    
    TARGET can be an IDE name or a skill group name.
    
    \b
    IDE units: all (default), antigravity, cursor, windsurf, cline, kilocode, copilot, kiro
    Group names: general-dev, n8n-dev, nocobase-dev, general-doc, research,
                 cloud-deploy, security-audit, seo-marketing, ai-agent,
                 saas-crm, saas-comms, saas-project, saas-marketing,
                 startup-biz, api-graphql, claude-code, context-data-rag,
                 database, observability-report, uipath, gen-doc
    
    \b
    Examples:
      gkt init kiro                         # Install ALL skills for Kiro IDE
      gkt init general-dev                  # Install 'general-dev' group for Antigravity (default)
      gkt init antigravity --group gen-doc  # Install 'gen-doc' group for Antigravity
      gkt init kiro --group uipath          # Install 'uipath' group for Kiro IDE
      gkt init all --group nocobase-dev     # Install 'nocobase-dev' group for all IDEs
    """
    package_dir = Path(__file__).resolve().parent
    skill_groups = load_skill_groups()
    
    # Auto-detect: is target an IDE name or a group name?
    if target in IDE_NAMES:
        ide_target = target
        group_name = group  # May be None (= install all)
    elif target in skill_groups and target != "_default":
        ide_target = "antigravity"  # Default IDE when group is specified directly
        group_name = target
    else:
        click.echo(f"❌ Unknown target: '{target}'")
        click.echo(f"   IDE names: all, antigravity, cursor, windsurf, cline, kilocode, copilot, kiro")
        click.echo(f"   Group names: {', '.join(skill_groups.keys())}")
        return

    # Validate group name if provided
    if group_name and group_name not in skill_groups:
        click.echo(f"❌ Unknown skill group: '{group_name}'")
        click.echo(f"   Available groups: {', '.join(skill_groups.keys())}")
        return
    
    # IDE configuration mapping
    ide_config = {
        "antigravity": {
            "source": package_dir / ".agent",
            "target": Path.cwd() / ".agent",
            "label": ".agent/ (workflows + skills)",
        },
        "cursor": {
            "source": package_dir / "ide-adapters" / "cursor",
            "target": Path.cwd() / ".cursor" / "rules",
            "label": ".cursor/rules/ (Cursor IDE)",
        },
        "windsurf": {
            "source": package_dir / "ide-adapters" / "windsurf",
            "target": Path.cwd() / ".windsurf" / "rules",
            "label": ".windsurf/rules/ (Windsurf IDE)",
        },
        "cline": {
            "source": package_dir / "ide-adapters" / "cline",
            "target": Path.cwd() / ".clinerules",
            "label": ".clinerules/ (Cline IDE)",
        },
        "kilocode": {
            "source": package_dir / "ide-adapters" / "kilocode",
            "target": Path.cwd() / ".kilocode" / "rules",
            "label": ".kilocode/rules/ (Kilo Code)",
        },
        "copilot": {
            "source": package_dir / "ide-adapters" / "copilot",
            "target": Path.cwd() / ".github" / "instructions",
            "label": ".github/instructions/ (GitHub Copilot)",
        },
        "kiro": {
            "source": package_dir / ".agent",
            "target": Path.cwd() / ".kiro",
            "label": ".kiro/ (Kiro IDE - skills, hooks, steering, specs)",
        },
        "codex": {
            # Codex CLI uses MCP only — no skill files to copy. We still list
            # it here so `gkt init codex` (and `gkt init all`) can register it
            # for the state file that `gkt mcp` consumes.
            "source": None,
            "target": None,
            "label": "Codex CLI (MCP-only — registered for `gkt mcp`)",
        },
    }
    
    # Determine which IDEs to install
    if ide_target == "all":
        targets = list(ide_config.keys())
    else:
        targets = [ide_target]

    if group_name:
        grp = skill_groups[group_name]
        default_skills = get_default_skills(skill_groups)
        group_skills = grp.get('skills', [])
        extra = len([s for s in default_skills if s not in group_skills])
        all_skills = merge_group_skills(grp, default_skills)
        available, _missing = split_existing_skills(SOURCE_ROOT / ".agent" / "skills", all_skills)
        click.echo(f"🚀 Installing group '{group_name}' ({grp['description']})...")
        click.echo(
            f"   Skills: {len(group_skills)} + {extra} default "
            f"({len(available)}/{len(all_skills)} available) | "
            f"Workflows: {len(grp.get('workflows', []))}"
        )
    else:
        click.echo(f"🚀 Installing GravityKit (all skills)...")
    
    installed = 0
    registered_targets: list[str] = []  # IDE names actually processed (for state file)
    created_paths = []
    for target_ide in targets:
        config = ide_config[target_ide]
        source_dir = config["source"]
        target_dir = config["target"]

        # Codex (and any future MCP-only target) has no skill files to copy.
        # Just record it as registered so `gkt mcp` knows to wire it up.
        if source_dir is None:
            click.echo(f"  ✅ {config['label']}")
            installed += 1
            registered_targets.append(target_ide)
            if target_dir:
                created_paths.append(target_dir)
            continue

        if not source_dir.exists():
            click.echo(f"  ⚠️  Skipped {target_ide}: source not found")
            continue

        try:
            if target_ide == "kiro":
                # Special install for Kiro: maps .agent/ to .kiro/ structure
                grp = skill_groups[group_name] if group_name else None
                copied = install_kiro(package_dir, grp, skill_groups, minimal)
                click.echo(f"  ✅ {config['label']} ({copied} skills){' (minimal)' if minimal else ''}")
            elif group_name and target_ide == "antigravity":
                # Selective copy for antigravity with group filter + _default merge
                default_skills = get_default_skills(skill_groups)
                copied = copy_group_selective(source_dir, target_dir, skill_groups[group_name], default_skills, minimal)
                click.echo(f"  ✅ {config['label']} ({copied} skills){' (minimal)' if minimal else ''}")
            elif target_ide in {"cursor", "windsurf", "cline", "kilocode", "copilot"}:
                # Safe copy rules for IDE adapters to prevent deleting other user files
                safe_copy_rules(source_dir, target_dir)
                click.echo(f"  ✅ {config['label']}{' (minimal)' if minimal else ''}")
            else:
                # Full copy (original behavior) for antigravity without group
                if target_dir.exists():
                    if target_ide == "antigravity":
                        safe_clean_agent_dir(target_dir, preserve_brain=True)
                    else:
                        shutil.rmtree(target_dir)
                else:
                    target_dir.parent.mkdir(parents=True, exist_ok=True)
                
                if minimal:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for item in source_dir.iterdir():
                        if item.name == 'skills':
                            continue
                        if item.is_dir():
                            shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, target_dir / item.name)
                else:
                    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
                click.echo(f"  ✅ {config['label']}{' (minimal)' if minimal else ''}")
            installed += 1
            registered_targets.append(target_ide)
            created_paths.append(target_dir)
        except Exception as e:
            click.echo(f"  ❌ {target_ide}: {str(e)}")
    
    # For single IDE adapter installs (not antigravity/kiro/all), adapter files reference
    # .agent/skills/ paths. Auto-install .agent/ if it's not already present.
    IDE_ADAPTERS = {"cursor", "windsurf", "cline", "kilocode", "copilot"}
    if ide_target in IDE_ADAPTERS and installed > 0:
        agent_target = Path.cwd() / ".agent"
        if not agent_target.exists():
            agent_src = package_dir / ".agent"
            if agent_src.exists():
                try:
                    if group_name:
                        default_skills = get_default_skills(skill_groups)
                        copy_group_selective(agent_src, agent_target, skill_groups[group_name], default_skills, minimal)
                    else:
                        if minimal:
                            agent_target.mkdir(parents=True, exist_ok=True)
                            for item in agent_src.iterdir():
                                if item.name == 'skills':
                                    continue
                                if item.is_dir():
                                    shutil.copytree(item, agent_target / item.name, dirs_exist_ok=True)
                                else:
                                    shutil.copy2(item, agent_target / item.name)
                        else:
                            shutil.copytree(agent_src, agent_target, dirs_exist_ok=True)
                    click.echo(f"  ✅ .agent/ (skills referenced by {ide_target} adapter){' (minimal)' if minimal else ''}")
                    installed += 1
                    created_paths.append(agent_target)
                except Exception as e:
                    click.echo(f"  ⚠️  .agent/ not installed: {str(e)}")

    # Persist what was init'd so `gkt mcp` only configures these IDEs.
    if registered_targets:
        state_path = _write_init_state(registered_targets, group_name)
        if state_path is not None:
            try:
                rel = state_path.relative_to(Path.cwd())
            except ValueError:
                rel = state_path
            click.echo(f"  📝 Recorded init scope → {rel}")

    if installed > 0:
        update_gitignore(Path.cwd(), created_paths)
        setup_agent_instructions(Path.cwd(), registered_targets, minimal)

    click.echo(f"\n✨ Done! Installed for {installed} IDE(s).")
    if group_name:
        grp = skill_groups[group_name]
        workflows_dir = package_dir / ".agent" / "workflows"
        show_group_workflows(workflows_dir, grp.get('workflows', []))
    else:
        click.echo("\n💡 Suggestions for your next steps (Type these in your AI chat):")
        click.echo("  👉 @[/wf-leader]       : Orchestrate the entire team from concept to production")
        click.echo("  👉 @[/wf-quickstart]   : Build an entire project automatically (no approvals needed)")
        click.echo("  👉 @[/wf-planner]      : Analyze requirements and create detailed PRDs")
        click.echo("  👉 @[/wf-gen-doc]      : Generate AI-designed PowerPoint presentations")
        click.echo("  👉 @[/wf-uipath-project]: End-to-end UiPath RPA automation workflow")
        click.echo("\n💬 Tip: Type /wf- to filter and view all 40+ available workflows.")

    click.echo("\n⚡ Zero-CLI Brain & Guardrails are Active:")
    click.echo("  👉 Start Task : Just tell your AI Agent what feature to build. It auto-branches Git and locks files under the hood.")
    click.echo("  👉 Guardrails : Agent is locked in 'Discussion Mode' until you approve (type 'yert' or 'duyệt' to unlock).")
    click.echo("  👉 Compact    : Type 'squish' or 'nén' in chat to compress history and save tokens.")

    click.echo("\n🧠 Enable Semantic Code Graph Search (Requires Python 3.9+):")
    click.echo("  Run this command to build the FAISS index and auto-configure MCP servers for your IDEs:")
    click.echo("  👉 gkt mcp")

@main.command("load")
@click.option(
    "--target",
    default="kiro",
    type=click.Choice(["kiro"]),
    show_default=True,
    help="Instruction target to populate.",
)
@click.option(
    "--project-root",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    show_default=True,
    help="Project root to scan.",
)
@click.option("--force", is_flag=True, help="Overwrite existing steering files.")
def load_context(target, project_root, force):
    """Load project metadata into generated instruction files."""
    root = project_root.resolve()
    if target == "kiro":
        written = load_kiro_foundation_docs(root, force=force)
        if written:
            click.echo(f"Loaded Kiro steering docs: {', '.join(written)}")
            click.echo(f"Target: {root / '.kiro' / 'steering'}")
        else:
            click.echo("No Kiro steering docs changed. Use --force to regenerate existing files.")


@main.command()
def groups():
    """List available skill groups."""
    skill_groups = load_skill_groups()
    if not skill_groups:
        click.echo("❌ No skill groups found.")
        return

    click.echo("\n📦 Available Skill Groups:\n")
    click.echo(f"{'Group':<18} {'Skills':>6} {'Avail':>8} {'Workflows':>9}   {'Description':<50}")
    click.echo("-" * 101)
    default_skills = get_default_skills(skill_groups)
    skills_src = SOURCE_ROOT / ".agent" / "skills"
    for name, config in skill_groups.items():
        if name == "_default":
            continue
        skills_count = len(config.get("skills", []))
        extra = len([s for s in default_skills if s not in config.get("skills", [])])
        all_skills = merge_group_skills(config, default_skills)
        available, _missing = split_existing_skills(skills_src, all_skills)
        wf_count = len(config.get("workflows", []))
        desc = config.get("description", "No description")
        click.echo(
            f"{name:<18} {skills_count:>3}+{extra:<2} "
            f"{len(available):>3}/{len(all_skills):<3} {wf_count:>9}   {desc}"
        )
    click.echo(f"\n   * Each group includes +{len(default_skills)} default skills (memory, lifecycle, code graph, cross-platform)")
    click.echo(f"\n💡 Usage: gkt init <group-name>  (e.g. gkt init general-dev)")
    click.echo("")

@main.command(name='list')
def list_agents():
    """List available AI Agents and their roles."""
    # .agent is inside GravityKit package
    workflows_dir = Path(__file__).resolve().parent / ".agent" / "workflows"
    if not workflows_dir.exists():
        click.echo("❌ .agent/workflows directory not found.")
        return

    click.echo("\n🤖 Available GravityKit Agents:\n")
    click.echo(f"{'Agent':<25} {'Role Description':<50}")
    click.echo("-" * 75)

    for workflow_file in sorted(workflows_dir.glob("*.md")):
        name = workflow_file.stem
        description = "No description available."
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "description:" in content:
                    # Simple parsing of frontmatter description
                    import re
                    match = re.search(r"description:\s*(.+)", content)
                    if match:
                        description = match.group(1).strip()
        except Exception:
            pass
        
        click.echo(f"@[/{name:<22}] {description}")
    click.echo("")

@main.command()
def doctor():
    """Check environment health (Python, Node, Git)."""
    import subprocess
    import shutil

    click.echo("\n🩺 GravityKit Doctor - Checking Environment...\n")
    
    checks = [
        ("python", "--version", "Python"),
        ("node", "--version", "Node.js"),
        ("git", "--version", "Git"),
        ("npm", "--version", "npm"),
    ]

    all_good = True

    for cmd, arg, name in checks:
        if shutil.which(cmd):
            try:
                result = subprocess.run([cmd, arg], capture_output=True, text=True, check=True)
                version = result.stdout.strip().split('\n')[0]
                click.echo(f"✅ {name:<10}: Found ({version})")
            except Exception:
                click.echo(f"⚠️  {name:<10}: Found but failed to run")
                all_good = False
        else:
            click.echo(f"❌ {name:<10}: NOT FOUND")
            all_good = False

    # Check .agent folder
    if (Path.cwd() / ".agent").exists():
        click.echo(f"✅ .agent    : Found in current directory")
    else:
        click.echo(f"⚠️  .agent    : Not found (Run 'gkt init' to install)")

    click.echo("")
    if all_good:
        click.echo("🎉 Your environment is healthy and ready to go!")
    else:
        click.echo("🩹 Some tools are missing. Please install them to use full capabilities.")

@main.command()
def update():
    """Update GravityKit to the latest version from GitHub."""
    import subprocess
    
    click.echo("⬇️  Checking for updates from GitHub...")
    try:
        git_root = Path(__file__).resolve().parent.parent
        
        if not (git_root / ".git").exists():
             click.echo("⚠️  Not a git repository. Attempting update via Pip...")
             subprocess.run([
                 "pip", "install", "--upgrade", 
                 "git+https://github.com/OrgGem/VibeGravityKit.git"
             ], check=True)
             click.echo("✅ Updated to latest version via Pip.")
             return

        # Fetch and pull
        subprocess.run(["git", "fetch"], cwd=git_root, check=True)
        status = subprocess.run(["git", "status", "-uno"], cwd=git_root, capture_output=True, text=True)
        
        if "behind" in status.stdout:
            click.echo("🚀 New version available! Updating...")
            subprocess.run(["git", "pull"], cwd=git_root, check=True)
            click.echo("✅ Updated to latest version.")
            
            # Show new version
            version_file = Path(__file__).resolve().parent / "VERSION"
            if version_file.exists():
                with open(version_file, "r") as f:
                    click.echo(f"📦 Current Version: {f.read().strip()}")
        else:
            click.echo("✨ You are already on the latest version.")
            
    except Exception as e:
        click.echo(f"❌ Update failed: {str(e)}")

@main.command()
def version():
    """Show current GravityKit version."""
    version_file = Path(__file__).resolve().parent / "VERSION"
    if version_file.exists():
        with open(version_file, "r") as f:
            click.echo(f"v{f.read().strip()}")
    else:
        click.echo("Version info not found.")

@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def brain(ctx):
    """Manage project brain — context, decisions, conventions.
    
    Supports Zero-CLI workflow with under-the-hood session lifecycle,
    discussion guardrails, and context compaction.
    
    Subcommands:
      gkt brain start    : Start a new git-tied task session (discussion locked)
      gkt brain complete : Auto-commit, merge, and clean up the active session
      gkt brain compact  : Compress session history to save token context
    
    Tip: For a 100% friction-free experience, let your AI Agent trigger these
    automatically under the hood through the local MCP server.
    """
    local_script = Path.cwd() / ".agent" / "skills" / "brain-manager" / "scripts" / "brain.py"
    global_script = Path(__file__).resolve().parent / ".agent" / "skills" / "brain-manager" / "scripts" / "brain.py"
    script = local_script if local_script.exists() else global_script
    if not script.exists():
        click.echo("❌ brain-manager skill not found. Run 'gkt init' first.")
        return
    run_python_script(script, ctx.args)

@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def journal(ctx):
    """Knowledge journal — capture lessons, bugs, insights."""
    local_script = Path.cwd() / ".agent" / "skills" / "journal-manager" / "scripts" / "journal.py"
    global_script = Path(__file__).resolve().parent / ".agent" / "skills" / "journal-manager" / "scripts" / "journal.py"
    script = local_script if local_script.exists() else global_script
    if not script.exists():
        click.echo("❌ journal-manager skill not found. Run 'gkt init' first.")
        return
    run_python_script(script, ctx.args)


@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def graph(ctx):
    """Build code graph + FAISS index and wire MCP into Antigravity / Kiro / Claude.

    \b
    Examples:
      gkt graph                                # Default: write .mcp.json + build both indexes
      gkt graph --auto                         # Detect IDEs from working dir markers
      gkt graph --ides antigravity,kiro,claude # Pick targets explicitly
      gkt graph --all                          # Configure every supported IDE
      gkt graph --incremental                  # Fast graph rebuild (skip unchanged files)
    """
    local_script = Path.cwd() / ".agent" / "skills" / "code-graph-index" / "scripts" / "setup_mcp.py"
    global_script = Path(__file__).resolve().parent / ".agent" / "skills" / "code-graph-index" / "scripts" / "setup_mcp.py"
    script = local_script if local_script.exists() else global_script
    if not script.exists():
        click.echo("❌ code-graph-index skill not found. Run 'gkt init' first.")
        return
    run_python_script(script, ctx.args)



@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def mcp(ctx):
    """Setup Semantic Code Graph & MCP for the IDEs registered by `gkt init`.

    \b
    Behaviour:
      - Reads .gkt/state.json (written by `gkt init`) and configures MCP only
        for those IDEs/CLIs.
      - If state file is missing, falls back to --all and prints a hint.
      - You can override either way by passing --ides, --auto, or --all
        explicitly to this command.
    """
    args_to_pass = list(ctx.args)
    user_specified_scope = any(
        a == "--all" or a == "--auto" or a == "--ides" or a.startswith("--ides=")
        for a in args_to_pass
    )
    if not user_specified_scope:
        state = _read_init_state()
        mcp_ides = state.get("mcp_ides") or []
        if mcp_ides:
            args_to_pass.extend(["--ides", ",".join(mcp_ides)])
            click.echo(f"📌 Using IDE scope from {INIT_STATE_FILE}: {', '.join(mcp_ides)}")
        else:
            args_to_pass.append("--all")
            click.echo(
                f"ℹ️  No {INIT_STATE_FILE} found — falling back to --all.\n"
                f"    Tip: run `gkt init <ide>` first so this command only configures the IDEs you actually use."
            )
    if "--ensure-model" not in args_to_pass:
        args_to_pass.append("--ensure-model")

    local_script = Path.cwd() / ".agent" / "skills" / "code-graph-index" / "scripts" / "setup_mcp.py"
    global_script = Path(__file__).resolve().parent / ".agent" / "skills" / "code-graph-index" / "scripts" / "setup_mcp.py"
    script = local_script if local_script.exists() else global_script
    if not script.exists():
        click.echo("❌ code-graph-index skill not found. Run 'gkt init' first.")
        return
    run_python_script(script, args_to_pass)

@main.command()
@click.option("--debounce", default=2000, help="Debounce interval in ms (default: 2000)")
@click.option("--verbose", is_flag=True, help="Show individual file change events")
def watch(debounce, verbose):
    """Start live file watcher — auto-updates graph + FAISS on every save.

    \b
    Monitors code files in the current directory for changes and automatically
    runs incremental graph + FAISS rebuilds. MCP servers auto-reload via mtime
    checks, so IDE agents always see the freshest context.

    \b
    Examples:
      gkt watch                   # Start with default 2s debounce
      gkt watch --debounce 1000   # Faster updates (1s debounce)
      gkt watch --verbose         # Show each file change event
    """
    local_script = Path.cwd() / ".agent" / "skills" / "code-graph-index" / "scripts" / "watcher.py"
    global_script = Path(__file__).resolve().parent / ".agent" / "skills" / "code-graph-index" / "scripts" / "watcher.py"
    script = local_script if local_script.exists() else global_script
    if not script.exists():
        click.echo("❌ code-graph-index skill not found. Run 'gkt init' first.")
        return

    args = ["--project-root", str(Path.cwd()), "--debounce", str(debounce)]
    if verbose:
        args.append("--verbose")
    run_python_script(script, args)

@main.group()
def skills():
    """Manage skills — list, enable, disable, search."""
    pass


@skills.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include disabled skills")
def skills_list(show_all):
    """List all active skills."""
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    args = ["list"]
    if show_all:
        args.append("--all")
    run_python_script(script, args)


@skills.command("enable")
@click.argument("name")
def skills_enable(name):
    """Enable a disabled skill."""
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    run_python_script(script, ["enable", name])


@skills.command("disable")
@click.argument("name")
def skills_disable(name):
    """Disable a skill (move to .disabled/)."""
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    run_python_script(script, ["disable", name])


@skills.command("search")
@click.argument("query")
def skills_search(query):
    """Search skills by keyword."""
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    run_python_script(script, ["search", query])


@skills.command("count")
def skills_count():
    """Show total skill count."""
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    run_python_script(script, ["count"])


@main.command()
@click.option("--strict", is_flag=True, help="Fail on any validation error (for CI)")
def validate(strict):
    """Validate all SKILL.md files in the toolkit."""
    script = Path(__file__).resolve().parent / "scripts" / "validate_skills.py"
    args = []
    if strict:
        args.append("--strict")
    run_python_script(script, args)


@main.command("generate-index")
def generate_index():
    """Generate skills_index.json from the skills directory."""
    script = Path(__file__).resolve().parent / "scripts" / "generate_index.py"
    run_python_script(script)



if __name__ == "__main__":
    main()
