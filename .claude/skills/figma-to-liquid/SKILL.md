---
name: figma-to-liquid
argument-hint: "[section-or-snippet-name]"
description: "Use when porting a UI unit from a FIGMA design into this Shopify Liquid theme under src/ — building a `src/sections/<name>/` section OR a `src/snippets/<name>/` snippet from a Figma frame. SOURCE = Figma, read through the Figma **Dev Mode MCP** (`mcp__figma-dev-mode-mcp__*`): the user selects a frame/component in the Figma DESKTOP app, then runs `/figma-to-liquid`, and this skill reads the current selection (get_metadata → get_code → get_variable_defs → get_image), maps Figma primitives to project conventions, runs the naming + CSS-strategy interview, audits existing snippets before building, lifts literals to schema settings, and restyles with SCSS/XO-CSS. Trigger on: `/figma-to-liquid`, 'figma sang liquid', 'chuyển figma', 'port figma', 'từ figma tạo section/snippet', 'làm section này từ figma', 'phân tích figma', 'figma to liquid', 'build a section from figma', 'convert this figma frame', 'design figma này thành section'. DISAMBIGUATION: the source here is FIGMA (a live frame via Dev Mode MCP) — to port from the local `design/` folder of pre-built HTML+SCSS use `design-to-liquid` instead; this is NOT styling-only (that's `xo-css`/`scss`), and NOT for dropping an already-built xo-* component into markup. Reuses the `liquid`/`snippet`/`schema`/`scss`/`xo-css`/`liquid-doc` sub-skills and the project schema/liquid validators."
---

# Figma → Liquid

Pipeline skill for porting a Figma frame into this Shopify Liquid theme as a **section** (`src/sections/<name>/`) or a **snippet** (`src/snippets/<name>/`).

It is the Figma-sourced sibling of `design-to-liquid`. The **downstream is the same project** — section wrapper, snippet-variant audit, schema settings, SCSS/XO-CSS, validators — but the **source analysis is different**: instead of reading pre-built `design/` HTML+SCSS files, you read a live Figma node tree + variables through the **Figma Dev Mode MCP**. This skill owns that Figma front-end and is otherwise self-contained.

## Core assumption — don't recreate what exists

> [!IMPORTANT]
> **`src/snippets/` is stable.** Button, product-card, article-card, icon, image, card primitives, header pieces — most already exist. Porting a Figma frame usually means: identify the primitives it's made of → find the matching snippets → compose a section that `{% render %}`s them → restyle so they match the Figma visual. Creating a brand-new snippet is the **exception**. Before building any primitive, search `src/snippets/` first (Step 2).

## Two layers of authority — project conventions + Shopify-native

> [!IMPORTANT]
> Consult BOTH before writing any non-trivial Liquid:
> 1. **Project layer** (`src/`) — read before writing schema/markup: `src/create-schema.js` (`createSectionSchema`/`createBlockSchema`/`createSchemaSettings`), `src/snippets/_base/section/schema.js` (`sectionSchemaSettings(...)` — the chrome: `color_scheme`/`width`/`height`/padding/borders/decoration), `src/snippets/_base/input-settings/` (reusable input groups), `src/config/global-schema/*.js` (valid setting ids), and 1-2 existing `src/sections/*/` of similar shape.
> 2. **Shopify-native layer** — authoritative Liquid syntax. Invoke `Skill(liquid)` (its `references/{tags,filters,objects,blocks,idioms,gotchas}.md`).
>
> Project source diverges from native Shopify in three spots (build bridges): schema in `schema.js` → compiled `{% schema %}`; per-component CSS in `<name>.global.scss` → compiled via scss-glob; doc-blocks via `{% comment %}`.

## Requires the Figma Dev Mode MCP

Server id `figma-dev-mode-mcp` (SSE `http://127.0.0.1:3845/sse`), tools called as `mcp__figma-dev-mode-mcp__<tool>`. It is **first-party** and reads the **current selection in the Figma DESKTOP app** — so it needs: the Figma desktop app open, "Dev Mode MCP Server" enabled (Preferences), a Dev/Full seat, and a frame selected. If the tools are unreachable, **STOP and tell the user** to open the desktop app, enable the server, and select a frame — never guess at design you can't read.

Tools (verify the exact names available in your session — the server evolves):

| Tool | Returns | Use for |
| --- | --- | --- |
| `get_metadata` | compact node-tree map (ids, names, types, x/y/w/h) | **first** on a big frame → the structure, then drill by `nodeId` |
| `get_code` | generated framework-ish code of the node | **structure/hierarchy HINT ONLY — never paste** (see gotcha below) |
| `get_variable_defs` | Figma variables the selection uses (color/space/type/radius) | Step 0 token mapping |
| `get_image` | rendered PNG of the selection | the **visual ground-truth** to check the finished Liquid against |
| `get_code_connect_map` | Figma component ↔ codebase symbol (if Code Connect set up) | check once; usually absent — don't depend on it |

