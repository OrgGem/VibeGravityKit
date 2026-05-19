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


def run_git(args: list) -> tuple:
    """Helper method to run a git command inside the current directory."""
    import subprocess
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def start_task_session(task_name: str) -> str:
    """Start a new task session. This will checkout to a git branch 'gkt-task/<task_name>' and set discussion_mode to True in context."""
    ensure_brain()
    
    # 1. Clean task_name to prevent command injection or invalid branch names
    safe_task_name = "".join(c for c in task_name if c.isalnum() or c in "-_")
    if not safe_task_name:
        return "Error: Invalid task name. Use alphanumeric characters, dashes, and underscores."
        
    branch_name = f"gkt-task/{safe_task_name}"
    
    # Check if in a git repo
    code, _, _ = run_git(["status"])
    if code != 0:
        git_msg = "Warning: Not a git repository, skipped git branch creation."
    else:
        # Check if branch exists
        code_chk, _, _ = run_git(["rev-parse", "--verify", branch_name])
        if code_chk == 0:
            # Checkout to existing branch
            code_co, _, err_co = run_git(["checkout", branch_name])
            if code_co != 0:
                return f"Error checking out to existing branch {branch_name}: {err_co}"
            git_msg = f"Checked out to existing branch '{branch_name}'."
        else:
            # Create and checkout to new branch
            code_co, _, err_co = run_git(["checkout", "-b", branch_name])
            if code_co != 0:
                return f"Error creating and checking out to branch {branch_name}: {err_co}"
            git_msg = f"Created and checked out to new branch '{branch_name}'."

    # 2. Update context
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
    
    ctx["active_task"] = safe_task_name
    ctx["discussion_mode"] = True
    
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # 3. Add to decisions log
    add_architecture_decision(
        decision=f"Started task '{safe_task_name}' on branch '{branch_name if code == 0 else 'N/A'}'",
        rationale="Automated task session initiation",
        category="session"
    )
    
    return f"Session started successfully!\n- {git_msg}\n- Active Task: {safe_task_name}\n- Discussion Mode: ON (AI must not write code or edit files until approved)."


def complete_task_session(task_name: str) -> str:
    """Complete a task session. This will commit the changes on the 'gkt-task/<task_name>' branch, checkout back to the main branch, merge, and clean up the task branch."""
    ensure_brain()
    
    safe_task_name = "".join(c for c in task_name if c.isalnum() or c in "-_")
    branch_name = f"gkt-task/{safe_task_name}"
    
    # 1. Read context to verify
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
        
    # 2. Git operations
    code, _, _ = run_git(["status"])
    git_msg = ""
    if code != 0:
        git_msg = "Warning: Not a git repository, skipped git operations."
    else:
        # Check current branch
        code_br, out_br, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if code_br == 0 and out_br != branch_name:
            # Checkout first
            run_git(["checkout", branch_name])
        
        # Add all and commit
        run_git(["add", "."])
        code_ci, _, _ = run_git(["commit", "-m", f"gkt: completed task '{safe_task_name}'"])
        if code_ci == 0:
            git_msg += f"Committed all changes on '{branch_name}'. "
        else:
            git_msg += "No changes to commit or commit failed. "
            
        # Determine main/master branch
        main_branch = "main"
        code_mb, _, _ = run_git(["rev-parse", "--verify", "main"])
        if code_mb != 0:
            code_mst, _, _ = run_git(["rev-parse", "--verify", "master"])
            if code_mst == 0:
                main_branch = "master"
        
        # Checkout to main branch
        code_co_main, _, err_co_main = run_git(["checkout", main_branch])
        if code_co_main != 0:
            return f"Error checking out to main branch '{main_branch}': {err_co_main}. Git merge aborted."
            
        git_msg += f"Switched back to '{main_branch}'. "
        
        # Merge task branch
        code_mg, _, err_mg = run_git(["merge", branch_name, "--no-ff", "-m", f"gkt: merge task branch '{branch_name}'"])
        if code_mg == 0:
            git_msg += f"Merged '{branch_name}' into '{main_branch}'. "
            # Delete branch
            code_del, _, _ = run_git(["branch", "-d", branch_name])
            if code_del == 0:
                git_msg += f"Deleted branch '{branch_name}'."
            else:
                # Try force delete
                run_git(["branch", "-D", branch_name])
                git_msg += f"Force deleted branch '{branch_name}'."
        else:
            git_msg += f"Merge failed: {err_mg}. Please resolve conflicts manually."
            
    # 3. Clean context
    if "active_task" in ctx:
        del ctx["active_task"]
    if "discussion_mode" in ctx:
        del ctx["discussion_mode"]
        
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    
    add_architecture_decision(
        decision=f"Completed task '{safe_task_name}'",
        rationale="Automated task session completion & git merge",
        category="session"
    )
    
    return f"Session completed successfully!\n- {git_msg}\n- Cleaned active_task and discussion_mode from context."


