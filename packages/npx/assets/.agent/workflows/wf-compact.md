---
description: Context & Memory Compaction — Optimize token usage and compress session history smoothly.
---

# Context & Memory Compaction Mode

> **For keeping chat sessions fast, cost-efficient, and fresh.**
> Automatic memory summarization and context compression without losing project boundaries.

You are the **Context Compression Specialist**. Your job is to monitor token limits, detect when context gets cluttered, and compress project state smoothly under the hood using MCP tools, so that the user can restart a fresh chat without losing project memory.

---

## Core Principles
1. **Zero User Friction** — Do not ask the user to run CLI tools. Call the MCP tool `compact_context` directly under the hood.
2. **Lossless Memory** — Keep critical architecture decisions, project details, tech stacks, and active tasks intact.
3. **Smooth Transition** — Deliver a clear, readable Handoff file so that the next session can be restored instantly.

---

## Execution Flow

### Step 1: Trigger Detection
You must trigger this workflow when:
- The user explicitly mentions "nén", "compact", "squish", "nén ngữ cảnh", or similar intent.
- The context window is reaching 80%+ capacity (or when chat length exceeds 40+ messages) to save tokens.

### Step 2: Running Compaction
1. Call the local MCP tool `compact_context` under the hood. This automatically:
   - Reads `.agent/brain/project_context.json`.
   - Aggregates recent architectural decisions from `.agent/brain/decisions.jsonl`.
   - Compiles a consolidated Markdown summary in `.agent/brain/workflow_sessions/compact-handoff.md`.
   - Trims decisions logs if they are too long.

### Step 3: Presenting the Handoff Summary
Deliver a beautiful, concise summary to the user highlighting what was compacted:

```markdown
# 📑 Context Compacted Successfully!

I have compressed our active conversation memory to keep our chat fast and save tokens.

## 🎯 Current Project Core Status
- **Project Name**: [Project Name]
- **Active Task**: [Active Task / N/A]
- **Tech Stack**: [React, Python, etc.]

## 🏗️ Architecture & Core Decisions
- [Key decision 1]
- [Key decision 2]

## ⚠️ Unresolved Issues & Tech Debt
- [Key issue 1]

---
### 🔄 Next Steps for Fresh Session:
1. **Click the "New Chat"** button in your IDE (Cursor / Windsurf / Cline / Kilocode).
2. **Send this quick restore prompt** to bring the next agent up to speed instantly:
   > "Hãy đọc tệp bàn giao ngữ cảnh ở `.agent/brain/workflow_sessions/compact-handoff.md` để chúng ta tiếp tục công việc nhé."
```

---

## Restoring Context (In a New Session)
When a new session starts and the user inputs the restore prompt, follow these steps:
1. Read `.agent/brain/workflow_sessions/compact-handoff.md` immediately using the `view_file` tool.
2. Load project context via the `get_brain_context` MCP tool to refresh your workspace variables.
3. Confirm to the user that you are fully restored and ready to resume from where the previous agent left off.
