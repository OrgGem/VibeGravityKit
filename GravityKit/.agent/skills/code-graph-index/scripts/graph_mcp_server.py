#!/usr/bin/env python3
"""
graph_mcp_server.py — MCP server exposing the structural code graph.

Tools:
    list_graph_stats()                                  → file/node/edge counts + langs
    search_symbols(query, kind=None, limit=50)          → matching symbols
    get_neighbors(node_id, edge_kind=None, depth=1)     → adjacent nodes
    find_callers(symbol)                                → reverse call graph
    outline(path=None)                                  → compact per-file symbol view
    get_lineage(node_id)                                → full source provenance (Phase D)
    blast_radius(node_id, max_depth=3)                  → impact analysis (Phase D)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]

mcp = FastMCP("code-graph") if FastMCP is not None else None
_GRAPH: dict | None = None
_GRAPH_PATH: str = ".code-graph-index/graph.json"
_GRAPH_MTIME: float = 0


def _load() -> dict:
    """Load graph with mtime-based cache invalidation for hot-reload (Phase B4)."""
    global _GRAPH, _GRAPH_MTIME
    p = Path(_GRAPH_PATH)
    if not p.exists():
        raise FileNotFoundError(f"Graph file not found: {p}. Run build_graph.py first.")
    current_mtime = p.stat().st_mtime
    if _GRAPH is not None and abs(current_mtime - _GRAPH_MTIME) < 1e-6:
        return _GRAPH
    _GRAPH = json.loads(p.read_text(encoding="utf-8"))
    _GRAPH_MTIME = current_mtime
    return _GRAPH


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
        if path and p != path:
            continue
        by_file.setdefault(p, []).append({
            "kind": n.get("kind"),
            "name": n.get("name"),
            "line": n.get("line"),
        })
    for v in by_file.values():
        v.sort(key=lambda x: x.get("line") or 0)
    return {"file_count": len(by_file), "files": by_file}


def get_lineage(node_id: str) -> dict:
    """Return full source provenance for a node: file, byte range, content hash."""
    g = _load()
    nodes_by_id = {n["id"]: n for n in g.get("nodes", [])}
    node = nodes_by_id.get(node_id)
    if not node:
        return {"error": f"Node not found: {node_id}"}

    file_info = g.get("files", {}).get(node.get("path", ""), {})
    return {
        "node_id": node_id,
        "kind": node.get("kind"),
        "name": node.get("name"),
        "path": node.get("path"),
        "line": node.get("line"),
        "end_line": node.get("end_line"),
        "byte_offset": node.get("byte_offset"),
        "byte_length": node.get("byte_length"),
        "content_hash": node.get("content_hash"),
        "source_file_hash": file_info.get("hash"),
    }


def blast_radius(node_id: str, max_depth: int = 3) -> dict:
    """Find all nodes affected if this node changes (reverse call/import graph).

    Traces: callers → their callers (up to max_depth hops) + importers.
    Useful for impact analysis before refactoring.
    """
    g = _load()
    nodes_by_id = {n["id"]: n for n in g.get("nodes", [])}
    edges = g.get("edges", [])

    if node_id not in nodes_by_id:
        return {"error": f"Node not found: {node_id}"}

    # Build reverse edge map (dst -> list of src)
    reverse_map: dict[str, list[tuple[str, str]]] = {}  # dst -> [(src, edge_kind)]
    for e in edges:
        if e["kind"] in ("calls", "imports", "references"):
            reverse_map.setdefault(e["dst"], []).append((e["src"], e["kind"]))

    # Also handle name-based matching for unresolved call edges
    target_node = nodes_by_id[node_id]
    target_name = target_node.get("name", "")

    # BFS from node_id along reverse edges
    visited: dict[str, int] = {node_id: 0}  # node_id -> distance
    frontier = {node_id}
    affected: list[dict] = []

    for depth in range(1, max_depth + 1):
        next_frontier: set[str] = set()
        for nid in frontier:
            # Direct reverse edges
            for src, edge_kind in reverse_map.get(nid, []):
                if src not in visited:
                    visited[src] = depth
                    next_frontier.add(src)
                    src_node = nodes_by_id.get(src)
                    if src_node:
                        affected.append({
                            "node_id": src,
                            "kind": src_node.get("kind"),
                            "name": src_node.get("name"),
                            "path": src_node.get("path"),
                            "line": src_node.get("line"),
                            "distance": depth,
                            "via_edge": edge_kind,
                        })
            # Name-based matching (for unresolved edges like "calls" -> "func_name")
            if nid == node_id:
                for src, edge_kind in reverse_map.get(target_name, []):
                    if src not in visited:
                        visited[src] = depth
                        next_frontier.add(src)
                        src_node = nodes_by_id.get(src)
                        if src_node:
                            affected.append({
                                "node_id": src,
                                "kind": src_node.get("kind"),
                                "name": src_node.get("name"),
                                "path": src_node.get("path"),
                                "line": src_node.get("line"),
                                "distance": depth,
                                "via_edge": edge_kind,
                            })
        frontier = next_frontier
        if not frontier:
            break

    return {
        "node_id": node_id,
        "max_depth": max_depth,
        "affected_count": len(affected),
        "affected": affected,
    }


if mcp is not None:
    mcp.tool()(list_graph_stats)
    mcp.tool()(search_symbols)
    mcp.tool()(get_neighbors)
    mcp.tool()(find_callers)
    mcp.tool()(outline)
    mcp.tool()(get_lineage)
    mcp.tool()(blast_radius)


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
