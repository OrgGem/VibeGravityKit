#!/usr/bin/env python3
"""
setup_mcp.py — One-shot installer for the code-graph-index skill.

Does four things:
  1. Build the structural graph         (build_graph.py)  — with fine-grained incremental
  2. Build the FAISS semantic index     (build_faiss_index.py) — auto-detects dirty_nodes
  3. Write MCP config for each target IDE so the servers auto-load
  4. Print hints for watch mode and next steps

Targets:
  --ides antigravity   → ./.mcp.json                 (also picked up by Claude Code project scope)
  --ides claude        → ./.claude/mcp_servers.json
  --ides kiro          → ./.kiro/settings/mcp.json
  --ides cursor        → ./.cursor/mcp.json
  --ides windsurf      → ./.windsurf/mcp.json
  --auto               → write to every IDE detected in the working directory
  --all                → all known IDEs regardless of detection

Each writer merges with any pre-existing `mcpServers` map — never overwrites
unrelated entries.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Make Windows consoles tolerate the emoji + arrows we print below.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# Server entries (relative paths so the config travels with the repo)
SERVER_NAMES = ("code-graph", "faiss-code-index", "document-reader", "skill-router")

GITIGNORE_LINE = ".code-graph-index/\n"

# Where each IDE picks up MCP config
IDE_CONFIG_PATHS = {
    "antigravity": Path(".mcp.json"),
    "claude": Path(".claude") / "mcp_servers.json",
    "kiro": Path(".kiro") / "settings" / "mcp.json",
    "cursor": Path(".cursor") / "mcp.json",
    "windsurf": Path(".windsurf") / "mcp.json",
}

# An IDE is considered "detected" when one of these markers exists
IDE_DETECTORS = {
    "antigravity": [Path(".agent"), Path(".mcp.json")],
    "claude": [Path(".claude"), Path("CLAUDE.md")],
    "kiro": [Path(".kiro")],
    "cursor": [Path(".cursor"), Path(".cursorrules")],
    "windsurf": [Path(".windsurf"), Path(".windsurfrules")],
}


def _python_cmd() -> str:
    """Pick the Python interpreter command that's most portable on this OS."""
    return sys.executable or ("python" if shutil.which("python") else "python3")


def build_server_entries(include_graph: bool = True, include_faiss: bool = True) -> dict:
    """Return the two MCP server entries pinned to absolute script paths.

    Absolute paths are used so the IDE can launch the servers regardless of
    its CWD; the *data* paths (`graph.json`, `faiss-index/`) stay relative
    to the project root.
    """
    py = _python_cmd()
    entries = {
        "code-graph": {
            "command": py,
            "args": [
                str((SCRIPT_DIR / "graph_mcp_server.py").resolve()),
                "--graph",
                ".code-graph-index/graph.json",
            ],
            "env": {},
            "disabled": False,
        },
    }
    if include_faiss:
        entries["faiss-code-index"] = {
            "command": py,
            "args": [
                str((SCRIPT_DIR / "faiss_mcp_server.py").resolve()),
                "--index-dir",
                ".code-graph-index/faiss-index",
            ],
            "env": {},
            "disabled": False,
        }
    
    entries["document-reader"] = {
        "command": py,
        "args": [
            str((SKILL_DIR.parent / "document-reader" / "scripts" / "reader_mcp_server.py").resolve()),
        ],
        "env": {},
        "disabled": False,
    }
    
    entries["skill-router"] = {
        "command": py,
        "args": [
            str((SKILL_DIR.parent / "skill-router" / "scripts" / "skill_router_mcp.py").resolve()),
        ],
        "env": {},
        "disabled": False,
    }

    if not include_graph:
        entries.pop("code-graph", None)
    return entries


def merge_config(existing: dict, new_servers: dict) -> dict:
    """Merge owned MCP entries and remove stale owned entries.

    If FAISS build is skipped or fails, `faiss-code-index` must not survive
    from an older config because the IDE would try to launch a server whose
    index artifacts do not exist.
    """
    out = dict(existing) if existing else {}
    servers = dict(out.get("mcpServers", {}))
    for server_name in SERVER_NAMES:
        if server_name not in new_servers:
            servers.pop(server_name, None)
    servers.update(new_servers)
    out["mcpServers"] = servers
    return out


