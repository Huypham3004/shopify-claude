# Clarify protocol (Step 1.5)

Sits between Step 1 (analyze the Figma frame) and Step 2 (variant audit). Surface architectural choices you'd otherwise pick silently — but only when genuinely ambiguous, and phrased like you actually read the frame.

> [!NOTE]
> Question text below is English documentation. At runtime, localise to the user's conversation language (per AGENT.md § Communication language). Identifiers (`hero-collage`, `collection_list`, `background-1`) stay English.

## Batching rule

```
COUNT = number of CONDITIONAL questions whose answer is NOT obvious from the frame
        (Q1 name AND Q7 CSS ALWAYS fire and are not counted)
COUNT == 0 → ask Q1 + Q7 (one AskUserQuestion call)          # the two-question minimum
COUNT == 1 → batch Q1 + that question + Q7
COUNT >= 2 → batch Q1 + triggered conditionals + Q7
AskUserQuestion holds ≤4 questions/call → with Q1+Q7 fixed, ≤2 conditionals per call; split if more
COUNT >= 5 → frame too ambiguous to batch — pause, ask freeform
```

The minimum interview is **two** questions (Q1 + Q7) — never zero, never one.

## Phrasing principles

1. **Lead with the Figma observation** — "1440×640 horizontal auto-layout, gap 64, two children (media + content)", "a wrap of 6 identical product cards", "a tab row above the card grid". The user validates the read before committing.
2. **Name the ambiguity** — say what's unclear, not just "which kind?".
3. **Recommend with reasoning** — one sentence of *why* in the lead option.
4. **Surface the consequence** — what changes if A vs B.
5. **No placeholder syntax** — never send `{N}`, `[describe motion]`. If you can't fill the observation, you haven't analyzed the frame — go back to Step 1.
6. **Match the user's register/language.**

## Decision table

| # | Question | Fire when | Cost if wrong |
| --- | --- | --- | --- |
| **Q1** | **Section/snippet name** (feature+layout formula) | **ALWAYS** — name is baked into 5-7 files | HIGH — rename touches dir, schema id, preset ref, PLAN row, callsites |
| Q2 | Block strategy — inline blocks vs hardcode (theme blocks only if user opts in) | Frame has 2+ repeating units | HIGH |
| Q3 | Data source — `collection_list` vs per-block vs single `collection` | Frame shows N collections/products (mock data) | HIGH |
| Q4 | Animation scope — port / static-first / skip | Frame implies scroll/parallax/motion (rare from a static frame; a Figma prototype/smart-animate or the user may describe it). On **port full** → invoke `Skill(motion)` to wire xo-animate/xo-parallax. Static-first defers the reveal layer to `/polish` | MEDIUM |
| Q5 | Snippet variant choice | 2+ existing variants plausibly match | MEDIUM |
| Q6 | Color scheme default | Frame is scheme-neutral or shown in multiple schemes | LOW-MED |
| **Q7** | **CSS strategy — SCSS-first vs XO-CSS-first** | **ALWAYS** (per project policy) | MED-HIGH |
| Q8 | Layout mechanism — `layout` system vs static grid vs raw CSS | Frame is a grid/wrap of N≥3 homogeneous items AND ≥2 modes interchangeable | MEDIUM |

Everything else (class names, setting order, wrapper choice, validator runs, inline_richtext-vs-richtext, placeholder type) is **auto** — decide by convention, surface in the preview.

## Q1 — name (always)

Single-select. **Option 1 = `Keep <current>`** when the frame name is already clean; **Options 2-3 = feature+layout suggestions** (the harness adds "Other"). Build the name from WHAT it does + HOW it's arranged: `image-text-split`, `logo-marquee`, `testimonial-carousel`, `product-grid`. Figma frame names are often editorial ("Hero – Homepage v3") — translate to a feature+layout name, don't ship the editorial label.

> *"Figma frame is `Hero – Homepage v3`, but structurally it's a centered hero with a media panel beside copy. Feature = hero, layout = split. Ship as? (rename touches 5-7 files)"*
> - **`hero-split`** — feature + layout, reusable (Recommended)
> - **`hero-media`** — if you read the panel as the focus
> - *(harness adds "Other")*

## Q7 — CSS strategy (always)

Single-select, 2 options. There is **no "Hybrid"** — XO-CSS-first already produces a tier-3 SCSS sidecar for anything atomic can't express (hover chains, keyframes, pseudo-elements, multi-target selectors).

Because Figma has no SCSS file to line-count, estimate the split from the frame: how much is plain layout/spacing/type + multi-value values (all atomic — multi-value uses `_` for spaces) vs genuinely tier-3 work (hover chains / `@keyframes` / pseudo-elements → SCSS). Quote that estimate.

> *"This frame is mostly layout + type (atomic-friendly) with one drop-shadow on the media panel (that shadow lands in SCSS either way). Two ways to author styling:"*
> - **XO-CSS-first** — atomic classes for layout/spacing/type in the liquid; the shadow + any hover fall through to a `.global.scss` sidecar. Recommended for static-layout sections.
> - **SCSS-first** — all styles in `<name>.global.scss` via framework helpers (`color()`, `fz()`, `media('>md')`). Recommended for heavy custom layout / multi-target hover / animation.

On **XO-CSS-first** → invoke `Skill(xo-css)` **and** `Skill(scss)`. On **SCSS-first** → invoke `Skill(scss)`.

## Conditional questions (fire only when triggered)

- **Q2 block strategy** — default 2-option (Inline blocks / Hardcode static). Theme blocks are OFF by default (present the 3-option form only if the user said "use a theme block").
- **Q3 data source** — 3 options (`collection_list` / section blocks per collection / single `collection` picker). Collection-tabs signature → one inline block per tab with a `collection` picker (no `collection_list`, no `All` tab).
- **Q8 layout mechanism** — default = the **`layout` system** (`{% render 'layout' %}` + `...layoutSchemaSettings()` — merchant switches grid↔carousel↔masonry + columns/gap); static grid primitive (`<div xo-grid class="xo-grid-block">`) for a fixed grid; raw CSS only if bespoke. **No `<xo-grid>` element.**

## Overrides

If the user says "just do it" / "tự quyết" / "skip questions", skip the protocol and proceed to Step 2. Don't re-ask a question already answered this session.
