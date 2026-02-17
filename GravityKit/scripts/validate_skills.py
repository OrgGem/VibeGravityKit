#!/usr/bin/env python3
"""
validate_skills.py — Validate all SKILL.md files in the VibeGravityKit skills directory.
Adapted from antigravity-awesome-skills for VibeGravityKit integration.
"""

import os
import re
import sys
import yaml
from pathlib import Path

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

    for root, dirs, files in os.walk(skills_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if "SKILL.md" not in files:
            continue

        skill_path = Path(root) / "SKILL.md"
        rel_path = skill_path.relative_to(skills_dir)
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
