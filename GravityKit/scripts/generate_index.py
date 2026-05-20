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

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_frontmatter(content):
    """Extract YAML frontmatter safely from SKILL.md content with robust fallback."""
    content = content.lstrip("\ufeff")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    yaml_text = parts[1]
    
    # Layer 1: Standard safe load via PyYAML
    try:
        data = yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            return data
    except Exception:
        # Syntax error (like raw reserved indicators @, :), proceed to robust fallback
        pass
        
    # Layer 2: Self-healing Robust Line Parser for simple flat keys
    metadata = {}
    for line in yaml_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^([\w-]+):\s*(.*)$', line)
        if match:
            key, val = match.groups()
            key = key.strip()
            val = val.strip()
            # Strip outer single/double quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            metadata[key] = val
    return metadata


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

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue
        skill_id = skill_dir.name

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
