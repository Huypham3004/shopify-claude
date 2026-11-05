# Clarify protocol

> Step 1.5 of the porting workflow. Sits between Step 1 (survey) and Step 2 (variant audit).
> Purpose: surface architectural choices the agent would otherwise pick silently, but only when the choice is genuinely ambiguous — and ask them like the agent actually read the design, not by filling a template.

> [!NOTE]
> Question text and option labels below are written in English as documentation.
> At runtime the agent localises them to match the user's conversation language per `.claude/AGENT.md` § "Communication language". Identifiers (`hero-collage`, `collection_list`, `background-1`, …) stay English regardless.

## When this protocol runs

Triggered automatically after Step 1 finishes (design HTML + SCSS read, reuse candidates identified). Walks the question table below and decides for each: **ask or skip**.

```
COUNT = number of CONDITIONAL questions (Q2–Q6, Q8) whose answer is NOT obvious
        (Q1 Section name AND Q7 CSS strategy BOTH always fire and are NOT counted)
COUNT == 0 → ask Q1 + Q7 (two questions, one batched AskUserQuestion call), then Step 2
COUNT == 1 → batch Q1 + that question + Q7 (one AskUserQuestion call), then Step 2
COUNT >= 2 → batch Q1 + all triggered conditionals + Q7 into one AskUserQuestion call, then Step 2
COUNT >= 5 → design is too ambiguous for a batched interview; pause and ask freeform instead

The minimum interview is now TWO questions (Q1 + Q7) — never one.

`AskUserQuestion` holds at most **4 questions per call**. With Q1 + Q7 always present, a single call fits at most **2 conditional** questions (Q1 + 2 + Q7 = 4). If Q1 + conditionals + Q7 would exceed 4, split into **two AskUserQuestion calls** (keep Q1 in the first); when conditional COUNT ≥ 5 the design is too ambiguous to batch — pause and ask freeform instead.
```

Never run for the sake of running. A clean section (`subscribe`, `manifesto` with already-named generics, no commerce data, no animation, no raw-CSS grid) reaches Step 2 having asked exactly **one** question — Q7.

## Phrasing principles

Once a question fires, write it like the agent actually read the design — not like a form. Seven rules:

1. **Lead with the observation.** Name what specifically in the design triggered the question — "6 corner shapes with subtle parallax", "4 product cards in a 2×2 grid", "scroll-bound per-character keyframes on the headline". The user can validate or correct the observation before they commit to the choice.

2. **Articulate the ambiguity.** Say what about the observation is unclear. "Could be ad-hoc decoration unique to this hero, or a shape system other hero variants might reuse." Don't just ask "which kind?" — show what made the choice non-obvious.

3. **Recommend with reasoning, not just a tag.** Don't write "(Recommended)" and stop. Say *why* — usually one sentence in the option's description. "Inline blocks — keeps the set scoped to this hero; recommended unless you plan a sibling hero archetype reusing the same shapes."

4. **Surface the downstream consequence.** Briefly mention what changes if the user picks A vs B. The user shouldn't have to reverse-engineer the trade-off ("inline keeps it scoped; theme blocks unlock reuse but add a separate file pair to maintain").

5. **Strip placeholder syntax before sending.** Notes like `{N}`, `{design-folder-name}`, `[{describe motion}]` are agent-side reminders to fill in. They never leak to the user. If the agent can't fill a placeholder, the question shouldn't fire.

6. **Don't over-explain a simple choice.** If the audit gives a 2-option pick with one obvious lead, 1-2 sentences + tight options is enough. Reserve discursive framing for genuinely complex decisions.

7. **Match the user's register.** Mirror their language (per AGENT.md). Match their pace — short and conversational if the chat is moving fast, more discursive if the user is exploring or new to the territory.

## Decision table — what to evaluate

Walk these in order. For each, apply the **trigger** rule. If trigger fires, the question goes into the batch.

