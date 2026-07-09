# Shopify theme (design-to-liquid port)

This project ports HTML designs from `design/` into a Liquid Shopify theme under `src/`. The work is large and spans multiple sessions, so the `.claude/` system is built around **persistent project memory** + **role-specialized skills**.

## Communication language

**Mirror the user's language.** Reply, ask questions, summarise, and explain in whichever language the user is writing — English in, English out; Vietnamese in, Vietnamese out. Same applies to `AskUserQuestion` prompts.

If the user switches mid-conversation, switch with them. If a single message mixes languages, follow the dominant one (the language carrying the actual request, not loanwords).

What stays in English regardless of the conversation language:

- Code, file paths, identifiers, command names (`/git`, `/design-to-liquid`, `mcp__xo-design__get_selection`)
- Commit messages (Conventional Commit format is English-only by project convention)
- File contents authored by the agent — `PLAN.md`, `PROGRESS.md`, schema labels, snippet docs, SCSS comments, section liquid — all stay English so the codebase reads consistently for any future contributor
- Error / warning text from validators and tools (echoed verbatim)

So the rule is: **chat in the user's language, write code/state in English.**

## Working philosophy

Four principles to follow on every change. Adapted from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on common LLM coding pitfalls. **Bias toward caution over speed** — for trivial tasks, use judgment.

### 1. Think before coding

Surface assumptions; don't pick silently.

- If something is unclear, stop and name what's confusing.
- If multiple interpretations exist, present them — don't choose for the user.
- If a simpler approach exists, say so. Push back when warranted.

> Here: before creating a new snippet variant (audit step C in `design-to-liquid` skill), always ask the user. Same for any change that ripples into the theme-settings UI or other shipped presets.

### 2. Simplicity first

Minimum code that solves the asked problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" / "configurability" that wasn't requested.
- No error handling for scenarios that can't happen.
- If you wrote 100 lines and it could be 30, rewrite it.

> Here: prefer configuring existing snippets via theme settings (audit step A) over writing section-scoped CSS overrides. Don't add settings the design doesn't actually need.

### 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it silently.

> Here: resist editing snippet `.liquid` markup unless absolutely necessary. SCSS + settings cascades almost always reach the design. When fixing a bug, fix the bug — don't also "tidy up" the surrounding file.

### 4. Goal-driven execution

Define verifiable success criteria. Loop until verified.

- "Port section X" → render X with **validator passing + visual match in editor**.
- "Fix the preset error" → reload editor, error gone, preview works.
- Vague goals ("make it work") trigger constant clarification — replace them with checks.

> Here: every `schema.js` edit → run the validator (`validate-schema.py`). Every preset change → reload Theme Editor and confirm no errors. Visual verification → playwright MCP screenshots.

## When starting a new conversation — read state first

The `planner` skill maintains three state documents that survive across sessions. Before doing anything else, read them in this order — **read with bounded `limit` parameters**, never the whole file:

1. **`.agent-state/PROGRESS.md`** — newest-first append-only changelog. The file's TOP has a "Session summary" table giving 1-line orientation per session — read that table + the latest 1-2 verbose entries. Concretely: `Read(PROGRESS.md, limit: 100)` gives table + most recent session. Do NOT read the whole file at session start — older entries are archaeology, only grep when investigating a specific past decision.
2. **`.agent-state/PLAN.md`** — the priority queue of pending work and the blockers. Look at status icons (⚪ pending · 🔵 in progress · ✅ done · ⏸ paused · ❓ needs decision). Usually <120 lines — safe to read whole.
3. **`.agent-state/INVENTORY.md`** — live coverage scan of `design/` vs `src/sections/`. If stale (more than ~3 sessions behind PROGRESS), refresh:
   ```bash
   python .claude/skills/planner/scripts/scan-inventory.py
   ```

Then announce status to the user: what the previous session did, what's open, what to do next.

The `planner` skill's `resumption-protocol.md` reference describes this in full.

### State-doc scope (what goes in / what doesn't)

`.agent-state/` files track **`src/` Liquid theme work only** — section ports, snippet variants, schema fixes, preset values, page templates, blocks, design-token mappings, JSON template wiring.

**Do NOT log in `.agent-state/`:**