def write_ide_config(project_root: Path, ide: str, new_servers: dict) -> Path:
    target = project_root / IDE_CONFIG_PATHS[ide]
    target.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            print(f"  ⚠️  {target} is not valid JSON — backing up to .bak and rewriting")
            target.with_suffix(target.suffix + ".bak").write_bytes(target.read_bytes())
            existing = {}

    merged = merge_config(existing, new_servers)
    target.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def detect_ides(project_root: Path) -> list[str]:
    found: list[str] = []
    for ide, markers in IDE_DETECTORS.items():
        for m in markers:
            if (project_root / m).exists():
                found.append(ide)
                break
    # Antigravity / Claude Code both honor `.mcp.json`; if neither marker is
    # present, fall back to writing the universal `.mcp.json` so Claude Code
    # picks it up automatically.
    if "antigravity" not in found and "claude" not in found:
        found.append("antigravity")
    return found


def ensure_gitignore(project_root: Path) -> None:
    gi = project_root / ".gitignore"
    line = GITIGNORE_LINE
    if gi.exists():
        text = gi.read_text(encoding="utf-8", errors="ignore")
        if line.strip() in text:
            return
        gi.write_text(text.rstrip() + "\n" + line, encoding="utf-8")
    else:
        gi.write_text(line, encoding="utf-8")


