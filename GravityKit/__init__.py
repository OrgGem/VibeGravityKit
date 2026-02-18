"""
GravityKit — The AI-Native Software House in a Box.

Install: pip install gk
Usage:   gk init [ide]
"""

from pathlib import Path

def _read_version() -> str:
    version_file = Path(__file__).parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"

__version__ = _read_version()
__author__ = "GravityKit Team"
__description__ = "The AI-Native Software House in a Box"

__all__ = ["__version__", "__author__", "__description__"]
