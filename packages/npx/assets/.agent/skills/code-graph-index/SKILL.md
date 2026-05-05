---
name: code-graph-index
description: |
  Build a hybrid code knowledge base — symbolic graph (functions, classes, imports, call edges)
  plus a FAISS semantic vector index — and auto-wire MCP servers into Antigravity, Kiro, and
  Claude Code so any AI agent can search, traverse, and reason about the codebase locally
  without re-reading whole files. Supports fine-grained incremental updates (AST node-level
  hash caching), live watch mode, and data lineage with byte-level source traceability.
risk: safe
source: VibeGravityKit
---

# Code Graph Index (Graph + FAISS + MCP)

A token-saving, fully local code intelligence layer for AI agents.

This skill turns any repository into:

1. A **structural graph** — files, classes, functions, imports, and call edges saved as JSON with docstrings/snippets and **content hashes for fine-grained incremental updates**.
2. A **Hybrid FAISS semantic index** — vector search directly over the structural graph nodes (Hybrid RAG) for lightning-fast, highly accurate API discovery. **Supports incremental re-embedding: only dirty nodes are re-vectorized.**
3. Two **MCP servers** that expose the graph and the index to any MCP-aware IDE, with **mtime-based hot-reload** so they always serve fresh data.
4. An auto-generated **MCP config** wired into Antigravity, Kiro, and Claude Code.
5. A **live watch mode** (`gkt watch`) that monitors file changes and auto-syncs the index in real time.

### 🤖 Agent Instruction
**Agents MUST automatically run `gkt mcp --incremental`** (or via `setup_mcp.py`) when finishing a coding task that alters the project structure, to ensure the graph and FAISS index remain synchronized.

## When to use

- First-time setup of a new/legacy repo for any AI workflow (review, refactor, debug, knowledge-guide).
- Before running `/wf-code-reviewer`, `/wf-architect`, `/wf-knowledge-guide`, or `/wf-fullstack-coder` on a large codebase.
- When agents start reading whole files just to find a symbol — that's the signal to index.
- After major refactors, branch switches, or stale-graph warnings.

## Prerequisites

```bash
python -m pip install faiss-cpu numpy mcp
# Optional — high-quality ONNX embedding (recommended)
python -m pip install onnxruntime
# Optional — live watch mode
python -m pip install watchdog>=3.0
```

`faiss-cpu` and `mcp` are optional — install only if you want semantic search and the MCP servers running. The graph builder works with stdlib alone.

`onnxruntime` enables **all-MiniLM-L6-v2** sentence embeddings (~23 MB INT8-quantized model, auto-downloaded from `cdn.jsdelivr.net`). Without it the index falls back to a deterministic hash embedding — functional but less accurate for semantic search.

`watchdog` enables the `gkt watch` live file watcher. Without it, you can still run `gkt graph --incremental` manually.

## Quick Start (one command)

```bash
python .agent/skills/code-graph-index/scripts/setup_mcp.py --all
```

This will:

1. Build the structural graph → `.code-graph-index/graph.json`
2. Build the FAISS index → `.code-graph-index/faiss-index/{code.index, metadata.json}`
3. Write MCP config for every IDE present in the working dir:
   - `~/.gemini/antigravity/mcp_config.json` — universal servers shared across all projects (`document-reader`)
   - `.mcp.json` — project-scoped servers (`code-graph`, `faiss-code-index`, `brain-manager`, `skill-router`); read by both Antigravity AND Claude Code
   - `.kiro/settings/mcp.json` — Kiro IDE
   - `.cursor/mcp.json` / `.windsurf/mcp.json` — Cursor / Windsurf
   - `~/.codex/config.toml` (universal) + `.codex/config.toml` (project) — Codex CLI (TOML format)

> **Why split?** Project-local servers carry per-project data paths (FAISS index, brain dir, graph). If they live in the global Antigravity config, the path of one project leaks into every other workspace, causing wrong-project lookups and timeouts. The split keeps universal tooling global and per-project tooling local.

> **`.claude/mcp_servers.json` is no longer written** — current Claude Code reads `.mcp.json` at the project root. Older copies of that file are deleted automatically on the next `setup_mcp.py` run.

To use ONNX embeddings (recommended for best search quality):

```bash
python .agent/skills/code-graph-index/scripts/setup_mcp.py --all --ensure-model
```

This downloads the ONNX model (~23 MB) from `cdn.jsdelivr.net` on first run, then uses it for all subsequent FAISS index builds.

