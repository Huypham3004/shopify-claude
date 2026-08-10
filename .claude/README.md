# Shopify theme

A Shopify theme with an HTML-design → Liquid porting pipeline, driven by the `.claude/` agent system running on Claude Code.

> Bản tiếng Việt: [README.vi.md](./README.vi.md)

## Overview

The project has three layers:

- `design/` — HTML design source (xo-include + xo-component convention) — input.
- `src/` — Liquid theme source (`sections/`, `snippets/`, `blocks/`, `groups/`, `layout/`, `pages/`, `config/`, `styles/`) — output authored by the agent.
- `shopify/` — compiled output (produced by the build pipeline, never hand-edited).

The `.claude/` agent sits in the middle: it reads the design, writes Liquid, validates schemas, and commits by scope. Project state lives in `.agent-state/` (markdown, committed to git) so multiple sessions can pick up where the previous one stopped without losing context.

## The `.claude/` system

### Three layers

| Layer | Location | Role |
|-------|----------|------|
| **Project memory** | `.agent-state/` | Three markdown files: `PLAN.md` (priority queue ⚪🔵✅⏸❓), `PROGRESS.md` (append-only changelog, one entry per session), `INVENTORY.md` (coverage map, auto-generated). |
| **Skill catalog** | `.claude/skills/<name>/` | 19 specialised skills — each is a folder with `SKILL.md` + `references/*.md` + `scripts/` if needed. |
| **External integrations** | `.mcp.json` | 3 MCP servers (`xo-components`, `playwright`, `xo-design`) + `context7` for docs lookup. |
| **Guardrails** | `.claude/hooks/` + `settings.json` | `skill-reminder.cjs` — a `PreToolUse` hook that nudges the right skill by file path on every Edit/Write; `settings.json` pins the model, the skill plugins, and registers the hook. |

### The 19 skills

| Skill | Answers | Triggered when |
|-------|---------|----------------|
| `planner` | **WHAT + STATUS** — what's next, where we are | Start of every session, or when asked "what's next" |
| `design-to-liquid` | **HOW** — port one section (Step 0 tokens → Step 6 restyle) | User picks a section in xo-design or calls `/design-to-liquid` |
| `figma-to-liquid` | **HOW (Figma)** — port a section/snippet from a Figma frame via the Dev Mode MCP | Select a frame in Figma desktop, then `/figma-to-liquid` |
| `design-sync` | Re-port worklist when `design/` is pulled forward | `/design-sync`, "design có bản mới", after `git -C design pull` |
| `polish` | Finishing-pass QA — a11y · `xo-animate` reveal · `xo-hover` | `/polish <target>`, or design-to-liquid's completion handoff |
| `editor-qa` | Live Theme Editor QA — add section/blocks, set fields, desktop↔mobile, screenshot | `/editor-qa <target>`, "test trên editor" |
| `lighthouse-audit` | Lighthouse scores (Perf/A11y/BP/SEO) + Core Web Vitals against a storefront URL | `/lighthouse-audit <url>` — run manually once the theme is done |
| `liquid` | Liquid language reference — tags, filters, objects, idioms, gotchas | Authoring/debugging any `.liquid` file |
| `snippet` | How to author the `.liquid` body of a snippet | Creating/editing a snippet |
| `schema` | How to write `schema.js` (section / block / global) | Creating/editing a schema |
| `scss` | The SCSS framework: `color()` / `fz()` / `media()` / BEM | Writing `.global.scss` |
| `xo-css` | Atomic class syntax: `p:1rem c:primary|h d:none@md` | Adding classes in liquid |
| `liquid-doc` | `{% comment %} @param … %}` doc blocks | Top of a snippet file |
| `motion` | Authority on wiring motion: `xo-animate` / `xo-parallax-scroll` / `xo-parallax-hover` (+ the `xo-start/xo-end` gotcha) | `/motion`, "add animation/parallax" |
| `web-components` | Author a NEW `xo-*` web component (TS, `XoComponent`) into `src/scripts/` | `/web-components`, "create a web component" |
| `git` | Scoped commits; after committing asks Push / commit next / stop (Step 11); push only on your explicit choice, never `--force`, no amend | User types `/git` |
| `extract-icon` | Sync Lucide SVGs into `src/snippets/icons/icon-*.liquid` | "update icons", "sync icons", "lucide → snippet" |
| `system-upgrade` | Check, evaluate + **upgrade** the `.claude/` system (skill changes delegated to `skill-creator`) | `/system-upgrade`, `/system-audit`, "check .claude", "nâng cấp hệ thống" |
| `shopify-watch` | Radar for theme-relevant Shopify news, hands off to `/system-upgrade` | `/shopify-watch`, "what's new in Shopify" |