def run_step(label: str, cmd: list[str], cwd: Path) -> bool:
    print(f"\n▶ {label}")
    print(f"   {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"   ❌ {label} failed (exit {exc.returncode})")
        return False
    except FileNotFoundError:
        print(f"   ❌ Interpreter not found: {cmd[0]}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build code graph + FAISS index and wire MCP into IDEs."
    )
    parser.add_argument("--project-root", default=".", help="Project root (default: cwd)")
    parser.add_argument(
        "--ides",
        default=None,
        help="Comma-separated list: antigravity,claude,kiro,cursor,windsurf",
    )
    parser.add_argument("--auto", action="store_true",
                        help="Detect IDEs from working directory markers")
    parser.add_argument("--all", action="store_true",
                        dest="all_ides", help="Configure every supported IDE")
    parser.add_argument("--skip-graph", action="store_true", help="Skip graph build")
    parser.add_argument("--skip-faiss", action="store_true", help="Skip FAISS build")
    parser.add_argument("--ensure-model", action="store_true",
                        help="Download ONNX embedding model from jsdelivr CDN if not present")
    parser.add_argument("--incremental", action="store_true",
                        help="Use incremental graph rebuild")
    parser.add_argument("--rebuild", action="store_true",
                        help="Force full rebuild of both index artifacts")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    project_root.mkdir(parents=True, exist_ok=True)

    if args.all_ides:
        ides = list(IDE_CONFIG_PATHS.keys())
    elif args.ides:
        ides = [s.strip() for s in args.ides.split(",") if s.strip()]
    elif args.auto:
        ides = detect_ides(project_root)
    else:
        # Default: write the universal `.mcp.json` only.
        ides = ["antigravity"]

    unknown = [i for i in ides if i not in IDE_CONFIG_PATHS]
    if unknown:
        print(f"❌ Unknown IDE(s): {', '.join(unknown)}")
        print(f"   Supported: {', '.join(IDE_CONFIG_PATHS)}")
        sys.exit(2)

    print(f"📦 code-graph-index setup")
    print(f"   project root: {project_root}")
    print(f"   target IDEs : {', '.join(ides)}")

    py = _python_cmd()
    graph_ok = True
    faiss_ok = True

    # 0. Check and install dependencies
    missing_deps = []
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    try:
        import faiss
    except ImportError:
        missing_deps.append("faiss-cpu")
    try:
        import onnxruntime
    except ImportError:
        missing_deps.append("onnxruntime")

    # Document reader dependencies
    try:
        import pypdf
    except ImportError:
        missing_deps.append("pypdf")
    try:
        import docx
    except ImportError:
        missing_deps.append("python-docx")
    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")

    if missing_deps:
        print(f"\n▶ Auto-installing missing dependencies: {', '.join(missing_deps)}")
        cmd = [py, "-m", "pip", "install"] + missing_deps
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("   ✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Dependency installation failed. Please install manually:")
            print(f"      pip install {' '.join(missing_deps)}")
            print(f"   Error details: {e.stderr.strip()}")

    # 1. Structural graph
    incremental_mode = args.incremental and not args.rebuild
    if not args.skip_graph:
        cmd = [py, str(SCRIPT_DIR / "build_graph.py"), "--path", str(project_root)]
        if incremental_mode:
            cmd.append("--incremental")
        label = "Building structural graph (incremental)" if incremental_mode else "Building structural graph"
        graph_ok = run_step(label, cmd, project_root)

    # 1.5. If --rebuild, clear dirty_nodes from graph so FAISS does full rebuild
    if args.rebuild and not args.skip_graph:
        graph_path = project_root / ".code-graph-index" / "graph.json"
        if graph_path.exists():
            try:
                g = json.loads(graph_path.read_text(encoding="utf-8"))
                if "dirty_nodes" in g.get("metadata", {}):
                    g["metadata"]["dirty_nodes"] = None  # signal full rebuild
                    g["metadata"].pop("incremental_stats", None)
                    graph_path.write_text(
                        json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
            except Exception:
                pass  # non-fatal

    # 2. Download ONNX model (if requested)
    if args.ensure_model:
        print("\n▶ Ensuring ONNX embedding model")
        try:
            if str(SCRIPT_DIR) not in sys.path:
                sys.path.insert(0, str(SCRIPT_DIR))
            from embedder import ensure_model
            model_dir = project_root / ".code-graph-index" / "model"
            ensure_model(model_dir)
            print("   ✅ ONNX model ready")
        except Exception as exc:
            print(f"   ⚠️  Model download failed: {exc}")
            print("   ↳ Will fall back to hash embedding for FAISS index")

    # 3. FAISS index (auto-detects dirty_nodes for incremental re-embedding)
    if not args.skip_faiss:
        cmd = [py, str(SCRIPT_DIR / "build_faiss_index.py"),
               "--project-root", str(project_root)]
        label = "Building FAISS index"
        if incremental_mode:
            label += " (incremental — only dirty nodes will be re-embedded)"
        faiss_ok = run_step(label, cmd, project_root)
        if not faiss_ok:
            print("   ↳ FAISS step skipped — install with: pip install faiss-cpu numpy")

    # 4. Write IDE configs
    print("\n▶ Writing MCP configs")
    graph_exists = (project_root / ".code-graph-index" / "graph.json").exists()
    faiss_exists = (
        (project_root / ".code-graph-index" / "faiss-index" / "code.index").exists()
        and (project_root / ".code-graph-index" / "faiss-index" / "metadata.json").exists()
    )
    include_graph = graph_ok or graph_exists
    include_faiss = faiss_ok or faiss_exists
    new_servers = build_server_entries(include_graph=include_graph, include_faiss=include_faiss)
    if not new_servers:
        print("   ❌ No MCP servers were registered because no usable index artifacts exist.")
        sys.exit(1)
    if not include_faiss:
        print("   ⚠️  faiss-code-index not registered; FAISS index artifacts are missing.")
    written: list[str] = []
    for ide in ides:
        try:
            target = write_ide_config(project_root, ide, new_servers)
            print(f"   ✅ {ide:<12} → {target.relative_to(project_root)}")
            written.append(ide)
        except Exception as exc:
            print(f"   ❌ {ide}: {exc}")

    # 5. .gitignore hygiene
    ensure_gitignore(project_root)

    # 6. Print incremental stats if available
    graph_path = project_root / ".code-graph-index" / "graph.json"
    if graph_path.exists():
        try:
            g = json.loads(graph_path.read_text(encoding="utf-8"))
            stats = g.get("metadata", {}).get("incremental_stats")
            dirty = g.get("metadata", {}).get("dirty_nodes", [])
            if stats and incremental_mode:
                print(f"\n📊 Incremental stats:")
                print(f"   Files changed : {stats.get('files_changed', 0)}")
                print(f"   Nodes kept    : {stats.get('nodes_kept', 0)}")
                print(f"   Nodes updated : {stats.get('nodes_updated', 0)}")
                print(f"   Nodes added   : {stats.get('nodes_added', 0)}")
                print(f"   Nodes deleted : {stats.get('nodes_deleted', 0)}")
                print(f"   Dirty nodes   : {len(dirty) if dirty else 0}")
        except Exception:
            pass

    print("\n✨ Done.")
    print(f"   Servers registered: {', '.join(new_servers)}")
    print(f"   MCP tools: list_graph_stats, search_symbols, get_neighbors,")
    print(f"              find_callers, outline, get_lineage, blast_radius,")
    print(f"              search_code_chunks")
    print(f"   Reload your IDE to pick up MCP changes.")
    if "kiro" in written:
        print("   Kiro: open the MCP panel and click 'Reload servers'.")
    if "claude" in written or "antigravity" in written:
        print("   Claude Code / Antigravity: restart the agent or run `/mcp` to verify.")
    print(f"\n💡 Tip: Run 'gkt watch' to auto-sync the index on every file save.")
    print(f"   Next incremental update: 'gkt graph --incremental'")


if __name__ == "__main__":
    main()
