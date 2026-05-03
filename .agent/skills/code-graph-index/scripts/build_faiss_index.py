#!/usr/bin/env python3
"""
build_faiss_index.py — Build a FAISS semantic index over project source code.

Output:
    <output-dir>/code.index      FAISS IndexFlatIP
    <output-dir>/metadata.json   Chunk metadata + dimension + counts

Default output: .code-graph-index/faiss-index/

Embedding strategy (auto-selected):
    1. ONNX: all-MiniLM-L6-v2 quantized via shared embedder.py (requires onnxruntime)
    2. Hash: deterministic token-hashing — zero deps, zero network.
    Override: set GKT_MODEL_CDN to control ONNX model CDN source.

Incremental mode:
    When the graph contains a `dirty_nodes` list in metadata, only those nodes
    are re-embedded. Existing vectors for unchanged nodes are preserved.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import faiss
except ImportError:
    faiss = None

try:
    import numpy as np
except ImportError:
    np = None

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
    ".go", ".rs", ".java", ".kt", ".swift",
    ".c", ".cc", ".cpp", ".h", ".hpp",
    ".cs", ".rb", ".php", ".scala", ".sql",
    ".md", ".json", ".yaml", ".yml",
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    ".code-graph-index", ".code-review-graph",
    "dist", "build", "__pycache__", ".idea", ".vscode",
}

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    node_id: str
    path: str
    start_line: int
    end_line: int
    text: str
    kind: str

def _get_embedder(project_root: Path, auto_download: bool = True):
    """Get the shared embedder — ONNX if available, else hash."""
    # Import from sibling module
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from embedder import get_embedder
    model_dir = project_root / ".code-graph-index" / "model"
    return get_embedder(model_dir=model_dir, auto_download=auto_download)


def _chunks_from_graph(graph_data: dict) -> list[Chunk]:
    """Extract embeddable chunks from graph nodes."""
    all_chunks: list[Chunk] = []
    for node in graph_data.get("nodes", []):
        if node.get("kind") == "file":
            continue
        node_id = node.get("id", "")
        path = node.get("path", "")
        line = node.get("line", 0)
        end_line = node.get("end_line", line)
        kind = node.get("kind", "")
        name = node.get("name", "")
        signature = node.get("signature", name)
        docstring = node.get("docstring", "")

        text = f"{kind} {signature}\n{docstring}".strip()
        if not text:
            continue

        all_chunks.append(Chunk(
            node_id=node_id,
            path=path,
            start_line=line,
            end_line=end_line,
            text=text,
            kind=kind,
        ))
    return all_chunks


def _embed_chunks(all_chunks: list[Chunk], embedder) -> "numpy.ndarray":
    """Embed a list of chunks using multi-threaded batching. Returns (N, dim) array."""
    import concurrent.futures

    batch_size = 256
    max_workers = max(1, (os.cpu_count() or 2) // 2)
    print(f"   Using {max_workers} threads for embedding (limit 50% CPU)")

    def process_batch(start_idx):
        batch = all_chunks[start_idx:start_idx + batch_size]
        texts = [chunk.text for chunk in batch]
        return start_idx, embedder.embed_batch(texts)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_batch, start): start
            for start in range(0, len(all_chunks), batch_size)
        }
        total_batches = len(futures)
        completed = 0

        print("   [", end="", flush=True)
        for future in concurrent.futures.as_completed(futures):
            start_idx = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                logger.error("Batch starting at %d failed: %s", start_idx, e)

            completed += 1
            if completed % max(1, total_batches // 20) == 0:
                print("█", end="", flush=True)
            elif completed == total_batches:
                print("█", end="", flush=True)
        print(f"] 100% ({total_batches} batches)\n", flush=True)

    results.sort(key=lambda x: x[0])
    return np.vstack([vecs for _, vecs in results])


def _write_index(output_dir: Path, all_chunks: list[Chunk], vectors, dim: int,
                 strategy: str, node_count: int) -> None:
    """Write FAISS index + metadata to disk."""
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    output_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_dir / "code.index"))

    metadata = [
        {
            "id": i,
            "node_id": chunk.node_id,
            "kind": chunk.kind,
            "path": chunk.path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "preview": chunk.text[:300],
        }
        for i, chunk in enumerate(all_chunks)
    ]
    (output_dir / "metadata.json").write_text(
        json.dumps(
            {
                "dimension": dim,
                "strategy": strategy,
                "node_count": node_count,
                "chunk_count": len(all_chunks),
                "chunks": metadata,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def build_index(project_root: Path, output_dir: Path, dim: int = 384) -> tuple[int, int]:
    """Full build: embed all graph nodes from scratch."""
    if faiss is None or np is None:
        raise RuntimeError("Missing deps. Install with: pip install faiss-cpu numpy")

    graph_path = output_dir.parent / "graph.json"
    if not graph_path.exists():
        raise RuntimeError(f"Missing graph.json at {graph_path}. Run build_graph.py first.")

    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph_data.get("nodes", [])

    # Check if incremental is possible
    dirty_ids = set(graph_data.get("metadata", {}).get("dirty_nodes", []))
    existing_meta_path = output_dir / "metadata.json"
    existing_index_path = output_dir / "code.index"

    if (dirty_ids is not None
            and len(dirty_ids) >= 0
            and existing_meta_path.exists()
            and existing_index_path.exists()):
        try:
            result = _incremental_build(project_root, output_dir, graph_data, dirty_ids)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning("Incremental FAISS build failed, falling back to full: %s", exc)
            print(f"   ⚠️  Incremental failed ({exc}), doing full rebuild")

    # Full rebuild
    embedder = _get_embedder(project_root)
    dim = embedder.dim
    strategy = type(embedder).__name__
    print(f"   Embedding strategy: {strategy} (dim={dim})")

    all_chunks = _chunks_from_graph(graph_data)
    if not all_chunks:
        raise RuntimeError("No chunks found from structural graph.")

    vectors = _embed_chunks(all_chunks, embedder)
    _write_index(output_dir, all_chunks, vectors, dim, strategy, len(nodes))

    return len(nodes), len(all_chunks)


def _incremental_build(
    project_root: Path,
    output_dir: Path,
    graph_data: dict,
    dirty_ids: set[str],
) -> tuple[int, int] | None:
    """Selectively re-embed only dirty nodes, keeping existing vectors for the rest.

    Returns (node_count, chunk_count) on success, or None to signal fallback.
    """
    if not dirty_ids:
        print("   ✅ No dirty nodes — FAISS index is up to date.")
        nodes = graph_data.get("nodes", [])
        existing_meta = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
        return len(nodes), existing_meta.get("chunk_count", 0)

    # Load existing FAISS index + metadata
    existing_index = faiss.read_index(str(output_dir / "code.index"))
    existing_meta = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
    existing_chunks_meta = existing_meta.get("chunks", [])
    old_dim = int(existing_meta.get("dimension", 384))

    # Map old chunk positions by node_id
    old_chunk_positions: dict[str, int] = {}
    for chunk_meta in existing_chunks_meta:
        old_chunk_positions[chunk_meta["node_id"]] = chunk_meta["id"]

    # Extract all current chunks from the updated graph
    all_chunks = _chunks_from_graph(graph_data)
    if not all_chunks:
        return None  # fall back to full build

    # Get embedder
    embedder = _get_embedder(project_root)
    dim = embedder.dim
    strategy = type(embedder).__name__

    if dim != old_dim:
        print(f"   ⚠️  Dimension mismatch (old={old_dim}, new={dim}), full rebuild needed")
        return None

    # Split chunks into clean (reuse old vector) vs dirty (need re-embed)
    clean_chunks: list[tuple[Chunk, int]] = []  # (chunk, old_faiss_position)
    dirty_chunks: list[Chunk] = []

    for chunk in all_chunks:
        if chunk.node_id in dirty_ids:
            dirty_chunks.append(chunk)
        elif chunk.node_id in old_chunk_positions:
            clean_chunks.append((chunk, old_chunk_positions[chunk.node_id]))
        else:
            # New node not in dirty list (shouldn't happen, but be safe)
            dirty_chunks.append(chunk)

    n_total = len(all_chunks)
    n_dirty = len(dirty_chunks)
    n_clean = len(clean_chunks)
    print(f"   Incremental FAISS: {n_dirty} dirty, {n_clean} cached, {n_total} total")
    print(f"   Embedding strategy: {strategy} (dim={dim})")

    # Reconstruct clean vectors from old index, embed only dirty ones
    vectors = np.empty((n_total, dim), dtype=np.float32)
    dirty_indices: list[int] = []
    for i, chunk in enumerate(all_chunks):
        if chunk.node_id in dirty_ids or chunk.node_id not in old_chunk_positions:
            dirty_indices.append(i)
        else:
            old_pos = old_chunk_positions[chunk.node_id]
            if old_pos < existing_index.ntotal:
                try:
                    vec = np.zeros(dim, dtype=np.float32)
                    existing_index.reconstruct(int(old_pos), vec)
                    vectors[i] = vec
                except Exception:
                    dirty_indices.append(i)
            else:
                dirty_indices.append(i)

    # Embed only dirty chunks
    if dirty_indices:
        dirty_texts = [all_chunks[i].text for i in dirty_indices]
        dirty_vecs = embedder.embed_batch(dirty_texts)
        for j, idx in enumerate(dirty_indices):
            vectors[idx] = dirty_vecs[j]
        print(f"   ✅ Re-embedded {len(dirty_indices)} chunk(s)")

    nodes = graph_data.get("nodes", [])
    _write_index(output_dir, all_chunks, vectors, dim, strategy, len(nodes))

    return len(nodes), len(all_chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS code index")
    parser.add_argument("--project-root", default=".", help="Path to project root")
    parser.add_argument(
        "--output-dir",
        default=".code-graph-index/faiss-index",
        help="Output directory for FAISS index and metadata",
    )
    parser.add_argument("--dim", type=int, default=384, help="Embedding dimension")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (project_root / output_dir).resolve()

    try:
        file_count, chunk_count = build_index(project_root, output_dir, args.dim)
    except RuntimeError as exc:
        print(f"FAISS index not built: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"FAISS index built: files={file_count}, chunks={chunk_count}, output={output_dir}")


if __name__ == "__main__":
    main()