| # | Question | Trigger (ask when) | Skip when | Cost if wrong |
|---|----------|--------------------|-----------|---------------|
| 1 | **Section name** (header/footer: **which layout**) | **ALWAYS fire** — every port confirms the name before it's committed. For a header/footer design, ask which `layout` it maps to instead (Q1 detail § header/footer). Propose names from the feature + layout formula (Q1 detail); when the folder name is already clean, "Keep `<current>`" is simply the recommended option | Never — fire on every section port | **HIGH** — rename touches 5-7 files (section dir, schema id, page preset reference, PLAN row, any `{% section %}` callsite, future imports), so confirming up front is far cheaper than renaming after |
| 2 | **Block strategy** | Design has 2+ repeating units with similar shape | No blocks needed (single-render section), OR shape is so different per unit that hardcoded markup wins | **HIGH** — inline blocks live in section schema, theme blocks live in `src/blocks/<group>/<name>/` with their own schema. Wrong choice = re-author both files. |
| 3 | **Collection / product data source** | Section displays N collections or N products | No commerce data in this section | **HIGH** — `collection_list` setting (merchant picks N from store, iterate dynamically) vs section blocks (per-block collection picker + per-card override) vs single `collection` picker (1 collection, iterate its products) produce 3 entirely different schema + markup shapes |
| 4 | **Animation port scope** | Design has scroll-triggered / parallax / per-character motion / IntersectionObserver-driven sequencing | Static design (CSS hover only is not "animation" for this purpose) | **MEDIUM** — animation can be added later as a separate pass, but bundling the effort upfront avoids the 2nd re-survey |
| 5 | **Snippet variant choice** | 2+ existing variants are plausible matches in the audit (e.g. `featured-products` vs `featured-collection`, `hotspot` vs `hotspot-popover`) | Single obvious match, OR step C will fire anyway (new variant — already mandatory ask) | **MEDIUM** — refactor easy, but writes early; agent might pick the looser-matching variant and burn effort restyling |
| 6 | **Color scheme default** | Design is scheme-neutral or shows multiple variants without indicating which is canonical | Design clearly maps to one scheme (cream bg → `background-1`, dark bg → `background-2`) | **LOW-MEDIUM** — scheme is a setting; merchant flips in editor. But default matters for first impression of the preset. Surface in preview if not asked. |
| 7 | **CSS strategy — SCSS-first vs XO-CSS-first** | **ALWAYS fire** (per user policy 2026-05-26). Section/snippet ports without an explicit CSS strategy default to BEM SCSS — codebase has drifted into inconsistency because of this. Fire even when answer feels obvious | Never — fire on every section + every brand-new snippet, including ports of simple sections (let user pick fast if obvious) | **MEDIUM-HIGH** — switching strategy mid-port costs ~20-40 line re-author. Critical: XO-CSS-first ≠ pure XO-CSS — tier-3 edge cases (hover chains / keyframes / pseudo-elements / multi-target selectors / dynamic CSS-var styles) STAY in SCSS sidecar regardless. See `xo-css/references/basics.md` § "Translating from design SCSS" for the 3-tier framework + font-size guidance (body sizes = direct rem like `fz:1.4rem`; heading sizes = `fz:hN`/`fz:dN` tokens) |
| 8 | **Layout mechanism** | Section renders **N≥3 homogeneous repeating items** as a grid / grid-block / masonry / carousel / grid-hover-expand (raw-CSS **or** existing `xo-grid-block` / `<xo-carousel>` / `<xo-component src="layout">` markup) AND ≥2 of those modes are interchangeable presentations | Bespoke / heterogeneous layout (hero collage, feature split, comparison table, timeline), single/2-item, or switching modes would break the design's meaning | **MEDIUM** — hand-rolling the layout in section SCSS loses merchant switchability (grid↔carousel↔masonry) + theme consistency. Default = the **`layout` system** (`{% render 'layout' %}` + `...layoutSchemaSettings()`); a static grid primitive (`<div xo-grid class="xo-grid-block">`) when only a fixed grid suffices; raw CSS only if bespoke. See `./grid-and-layout.md` |

The remaining decisions (CSS classes, schema setting order, internal var names, exact placeholder type, vertical spacing, wrapper choice, validator invocation, inline_richtext vs richtext) are **always auto** — agent picks based on convention, surfaces in the preview if non-obvious.

> [!IMPORTANT]
> **Two questions always fire: Q1 (Section name) and Q7 (CSS strategy).** Q2–Q6 and Q8 obey the COUNT/skip rule (fire only when triggered).
> - **Q7** always fires because the codebase needs an explicit CSS choice per write — silent default has produced an inconsistent mix (BEM-heavy `collection-card` vs XO-CSS-heavy `section-heading-1`). User requested this 2026-05-26.
> - **Q1** always fires because the name is baked into 5-7 files at port time (dir, schema id/class, page-preset reference, PLAN row, `{% section %}` callsites), so renaming afterward is expensive — confirming up front is cheap, and the user should always get a deliberate name decision.

