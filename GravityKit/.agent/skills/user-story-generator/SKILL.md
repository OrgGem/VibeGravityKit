---
name: user-story-generator
description: |
  Generates User Stories and Acceptance Criteria following INVEST criteria +
  Given-When-Then (Gherkin) format for BA/PO. Enforces 6 INVEST criteria
  (Independent, Negotiable, Valuable, Estimable, Small, Testable) and
  structures AC in Gherkin syntax.

  Supports 3 modes:
  - Mode A (Write new): Generate US + AC from a feature description
  - Mode B (Refine): Review & improve an existing US/AC
  - Mode C (Add AC): Supplement AC to an existing User Story

  Trigger keywords: "write user story", "create US", "write AC",
  "acceptance criteria", "INVEST user story", "Given-When-Then AC",
  "Gherkin AC", "refine user story", "review this US", "split user story",
  "story for this feature", paste feature description + "write story",
  upload PRD + "create US list".

  NOT for: writing full PRD/URD/SRS, detailed technical test cases
  (AC ≠ test case), formal Use Cases, or business rules documentation.
---

## Purpose

Help BA/PO write high-quality User Stories and Acceptance Criteria that are
ready for dev estimation and QA test case writing.

---

## Standard Workflow

### Step 1: Identify Mode

Ask the user to select one of 3 modes:

- **Mode A — Write New**: User provides a feature description → generate US + AC from scratch
- **Mode B — Refine**: User has existing US/AC → review and suggest improvements
- **Mode C — Add AC**: User has a US → add detailed AC

If the user pastes clear content, infer the mode automatically and confirm once.

### Step 2: Collect Required Inputs

Need all 4 pieces of information before generating. Ask if missing:

1. **Persona/User type**: Who will use this feature? (e.g., Student, Mentor, Admin, Enterprise HR)
2. **Goal**: What does the user want to do?
3. **Business value**: Why is this feature needed?
4. **Context/Scope**: Which feature/module does this belong to?

**NEVER fabricate inputs** — always ask if not provided.

### Step 3: Generate User Story

Use the standard 3-part format:

```
**US-[FEATURE-CODE]-[NUMBER]**: [Short descriptive title]

**As a** [specific persona — NOT generic "user"]
**I want to** [specific, measurable action]
**So that** [clear business value — NOT a repeat of I want]
```

### Step 4: Apply INVEST Checklist

Self-check the US against all 6 criteria before outputting:

| Criterion       | Check Question                                     | If Fail → Action              |
| --------------- | -------------------------------------------------- | ----------------------------- |
| **I**ndependent | Can this story be built & tested independently?    | Split dependency or merge     |
| **N**egotiable  | Is there room for discussion (not over-specified)? | Remove hard technical details |
| **V**aluable    | What value does it deliver to user/business?       | Rewrite "So that"             |
| **E**stimable   | Can dev estimate the effort?                       | Add context/constraints       |
| **S**mall       | Completable in 1 sprint (≤ 5 dev days)?            | Split into smaller stories    |
| **T**estable    | Can QA write test cases from the AC?               | Add specific AC               |

See detailed guide: `references/invest-criteria.md`

### Step 5: Generate Acceptance Criteria

Each US needs **minimum 3 AC** in Given-When-Then format:

```
**AC1: [Scenario name — Happy path]**
- **Given** [specific precondition]
- **When** [user action]
- **Then** [measurable expected result]
- **And** [secondary result if applicable]

**AC2: [Scenario name — Edge case / Validation]**
- **Given** [edge case context]
- **When** [action triggering edge case]
- **Then** [system handles correctly]
- **And** [specific behavior/message]

**AC3: [Scenario name — Negative path / Error]**
- **Given** [error context]
- **When** [action leading to error]
- **Then** [system handles error correctly]
- **And** [specific error message displayed]
- **And** [no unintended side effects]
```

**Rules for good AC:**

- Cover all 3 types: happy path, edge case, negative path
- Every Given/When/Then must be measurable (numbers, clear states)
- Avoid vague words: "fast", "appropriate", "user-friendly"
- Do NOT write implementation logic (that's for dev)
- 1 AC = 1 scenario only — never merge multiple cases

### Step 6: Final Output

Present in this structure:

1. **User Story** (3-line As a / I want to / So that)
2. **INVEST Self-check** (6-row table with ✅/⚠️)
3. **Acceptance Criteria** (numbered AC1, AC2, AC3…)
4. **Notes** (dependencies, assumptions, open questions for PO)

---

## Anti-Patterns — NEVER Do These

❌ **Generic persona**: "As a user" → ✅ "As a registered student who has verified their email"

❌ **Vague goal**: "I want to manage profile" → ✅ "I want to update my email address"

❌ **Value repeats goal**: "So that I can manage profile" → ✅ "So that I receive notifications at the correct address"

❌ **AC describes UI**: "Then button turns blue" → ✅ "Then system displays a confirmation message"

❌ **AC contains tech logic**: "Then call API /v1/users/update" → ✅ "Then user data is updated and persisted"

❌ **Too few AC**: Only 1 happy path → ✅ Minimum 3 AC covering all branches

❌ **Story too large**: 1 story covers full CRUD → ✅ Split into Create, Read, Update, Delete

---

## When to Split a User Story?

Propose splitting when:

- Story title contains "AND" (e.g., "Login AND Register")
- Multiple different personas in 1 story
- Story covers multiple CRUD operations
- AC exceeds 7–8 scenarios
- Dev estimates > 5 working days

**Common split patterns:**

- **By CRUD**: Create / Read / Update / Delete
- **By persona**: Student / Mentor / Admin / Enterprise
- **By business rule**: Happy path / Validation / Permission
- **By data type**: Split by type of data being processed
- **By workflow step**: Register → Pay → Enroll → Study
- **By platform**: Web / Mobile App / API

---

## Script Usage (Quick Generation from Feature List)

For rapid scaffolding from a list of known features:

```bash
python .agent/skills/user-story-generator/scripts/generator.py \
  --features "login,cart,checkout" \
  --roles "buyer,admin"
```

Output: Markdown user stories with basic AC per feature.

> **Note**: Script output is a starting point only. Always apply the
> INVEST checklist and refine AC using the Gherkin format above
> before presenting to stakeholders.

---

## Reference Files

| File                               | Purpose                                                      |
| ---------------------------------- | ------------------------------------------------------------ |
| `templates/user-story-template.md` | Blank template to fill in                                    |
| `templates/ac-template.md`         | Standard Gherkin AC template                                 |
| `references/invest-criteria.md`    | Deep-dive explanation of all 6 INVEST criteria with examples |
| `references/examples.md`           | 7 real-world examples (EdTech / SaaS domain)                 |
| `checklists/quality-checklist.md`  | Self-review checklist before final output                    |

---

## Integration with GravityKit Lifecycle

This skill sits between **Requirements** and **Planning** phases:

```
gravity-requirement-analysis → [user-story-generator] → concise-planning → implementation
```

**Complementary skills:**

- `gravity-requirement-analysis` — Requirement clarification before writing stories
- `concise-planning` — Break stories into dev tasks
- `test-generator` — Generate technical test cases from AC
- `gravity-adversarial-review` — Adversarial review of AC completeness

---