- `.claude/` system updates — skill description edits, AGENT.md changes, new hook files, reference doc additions, clarify-protocol edits, validator script changes.
- Build pipeline / `theme-config/` tweaks unrelated to a specific section port.
- README / docs-only changes.

System-level changes leave a trace in **git commit history** (use `/git` with scope `.claude` / `.claude/<skill>` / `agent-state` etc.). That's the system changelog — don't duplicate into PROGRESS.

Why: PROGRESS is the next-agent's read-on-start orientation for "where are we in the theme port?". System updates that don't move the port forward are noise at session start.

### State-doc growth policy

**PROGRESS.md active file capped at ~500 lines.** When the next planner-skill append would cross 500:

1. Pick the oldest 2-3 sessions still in the file.
2. Cut them into `.agent-state/archive/PROGRESS-<YYYY-Q>.md` (preserve full verbose entry).
3. Update the "Session summary" table at the top of `PROGRESS.md` — keep the row, append `(archived → archive/PROGRESS-YYYY-Q1.md)` to the Status column.
4. Result: active `PROGRESS.md` stays roughly 300-500 lines no matter how long the project runs. Archive holds the rest.

**Never compact in place** (rewriting older entries into shorter forms) — that's lossy. The archive preserves full text; the table in active file gives O(1) glance orientation.

`PLAN.md` and `INVENTORY.md` are rewritten in-place each session — no archive needed.

## Skill catalog

