# 🌌 VibeGravityKit

> **The AI-Native Software House in a Box.**
> *Build enterprise-grade software with a team of 11 AI Agents — optimized for maximum speed and minimum token costs.*

---

## 🎩 What is VibeGravityKit?

Imagine having a full-stack engineering team living inside your IDE. 
**VibeGravityKit** isn't just a collection of scripts; it's a philosophy. It turns your LLM (Claude, GPT-4, Gemini) into a coordinated squad of **11 specialized agents**, from the **Architect** who designs your database, to the **Security Engineer** who guards your keys.

But here's the killer feature: **We hate wasting tokens.**
- **Context Manager**: Minifies your code before the AI sees it. (Saves ~50% tokens).
- **Diff Applier**: Applies surgical patches instead of rewriting files. (Saves ~90% tokens).

---

## 🚀 Key Roles

1.  **Strategy**: Leader, Planner, Market Analyst, Tech Stack Advisor.
2.  **Creative**: Designer (Tailwind Systems), Mobile Wizard, Tech Writer.
3.  **Engineering**: Frontend/Backend Dev, QA, Security, DevOps.

---

## 🛠️ Installation & Usage

### 1. Global Setup (Run Once)
Turn `VibeGravityKit` into a command everywhere on your machine.
```bash
git clone https://github.com/Nhqvu2005/VibeGravityKit.git
cd VibeGravityKit
pip install .
```
*(Make sure you have **Python 3.9+** and **Node.js 18+** installed)*
> **Why Node.js?** Some skills like `mobile-wizard` (Expo), `ui-ux-pro-max` (Tailwind), and `api-designer` rely on standard Node.js tools.

### 2. Deploy to a Project
Go to any project folder (new or existing) and summon your team:
```bash
cd my-new-project
vibe init antigravity
```
*Boom! The `.agent` folder is created, and your 11 agents are ready to work.*

---

## 🎮 Agentic Workflow (How to Chat)

In VibeGravityKit, **You are the Boss.** You talk, Agents work.

### 👑 The Leader Flow (Full Project Management)
When you want to start a big feature or project, call the **Leader**.
> **You**: "@[/leader] I want to add a 'Dark Mode' feature to the app."
> **Leader**:
> 1. Calls `planner` to break down tasks.
> 2. Calls `designer` to update the Design System.
> 3. Assigns `frontend-dev` to implement the switch.
> 4. Assigns `qa-engineer` to test it.

### 🧩 Calling Individual Agents (Micromanagement)
 sometimes you just need a specialist.

#### 1. The Architect (Database & API)
> **You**: "@[/architect] Update the `User` schema to include `phoneNumber` and regenerate the OpenAPI spec."
> **Agent**: Runs `db-designer` (Prisma) and `api-designer` (Swagger).

#### 2. The Frontend Developer (Coding)
> **You**: "@[/frontend-dev] Refactor the `Button` component to match the new Design System."
> **Agent**: Uses `context-manager` to read the file, then `diff-applier` to patch it safely.

#### 3. The Tech Writer (Documentation)
> **You**: "@[/tech-writer] Write a `RELEASE_NOTES.md` for this version."
> **Agent**: Scans the git log and generates a beautiful changelog.

---

## 📂 Project Structure

```bash
.agent/
├── workflows/       # The "Brain": Instructions for each Role
├── skills/          # The "Hands": Python scripts that do the work
└── brain/           # Project Context & Memory
```

## ❤️ Credits
Special thanks to **[ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)** for pioneering the data-driven approach to UI/UX generation.

## 📄 License
MIT © [Nhqvu2005](https://github.com/Nhqvu2005)
