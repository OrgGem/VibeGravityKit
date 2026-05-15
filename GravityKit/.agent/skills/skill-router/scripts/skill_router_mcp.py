#!/usr/bin/env python3
"""
skill_router_mcp.py — MCP server for intelligent skill and workflow routing.

Provides tools to find the right skills and workflows for a given task,
eliminating the need for manual skill grouping when all skills are installed.
"""

from __future__ import annotations

import argparse
import json
import re
import os
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]

mcp = FastMCP("skill-router") if FastMCP is not None else None


def get_project_root() -> Path:
    """Resolve the root directory of the project."""
    # Assuming script is in .agent/skills/skill-router/scripts/
    # Root would be 4 levels up
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def load_skills_index() -> list:
    """Load the master skills_index.json file."""
    root = get_project_root()
    paths = [
        root / ".agent" / "brain" / "skills_index.json",
        root / ".kiro" / "brain" / "skills_index.json",
        root / "GravityKit" / "skills_index.json",
        root / "skills_index.json",
    ]
    all_skills = []
    for p in paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    all_skills.extend(json.load(f))
            except Exception:
                pass
    return all_skills


def load_skill_groups() -> dict:
    """Load the skill_groups.json file."""
    root = get_project_root()
    paths = [
        root / "GravityKit" / "data" / "skill_groups.json",
        root / "data" / "skill_groups.json",
    ]
    for p in paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def load_workflows() -> list:
    """Parse workflow markdown files to get their names and descriptions."""
    root = get_project_root()
    paths = [
        root / ".agent" / "workflows",
        root / "GravityKit" / ".agent" / "workflows"
    ]
    
    workflows_dir = None
    for p in paths:
        if p.exists() and p.is_dir():
            workflows_dir = p
            break
            
    results = []
    if workflows_dir:
        for wf_file in workflows_dir.glob("*.md"):
            try:
                content = wf_file.read_text(encoding="utf-8", errors="ignore")
                desc_match = re.search(r"description:\s*(.+)", content)
                desc = desc_match.group(1).strip() if desc_match else "No description available"
                results.append({
                    "name": wf_file.stem,
                    "description": desc
                })
            except Exception:
                pass
    return results


def score_text(query: str, target: str) -> float:
    """Score how well a query matches a target string based on word overlap."""
    # Extract meaningful words (length > 2)
    query_words = set(w for w in re.findall(r'\w+', query.lower()) if len(w) > 2)
    if not query_words:
        return 0.0
    
    target_lower = target.lower()
    score = 0.0
    for w in query_words:
        if w in target_lower:
            # Bonus if it's an exact word match rather than substring
            if re.search(r'\b' + re.escape(w) + r'\b', target_lower):
                score += 2.0
            else:
                score += 1.0
    return score


def get_active_sessions() -> list:
    """Find all active workflow sessions in the brain."""
    root = get_project_root()
    sessions_dir = root / ".agent" / "brain" / "workflow_sessions"
    active = []
    
    if not sessions_dir.exists():
        return active
        
    for latest_file in sessions_dir.glob("*-latest.md"):
        try:
            content = latest_file.read_text(encoding="utf-8", errors="ignore")
            # Extremely simple frontmatter parsing
            wf_match = re.search(r"workflow:\s*(.+)", content)
            proj_match = re.search(r"project:\s*(.+)", content)
            phase_match = re.search(r"last_phase:\s*['\"]?(.+?)['\"]?\n", content)
            status_match = re.search(r"status:\s*(.+)", content)
            
            if wf_match:
                active.append({
                    "workflow": wf_match.group(1).strip(),
                    "project": proj_match.group(1).strip() if proj_match else "Unknown",
                    "last_phase": phase_match.group(1).strip() if phase_match else "Unknown",
                    "status": status_match.group(1).strip() if status_match else "Unknown",
                    "file_path": str(latest_file.relative_to(root))
                })
        except Exception:
            pass
    return active