## Anti-patterns

| Anti-pattern | Why it's bad |
|--------------|--------------|
| Asking all 6 questions every section | Friction collapses the workflow. The skip rule exists precisely to avoid this. |
| Asking "should the validator run?" / "wrap in `{% render 'section' %}`?" | Convention, not a choice. Don't surface deterministic decisions. |
| Asking about CSS class names / internal variable naming | Out of user's concern; agent owns these. |
| Asking "which page template should this section be placed on?" upfront | Better asked at end-of-port after the section actually works — placement is reversible, the section is the artifact. |
| Asking without offering a leading option | Forces the user to do all the decision work. Always lead with one and say why. |
| Asking, then silently overriding the answer later | Erodes trust. If a downstream constraint forces a different choice, surface and re-ask. |
| Asking a tier-3 question (color scheme is obvious from design) | Pads the batch and trains the user to skim-click. |
| Re-asking the same question that step C (new variant) is about to ask | Duplicate ask. Q5 of this table excludes the `→ new variant` branch precisely to avoid this. |
| Sending placeholder syntax (`{N}`, `[{describe motion}]`) verbatim to the user | Signals the agent didn't actually fill the observation. If it can't fill it, it shouldn't ask. |
| Phrasing the question as a template (`"{N} repeating units. Which block kind?"`) | The user can't tell if the agent actually understood the design or just pattern-matched the section type. Lead with the observation, not the count. |

## Question shapes + example phrasings

For each question: the decision shape, what to observe before phrasing, one good example, one anti-example for contrast where useful.

### Q1 — Section name (always fires)

**Decision shape:** single-select AskUserQuestion. **Option 1 = `Keep <current-name>`** (recommend it when the folder name is already clean). **Options 2–4 = 2-3 suggested names** built from the feature + layout formula below. The AskUserQuestion harness auto-adds an **"Other"** free-text choice, so the user can always type their own — provide only `Keep` + the suggestions, never hand-author an "Other" option.

**Naming formula = feature + layout.** Build the name from WHAT the section does (the content/feature archetype — featured products, newsletter signup, testimonials, bundle builder, image + text, logo wall) joined with HOW it's arranged (the layout — grid, carousel, tabs, collage, marquee, split, masonry, slideshow, accordion). Kebab-case, lowercase. Worked names: `product-grid`, `featured-products-tabs`, `testimonial-carousel`, `hero-collage`, `bundle-tabs`, `logo-marquee`, `image-text-split`. **Read the design first** and propose real feature+layout names — never `{N}`-style placeholders.

**Observe first:** the design folder name, what the section actually does (feature), how it's laid out (layout), and whether the current name is brand-coupled (proper noun / sub-brand vertical) or already feature-generic.

**Good — brand-coupled folder, real alternatives proposed:**

> *Question:* "Design folder is `hero-pet`, but the section is just a centered hero with corner decoration shapes — nothing pet-specific in the architecture. Feature = hero; layout = collage of decoration shapes. What should it ship as? (rename touches 5-7 files, so it's worth deciding now)"
>
> *Options:*
> - **`hero-collage`** — feature (hero) + layout (collage); reusable across sibling sub-brands (Recommended)
> - **`hero-pet`** — keeps the design ↔ section 1:1 mapping
> - **`hero-split`** — if you read the layout as a split rather than a collage
>
> *(harness adds "Other" for a custom name)*

**Good — already-clean folder, Keep is recommended (Q1 still fires):**

> *Question:* "Folder is `subscribe` — a single-render newsletter signup, centered. Already feature-generic. Keep it, or standardize to a feature+layout name?"
>
> *Options:*
> - **`Keep \`subscribe\``** — clean and conventional already (Recommended)
> - **`newsletter-signup`** — more explicit feature naming if you're standardizing

**Anti-example (rigid template):** "Section name: keep `hero-pet` or rename to a feature-generic alternative?"
*Doesn't show the agent grasped the feature/layout or proposed real names. The user has to do that work.*

#### Q1 for a header or footer — "which layout?" instead of a name

A header/footer port never creates a section, so there is no name to confirm. Q1 still always fires, but it
asks which **layout** of the single header/footer section the design maps to (see `./header-port.md` §3,
`./footer-port.md`). Read the current `layout` options in the section's `schema.js` and every layout
snippet's markup + SCSS first, then compare structure (not paint).

