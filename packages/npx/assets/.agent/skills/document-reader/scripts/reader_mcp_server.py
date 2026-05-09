#!/usr/bin/env python3
"""
reader_mcp_server.py — MCP server exposing document reading capabilities
powered by Microsoft's MarkItDown library.

Supported formats: PDF, DOCX, XLSX, PPTX, HTML, CSV, JSON, XML, ZIP,
images (with optional LLM), audio (with optional LLM), and more.

Tools:
    read_document(filepath: str) -> str
"""
import sys
import warnings
from pathlib import Path

# Suppress pydub ffmpeg warning noise (only affects audio features)
warnings.filterwarnings("ignore", message=".*ffmpeg.*", category=RuntimeWarning)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

# Lazy-loaded MarkItDown instance
_MD_INSTANCE = None


def _get_md():
    """Lazy-init MarkItDown to avoid import cost at module load."""
    global _MD_INSTANCE
    if _MD_INSTANCE is None:
        try:
            from markitdown import MarkItDown
        except ImportError:
            raise RuntimeError(
                'markitdown is not installed. Run: pip install "markitdown[all]"'
            )
        _MD_INSTANCE = MarkItDown()
    return _MD_INSTANCE


def read_document(filepath: str) -> str:
    """Reads the text content of a document file and returns it as Markdown format.

    Supports PDF, DOCX, XLSX, PPTX, HTML, CSV, JSON, XML, images, audio,
    and many more formats via Microsoft MarkItDown.

    Use this whenever the user asks to process or read a document.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        return f"Error: File not found at {filepath}"

    try:
        from markitdown import UnsupportedFormatException
    except ImportError:
        UnsupportedFormatException = None

    try:
        md = _get_md()
        result = md.convert(path)
        text = result.text_content
        if not text or not text.strip():
            return f"Warning: No text content could be extracted from {path.name}"
        return text
    except RuntimeError as e:
        return str(e)
    except Exception as e:
        if UnsupportedFormatException and isinstance(e, UnsupportedFormatException):
            return (
                f"Error: Unsupported file format '{path.suffix}'. "
                f"See https://github.com/microsoft/markitdown for supported formats."
            )
        return f"Error reading document: {type(e).__name__}: {e}"


def main():
    if FastMCP is None:
        print("Missing mcp package. pip install mcp", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("document-reader")
    mcp.tool()(read_document)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
