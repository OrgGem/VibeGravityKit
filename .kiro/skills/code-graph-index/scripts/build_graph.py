#!/usr/bin/env python3
"""
build_graph.py — Build a structural code graph (nodes + edges) for a project.

Output: .code-graph-index/graph.json with shape:
    {
      "nodes":    [{id, kind, name, path, line, end_line?, signature?,
                    content_hash, byte_offset?, byte_length?}],
      "edges":    [{src, dst, kind}],            # kind ∈ contains|imports|calls|references
      "files":    {path: {mtime, language, hash}},
      "metadata": {generated_at, root, languages, counts, dirty_nodes?,
                   incremental_stats?}
    }

Stdlib only. Uses Python AST for high-fidelity Python parsing and regex for
JS/TS/Java/C#/Go (cheap heuristic — good enough for symbol+import edges).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Make Windows consoles tolerate emoji we print below.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_OUTPUT = ".code-graph-index/graph.json"

EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vue": "vue",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    ".code-graph-index", ".code-review-graph",
    "dist", "build", "__pycache__", ".idea", ".vscode",
    "target", "out",
}

JS_PATTERNS = [
    (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)"), "class"),
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("), "function"),
    (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\("), "function"),
    (re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "interface"),
    (re.compile(r"^\s*(?:export\s+)?type\s+(\w+)\s*="), "type"),
]
JS_IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+.+?\s+from\s+['\"]([^'\"]+)['\"]"),
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]"),
    re.compile(r"\brequire\(['\"]([^'\"]+)['\"]\)"),
]

JAVA_PATTERNS = [
    (re.compile(r"^\s*(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?class\s+(\w+)"), "class"),
    (re.compile(r"^\s*(?:public|private|protected)?\s*interface\s+(\w+)"), "interface"),
    (re.compile(r"^\s*(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\],\s]+?\s+(\w+)\s*\("), "method"),
]
JAVA_IMPORT = re.compile(r"^\s*import\s+([\w\.]+)\s*;")

CSHARP_PATTERNS = [
    (re.compile(r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?class\s+(\w+)"), "class"),
    (re.compile(r"^\s*(?:public|private|protected|internal)?\s*interface\s+(\w+)"), "interface"),
    (re.compile(r"^\s*(?:public|private|protected|internal)\s+[\w<>\[\],\s]+?\s+(\w+)\s*\("), "method"),
]
CSHARP_IMPORT = re.compile(r"^\s*using\s+([\w\.]+)\s*;")

GO_PATTERNS = [
    (re.compile(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\("), "function"),
    (re.compile(r"^type\s+(\w+)\s+struct"), "struct"),
    (re.compile(r"^type\s+(\w+)\s+interface"), "interface"),
]
GO_IMPORT = re.compile(r'^\s*"([^"]+)"')


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


class GraphBuilder:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self.files: dict[str, dict] = {}
        self._node_index: dict[str, int] = {}
        self._source_cache: dict[str, str] = {}  # rel_path -> source text

    def _node_id(self, path: str, name: str | None = None, line: int | None = None) -> str:
        if name is None:
            return path
        return f"{path}::{name}@{line or 0}"

    @staticmethod
    def _compute_content_hash(source_lines: list[str], line: int, end_line: int) -> str:
        """Compute SHA-256 hash of the actual source text between line and end_line."""
        source_slice = "\n".join(source_lines[line - 1:end_line])
        return _hash(source_slice)

    @staticmethod
    def _compute_byte_info(source: str, line: int, end_line: int) -> tuple[int, int]:
        """Compute byte_offset and byte_length for a node within its source file."""
        lines_with_ends = source.splitlines(keepends=True)
        byte_offset = sum(len(l.encode("utf-8")) for l in lines_with_ends[:line - 1])
        source_slice = "\n".join(source.splitlines()[line - 1:end_line])
        byte_length = len(source_slice.encode("utf-8"))
        return byte_offset, byte_length

    def _add_node(self, **kwargs) -> str:
        nid = kwargs["id"]
        if nid in self._node_index:
            return nid
        self._node_index[nid] = len(self.nodes)
        self.nodes.append(kwargs)
        return nid

    def _add_edge(self, src: str, dst: str, kind: str) -> None:
        self.edges.append({"src": src, "dst": dst, "kind": kind})

    # ---------- Python (AST) ----------

    def _parse_python(self, rel_path: str, source: str) -> None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        file_id = self._add_node(id=rel_path, kind="file", name=os.path.basename(rel_path),
                                 path=rel_path, line=1, language="python")

        # Imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add_edge(file_id, alias.name, "imports")
            elif isinstance(node, ast.ImportFrom) and node.module:
                self._add_edge(file_id, node.module, "imports")

        # Symbols + calls
        class Visitor(ast.NodeVisitor):
            def __init__(self, gb: "GraphBuilder", file_id: str, path: str, source: str):
                self.gb = gb
                self.file_id = file_id
                self.path = path
                self.source = source
                self.lines = source.splitlines()
                self.scope_stack: list[str] = []
                self.class_stack: list[str] = []  # track current class for self.x() calls

            def _enter(self, node, kind: str, name: str):
                line = getattr(node, "lineno", 0)
                end_line = getattr(node, "end_lineno", None) or line
                args = ""
                docstring = ""
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node) or ""
                if not docstring and line > 0 and end_line >= line:
                    docstring = "\n".join(self.lines[line-1:min(end_line, line+4)])

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = "(" + ", ".join(a.arg for a in node.args.args) + ")"
                signature = f"{kind} {name}{args}"
                node_id = self.gb._node_id(self.path, name, line)

                # Phase A: content_hash from actual source slice
                content_hash = GraphBuilder._compute_content_hash(self.lines, line, end_line)
                # Phase D: byte-level lineage
                byte_offset, byte_length = GraphBuilder._compute_byte_info(
                    self.source, line, end_line
                )

                self.gb._add_node(
                    id=node_id, kind=kind, name=name, path=self.path,
                    line=line, end_line=end_line, signature=signature,
                    docstring=docstring, content_hash=content_hash,
                    byte_offset=byte_offset, byte_length=byte_length,
                )
                parent = self.scope_stack[-1] if self.scope_stack else self.file_id
                self.gb._add_edge(parent, node_id, "contains")
                self.scope_stack.append(node_id)

            def _exit(self):
                self.scope_stack.pop()

            def visit_ClassDef(self, node):
                self._enter(node, "class", node.name)
                self.class_stack.append(node.name)
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        self.gb._add_edge(self.scope_stack[-1], base.id, "references")
                self.generic_visit(node)
                self.class_stack.pop()
                self._exit()

            def visit_FunctionDef(self, node):
                self._enter(node, "function", node.name)
                self.generic_visit(node)
                self._exit()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node):
                if not self.scope_stack:
                    self.generic_visit(node)
                    return
                caller_id = self.scope_stack[-1]
                target = None
                if isinstance(node.func, ast.Name):
                    target = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    # Track self.method() → resolve to ClassName.method within class
                    if (isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "self"
                            and self.class_stack):
                        # Find the method node_id in the current class
                        class_name = self.class_stack[-1]
                        # Search for method in existing nodes
                        for n in self.gb.nodes:
                            if (n.get("name") == attr_name
                                    and n.get("path") == self.path
                                    and n.get("kind") == "function"):
                                nid = n["id"]
                                # Only link if it belongs to same class
                                if f"::{attr_name}@" in nid:
                                    self.gb._add_edge(caller_id, nid, "calls")
                                    break
                        else:
                            # Method not parsed yet — add unresolved edge
                            self.gb._add_edge(caller_id, attr_name, "calls")
                    else:
                        target = attr_name
                if target:
                    self.gb._add_edge(caller_id, target, "calls")
                self.generic_visit(node)

        Visitor(self, file_id, rel_path, source).visit(tree)

    # ---------- Regex-based languages ----------

    def _parse_regex(self, rel_path: str, source: str, lang: str) -> None:
        file_id = self._add_node(id=rel_path, kind="file", name=os.path.basename(rel_path),
                                 path=rel_path, line=1, language=lang)

        if lang in {"javascript", "typescript", "vue"}:
            patterns = JS_PATTERNS
            import_patterns = JS_IMPORT_PATTERNS
        elif lang == "java":
            patterns = JAVA_PATTERNS
            import_patterns = [JAVA_IMPORT]
        elif lang == "csharp":
            patterns = CSHARP_PATTERNS
            import_patterns = [CSHARP_IMPORT]
        elif lang == "go":
            patterns = GO_PATTERNS
            import_patterns = [GO_IMPORT]
        else:
            return

        lines = source.splitlines()
        # Collect symbol start lines first, then compute end_line
        symbol_starts: list[tuple[int, str, str, str]] = []  # (line_num, kind, name, sig)

        for line_num, line in enumerate(lines, 1):
            for pat in import_patterns:
                m = pat.search(line)
                if m:
                    self._add_edge(file_id, m.group(1), "imports")

            for pat, kind in patterns:
                m = pat.search(line)
                if m:
                    symbol_starts.append((line_num, kind, m.group(1), line.strip()))

        # Compute end_line: each symbol ends just before the next symbol or at EOF
        total_lines = len(lines)
        for i, (line_num, kind, name, sig) in enumerate(symbol_starts):
            if i + 1 < len(symbol_starts):
                end_line = symbol_starts[i + 1][0] - 1
            else:
                end_line = total_lines
            
            docstring = "\n".join(lines[line_num-1:min(end_line, line_num+4)])

            # Phase A: content_hash from actual source slice
            content_hash = self._compute_content_hash(lines, line_num, end_line)
            # Phase D: byte-level lineage
            byte_offset, byte_length = self._compute_byte_info(source, line_num, end_line)

            node_id = self._node_id(rel_path, name, line_num)
            self._add_node(
                id=node_id, kind=kind, name=name,
                path=rel_path, line=line_num, end_line=end_line,
                signature=sig, docstring=docstring,
                content_hash=content_hash,
                byte_offset=byte_offset, byte_length=byte_length,
            )
            self._add_edge(file_id, node_id, "contains")

    # ---------- Driver ----------

    def parse_file(self, path: Path) -> None:
        rel = path.relative_to(self.root).as_posix()
        ext = path.suffix.lower()
        lang = EXTENSIONS.get(ext)
        if not lang:
            return

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return

        file_hash = _hash(source)
        self.files[rel] = {
            "mtime": path.stat().st_mtime,
            "language": lang,
            "hash": file_hash,
        }
        self._source_cache[rel] = source

        if lang == "python":
            self._parse_python(rel, source)
        else:
            self._parse_regex(rel, source, lang)

    def build(self) -> dict:
        for root_dir, dirs, filenames in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fn in filenames:
                self.parse_file(Path(root_dir) / fn)

        languages = sorted({f["language"] for f in self.files.values()})
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "files": self.files,
            "metadata": {
                "generated_at": time.time(),
                "root": str(self.root),
                "languages": languages,
                "counts": {
                    "files": len(self.files),
                    "nodes": len(self.nodes),
                    "edges": len(self.edges),
                },
            },
        }


def incremental_update(existing: dict, root: Path) -> dict:
    """Re-parse only files whose mtime changed; diff nodes by content_hash.

    Returns the updated graph with a ``dirty_nodes`` list in metadata that
    downstream consumers (e.g. build_faiss_index) can use to selectively
    re-embed only the nodes whose source actually changed.
    """
    old_nodes_by_id: dict[str, dict] = {n["id"]: n for n in existing.get("nodes", [])}

    builder = GraphBuilder(root)
    builder.nodes = list(existing.get("nodes", []))
    builder.edges = list(existing.get("edges", []))
    builder.files = dict(existing.get("files", {}))
    builder._node_index = {n["id"]: i for i, n in enumerate(builder.nodes)}

    dirty_nodes: list[str] = []
    stats = {"files_changed": 0, "nodes_kept": 0, "nodes_updated": 0,
             "nodes_added": 0, "nodes_deleted": 0}

    seen: set[str] = set()
    for root_dir, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in filenames:
            path = Path(root_dir) / fn
            if path.suffix.lower() not in EXTENSIONS:
                continue
            rel = path.relative_to(root).as_posix()
            seen.add(rel)
            mtime = path.stat().st_mtime
            prev = builder.files.get(rel)
            if prev and abs(prev["mtime"] - mtime) < 1e-6:
                continue

            stats["files_changed"] += 1

            # Snapshot old nodes for this file (keyed by id)
            old_file_nodes = {n["id"]: n for n in builder.nodes if n.get("path") == rel}

            # Drop existing nodes/edges for this file then re-parse.
            builder.nodes = [n for n in builder.nodes if n.get("path") != rel]
            builder.edges = [e for e in builder.edges
                             if not (e["src"] == rel or e["src"].startswith(f"{rel}::"))]
            builder._node_index = {n["id"]: i for i, n in enumerate(builder.nodes)}
            builder.parse_file(path)

            # Diff: compare new nodes vs old nodes by content_hash
            new_file_nodes = {n["id"]: n for n in builder.nodes if n.get("path") == rel}
            for nid, new_node in new_file_nodes.items():
                if new_node.get("kind") == "file":
                    continue
                old_node = old_file_nodes.get(nid)
                if old_node is None:
                    # Brand new node
                    dirty_nodes.append(nid)
                    stats["nodes_added"] += 1
                elif old_node.get("content_hash") != new_node.get("content_hash"):
                    # Content actually changed
                    dirty_nodes.append(nid)
                    stats["nodes_updated"] += 1
                else:
                    # Same content_hash — node is unchanged
                    stats["nodes_kept"] += 1

            # Detect deleted nodes (were in old, not in new)
            for nid in old_file_nodes:
                if nid not in new_file_nodes and old_file_nodes[nid].get("kind") != "file":
                    dirty_nodes.append(nid)  # mark for FAISS removal
                    stats["nodes_deleted"] += 1

    # Drop deleted files
    deleted = set(builder.files) - seen
    for rel in deleted:
        # Mark all nodes from deleted files as dirty
        for n in builder.nodes:
            if n.get("path") == rel and n.get("kind") != "file":
                dirty_nodes.append(n["id"])
                stats["nodes_deleted"] += 1
        builder.files.pop(rel, None)
        builder.nodes = [n for n in builder.nodes if n.get("path") != rel]
        builder.edges = [e for e in builder.edges
                         if not (e["src"] == rel or e["src"].startswith(f"{rel}::"))]

    languages = sorted({f["language"] for f in builder.files.values()}) if builder.files else []
    return {
        "nodes": builder.nodes,
        "edges": builder.edges,
        "files": builder.files,
        "metadata": {
            "generated_at": time.time(),
            "root": str(root.resolve()),
            "languages": languages,
            "counts": {
                "files": len(builder.files),
                "nodes": len(builder.nodes),
                "edges": len(builder.edges),
            },
            "dirty_nodes": dirty_nodes,
            "incremental_stats": stats,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build code structural graph (JSON)")
    parser.add_argument("--path", default=".", help="Project root")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output graph JSON path")
    parser.add_argument("--incremental", action="store_true",
                        help="Only re-parse changed files (requires existing graph.json)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = (root / output).resolve()

    if args.incremental and output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        graph = incremental_update(existing, root)
        stats = graph["metadata"].get("incremental_stats", {})
        dirty = graph["metadata"].get("dirty_nodes", [])
        print(f"Incremental: {stats.get('files_changed', 0)} file(s) changed, "
              f"{stats.get('nodes_kept', 0)} kept, "
              f"{stats.get('nodes_updated', 0)} updated, "
              f"{stats.get('nodes_added', 0)} added, "
              f"{stats.get('nodes_deleted', 0)} deleted, "
              f"{len(dirty)} dirty node(s)")
    else:
        graph = GraphBuilder(root).build()

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = graph["metadata"]["counts"]
    print(f"Graph built: files={counts['files']}, nodes={counts['nodes']}, "
          f"edges={counts['edges']} -> {output}")


if __name__ == "__main__":
    main()
