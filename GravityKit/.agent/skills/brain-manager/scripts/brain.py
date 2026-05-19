#!/usr/bin/env python3
"""
brain.py — Manage project brain (context, decisions, conventions, and task sessions).
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

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
                "repo_url": "",
                "created_at": datetime.now().isoformat()
            },
            "architecture": {
                "pattern": "",
                "database": "",
                "api_style": "",
                "auth_method": "",
                "hosting": "",
                "notes": []
            },
            "conventions": {
                "naming": "",
                "file_structure": "",
                "git_branch_strategy": "",
                "commit_format": "",
                "code_style": ""
            },
            "known_issues": [],
            "current_sprint": {
                "goal": "",
                "status": "",
                "tasks": []
            }
        }
        CONTEXT_FILE.write_text(json.dumps(default_context, indent=2, ensure_ascii=False), encoding='utf-8')

    if not DECISIONS_FILE.exists():
        DECISIONS_FILE.touch()

    if not CONVENTIONS_FILE.exists():
        CONVENTIONS_FILE.write_text(
            "# Project Conventions\n\n"
            "## Naming\n\n## File Structure\n\n## Code Style\n\n## Git\n\n",
            encoding='utf-8'
        )


def run_git(args: list) -> tuple:
    """Helper method to run a git command inside the current directory."""
    import subprocess
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def cmd_show(args):
    """Show current project context."""
    ensure_brain()

    print("🧠 Project Brain\n")

    # Show context
    ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    project = ctx.get("project", {})
    print(f"📦 Project: {project.get('name', 'Unknown')}")
    print(f"   Description: {project.get('description', '(not set)')}")
    if project.get('tech_stack'):
        print(f"   Tech Stack: {', '.join(project['tech_stack'])}")
        
    if "active_task" in ctx:
        print(f"\n🎯 Active Task: {ctx['active_task']}")
        print(f"   Discussion Mode: {'ON' if ctx.get('discussion_mode') else 'OFF'}")

    arch = ctx.get("architecture", {})
    if arch.get("pattern"):
        print(f"\n🏗️  Architecture: {arch['pattern']}")
    if arch.get("database"):
        print(f"   Database: {arch['database']}")
    if arch.get("api_style"):
        print(f"   API: {arch['api_style']}")

    # Show recent decisions
    if DECISIONS_FILE.exists() and DECISIONS_FILE.stat().st_size > 0:
        decisions = [json.loads(line) for line in DECISIONS_FILE.read_text(encoding='utf-8').strip().split('\n') if line.strip()]
        print(f"\n📋 Decisions ({len(decisions)} total):")
        for d in decisions[-5:]:  # Last 5
            print(f"   [{d.get('date', '?')}] {d.get('decision', '')}")
            if d.get('rationale'):
                print(f"      ↳ {d['rationale']}")

    # Known issues
    issues = ctx.get("known_issues", [])
    if issues:
        print(f"\n⚠️  Known Issues ({len(issues)}):")
        for issue in issues:
            print(f"   • {issue}")


def cmd_add_decision(args):
    """Add an architecture decision."""
    ensure_brain()

    decision = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "decision": args.decision,
        "rationale": args.rationale or "",
        "category": args.category or "general",
    }

    with open(DECISIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(decision, ensure_ascii=False) + '\n')

    print(f"✅ Decision recorded: {args.decision}")


def cmd_set(args):
    """Set a project context value."""
    ensure_brain()

    ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))

    # Navigate nested keys (e.g., "project.name")
    keys = args.key.split('.')
    obj = ctx
    for key in keys[:-1]:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]

    # Handle list values
    value = args.value
    if ',' in value and keys[-1] in ('tech_stack', 'notes', 'known_issues', 'tasks'):
        value = [v.strip() for v in value.split(',')]

    obj[keys[-1]] = value
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ Set {args.key} = {value}")


def cmd_start_session(args):
    """Start a new task session."""
    ensure_brain()
    
    safe_task_name = "".join(c for c in args.task_name if c.isalnum() or c in "-_")
    if not safe_task_name:
        print("❌ Error: Invalid task name.")
        sys.exit(1)
        
    branch_name = f"gkt-task/{safe_task_name}"
    
    # Check git
    code, _, _ = run_git(["status"])
    if code != 0:
        print("⚠️ Warning: Not a git repository, skipped git branch creation.")
        git_msg = "Skipped git branch"
    else:
        code_chk, _, _ = run_git(["rev-parse", "--verify", branch_name])
        if code_chk == 0:
            code_co, _, err_co = run_git(["checkout", branch_name])
            if code_co != 0:
                print(f"❌ Error checking out to branch: {err_co}")
                sys.exit(1)
            git_msg = f"Checked out to existing branch '{branch_name}'"
        else:
            code_co, _, err_co = run_git(["checkout", "-b", branch_name])
            if code_co != 0:
                print(f"❌ Error creating branch: {err_co}")
                sys.exit(1)
            git_msg = f"Created and checked out branch '{branch_name}'"

    # Update Context
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
        
    ctx["active_task"] = safe_task_name
    ctx["discussion_mode"] = True
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Add decision log
    dec = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "decision": f"Started task '{safe_task_name}' on branch '{branch_name if code == 0 else 'N/A'}'",
        "rationale": "CLI automated task session initiation",
        "category": "session"
    }
    with open(DECISIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(dec, ensure_ascii=False) + '\n')
        
    print(f"✅ Session started successfully!")
    print(f"   • {git_msg}")
    print(f"   • Active Task: {safe_task_name}")
    print(f"   • Discussion Mode: ON (Chặn AI sửa code cho tới khi bạn phê duyệt)")


def cmd_complete_session(args):
    """Complete a task session."""
    ensure_brain()
    
    safe_task_name = "".join(c for c in args.task_name if c.isalnum() or c in "-_")
    branch_name = f"gkt-task/{safe_task_name}"
    
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
        
    # Git
    code, _, _ = run_git(["status"])
    git_msg = ""
    if code != 0:
        git_msg = "Skipped git (not a git repo)"
    else:
        # Check current branch
        code_br, out_br, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if code_br == 0 and out_br != branch_name:
            run_git(["checkout", branch_name])
            
        run_git(["add", "."])
        run_git(["commit", "-m", f"gkt: completed task '{safe_task_name}'"])
        
        main_branch = "main"
        code_mb, _, _ = run_git(["rev-parse", "--verify", "main"])
        if code_mb != 0:
            code_mst, _, _ = run_git(["rev-parse", "--verify", "master"])
            if code_mst == 0:
                main_branch = "master"
                
        code_co_main, _, err_co_main = run_git(["checkout", main_branch])
        if code_co_main != 0:
            print(f"❌ Error checking out to main: {err_co_main}")
            sys.exit(1)
            
        code_mg, _, err_mg = run_git(["merge", branch_name, "--no-ff", "-m", f"gkt: merge task '{branch_name}'"])
        if code_mg == 0:
            git_msg = f"Merged '{branch_name}' into '{main_branch}' & deleted branch"
            run_git(["branch", "-d", branch_name])
        else:
            git_msg = f"Merge failed ({err_mg}), please resolve conflicts manually"

    # Clean context
    if "active_task" in ctx:
        del ctx["active_task"]
    if "discussion_mode" in ctx:
        del ctx["discussion_mode"]
    CONTEXT_FILE.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Decision log
    dec = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "decision": f"Completed task '{safe_task_name}'",
        "rationale": "CLI automated task session completion",
        "category": "session"
    }
    with open(DECISIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(dec, ensure_ascii=False) + '\n')
        
    print(f"✅ Session completed successfully!")
    print(f"   • {git_msg}")


def cmd_compact_session(args):
    """Compact project brain context and history."""
    ensure_brain()
    
    try:
        ctx = json.loads(CONTEXT_FILE.read_text(encoding='utf-8'))
    except Exception:
        ctx = {}
        
    decisions_summary = []
    if DECISIONS_FILE.exists() and DECISIONS_FILE.stat().st_size > 0:
        decisions = [json.loads(line) for line in DECISIONS_FILE.read_text(encoding='utf-8').strip().split('\n') if line.strip()]
        for d in decisions:
            decisions_summary.append(f"- [{d.get('date', '?')}] {d.get('decision', '')} ({d.get('rationale', '')})")
    else:
        decisions = []
        
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
        content.extend(decisions_summary[-15:])
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
        
    handoff_file.write_text("\n".join(content), encoding='utf-8')
    
    if len(decisions_summary) > 100:
        trimmed = decisions[-30:]
        with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
            for d in trimmed:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
        trim_msg = "Decisions log trimmed to the last 30 entries. "
    else:
        trim_msg = ""
        
    print(f"✅ Context compacted successfully!")
    if trim_msg:
        print(f"   • {trim_msg}")
    print(f"   • Handoff file created at: .agent/brain/workflow_sessions/compact-handoff.md")


def cmd_export(args):
    """Export brain to a single JSON file."""
    ensure_brain()

    brain = {
        "context": json.loads(CONTEXT_FILE.read_text(encoding='utf-8')),
        "decisions": [],
        "conventions": "",
        "exported_at": datetime.now().isoformat(),
    }

    if DECISIONS_FILE.exists() and DECISIONS_FILE.stat().st_size > 0:
        brain["decisions"] = [
            json.loads(line) for line in DECISIONS_FILE.read_text(encoding='utf-8').strip().split('\n') if line.strip()
        ]

    if CONVENTIONS_FILE.exists():
        brain["conventions"] = CONVENTIONS_FILE.read_text(encoding='utf-8')

    output = Path(args.output)
    output.write_text(json.dumps(brain, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ Brain exported to {output}")


def cmd_import(args):
    """Import brain from a JSON file."""
    ensure_brain()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return

    brain = json.loads(input_file.read_text(encoding='utf-8'))

    if "context" in brain:
        CONTEXT_FILE.write_text(json.dumps(brain["context"], indent=2, ensure_ascii=False), encoding='utf-8')

    if "decisions" in brain:
        with open(DECISIONS_FILE, 'w', encoding='utf-8') as f:
            for d in brain["decisions"]:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')

    if "conventions" in brain:
        CONVENTIONS_FILE.write_text(brain["conventions"], encoding='utf-8')

    print(f"✅ Brain imported from {input_file}")


def main():
    parser = argparse.ArgumentParser(description='VibeGravityKit Brain Manager')
    subparsers = parser.add_subparsers(dest='command')

    # show
    subparsers.add_parser('show', help='Show project context')

    # add-decision
    add_dec = subparsers.add_parser('add-decision', help='Record an architecture decision')
    add_dec.add_argument('decision', help='The decision made')
    add_dec.add_argument('--rationale', '-r', help='Why this decision was made')
    add_dec.add_argument('--category', '-c', help='Category (e.g., database, auth, infra)')

    # set
    set_cmd = subparsers.add_parser('set', help='Set a project context value')
    set_cmd.add_argument('key', help='Dot-notation key (e.g., project.name)')
    set_cmd.add_argument('value', help='Value to set')

    # start (task session)
    start_cmd = subparsers.add_parser('start', help='Start a task session (Git branch & discussion mode)')
    start_cmd.add_argument('task_name', help='Name of the task to start')

    # complete (task session)
    complete_cmd = subparsers.add_parser('complete', help='Complete a task session (Merge branch & clean)')
    complete_cmd.add_argument('task_name', help='Name of the task to complete')

    # compact (context)
    subparsers.add_parser('compact', help='Compact context and generate a compact-handoff.md')

    # export
    export_cmd = subparsers.add_parser('export', help='Export brain to JSON')
    export_cmd.add_argument('--output', '-o', default='brain_export.json')

    # import
    import_cmd = subparsers.add_parser('import', help='Import brain from JSON')
    import_cmd.add_argument('--input', '-i', required=True)

    args = parser.parse_args()

    commands = {
        'show': cmd_show,
        'add-decision': cmd_add_decision,
        'set': cmd_set,
        'start': cmd_start_session,
        'complete': cmd_complete_session,
        'compact': cmd_compact_session,
        'export': cmd_export,
        'import': cmd_import,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
