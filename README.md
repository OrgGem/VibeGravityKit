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

1.  **Strategy**: Planner, Market Analyst, Tech Stack Advisor.
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

### 3. How to Use (Agentic Workflow)
In VibeGravityKit, **You are the Boss.** You talk, Agents work.

#### Example: Building a "Food Delivery App"

**Step 1: Planning**
> **You**: "@[/planner] I want to build a GrabFood clone. Analyze the market and list core features."
> **Agent**: Runs `market-trend-analyst` and creates a project plan.

**Step 2: Design**
> **You**: "@[/architect] Design the database for Users, Restaurants, and Orders."
> **Agent**: Runs `db-designer` to generate a `schema.prisma` file.

**Step 3: Coding**
> **You**: "@[/frontend-dev] Create the Login screen using our Design System."
> **Agent**: Runs `context-manager` to read cues, then `diff-applier` to write the code.

---

## 📂 Project Structure

```bash
.agent/
├── workflows/       # The "Brain": Instructions for each Role
├── skills/          # The "Hands": Python scripts that do the work
└── brain/           # Project Context & Memory
```

---

## ❤️ Credits & Acknowledgements

Special thanks to **[ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)** for pioneering the data-driven approach to UI/UX generation. Your work heavily inspired our Designer role.

---

## 📄 License
MIT © [Nhqvu2005](https://github.com/Nhqvu2005)
