---
name: code-graph-index
description: Build a hybrid code knowledge base — symbolic graph (functions, classes, imports, call edges) plus a FAISS semantic vector index — and auto-wire MCP servers into Antigravity, Kiro, and Claude Code so any AI agent can search, traverse, and reason about the codebase locally without re-reading whole files.
risk: safe
source: VibeGravityKit (merged from code-review-graph)
---

# Code Graph Index (Graph + FAISS + MCP)

A token-saving, fully local code intelligence layer for AI agents.

This skill turns any repository into:

1. A **structural graph** — files, classes, functions, imports, and call edges saved as JSON with docstrings/snippets.
2. A **Hybrid FAISS semantic index** — vector search directly over the structural graph nodes (Hybrid RAG) for lightning-fast, highly accurate API discovery.
3. Two **MCP servers** that expose the graph and the index to any MCP-aware IDE.
4. An auto-generated **MCP config** wired into Antigravity, Kiro, and Claude Code.

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
```

`faiss-cpu` and `mcp` are optional — install only if you want semantic search and the MCP servers running. The graph builder works with stdlib alone.

`onnxruntime` enables **all-MiniLM-L6-v2** sentence embeddings (~23 MB INT8-quantized model, auto-downloaded from `cdn.jsdelivr.net`). Without it the index falls back to a deterministic hash embedding — functional but less accurate for semantic search.

## Quick Start (one command)

```bash
python .agent/skills/code-graph-index/scripts/setup_mcp.py --all
```

This will:

1. Build the structural graph → `.code-graph-index/graph.json`
2. Build the FAISS index → `.code-graph-index/faiss-index/{code.index, metadata.json}`
3. Write MCP config for every IDE present in the working dir:
   - `.mcp.json` (Antigravity, Claude Code, generic MCP clients)
   - `.kiro/settings/mcp.json` (Kiro IDE)
   - `.claude/mcp_servers.json` (Claude Code project-scoped fallback)

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

- `nodes`: `{id, kind, name, path, line, end_line}` for every file, class, function, import.
- `edges`: `{src, dst, kind}` where `kind ∈ {contains, imports, calls, references}`.
- `metadata`: file mtimes for incremental rebuilds.

Python parsing uses AST with `end_lineno` for accurate function boundaries.
Method-level call tracking resolves `self.method()` calls within classes.

Add `--incremental` after the first build for fast re-indexing.

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
| `outline(path?)` | Compact per-file symbol outline (huge token saver). Supports path prefix filter. |
| `get_review_context(path, depth?)` | **Review context** for a file/module: outline + incoming/outgoing edges + coupling score. |
| `get_architecture_overview(limit?)` | **Architecture map**: top-level modules, symbol counts, cross-module coupling. Use first! |
| `get_impact_radius(node_id, depth?)` | **Blast radius** of a symbol: what it affects + what depends on it. |
| `find_hotspots(top_n?)` | Most-connected symbols (architectural hotspots with high change risk). |
| `find_dependencies(path)` | Dependency view: what a file imports/calls and who imports/calls it. |

### `faiss-code-index` server

| Tool | Purpose |
|---|---|
| `search_code_chunks(query, top_k?)` | Semantic node search (Hybrid RAG) — returns `{node_id, kind, path, start_line, end_line, preview, score}`. |

Combine both: use FAISS to find candidate graph nodes, then `get_neighbors` to widen context along call edges — the graph keeps the agent grounded, FAISS keeps it discoverable.

## IDE config locations

| IDE | File | How it picks up |
|---|---|---|
| Antigravity / Claude Code (project) | `.mcp.json` | Auto-loaded from repo root. |
| Claude Code (alt) | `.claude/mcp_servers.json` | Project-scoped fallback. |
| Kiro | `.kiro/settings/mcp.json` | Kiro reads on workspace open; `disabled: false` enables. |
| Cursor / Windsurf | Append to existing MCP config if present. | |

`setup_mcp.py` writes only the entries it owns and merges with any pre-existing servers — it never overwrites unrelated keys.

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
├── .kiro/settings/mcp.json         ← Kiro IDE config (only if .kiro/ exists)
└── .claude/mcp_servers.json        ← Claude Code project fallback
```

## Notes

- 100% local — no source code leaves the machine.
- ONNX model is **bundled** — no network required for first run.
- Falls back to `cdn.jsdelivr.net` download if bundled `.gz` files are missing.
- `.code-graph-index/` should be added to `.gitignore` (the skill writes one automatically the first time).
- Re-run `setup_mcp.py --rebuild` after large code changes; `--incremental` on the graph keeps day-to-day rebuilds fast.
- Pairs naturally with `codebase-navigator` (regex symbol search) and `vector-index-tuning` (encoder tuning).

## Custom CDN source

To override the CDN fallback, set `GKT_MODEL_CDN` to a base URL:

```bash
export GKT_MODEL_CDN=https://cdn.jsdelivr.net/gh/{owner}/{repo}@{tag}/all-MiniLM-L6-v2
```

The tool will append `/model_quantized.onnx` and `/vocab.txt` to the base.
