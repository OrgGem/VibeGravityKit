#!/usr/bin/env python3
"""
setup_mcp.py — One-shot installer for the code-graph-index skill.

Does four things:
  1. Build the structural graph         (build_graph.py)  — with fine-grained incremental
  2. Build the FAISS semantic index     (build_faiss_index.py) — auto-detects dirty_nodes
  3. Write MCP config for each target IDE so the servers auto-load
  4. Print hints for watch mode and next steps

Targets:
  --ides antigravity   → ~/.gemini/antigravity/mcp_config.json (universal servers only)
                         + ./.mcp.json (project-specific servers; also read by Claude Code)
  --ides claude        → ./.mcp.json (Claude Code project-scoped MCP file)
  --ides kiro          → ./.kiro/settings/mcp.json
  --ides cursor        → ./.cursor/mcp.json
  --ides windsurf      → ./.windsurf/mcp.json
  --ides codex         → ~/.codex/config.toml (universal servers only)
                         + ./.codex/config.toml (project-specific servers; TOML format)
  --auto               → write to every IDE detected in the working directory
  --all                → all known IDEs regardless of detection

MCP server topology
  Universal (global config):
    - document-reader     → no per-project state, runs from anywhere
  Project-local (.mcp.json):
    - code-graph          → reads .code-graph-index/graph.json (per project)
    - faiss-code-index    → reads .code-graph-index/faiss-index/ (per project)
    - brain-manager       → uses cwd/.agent/brain (per project)
    - skill-router        → resolves project root from script + cwd (per project)

Each writer merges with any pre-existing `mcpServers` map — never overwrites
unrelated entries. Owned entries are reconciled: stale ones (e.g. a project-local
server leaked into the global config by older versions) are removed automatically.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
    _HAS_TOMLLIB = True
except ImportError:
    _HAS_TOMLLIB = False

# Make Windows consoles tolerate the emoji + arrows we print below.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_ROOT = SKILL_DIR.parent  # .../.agent/skills

# Servers GravityKit owns. We will only ever add/remove these names; any other
# server already present in a config file is left untouched.
_GLOBAL_SERVERS = {"document-reader"}
_PROJECT_LOCAL_SERVERS = {"code-graph", "faiss-code-index", "brain-manager", "skill-router"}
SERVER_NAMES = tuple(sorted(_GLOBAL_SERVERS | _PROJECT_LOCAL_SERVERS))

# Names from earlier GravityKit versions / external packages that should be
# scrubbed if encountered, to avoid agents calling dead servers.
LEGACY_SERVER_NAMES = ("code-review-graph",)

# Default Windows-safe env so MCP servers that print Unicode don't crash on cp1252.
_BASE_ENV = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

GITIGNORE_LINE = ".code-graph-index/\n"

# Antigravity has a separate user-level config that holds servers shared across
# all projects. Project-specific servers must NOT live here.
ANTIGRAVITY_GLOBAL_CONFIG = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"

# Codex CLI uses TOML and supports the same split: a global config for universal
# servers and a project-local config gated by Codex's `trust` model.
CODEX_GLOBAL_CONFIG = Path.home() / ".codex" / "config.toml"

# Where each IDE picks up its project-local MCP config.
IDE_CONFIG_PATHS = {
    # Antigravity reads ~/.gemini/antigravity/mcp_config.json (global) AND
    # ./.mcp.json (project). Claude Code also natively reads ./.mcp.json.
    "antigravity": Path(".mcp.json"),
    "claude": Path(".mcp.json"),
    "kiro": Path(".kiro") / "settings" / "mcp.json",
    "cursor": Path(".cursor") / "mcp.json",
    "windsurf": Path(".windsurf") / "mcp.json",
    # Codex CLI — TOML format, project-local file is loaded only for trusted projects.
    "codex": Path(".codex") / "config.toml",
}

# Legacy file written by older versions; we will delete it during setup if found.
LEGACY_CLAUDE_FILE = Path(".claude") / "mcp_servers.json"

# An IDE is considered "detected" when one of these markers exists.
IDE_DETECTORS = {
    "antigravity": [Path(".agent"), Path(".mcp.json")],
    "claude": [Path(".claude"), Path("CLAUDE.md")],
    "kiro": [Path(".kiro")],
    "cursor": [Path(".cursor"), Path(".cursorrules")],
    "windsurf": [Path(".windsurf"), Path(".windsurfrules")],
    "codex": [Path(".codex"), Path("AGENTS.md")],
}


def _python_cmd() -> str:
    """Pick the Python interpreter command that's most portable on this OS."""
    return sys.executable or ("python" if shutil.which("python") else "python3")


