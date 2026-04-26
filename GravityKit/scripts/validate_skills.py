#!/usr/bin/env python3
"""
validate_skills.py — Validate all SKILL.md files in the VibeGravityKit skills directory.
Adapted from antigravity-awesome-skills for VibeGravityKit integration.
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REQUIRED_FIELDS = ["name", "description"]
VALID_RISK_LEVELS = {"safe", "none", "critical", "offensive", "unknown", ""}
WHEN_TO_USE_PATTERNS = [
    re.compile(r"^##\s+When\s+to\s+Use", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Use\s+this\s+skill\s+when", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+Use\s+This\s+Skill", re.MULTILINE | re.IGNORECASE),
]
SECURITY_DISCLAIMER = re.compile(r"AUTHORIZED\s+USE\s+ONLY", re.IGNORECASE)


def parse_frontmatter(content):
    """Extract YAML frontmatter from SKILL.md content."""
    content = content.lstrip("\ufeff")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    yaml_text = parts[1]
    # Sanitize @ values
    sanitized_lines = []
    for line in yaml_text.splitlines():
        match = re.match(r'^(\s*[\w-]+):\s*(.*)$', line)
        if match:
            key, val = match.groups()
            val_s = val.strip()
            if '@' in val_s and not (val_s.startswith('"') or val_s.startswith("'")):
                safe_val = val_s.replace('"', '\\"')
                line = f'{key}: "{safe_val}"'
        sanitized_lines.append(line)
    try:
        return yaml.safe_load("\n".join(sanitized_lines)) or {}
    except yaml.YAMLError:
        return {}


def has_when_to_use_section(content):
    """Check for 'When to Use' section."""
    return any(p.search(content) for p in WHEN_TO_USE_PATTERNS)


def validate_skills(skills_dir, strict_mode=False):
    """Validate all SKILL.md files in the given directory."""
    skills_dir = Path(skills_dir)
    errors = []
    warnings = []
    validated = 0
    active_skill_ids = set()

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue

        rel_path = skill_path.relative_to(skills_dir)
        active_skill_ids.add(skill_dir.name)
        validated += 1

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"❌ {rel_path}: Cannot read file: {e}")
            continue

        # 1. Frontmatter check
        metadata = parse_frontmatter(content)
        if not metadata:
            errors.append(f"❌ {rel_path}: Missing or invalid YAML frontmatter")
            continue

        # 2. Required fields
        for field in REQUIRED_FIELDS:
            if not metadata.get(field):
                errors.append(f"❌ {rel_path}: Missing required field '{field}'")

        # 3. Risk level validation
        risk = str(metadata.get("risk", "")).strip().lower()
        if risk and risk not in VALID_RISK_LEVELS:
            warnings.append(f"⚠️ {rel_path}: Unknown risk level '{risk}'")

        # 4. When to Use section
        if not has_when_to_use_section(content):
            warnings.append(f"⚠️ {rel_path}: Missing 'When to Use' section")

        # 5. Security guardrails for offensive skills
        if metadata.get("risk") == "offensive":
            if not SECURITY_DISCLAIMER.search(content):
                errors.append(
                    f"🚨 {rel_path}: OFFENSIVE SKILL MISSING SECURITY DISCLAIMER! "
                    f"(Must contain 'AUTHORIZED USE ONLY')"
                )

    kit_dir = skills_dir.parent.parent
    groups_file = kit_dir / "data" / "skill_groups.json"
    workflows_dir = kit_dir / ".agent" / "workflows"
    if groups_file.exists():
        try:
            groups = json.loads(groups_file.read_text(encoding="utf-8"))
            workflow_ids = (
                {p.stem for p in workflows_dir.glob("*.md")}
                if workflows_dir.exists()
                else set()
            )
            for group_name, config in groups.items():
                missing_skills = [
                    skill for skill in config.get("skills", [])
                    if skill not in active_skill_ids
                ]
                if missing_skills:
                    preview = ", ".join(missing_skills[:10])
                    more = (
                        f", ... +{len(missing_skills) - 10} more"
                        if len(missing_skills) > 10
                        else ""
                    )
                    warnings.append(
                        f"⚠️ group '{group_name}': Missing skill refs: {preview}{more}"
                    )
                missing_workflows = [
                    workflow for workflow in config.get("workflows", [])
                    if workflow not in workflow_ids
                ]
                if missing_workflows:
                    preview = ", ".join(missing_workflows[:10])
                    more = (
                        f", ... +{len(missing_workflows) - 10} more"
                        if len(missing_workflows) > 10
                        else ""
                    )
                    warnings.append(
                        f"⚠️ group '{group_name}': Missing workflow refs: {preview}{more}"
                    )
        except Exception as e:
            warnings.append(f"⚠️ Cannot validate skill_groups.json: {e}")

    # Report
    print(f"\n{'='*60}")
    print(f"📋 Skill Validation Report")
    print(f"{'='*60}")
    print(f"  📁 Skills validated: {validated}")
    print(f"  ❌ Errors: {len(errors)}")
    print(f"  ⚠️  Warnings: {len(warnings)}")

    if errors:
        print(f"\n{'─'*40}")
        print("ERRORS:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")

    if warnings and (strict_mode or len(warnings) <= 20):
        print(f"\n{'─'*40}")
        print("WARNINGS:")
        for w in warnings[:20]:
            print(f"  {w}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more warnings")

    if strict_mode and errors:
        print("\n🚫 Strict mode: failing due to errors.")
        sys.exit(1)

    if not errors:
        print("\n✅ All skills passed validation!")

    return len(errors) == 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    script_dir = Path(__file__).resolve().parent
    skills_dir = script_dir.parent / ".agent" / "skills"
    validate_skills(skills_dir, strict_mode=strict)
