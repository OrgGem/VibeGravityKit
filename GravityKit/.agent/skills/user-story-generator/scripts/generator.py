#!/usr/bin/env python3
"""
User Story Generator — Generate INVEST-compliant User Stories with Gherkin AC.

Follows the BA Zone INVEST + Given-When-Then framework documented in SKILL.md.

Usage:
    python generator.py --feature "User Login" --persona "registered user" --goal "log in with email and password" --value "access my account"
    python generator.py --feature "Shopping Cart" --persona "buyer" --goal "add products to cart" --value "save items before checkout"
    python generator.py --feature "User Login" --persona "registered user" --goal "log in" --value "access account" --json
    python generator.py --list-examples
"""

import argparse
import json
import sys

# ============================================================
# INVEST Checklist items (from references/invest-criteria.md)
# ============================================================
INVEST_CRITERIA = [
    ("I", "Independent",  "Story can be developed and delivered independently"),
    ("N", "Negotiable",   "Implementation details are open for discussion"),
    ("V", "Valuable",     "Delivers clear value to user or business"),
    ("E", "Estimable",    "Dev team can estimate the effort required"),
    ("S", "Small",        "Can be completed within one sprint"),
    ("T", "Testable",     "QA can write test cases from the acceptance criteria"),
]

# ============================================================
# Example story templates (generic, domain-agnostic)
# Used only when --list-examples flag is passed
# ============================================================
EXAMPLES = [
    {
        "feature": "User Login",
        "persona": "registered user with verified email",
        "goal": "log in using email and password",
        "value": "access my personal account and saved data",
        "stories": [
            {
                "id": "US-001",
                "title": "Login with email and password",
                "ac": [
                    {
                        "id": "AC1",
                        "name": "Happy path — valid credentials",
                        "given": "the user is on the login page with a verified account",
                        "when": "the user enters correct email and password and clicks Login",
                        "then": "the system redirects to the dashboard within 2 seconds",
                        "and": "a session is created and persists on page reload",
                    },
                    {
                        "id": "AC2",
                        "name": "Edge case — wrong password (lockout)",
                        "given": "the user has entered an incorrect password 3 times",
                        "when": "the user tries to log in again",
                        "then": "the system locks the account and displays: 'Too many attempts. Try again in 30 seconds'",
                        "and": None,
                    },
                    {
                        "id": "AC3",
                        "name": "Negative path — unregistered email",
                        "given": "the user enters an email that does not exist in the system",
                        "when": "the user clicks Login",
                        "then": "the system displays: 'Email or password is incorrect' (generic, no info leak)",
                        "and": None,
                    },
                ],
            }
        ],
    },
    {
        "feature": "Shopping Cart",
        "persona": "authenticated buyer",
        "goal": "add a product to the cart",
        "value": "save items before completing checkout",
        "stories": [
            {
                "id": "US-001",
                "title": "Add product to cart",
                "ac": [
                    {
                        "id": "AC1",
                        "name": "Happy path — new item added",
                        "given": "the buyer is on a product detail page with items in stock",
                        "when": "the buyer clicks 'Add to Cart'",
                        "then": "the cart item count increases by 1 and a success toast appears",
                        "and": "the product appears in the cart with correct name, price, and quantity",
                    },
                    {
                        "id": "AC2",
                        "name": "Edge case — item already in cart",
                        "given": "the product is already in the buyer's cart",
                        "when": "the buyer clicks 'Add to Cart' again",
                        "then": "the quantity of that product in the cart increases by 1",
                        "and": None,
                    },
                    {
                        "id": "AC3",
                        "name": "Negative path — out of stock",
                        "given": "the product is out of stock",
                        "when": "the buyer views the product detail page",
                        "then": "the 'Add to Cart' button is disabled and labeled 'Out of Stock'",
                        "and": None,
                    },
                ],
            }
        ],
    },
]


# ============================================================
# Core generation logic
# ============================================================

