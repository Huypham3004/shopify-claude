# Figma analysis — reading the Dev Mode MCP and mapping to project primitives

This is the Figma-specific heart of the skill: turn a live Figma selection into a project-convention section/snippet plan. Everything downstream (variant audit, schema, SCSS/XO-CSS) is the same as any other port; only this front-end is Figma-shaped.

## 1. Reading the selection (Dev Mode MCP)

The Dev Mode MCP reads the **current selection in the Figma desktop app**. Tools (`mcp__figma-dev-mode-mcp__<tool>`; verify exact names in-session):

| Tool | What it gives | How to use it |
| --- | --- | --- |
| `get_metadata` | compact node-tree map: node ids, names, types (FRAME/TEXT/INSTANCE/VECTOR/RECTANGLE…), x/y/w/h | **Call FIRST** on any non-trivial frame. It's cheap and gives you the skeleton + the `nodeId`s to drill into. Big frames should be explored top-down, not fetched whole. |
| `get_code` | generated framework-ish code for a node (or a passed `nodeId`) | **Hierarchy/nesting HINT ONLY.** Read it to see how layers nest and which are grouped; then author project Liquid by hand. Never paste it. |
| `get_variable_defs` | the Figma variables the selection references (color, spacing, typography, radius) | Feeds Step 0 token mapping. Prefer variable NAMES over raw values — a variable named `color/brand/primary` maps to `color(primary)`, not `#123`. |
| `get_image` | rendered PNG of the selection | Your visual ground-truth. Keep it and compare the finished Liquid render against it in Step 5. |
| `get_code_connect_map` | Figma component → codebase symbol, if Code Connect is configured | Check once; usually absent in this project. If present, it's a strong hint that a Figma instance maps to a known snippet. |

**Recommended read order:** `get_metadata` (skeleton) → `get_image` (what it looks like) → `get_variable_defs` (tokens) → `get_code` on the specific sub-nodes you need detail for. Drill into children by `nodeId` rather than fetching one giant blob.

> [!IMPORTANT]
> **`get_code` is not code to paste.** It emits generic React/Tailwind/HTML that knows nothing about `{% render 'section' %}`, snippets, `schema.js`, `<xo-container>`, XO-CSS, or Liquid. It routinely inlines hex colors, px values, and duplicates markup a snippet already provides. Use it to understand *structure*; discard its literal output. Pasting it is the #1 failure mode.

> [!NOTE]
> If the MCP is unreachable or the selection is empty, STOP. Ask the user to (1) open the Figma **desktop** app, (2) enable Preferences → "Dev Mode MCP Server", (3) select the frame. Do not invent structure from a screenshot the user pasted unless that's explicitly all you have — and say so.

## 2. Figma primitive → project primitive (the mapping table)

Read each node and translate. **The goal is not a pixel-faithful DOM clone — it's the project's semantic equivalent**, styled by tokens so it inherits the theme.