def _read_json_or_empty(path: Path) -> dict:
    """Read a JSON file; on parse failure, back it up and return {}."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        backup = path.with_suffix(path.suffix + ".bak")
        print(f"   ⚠️  {path} is not valid JSON — backing up to {backup.name} and rewriting")
        backup.write_bytes(path.read_bytes())
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _entry(
    script: Path,
    *extra_args: str,
    cwd: Path | None = None,
    extra_env: dict | None = None,
) -> dict:
    """Build an MCP server entry with consistent shape."""
    env = dict(_BASE_ENV)
    if extra_env:
        env.update(extra_env)
    out: dict = {
        "command": _python_cmd(),
        "args": [str(script.resolve()), *extra_args],
        "env": env,
        "disabled": False,
    }
    if cwd is not None:
        out["cwd"] = str(cwd)
    return out


def build_server_entries(
    project_root: Path,
    include_graph: bool = True,
    include_faiss: bool = True,
) -> dict:
    """Build MCP entries with absolute script paths AND absolute data paths.

    Data paths (graph.json / faiss-index/) are absolute so the IDE can launch
    each server with any CWD. `cwd` is also set to project_root for servers
    that read state from `Path.cwd()` (brain-manager) — defence in depth.
    """
    pr = project_root.resolve()
    cgi = pr / ".code-graph-index"
    entries: dict = {}

    if include_graph:
        entries["code-graph"] = _entry(
            SCRIPT_DIR / "graph_mcp_server.py",
            "--graph", str(cgi / "graph.json"),
            cwd=pr,
        )
    if include_faiss:
        entries["faiss-code-index"] = _entry(
            SCRIPT_DIR / "faiss_mcp_server.py",
            "--index-dir", str(cgi / "faiss-index"),
            cwd=pr,
        )

    # brain-manager reads/writes `.agent/brain/` relative to Path.cwd().
    # Setting cwd here is REQUIRED for correct per-project behaviour.
    entries["brain-manager"] = _entry(
        SKILLS_ROOT / "brain-manager" / "scripts" / "brain_mcp_server.py",
        cwd=pr,
    )

    # skill-router resolves project root from __file__ (5 levels up). cwd is a
    # belt-and-braces fallback so any future code paths see the right project.
    entries["skill-router"] = _entry(
        SKILLS_ROOT / "skill-router" / "scripts" / "skill_router_mcp.py",
        cwd=pr,
    )

    # document-reader has no per-project state — included here so callers can
    # pick it up; the writer routes it to the global config for Antigravity.
    entries["document-reader"] = _entry(
        SKILLS_ROOT / "document-reader" / "scripts" / "reader_mcp_server.py",
    )

    return entries


def _reconcile(
    existing_servers: dict,
    new_owned: dict,
    *,
    owned_allow: set[str],
    owned_drop: set[str],
) -> dict:
    """Reconcile existing MCP servers with the set we own.

    - Entries in `owned_allow` are written/refreshed from `new_owned`.
    - Entries in `owned_drop` (servers GravityKit owns but does not belong here)
      are removed if present, fixing leaks from older versions.
    - Legacy server names are scrubbed.
    - Any other entries (third-party MCP servers) are preserved untouched.
    """
    out = dict(existing_servers)
    for name in owned_drop:
        out.pop(name, None)
    for name in LEGACY_SERVER_NAMES:
        out.pop(name, None)
    for name in owned_allow:
        if name in new_owned:
            out[name] = new_owned[name]
        else:
            # Owned but not provided this run (e.g., FAISS skipped) → drop stale entry.
            out.pop(name, None)
    return out


def _write_global_antigravity(new_servers: dict) -> Path:
    """Write the universal-only global config for Antigravity."""
    target = ANTIGRAVITY_GLOBAL_CONFIG
    existing = _read_json_or_empty(target)
    existing_servers = dict(existing.get("mcpServers", {}))
    reconciled = _reconcile(
        existing_servers,
        {k: v for k, v in new_servers.items() if k in _GLOBAL_SERVERS},
        owned_allow=_GLOBAL_SERVERS,
        owned_drop=_PROJECT_LOCAL_SERVERS,
    )
    out = dict(existing)
    out["mcpServers"] = reconciled
    _write_json(target, out)
    return target


def _write_project_local(
    target: Path,
    new_servers: dict,
    *,
    include_global: bool = False,
) -> Path:
    """Write a project-local MCP config file.

    For Antigravity's `.mcp.json` we keep only `_PROJECT_LOCAL_SERVERS` (the
    universal ones live in the global Antigravity config). For IDEs that have
    no global-config concept (Kiro / Cursor / Windsurf) the caller passes
    `include_global=True` so universal servers are written here too.
    """
    if include_global:
        owned_allow = _PROJECT_LOCAL_SERVERS | _GLOBAL_SERVERS
        owned_drop: set[str] = set()
    else:
        owned_allow = _PROJECT_LOCAL_SERVERS
        owned_drop = _GLOBAL_SERVERS
    existing = _read_json_or_empty(target)
    existing_servers = dict(existing.get("mcpServers", {}))
    reconciled = _reconcile(
        existing_servers,
        {k: v for k, v in new_servers.items() if k in owned_allow},
        owned_allow=owned_allow,
        owned_drop=owned_drop,
    )
    out = dict(existing)
    out["mcpServers"] = reconciled
    _write_json(target, out)
    return target


# --- TOML support (Codex CLI) -------------------------------------------------
#
# Codex stores config at `~/.codex/config.toml` and `./.codex/config.toml`.
# We only need to (a) read/preserve unrelated content and (b) emit
# `[mcp_servers.<name>]` sections idiomatically. Reading uses stdlib `tomllib`
# (Python 3.11+); writing uses a small purpose-built emitter so we don't add
# a runtime dependency.

_TOML_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Conventional ordering of keys inside a `[mcp_servers.*]` section so generated
# files diff cleanly across runs.
_CODEX_KEY_ORDER = (
    "command", "args", "env", "cwd",
    "url", "bearer_token_env_var", "http_headers", "env_http_headers",
    "startup_timeout_sec", "tool_timeout_sec",
    "enabled", "required", "enabled_tools", "disabled_tools",
)


def _toml_escape_string(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_key(k: str) -> str:
    return k if _TOML_BARE_KEY_RE.match(k) else _toml_escape_string(k)


def _emit_toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return _toml_escape_string(v)
    if isinstance(v, list):
        return "[" + ", ".join(_emit_toml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        pairs = [f"{_toml_key(k)} = {_emit_toml_value(val)}" for k, val in v.items()]
        return "{ " + ", ".join(pairs) + " }"
    raise TypeError(f"Unsupported TOML value type: {type(v).__name__}")


def _emit_codex_toml(parsed: dict) -> str:
    """Emit a TOML document, writing `mcp_servers` as `[mcp_servers.<name>]`
    sub-sections (the idiomatic Codex form). Other top-level scalars and
    tables are preserved as best-effort with inline-table fallback for any
    value that is itself a dict.
    """
    lines: list[str] = []
    mcp_servers = dict(parsed.get("mcp_servers", {}))
    other = {k: v for k, v in parsed.items() if k != "mcp_servers"}

    # 1. Top-level scalars / arrays first.
    scalars = {k: v for k, v in other.items() if not isinstance(v, dict)}
    for k, v in scalars.items():
        lines.append(f"{_toml_key(k)} = {_emit_toml_value(v)}")
    if scalars:
        lines.append("")

    # 2. mcp_servers.<name> sub-sections.
    for name, entry in mcp_servers.items():
        lines.append(f"[mcp_servers.{_toml_key(name)}]")
        if isinstance(entry, dict):
            ordered_keys = list(_CODEX_KEY_ORDER) + [
                k for k in entry if k not in _CODEX_KEY_ORDER
            ]
            for key in ordered_keys:
                if key in entry:
                    lines.append(f"{_toml_key(key)} = {_emit_toml_value(entry[key])}")
        lines.append("")

    # 3. Any other top-level tables (e.g. [profiles.default]). Preserved
    #    one level deep using inline-table syntax for nested dict values.
    for k, v in other.items():
        if not isinstance(v, dict):
            continue
        lines.append(f"[{_toml_key(k)}]")
        for sub_k, sub_v in v.items():
            lines.append(f"{_toml_key(sub_k)} = {_emit_toml_value(sub_v)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _read_toml_or_empty(path: Path) -> dict:
    """Read a TOML file; on parse failure, back it up and return {}.
    If `tomllib` is not available (Python < 3.11), back up and return {}
    so we never silently corrupt existing config.
    """
    if not path.exists():
        return {}
    if not _HAS_TOMLLIB:
        backup = path.with_suffix(path.suffix + ".bak")
        try:
            backup.write_bytes(path.read_bytes())
            print(f"   ⚠️  tomllib unavailable (Python 3.11+ required) — backed up "
                  f"{path.name} → {backup.name} and rewriting from scratch")
        except OSError:
            pass
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8-sig"))
    except tomllib.TOMLDecodeError:
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_bytes(path.read_bytes())
        print(f"   ⚠️  {path} is not valid TOML — backing up to {backup.name} and rewriting")
        return {}


def _write_toml(path: Path, parsed: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_emit_codex_toml(parsed), encoding="utf-8")


def _to_codex_entry(entry: dict) -> dict:
    """Translate our internal MCP entry shape to Codex's TOML schema.

    `disabled: false` (our default) maps to Codex's implicit `enabled = true`,
    so we just drop the key. `disabled: true` maps to `enabled = false`.
    """
    out: dict = {}
    for key in ("command", "args", "env", "cwd"):
        if key in entry:
            out[key] = entry[key]
    if entry.get("disabled") is True:
        out["enabled"] = False
    return out


def _write_global_codex(new_servers: dict) -> Path:
    """Write the universal-only global Codex config."""
    target = CODEX_GLOBAL_CONFIG
    parsed = _read_toml_or_empty(target)
    existing_servers = dict(parsed.get("mcp_servers", {}))
    new_globals = {
        k: _to_codex_entry(v) for k, v in new_servers.items() if k in _GLOBAL_SERVERS
    }
    reconciled = _reconcile(
        existing_servers, new_globals,
        owned_allow=_GLOBAL_SERVERS, owned_drop=_PROJECT_LOCAL_SERVERS,
    )
    parsed["mcp_servers"] = reconciled
    _write_toml(target, parsed)
    return target


def _write_project_codex(target: Path, new_servers: dict) -> Path:
    """Write the project-local Codex config (`./.codex/config.toml`)."""
    parsed = _read_toml_or_empty(target)
    existing_servers = dict(parsed.get("mcp_servers", {}))
    new_locals = {
        k: _to_codex_entry(v) for k, v in new_servers.items() if k in _PROJECT_LOCAL_SERVERS
    }
    reconciled = _reconcile(
        existing_servers, new_locals,
        owned_allow=_PROJECT_LOCAL_SERVERS, owned_drop=_GLOBAL_SERVERS,
    )
    parsed["mcp_servers"] = reconciled
    _write_toml(target, parsed)
    return target


# --- IDE dispatcher -----------------------------------------------------------


def write_ide_config(project_root: Path, ide: str, new_servers: dict) -> list[Path]:
    """Write MCP config for a single IDE. Returns the list of files touched."""
    written: list[Path] = []

    if ide == "antigravity":
        # 1) Global universal config
        gpath = _write_global_antigravity(new_servers)
        written.append(gpath)
        print(f"   ✅ antigravity (global)  → {gpath}")
        # 2) Project-local config
        ppath = _write_project_local(project_root / IDE_CONFIG_PATHS["antigravity"], new_servers)
        written.append(ppath)
        try:
            print(f"   ✅ antigravity (project) → {ppath.relative_to(project_root)}")
        except ValueError:
            print(f"   ✅ antigravity (project) → {ppath}")
        return written

    if ide == "codex":
        gpath = _write_global_codex(new_servers)
        written.append(gpath)
        print(f"   ✅ codex (global)        → {gpath}")
        ppath = _write_project_codex(project_root / IDE_CONFIG_PATHS["codex"], new_servers)
        written.append(ppath)
        try:
            print(f"   ✅ codex (project)       → {ppath.relative_to(project_root)}")
        except ValueError:
            print(f"   ✅ codex (project)       → {ppath}")
        return written

    target = project_root / IDE_CONFIG_PATHS[ide]
    # Non-Antigravity IDEs have no separate global config — write all servers.
    _write_project_local(target, new_servers, include_global=True)
    written.append(target)
    try:
        rel = target.relative_to(project_root)
    except ValueError:
        rel = target
    print(f"   ✅ {ide:<12} → {rel}")
    return written


def _cleanup_legacy_files(project_root: Path) -> None:
    """Remove files written by older GravityKit versions that current Claude
    Code / Antigravity no longer read."""
    legacy = project_root / LEGACY_CLAUDE_FILE
    if legacy.exists():
        try:
            legacy.unlink()
            print(f"   🧹 removed legacy {LEGACY_CLAUDE_FILE} (Claude Code reads .mcp.json)")
        except OSError as exc:
            print(f"   ⚠️  could not remove {legacy}: {exc}")


def detect_ides(project_root: Path) -> list[str]:
    """Detect IDEs by scanning for known marker files. `antigravity` and
    `claude` both target `.mcp.json`; we collapse them so we don't write the
    same file twice."""
    found: list[str] = []
    for ide, markers in IDE_DETECTORS.items():
        for m in markers:
            if (project_root / m).exists():
                found.append(ide)
                break
    if "antigravity" in found and "claude" in found:
        found.remove("claude")
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
        help="Comma-separated list: antigravity,claude,kiro,cursor,windsurf,codex",
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
        # antigravity already covers .mcp.json — drop claude to avoid double write
        if "antigravity" in ides and "claude" in ides:
            ides.remove("claude")
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
        import numpy  # noqa: F401
    except ImportError:
        missing_deps.append("numpy")
    try:
        import faiss  # noqa: F401
    except ImportError:
        missing_deps.append("faiss-cpu")
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        missing_deps.append("onnxruntime")

    # Document reader dependencies
    try:
        import pypdf  # noqa: F401
    except ImportError:
        missing_deps.append("pypdf")
    try:
        import docx  # noqa: F401
    except ImportError:
        missing_deps.append("python-docx")
    try:
        import openpyxl  # noqa: F401
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
    new_servers = build_server_entries(
        project_root, include_graph=include_graph, include_faiss=include_faiss
    )
    if not new_servers:
        print("   ❌ No MCP servers were registered because no usable index artifacts exist.")
        sys.exit(1)
    if not include_faiss:
        print("   ⚠️  faiss-code-index not registered; FAISS index artifacts are missing.")

    written: list[str] = []
    for ide in ides:
        try:
            write_ide_config(project_root, ide, new_servers)
            written.append(ide)
        except Exception as exc:
            print(f"   ❌ {ide}: {exc}")

    # 4b. Remove legacy files written by older versions
    _cleanup_legacy_files(project_root)

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
    print(f"   Reload your IDE to pick up MCP changes.")
    if "kiro" in written:
        print("   Kiro: open the MCP panel and click 'Reload servers'.")
    if "claude" in written or "antigravity" in written:
        print("   Claude Code / Antigravity: restart the agent or run `/mcp` to verify.")
    if "codex" in written:
        print("   Codex CLI: project-local config loads only for trusted projects.")
        print("              First-time use: run `codex` in this directory and accept the trust prompt,")
        print("              or add an entry under [projects] in ~/.codex/config.toml.")
    print(f"\n💡 Tip: Run 'gkt watch' to auto-sync the index on every file save.")
    print(f"   Next incremental update: 'gkt graph --incremental'")


if __name__ == "__main__":
    main()