def compact_context() -> str:
    """Compact context by compressing history and creating a clean handoff.md summary in workflow_sessions."""
    ensure_brain()
    
    # 1. Summarize context
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
        
    # 2. Summarize decisions
    decisions_summary = []
    if DECISIONS_FILE.exists() and DECISIONS_FILE.stat().st_size > 0:
        decisions = [json.loads(line) for line in DECISIONS_FILE.read_text(encoding='utf-8').strip().split('\n') if line.strip()]
        for d in decisions:
            decisions_summary.append(f"- [{d.get('date', '?')}] {d.get('decision', '')} ({d.get('rationale', '')})")
    else:
        decisions = []
    
    # 3. Build compact handoff markdown
    handoff_file = SESSIONS_DIR / "compact-handoff.md"
    
    content = [
        "# 📑 Compact Context Handoff",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Use this document as a quick context restorer to start a fresh chat session without losing critical project memory.",
        "",
        "## 🎯 Project Core Status",
        f"- **Project Name**: {ctx.get('project', {}).get('name', 'N/A')}",
        f"- **Description**: {ctx.get('project', {}).get('description', 'N/A')}",
        f"- **Tech Stack**: {', '.join(ctx.get('project', {}).get('tech_stack', [])) if isinstance(ctx.get('project', {}).get('tech_stack'), list) else 'N/A'}",
        "",
        "## 🏗️ Architecture & Database",
        f"- **Pattern**: {ctx.get('architecture', {}).get('pattern', 'N/A')}",
        f"- **Database**: {ctx.get('architecture', {}).get('database', 'N/A')}",
        "",
        "### Architecture Notes",
    ]
    
    notes = ctx.get('architecture', {}).get('notes', [])
    if isinstance(notes, list):
        for note in notes:
            content.append(f"- {note}")
    else:
        content.append("- No specific architectural notes.")
        
    content.extend([
        "",
        "## 📜 Consolidated Architecture Decisions",
    ])
    
    if decisions_summary:
        content.extend(decisions_summary[-15:])  # Last 15 decisions
    else:
        content.append("- No decisions recorded yet.")
        
    content.extend([
        "",
        "## ⚠️ Known Issues & Technical Debt",
    ])
    
    issues = ctx.get('known_issues', [])
    if isinstance(issues, list) and issues:
        for issue in issues:
            content.append(f"- {issue}")
    else:
        content.append("- No major known issues recorded.")
        
    # Write handoff file
    handoff_text = "\n".join(content)
    handoff_file.write_text(handoff_text, encoding='utf-8')
    
    # 4. Optional: Trim decisions.jsonl if it gets too large (> 100 lines) to save space
    if len(decisions_summary) > 100:
        trimmed = decisions[-30:]
        with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
            for d in trimmed:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        trim_msg = "Decisions log trimmed to the last 30 entries. "
    else:
        trim_msg = ""
        
    return f"Context compacted successfully!\n- {trim_msg}Created handoff file at: .agent/brain/workflow_sessions/compact-handoff.md\n- Use this handoff file to restore context in new sessions."


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
    mcp.tool()(start_task_session)
    mcp.tool()(complete_task_session)
    mcp.tool()(compact_context)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