> [!IMPORTANT]
> **`get_code` is a structure hint, not code to paste.** It emits generic React/HTML-ish markup that knows nothing about this project — no `{% render 'section' %}` wrapper, no snippets, no `schema.js`, no `<xo-container>`, no XO-CSS, no Liquid. Read it to understand the *hierarchy and nesting*, then author project-convention Liquid by hand. Pasting `get_code` output is the #1 failure mode for this skill.

## Before you start — read project state

> [!IMPORTANT]
> This skill is the executor (HOW). The `planner` skill owns WHAT's planned and where we are. Skip if a `planner` invocation already happened this conversation; otherwise read `.agent-state/PROGRESS.md` (top 1-2 entries) + `.agent-state/PLAN.md` (the row for this work), and hand off to `planner` if state is missing/stale.

## Entry — read the selection

```
on /figma-to-liquid …:
  1. If the user named a unit ("/figma-to-liquid hero"): use that name, still analyze the current selection for its content.
  2. Read the current Figma selection:
       • get_metadata()        → the node-tree map (start here for anything non-trivial)
       • get_image()           → visual ground-truth (keep for the final compare)
       • get_variable_defs()   → tokens (feeds Step 0)
       • get_code(nodeId?)     → hierarchy hint only (drill into sub-nodes as needed)
  3. MCP unreachable / empty selection → STOP: ask the user to open Figma desktop,
     enable the Dev Mode MCP Server, and select a frame. Do not fabricate structure.
```

## Authoring workflow

### Step 0 — Map Figma variables → theme tokens (once per design)

> [!IMPORTANT]
> Map the design's foundation — colors, fonts, type scale, radius, spacing — into theme settings BEFORE porting a unit. Inlining hex/font strings per section is the most common porting mistake. Once tokens are mapped, every ported unit inherits them via CSS variables (`color(primary)`, `var(--font-heading-1-size)`, `bdrs:…`).

Read `get_variable_defs`, then map into `src/config/presets/preset-N.js` + `theme-config/theme.config.json` (edit the existing preset slot — **never create a new preset file**; keep `settings_data.js` shape stable). → `references/tokens-mapping.md`.

### Step 1 — Analyze the frame

Decode the selection into project primitives — this is the Figma-specific heart of the skill. → `references/figma-analysis.md` (the mapping table: auto-layout → flex/`<xo-container>`/grid, constraints → responsive intent, text layers → type-scale tokens, fills/strokes → **color tokens not hex**, radius → `bdrs`, effects → SCSS, component instances → candidate snippets, vectors → icon snippet, raster fills → image snippet).

**Decide SECTION vs SNIPPET here:** a full-width page composition → a `src/sections/<name>/` section; a self-contained reusable primitive (a card, a badge, a callout) → a `src/snippets/<name>/` snippet. When ambiguous, fold it into Q1.

> [!NOTE]
> Flag a **layout-able collection** (N≥3 homogeneous items in a Figma auto-layout grid / wrap) → triggers clarify Q-Layout. Flag a **collection-tabs** signature (tab row above a product grid) → its own handling. Don't copy raw grid geometry verbatim.

### Step 1.5 — Clarify protocol

Batched interview — surface only genuinely ambiguous architectural choices. **Q1 (name) and Q7 (CSS strategy) ALWAYS fire**; the rest obey the skip rule. Phrase every question from the **actual Figma observation** (frame name, layer counts, auto-layout specifics), never a template. → `references/clarify-protocol.md`.

- On **XO-CSS-first** → invoke `Skill(xo-css)` **and** `Skill(scss)` (tier-3 sidecar is inevitable). On **SCSS-first** → invoke `Skill(scss)`.

### Step 2 — Reuse-first / snippet-variant audit

For each primitive the frame is made of, find the matching `src/snippets/<name>/`. List its numbered variants (`*-1`, `*-2`, …), trace hardcoded vs settings-driven, pick the closest. Escalate only when needed:

| Step | Action | When |
| ---- | ------ | ---- |
| A | Configure via theme settings (right value in `preset-N.js`) | a variant already reads the setting |
| B | Modify the closest existing variant | change is universally beneficial / variant inconsistent |
| C | **New numbered variant + dispatcher + global-schema** | genuinely new archetype AND modifying any variant breaks other presets — **STOP, ask the user** |

The bulk of the work is selecting the right variant + passing the right params (usually A), NOT rebuilding snippets or hacking section-scoped CSS. → `references/sections-and-snippets.md`.