*(Illustrative wording — the layout match must come from your own structure comparison, not from this example.)*

> *Question:* "Design `header-kids` is a two-row header: brand bar on top, numbered column menu below. That's
> the structure of the existing **Editorial** layout; differences are paint only (rounded sticker logo, kids
> palette). How should it land?"
>
> *Options:*
> - **Use Editorial + restyle** — set `layout: editorial` in header-group.json, restyle its SCSS (Recommended)
> - **Use Editorial as-is** — only change settings/defaults, no SCSS
> - **New layout** — add a `header-<archetype>` layout snippet + option (new markup + settings)

Recommend "New layout" only when no layout shares the design's structure — and say what the new layout
would reuse. Never offer "new header section" as an option. The design folder may be `header-1`,
`header-2`, `header-<preset>`, `footer-3`… — quote it so the user knows which design you mean, but derive the
layout match (and any proposed new layout name) from structure, not from the suffix.

### Q2 — Block strategy

**Decision shape:** single-select, 2-3 options — inline blocks / theme blocks / hardcoded.

**Observe first:** count of units, whether they share shape, whether that shape appears in other sections of the design, whether merchants would plausibly want to add / remove / reorder them.

**Project policy (2026-05-26):** **theme blocks are OFF by default.** Always default to inline blocks for repeating units. Theme blocks (`src/blocks/<group>/<name>/`) require an explicit user instruction — don't propose them as an option in Q2 unless the user said something like "use a theme block" / "make it reusable across sections" / "split into a block file". Default 2-option choice:

> *Options:*
> - **Inline blocks** — Section-private, declared in section schema. Recommended.
> - **Hardcode static** — No merchant control, fastest to author; pick if merchants will never tweak the count or content.

**Only when user has explicitly opted into theme blocks**, present the 3-option form below:

> *Question:* "6 corner shapes (rings, sunbursts, blooms) with subtle parallax drift — they look ad-hoc to this hero, no other section in the design reuses the same shape set. Want each shape as an inline block (lives in the section schema, section-private) so merchants can swap individual shapes, or pull them out as theme blocks (separate files in `src/blocks/`) so a sibling hero variant could compose the same set?"
>
> *Options:*
> - **Inline blocks** — Section-private, compact schema, no extra file pair to maintain. Recommended for ad-hoc decoration
> - **Theme blocks** — Reusable across sections; pick if another hero variant might compose these same shapes
> - **Hardcode static** — No merchant control, fastest to author; pick if merchants will never tweak the decoration

### Q3 — Collection / product data source

**Decision shape:** single-select, 3 options — `collection_list` / per-block / single picker.

**Observe first:** count of items, whether per-card overrides are visible in the design (custom headings, custom image overlays, custom CTA per card), whether the design implies the items are merchant-curated or pulled from a single collection.

**Good:**

> *Question:* "Section shows a 2×2 grid of 4 product cards, rendered identically — no per-card custom heading or image overlay visible in the design. Three ways to wire the data: `collection_list` (merchant picks N collections from the store, you iterate dynamically — cleanest for a vanilla grid), section blocks per collection (each block has its own picker + override fields — pick this if you anticipate per-card flair), or a single `collection` picker where you iterate its products. Which fits the brief?"
>
> *Options:*
> - **`collection_list` setting** — Merchant picks N collections, iterate dynamically. Cleanest for vanilla grids (Recommended)
> - **Section blocks per collection** — Per-block picker + override fields; pick if per-card customization is on the roadmap
> - **Single `collection` picker** — One collection setting, iterate its products inside the section

> [!NOTE]
> **Collection-tabs form.** If Step 1 flagged a collection-tabs signature (tab row above a product grid, tabs swap collections), Q3 is **not** the generic 3-way above — it resolves to **one inline block per tab, each with a `collection` picker** (no `collection_list`, no `All` tab). Confirm the collection-per-tab framing with the user, then port via `references/collection-tabs.md`.

### Q4 — Animation port scope

**Decision shape:** single-select, 3 options — port full / static first / skip.

**Observe first:** the specific motion (parallax? scroll-bound? per-character? marquee? IntersectionObserver fade?), whether the primitive exists in the project (`<xo-magnetic>`, `<xo-parallax-scroll>`, `<xo-intersection-video>`), how much extra code the motion adds, whether the design's concept depends on the motion.

**Good:**