### Script tooling

| Script | Purpose |
|--------|---------|
| `.claude/skills/design-to-liquid/scripts/validate-schema.py` | Validates `schema.js`: compile, duplicate IDs, range, select, inline_richtext tags, block resolution. Plus Theme Store label audit (AmE spelling, banned phrases, ampersand, `?`). Use `--strict` to escalate warnings to errors. |
| `.claude/skills/planner/scripts/scan-inventory.py` | Walks `design/` + `src/sections/`, generates `INVENTORY.md`. |

### Entry point

```
CLAUDE.md  →  .claude/AGENT.md
                    │
                    └─→ contract: read .agent-state/PROGRESS then PLAN before doing anything else
```

## Starting a fresh design project

### Day 0 — Setup (~30 minutes, manual)

1. Copy `.claude/` + `CLAUDE.md` from a reference project into the new repo.
2. Create an empty `.agent-state/` — the kickoff-protocol will seed PLAN/PROGRESS/INVENTORY.
3. Drop the design into `design/` (layout: `design/src/pages/*.html` + `design/src/sections/<name>/<name>.html`).
4. If the design includes xo-design: `cd design && npm run xo-design` → the browser shows the `◎ Pick section` toolbar.
5. Update `.mcp.json` if the xo-design URL differs from the port set in `design/xo-design/.env`.
6. (Optional) Wire any extra MCP servers your design pipeline uses (e.g. `context7` for docs lookup) in `.mcp.json`.

### Day 1 — First session with Claude

Open Claude Code and type `let's begin` or `port this design`. The agent will automatically:

1. Read `CLAUDE.md` → `AGENT.md` → look for state docs.
2. State doesn't exist → activate the `planner` kickoff-protocol.
3. Scan `design/` + `src/sections/`, generate `PLAN.md` v0 (pages + sections + Step 0 tokens) and `INVENTORY.md` v0.
4. Ask for page priorities → user confirms.
5. Append session-1 entry to `PROGRESS.md`.

### Day 2 — Step 0 (once per project)

User: `do Step 0`. The agent will:

1. Read the brand guide / global SCSS / palette from the design.
2. Edit `src/config/presets/preset-1.js` (DO NOT create `preset-<brandname>.js`).
3. Set `color_schemes` (≥ 4 colors, each background paired with foreground), 4 font slots, 6 heading presets, radius, page width, spacing.
4. `src/config/settings_data.js`: `current = JSON.parse(JSON.stringify(preset1))` (object clone — NOT a string ref).
5. Add italic-em rule to `src/styles/base/content.scss` if the design uses one.
6. Build + reload Theme Editor → verify `:root` emits the expected `--color-…` / `--font-…` variables.
7. Flip "Theme tokens" in PLAN.md → ✅.

## A normal working day

```
09:00  Open Claude Code, type "what's on today?"
        → Agent reads top of PROGRESS + PLAN, suggests the next section.

09:05  Browser: click ◎ Pick on the target section.
        Claude: /design-to-liquid

09:06  Agent automatically:
        - mcp__xo-design__get_selection() → gets htmlPath / scssPath
        - Confirms "Convert {page}.{sectionName} → src/sections/{name}/ ?"
        - Reads design HTML + SCSS
        - Variant audit: walks ladder A→B→C for every snippet to render
        - Writes 3 files: <name>.liquid + <name>.global.scss + schema.js
        - Runs validate-schema.py → fixes warnings
        - mcp__xo-design__clear_selection()
        - Updates PLAN.md → ✅

09:45  (optional) Visual check via the playwright MCP — screenshot the Theme Editor preview.

10:00  /git
        → git skill: scan → preview → confirm → commit one scope.

10:30  Repeat from 09:05 for the next section.

17:00  End of session: agent appends PROGRESS.md with Goal/Done/Decisions/Open.
        /git agent-state to commit the state files.
        git push (by hand, when ready).
```

