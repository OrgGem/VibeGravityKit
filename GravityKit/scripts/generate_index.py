#!/usr/bin/env python3
"""
generate_index.py — Generate skills_index.json from VibeGravityKit skills directory.
Adapted from antigravity-awesome-skills for VibeGravityKit integration.
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path


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


def detect_category(skill_id, description):
    """Auto-detect category from skill ID and description."""
    text = f"{skill_id} {description}".lower()
    categories = {
        "security": ["security", "sast", "compliance", "threat", "vulnerability",
                      "owasp", "pentest", "malware", "attack", "exploit"],
        "infrastructure": ["kubernetes", "k8s", "helm", "terraform", "cloud",
                           "devops", "docker", "cicd", "deployment", "monitoring"],
        "data-ai": ["data", "database", "sql", "ml", "ai", "llm", "rag",
                    "vector", "analytics", "spark", "airflow"],
        "development": ["python", "javascript", "typescript", "java", "golang",
                        "rust", "react", "frontend", "backend", "mobile", "api"],
        "architecture": ["architecture", "microservices", "c4", "ddd", "patterns"],
        "testing": ["testing", "tdd", "e2e", "qa", "test"],
        "business": ["business", "market", "sales", "seo", "marketing", "startup"],
    }
    for cat, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return cat
    return "general"


def generate_index(skills_dir, output_file):
    """Generate skills_index.json from skills directory."""
    skills_dir = Path(skills_dir)
    skills = []

    for root, dirs, files in os.walk(skills_dir):
        dirs[:] = sorted([d for d in dirs if not d.startswith('.')])
        if "SKILL.md" not in files:
            continue

        skill_path = Path(root) / "SKILL.md"
        rel_dir = Path(root).relative_to(skills_dir)
        skill_id = str(rel_dir).replace("\\", "/")

        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception:
            continue

        metadata = parse_frontmatter(content)
        name = metadata.get("name", skill_id)
        description = metadata.get("description", "")
        risk = metadata.get("risk", "unknown")
        source = metadata.get("source", "community")

        if isinstance(name, str):
            name = name.strip()
        if isinstance(description, str):
            description = description.strip()
        if isinstance(risk, str):
            risk = risk.strip()
        if isinstance(source, str):
            source = source.strip()

        category = detect_category(skill_id, str(description))

        skill_info = {
            "id": skill_id,
            "path": f"skills/{skill_id}/SKILL.md",
            "category": category,
            "name": name or skill_id,
            "description": description or "",
            "risk": risk or "unknown",
            "source": source or "community",
        }
        skills.append(skill_info)

    skills.sort(key=lambda s: s["id"])

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated index with {len(skills)} skills → {output_file}")
    return skills


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    skills_dir = script_dir.parent / ".agent" / "skills"
    output = script_dir.parent / "skills_index.json"
    generate_index(skills_dir, output)
