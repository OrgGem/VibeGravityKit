#!/usr/bin/env python3
"""
graph_mcp_server.py — MCP server exposing the structural code graph.

Tools (original):
    list_graph_stats()                                  → file/node/edge counts + langs
    search_symbols(query, kind=None, limit=50)          → matching symbols
    get_neighbors(node_id, edge_kind=None, depth=1)     → adjacent nodes
    find_callers(symbol)                                → reverse call graph
    outline(path=None)                                  → compact per-file symbol view

Tools (review & architecture):
    get_review_context(path, depth=1)                   → review context for a path/module
    get_architecture_overview(limit=30)                  → top-level module summary
    get_impact_radius(node_id, depth=2)                 → blast radius of a symbol
    find_hotspots(top_n=15)                             → most-connected symbols
    find_dependencies(path)                             → what a file imports + who imports it
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]

mcp = FastMCP("code-graph") if FastMCP is not None else None
_GRAPH: dict | None = None
_GRAPH_PATH: str = ".code-graph-index/graph.json"


def _load() -> dict:
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    p = Path(_GRAPH_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Graph file not found: {p}. Run build_graph.py first.")
    _GRAPH = json.loads(p.read_text(encoding="utf-8"))
    return _GRAPH


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _nodes_by_id(g: dict) -> dict[str, dict]:
    return {n["id"]: n for n in g.get("nodes", [])}


def _edges_from(g: dict) -> dict[str, list[dict]]:
    """Build adjacency map: src → list of edges."""
    adj: dict[str, list[dict]] = defaultdict(list)
    for e in g.get("edges", []):
        adj[e["src"]].append(e)
    return adj


def _edges_to(g: dict) -> dict[str, list[dict]]:
    """Build reverse adjacency map: dst → list of edges."""
    adj: dict[str, list[dict]] = defaultdict(list)
    for e in g.get("edges", []):
        adj[e["dst"]].append(e)
    return adj


def _match_path(node_path: str | None, filter_path: str) -> bool:
    """Check if node_path matches the filter (prefix or substring)."""
    if not node_path:
        return False
    fp = filter_path.replace("\\", "/").rstrip("/")
    np = node_path.replace("\\", "/")
    return np.startswith(fp) or fp in np


# ---------------------------------------------------------------------------
# Original tools
# ---------------------------------------------------------------------------

def list_graph_stats() -> dict:
    """Return counts of files, nodes, edges + detected languages and last build time."""
    g = _load()
    return {
        "counts": g.get("metadata", {}).get("counts", {}),
        "languages": g.get("metadata", {}).get("languages", []),
        "generated_at": g.get("metadata", {}).get("generated_at"),
        "root": g.get("metadata", {}).get("root"),
    }


def search_symbols(query: str, kind: str | None = None, limit: int = 50) -> dict:
    """Find symbols by name or signature substring (case-insensitive)."""
    g = _load()
    q = query.lower()
    hits = []
    for node in g.get("nodes", []):
        if kind and node.get("kind") != kind:
            continue
        name = (node.get("name") or "").lower()
        sig = (node.get("signature") or "").lower()
        if q in name or q in sig:
            hits.append({
                "id": node.get("id"),
                "kind": node.get("kind"),
                "name": node.get("name"),
                "path": node.get("path"),
                "line": node.get("line"),
                "signature": node.get("signature"),
            })
            if len(hits) >= limit:
                break
    return {"query": query, "kind": kind, "count": len(hits), "results": hits}


def get_neighbors(node_id: str, edge_kind: str | None = None, depth: int = 1) -> dict:
    """Traverse outgoing edges from a node up to `depth` hops."""
    g = _load()
    edges = g.get("edges", [])
    nodes_by_id = {n["id"]: n for n in g.get("nodes", [])}
    visited = {node_id}
    frontier = {node_id}
    layers: list[list[dict]] = []
    for _ in range(max(1, depth)):
        next_frontier: set[str] = set()
        layer: list[dict] = []
        for src in frontier:
            for e in edges:
                if e["src"] != src:
                    continue
                if edge_kind and e["kind"] != edge_kind:
                    continue
                dst = e["dst"]
                if dst in visited:
                    continue
                visited.add(dst)
                next_frontier.add(dst)
                layer.append({
                    "edge_kind": e["kind"],
                    "src": src,
                    "dst": dst,
                    "node": nodes_by_id.get(dst),
                })
        layers.append(layer)
        frontier = next_frontier
        if not frontier:
            break
    return {"node_id": node_id, "edge_kind": edge_kind, "depth": depth, "layers": layers}


def find_callers(symbol: str) -> dict:
    """Return all nodes that have a `calls` edge into the given symbol name."""
    g = _load()
    nodes_by_id = {n["id"]: n for n in g.get("nodes", [])}
    callers = []
    for e in g.get("edges", []):
        if e["kind"] != "calls":
            continue
        if e["dst"] == symbol or e["dst"].endswith(f"::{symbol}") or _name_match(e["dst"], symbol):
            src_node = nodes_by_id.get(e["src"])
            if src_node:
                callers.append(src_node)
    return {"symbol": symbol, "count": len(callers), "callers": callers}


def _name_match(node_id: str, symbol: str) -> bool:
    if "::" in node_id:
        rest = node_id.split("::", 1)[1]
        name = rest.split("@", 1)[0]
        return name == symbol
    return False


def outline(path: str | None = None) -> dict:
    """Compact outline: file → list of (kind, name, line). Optional path filter."""
    g = _load()
    by_file: dict[str, list[dict]] = {}
    for n in g.get("nodes", []):
        if n.get("kind") == "file":
            continue
        p = n.get("path")
        if path and not _match_path(p, path):
            continue
        by_file.setdefault(p, []).append({
            "kind": n.get("kind"),
            "name": n.get("name"),
            "line": n.get("line"),
        })
    for v in by_file.values():
        v.sort(key=lambda x: x.get("line") or 0)
    return {"file_count": len(by_file), "files": by_file}


# ---------------------------------------------------------------------------
# NEW: Review & Architecture tools
# ---------------------------------------------------------------------------

def get_review_context(path: str, depth: int = 1) -> dict:
    """Get review-oriented context for a file or directory path.

    Returns:
      - outline of all symbols in the target path
      - incoming edges (who calls/imports this module)
      - outgoing edges (what this module calls/imports)
      - key metrics (symbol count, coupling score)

    Perfect for code review: tells you what a module does AND what it touches.

    Args:
        path: File path or directory prefix to analyze (e.g. "src/auth" or "src/auth/login.ts").
        depth: How many hops of edges to include. Default: 1.
    """
    g = _load()
    nbi = _nodes_by_id(g)

    # Find all nodes in this path
    target_nodes: dict[str, dict] = {}
    target_files: set[str] = set()
    for n in g.get("nodes", []):
        if _match_path(n.get("path"), path):
            target_nodes[n["id"]] = n
            if n.get("kind") == "file":
                target_files.add(n["id"])

    if not target_nodes:
        return {"error": f"No symbols found matching path: {path}", "path": path}

    # Classify edges
    internal_edges = []
    outgoing_edges = []  # from target → outside
    incoming_edges = []  # from outside → target
    for e in g.get("edges", []):
        src_in = e["src"] in target_nodes
        dst_in = e["dst"] in target_nodes
        if src_in and dst_in:
            internal_edges.append(e)
        elif src_in and not dst_in:
            dst_node = nbi.get(e["dst"])
            outgoing_edges.append({
                "kind": e["kind"],
                "from": e["src"],
                "to": e["dst"],
                "to_path": dst_node.get("path") if dst_node else None,
            })
        elif not src_in and dst_in:
            src_node = nbi.get(e["src"])
            incoming_edges.append({
                "kind": e["kind"],
                "from": e["src"],
                "from_path": src_node.get("path") if src_node else None,
                "to": e["dst"],
            })

    # Build outline
    symbols = []
    for nid, n in target_nodes.items():
        if n.get("kind") == "file":
            continue
        symbols.append({
            "kind": n.get("kind"),
            "name": n.get("name"),
            "path": n.get("path"),
            "line": n.get("line"),
            "signature": n.get("signature"),
        })
    symbols.sort(key=lambda x: (x.get("path", ""), x.get("line") or 0))

    # Coupling: unique external modules touched
    ext_modules = set()
    for e in outgoing_edges + incoming_edges:
        p = e.get("to_path") or e.get("from_path")
        if p:
            # Get directory-level module
            parts = p.replace("\\", "/").split("/")
            if len(parts) > 1:
                ext_modules.add(parts[0] + "/" + parts[1] if len(parts) > 2 else parts[0])
            else:
                ext_modules.add(parts[0])

    return {
        "path": path,
        "files": len(target_files),
        "symbols": len(symbols),
        "symbol_list": symbols[:100],
        "internal_edges": len(internal_edges),
        "outgoing": outgoing_edges[:50],
        "incoming": incoming_edges[:50],
        "coupling_score": len(ext_modules),
        "coupled_modules": sorted(ext_modules)[:20],
        "summary": (
            f"{path}: {len(symbols)} symbols across {len(target_files)} files. "
            f"Coupling: {len(ext_modules)} external modules. "
            f"{len(incoming_edges)} incoming, {len(outgoing_edges)} outgoing edges."
        ),
    }


def get_architecture_overview(limit: int = 30) -> dict:
    """Generate a compact architecture overview of the project.

    Groups files by top-level directory, shows:
      - Per-module: file count, symbol count, primary language
      - Cross-module coupling (import/call edges between modules)
      - Key entry points (files with many incoming edges)

    Use this as the FIRST tool call when exploring any new codebase.

    Args:
        limit: Max number of modules to show. Default: 30.
    """
    g = _load()
    nbi = _nodes_by_id(g)
    stats = g.get("metadata", {})

    # Group nodes by top-level directory
    modules: dict[str, dict] = defaultdict(lambda: {
        "files": set(), "symbols": 0, "languages": Counter(),
        "kinds": Counter()
    })

    for n in g.get("nodes", []):
        p = (n.get("path") or "").replace("\\", "/")
        parts = p.split("/")
        # Use first 1-2 path segments as module name
        if len(parts) >= 2:
            mod = parts[0] + "/" + parts[1]
        else:
            mod = parts[0]

        if n.get("kind") == "file":
            modules[mod]["files"].add(p)
            lang = n.get("language") or g.get("files", {}).get(p, {}).get("language", "")
            if lang:
                modules[mod]["languages"][lang] += 1
        else:
            modules[mod]["symbols"] += 1
            modules[mod]["kinds"][n.get("kind", "?")] += 1

    # Cross-module edges
    cross_edges: Counter = Counter()
    for e in g.get("edges", []):
        if e["kind"] == "contains":
            continue
        src_node = nbi.get(e["src"])
        dst_node = nbi.get(e["dst"])
        if not src_node or not dst_node:
            continue
        sp = (src_node.get("path") or "").replace("\\", "/").split("/")
        dp = (dst_node.get("path") or "").replace("\\", "/").split("/")
        src_mod = sp[0] + "/" + sp[1] if len(sp) >= 2 else sp[0]
        dst_mod = dp[0] + "/" + dp[1] if len(dp) >= 2 else dp[0]
        if src_mod != dst_mod:
            key = f"{src_mod} → {dst_mod}"
            cross_edges[key] += 1

    # Build module summary
    module_list = []
    for mod, data in sorted(modules.items(), key=lambda x: -x[1]["symbols"]):
        top_lang = data["languages"].most_common(1)
        module_list.append({
            "module": mod,
            "files": len(data["files"]),
            "symbols": data["symbols"],
            "language": top_lang[0][0] if top_lang else "?",
            "breakdown": dict(data["kinds"]),
        })

    return {
        "project_root": stats.get("root"),
        "total_files": stats.get("counts", {}).get("files", 0),
        "total_symbols": stats.get("counts", {}).get("nodes", 0),
        "total_edges": stats.get("counts", {}).get("edges", 0),
        "languages": stats.get("languages", []),
        "modules": module_list[:limit],
        "cross_module_coupling": [
            {"edge": k, "count": v}
            for k, v in cross_edges.most_common(20)
        ],
        "summary": (
            f"Project has {stats.get('counts', {}).get('files', 0)} files, "
            f"{stats.get('counts', {}).get('nodes', 0)} symbols, "
            f"{len(module_list)} modules. "
            f"Languages: {', '.join(stats.get('languages', []))}."
        ),
    }


def get_impact_radius(node_id: str, depth: int = 2) -> dict:
    """Analyze the blast radius of a symbol — what it touches and what touches it.

    Performs bidirectional BFS from the given node to find all reachable
    symbols within `depth` hops. Useful for understanding the risk of
    modifying a specific function or class.

    Args:
        node_id: The ID of the node to analyze (e.g. "src/auth.ts::login@15").
        depth: Max BFS hops in each direction. Default: 2.
    """
    g = _load()
    nbi = _nodes_by_id(g)
    edges_fwd = _edges_from(g)
    edges_rev = _edges_to(g)

    if node_id not in nbi:
        # Try fuzzy match
        candidates = [nid for nid in nbi if node_id in nid]
        if not candidates:
            return {"error": f"Node not found: {node_id}"}
        node_id = candidates[0]

    # BFS forward (what this node affects)
    fwd_visited: set[str] = {node_id}
    fwd_frontier: set[str] = {node_id}
    affected: list[dict] = []
    for d in range(depth):
        next_f: set[str] = set()
        for nid in fwd_frontier:
            for e in edges_fwd.get(nid, []):
                if e["kind"] == "contains":
                    continue
                dst = e["dst"]
                if dst not in fwd_visited:
                    fwd_visited.add(dst)
                    next_f.add(dst)
                    dn = nbi.get(dst)
                    if dn:
                        affected.append({
                            "id": dst,
                            "kind": dn.get("kind"),
                            "name": dn.get("name"),
                            "path": dn.get("path"),
                            "hop": d + 1,
                            "via_edge": e["kind"],
                        })
        fwd_frontier = next_f

    # BFS backward (what depends on this node)
    rev_visited: set[str] = {node_id}
    rev_frontier: set[str] = {node_id}
    dependents: list[dict] = []
    for d in range(depth):
        next_r: set[str] = set()
        for nid in rev_frontier:
            for e in edges_rev.get(nid, []):
                if e["kind"] == "contains":
                    continue
                src = e["src"]
                if src not in rev_visited:
                    rev_visited.add(src)
                    next_r.add(src)
                    sn = nbi.get(src)
                    if sn:
                        dependents.append({
                            "id": src,
                            "kind": sn.get("kind"),
                            "name": sn.get("name"),
                            "path": sn.get("path"),
                            "hop": d + 1,
                            "via_edge": e["kind"],
                        })
        rev_frontier = next_r

    # Affected files
    affected_files = sorted({
        a["path"] for a in affected + dependents if a.get("path")
    })
    source = nbi[node_id]

    return {
        "node": {
            "id": node_id,
            "kind": source.get("kind"),
            "name": source.get("name"),
            "path": source.get("path"),
        },
        "depth": depth,
        "affects": affected[:50],
        "affected_by": dependents[:50],
        "affected_files": affected_files[:30],
        "blast_radius": len(affected) + len(dependents),
        "summary": (
            f"{source.get('name')}: affects {len(affected)} symbols, "
            f"depended on by {len(dependents)} symbols, "
            f"spanning {len(affected_files)} files."
        ),
    }


def find_hotspots(top_n: int = 15) -> dict:
    """Find the most connected symbols (architectural hotspots).

    Hotspots have the highest combined in+out degree (excluding 'contains' edges).
    Changes to hotspots have disproportionate blast radius.

    Args:
        top_n: Number of top hotspots to return. Default: 15.
    """
    g = _load()
    nbi = _nodes_by_id(g)
    degree: Counter = Counter()

    for e in g.get("edges", []):
        if e["kind"] == "contains":
            continue
        # Only count edges whose endpoints are real graph nodes
        if e["src"] in nbi:
            degree[e["src"]] += 1
        if e["dst"] in nbi:
            degree[e["dst"]] += 1

    results = []
    for nid, deg in degree.most_common(top_n * 3):
        node = nbi.get(nid)
        if not node or node.get("kind") == "file":
            continue
        results.append({
            "id": nid,
            "kind": node.get("kind"),
            "name": node.get("name"),
            "path": node.get("path"),
            "line": node.get("line"),
            "degree": deg,
        })
        if len(results) >= top_n:
            break

    return {
        "top_n": top_n,
        "count": len(results),
        "hotspots": results,
        "summary": (
            f"Top {len(results)} hotspots: "
            + ", ".join(f"{r['name']}({r['degree']})" for r in results[:5])
            + ("..." if len(results) > 5 else "")
        ),
    }


def find_dependencies(path: str) -> dict:
    """Show what a file/module imports and who imports it.

    A focused dependency view for a specific path. Shows:
      - imports_out: what this file/module imports
      - imports_in: who imports this file/module
      - calls_out: external functions this module calls
      - calls_in: external functions calling into this module

    Args:
        path: File path or directory prefix (e.g. "src/auth" or "src/auth/login.ts").
    """
    g = _load()
    nbi = _nodes_by_id(g)

    # Find target node IDs
    target_ids: set[str] = set()
    for n in g.get("nodes", []):
        if _match_path(n.get("path"), path):
            target_ids.add(n["id"])

    if not target_ids:
        return {"error": f"No nodes found matching: {path}", "path": path}

    imports_out: list[dict] = []
    imports_in: list[dict] = []
    calls_out: list[dict] = []
    calls_in: list[dict] = []

    for e in g.get("edges", []):
        src_in = e["src"] in target_ids
        dst_in = e["dst"] in target_ids
        if src_in and not dst_in:
            target = nbi.get(e["dst"])
            entry = {
                "kind": e["kind"],
                "target": e["dst"],
                "target_path": target.get("path") if target else None,
            }
            if e["kind"] == "imports":
                imports_out.append(entry)
            elif e["kind"] == "calls":
                calls_out.append(entry)
        elif not src_in and dst_in:
            source = nbi.get(e["src"])
            entry = {
                "kind": e["kind"],
                "source": e["src"],
                "source_path": source.get("path") if source else None,
            }
            if e["kind"] == "imports":
                imports_in.append(entry)
            elif e["kind"] == "calls":
                calls_in.append(entry)

    return {
        "path": path,
        "imports_out": imports_out[:30],
        "imports_in": imports_in[:30],
        "calls_out": calls_out[:30],
        "calls_in": calls_in[:30],
        "summary": (
            f"{path}: imports {len(imports_out)} modules, "
            f"imported by {len(imports_in)} modules, "
            f"calls {len(calls_out)} external symbols, "
            f"called by {len(calls_in)} external symbols."
        ),
    }


# ---------------------------------------------------------------------------
# Register all tools with MCP
# ---------------------------------------------------------------------------

if mcp is not None:
    # Original tools
    mcp.tool()(list_graph_stats)
    mcp.tool()(search_symbols)
    mcp.tool()(get_neighbors)
    mcp.tool()(find_callers)
    mcp.tool()(outline)
    # Review & architecture tools
    mcp.tool()(get_review_context)
    mcp.tool()(get_architecture_overview)
    mcp.tool()(get_impact_radius)
    mcp.tool()(find_hotspots)
    mcp.tool()(find_dependencies)


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server for code structural graph")
    parser.add_argument("--graph", default=".code-graph-index/graph.json",
                        help="Path to graph.json")
    args = parser.parse_args()

    global _GRAPH_PATH
    _GRAPH_PATH = str(Path(args.graph).resolve())

    if mcp is None:
        raise RuntimeError("mcp package is required. Install with: pip install mcp")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