### Picker MCP

The user points (`◎ Pick section`) instead of typing the section name — the agent receives the selection via MCP. Natural-language prompts like "do this one", "port the picked one", or a bare `/design-to-liquid` all work.

### Variant audit ladder

Before `{% render 'X' %}` in a new section, the agent **must** walk the ladder:

| Step | Action | When to use |
|------|--------|-------------|
| A | Set a value in `preset-N.js` | A variant already reads the setting; only the value is wrong |
| B | Modify the closest variant | Change is universally beneficial; doesn't break other presets |
| C | Create a new variant (`<snippet>-N`) | **STOP — ASK USER FIRST.** Ripples into the dispatcher + global-schema |

## Validator workflow

```bash
# Validate one section
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/

# Sweep everything
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all

# CI mode — warnings escalate to errors
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all --strict

# Theme settings sanity (settings_data.json vs settings_schema.json)
python .claude/skills/design-to-liquid/scripts/validate-schema.py --theme

# Cross-validate a preset against its sibling schema
python .claude/skills/design-to-liquid/scripts/validate-schema.py --preset src/sections/<name>/preset-1.js
```

Catches: disallowed `inline_richtext` tags, missing range bounds, undefined select options, unresolved block types, theme-settings `current` as string, orphan color schemes, missing labels, British spelling, banned phrases (`CTA` / `X position` / `homepage` / `slider` / …), `&` or `?` in labels.

## Commit workflow (`/git`)

Hard rules:

- 1 commit = 1 scope. Never straddle scopes (`.claude` + `root` must be two separate commits).
- Conventional Commit format: `<type>(<scope>): <summary>` ≤ 70 chars, lowercase.
- Stage specific paths only — never `git add -A` / `.`.
- No push, no amend, no hook bypass, no AI co-author trailer.

The `git` skill scans dirty files, suggests a scope, drafts the message, asks for confirmation, runs pre-commit gates (secret-file block, schema mismatch, scope leak, settings JSON sync), then commits. The user confirms before every commit.

## Project lifecycle (reference timeline)

| Week | Phase | Activity |
|------|-------|----------|
| 1 | Kickoff + Step 0 | PLAN seeded; preset-1.js fully tokenised; 1-2 trial sections to validate the pipeline |
| 2-3 | Home page sprint | 12-15 home sections; 1-2 new snippet variants (audit ladder step C, user-approved) |
| 4 | Product + Collection | PDP + PLP; blocks (price/vendor/add-to-cart); facet filters |
| 5 | Cart + Article + remaining pages | Small but numerous sections |
| 6 | Polish + Theme Store prep | Clear pre-existing validator errors; run `--strict`; Lighthouse; demo store; docs |

"Done" criteria: see `.claude/skills/design-to-liquid/references/theme-store-requirements.md`.

## Deeper references

| To learn | File |
|---------|------|
| Full working philosophy + skill catalog | `.claude/AGENT.md` |
| Format of each state doc | `.claude/skills/planner/references/*.md` |
| Step-by-step section porting | `.claude/skills/design-to-liquid/SKILL.md` |
| Mapping design tokens → preset | `.claude/skills/design-to-liquid/references/tokens-mapping.md` |
| Theme Store requirements + label audit | `.claude/skills/design-to-liquid/references/theme-store-requirements.md` |
| Variant audit + escalation ladder | `.claude/skills/design-to-liquid/references/sections-to-liquid.md` |
| Picker MCP protocol | `.claude/skills/design-to-liquid/references/picker-protocol.md` |
| BaseHTML SCSS framework | `.claude/skills/scss/SKILL.md` |
| Atomic class syntax (XO-CSS) | `.claude/skills/xo-css/SKILL.md` |
| Detailed commit workflow | `.claude/skills/git/SKILL.md` |

## Tech stack

- Shopify Liquid theme (source `src/`, compile `shopify/`)
- Vite + scss-glob plugin
- BaseHTML SCSS framework + XO-CSS atomic utilities
- xo-webcomponents runtime (`<xo-container>`, `<xo-carousel>`, `<xo-magnetic>`, …)
- Claude Code + MCP (xo-components, playwright, xo-design)
- `context7` MCP for fetching up-to-date library docs (Liquid, Shopify APIs, …)