> *Question:* "Headline animates per-character with a scroll-bound keyframe — each letter eases in as the section enters the viewport. The project has `<xo-parallax-scroll>` so the primitive is there, but wiring the per-character split + staggered keyframes adds maybe 30-40 lines of SCSS plus a small snippet. Port the motion now since it carries the manifesto concept, or ship static layout first and treat motion as a follow-up?"
>
> *Options:*
> - **Port full** — Bundle motion + markup this session; motion carries concept (Recommended for manifesto-style copy)
> - **Static first** — Markup now, motion as a follow-up pass once layout is validated
> - **Skip animation** — No motion, ship static permanently

### Q5 — Snippet variant choice

**Decision shape:** single-select, 2+ options — existing variants only. The "create new variant" branch is step C's job, NOT offered here.

**Observe first:** what each candidate variant currently does, what's hardcoded vs settings-driven in each, which is closer to the design's intent, what the gap looks like.

**Good:**

> *Question:* "Product carousel in the design could plug into two existing options: `featured-products-1` (4-up static grid, hand-picked products, no carousel) or `featured-collection-2` (carousel mode, iterates a single collection, has slide arrows). The design shows arrows + sliding, which leans toward `featured-collection-2`, but it pulls from one collection rather than a hand-picked product list. Which closer match do you want to start from? (If neither fits, we'll escalate to step C — new variant.)"
>
> *Options:*
> - **`featured-collection-2`** — Carousel matches; downside is single-collection iterate, not hand-picked products (Recommended starting point)
> - **`featured-products-1`** — Hand-picked products match; downside is no carousel, would need step B refactor to add slide mode

### Q6 — Color scheme default