## Step-by-step usage

### 1. Build the structural graph

```bash
python .agent/skills/code-graph-index/scripts/build_graph.py --path .
```

Output: `.code-graph-index/graph.json` containing:

- `nodes`: `{id, kind, name, path, line, end_line, content_hash, byte_offset, byte_length}` for every file, class, function, import.
- `edges`: `{src, dst, kind}` where `kind ∈ {contains, imports, calls, references}`.
- `metadata`: file mtimes, `dirty_nodes` list (for incremental FAISS), and `incremental_stats` for performance tracking.

Python parsing uses AST with `end_lineno` for accurate function boundaries.
Method-level call tracking resolves `self.method()` calls within classes.

Add `--incremental` after the first build for fast re-indexing. The incremental engine compares **per-node content hashes** to identify exactly which functions/classes changed — unchanged nodes are marked clean so FAISS can skip re-embedding them.

Supported languages: Python, JavaScript, TypeScript, Java, C#, Go.

### 2. Build the Hybrid FAISS semantic index

```bash
python .agent/skills/code-graph-index/scripts/build_faiss_index.py --project-root .
```

Output: `.code-graph-index/faiss-index/code.index` and `metadata.json`.

Embedding strategy (auto-selected):

| Strategy | Requires | Quality | Model Source |
|---|---|---|---|
| **OnnxEmbedder** | `onnxruntime` | ★★★★★ | Bundled in skill (~16 MB gzip, extracted on first use) |
| **HashEmbedder** | only `numpy` | ★★☆☆☆ | No model needed |

**Dependencies:** If `faiss-cpu` or `onnxruntime` are missing, the `setup_mcp.py` script will **automatically install them** via `pip`.
**Performance:** Embedding runs across multiple threads (limited to 50% of CPU cores) to ensure fast semantic indexing without overloading the host machine.

The ONNX model (`all-MiniLM-L6-v2` INT8 quantized) is **shipped with GravityKit** as compressed `.gz` files.
On first build it extracts to `.code-graph-index/model/` — no network required.
If the bundled files are missing, it falls back to downloading from `cdn.jsdelivr.net`.

### 3. Generate MCP config

```bash
python .agent/skills/code-graph-index/scripts/setup_mcp.py --ides antigravity,kiro,claude
```

Or auto-detect every IDE by scanning the working dir:

```bash
python .agent/skills/code-graph-index/scripts/setup_mcp.py --auto
```

Produces config entries for:

- `code-graph` — structural graph queries (`graph_mcp_server.py`)
- `faiss-code-index` — semantic chunk search (`faiss_mcp_server.py`)

### 4. Run the MCP servers

The IDE will normally launch them on demand via the generated config. To run manually:

```bash
python .agent/skills/code-graph-index/scripts/graph_mcp_server.py \
  --graph .code-graph-index/graph.json

python .agent/skills/code-graph-index/scripts/faiss_mcp_server.py \
  --index-dir .code-graph-index/faiss-index
```

## MCP tools exposed

### `code-graph` server

| Tool | Purpose |
|---|---|
| `list_graph_stats` | Counts of files, nodes, edges; languages; last build time. |
| `search_symbols(query, kind?)` | Find symbols by name / signature. Returns `{name, kind, path, line}`. |
| `get_neighbors(node_id, edge_kind?, depth?)` | Traverse `contains` / `imports` / `calls` edges. |
| `find_callers(symbol)` | Reverse call graph — who calls this function. |
| `outline(path?)` | Compact per-file symbol outline (huge token saver). |
| `get_lineage(node_id)` | Full source provenance: byte range, content hash, file hash. |
| `blast_radius(node_id, max_depth?)` | Impact analysis: find all nodes affected if this one changes. |

### `faiss-code-index` server

| Tool | Purpose |
|---|---|
| `search_code_chunks(query, top_k?)` | Semantic node search (Hybrid RAG) — returns `{node_id, kind, path, start_line, end_line, preview, score}`. |

Combine both: use FAISS to find candidate graph nodes, then `get_neighbors` to widen context along call edges — the graph keeps the agent grounded, FAISS keeps it discoverable. Use `blast_radius` before refactoring to understand downstream impact.

### Live watch mode

```bash
gkt watch                   # Start with default 2s debounce
gkt watch --debounce 1000   # Faster updates (1s)
gkt watch --verbose         # Show each file change event
```

