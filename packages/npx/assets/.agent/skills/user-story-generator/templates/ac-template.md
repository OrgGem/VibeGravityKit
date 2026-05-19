# Acceptance Criteria Template · GravityKit

> Format: Given-When-Then (Gherkin syntax)  
> Minimum 3 AC per User Story: Happy path + Edge case + Negative path

---

## AC1: [Scenario name — Happy path]

**Given** [precondition 1]  
**And** [precondition 2 — if applicable]

**When** [main user action]

**Then** [primary measurable result]  
**And** [secondary result 1 — if applicable]  
**And** [secondary result 2 — if applicable]

---

## AC2: [Scenario name — Edge case / Validation]

**Given** [edge case context]

**When** [action that triggers the edge case]

**Then** [system handles correctly]  
**And** [specific behavior or message]

---

## AC3: [Scenario name — Negative path / Error]

**Given** [error context]

**When** [action leading to error]

**Then** [system handles error correctly]  
**And** [specific error message displayed]  
**And** [no unintended side effects]

---

## Pre-commit Checklist

- [ ] Each AC tests exactly 1 scenario
- [ ] Given/When/Then are all measurable (numbers, clear states)
- [ ] No vague words: "fast", "appropriate", "user-friendly"
- [ ] No implementation logic (API names, DB tables, code)
- [ ] No specific UI details (colors, pixel positions)
- [ ] Minimum coverage: 1 happy + 1 edge + 1 negative
- [ ] QA can write test cases from this AC

---

## AC Quality Rules

| Rule            | Bad ❌                     | Good ✅                             |
| --------------- | -------------------------- | ----------------------------------- |
| Measurable Then | "System responds quickly"  | "System responds within 2 seconds"  |
| No UI detail    | "Button turns blue"        | "Confirmation message is displayed" |
| No tech logic   | "Call POST /api/users"     | "User data is saved and persisted"  |
| Specific state  | "Shows an error"           | "Displays: 'Invalid email format'"  |
| Single scenario | AC covers login + register | Separate AC for each                |

---
