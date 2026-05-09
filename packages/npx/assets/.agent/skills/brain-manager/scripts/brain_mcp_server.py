#!/usr/bin/env python3
"""
brain_mcp_server.py — MCP server exposing memory and context management capabilities.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

BRAIN_DIR = Path.cwd() / ".agent" / "brain"
CONTEXT_FILE = BRAIN_DIR / "project_context.json"
DECISIONS_FILE = BRAIN_DIR / "decisions.jsonl"
CONVENTIONS_FILE = BRAIN_DIR / "conventions.md"
SESSIONS_DIR = BRAIN_DIR / "workflow_sessions"

def ensure_brain():
    """Ensure brain directory and files exist."""
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    if not CONTEXT_FILE.exists():
        default_context = {
            "project": {
                "name": Path.cwd().name,
                "description": "",
                "tech_stack": [],
            },
            "architecture": {
                "pattern": "",
                "database": "",
                "notes": []
            },
            "known_issues": []
        }
        CONTEXT_FILE.write_text(json.dumps(default_context, indent=2, ensure_ascii=False), encoding='utf-8')

    if not DECISIONS_FILE.exists():
        DECISIONS_FILE.touch()

    if not CONVENTIONS_FILE.exists():
        CONVENTIONS_FILE.write_text("# Project Conventions\n\n## Naming\n\n## File Structure\n\n## Code Style\n\n", encoding='utf-8')


def get_brain_context() -> str:
    """Retrieve the overall project context, recent decisions, and conventions. Call this when you need to understand the project background."""
    ensure_brain()
    
    output = ["# 🧠 Project Brain\n"]
    
    # 1. Project Context
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
        output.append("## Project Context")
        output.append(json.dumps(ctx, indent=2, ensure_ascii=False))
        output.append("")
    except Exception as e:
        output.append(f"Error reading context: {e}\n")

    # 2. Recent Decisions
    if DECISIONS_FILE.exists() and DECISIONS_FILE.stat().st_size > 0:
        decisions = [json.loads(line) for line in DECISIONS_FILE.read_text(encoding='utf-8').strip().split('\n') if line.strip()]
        output.append("## Recent Decisions")
        for d in decisions[-10:]:  # Last 10
            output.append(f"- [{d.get('date', '?')}] {d.get('decision', '')} (Rationale: {d.get('rationale', '')})")
        output.append("")

    # 3. Conventions
    if CONVENTIONS_FILE.exists():
        output.append("## Conventions")
        output.append(CONVENTIONS_FILE.read_text(encoding='utf-8')[:1000] + "\n...(truncated if long)")
        
    return "\n".join(output)


def add_architecture_decision(decision: str, rationale: str = "", category: str = "general") -> str:
    """Record a new architecture or structural decision so that future agents are aware of it."""
    ensure_brain()
    
    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "decision": decision,
        "rationale": rationale,
        "category": category,
    }

    with open(DECISIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')

    return f"Decision recorded successfully: {decision}"


def update_project_context(key_path: str, value: str) -> str:
    """Update a specific field in the project context. key_path uses dot notation (e.g., 'project.description' or 'architecture.database'). For list values like 'tech_stack', provide comma-separated items."""
    ensure_brain()
    
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}

    keys = key_path.split('.')
    obj = ctx
    for key in keys[:-1]:
        if key not in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        obj = obj[key]

    # Handle lists
    if ',' in value and keys[-1] in ('tech_stack', 'notes', 'known_issues', 'tasks'):
        actual_value = [v.strip() for v in value.split(',')]
    else:
        actual_value = value

    obj[keys[-1]] = actual_value
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    return f"Context updated: {key_path} = {actual_value}"


def save_workflow_checkpoint(workflow_name: str, phase: str, content: str) -> str:
    """Save a workflow session checkpoint. This allows you to pause and resume complex workflows (e.g. Phase 1, Phase 2) safely.
    workflow_name: name of the workflow (e.g. 'wf-architect')
    phase: current phase or status (e.g. 'Phase 1 - Planning')
    content: the detailed markdown notes to save for the next session
    """
    ensure_brain()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    dated_file = SESSIONS_DIR / f"{workflow_name}-{date_str}.md"
    latest_file = SESSIONS_DIR / f"{workflow_name}-latest.md"
    
    header = f"---\nworkflow: {workflow_name}\nsession_date: {date_str}\nlast_phase: {phase}\nstatus: in_progress\n---\n\n"
    full_content = header + content
    
    dated_file.write_text(full_content, encoding='utf-8')
    latest_file.write_text(full_content, encoding='utf-8')
    
    return f"Checkpoint saved to {latest_file.name} (Phase: {phase})"


def load_workflow_checkpoint(workflow_name: str) -> str:
    """Load the latest saved checkpoint for a specific workflow to resume work."""
    ensure_brain()
    
    latest_file = SESSIONS_DIR / f"{workflow_name}-latest.md"
    if latest_file.exists():
        return latest_file.read_text(encoding='utf-8')
    return f"No existing checkpoint found for workflow: {workflow_name}"


def main():
    if FastMCP is None:
        print("Missing mcp package. pip install mcp", file=sys.stderr)
        sys.exit(1)
        
    mcp = FastMCP("brain-manager")
    mcp.tool()(get_brain_context)
    mcp.tool()(add_architecture_decision)
    mcp.tool()(update_project_context)
    mcp.tool()(save_workflow_checkpoint)
    mcp.tool()(load_workflow_checkpoint)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