The watcher monitors code files for changes and automatically triggers incremental graph + FAISS rebuilds. MCP servers auto-detect updated index files via mtime checks — no restart required.

## IDE config locations

| IDE | File | Format | Scope | Servers |
|---|---|---|---|---|
| Antigravity (global) | `~/.gemini/antigravity/mcp_config.json` | JSON | User-wide | `document-reader` |
| Antigravity / Claude Code (project) | `.mcp.json` | JSON | Project | `code-graph`, `faiss-code-index`, `brain-manager`, `skill-router` |
| Kiro | `.kiro/settings/mcp.json` | JSON | Project | All servers (`disabled: false` enables) |
| Cursor | `.cursor/mcp.json` | JSON | Project | All servers |
| Windsurf | `.windsurf/mcp.json` | JSON | Project | All servers |
| Codex CLI (global) | `~/.codex/config.toml` | TOML | User-wide | `document-reader` |
| Codex CLI (project) | `.codex/config.toml` | TOML | Project | `code-graph`, `faiss-code-index`, `brain-manager`, `skill-router` |

**Reconciliation rules** in `setup_mcp.py`:

- Owned entries (the 5 servers above) are merged in / refreshed on every run.
- Owned entries that don't belong in a given file are **removed** (e.g. `code-graph` is purged from the global Antigravity / Codex config — fixes leaks from older versions where every project overwrote global with its own paths).
- Legacy server names (`code-review-graph`) are scrubbed from any file we touch.
- Third-party MCP servers in the same file are left **untouched**.
- For Codex (TOML), top-level scalars (`model`, `model_reasoning_effort`) and unrelated tables (`[windows]`, `[projects.*]`) are preserved; only `[mcp_servers.*]` sub-sections are reconciled. Reading TOML requires Python 3.11+ (`tomllib`); on older interpreters the existing config is backed up to `.bak` before rewrite.

> **Codex trust note**: Codex only loads `./.codex/config.toml` for projects flagged as trusted. After running `gkt mcp`, run `codex` once in the project directory and accept the trust prompt, or add the project path under `[projects]` in `~/.codex/config.toml` with `trust_level = "trusted"`.

## Output layout

```
<project>/
├── .agent/skills/code-graph-index/
│   └── model/                      ← bundled ONNX model (gzip compressed)
│       ├── model.onnx.gz           ← all-MiniLM-L6-v2 INT8 (~15.8 MB)
│       └── vocab.txt.gz            ← WordPiece vocabulary (~100 KB)
├── .code-graph-index/              ← generated artifacts (gitignored)
│   ├── graph.json                  ← structural graph (nodes with end_line)
│   ├── model/                      ← extracted ONNX model (auto on first use)
│   │   ├── model.onnx              ← ~21.9 MB decompressed
│   │   └── vocab.txt               ← ~232 KB decompressed
│   └── faiss-index/
│       ├── code.index              ← FAISS index
│       └── metadata.json           ← chunk metadata + embedding strategy
├── .mcp.json                       ← Antigravity / Claude Code project config
└── .kiro/settings/mcp.json         ← Kiro IDE config (only if .kiro/ exists)
```

User-level (Antigravity only):

```
~/.gemini/antigravity/mcp_config.json   ← universal servers (document-reader)
```

## Notes

- 100% local — no source code leaves the machine.
- ONNX model is **bundled** — no network required for first run.
- Falls back to `cdn.jsdelivr.net` download if bundled `.gz` files are missing.
- `.code-graph-index/` should be added to `.gitignore` (the skill writes one automatically the first time).
- Re-run `setup_mcp.py --rebuild` after large code changes; `--incremental` on the graph keeps day-to-day rebuilds fast.
- **Fine-grained incremental**: only nodes with changed `content_hash` are re-embedded, saving 80-95% of embedding time for typical edits.
- **Watch mode**: `gkt watch` auto-syncs the index on every file save. MCP servers hot-reload via mtime checks.
- **Data lineage**: each node carries `byte_offset`, `byte_length`, and `content_hash` for precise source traceability.
- Pairs naturally with `codebase-navigator` (regex symbol search) and `vector-index-tuning` (encoder tuning).

## Custom CDN source

To override the CDN fallback, set `GKT_MODEL_CDN` to a base URL:

```bash
export GKT_MODEL_CDN=https://cdn.jsdelivr.net/gh/{owner}/{repo}@{tag}/all-MiniLM-L6-v2
```

The tool will append `/model_quantized.onnx` and `/vocab.txt` to the base.