**Decision shape:** single-select, 2+ options (matches the active preset's declared schemes).

**Observe first:** the background colour in the design, whether the design mocks the section in more than one scheme, whether the section reads "editorial / break" (lean dark) or "body / content flow" (lean light).

**Good (only fires when the design is genuinely ambiguous):**

> *Question:* "The design mocks this section in both the cream and the dark scheme, weighted equally in the mockup — no clear default. Which one should ship as the preset's default? Merchants can flip per-instance via the `color_scheme` setting either way."
>
> *Options:*
> - **`background-1` (cream)** — Warmer, the dominant scheme across the home flow (Recommended)
> - **`background-2` (dark)** — More editorial; pick if the section is meant as a visual break

### Q7 — CSS strategy (always fires)

**Decision shape:** single-select, 2 options (SCSS-first / XO-CSS-first). Fires on every section port AND every brand-new snippet.

> [!IMPORTANT]
> There is no separate "Hybrid" option. The XO-CSS-first path **already produces a tier-3 SCSS sidecar by definition** — anything XO-CSS cannot express (hover chains, keyframes, pseudo-elements, multi-value props) automatically falls through to `<name>.global.scss`. A "Hybrid" choice would be identical to XO-CSS-first, so don't offer it.

**Observe first:** scan design's SCSS file(s). Count: how many lines? What's the breakdown — layout/spacing/typography (atomic-eligible) vs hover-chain / keyframes / pseudo-elements / complex selectors (tier-3 → SCSS sidecar)? Does design markup already use `xo-hover` / `xo-abs` / other `xo-*` attribute patterns (tier 2 — copy verbatim, no CSS)?

**Good:**

> *Question:* "Design SCSS for this section is {N} lines: ~{M} lines of layout/spacing/typography (atomic-eligible), ~{K} lines of hover-chain + keyframes (must stay in SCSS regardless). Design markup also uses {`xo-hover` count} on {N elements} (those copy verbatim, no CSS needed). Two ways to author the styling:"
>
> *Options:*
> - **XO-CSS-first** — Atomic classes for layout/spacing/typography in the liquid; tier-3 styles (~{K} lines) automatically fall through to a `.global.scss` sidecar. Space tokens approximated to nearest match (surfaced in preview). Recommended for static-layout sections with simple hover patterns.
> - **SCSS-first** — Copy the design SCSS into the project's `<name>.global.scss`, translated to framework helpers (`color()`, `fz()`, `media('>md')`). Closest to design file structure. Recommended for sections with heavy custom layouts / multi-target hover / animation.

**Phrasing rule for Q7:** ALWAYS quote concrete numbers from the design SCSS audit ({N}/{M}/{K}). Generic question without numbers = anti-pattern. The user makes a faster decision when the trade-off is concrete.

When user picks **XO-CSS-first**, the agent MUST invoke `Skill(xo-css)` and read `references/basics.md` § "Translating from design SCSS" before authoring. Also invoke `Skill(scss)` because tier-3 SCSS sidecar is inevitable.

When user picks **SCSS-first**, the agent MUST invoke `Skill(scss)` before authoring.

### Q8 — Layout mechanism

**Decision shape:** single-select, 2-3 options — `layout` system / static grid primitive / keep raw CSS. Fires only when Step 1 found a **layout-able collection** (N≥3 homogeneous items as grid/masonry/carousel/grid-hover-expand) and the suitable-case gate passes.

**Observe first:** how many items, are they homogeneous (same card repeated), what layout mode the design uses (grid / `column-count` masonry / scroll-snap carousel), the column count + gap, and whether ≥2 modes are interchangeable for this content. Confirm it's NOT bespoke/heterogeneous (hero collage, feature split, comparison table). See `./grid-and-layout.md` before phrasing.

> [!IMPORTANT]
> Default recommendation is the **`layout` system** (`{% render 'layout' %}` + `...layoutSchemaSettings()`) — it gives the merchant a Type switch across grid/carousel/masonry/grid-hover-expand + columns/gap, and is what every existing collection section uses (`product-list`, `collection-list`, `blog-list`, …). The static grid primitive is `<div xo-grid class="xo-grid-block">` — **there is no `<xo-grid>` element.**

**Good (homogeneous product grid):**

> *Question:* "The design's `.collection__grid` is a hand-rolled `display:grid; grid-template-columns: repeat(4,1fr); gap:1.5rem` over 8 identical product cards. This theme has a `layout` system — wrapping the cards in it gives the merchant a Type switch (grid ↔ carousel ↔ masonry) plus column/gap controls, and matches every other collection section. Adopt the `layout` system, or keep it a fixed grid?"
>
> *Options:*
> - **`layout` system** — `{% render 'layout', content: items, context: section %}` + `...layoutSchemaSettings()`; merchant switches grid/carousel/masonry + columns/gap. Matches `product-list`/`collection-list`. (Recommended)
> - **Static grid primitive** — `<div xo-grid class="xo-grid-block" style="--xo-col-desktop:4; --xo-col-tablet:2; --xo-col-mobile:2">` with `<xo-item>` children. Fixed grid, lighter; pick if a Type switch isn't wanted.
> - **Keep raw CSS** — Only if the layout is bespoke (asymmetric spans / named areas) the primitives can't express; surfaced in preview.

**Anti-example:** silently copying `display:grid; grid-template-columns: repeat(4,1fr)` into `<name>.global.scss`. *Loses merchant switchability + theme consistency, and diverges from every other ported collection section.*

## Worked examples — how the protocol behaves end-to-end

### Example 1 — `subscribe` (2 questions — Q1 + Q7)

Step 1 survey output: design `design/src/sections/subscribe/subscribe.html`. Name = feature-generic. Single render (no blocks). No commerce. No animation. Cream bg → `background-1` obvious.

Evaluation:
- **Q1 name: FIRE** (always) — `subscribe` is already clean, so lead with `Keep \`subscribe\`` (Recommended), offer `newsletter-signup` as a standardize alternative
- Q2 blocks: SKIP (no repeating units)
- Q3 data: SKIP (no commerce)
- Q4 animation: SKIP (static)
- Q5 variant: SKIP (only `button-1`, `image-1`, form helper — all obvious)
- Q6 scheme: SKIP (design clearly cream)
- **Q7 CSS strategy: FIRE** (always fires)

→ COUNT(Q2-Q6, Q8) = 0. **Batch Q1 + Q7 into one AskUserQuestion call** (the two-question minimum). Proceed to Step 2 after answer.

### Example 2 — `hero-pet` → `hero-collage` (4 questions: Q1 + Q2 + Q4 + Q7)

Step 1 survey output: design `design/src/sections/hero-pet/hero-pet.html`. Name brand-coupled. 6 decorative shapes positioned absolutely with parallax. Centered content. Pet-brand theme but the section concept is generic.

Evaluation:
- **Q1 name: FIRE** (always) — `hero-pet` is brand-coupled; feature (hero) + layout (collage) → propose `hero-collage` / `hero-split`, with Keep `hero-pet`
- Q2 blocks: **ASK** — 6 decoration units, inline vs theme block matters
- Q3 data: SKIP (no commerce)
- Q4 animation: **ASK** — parallax drift on shapes, non-trivial to port
- Q5 variant: SKIP (button + image obvious)
- Q6 scheme: SKIP (design clearly cream)
- **Q7 CSS strategy: FIRE** (always fires; design SCSS has heavy CSS-variable-driven positioning → likely XO-CSS-first with non-trivial tier-3 sidecar)

→ COUNT(Q2-Q6, Q8) = 2 (Q2, Q4); + Q1 + Q7 = 4 questions total — fits one AskUserQuestion call. **Batch all 4.**

### Example 3 — `featured-products` (5 questions: Q1 + Q3 + Q5 + Q8 + Q7 → two calls)

Step 1 survey output: design `design/src/sections/featured-products/featured-products.html`. Name fine. Grid of 4 product cards. No animation. Two existing src snippets candidate: `featured-collection` (single-collection iterate) and `featured-products` (no existing section but matches the design's name).

Evaluation:
- **Q1 name: FIRE** (always) — `featured-products` already feature-generic (feature + layout = `featured-products-grid`); lead with Keep `featured-products` (Recommended), offer `featured-products-grid`
- Q2 blocks: SKIP (no merchant-added blocks, the 4 cards come from collection data)
- Q3 data: **ASK** — single collection picker vs collection_list vs per-card block override → 3 real options
- Q4 animation: SKIP (static)
- Q5 variant: **ASK** — reuse existing `featured-collection` section vs author new `featured-products` (2 candidates, schema compatibility unclear — exactly the case PLAN has marked ❓)
- Q6 scheme: SKIP (design clearly cream)
- **Q7 CSS strategy: FIRE** (always fires; product-card visual archetype matters here)
- Q8 layout: **ASK** — 4 identical product cards in a raw-CSS 2×2 grid → recommend the `layout` system (merchant could flip grid↔carousel). SKIP only if items aren't a homogeneous collection

→ COUNT(Q2-Q6, Q8) = 3 (Q3, Q5, Q8); + Q1 + Q7 = 5 questions total. That's over the 4-per-call cap, so **split into two AskUserQuestion calls** — e.g. call 1 = Q1 + Q3 + Q5 + Q7 (the name + reuse-shaping batch), call 2 = Q8 (layout) — rather than dropping any.

→ COUNT(conditional: Q3, Q5, Q8) = 3 + Q7 = 4 questions total. **Batch 4 questions.**

## Integration with downstream steps

After the clarify protocol returns:

1. **Step 2 (variant audit)** — uses Q5 answer (if asked) as the starting point. Steps A/B still walk normally; step C still asks if needed.
2. **Step 3 (section composition)** — uses Q1 (name → file paths), Q2 (block strategy → schema shape), Q3 (data source → settings + markup), Q4 (animation → whether to wire `<xo-magnetic>` / `data-parallax` / etc.).
3. **Step 4 (settings)** — Q3 informs which settings exist.
4. **Step 5 (JSON template)** — Q1 informs the section type referenced.
5. **Preview / PLAN update** — surface every answer the protocol DIDN'T ask but auto-decided (scheme, placeholder, wrapper) so the user can catch silent wrong choices.

## Anti-friction safeguards

- **Never batch more than 4 questions.** If 5+ would trigger, the section is too ambiguous for a single interview — pause, ask the user to clarify the design first, or break the section into smaller ports.
- **Always lead with one option + reasoning.** The first option in `AskUserQuestion` is the visual default; lean into that with a sentence explaining why.
- **Don't re-ask within a session.** If Q1 was asked for `hero-collage` already, don't ask Q1 again when porting `hero-collage`'s related sub-section the same session.
- **Honour user overrides.** If the user says "just do it", "skip questions", "tự quyết", or any equivalent, skip the protocol and proceed to Step 2 — trust the override.
- **Phrase from observation, not from the template.** If the agent finds itself writing `{N}` or `[{describe motion}]` into the actual question text, it hasn't done the observation step — stop, re-read the design, then phrase.

## When this protocol is wrong for a port

Some ports legitimately need more than 4 questions because the design is genuinely complex (e.g. bundle-builder with custom variant pricing). In that case:

1. Skip this protocol.
2. Hand off to the user with a freeform "I see N architectural decisions to make: [list]. Which do you want to lock first?"
3. Iterate question-by-question with the user instead of batching.

This protocol is for the 80% case (clean port with 0-3 ambiguities). The 20% case is a freeform design discussion.
