---
name: accessibility-pro
description: "Accessible component development following WCAG 2.1/2.2 AA standards. Use for building keyboard-navigable, screen-reader-friendly, ARIA-compliant UI components."
user-invocable: true
risk: safe
---

# Accessibility Pro

Expert in building accessible, inclusive UI components following WCAG 2.1/2.2 AA standards.

## When to Use
- Building UI components that must be keyboard-navigable
- Auditing components for screen reader compatibility
- Implementing ARIA roles, labels, and live regions
- Ensuring color contrast, focus management, and semantic HTML

## Core Principles

### Semantic HTML First
- Use native HTML elements before ARIA (`<button>` not `<div role="button">`)
- Headings hierarchy: `<h1>` → `<h2>` → `<h3>`, never skip levels
- Landmark regions: `<main>`, `<nav>`, `<aside>`, `<footer>`

### Keyboard Navigation
- All interactive elements reachable via Tab
- Logical focus order matching visual layout
- Visible focus indicators (never `outline: none` without replacement)
- Escape closes modals/dropdowns; Arrow keys navigate menus

### ARIA Patterns
- `aria-label` / `aria-labelledby` for unlabeled elements
- `aria-expanded`, `aria-haspopup` for disclosure widgets
- `aria-live="polite"` for dynamic content updates
- `role="dialog"` + `aria-modal="true"` for modals

### Color & Contrast
- Normal text: 4.5:1 contrast ratio minimum
- Large text (18px+): 3:1 minimum
- UI components: 3:1 against adjacent colors

## Common Patterns

```tsx
// Accessible button with loading state
<button
  aria-busy={isLoading}
  aria-label={isLoading ? 'Saving...' : 'Save'}
  disabled={isLoading}
>
  {isLoading ? <Spinner aria-hidden /> : 'Save'}
</button>

// Skip navigation link
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

## Testing Checklist
- [ ] Tab through all interactions without mouse
- [ ] Test with screen reader (NVDA/VoiceOver)
- [ ] Check color contrast with browser DevTools
- [ ] Verify zoom to 200% doesn't break layout
- [ ] Validate with axe-core or Lighthouse accessibility audit
