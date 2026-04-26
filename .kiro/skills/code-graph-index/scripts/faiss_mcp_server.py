#!/usr/bin/env python3
"""
faiss_mcp_server.py — MCP server exposing semantic chunk search.

Tools:
    search_code_chunks(query, top_k=8)  → list of {path, start_line, end_line, preview, score}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import faiss
except ImportError:
    faiss = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None  # type: ignore[assignment]

mcp = FastMCP("faiss-code-index") if FastMCP is not None else None
_INDEX = None
_METADATA: dict | None = None
_DIM: int = 384
_SERVER_INDEX_DIR = ".code-graph-index/faiss-index"
_EMBEDDER = None


def _get_embedder():
    """Get the shared embedder, matching the strategy used during build."""
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER

    import sys
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from embedder import get_embedder, HashEmbedder, OnnxEmbedder

    # Check what strategy was used during build
    strategy = (_METADATA or {}).get("strategy", "HashEmbedder")

    if strategy == "OnnxEmbedder":
        # Try to use ONNX, fall back to hash if not available
        model_dir = Path(_SERVER_INDEX_DIR).resolve().parent / "model"
        _EMBEDDER = get_embedder(model_dir=model_dir, auto_download=False)
        if isinstance(_EMBEDDER, HashEmbedder) and strategy == "OnnxEmbedder":
            import logging
            logging.getLogger(__name__).warning(
                "Index was built with OnnxEmbedder but onnxruntime not available. "
                "Search quality may be degraded. Install: pip install onnxruntime"
            )
    else:
        _EMBEDDER = get_embedder(auto_download=False)

    return _EMBEDDER


def _ensure_loaded(index_dir: Path) -> None:
    global _INDEX, _METADATA, _DIM
    if _INDEX is not None and _METADATA is not None:
        return

    index_path = index_dir / "code.index"
    metadata_path = index_dir / "metadata.json"
    if not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing index files in {index_dir}. Run build_faiss_index.py first."
        )

    if faiss is None:
        raise RuntimeError("faiss-cpu is required. Install with: pip install faiss-cpu")

    _INDEX = faiss.read_index(str(index_path))
    _METADATA = json.loads(metadata_path.read_text(encoding="utf-8"))
    _DIM = int(_METADATA.get("dimension", 384))


def search_code_chunks(query: str, top_k: int = 8) -> dict:
    """Semantic-like code chunk search using a local FAISS index."""
    index_dir_env = Path(_SERVER_INDEX_DIR)
    _ensure_loaded(index_dir_env)

    assert _INDEX is not None
    assert _METADATA is not None

    embedder = _get_embedder()
    q = embedder.embed(query).reshape(1, -1)
    scores, ids = _INDEX.search(q, top_k)

    chunks = _METADATA.get("chunks", [])
    hits = []
    for rank, (score, idx) in enumerate(zip(scores[0], ids[0]), start=1):
        if idx < 0 or idx >= len(chunks):
            continue
        chunk = chunks[idx]
        hits.append(
            {
                "rank": rank,
                "score": float(score),
                "path": chunk.get("path"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "preview": chunk.get("preview"),
            }
        )

    return {
        "query": query,
        "top_k": top_k,
        "total_chunks": len(chunks),
        "strategy": _METADATA.get("strategy", "HashEmbedder"),
        "results": hits,
    }


if mcp is not None:
    mcp.tool()(search_code_chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP server for FAISS code index")
    parser.add_argument(
        "--index-dir",
        default=".code-graph-index/faiss-index",
        help="Directory containing code.index and metadata.json",
    )
    args = parser.parse_args()

    global _SERVER_INDEX_DIR
    _SERVER_INDEX_DIR = str(Path(args.index_dir).resolve())

    if mcp is None:
        raise RuntimeError("mcp package is required. Install with: pip install mcp")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
