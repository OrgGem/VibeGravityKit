---
name: cost-tracker
description: Token cost estimation for AI-assisted development. Helps teams understand and optimize their AI spend.
---

# Cost Tracker

Estimates token usage and cost for AI-assisted coding sessions. Helps teams budget and optimize their AI workflow.

## Usage

```bash
python .agent/skills/cost-tracker/scripts/cost_estimator.py --files "src/" --model "gpt-4"
```

### What It Does

1. Counts tokens in source files (using tiktoken-like estimation)
2. Estimates cost based on model pricing
3. Suggests optimization strategies (context-manager, diff-applier)

## Data

- `data/model_pricing.json` — Token pricing for popular AI models
