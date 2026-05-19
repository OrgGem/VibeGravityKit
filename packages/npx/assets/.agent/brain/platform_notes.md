# Cross-Platform Compatibility Notes

> Related default skills: `powershell-windows`, `bash-linux`
> Always check platform before running shell commands.

## Platform Detection
- Check `sys.platform` (Python) or `$env:OS` (PowerShell) or `uname` (Bash)
- Windows: `win32` | Linux: `linux` | macOS: `darwin`
- Use `powershell-windows` skill on Windows, `bash-linux` on Linux/macOS

## Path Separators
- Windows: backslash (\\), PowerShell also supports forward slash
- Linux/macOS: forward slash (/)
- Best practice: Use forward slash in code, let runtime handle conversion

## Shell Commands
- Windows: Use `powershell-windows` skill for PS patterns and pitfalls  
- Linux/macOS: Use `bash-linux` skill for Bash patterns and piping
- Avoid: `rm -rf` on Windows (use `Remove-Item -Recurse -Force`)
- Avoid: PowerShell-specific operators on Linux (use POSIX-compliant alternatives)

## Line Endings
- Windows: CRLF (\\r\\n)
- Linux/macOS: LF (\\n)
- Always: Configure `.gitattributes` with `* text=auto`

## Environment Variables
- Windows: `$env:VAR_NAME` (PowerShell), `%VAR_NAME%` (CMD)
- Linux/macOS: `$VAR_NAME` or `${VAR_NAME}`
- Best practice: Use dotenv files for consistency across platforms

## Encoding
- Windows: Default console is cp1252, may fail on emoji/Unicode
- Fix: Set `PYTHONIOENCODING=utf-8` or use `sys.stdout.reconfigure(encoding='utf-8')`
- Git: Ensure `core.quotepath=false` for UTF-8 filenames

## File Permissions
- Windows: ACL-based, no chmod equivalent needed for most cases
- Linux/macOS: chmod required for scripts (`chmod +x script.sh`)
- Best practice: Set executable bit in git with `git update-index --chmod=+x`

## File Reading Tool Selection

**RULE: Always use `view_file` for text-based formats. Never use `mcp_document-reader` for plain text.**

| Format | Correct tool | Reason |
|--------|-------------|--------|
| `.md`, `.txt`, `.csv`, `.json`, `.yaml`, `.yml` | `view_file` | Native, fast, no subprocess overhead |
| `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.cs` | `view_file` | Code files are plain text |
| `.html`, `.xml`, `.sql`, `.sh`, `.ps1` | `view_file` | Plain text formats |
| `.env`, `.gitignore`, `.toml`, `.ini`, `.cfg` | `view_file` | Config files are plain text |
| `.pdf`, `.docx`, `.xlsx`, `.pptx` | `mcp_document-reader` | Binary formats that need MarkItDown conversion |
| `.png`, `.jpg`, `.mp3`, `.mp4` | `mcp_document-reader` | Media files needing extraction |

**Why this matters on Windows:**
- `mcp_document-reader` spawns a subprocess (MarkItDown). If the file path exceeds 260 chars or contains unusual encoding, the subprocess can **hang indefinitely** with no error.
- `view_file` reads files natively — no subprocess, no timeout risk.
- Long paths like `C:\Users\...\Downloads\very-long-folder-name\...` are common on Windows and trigger this risk.

## Common Pitfalls
- Windows paths with spaces: Always quote paths
- Case sensitivity: Windows is case-insensitive, Linux is case-sensitive
- Max path length: Windows has 260 char limit (enable long paths via registry)
- Script shebang: `#!/usr/bin/env bash` not applicable on Windows
- npm/pip paths: Windows may need `--user` flag or admin privileges
