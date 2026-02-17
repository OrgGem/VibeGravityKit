#!/usr/bin/env python3
"""
skills_manager.py — Enable/disable skills locally in VibeGravityKit.
Adapted from antigravity-awesome-skills for VibeGravityKit integration.
"""

import os
import shutil
import sys
from pathlib import Path


def get_skills_dir():
    """Get the skills directory path."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent / ".agent" / "skills"


def get_disabled_dir(skills_dir):
    """Get the .disabled directory path."""
    disabled = skills_dir / ".disabled"
    disabled.mkdir(exist_ok=True)
    return disabled


def list_skills(skills_dir, show_disabled=False):
    """List all active (and optionally disabled) skills."""
    active = []
    for item in sorted(skills_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            if (item / "SKILL.md").exists():
                active.append(item.name)
            else:
                # Check for nested sub-skills
                for sub in sorted(item.iterdir()):
                    if sub.is_dir() and (sub / "SKILL.md").exists():
                        active.append(f"{item.name}/{sub.name}")

    disabled = []
    disabled_dir = skills_dir / ".disabled"
    if disabled_dir.exists():
        for item in sorted(disabled_dir.iterdir()):
            if item.is_dir() and (item / "SKILL.md").exists():
                disabled.append(item.name)

    return active, disabled


def enable_skill(skills_dir, skill_name):
    """Move a skill from .disabled back to active."""
    disabled_dir = get_disabled_dir(skills_dir)
    source = disabled_dir / skill_name
    target = skills_dir / skill_name

    if not source.exists():
        print(f"❌ Skill '{skill_name}' not found in disabled skills.")
        return False

    if target.exists():
        print(f"⚠️  Skill '{skill_name}' already exists in active skills.")
        return False

    shutil.move(str(source), str(target))
    print(f"✅ Enabled skill: {skill_name}")
    return True


def disable_skill(skills_dir, skill_name):
    """Move a skill to .disabled directory."""
    disabled_dir = get_disabled_dir(skills_dir)
    source = skills_dir / skill_name
    target = disabled_dir / skill_name

    if not source.exists():
        print(f"❌ Skill '{skill_name}' not found in active skills.")
        return False

    if target.exists():
        print(f"⚠️  Skill '{skill_name}' already exists in disabled skills.")
        return False

    shutil.move(str(source), str(target))
    print(f"✅ Disabled skill: {skill_name}")
    return True


def search_skills(skills_dir, query):
    """Search skills by keyword in name and description."""
    import re
    import yaml

    query_lower = query.lower()
    results = []

    for root, dirs, files in os.walk(skills_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if "SKILL.md" not in files:
            continue

        skill_path = Path(root) / "SKILL.md"
        rel_dir = Path(root).relative_to(skills_dir)
        skill_id = str(rel_dir).replace("\\", "/")

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            continue

        if query_lower in skill_id.lower() or query_lower in content.lower():
            # Parse name from frontmatter
            name = skill_id
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1]) or {}
                        name = meta.get("name", skill_id)
                    except Exception:
                        pass
            results.append((skill_id, name))

    return results


def main():
    skills_dir = get_skills_dir()

    if len(sys.argv) < 2:
        print("Usage: skills_manager.py <command> [args]")
        print("  list              - List active skills")
        print("  list --all        - List active and disabled skills")
        print("  enable <name>     - Enable a disabled skill")
        print("  disable <name>    - Disable a skill")
        print("  search <query>    - Search skills by keyword")
        print("  count             - Show skill count")
        return

    command = sys.argv[1]

    if command == "list":
        show_all = "--all" in sys.argv
        active, disabled = list_skills(skills_dir, show_disabled=show_all)
        print(f"\n📦 Active skills ({len(active)}):")
        for s in active:
            print(f"  ✅ {s}")
        if show_all and disabled:
            print(f"\n🚫 Disabled skills ({len(disabled)}):")
            for s in disabled:
                print(f"  ⏸️  {s}")

    elif command == "enable":
        if len(sys.argv) < 3:
            print("Usage: skills_manager.py enable <skill-name>")
            return
        enable_skill(skills_dir, sys.argv[2])

    elif command == "disable":
        if len(sys.argv) < 3:
            print("Usage: skills_manager.py disable <skill-name>")
            return
        disable_skill(skills_dir, sys.argv[2])

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: skills_manager.py search <query>")
            return
        query = " ".join(sys.argv[2:])
        results = search_skills(skills_dir, query)
        if results:
            print(f"\n🔍 Found {len(results)} skills matching '{query}':")
            for sid, name in results[:50]:
                print(f"  📎 {sid} — {name}")
            if len(results) > 50:
                print(f"  ... and {len(results) - 50} more")
        else:
            print(f"❌ No skills found matching '{query}'")

    elif command == "count":
        active, disabled = list_skills(skills_dir)
        print(f"📊 Active: {len(active)}, Disabled: {len(disabled)}, Total: {len(active) + len(disabled)}")

    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
