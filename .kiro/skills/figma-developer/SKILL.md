---
name: figma-developer
description: "Figma design integration for developers — extract design tokens, inspect components, use Figma REST API, and bridge Figma to code. Use when implementing designs from Figma or automating design-to-code workflows."
user-invocable: true
risk: safe
---

# Figma Developer

Bridge Figma designs to production code — extract tokens, inspect components, and automate design-to-code workflows.

## When to Use
- Implementing UI from Figma designs accurately
- Extracting design tokens (colors, spacing, typography) from Figma
- Using Figma REST API to automate asset export
- Setting up design token sync pipelines

## Reading Figma Designs

### Key Inspection Points
- **Frame/Component** → maps to a React/Vue component
- **Auto Layout** → maps to flexbox (`direction`, `gap`, `padding`, `alignment`)
- **Constraints** → maps to CSS positioning or responsive behavior
- **Styles** → maps to design tokens (colors, typography, effects)

### Figma REST API

```bash
# Get file structure
curl -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY"

# Export images
curl -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=1:2&format=svg"

# Get design tokens (styles)
curl -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/styles"
```

### Extract Design Tokens (JS)
```js
const Figma = require('figma-js')
const client = Figma.Client({ personalAccessToken: process.env.FIGMA_TOKEN })

const file = await client.file(FILE_KEY)
const styles = file.data.styles
// Map to CSS custom properties or Tailwind config
```

## Design Token Pipeline

```bash
# Using Style Dictionary
npm install -D style-dictionary

# tokens/colors.json (from Figma export)
{
  "color": {
    "primary": { "value": "#0066FF" },
    "neutral": { "100": { "value": "#F5F5F5" } }
  }
}

# Generates: CSS variables, Tailwind config, iOS Swift, Android XML
style-dictionary build
```

## Auto Layout → CSS Mapping

| Figma Auto Layout | CSS |
|---|---|
| Horizontal | `display: flex; flex-direction: row` |
| Vertical | `display: flex; flex-direction: column` |
| Gap | `gap: Xpx` |
| Padding | `padding: top right bottom left` |
| Align: Center | `align-items: center` |
| Fill container | `flex: 1` |

## Best Practices
- Always use Figma's "Inspect" panel for exact values, not visual estimation
- Request design tokens as Figma variables (Variables API) for synced pipelines
- Export icons as SVG and optimize with SVGO
- Use `figma-export` CLI for automated asset extraction in CI
