#!/usr/bin/env python3
"""
watcher.py — Live filesystem watcher for code-graph-index (Phase B).

Monitors the project directory for code file changes and automatically triggers
incremental graph + FAISS rebuilds with debouncing.

Usage:
    python watcher.py --project-root . --debounce 2000 --verbose

Requires: watchdog>=3.0 (pip install watchdog)
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

# Make Windows consoles tolerate emoji we print below.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None  # type: ignore[assignment]
    FileSystemEventHandler = object  # type: ignore[assignment,misc]

SCRIPT_DIR = Path(__file__).resolve().parent

EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".vue",
    ".java", ".cs", ".go",
    ".xml", ".xaml", ".json", ".txt",
}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    ".code-graph-index", ".code-review-graph",
    "dist", "build", "__pycache__", ".idea", ".vscode",
    "target", "out",
}


class CodeChangeHandler(FileSystemEventHandler):
    """Debounced file change handler that triggers incremental graph/FAISS updates."""

    def __init__(self, project_root: Path, debounce_ms: int = 2000,
                 verbose: bool = False):
        super().__init__()
        self.project_root = project_root
        self.debounce_ms = debounce_ms
        self.verbose = verbose
        self._dirty_files: set[str] = set()
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._update_count = 0

    def _should_watch(self, path: str) -> bool:
        """Check if a file path is a relevant code file."""
        p = Path(path)

        # Skip files inside ignored directories
        parts = p.parts
        for part in parts:
            if part in IGNORE_DIRS:
                return False

        return p.suffix.lower() in EXTENSIONS

    def on_modified(self, event):
        if event.is_directory:
            return
        if not self._should_watch(event.src_path):
            return
        with self._lock:
            self._dirty_files.add(event.src_path)
            if self.verbose:
                rel = os.path.relpath(event.src_path, self.project_root)
                print(f"   📝 Changed: {rel}")
            self._reset_timer()

    def on_created(self, event):
        if event.is_directory:
            return
        if not self._should_watch(event.src_path):
            return
        with self._lock:
            self._dirty_files.add(event.src_path)
            if self.verbose:
                rel = os.path.relpath(event.src_path, self.project_root)
                print(f"   ➕ Created: {rel}")
            self._reset_timer()

    def on_deleted(self, event):
        if event.is_directory:
            return
        if not self._should_watch(event.src_path):
            return
        with self._lock:
            self._dirty_files.add(event.src_path)
            if self.verbose:
                rel = os.path.relpath(event.src_path, self.project_root)
                print(f"   ❌ Deleted: {rel}")
            self._reset_timer()

    def _reset_timer(self):
        """Reset the debounce timer."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(
            self.debounce_ms / 1000.0,
            self._flush,
        )
        self._timer.daemon = True
        self._timer.start()

    def _flush(self):
        """Run incremental update for accumulated dirty files."""
        with self._lock:
            files = self._dirty_files.copy()
            self._dirty_files.clear()

        if not files:
            return

        self._update_count += 1
        n = len(files)
        print(f"\n🔄 [{self._update_count}] Auto-syncing {n} changed file(s)...")

        t0 = time.monotonic()
        success = self._run_incremental()
        elapsed = time.monotonic() - t0

        if success:
            print(f"✅ Synced in {elapsed:.1f}s — MCP servers will auto-reload")
        else:
            print(f"⚠️  Sync failed after {elapsed:.1f}s — see errors above")

    def _run_incremental(self) -> bool:
        """Run incremental graph build + FAISS re-index."""
        py = sys.executable or "python"
        root = str(self.project_root)

        # Step 1: Incremental graph build
        graph_cmd = [
            py, str(SCRIPT_DIR / "build_graph.py"),
            "--path", root,
            "--incremental",
        ]
        try:
            result = subprocess.run(
                graph_cmd, check=True, cwd=root,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"   {line}")
        except subprocess.CalledProcessError as exc:
            print(f"   ❌ Graph build failed (exit {exc.returncode})")
            if exc.stderr:
                print(f"   {exc.stderr.strip()}")
            return False

        # Step 2: FAISS index rebuild (will auto-detect dirty nodes)
        faiss_cmd = [
            py, str(SCRIPT_DIR / "build_faiss_index.py"),
            "--project-root", root,
        ]
        try:
            result = subprocess.run(
                faiss_cmd, check=True, cwd=root,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"   {line}")
        except subprocess.CalledProcessError as exc:
            print(f"   ⚠️  FAISS build failed (exit {exc.returncode})")
            if exc.stderr:
                print(f"   {exc.stderr.strip()}")
            # Graph was updated successfully, FAISS failure is non-fatal
            return True

        return True


def start_watcher(project_root: Path, debounce_ms: int = 2000,
                  verbose: bool = False) -> None:
    """Start the filesystem watcher (blocking)."""
    if Observer is None:
        print("❌ watchdog is required. Install with: pip install watchdog>=3.0")
        sys.exit(1)

    handler = CodeChangeHandler(
        project_root=project_root,
        debounce_ms=debounce_ms,
        verbose=verbose,
    )
    observer = Observer()
    observer.schedule(handler, str(project_root), recursive=True)
    observer.start()

    print(f"👁️  Watching for code changes in: {project_root}")
    print(f"   Debounce: {debounce_ms}ms")
    print(f"   Extensions: {', '.join(sorted(EXTENSIONS))}")
    print(f"   Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Watcher stopped.")
        observer.stop()
    observer.join()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Live filesystem watcher for code-graph-index"
    )
    parser.add_argument("--project-root", default=".", help="Project root (default: cwd)")
    parser.add_argument("--debounce", type=int, default=2000,
                        help="Debounce interval in ms (default: 2000)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show individual file change events")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    start_watcher(project_root, debounce_ms=args.debounce, verbose=args.verbose)


if __name__ == "__main__":
    main()
