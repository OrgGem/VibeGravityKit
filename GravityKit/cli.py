#!/usr/bin/env python3
import click
import os
import json
import shutil
from pathlib import Path

# Get the absolute path to the GravityKit source directory
# This assumes cli.py is in the root of the repo
SOURCE_ROOT = Path(__file__).resolve().parent

# IDE names that are valid targets for init
IDE_NAMES = {"antigravity", "cursor", "windsurf", "cline", "kilocode", "copilot", "kiro", "all"}


def load_skill_groups():
    """Load skill group definitions from data/skill_groups.json."""
    groups_file = SOURCE_ROOT / "data" / "skill_groups.json"
    if not groups_file.exists():
        return {}
    with open(groups_file, "r", encoding="utf-8") as f:
        return json.load(f)


def copy_group_selective(source_agent_dir, target_agent_dir, group_config):
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

    # Copy selected skills
    skills_target = target_agent_dir / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)
    skills_src = source_agent_dir / "skills"
    copied_skills = 0
    for skill_name in group_config.get("skills", []):
        src = skills_src / skill_name
        if src.exists():
            shutil.copytree(src, skills_target / skill_name)
            copied_skills += 1

    # Copy selected workflows
    workflows_target = target_agent_dir / "workflows"
    workflows_target.mkdir(parents=True, exist_ok=True)
    for wf_name in group_config.get("workflows", []):
        src = source_agent_dir / "workflows" / f"{wf_name}.md"
        if src.exists():
            shutil.copy2(src, workflows_target / f"{wf_name}.md")

    return copied_skills


def install_kiro(package_dir, group_config=None):
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
            # Selective: only copy skills in the group
            for skill_name in group_config.get("skills", []):
                src = skills_src / skill_name
                if src.exists():
                    shutil.copytree(src, skills_target / skill_name)
                    copied_skills += 1
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

    # 4. Create specs directory
    specs_dir = kiro_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

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
    IDE names: all (default), antigravity, cursor, windsurf, cline, kilocode, copilot
    Group names: general-dev, n8n-dev, nocobase-dev, general-doc, research,
                 cloud-deploy, security-audit, seo-marketing, ai-agent,
                 saas-integrate, startup-biz
    
    \b
    Examples:
      gkt init antigravity              # Install all skills for Antigravity
      gkt init general-dev              # Install general-dev group (Antigravity)
      gkt init antigravity --group n8n-dev  # Install n8n-dev group for Antigravity
      gkt init all --group nocobase-dev # Install nocobase-dev group for all IDEs
    """
    package_dir = Path(__file__).resolve().parent
    skill_groups = load_skill_groups()
    
    # Auto-detect: is target an IDE name or a group name?
    if target in IDE_NAMES:
        ide_target = target
        group_name = group  # May be None (= install all)
    elif target in skill_groups:
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
        click.echo(f"🚀 Installing group '{group_name}' ({grp['description']})...")
        click.echo(f"   Skills: {len(grp.get('skills', []))} | Workflows: {len(grp.get('workflows', []))}")
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
                copied = install_kiro(package_dir, grp)
                click.echo(f"  ✅ {config['label']} ({copied} skills)")
            elif group_name and target_ide == "antigravity":
                # Selective copy for antigravity with group filter
                copied = copy_group_selective(source_dir, target_dir, skill_groups[group_name])
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
    
    click.echo(f"\n✨ Done! Installed for {installed} IDE(s).")
    if group_name:
        click.echo(f"👉 Group '{group_name}' is ready. Use the workflows in .agent/workflows/.")
    else:
        click.echo("👉 Use @[/planner], @[/architect], etc. in your AI chat.")

@main.command()
def groups():
    """List available skill groups."""
    skill_groups = load_skill_groups()
    if not skill_groups:
        click.echo("❌ No skill groups found.")
        return

    click.echo("\n📦 Available Skill Groups:\n")
    click.echo(f"{'Group':<18} {'Skills':>6} {'Workflows':>9}   {'Description':<50}")
    click.echo("-" * 90)
    for name, config in skill_groups.items():
        skills_count = len(config.get("skills", []))
        wf_count = len(config.get("workflows", []))
        desc = config.get("description", "No description")
        click.echo(f"{name:<18} {skills_count:>6} {wf_count:>9}   {desc}")
    click.echo(f"\n💡 Usage: gkt init <group-name>  (e.g. gkt init general-dev)")
    click.echo("")

@main.command()
def list():
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
                 "git+https://github.com/Nhqvu2005/VibeGravityKit.git"
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
    import subprocess as sp
    script = Path(__file__).resolve().parent / ".agent" / "skills" / "brain-manager" / "scripts" / "brain.py"
    if not script.exists():
        click.echo("❌ brain-manager skill not found. Run 'gkt init' first.")
        return
    sp.run(["python", str(script)] + ctx.args)

@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def journal(ctx):
    """Knowledge journal — capture lessons, bugs, insights."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / ".agent" / "skills" / "journal-manager" / "scripts" / "journal.py"
    if not script.exists():
        click.echo("❌ journal-manager skill not found. Run 'gkt init' first.")
        return
    sp.run(["python", str(script)] + ctx.args)


@main.group()
def skills():
    """Manage skills — list, enable, disable, search."""
    pass


@skills.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include disabled skills")
def skills_list(show_all):
    """List all active skills."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    args = ["python", str(script), "list"]
    if show_all:
        args.append("--all")
    sp.run(args)


@skills.command("enable")
@click.argument("name")
def skills_enable(name):
    """Enable a disabled skill."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    sp.run(["python", str(script), "enable", name])


@skills.command("disable")
@click.argument("name")
def skills_disable(name):
    """Disable a skill (move to .disabled/)."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    sp.run(["python", str(script), "disable", name])


@skills.command("search")
@click.argument("query")
def skills_search(query):
    """Search skills by keyword."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    sp.run(["python", str(script), "search", query])


@skills.command("count")
def skills_count():
    """Show total skill count."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "skills_manager.py"
    sp.run(["python", str(script), "count"])


@main.command()
@click.option("--strict", is_flag=True, help="Fail on any validation error (for CI)")
def validate(strict):
    """Validate all SKILL.md files in the toolkit."""
    import subprocess as sp
    script = Path(__file__).resolve().parent / "scripts" / "validate_skills.py"
    args = ["python", str(script)]
    if strict:
        args.append("--strict")
    sp.run(args)


@main.command("generate-index")
def generate_index():
    """Generate skills_index.json from the skills directory."""
    import subprocess as sp
    import os as _os
    env = _os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    script = Path(__file__).resolve().parent / "scripts" / "generate_index.py"
    sp.run(["python", str(script)], env=env)



if __name__ == "__main__":
    main()
