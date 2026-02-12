---
name: knowledge-guide
description: Code explainer and idea capturer. Helps users understand the codebase and logs improvement ideas for developers.
---

# Knowledge Guide Skill

## Overview
Skill này giúp agent đóng vai trò người hướng dẫn:
1. Đọc và giải thích code.
2. Ghi chú lại ý tưởng (Note Taking).
3. Chuẩn bị context để handoff cho dev khác.

## Scripts

### `scripts/note_taker.py`
Ghi chú ý tưởng vào file `.agent/memory/ideas_inbox.md` theo format chuẩn.

**Usage:**
```bash
python scripts/note_taker.py --title "Refactor Auth" --content "Chuyển từ JWT sang Session" --tags "auth,backend"
```

**Output (Append to file):**
```markdown
## [2026-02-12] Refactor Auth
**Tags:** #auth #backend
**Status:** New

Chuyển từ JWT sang Session để tăng security...
```

## Data
Không có data file tĩnh, agent dựa vào codebase hiện tại và `ideas_inbox.md`.