| Skill                | Role                                                                                                |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| **`planner`**          | WHAT to do + STATUS. Owns PLAN.md / PROGRESS.md / INVENTORY.md. Use at session start and for planning. |
| **`design-to-liquid`** | HOW to port a section. Entry: check `xo-design` MCP picker for the section the user pointed at (`mcp__xo-design__get_selection`); fall through to manual survey if no selection. Then Step 0 (tokens) → Step 1 (survey) → Step 2 (variant audit) → … → Step 6 (restyle). Use during actual porting work. Suggests `/polish` at completion. |
| `design-sync`          | `/design-sync` — bridge for when the `design/` repo (separate git clone, versioned via `design/package.json`) is pulled forward. Diffs current design HEAD vs the last synced baseline in `.agent-state/DESIGN-SYNC.md`, buckets changes by severity, resolves which already-ported units need re-sync vs net-new backlog, proposes batches handed off to `design-to-liquid`. Auto-appends net-new sections to the PLAN.md backlog (deduped) so they're never lost. Advances the baseline ledger only on user confirmation. |
| `polish`               | `/polish <target>` — finishing-pass QA after a section/snippet/page/theme is ported. Audits 3 dimensions (a11y · `xo-animate` scroll-reveal · `xo-hover` interaction), proposes a grouped checklist with exact markup, applies only user-selected items. Standalone OR via design-to-liquid's completion handoff. Bundles `scan-target.py` detector. |
| `editor-qa`            | `/editor-qa <target>` — **live**-editor QA pass. Drives the real Shopify Theme Editor (merchant's logged-in session, via Playwright **extension-mode** MCP) to exercise a just-ported section/block: add section, add blocks, set fields, scroll, toggle **desktop↔mobile** (`⌘⌃M`) for responsive, screenshot both vs `design/`. Never Saves without asking. Requires the Playwright Extension connected to a logged-in editor tab (`references/setup.md`). Standalone OR via design-to-liquid's completion handoff. Bundles `grep-refs.py`. |
| `lighthouse-audit`     | `/lighthouse-audit <storefront-url>` — read-only **stateless** Lighthouse score radar. Runs `npx lighthouse` (mobile + desktop) against a storefront URL the user supplies (NOT the admin `/editor` URL), reports all 4 category scores + Core Web Vitals (LCP/CLS/TBT/FCP/SI) PASS/FAIL vs a 90+ bar, then **hands off** failing audits — a11y → `polish`, image/markup perf → `design-to-liquid`, app/platform perf + SEO/Best-Practices → flag only. Splits app-script noise from theme-owned issues. Changes nothing; reports land in gitignorable `.lighthouse/`. Bundles `run-lighthouse.sh` + `parse-report.py`. |
| **`snippet`**          | Authoring the `.liquid` body of a snippet — pure / schema (context) / variant (dispatcher + numbered) shapes, the `{% liquid %}` prelude conventions, conditional wrappers, complex class composition, nested render. |
| **`liquid`**           | Liquid language reference — tags, filters, objects/drops, blocks, project idioms, gotchas. Self-contained; material distilled from shopify.dev/docs/api/liquid via context7. |
| `schema`               | Authoring section/block/global schemas via `createSectionSchema` / `createGlobalSchema` / `createSchemaSettings`. |
| `scss`                 | BaseHTML SCSS framework (`color()`, `fz()`, `media('>md')`, `<xo-container>`, `<xo-grid>`, BEM).     |
| `xo-css`               | XO-CSS atomic class syntax (`p:1rem`, `c:primary|h`, `d:none@md`).                                    |
| `liquid-doc`           | Liquid doc-comment `{% comment %} @param … %}` format at the top of every snippet.                  |
| **`git`**              | `/git` — scoped commit workflow. Scans dirty files, groups by scope (skill / section / snippet / config / state / root), drafts Conventional-Commit message, light pre-commit gates, commits ONE scope per invocation after preview. Never pushes or amends. |
| `extract-icon`         | Sync Lucide SVG content into `src/snippets/icons/icon-*.liquid` from `unpkg.com/lucide-static@latest`. Triggered by "update icons", "sync icons", "lucide → snippet". |
| `system-upgrade`       | Check, evaluate + **upgrade** the `.claude/` system (skills, AGENT.md, hooks, MCP, validators) + Shopify-platform drift. Distribution-repo aware. **Skill-targeted changes are delegated to `skill-creator`.** Triggered by `/system-upgrade`, `/system-audit`, "kiểm tra hệ thống", "nâng cấp hệ thống", "check .claude". |
| `shopify-watch`        | `/shopify-watch` — read-only **radar** for what's NEW in Shopify relevant to **theme** dev (changelog / Editions / themes-Liquid docs / Dawn-Horizon releases). Filters out app/Functions/extension-runtime news (THEME-not-APP), cites a source URL + date per item, emits a grouped digest, then **hands actionable items to `/system-upgrade`**. Stateless (asks for a "since" anchor), edits nothing. Triggered by "Shopify có gì mới", "Shopify changelog", "Editions mới", "what's new in Shopify themes". |

## Validators

**After every `schema.js` or preset edit** — run the schema validator:

```bash
# Validate a section schema.js after writing it
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/

# Sweep everything
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all
```

Catches: disallowed `inline_richtext` tags (e.g. `<br>`), missing range bounds, undefined select options, step violations, unresolved block types, theme-settings `current` as string, orphan color schemes.

Also surfaces Theme Store label/copy warnings (missing labels, British spelling, banned phrases like `CTA`/`X position`/`homepage`/`slider`/`sub-heading`, `&` or `?` in labels). Run with `--strict` to escalate warnings to errors. See `.claude/skills/design-to-liquid/references/theme-store-requirements.md`.

**After every `.liquid` markup edit** — run the Liquid validator:

```bash
# Validate one section / dir of liquid after writing it
python .claude/skills/design-to-liquid/scripts/validate-liquid.py src/sections/<name>/

# Sweep everything
python .claude/skills/design-to-liquid/scripts/validate-liquid.py --all
```

Catches runtime-silent Liquid bugs that don't show up in schema validation — currently the `assign`-with-condition mistake (`{% assign x = a != blank %}` doesn't evaluate the comparison; `assign` takes a value, not a condition — see `liquid` skill `gotchas.md` #31). The rule set is intentionally small and grows as new bug classes surface.

## Key conventions

### Theme tokens (Step 0 — done once per design)

- All theme tokens (colors, fonts, type scale, radius, spacing) live in `src/config/presets/preset-N.js`.
- **Edit the existing slot** (`preset-1.js`, `preset-2.js`, …); do NOT create new preset files like `preset-folio.js`.
- `src/config/settings_data.js` must have `current` as a full object (clone of the active preset), NOT a string preset name — Theme Editor preview rejects the string form.

### Section file layout

```
src/sections/<name>/
├── <name>.liquid          # markup (uses {% render 'section', content %} wrapper)
├── <name>.global.scss     # scoped styles (scss-glob auto-imports *.global.scss)
└── schema.js              # createSectionSchema + spread ...sectionSchemaSettings({...})
```

The section liquid uses the project wrapper, never hand-writes `<section>` + `<xo-container>` + padding:

```liquid
{%- capture content -%}
  …inner markup…
{%- endcapture -%}

{% render 'section', content: content %}
```

### Snippet variant audit (before rendering)

Before `{% render 'X', … %}` in a new section: list `src/snippets/X/` variants, trace what's hardcoded vs settings-driven, pick the closest. If none match, escalate (A: theme setting → B: modify variant → **C: NEW variant — ask the user first**). See `design-to-liquid/references/sections-to-liquid.md` "Audit Snippet Variants BEFORE Rendering".

### Theme blocks are OFF by default (2026-05-26 policy)

This project deliberately leans on **sections + snippets + inline blocks**, not theme blocks (`src/blocks/<group>/<name>/`). When porting a design that has repeating units:

1. **Default to inline blocks** (declared in the section's `schema.js`, scoped to the section).
2. **Use a snippet** if the unit is a reusable presentation primitive (image, button, card).
3. **Hardcode** if merchant flexibility isn't needed.
4. **Theme block** ONLY when the user explicitly says "use a theme block" / "make this a reusable block" / similar.

When walking clarify-protocol Q2 (block strategy), present a 2-option choice (Inline blocks / Hardcode static) by default. Only present the 3-option form (with Theme blocks) when user has opted in. Reasoning: theme blocks add a separate schema/preset/file trio, ripple into the editor's "block picker", and are usually overkill for one-off section needs.

### Header / Footer / Popups / Announcement-bar — override, do NOT create new (2026-05-28 policy)

These live under `src/groups/<group>/<name>/`, NOT `src/sections/`. They are **shared theme infrastructure** that ships with rich schema + markup. Default port = **OVERRIDE in place**, not file replacement.

Targets (already exist — DO NOT create siblings):

| Surface | Path | xo-modal name (if applicable) |
| --- | --- | --- |
| Header | `src/groups/headers/header/` | — |
| Mega menu | `src/groups/headers/mega-menu/` | — (uses `<template xo-mega-menu-name>` dispatch — see `references/mega-menu.md`) |
| Announcement bar | `src/groups/headers/announcement-bar/` | — |
| Predictive search (search modal) | `src/groups/headers/main-predictive-search/` | `search` |
| Footer | `src/groups/footers/footer/` | — |
| Cart mini (drawer/notification) | `src/groups/overlay/xo-cart-mini/` | `cart` |
| Quick view | `src/groups/overlay/quick-view/` | (verify per use) |
| Product compare modal | `src/groups/overlay/product-compare-modal/` | (verify per use) |
| Age verification popup | `src/groups/popups/popup-age-verification/` | (auto-open) |
| Promo popup | `src/groups/popups/popup-promo/` | (auto-open) |
| Countdown promo popup | `src/groups/popups/popup-countdown-promo/` | (auto-open) |
| Sign-up popup | `src/groups/popups/popup-sign-up/` | (auto-open) |
| Feature group (above-footer) | `src/groups/features/*/` | — |

**Naming exception:** `main-predictive-search` lives in `src/groups/headers/` (not `overlay/`) because Shopify section groups bucket it as a header sibling. Architecturally it's a modal.

**Port ladder for groups (different from snippet-variant ladder):**

| Step | Action | When |
|---|---|---|
| A | Tweak default settings in `<group>-group.json` | Existing schema's defaults don't match design (logo position, sticky direction, color scheme, action toggles) |
| B | Restyle SCSS in place (`<name>.global.scss`) | Visual aesthetic (typography, color, spacing, decorative shape) doesn't match — most common case |
| C | Add ONE new schema setting in `<name>/schema.js` + read in liquid | Design needs a behavior toggle that has no existing setting |
| D | **STOP — ask user** before editing `<name>.liquid` markup or creating new file | Markup changes ripple to every theme instance; file creation breaks the "override" assumption |

Sub-brand variants (`header-pet`, `header-sound`, `header-parfum`, `header-kids`, etc.) → `body.theme-*` SCSS cascade inside the SAME `<name>.global.scss`, NEVER a new `src/groups/headers/header-pet/` folder.

**Only create a new file** when the user explicitly says "make a new header" / "second header variant" / equivalent in their own language.

**References:**
- `.claude/skills/design-to-liquid/references/mega-menu.md` — mega-menu dispatch (`<template xo-mega-menu-name xo-mega-menu-index>` ↔ `<xo-mega-menu xo-name xo-index>` matching)
- `.claude/skills/design-to-liquid/references/modals.md` — modal architecture for any group containing `<xo-modal>` (search overlay, cart drawer, popups, quick-view, compare). Covers TRIGGER ↔ MODAL pairing, modal-content snippet API, predictive-search dispatch, cart-mini dispatch, port ladder extension for modal-shaped groups (always scope SCSS via `xo-modal[xo-name="X"]` to avoid cross-modal leak)
- `.claude/skills/design-to-liquid/references/sections-to-liquid.md` § "Scope-style mirror rules" — 3 guidelines when Group port ladder Step B scope-styles a section to mimic an existing snippet's visual: (1) never override CSS properties driven by snippet schema settings (audit `var(--X)` references first), (2) breathing space lives on parent container as `padding-top`, never on child as `margin-top`, (3) hover/active/focus state values must mirror the equivalent primitive's variant SCSS exactly to avoid side-by-side inconsistency. With worked examples from the Folio header port.

### Verify `Category` enum before referencing in schema/preset

The project's `Category` enum (in `src/constants.js`) is the authoritative list of section/block categories. **Read it before writing `category: Category.Section.X` or `category: Category.Block.X`** — misnaming the leaf (e.g. `Products` vs `Product`) compiles but produces a wrong category in the Theme Editor's section picker. Current shape:

```js
Category.Section = { Basic, Header, Banners, Collections, Products, Carts, Blog, Forms, Storytelling, Footer, Layout }
Category.Block   = { Basic, Product, Article, Collection, Cart, Layout, Links, Forms, Header, Footer, Custom }
```

Notice: `Section.Products` is plural; `Block.Product` is singular. Schemas commonly trip on this.

### Verify tokens against source-of-truth BEFORE referencing (do not invent)

This project has had repeated mistakes where the agent invented identifiers that don't exist:
- `color(layer-2)` (not in `theme.config.json` colors map — use `color(layer)`)
- `Category.Section.Product` (singular doesn't exist — use `Products`)
- `fz:body|1.4` (the `|` is pseudo separator, not multiplier — use atomic `fz:sN` body-size token)
- `p:2rem p:2.4rem` (duplicate property; multi-value padding needs direction shortcuts `py:`/`px:`)
- `grid-row:1` as class (not an atomic shortcut — use `grs:1`)
- `bdt:s1 bds:solid bdc:border` (redundant; `css.border.s1 = "0.1rem solid"` already includes the style — drop the `bds:solid`. See xo-css basics § "Common Mistakes" #8)

The pattern: assuming a name exists or a syntax works without checking. Before writing any token / enum / shortcut, **grep or read the source file**:

| Reference type | Source of truth |
|----------------|----------------|
| Color name in `color(X)` or `c:X` / `bgc:X` / `bdc:X` | `theme-config/theme.config.json` → `css.colors` |
| Space — write as direct rem (e.g. `p:1rem`, `gp:0.6rem`) | NO token map — `space` removed 2026-05. Same direction as `bodySizes`. |
| Body font-size — write as direct rem (e.g. `fz:1.4rem`) | NO token map — `bodySizes` removed 2026-05. Tokenize via `headingSizes` only. |
| Heading font-size token `fz:hN` / `fz:dN` | `theme-config/theme.config.json` → `css.headingSizes` |
| Font family `ff:X` | `theme-config/theme.config.json` → `css.fonts` |
| Border radius `bdrs:X` | `theme-config/theme.config.json` → `css.borderRadius` |
| Border shorthand `bd:sN` / `bdt:sN` / `bdr:sN` / `bdb:sN` / `bdl:sN` | `theme-config/theme.config.json` → `css.border` — values are **full shorthand** (`"0.1rem solid"`), so don't add `bds:solid` alongside; only use `bds:dashed`/`bds:dotted` to OVERRIDE the baked-in style |
| Atomic property shortcut (`p`, `gtc`, `bdrs`, …) | `.claude/skills/xo-css/references/properties.md` |
| Atomic pseudo shortcut (`h`, `f`, `w`, `gh`, …) | `.claude/skills/xo-css/references/pseudo.md` |
| `Category.Section.X` / `Category.Block.X` | `src/constants.js` |
| Snippet `{% render 'X' %}` param names | The snippet's `{% comment %}` doc block at top of file |
| Section schema setting `id` collision | Run `python .claude/skills/design-to-liquid/scripts/validate-schema.py <section-dir>` after every edit |

If you can't verify it in 1-2 seconds, **don't write it.** Making things up by feel costs more re-author time than a 5-second grep.

### Italic-emphasis pattern

Headings can wrap a single sensorial word in `<em>` to flip to the subheading font (Source Serif 4 italic for Folio). Implemented globally in `src/styles/base/content.scss` — section SCSS does NOT repeat the rule.

`inline_richtext` settings only accept inline tags (`em`, `strong`, `b`, `i`, `u`, `a`, `span`, `sup`, `sub`). For line breaks or paragraphs, use `richtext` (top-level `<p>`/`<ul>`/`<ol>`/`<h1>-<h6>`) — never `<br>`.

### `rte` wrapper class on richtext output

Any Liquid tag that **outputs a `richtext` or `inline_richtext` schema field** must carry the `rte` class on the wrapper, alongside its BEM class:

```liquid
<div class="xo-xxx__text rte">{{ section.settings.text }}</div>
<h2 class="xo-xxx__heading rte">{{ section.settings.heading }}</h2>
```

The styling already ships globally — `.rte { … }` in `src/styles/base/content.scss` (heading/paragraph/list spacing) and `src/snippets/_base/text/text.global.scss` exempts `.rte` from font-size normalization. The class is what tells the cascade "this is editor-authored rich text", so the spacing rules apply. Omitting it leaves richtext rendering unstyled. Applies to both `section.settings.*` and `block.settings.*`; plain `text`/`url`/`image` settings do NOT get `rte`.

**Wrapper element for a `richtext` field must be `<div>` — never `<p>` (nor a bare `<h1>-<h6>`).** A `richtext` field already outputs its own block-level tags (`<p>`, `<ul>`, `<h1>-<h6>`), so wrapping it in a `<p>` produces `<p><p>…</p></p>` — invalid nesting the browser silently auto-closes, detaching the class/styling from the content and breaking layout. This bites during ports: the design element is often a `<p class="lead">…`, and the reflex is to keep the `<p>` and just add `rte` — don't; swap it to `<div class="… rte">`. The `<h2>` in the example above is only safe because `heading` is an **`inline_richtext`** field (inline tags only, no block wrapper) — for `inline_richtext` a `<p>`/`<h2>` wrapper is fine. Rule of thumb: `richtext` → `<div>`; `inline_richtext` → any element. See `liquid` skill `references/gotchas.md`.

## End of session

Append one entry to `.agent-state/PROGRESS.md` at the TOP of the file (under the title). See `planner` skill's `progress-protocol.md` for the entry template (Goal / Done / Decisions / Files touched / Open / next session).

## Anchor map

| What | Where |
| ---- | ----- |
| Design source | `design/` (pages, sections, components) |
| Liquid output | `src/sections/`, `src/snippets/`, `src/blocks/`, `src/groups/`, `src/layout/`, `src/pages/` |
| Theme settings UI schema | `src/config/global-schema/*.js` (compiled via `src/config/settings_schema.js`) |
| Theme settings shipped defaults | `src/config/presets/preset-N.js` + `src/config/settings_data.js` |
| Settings → CSS variable adapters | `src/snippets/settings-adapter/*-adapter.liquid` |
| Build-time tokens (xo-css plugin) | `theme-config/theme.config.json` |
| Compiled Shopify theme | `shopify/` (do not hand-edit) |
| State (planner) | `.agent-state/{PLAN, PROGRESS, INVENTORY}.md` |
| Skills | `.claude/skills/*/` |
| MCP servers | `.mcp.json` (xo-components, playwright, xo-design) |
| xo-design (design preview + picker) | `design/xo-design/` (portable bundle) — `cd design && npm run xo-design` to start (`npm run xo-design:stop` to stop). Exposes the picker MCP at the URL listed in `.mcp.json#xo-design`. |
| Editor QA target | `.editor` (repo root) — single-line editor URL the `editor-qa` skill navigates to when no editor tab is already connected. |
