---
name: design-to-liquid
argument-hint: "[section-name]"
description: Use when porting a static HTML design (typically under a design/ folder built with the xo-include + xo-component HTML assembler convention) into this Shopify Liquid theme under src/. ENTRY POINT — every invocation first checks the `xo-design` MCP (`mcp__xo-design__get_selection`) for a section the user picked via the xo-design ◎ Pick section toolbar, so phrases like "/design-to-liquid làm section này" / "port this one" / a bare "/design-to-liquid" auto-target the selected section without re-asking. Falls back to manual section discovery only when no selection is set. Step 0 — map design tokens (colors, fonts, type scale, radius, spacing) into theme settings (global-schema + settings_data + theme.config.json) so every section inherits the foundation via CSS variables; never inline hex/font-family per section. Then covers file-structure mapping (design page → JSON template, design section → liquid section, design component → snippet), converting xo-include/xo-component to {% section %} / {% render %}, lifting per-section hardcoded text/images/links into schema settings, and consuming any design documentation/blueprints. The default working assumption is that src/snippets/ already contains stable, reusable snippets — so BEFORE rendering any snippet inside a new section, audit its existing variants (`<snippet>-1`, `<snippet>-2`, …), trace what's hardcoded vs settings-driven, and pick the closest match. Escalate only when needed — theme setting cascade, then variant modification, then new variant. Never inline section-scoped CSS to hack a snippet's look. Header and footer designs are a special case — use this skill too for "port header", "làm header theo design", "port header-1 / header-2 / header-kids → theme", "footer theo design", "port footer-3 / footer-parfum": they never become a new section; the skill routes them to adapting the single header/footer section via its `layout` setting + layout snippets (references/header-port.md, references/footer-port.md). Ships a Python validator at .claude/skills/design-to-liquid/scripts/validate-schema.py to run after each schema.js edit.
---

# Design → Liquid

Pipeline skill for porting any HTML design into this Shopify Liquid theme.

## Core Assumption — Don't Recreate What Exists

> [!IMPORTANT]
> **`src/snippets/` is stable.** Most snippets (button, product-card, article-card, icon, image, header pieces, card primitives, etc.) are already built and rarely change. The `src/snippets/_base/` helpers change even less.
>
> When porting a design, your work usually looks like:
>
> 1. **Read** the design page/section/component.
> 2. **Check** `src/snippets/` for the equivalent — almost always exists.
> 3. **Restyle** SCSS (BEM `.xo-…__el--mod`) or atomic XO-CSS classes so the existing snippet renders to the new visual.
> 4. **Compose** the section (new `src/sections/<name>/<name>.liquid` + `schema.js`) using existing snippets via `{% render %}`.
> 5. **Build** the page's JSON template referencing the new section(s).
>
> Creating a brand-new snippet should be the **exception**, not the default. If you think you need a new snippet, search `src/snippets/` first.
>
> **Before modifying shared infrastructure** (any file under `src/groups/`, any frequently-shared snippet like `cart-mini`, `predictive-search-base`, `modal-content`, `menu-horizontal`), pause and consider the `system-upgrade` skill as a pre-port checkpoint — if no existing reference under `references/` documents the pattern you're about to modify, document FIRST (new reference / AGENT.md addendum), commit `.claude` umbrella, THEN apply the port. This mirrors the header-port + modal-port precedents and prevents the next agent from re-deriving the same pattern from scratch. (Header/footer ports are already documented in `references/header-port.md` / `footer-port.md` — no checkpoint needed unless the port goes beyond them.)

## Two layers of authority — project conventions + Shopify-native

