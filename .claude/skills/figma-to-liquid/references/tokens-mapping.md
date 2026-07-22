# Tokens mapping — Figma variables → theme tokens (Step 0)

Do this **once per design**, before porting any unit. The goal: the design's foundation (colors, fonts, type scale, radius, spacing) lives in theme settings so every ported section inherits it via CSS variables — never inline a hex or font-family inside a section.

## Source: `get_variable_defs`

Call `mcp__figma-dev-mode-mcp__get_variable_defs` on the selection (or a top frame). It returns the Figma **variables** the design references — e.g. `color/brand/primary`, `color/surface/base`, `radius/md`, `space/4`, `font/heading/display`. Prefer the variable **name** over its resolved value: a layer that fills with `color/brand/primary` maps to the theme's `primary` color, regardless of the hex behind it today.

> [!NOTE]
> If the design uses **raw values** (hex, px) with no Figma variables, you can't token-map automatically. Map each to the **nearest existing theme token** and surface that approximation in the port preview so the user can correct it. Don't silently invent new tokens.

## Destinations (project source of truth)

| Token kind | Where it lives | How referenced later |
| --- | --- | --- |
| Colors | `theme-config/theme.config.json` → `css.colors` + the active `src/config/presets/preset-N.js` | `color(primary)` (SCSS) · `c:primary` / `bgc:layer` / `bdc:border` (XO-CSS) |
| Fonts (family) | `theme.config.json` → `css.fonts` + preset | `ff:heading` / SCSS font var |
| Heading type scale | `theme.config.json` → `css.headingSizes` (`h1`–`h6`, `d1`–`d4`) | `fz:h1` … `fz:d4` |
| Body font-size | **not tokenized** — direct rem | `fz:1.4rem` |
| Border radius | `theme.config.json` → `css.borderRadius` | `bdrs:<name>` |
| Border | `theme.config.json` → `css.border` (full shorthand incl. style) | `bd:s1` / `bdt:s1` (don't add `bds:solid`) |
| Spacing | **not tokenized** — direct rem, same direction as body sizes | `p:1rem`, `gp:0.6rem` |

## Procedure

1. **Read the destinations first** so you map onto what exists: `theme-config/theme.config.json` (colors/fonts/headingSizes/borderRadius/border), the active `src/config/presets/preset-N.js`, and `src/config/global-schema/*.js` for valid setting ids.
2. **Map Figma variables onto the existing token names.** Match by role: Figma `color/brand/primary` → theme `primary`; `color/surface/base` → `layer`/`background`; `radius/md` → the borderRadius entry closest in intent.
3. **Edit the existing preset slot** — `preset-1.js` (first design) or the next free `preset-N.js`. **Never create a new preset file** (`preset-folio.js` etc.). Keep `src/config/settings_data.js` shape stable — `current` must be a full object (clone of the active preset), never a string preset name (Theme Editor rejects the string form).
4. **Only add a token if the design genuinely introduces one** the theme lacks (e.g. a new accent color) — and confirm with the user before growing the token map.
5. **Verify** the rendered `<head>` `:root` emits the expected `--color-…` / `--font-…` variables before porting sections.

## Common mistakes (from the project's token-hygiene rules)

- `color(layer-2)` — not in the colors map; use `color(layer)`.
- Confusing font-family with font-size — font family is `ff:body`; body font-size is a direct rem `fz:1.4rem`. There is **no** `fz:body` / `fz:body|1.4` form (`|` is a pseudo/state separator like `c:primary|h`, never a size multiplier).
- Inventing a token name by feel — **grep/read `theme.config.json` first**. If you can't verify a token in 1-2 seconds, don't write it.