def build_story(feature: str, persona: str, goal: str, value: str, story_id: int = 1) -> dict:
    """Build a User Story data structure from the 4 required inputs."""
    us_id = f"US-{story_id:03d}"
    title = f"{goal.strip().capitalize()}"

    # Generate 3 default AC placeholders based on SKILL.md patterns
    ac_list = [
        {
            "id": "AC1",
            "name": "Happy path",
            "given": f"the {persona} is on the correct page with all prerequisites met",
            "when": f"the {persona} performs: {goal}",
            "then": "the system completes the action successfully and provides confirmation",
            "and": "the result is persisted and visible on the next page load",
        },
        {
            "id": "AC2",
            "name": "Edge case / Validation",
            "given": f"the {persona} provides invalid or boundary input",
            "when": f"the {persona} attempts to: {goal}",
            "then": "the system displays a clear, specific error message",
            "and": "no data is changed or corrupted",
        },
        {
            "id": "AC3",
            "name": "Negative path / Permission denied",
            "given": f"the {persona} does not meet the required conditions",
            "when": f"the {persona} tries to access or perform: {goal}",
            "then": "the system blocks the action and shows an appropriate message or redirect",
            "and": None,
        },
    ]

    invest_check = {c[0]: True for c in INVEST_CRITERIA}

    return {
        "id": us_id,
        "feature": feature.strip(),
        "title": title,
        "persona": persona.strip(),
        "goal": goal.strip(),
        "value": value.strip(),
        "story_statement": (
            f"**As a** {persona.strip()}\n"
            f"**I want to** {goal.strip()}\n"
            f"**So that** {value.strip()}"
        ),
        "invest": invest_check,
        "acceptance_criteria": ac_list,
        "notes": [],
    }


# ============================================================
# Output formatters
# ============================================================

def format_invest_table(invest: dict) -> str:
    lines = ["| Criteria | Status | Description |",
             "|----------|--------|-------------|"]
    for letter, name, desc in INVEST_CRITERIA:
        status = "✅" if invest.get(letter, False) else "⚠️ Review needed"
        lines.append(f"| **{letter}** — {name} | {status} | {desc} |")
    return "\n".join(lines)


def format_ac(ac_list: list) -> str:
    blocks = []
    for ac in ac_list:
        block = [f"**{ac['id']}: {ac['name']}**"]
        block.append(f"- **Given** {ac['given']}")
        block.append(f"- **When** {ac['when']}")
        block.append(f"- **Then** {ac['then']}")
        if ac.get("and"):
            block.append(f"- **And** {ac['and']}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def print_story(story: dict):
    sep = "=" * 65
    thin = "─" * 65

    print(f"\n{sep}")
    print(f"  [US] {story['id']}: {story['title']}")
    print(f"  Feature: {story['feature']}")
    print(sep)

    print("\n### User Story\n")
    print(story["story_statement"])

    print(f"\n{thin}")
    print("\n### INVEST Self-check\n")
    print(format_invest_table(story["invest"]))
    print("> [!] Review each criterion against the actual story before submitting.")

    print(f"\n{thin}")
    print("\n### Acceptance Criteria\n")
    print(format_ac(story["acceptance_criteria"]))

    if story.get("notes"):
        print(f"\n{thin}")
        print("\n### Notes\n")
        for note in story["notes"]:
            print(f"- {note}")

    print(f"\n{sep}\n")


def print_examples():
    print("\n" + "=" * 65)
    print("  [EXAMPLES] INVEST + Gherkin format")
    print("=" * 65)
    for ex in EXAMPLES:
        story = build_story(ex["feature"], ex["persona"], ex["goal"], ex["value"])
        # Override with richer example AC
        story["acceptance_criteria"] = ex["stories"][0]["ac"]
        print_story(story)


# ============================================================
# CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="User Story Generator — INVEST + Given-When-Then (Gherkin) format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generator.py --feature "User Login" --persona "registered user" \\
      --goal "log in with email and password" --value "access my account"

  python generator.py --feature "Product Search" --persona "buyer" \\
      --goal "search products by keyword" --value "find items quickly" --json

  python generator.py --list-examples
        """
    )
    parser.add_argument("--feature",  type=str, help="Feature or module name (e.g. 'User Login')")
    parser.add_argument("--persona",  type=str, help="Who uses this feature (e.g. 'registered buyer')")
    parser.add_argument("--goal",     type=str, help="What they want to do (verb phrase)")
    parser.add_argument("--value",    type=str, help="Business/user value delivered (So that...)")
    parser.add_argument("--id",       type=int, default=1, help="Starting story ID number (default: 1)")
    parser.add_argument("--json",     action="store_true", help="Output as JSON instead of Markdown")
    parser.add_argument("--list-examples", action="store_true", help="Show built-in example stories and exit")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list_examples:
        print_examples()
        sys.exit(0)

    # Validate required args
    missing = [f for f, v in [("--feature", args.feature), ("--persona", args.persona),
                                ("--goal", args.goal), ("--value", args.value)] if not v]
    if missing:
        print(f"[!] Missing required arguments: {', '.join(missing)}", file=sys.stderr)
        print("   Run with --help for usage, or --list-examples to see samples.", file=sys.stderr)
        sys.exit(1)

    story = build_story(args.feature, args.persona, args.goal, args.value, args.id)

    if args.json:
        print(json.dumps(story, ensure_ascii=False, indent=2))
    else:
        print_story(story)

    print("[TIP] The AC above are scaffolds. Review and refine each Given/When/Then")
    print("   against the full checklist in: checklists/quality-checklist.md\n")


if __name__ == "__main__":
    main()