> [!IMPORTANT]
> This pipeline straddles **two layers**. Consult BOTH before writing any non-trivial Liquid:
>
> 1. **Project layer** (`src/`) — the custom source convention. Read these BEFORE writing schema or markup:
>    - `src/create-schema.js` — `createSectionSchema` / `createBlockSchema` / `createSchemaSettings` API
>    - `src/snippets/_base/section/schema.js` — `sectionSchemaSettings(...)` helper (`color_scheme`, `width`, `height`, padding, borders, decoration)
>    - `src/snippets/_base/input-settings/` — reusable input groups (alignment, color, space, …)
>    - `src/snippets/settings-adapter/*.liquid` — how settings emit CSS variables at runtime
>    - `src/config/global-schema/*.js` — every valid theme setting `id` + range/step/option
>    - 1-2 existing sections/blocks under `src/sections/` / `src/blocks/` of similar shape (for convention)
>
> 2. **Shopify-native layer** — authoritative Liquid syntax + theme architecture rules. Consult the **`liquid` skill** — its references live at `.claude/skills/liquid/references/{tags,filters,objects,blocks,idioms,gotchas}.md`. Self-contained, distilled from shopify.dev via context7.
>
> The project's source layer **diverges from native Shopify in three areas** (build pipeline bridges): schema in separate `schema.js` → compiled `{% schema %}` JSON · per-component CSS in `<name>.global.scss` → compiled via scss-glob · doc blocks via `{% comment %}` (not `{% doc %}`). Native Shopify wins for liquid syntax inside the body; project convention wins for file layout + helper usage.

## Quick Mental Model