| Figma node / property | Project equivalent |
| --- | --- |
| **Auto-layout frame, vertical** | a flex column — usually just block flow inside the section wrapper; gap → `gp:…` / SCSS `gap` |
| **Auto-layout frame, horizontal** | flex row (`d:flex ai:center jc:…` XO-CSS, or SCSS flex); gap → gap token |
| **Auto-layout with wrap / a grid of N≥3 homogeneous cells** | the **`layout` system** (`{% render 'layout' %}` + `...layoutSchemaSettings()`) — see clarify Q-Layout; or a static `<div xo-grid class="xo-grid-block">` if a fixed grid |
| **Frame padding / item spacing** | container/section padding via `sectionSchemaSettings` chrome, or `p:`/`gp:` atomic (direct rem) — never a magic px |
| **Constraints (left/right/scale/center)** | responsive intent — full-bleed vs boxed maps to the section `width` setting; center → `mi:auto` |
| **TEXT layer** | semantic tag by role: page/section title → `<h1>`/`<h2>` with `fz:hN`/`fz:dN`; body → `<p>` `fz:1.4rem` (direct rem); a single emphasized word → `<em>` (subheading font). Rich copy → `richtext`/`inline_richtext` setting |
| **Text style (Figma type token)** | a heading-size token (`fz:h1`…`fz:d4`) from `theme.config.json`; body sizes are **direct rem**, not tokenized |
| **Solid fill / stroke color** | a **color token** — `c:primary`, `bgc:layer`, `bdc:border`, or SCSS `color(primary)`. **Never inline the hex.** Match the Figma variable NAME to the theme color; if it's a raw hex with no variable, map it to the nearest theme color and surface that in the preview |
| **Corner radius** | `bdrs:<token>` from `theme.config.json` borderRadius (not a raw px) |
| **Border** | `bd:sN` / `bdt:sN`… from `theme.config.json` border (values are full shorthand incl. style — don't add `bds:solid`) |
| **Effect (drop/inner shadow)** | atomic via `bxsh:` with `_` for spaces — `bxsh:0_2px_12px_rgba(0,0,0,0.18)`. Only genuinely non-atomic effects (blur behind a pseudo-element, layered `@keyframes`) or very long values go to SCSS |
| **COMPONENT / INSTANCE** | a **candidate snippet** — the strongest signal to run the Step 2 reuse audit. A Figma "Button"/"Card"/"Badge" instance almost always maps to an existing `src/snippets/` primitive; find it, don't rebuild |
| **VECTOR / icon (esp. named like a Lucide icon)** | `{% render 'icon', name: '<mapped>', size: '24' %}` — map to an existing `src/snippets/icons/icon-*.liquid`; if the vector is bespoke, inline the SVG. See the `extract-icon` skill for syncing Lucide names |
| **Image fill / raster** | `image_picker` setting + the project image snippet (`{% render 'image', … %}`) — never a hardcoded URL. Export a placeholder only for local preview |
| **Boolean/vector shape used as decoration** | section decoration setting, or an inline SVG in the markup if truly one-off |
| **Hidden layer / Figma-only annotation** | ignore — don't port dev annotations, redlines, or hidden variants |

### Naming from Figma

Figma frame/layer names are the best naming hint but are often editorial ("Hero – Homepage v3"). Build the section/snippet name from **feature + layout** (what it does + how it's arranged): `image-text-split`, `logo-marquee`, `testimonial-carousel`, `product-grid`. Q1 confirms it.

### Section vs snippet decision

- **Section** — a full-width page composition (hero, banner, featured grid, CTA band). Multiple text/image/CTA parts, meant to sit in a page template.
- **Snippet** — a single self-contained reusable primitive (a card, a badge, a price block, a callout) that a section would `{% render %}` N times. If the Figma selection is one "component" that repeats, it's a snippet (and probably already exists — audit first).

## 3. What Figma does NOT tell you (decide these yourself)

- **What's merchant-editable.** Figma has no schema concept — every string/image is literal. YOU decide what becomes a `settings.X` (copy, images, links, counts) vs structural markup. See `sections-and-snippets.md` § lift-to-settings.
- **Responsive behavior beyond constraints.** Figma may only show one breakpoint. Infer mobile stacking from the layout; the project is mobile-first (`@md` etc.).
- **Interaction / motion.** A static frame won't show hover/scroll motion (a Figma prototype/smart-animate or the user may describe it). Ask (clarify Q-Animation) rather than inventing it. On "port full", motion (xo-animate / xo-parallax) is wired via the `motion` skill; the reveal layer can also be deferred to `/polish`.
- **Real data.** Product/collection cards in Figma are mock — wire them to `collection`/`collection_list`/blocks per clarify Q-Data.

## 4. Worked example — a Figma "Image + Text" frame → a section

**Selection (`get_metadata`):** FRAME `Image text split` (1440×640, auto-layout horizontal, gap 64, padding 80), children: FRAME `media` (RECTANGLE image fill, radius 16), FRAME `content` (auto-layout vertical, gap 16) → TEXT `Eyebrow`, TEXT `Heading` (type style `Display/M`), TEXT `Body`, INSTANCE `Button/Primary`.

**Analysis:**
- Horizontal auto-layout + 2 children → a two-column split; constraints suggest boxed → section `width` boxed, mobile stacks (`d:flex fd:column@md`).
- `media` rectangle image fill → `image_picker` setting + `{% render 'image' %}`; radius 16 → `bdrs:<token>`.
- `Heading` type style `Display/M` → `fz:d2` (confirm token in `theme.config.json`); `Eyebrow` small caps → `inline_richtext`; `Body` → `richtext` (wrapper `<div class="… rte">`).
- `Button/Primary` INSTANCE → audit `src/snippets/button/` → render existing `button` variant with `label`/`link` settings. **Do not rebuild the button.**

**Result:** `src/sections/image-text-split/` — `image-text-split.liquid` (wrapper + flex + `{% render 'image' %}` + `{% render 'button' %}`), `schema.js` (`...sectionSchemaSettings({})` + image_picker + inline_richtext eyebrow + richtext body + button label/link + `presets`), `image-text-split.global.scss` or XO-CSS per Q7. Tokens (radius, type, colors) came from Step 0, not inlined.

This is the shape of every port: **structure from Figma, primitives from `src/snippets/`, values from theme tokens, editability from schema settings.**
