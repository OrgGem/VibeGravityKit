---
name: document-reader
description: MCP server that reads documents (PDF, DOCX, XLSX, PPTX, HTML, images, audio, and more) and converts them to Markdown using Microsoft MarkItDown.
risk: safe
source: VibeGravityKit
---

# Document Reader

Exposes the `read_document` MCP tool to allow AI agents to natively read documents and convert them to structured Markdown.

Powered by [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — a single library that replaces multiple format-specific parsers.

## Supported Formats

| Category | Extensions |
|---|---|
| **Documents** | `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.rtf` |
| **Web/Data** | `.html`, `.htm`, `.csv`, `.json`, `.xml` |
| **Text** | `.md`, `.txt`, `.rst`, `.ipynb` |
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp` |
| **Audio** | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac` |
| **Archives** | `.zip` |

> MarkItDown may support additional formats not listed here. Files are auto-detected — unlisted formats will be attempted and return a clear error if unsupported.

## Setup & Dependencies

```bash
# Install with all format support (recommended)
pip install "markitdown[all]" mcp

# Or minimal install (PDF + Office only)
pip install markitdown mcp
```

## How to enable it

Add this server to your `.mcp.json` (for Antigravity/Claude Code) or `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "document-reader": {
      "command": "python",
      "args": [
        ".agent/skills/document-reader/scripts/reader_mcp_server.py"
      ]
    }
  }
}
```

Once registered, whenever the user asks you to "summarize this PDF", "read data from the Excel file", or "extract text from this PowerPoint", you will autonomously see the `read_document` tool in your toolbox, pass the file path to it, and get structured Markdown back to process!

## Notes

- **Image/Audio AI**: For AI-powered image descriptions or audio transcription, initialize MarkItDown with an LLM client (see markitdown docs). The default setup extracts metadata only.
- **Large files**: MarkItDown processes files in-memory. Very large files (>100MB) may require significant RAM.
- **ZIP archives**: MarkItDown will extract and convert supported files within ZIP archives.