| HTML design (xo-assembler convention) | Shopify Liquid theme (`src/`)                                  |
| ------------------------------------- | -------------------------------------------------------------- |
| `<design>/pages/X.html`               | `src/pages/<template>/index.preset-N.json`                     |
| `<design>/sections/X/X.html`          | `src/sections/X/X.liquid` + `schema.js`                        |
| `<design>/components/Y/Y.html`        | `src/snippets/Y/Y/Y.liquid` (only if not already present)      |
| `<xo-include src="sections/X/X.html">`| `{% section 'X' %}` (in layout/group) or entry in JSON template|
| `<xo-component src="Y" data="…">`     | `{% render 'Y', … %}`                                          |
| `<xo-container>`, `<xo-carousel>`, …  | **same tag** — xo-webcomponents are runtime in both worlds     |
| `<i data-lucide="X">`                 | `{% render 'icon', name: '<mapped>', size: '24' %}`            |
| Hardcoded image URL                   | `image_picker` setting + `image_url` filter (or the project's image snippet) |
| Hardcoded copy                        | `section.settings.X` / `block.settings.X`                      |
| `<body class="theme-X">`              | Color scheme override and/or `settings.root_class_name`        |

## Before you start — read project state

> [!IMPORTANT]
> This skill is the **executor** (HOW). The **planner** skill (in `.claude/skills/planner/`) owns **what's planned and where we are**. Before porting anything, confirm state has been read.

Two lightweight checks (skip if a `planner` invocation already happened earlier in this conversation):

1. **`.agent-state/PROGRESS.md`** — read the top 1-2 entries. Confirm the section/page you're about to port wasn't already done last session, and there are no notes ("⏸ blocked on X") that affect it.
2. **`.agent-state/PLAN.md`** — find the row for the work you're about to do. Confirm it isn't ⏸ paused upstream (e.g. Theme tokens row ⏸ means Step 0 is blocked → cascading sections shouldn't start). If the work isn't in the plan yet, add a row and ask the user to confirm priority before continuing.

If state files don't exist or are stale, hand off to the `planner` skill (kickoff or resume protocol) before executing.

The remainder of this skill describes the execution itself. Updating PLAN/PROGRESS is the planner's job — see the "When you finish" section at the bottom.

## Entry Point — Which section to port?

> [!IMPORTANT]
> Every `/design-to-liquid` invocation **starts by checking the `xo-design` MCP**
> for a section the user picked via the xo-design `◎ Pick section`
> toolbar. The user pointed visually — don't ask them to type the name again.

```
on /design-to-liquid …:

  1. If the user message explicitly names a section (e.g. "/design-to-liquid hero"):
     → skip the picker, proceed to Step 1 with that name.

  2. Else, call mcp__xo-design__get_selection().
       • Selection found → confirm "Convert {page}.{sectionName} → src/sections/{sectionName}/ ?"
                          then proceed to Step 1, but skip discovery — use
                          selection.htmlPath + selection.scssPath directly.
       • selection: null →
            – If the user said "này / this / the one I picked" → ask them
              to click ◎ Pick in xo-design first, then re-invoke.
            – Otherwise → fall through to normal Step 1 survey.
       • MCP unreachable (xo-design not running, studio mode, 404) → fall
            through silently. Mention once: "xo-design picker unreachable;
            running manual discovery instead."

  3. After the port lands (validator passes, files written), call
     mcp__xo-design__clear_selection() so the chip in xo-design disappears and
     the next invocation doesn't accidentally re-target the same section.
```

> [!IMPORTANT]
> **The picker only resolves WHICH section — it does NOT shorten the workflow.** "auto-target without re-asking" means *don't re-ask the section name*; it does **not** mean skip the interview or the audit. After a picker hit you still run, in order: Step 1 (survey both sides), **Step 1.5 (clarify — Q7 CSS strategy ALWAYS fires)**, **Step 2 (mandatory variant audit for every `<xo-component>` — two-sided read + A/B/C ladder, where C = STOP and ask the user)**, then Step 3+. The picker fast-path is the historical cause of skipped Q7 + skipped snippet audits — do not jump from "read htmlPath" straight to "write the section".

`Selection` returns absolute on-disk paths (`htmlPath`, `scssPath`) you can
pass straight to `Read()`. Studio-mode previews never expose these tools, so
treat any failure as "no selection".

→ See `references/picker-protocol.md` for the full protocol + edge cases.

### Is the target a header or footer? — route before Step 1

Once you know which design section you're porting, check whether it is a **site header or footer**. Signals
(any one is enough):

- its design folder name starts with `header` or `footer`, whatever follows. The suffix is whatever the
  designer chose — a number (`header-1`, `footer-3`), a preset (`header-kids`), or any arbitrary word
  (`header-aurora`, `footer-minimal`, `header-v2-final`). It carries no meaning for the port and never becomes
  a section or layout name. A designer may also skip the prefix entirely (`topbar`, `site-nav`,
  `bottom-bar`) — the next two signals catch those;
- on the design page it sits **outside `<main>`** (header/footer area, not page content);
- the markup is the site chrome: logo/wordmark + main nav + search/account/cart icons (header), or link
  columns + newsletter/social + copyright/payment row (footer).

If it is, **don't create a section.** The theme ships exactly one `header` and one `footer` section
(`src/groups/headers/header/`, `src/groups/footers/footer/`), each with a `layout` select that dispatches to
layout snippets in `src/snippets/header-layout/` / `src/snippets/footer-layout/`. A second header/footer
section type would let merchants activate two at once — a Theme Store rejection (SF-SECTION-01). The port
becomes "make the existing section match the design": pick/tune a layout, restyle, or (after asking) add a
layout. Follow `references/header-port.md` or `references/footer-port.md` instead of Steps 3–5 below; Step 0
(tokens), Step 1 (two-sided survey), Q7 of Step 1.5 and Step 6 (restyle) still apply, and Q1 becomes the
"which layout?" question (`references/clarify-protocol.md` § Q1).

## Authoring Workflow

### Step 0 — Map design tokens (do this FIRST, once per design)

> [!IMPORTANT]
> **Before porting any section, map the design's foundation tokens** — colors, fonts, type scale, radius, spacing — into the theme settings (`src/config/global-schema/*.js`, `src/config/presets/preset-N.js`, `theme-config/theme.config.json`).
>
> Skipping this and inlining hex colors / font-family strings inside sections is the most common porting mistake. Once tokens are mapped, every ported section automatically inherits the design's foundation via CSS variables (`color(primary)`, `var(--font-heading-1-size)`, etc.).
>
> **Project convention:** edit `src/config/presets/preset-1.js` (first design) or the next free `preset-N.js` slot — **do not create new preset files**. Then keep `settings_data.js` shape stable (`import { preset1 } from './presets/preset-1.js'`).

→ See `references/tokens-mapping.md`. Verify in the rendered `<head>` that `:root` emits the expected `--color-…` / `--font-…` variables before moving on.

### Step 1 — Survey the design

Find the design root folder (typically `design/` but the name varies). Inside, expect this convention:

- `pages/*.html` — page-level compositions, mostly `<xo-include>` calls
- `sections/<name>/<name>.html` (+ optional `.scss`) — composable sections
- `components/<name>/<name>.html` (+ `.scss`, `.signature.json`) — reusable components

Read any markdown documentation in the design folder (brand/style guide, design system, blueprints, component inventories) before touching files.

> [!NOTE]
> **While reading the section's SCSS/markup, flag a layout-able collection** — N≥3 homogeneous items laid out as a grid (`display:grid` / `grid-template-columns`), masonry (`column-count`), or carousel (`scroll-snap` / slider). That triggers **clarify-protocol Q8 (Layout mechanism)** — offer the `layout` system vs a static grid primitive vs keep. Don't copy the raw layout CSS into the section verbatim. See `references/grid-and-layout.md`.

> [!NOTE]
> **Flag a collection-tabs signature** — a row of tab triggers (text pills / buttons, e.g. category names) sitting directly **above a repeating product-card grid**, where clicking a tab is meant to swap which collection's products show. The design ships these tabs *static* (`xo-tabs` / button row), but they must be **converted** to the `xo-collection-tabs` trio — do NOT pass them through. On match, route to `references/collection-tabs.md` and steer **clarify Q3** to its collection-tabs form (one inline block per tab, each with a `collection` picker — no `collection_list`, no `All` tab). Don't confuse with generic content `xo-tabs`, a static grid with no tabs, or collection-page filters.

> [!IMPORTANT]
> **Read BOTH sides of every `<xo-component src=X>`.** For each `<xo-component src="X">` rendered inside the section's HTML, you MUST open `design/src/components/X/` (both `X.html` and `X.scss`) AND `src/snippets/X/` (project's snippet body + SCSS). These two often share a NAME but render different visual archetypes — see PROGRESS session 5b for the concrete miss (design's `collection-card` was caption-below; project's was overlay-on-image; reuse decision based on one-sided audit produced wrong visual).
>
> Same applies to `<xo-include>` of design sections vs project's `src/sections/`. Read both sides before any reuse decision.
>
> This rule is non-negotiable. Skipping it leads to a port whose markup compiles, schema validates, but **visually does not match the design** — caught only by manual editor preview, after the wrong reuse choice is already baked in.

→ See `references/blueprint-protocol.md`.

### Step 1.5 — Clarify ambiguities (batched interview)

> [!IMPORTANT]
> After Step 1 survey, before Step 2 audit, walk a short decision table and surface any architectural choice the agent would otherwise pick silently. Goal: minimum friction — only ask what's genuinely ambiguous, batch the rest.

Eight decisions to evaluate per port. **Q1 (name) and Q7 (CSS) ALWAYS fire; Q2–Q6 and Q8 obey the skip rule:**

1. **Section name** — **ALWAYS fire.** Before the name is baked into 5-7 files, ask the user to confirm or change it. Offer `Keep <current>` (recommended when already clean) + 2-3 suggested names built from the **feature + layout** formula (what it does + how it's arranged → `featured-products-tabs`, `hero-collage`, `testimonial-carousel`); the harness adds an "Other" free-text choice. See `references/clarify-protocol.md` Q1.
2. **Block strategy** — design has repeating units? Inline blocks vs theme blocks vs hardcode static. Skip if no blocks.
3. **Collection / product data source** — section displays collections/products? `collection_list` vs section blocks per collection vs single `collection` picker. Skip if no commerce data.
4. **Animation port scope** — design has scroll-triggered / parallax / per-character motion? Port full vs static-first vs skip. Skip if static.
5. **Snippet variant choice** — 2+ existing variants are plausible? Pick at audit-entry time. Skip if single obvious match (step C remains the new-variant ask).
6. **Color scheme default** — design is scheme-neutral or shows multiple variants? Skip if design clearly maps to one scheme.
7. **CSS strategy — SCSS-first vs XO-CSS-first** — **ALWAYS fire, NEVER skip** (per user policy 2026-05-26). Without an explicit per-port choice the codebase drifts into an inconsistent BEM/atomic mix. Fires on every section port AND every brand-new snippet — even a "clean" 0-question section still gets a single Q7 ask. Quote concrete numbers from the design SCSS audit (lines of layout/spacing/typography vs hover-chain/keyframes). On XO-CSS-first → also invoke `Skill(xo-css)` + `Skill(scss)` (tier-3 sidecar is inevitable); on SCSS-first → invoke `Skill(scss)`.
8. **Layout mechanism** — section renders **N≥3 homogeneous repeating items** as a grid / masonry / carousel / grid-hover-expand? Ask whether to adopt the **`layout` system** (`{% render 'layout' %}` + `...layoutSchemaSettings()` — recommended; merchant switches grid↔carousel↔masonry + columns/gap, like `product-list`) vs a **static grid primitive** (`<div xo-grid class="xo-grid-block">`, fixed grid) vs keep raw CSS (bespoke only). Skip when the suitable-case gate fails (bespoke/heterogeneous layout, single/2-item, or switching modes breaks meaning). **No `<xo-grid>` element — the grid is `<div xo-grid class="xo-grid-block">`.** See `references/grid-and-layout.md`.

Skip rule (applies to **Q2–Q6 and Q8** — Q1 and Q7 always fire):

```
COUNT = number of Q2–Q6 + Q8 whose answer is NOT obvious from context
COUNT == 0 → ask Q1 + Q7 (two questions, one AskUserQuestion call)
COUNT == 1 → batch Q1 + that question + Q7
COUNT >= 2 → batch Q1 + all triggered conditionals + Q7
AskUserQuestion holds ≤4 questions → with Q1 + Q7 always present, one call fits ≤2
  conditionals; if more, split into two calls (keep Q1 in the first)
COUNT >= 5 → design is too ambiguous; pause and ask freeform instead of batching
```

The minimum interview is now TWO questions (Q1 + Q7) — never one.

> [!IMPORTANT]
> **Q1 (name) and Q7 (CSS) never skip.** A clean section (`subscribe`, `manifesto`) reaches Step 2 having asked exactly two questions — Q1 + Q7. Do NOT collapse "COUNT(Q2–Q6, Q8) == 0" into "skip the whole protocol"; that is the historical bug that left CSS strategy un-asked (and now would skip the name confirmation too). See `references/clarify-protocol.md` § Q1 + Q7.

Never ask: CSS class names, schema setting order, internal variable names, validator invocation, wrapper choice, inline_richtext-vs-richtext (follow design), placeholder type, vertical spacing (wrapper handles it). Surface auto-decisions in the post-port preview so the user can catch silent wrong choices.

**Phrasing matters.** When a question fires, lead with the specific observation from the design (not `{N}` placeholders), name the ambiguity, recommend with reasoning, and surface the downstream consequence. A template-shaped question ("`{N}` units. Which block kind?") signals the agent didn't actually read the design.

→ See `references/clarify-protocol.md` for the full decision table, phrasing principles, example question wordings with observation + reasoning, worked examples (subscribe=1q Q7-only, hero-collage=4q, featured-products=4q), and anti-patterns.

### Step 2 — Reuse-first audit + variant audit

For each `<xo-component>` in the design, find the matching snippet in `src/snippets/`. For each `<xo-include>`, decide whether an existing `src/sections/` can be reused (often yes — the design "name" is editorial; the underlying pattern often exists generically).

> [!IMPORTANT]
> **Two-sided audit is mandatory.** Before declaring reuse: read design's `components/<X>/<X>.html` + `<X>.scss` AND project's `src/snippets/<X>/<X>.liquid` + `<X>.global.scss`. Compare visual archetypes (overlay vs caption-below, full-bleed vs padded, gradient vs solid, hover behaviors). Same NAME ≠ same RENDERING. If archetypes differ → cannot reuse as-is, must escalate ladder (A/B/C) or restyle.
>
> A reuse decision made from one side only is the most common porting bug — it produces output that compiles, validates, but visually does not match the design.

**Then — for every snippet you plan to render — run the variant audit:** list the snippet's variants (`*-1`, `*-2`, … under `src/snippets/<name>/`), trace which visual properties are hardcoded vs settings-driven, reason about which one matches the design's intent, pick the closest. This is a reasoning step, not a lookup — the variant set evolves, so always read the actual files at audit time.

If none match exactly, walk the escalation ladder:

| Step | Action                                                                                | When                                                                | Authority |
| ---- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | --------- |
| A    | Configure via theme settings (set the right value in `preset-N.js`)                   | A variant already reads the setting; just needs the right value     | Proceed   |
| B    | Modify the closest existing variant (`<snippet>-N.liquid` / `.global.scss`)           | Change is universally beneficial OR variant is currently inconsistent across themes | Proceed if no other shipped preset visually breaks; otherwise ask |
| C    | Add a new numbered variant + dispatcher + global-schema                               | A new visual archetype is genuinely needed AND modifying any existing variant breaks other presets | **STOP — ask the user.** Never silently create a new variant. |

The bulk of the porting effort is **selecting the right variant + passing the right params** (usually step A), NOT rebuilding snippets or adding section-scoped CSS hacks.

→ See **"Audit Snippet Variants BEFORE Rendering"** in `references/sections-to-liquid.md` for the worked example + anti-patterns.

### Step 3 — Section composition

For each design section that doesn't have a direct equivalent in `src/sections/`, create one that **composes existing snippets**.

**Before writing or editing any `.liquid` markup — invoke `Skill(liquid)`.** Not "if you're unsure" — that phrasing is exactly what failed, because the Liquid mistakes that bite are the ones you're *wrongly confident* about (e.g. `{% assign x = a != blank %}`, which compiles but never evaluates the comparison). A confidence gate can't catch a confident error. So treat this like Q7's scss/xo-css invocation: unconditional, up front. Its `references/{tags,filters,objects,blocks,idioms,gotchas}.md` carry the official syntax + project idioms. This is the *front gate*; `validate-liquid.py` (below) is the *back stop* — the gate prevents the whole class of Liquid errors, the validator only catches the specific rules it already encodes. Use both.

**After writing or editing `schema.js`**, run the source-side validator:

```bash
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/
```

Detects: disallowed `inline_richtext` tags, missing range bounds, undefined select options, step violations, unresolved block types, theme-store label hygiene.

**After writing or editing any `.liquid` markup**, run the Liquid validator:

```bash
python .claude/skills/design-to-liquid/scripts/validate-liquid.py src/sections/<name>/
```

Catches Liquid bugs the schema validator can't see — the `assign`-with-condition mistake (`{% assign x = a != blank %}` doesn't evaluate the comparison; `assign` takes a value, not a condition — `liquid` skill `gotchas.md` #31), and render arguments carrying an expression (`{% render 'x', label: 'a.b' | t %}`, `lazy: forloop.first == false` — an argument takes a bare value; `gotchas.md` #33, a hard compile error). This is a verification gate, not optional polish: it closes the loop on confident-but-wrong Liquid the same way `validate-schema.py` does for schema, rather than trusting that you remembered to consult the `liquid` skill.

> [!IMPORTANT]
> **Compile gotcha — blocks + snippets don't compile via `npm run build`.** The `vite-xotiny` plugin processes `src/blocks/` and `src/snippets/` only in `configureServer` (dev mode). To compile a new block/snippet without dev running, force-process via direct import:
>
> ```bash
> node --input-type=module -e "
> import { processBlocks } from '$(pwd)/node_modules/@xotiny-private/vite-xotiny/dist/plugins/blocks/processor.js';
> await processBlocks();
> "
> node --input-type=module -e "
> import { processSnippets } from '$(pwd)/node_modules/@xotiny-private/vite-xotiny/dist/plugins/snippets/processor.js';
> await processSnippets();
> "
> ```
>
> Sections compile via `npm run build` normally; only blocks + snippets have this quirk. Verify `shopify/blocks/<type>.liquid` and `shopify/snippets/<name>.liquid` exist before assuming compile succeeded.

→ See `references/sections-to-liquid.md` for the section pattern, the `liquid` skill for Liquid syntax.

### Step 4 — Lift hardcoded values to settings

Every hardcoded string / image / URL / number becomes a schema setting. Each setting's `default` is a generic **placeholder** (Shopify/Dawn convention — heading = section purpose, body = "what goes here", button = "Button label"), **not** the design's literal copy; the design's actual text is only the porting target, never persisted.

→ See `references/data-to-settings.md` § "Defaults are placeholders, not design copy".

### Step 5 — JSON page template

Write the JSON template at `src/pages/<template>/index.preset-N.json` referencing the new (and reused) sections with their settings/blocks.

→ See `references/pages-to-templates.md`.

### Step 6 — Restyling

For every reused snippet whose visual doesn't match the design out-of-the-box, restyle via:

- **SCSS** (BEM) for component-scoped styles — see `scss` skill
- **XO-CSS** atomic classes inline in liquid for utility tweaks — see `xo-css` skill
- Theme-level overrides under `body.<theme-class> { … }` if the design ships multiple themes

> [!NOTE]
> Resist editing the existing snippet's liquid markup unless absolutely required. Most visual differences are SCSS-only. Liquid changes mean future design swaps would need re-coding.

## Navigation — When to read which reference

- **Entry point — picker MCP / "which section to port?"** → `references/picker-protocol.md`
- **Step 0 — Mapping design tokens (colors / fonts / scale / radius / spacing) into theme settings** → `references/tokens-mapping.md`
- **Reading design documentation / blueprints** → `references/blueprint-protocol.md`
- **Step 1.5 — Clarify protocol (interview decision table + question templates)** → `references/clarify-protocol.md`
- **Layout / grid — the `layout` system (grid/carousel/masonry switch) vs static grid vs raw CSS (Q8)** → `references/grid-and-layout.md`
- **Building the JSON page template** → `references/pages-to-templates.md`
- **Creating a new liquid section that composes existing snippets** → `references/sections-to-liquid.md`
- **Porting a design header** (match the one `header` section via its `layout` setting — never a new section) → `references/header-port.md`
- **Porting a design footer** (same model, `footer` section + `footer-layout` snippets) → `references/footer-port.md`
- **Promoting hardcoded values to schema settings** → `references/data-to-settings.md`
- **Mapping Lucide icons / handling images** → `references/icons-and-images.md`
- **The rare case where a new snippet is genuinely needed** → `references/components-to-snippets.md`
- **Theme Store submission requirements (label hygiene, accessibility, copy rules)** → `references/theme-store-requirements.md`
- **Picker selection state** (which section is currently picked in xo-design) → `xo-design` MCP — `mcp__xo-design__get_selection` / `select_section` / `clear_selection`
- **xo-webcomponents API** (carousel, marquee, modal, animate, magnetic, etc.) → use the **`xo-components` MCP** server when available
- **Liquid syntax — tags / filters / objects / blocks / idioms / gotchas** → the `liquid` skill (self-contained, no external plugin needed)

## Where Things Live (Anchor Map)

| Where to look for                                              | Path                                              |
| -------------------------------------------------------------- | ------------------------------------------------- |
| Existing snippets                                              | `src/snippets/<name>/<name>/<name>.liquid`        |
| Snippet schemas (reusable settings)                            | `src/snippets/<name>/<name>/schema.js`            |
| Project's input-setting helpers (alignment, color, space, …)   | `src/snippets/_base/input-settings/`              |
| Icon snippets                                                  | `src/snippets/icons/icon-<name>.liquid`           |
| Existing sections                                              | `src/sections/<name>/<name>.liquid` + `schema.js` |
| Section groups (header / footer / popups / etc.)               | `src/groups/<group>/<name>/`                      |
| Header / footer layout snippets (one per `layout` value)       | `src/snippets/header-layout/`, `src/snippets/footer-layout/` |
| Page templates                                                 | `src/pages/<template>/*.json`                     |
| Layout shell                                                   | `src/layout/theme.liquid`                         |
| Theme global-schemas (Theme Editor inputs)                     | `src/config/global-schema/*.js`                   |
| Theme shipped defaults (per-shop)                              | `src/config/settings_data.js`                     |
| Settings → CSS variable adapters                               | `src/snippets/settings-adapter/*-adapter.liquid`  |
| Build-time tokens (xo-css generator source)                    | `theme-config/theme.config.json`                  |
| Schema builders                                                | `src/create-schema.js`, `src/schema.types.ts`     |

## When you finish

Before reporting "done", close the loop with project state:

1. **Update `.agent-state/PLAN.md`** — flip the row's status icon (⚪→🔵 while in progress, then 🔵→✅ on completion). Update the "Last refreshed" date in the header.
2. **Append `.agent-state/PROGRESS.md`** — add a new entry at the top per the `planner` skill's `progress-protocol.md`. Capture: Goal, Done (files touched), Decisions (anything non-obvious you chose), Open (what's pending or blocked for next session).
3. **Suggest the `/polish` finishing pass** — this port pass focuses on structure + schema + visual match, so a11y, scroll-reveal (`xo-animate`), and hover details often get partially applied or dropped. Before calling it fully done, tell the user they can run `/polish <this target>` to audit + apply accessibility fixes, `xo-animate` opportunities, and `xo-hover` interactions. It's a suggestion, not a gate — `polish` is a standalone skill the user opts into.
4. **Suggest the `/editor-qa` live test** — structure + visual match are verified statically here, but how the section behaves once it's actually in the Theme Editor (settings wiring through, blocks adding cleanly, the mobile breakpoint stacking right) only shows at runtime. Tell the user they can run `/editor-qa <this target>` to have the agent drive the real editor — add the section, exercise its settings/blocks, flip to mobile view, and screenshot both breakpoints against the design. **Hand it a one-line recipe of what to exercise** — you just built the section, so you know its block types and which settings matter most. e.g. "add an image block + a text block, set the heading and the desktop height". That lets editor-qa skip live discovery and go straight to the test (faster); it's optional, editor-qa works without it. Like `polish`, it's an opt-in suggestion, not a gate; it needs the Playwright extension connected to a logged-in editor tab (the `editor-qa` skill's setup notes cover the one-time wiring).
5. **Don't commit** — that's `/git`'s job. The user runs `/git` separately when they want to checkpoint.

If the state files don't exist, hand off to `planner`'s kickoff protocol first.

## Related Skills

- `planner` — project state docs (PLAN/PROGRESS/INVENTORY) — invoke at session start and when finishing
- `schema` — section / block / theme settings schemas
- `snippet` — authoring the `.liquid` body of a snippet
- `liquid-doc` — snippet doc comments
- `scss` — BaseHTML SCSS framework, BEM
- `xo-css` — atomic utility classes inside liquid
- `polish` — `/polish` finishing pass (a11y + xo-animate + xo-hover) on the just-ported target
- `editor-qa` — `/editor-qa` live-editor test pass (add section/blocks, exercise settings, desktop↔mobile) on the just-ported target
- `git` — `/git` scoped commit workflow when ready to checkpoint