### Step 3 — Compose the section / snippet

**Invoke `Skill(liquid)` BEFORE writing any `.liquid` markup** — unconditional front gate, not "if unsure" (the Liquid mistakes that bite are the ones you're wrongly confident about, e.g. `{% assign x = a != blank %}`).

- **Section** — use the project wrapper, never hand-write `<section>` + container + padding:
  ```liquid
  {%- capture content -%}
    …inner markup, composing snippets via {% render %}…
  {%- endcapture -%}
  {% render 'section', content: content %}
  ```
  Schema: `createSectionSchema({ name, class, settings: [ ...sectionSchemaSettings({}), … ], blocks, presets })`.
- **Snippet** — follow `Skill(snippet)` shapes (pure-param / context+schema / dispatched variant) + `Skill(liquid-doc)` for the `{% comment %} @param … %}` doc-block.

Verify `Category.Section.X` / `Category.Block.X` against `src/constants.js` before referencing (`Section.Products` is plural, `Block.Product` singular).

### Step 4 — Lift literals to schema settings

Every literal string / image / URL / number / color from the Figma frame becomes a schema setting via `Skill(schema)`.

> [!NOTE]
> **Figma has no "hardcoded vs dynamic" concept** — every value is literal. YOU decide what a merchant should be able to edit (headings, body copy, images, links, CTA labels, counts) vs what's structural. Each setting's `default` is a generic **placeholder** (Dawn convention — heading = section purpose, body = "what goes here", button = "Button label"), **never** the Figma literal copy.

Richtext-wrapper rule (per AGENT.md): a `richtext` field's wrapper element must be `<div>`, **never `<p>`** (richtext emits its own `<p>` → invalid nesting), and carries the `rte` class. `inline_richtext` may use `<p>`/`<h2>`. Run `validate-schema.py` after each `schema.js` edit (below).

### Step 5 — Restyle to match the Figma visual

Per the Q7 answer, author **SCSS** (BEM `.xo-<name>__el--mod`, `color()`/`fz()`/`media('>md')`) or **XO-CSS** atomic classes inline. Figma fills/strokes/effects → **theme tokens, never inlined hex**. Compare the rendered result against the `get_image` PNG. Resist editing an existing snippet's `.liquid` — most visual gaps are SCSS-only.

## Validators (run after edits — project tooling)

```bash
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/   # after schema.js
python .claude/skills/design-to-liquid/scripts/validate-liquid.py src/sections/<name>/    # after .liquid
```

These are shared project validators (AGENT.md § Validators). `validate-schema.py` catches disallowed `inline_richtext` tags, missing range bounds, undefined select options, label hygiene; `validate-liquid.py` catches runtime-silent Liquid bugs (`assign`-with-condition). The `liquid` skill is the front gate; the validators are the back stop — use both.

> [!IMPORTANT]
> **Blocks + snippets don't compile via `npm run build`** (the plugin processes them only in dev `configureServer`). Force-process via direct import — see `design-to-liquid` SKILL.md § "Compile gotcha" for the exact `processBlocks()`/`processSnippets()` snippet. Sections compile via `npm run build` normally.

## When you finish

1. **Update `.agent-state/PLAN.md`** — flip the row's status icon (⚪→🔵→✅), update "Last refreshed".
2. **Append `.agent-state/PROGRESS.md`** — new top entry (Goal / Done / Decisions / Open) per `planner`'s `progress-protocol.md`. Hand to `planner` if state files are missing.
3. **Suggest `/polish`** — this pass focuses on structure + schema + visual match; a11y, `xo-animate` scroll-reveal, and `xo-hover` often get dropped.
4. **Suggest `/editor-qa`** — hand it a one-line recipe (block types + key settings) to exercise the unit live and check desktop↔mobile against the Figma frame.
5. **Don't commit** — that's `/git`'s job.

## References — when to read which

- **Reading the Figma selection + mapping primitives → project primitives** → `references/figma-analysis.md`
- **Step 0 — Figma variables → theme tokens** → `references/tokens-mapping.md`
- **Step 1.5 — the interview (decision table, phrasing, worked examples)** → `references/clarify-protocol.md`
- **Composing the section/snippet, the variant audit, lifting to settings** → `references/sections-and-snippets.md`

## Related skills

- `liquid` — Liquid syntax (front gate before any markup) · `snippet` — snippet bodies · `liquid-doc` — snippet doc-blocks · `schema` — schema.js · `scss` / `xo-css` — styling (per Q7) · `motion` — wiring xo-animate/xo-parallax when porting motion (Q-Animation = port full) · `planner` — state docs · `polish` — finishing pass · `editor-qa` — live test · `git` — commit · `design-to-liquid` — the `design/`-folder sibling (different source).
