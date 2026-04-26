---
name: document-reader
description: Provides an MCP server that reads PDF, DOCX, and XLSX files, converting them to Markdown text so AI agents can natively read them.
risk: safe
source: VibeGravityKit
---

# Document Reader

Exposes the `read_document` MCP tool to allow AI agents to natively read `.pdf`, `.docx`, and `.xlsx` files without requiring the user to copy-paste contents.

## Setup & Dependencies

```bash
python -m pip install mcp pypdf python-docx openpyxl
```

## How to enable it

You can manually add this server to your `.mcp.json` (for Antigravity/Claude Code) or `.kiro/settings/mcp.json`:

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

Once registered, whenever the user asks you to "summarize this PDF" or "read data from the Excel file", you will autonomously see the `read_document` tool in your toolbox, pass the file path to it, and get the text back to process!
