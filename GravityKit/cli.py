#!/usr/bin/env python3
import click
import os
import sys
import re
import json
import shutil
import subprocess as sp
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
IDE_NAMES = {"antigravity", "cursor", "windsurf", "cline", "kilocode", "copilot", "kiro", "all"}


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


def copy_group_selective(source_agent_dir, target_agent_dir, group_config, default_skills=None):
    """Copy only the skills and workflows defined in a group config.
    
    Always copies: brain/
    Selectively copies: skills/<name>/, workflows/<name>.md
    """
    if target_agent_dir.exists():
        shutil.rmtree(target_agent_dir)
    target_agent_dir.mkdir(parents=True, exist_ok=True)

    # Always copy brain/
    brain_src = source_agent_dir / "brain"
    if brain_src.exists():
        shutil.copytree(brain_src, target_agent_dir / "brain")

    all_skills = merge_group_skills(group_config, default_skills)

    # Copy selected skills
    skills_target = target_agent_dir / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)
    skills_src = source_agent_dir / "skills"
    copied_skills = 0
    missing_skills = []
    for skill_name in all_skills:
        src = skills_src / skill_name
        if src.is_dir() and (src / "SKILL.md").exists():
            shutil.copytree(src, skills_target / skill_name)
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
        shutil.copytree(agents_src, target_agent_dir / "agents")

    return copied_skills


def install_kiro(package_dir, group_config=None, skill_groups=None):
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

    # Clean existing .kiro/ directory
    if kiro_dir.exists():
        shutil.rmtree(kiro_dir)
    kiro_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy skills: .agent/skills/ → .kiro/skills/
    skills_src = agent_dir / "skills"
    skills_target = kiro_dir / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)
    copied_skills = 0
    if skills_src.exists():
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
                    shutil.copytree(src, skills_target / skill_name)
                    copied_skills += 1
                else:
                    missing_skills.append(skill_name)
            warn_missing("skills", missing_skills)
        else:
            # Full: copy all skills
            for skill_folder in skills_src.iterdir():
                if skill_folder.is_dir() and (skill_folder / "SKILL.md").exists():
                    shutil.copytree(skill_folder, skills_target / skill_folder.name)
                    copied_skills += 1

    # 2. Copy steering: ide-adapters/kiro/steering/ → .kiro/steering/
    steering_src = templates_dir / "steering"
    steering_target = kiro_dir / "steering"
    if steering_src.exists():
        shutil.copytree(steering_src, steering_target)

    # 3. Copy hooks: ide-adapters/kiro/hooks/ → .kiro/hooks/
    hooks_src = templates_dir / "hooks"
    hooks_target = kiro_dir / "hooks"
    if hooks_src.exists():
        shutil.copytree(hooks_src, hooks_target)

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
        shutil.copytree(agents_src, kiro_dir / "agents")

    # 6. Copy brain/ → .kiro/brain/ (session continuity + workflow checkpoints)
    brain_src = agent_dir / "brain"
    if brain_src.exists():
        shutil.copytree(brain_src, kiro_dir / "brain")

    return copied_skills


@click.group()
def main():
    """GravityKit CLI - Manage your AI Agent Team."""
    pass

@main.command()
@click.argument('target', default='all', required=False)
@click.option('--group', '-g', default=None, help='Skill group to install (e.g. general-dev, n8n-dev)')
def init(target, group):
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
    for target_ide in targets:
        config = ide_config[target_ide]
        source_dir = config["source"]
        target_dir = config["target"]
        
        if not source_dir.exists():
            click.echo(f"  ⚠️  Skipped {target_ide}: source not found")
            continue
        
        try:
            if target_ide == "kiro":
                # Special install for Kiro: maps .agent/ to .kiro/ structure
                grp = skill_groups[group_name] if group_name else None
                copied = install_kiro(package_dir, grp, skill_groups)
                click.echo(f"  ✅ {config['label']} ({copied} skills)")
            elif group_name and target_ide == "antigravity":
                # Selective copy for antigravity with group filter + _default merge
                default_skills = get_default_skills(skill_groups)
                copied = copy_group_selective(source_dir, target_dir, skill_groups[group_name], default_skills)
                click.echo(f"  ✅ {config['label']} ({copied} skills)")
            else:
                # Full copy (original behavior) for non-antigravity IDEs or no group
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source_dir, target_dir)
                click.echo(f"  ✅ {config['label']}")
            installed += 1
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
                        copy_group_selective(agent_src, agent_target, skill_groups[group_name], default_skills)
                    else:
                        shutil.copytree(agent_src, agent_target)
                    click.echo(f"  ✅ .agent/ (skills referenced by {ide_target} adapter)")
                    installed += 1
                except Exception as e:
                    click.echo(f"  ⚠️  .agent/ not installed: {str(e)}")

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

        click.echo("\n🧠 Enable Semantic Code Graph Search (Requires Python 3.9+):")
        click.echo("  Run this command to build the FAISS index and auto-configure MCP servers for your IDEs:")
        click.echo("  👉 gkt mcp")

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
    """Manage project brain — context, decisions, conventions."""
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
    """Setup Semantic Code Graph & MCP (alias for graph)."""
    if "--all" not in ctx.args:
        ctx.args.append("--all")
    if "--ensure-model" not in ctx.args:
        ctx.args.append("--ensure-model")
    ctx.forward(graph)

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
