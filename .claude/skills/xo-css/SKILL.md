---
name: xo-css
description: MUST be invoked (via Skill tool) BEFORE writing any atomic class attribute in liquid templates (snippets, sections, blocks) AND ALWAYS when user picks "XO-CSS-first" in clarify-protocol Q7. XO-CSS = atomic framework with syntax `property:value|pseudo@breakpoint!` (e.g. p:1rem, c:primary|h, d:none@md, pos:absolute!). Memory of property/pseudo shortcuts is incomplete — agent skip = hardcoded values (`p:10px` instead of `p:1rem`), wrong color tokens, dynamic class concat bugs. Covers property/pseudo shortcuts, design tokens from theme-config/theme.config.json (heading sizes `h1-h6`/`d1-d4`, colors, fonts) — body font-sizes AND spacing (padding/margin/gap/positioning) use direct rem values (e.g. `fz:1.4rem`, `p:1rem`, `gp:0.6rem`), not tokenized, mobile-first responsive design, group hover (*gh), parent-attribute selectors (/xo-attr), safe patterns for dynamic class names in Liquid. `references/basics.md` § "Translating from design SCSS" covers the 3-tier framework (atomic / xo-attribute / SCSS-sidecar), direct-rem body font-sizes (e.g. `fz:1.4rem`), and the edge cases (keyframes, chained/multi-target selectors, pseudo-elements) that ALWAYS land in SCSS regardless of strategy — while multi-value / function values (grid, box-shadow, transition lists, calc) are atomic via the underscore `_` space-separator. There is no separate "Hybrid" CSS strategy — the tier-3 SCSS sidecar is part of XO-CSS-first by definition.
---

# XO-CSS

Atomic CSS framework for Shopify themes with a compact, expressive syntax.

## Syntax

```
property:value|pseudo@breakpoint!
```

### Examples

```html
<div class="c:primary">Color primary</div>
<div class="c:foreground|h">Color on hover</div>
<div class="p:1rem@md">Padding on ≥768px</div>
<div class="pos:relative!">Position relative !important</div>
```

## Core Rules

1. **Use rem, never px** — `p:1rem`, not `p:10px` (atomic pipeline emits direct values; px would be off-grid)
2. **Use rem when in doubt** — `w:1rem`, not `w:10px`
3. **Use color tokens** — `c:primary`, not `c:white` or `c:#fff`
4. **Do NOT concatenate dynamic class names** — XO-CSS cannot generate CSS from runtime strings
5. **CSS-native escape hatches allowed** — `var(--custom)`, `%`, `vh`, `vw`, `auto`, `inherit`

## Navigation — When to read which file

### Foundations

- **New to XO-CSS** → `references/basics.md`
  - Full syntax breakdown, token system, safe patterns in Liquid

### By task

- **Layout / flex / grid / spacing / positioning** → `references/layout.md`
- **Colors, typography, borders, backgrounds, shadows** → `references/styling.md`
- **Responsive design (breakpoints, mobile-first, max-width)** → `references/responsive.md`
- **Pseudo states, group hover, parent attributes, transforms** → `references/advanced.md`

### Lookup tables

- **Find a property shortcut** (`p` → `padding`, etc.) → `references/properties.md`
- **Find a pseudo shortcut** (`h` → `:hover`, etc.) → `references/pseudo.md`

### Translation

- **Mapping design SCSS → atomic classes** (when user picks "XO-CSS strategy" in clarify-protocol Q7) → `references/basics.md` § "Translating from design SCSS" (3-tier framework, font-size table, worked example)

### Troubleshooting

- **Class isn't generating, error, or unexpected behavior** → `references/debugging.md`

## Source

- **Plugin**: `./xo-css.vite-plugin.js`
- **Token config**: `./theme-config/theme.config.json`
- **Generated CSS**: `./src/styles/atomic.scss`