def route_task(task_description: str) -> dict:
    """Analyze a task description and recommend relevant workflows and skills.
    
    Args:
        task_description: A natural language description of what you want to achieve.
    """
    skills = load_skills_index()
    workflows = load_workflows()
    groups = load_skill_groups()
    active_sessions = get_active_sessions()
    
    # Score workflows
    wf_scores = []
    for wf in workflows:
        score = score_text(task_description, wf['name'] + " " + wf['description'])
        if score > 0:
            wf_scores.append((score, wf))
    
    wf_scores.sort(key=lambda x: x[0], reverse=True)
    top_workflows = [w for s, w in wf_scores[:3]]
    
    # Check if any recommended workflows have active sessions
    relevant_sessions = []
    for wf in top_workflows:
        for sess in active_sessions:
            if sess["workflow"] == wf["name"]:
                relevant_sessions.append(sess)
    
    # Score skills
    skill_scores = []
    for s in skills:
        text = f"{s.get('name','')} {s.get('category','')} {s.get('description','')}"
        score = score_text(task_description, text)
        if score > 0:
            skill_scores.append((score, s))
            
    skill_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Format top skills compactly
    top_skills = []
    for sc, s in skill_scores[:10]:
        desc = s.get('description', '')
        if len(desc) > 100:
            desc = desc[:97] + "..."
        top_skills.append({
            "name": s['name'], 
            "category": s.get('category', ''), 
            "description": desc
        })
    
    # Recommend groups based on top skills
    recommended_groups = set()
    for _, s in skill_scores[:5]:
        for gname, gdata in groups.items():
            if gname == "_default":
                continue
            if s['name'] in gdata.get('skills', []):
                recommended_groups.add(gname)
                
    response = {
        "analysis_summary": "Task analyzed successfully",
        "recommended_workflows": top_workflows,
        "recommended_skills": top_skills,
        "recommended_groups": list(recommended_groups)
    }
    
    if relevant_sessions:
        response["active_sessions_found"] = relevant_sessions
        response["guidance"] = "⚠️ ACTIVE SESSIONS FOUND! You should probably RESUME one of the active sessions (using mcp_brain-manager_load_workflow_checkpoint) instead of starting from scratch."
    else:
        response["guidance"] = "Start by invoking the top recommended workflow (e.g., @/wf-name). Use the recommended skills as needed for specific sub-tasks."
        
    return response


def get_skill_info(skill_name: str) -> dict:
    """Get detailed information about a specific skill by its name.
    
    Args:
        skill_name: The exact name of the skill (e.g., 'api-designer').
    """
    skills = load_skills_index()
    groups = load_skill_groups()
    
    for s in skills:
        if s.get('name') == skill_name:
            memberships = []
            for gname, gdata in groups.items():
                if gname != "_default" and skill_name in gdata.get('skills', []):
                    memberships.append(gname)
                    
            return {
                "name": s.get('name'),
                "category": s.get('category', ''),
                "description": s.get('description', ''),
                "risk": s.get('risk', ''),
                "path": s.get('path', ''),
                "groups": memberships
            }
    return {"error": f"Skill '{skill_name}' not found."}


def get_group_skills(group_name: str) -> dict:
    """Get all skills and workflows associated with a named skill group.
    
    Args:
        group_name: The name of the group (e.g., 'general-dev', 'seo-marketing').
    """
    groups = load_skill_groups()
    if group_name not in groups:
        return {"error": f"Group '{group_name}' not found. Available groups: {', '.join(groups.keys())}"}
        
    gdata = groups[group_name]
    return {
        "name": group_name,
        "description": gdata.get('description', ''),
        "skills": gdata.get('skills', []),
        "workflows": gdata.get('workflows', [])
    }


def list_groups() -> dict:
    """List all available skill groups and their descriptions."""
    groups = load_skill_groups()
    result = []
    for gname, gdata in groups.items():
        if gname == "_default": 
            continue
        result.append({
            "name": gname,
            "description": gdata.get('description', ''),
            "skill_count": len(gdata.get('skills', [])),
            "workflow_count": len(gdata.get('workflows', []))
        })
    return {"groups": result}


def list_active_sessions() -> dict:
    """List all currently active workflow sessions that can be resumed."""
    active = get_active_sessions()
    if not active:
        return {"message": "No active workflow sessions found."}
    return {"active_sessions": active}


def search_skills(query: str) -> str:
    """Search for skills by name or description.
    
    Args:
        query: The keyword to search for.
    """
    skills = load_skills_index()
    results = []
    q_lower = query.lower()
    for s in skills:
        name = s.get('name', '').lower()
        desc = s.get('description', '').lower()
        if q_lower in name or q_lower in desc:
            results.append(s)
            
    if not results:
        return f"No skills found matching '{query}'"
        
    out = [f"Found {len(results)} skills matching '{query}':"]
    for i, s in enumerate(results, 1):
        out.append(f"{i}. {s.get('name')} (File: {s.get('path', 'Unknown')})")
        desc_preview = s.get('description', '')[:100]
        if len(s.get('description', '')) > 100:
            desc_preview += "..."
        out.append(f"   Description: {desc_preview}")
        
    out.append("\nInstruction: Read the contents of the relevant file(s) before proceeding.")
    return "\n".join(out)


if mcp is not None:
    mcp.tool()(route_task)
    mcp.tool()(get_skill_info)
    mcp.tool()(get_group_skills)
    mcp.tool()(list_groups)
    mcp.tool()(list_active_sessions)
    mcp.tool()(search_skills)


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server for Intelligent Skill Routing")
    args = parser.parse_args()

    if mcp is None:
        raise RuntimeError("mcp package is required. Install with: pip install mcp")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
