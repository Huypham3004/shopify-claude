# Sections → Liquid Sections

Convert a design section HTML file into `src/sections/<name>/<name>.liquid` + `schema.js`.

## File Layout

For a section named `<name>`:

```
src/sections/<name>/
├── <name>.liquid          # render output (this skill)
├── <name>.global.scss     # optional section-scoped SCSS (`scss` skill)
├── schema.js              # createSectionSchema (`schema` skill)
└── preset-1.js            # optional preset definitions
```

> [!IMPORTANT]
> **SCSS naming convention:** every `xxx.liquid` pairs with `xxx.global.scss` in the same folder — both for sections (`src/sections/<name>/<name>.global.scss`) and for snippets (`src/snippets/<name>/<name>/<name>.global.scss`). Do NOT use the legacy `section-<name>.scss` prefix; the project auto-imports `*.global.scss` via the SCSS glob plugin.

## Anatomy — The `{% render 'section' %}` Wrapper Pattern

> [!IMPORTANT]
> **This project uses a section-wrapper snippet (`src/snippets/_base/section/section.liquid`).** Always wrap your section body with `{% render 'section', content: content %}` instead of hand-writing `<section class="xo-section">`, `<xo-container>`, color-scheme class, background, padding, etc. The wrapper handles all of that based on settings from `sectionSchemaSettings()` (see `src/snippets/_base/section/schema.js`).
>
> Equally important — your section schema must spread `...sectionSchemaSettings({...})` so the merchant gets the standard width / height / color scheme / background / padding / decoration controls in the Theme Editor.

### Canonical liquid file

```liquid
{% liquid
  assign overline  = section.settings.overline
  assign heading   = section.settings.heading
  assign cta_label = section.settings.cta_label
  assign cta_link  = section.settings.cta_link
%}

{%- capture content -%}
  <div class="xo-{{ name }}__inner">
    {%- if overline != blank -%}
      <p class="xo-{{ name }}__overline">{{ overline }}</p>
    {%- endif -%}
    {%- if heading != blank -%}
      <h2 class="xo-{{ name }}__title">{{ heading }}</h2>
    {%- endif -%}
    {%- if cta_label != blank -%}
      {% render 'button', text: cta_label, link: cta_link %}
    {%- endif -%}
  </div>
{%- endcapture -%}

{% render 'section', content: content %}
```

For a section with repeated children driven by blocks, capture the items list and pass it through a `layout` snippet (grid/carousel/freedom) before the `section` wrapper:

```liquid
{%- capture items -%}
  {%- for block in section.blocks -%}
    <xo-item {{ block.shopify_attributes }}>
      {%- render 'product-card', product: block.settings.product -%}
    </xo-item>
  {%- endfor -%}
{%- endcapture -%}

{%- capture layout -%}
  {%- render 'layout', content: items, context: section -%}
{%- endcapture -%}

{%- capture content -%}
  {%- if heading != blank -%}<h2 class="xo-{{ name }}__title">{{ heading }}</h2>{%- endif -%}
  {{ layout }}
  {%- content_for 'blocks' -%}
{%- endcapture -%}

{%- render 'section', content: content -%}
```

Pattern source: `src/sections/product-list/product-list.liquid` is the canonical reference.

### Canonical schema file

```javascript
import { createSectionSchema } from "../../create-schema.js";
import { sectionSchemaSettings } from "../../snippets/_base/section/schema.js";
// import { layoutSchemaSettings } from "../../snippets/_layout/layout/schema.js";  // if using layout

export const schema = createSectionSchema({
  name: "<Display name>",
  class: "section-<name>",
  settings: [
    { type: "header", content: "Content" },
    { type: "text",            id: "overline", label: "Overline" },
    { type: "inline_richtext", id: "heading",  label: "Heading" },
    // …per-section content settings

    // Width / height / color scheme / background / padding / decoration —
    // standard section chrome controls. Overrides via `input`:
    // NOTE: `padding_top`/`padding_bottom` here are INPUT defaults, NOT setting
    // IDs. The emitted IDs are `top_padding_desktop`, `bottom_padding_desktop`, …
    // (range 0–100). In `preset-N.js` key on those real IDs, or omit padding
    // (this input already set the default). Never put `padding_top` in a preset —
    // it matches nothing and is silently dropped. See schema skill → preset.md.
    ...sectionSchemaSettings({ padding_top: 80, padding_bottom: 80 }),

    // Grid / carousel / freedom layout controls (only when the section has a layout):
    // ...layoutSchemaSettings({ header: "Layout" }),
  ],
});
```

> The literal `<name>` placeholder above is *for this template only*. In the real file, hardcode the section's actual name into class strings.

### What the `section` snippet wraps you with (automatic)

- `<div class="xo-section xo-section--<section.id> color-<scheme>">` outer
- `{% render 'bg', context: section %}` — background color / gradient / image / video / parallax / overlay (all from settings)
- `<xo-container class="xo-container">` with custom container_gap / width if set
- Section padding via class + CSS variables
- Width / height CSS variables (`--xo-container-width`, `--height`)
- Border attributes
- Top / bottom decorations (when `decoration_enabled`)

You write **only the inner content**.

## Mapping Rules

### 1. Top-level `<section>` tag — DON'T write it

Design pattern:
```html
<section class="xo-section xo-<name>" data-section-path="…">
  <xo-container>
    <!-- ... -->
  </xo-container>
</section>
```

Liquid — **do NOT replicate this**. Wrap your inner content with `{% render 'section', content: content %}`. The wrapper emits the outer element, `xo-section` class, color scheme class, container, background and padding for you.

- Drop `data-section-path` (design-time inspector hook).
- The `xo-section xo-<name>` outer is handled by the wrapper (it adds `xo-section--<section.id>` and the optional color-scheme class automatically).
- Section padding values are NOT inlined as `--section-pt`/`--section-pb` style on `<section>`; they come from the section's `top_padding_desktop/...` settings (the `paddingAttrsSchemaSettings` block inside `sectionSchemaSettings()`).

### 2. xo-webcomponents pass through

`<xo-container>`, `<xo-grid>`, `<xo-item>`, `<xo-carousel>`, `<xo-animate>`, `<xo-marquee>`, `<xo-modal>`, `<xo-sticky>`, `<xo-magnetic>`, `<xo-image>` (and friends) work the same in liquid because the runtime script loads them in `src/layout/theme.liquid`. No conversion needed.

When you need to understand a web component's attributes/slots, query the **`xo-components` MCP** server.

> [!IMPORTANT]
> **Exception — `xo-collection-tabs` is NOT pass-through.** A design section with a row of tabs above a product-card grid (each tab = a collection) ships *static* tabs (`xo-tabs` or a button/pill row) that must be **converted** to the `xo-collection-tabs` / `-trigger` / `-content` trio + Section Rendering API wiring — passing them through unchanged yields a dead section. See `references/collection-tabs.md`.

### 3. `<xo-component>` → `{% render %}`

```html
<!-- design -->
<xo-component src="button" data="{
  href: '/some/link',
  label: 'Click me',
  variant: 'primary'
}"></xo-component>
```

```liquid
{# liquid #}
{% render 'button', link: '/some/link', text: 'Click me', variant: 'primary' %}
```

> [!IMPORTANT]
> **Parameter names rarely match 1:1.** The design's data keys (`label`, `href`, etc.) are its own contract. The src snippet has its own parameter names (`text`, `link`, etc.). **Always read the existing src snippet's liquid-doc** for the correct param names — don't copy design data keys blindly.

> A common case: a `section-heading` component (overline + title + intro). Override it to the project's `section-heading` snippet, never hand-write the header — see `components-to-snippets.md` § "Worked primitive — `section-heading`".

### 4. Hardcoded values → settings

Promote every hardcoded `<p>`, heading, link, image, count, choice into `section.settings.X` or `block.settings.X`.

→ See `./data-to-settings.md`.

> **When a promoted `<p>` becomes a `richtext` field, render it inside a `<div>` — not the original `<p>`.** `richtext` outputs its own `<p>`, so keeping the design's `<p>` wrapper yields invalid `<p><p>…</p></p>` (the browser auto-closes the outer `<p>`, detaching the class and breaking the layout — schema validation won't catch it). Swap `<p class="…">` → `<div class="… rte">`. For an `inline_richtext` field the original `<p>`/heading wrapper is fine. See `liquid` skill `references/gotchas.md` #32.

### 5. Repeating children → blocks

When the design renders N similar items via repeated `<xo-component>`s, convert to:

```liquid
{% for block in section.blocks %}
  <div class="xo-{{ name }}__item" {{ block.shopify_attributes }}>
    {# render block content #}
  </div>
{% endfor %}
```

Each block type + its settings are declared in `schema.js`.

### 6. Italic / emphasis inside copy

Patterns like `<h2>Some <em>word</em> here.</h2>` need an `inline_richtext` (or `richtext`) setting to preserve `<em>`. A plain `text` setting will escape the tag.

```javascript
{ type: "inline_richtext", id: "heading", label: "Heading",
  default: "Some <em>word</em> here." }
```

### 7. Class strings

Keep the design's BEM `.xo-<name>__element` names — that's the contract SCSS uses. If the SCSS doesn't yet exist, create `src/sections/<name>/<name>.global.scss` and write the styles.

## Audit Snippet Variants BEFORE Rendering (mandatory step)

> [!IMPORTANT]
> **Before calling `{% render 'X', … %}` in a new section, audit what variants the snippet ships and which one matches the design's intent.** The project's snippets are nearly-complete primitives — the right path 90% of the time is "pick the variant + pass the right params", not "write a CSS override in the section".

Concretely, when the design uses a component (button, product-card, article-card, image, etc.):

### 1. List the snippet's variants

```bash
ls src/snippets/<snippet>/
# e.g. for button: button-1/ button-2/ … button-7/ button-base/ button-icon-1/ button/ utils/
```

The `*-base/` folder is shared logic (don't render it directly). The numbered folders (`*-1`, `*-2`, …) are alternative visual implementations. Read each `.liquid` to know what classes / animations / hardcoded styles it emits.

### 2. Read the design's intent for the component

From the design files (`<design>/components/<name>/<name>.scss` and any blueprint), extract:

- Shape — pill / rounded / square / circle (border-radius)
- Fill vs outline vs ghost / link
- Animation on hover (subtle opacity vs heavy text-split vs fill-up vs lift)
- Icon position (before / after / icon-only)
- Color scheme (primary fill vs neutral)

### 3. Trace each visual property: hardcoded vs settings-driven

In every variant's `.liquid`, look at the `container_class` string. Properties baked in as `bdrs:s10|w`, `bgc:primary`, etc. are **hardcoded** — they cannot be overridden by theme settings. Properties that fall through to `button-base` → `border-attrs` / `padding-attrs` / `shadow-attrs` are **settings-driven** — they read from `block.settings.X` then fall back to `settings.X` (theme).

This trace tells you whether your design intent is reachable by configuring theme settings alone or whether you need to modify the variant.

### 4. Pick the closest match

For each design property, pick the variant whose:

- **Hardcoded styles match** (or are absent so they're settings-driven), AND
- **Settings-driven styles can be cascaded** from the active preset

If a clean match exists → use it via params, no snippet edit needed.

### 5. If no match — escalation ladder

Walk down the ladder; stop at the first step that fits. These are heuristics — exercise judgment:

| Step | Action                                                                                          | When it fits                                                                              | Author authority |
| ---- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------- |
| A    | **Configure via theme settings** (set a value in `preset-N.js` that an existing variant already reads) | A variant already reads the setting; it just needs the right value.                | Proceed.         |
| B    | **Modify the closest existing variant** (`<snippet>-N.liquid` / `.global.scss`)                 | The change is universally beneficial OR the variant is currently broken / inconsistent across themes. | Proceed if the change won't visually break other presets shipped in `src/config/presets/`; otherwise ask. |
| C    | **Add a new numbered variant** + register it in the dispatcher + global-schema                  | The design needs a visual archetype other themes shouldn't inherit, AND modifying any existing variant would break them. | **STOP — ask the user.** New variants ripple into the dispatcher, the Theme-Settings UI, and every preset that picks them. This is a design call, not Claude's call. |

When step C looks necessary, present the user with:

- Which variant was closest and what specifically doesn't match.
- Why steps A and B don't work (cascading wouldn't help; modifying would break another preset).
- The proposed new variant's intent in one sentence (e.g. "a primary CTA with no animation and pill radius for editorial restraint").
- Three options to choose from: (i) add the new variant, (ii) modify an existing one anyway and accept the ripple, (iii) defer and live with the closest match for now.

Do NOT silently create a new variant.

### 6. Anti-patterns to avoid

- **Section-scoped CSS overriding the snippet's `.xo-button` class** — the snippet then renders inconsistently across sections; future maintainers won't know where the override lives.
- **Hand-writing the component markup inside the section** — breaks the contract that the snippet owns the markup.
- **Adding "this design's button" as section-level settings** — button defaults belong in `global-schema/buttons.js` + `preset-N.js`, not in each section schema.
- **Editing `<snippet>-base/`** — base is shared by every variant; changes there ripple everywhere.

## Group port ladder (header / footer / popups / announcement-bar / overlay)

When the design section is structurally a **group**, NOT a free-standing section, the target lives under `src/groups/<group>/<name>/` (already exists — header, mega-menu, announcement-bar, main-predictive-search, footer, popups, overlays, features). The reuse ladder shifts:

| Step | Action                                                                                   | When it fits                                                                       | Author authority |
| ---- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------- |
| A    | **Tweak default settings** in `src/groups/<group>/<group>-group.json`                    | Existing schema already exposes the toggle (logo position, sticky, color scheme, action visibility, absolute mode per template) and the default just needs to change. | Proceed.         |
| B    | **Restyle SCSS in place** — edit `src/groups/<group>/<name>/<name>.global.scss`           | Visual aesthetic doesn't match — typography, color, padding, decorative chrome (pill card, glass blur, sticker borders). Most common case. | Proceed.         |
| C    | **Add ONE new schema setting** to `src/groups/<group>/<name>/schema.js` + consume in liquid | Design needs a behavior toggle that has NO existing setting (e.g. a new background mode). | Proceed if surgical (1-2 fields, doesn't conflict with existing settings); otherwise ask. |
| D    | **STOP — ask the user** before editing `<name>.liquid` markup or creating a new file       | Markup edits ripple to every theme instance; new file creation breaks the "override" assumption. Sub-brand variants belong in the SAME `.global.scss` via `body.theme-*` cascade, NOT a new folder. | **Never proceed silently.** |

**Why different from the snippet ladder:**
- Groups have NO numbered variants (`-1`, `-2`) — there is exactly ONE header section and ONE footer section.
- Groups ship with rich schemas already covering most port needs.
- Groups are referenced by `{% sections '<group>-group' %}` in `src/layout/theme.liquid` — file-name changes break the layout.

**Header and footer have their own, more specific ladder.** Each is a single section whose `layout` select
dispatches to layout snippets (`src/snippets/header-layout/header-<layout>/`,
`src/snippets/footer-layout/footer-<layout>/`). A design header/footer that differs only in paint is step B;
one whose structure matches no layout is a new *layout* (asked first), never a new section type — two
header/footer section types let merchants activate both, which the Theme Store rejects. Sub-brand designs
(`header-kids`, `footer-parfum`…) map to a layout named by archetype. Full rules: `./header-port.md`,
`./footer-port.md`.

**Mega menu has its own dispatch architecture** — see `./mega-menu.md`. Adding a mega-menu instance for a new top-level nav link is a `header-group.json` edit (add entry to `sections` map + `order` array with the right `index_nav`), not a markup change.

**Modal-shaped groups have their own port pattern** — see `./modals.md`. When the group contains an `<xo-modal>` (search, cart, quick-view, popups, compare):

| Step | Modal-specific action |
|---|---|
| A | Tweak modal section defaults in `<group>-group.json` (search blocks, cart settings) |
| B | Restyle SCSS scoped to `xo-modal[xo-name="X"]` — NEVER unscoped, will leak to sibling modals |
| C | Tweak `<xo-modal>` attrs in the modal's `.liquid` (`xo-animate`, `xo-placement`, `xo-backdrop-blur`) |
| D | Add ONE schema setting OR ONE block type — surgical |
| E | **STOP — ask user** before adding block types that require markup edits to shared rendering snippets (`predictive-search-base`, `predictive-search-suggest`, `cart-mini-item-*`) |

Reflex checklist for any modal port:
1. Run `grep -rn 'xo-name="X"' src/` to verify TRIGGER ↔ MODAL match (expect 2+ hits, ≥1 trigger + 1 modal)
2. Identify the dispatch path — predictive-search has `drawer|overlay` variants, cart-mini has `drawer|notification|page` variants
3. Use `modal-content` snippet as the inner shell (don't hand-write `<div class="xo-modal-content__inner">…`)
4. Scope every SCSS rule under `xo-modal[xo-name="X"]` — critical to avoid cross-modal regressions

## Scope-style mirror rules (for Group port ladder Step B)

When step B SCSS restyle scopes a section/group to override or supplement an existing snippet's visual (e.g., `.xo-header__right .xo-header-action__item` styled to mimic the `icon-button` primitive's ghost variant WITHOUT refactoring the markup to use the primitive), follow these 3 guideline rules. They prevent silent breakage that only surfaces after the merchant tries to customize OR when the same brand renders the primitive directly elsewhere.

### Rule 1 — Never override CSS properties driven by snippet schema settings

The snippet's SCSS often reads CSS variables emitted by the snippet's liquid `style="--X: {{ settingvalue }}"`. Audit the snippet's `.global.scss` for `var(--X)` references AND trace each back to its schema setting BEFORE adding a property override in scope-style. If the property is schema-driven, **scope-style must NOT hardcode it**.

Worked example (header port, 2026-05-28):
- `.xo-logo` width/height driven by `width_desktop`/`width_mobile` schema settings via `--w-desktop`/`--w-mobile` CSS vars (see `src/snippets/logo/logo.global.scss`).
- Initial header scope-style violation: `.xo-header .xo-logo { width: auto; height: auto }` to make the text-fallback wordmark sit naturally.
- Bug surfaced: merchant tweaks to logo width in Theme Editor had no effect. Override cut the schema → CSS-var → SCSS chain silently.
- Fix: remove the property override; keep only typography styling on `.xo-logo__title` (text styling, not a schema-driven dimension).

Apply pattern to any snippet whose SCSS contains `var(--`:
- `.xo-logo` → width/height
- `.xo-button` → height (from button size settings)
- `.xo-image` → aspect-ratio / object-fit (from image ratio settings)
- Run `grep "var(--" src/snippets/<name>/<name>/<name>.global.scss` to enumerate before scope-styling.

### Rule 2 — Breathing space goes on parent CONTAINER as `padding-top`, NEVER on child as `margin-top`

When adding vertical space between elements inside a group (above a pill, between sections), use `padding-top` on the parent CONTAINER, not `margin-top` on the child. Child margin pulls + complicates flex / sticky / absolute behavior; container padding owns the space cleanly within its bounds.

Worked example (header port, 2026-05-28):
- Initial: `.xo-header__inner { margin-top: 2rem; @include media('>md') { margin-top: 3rem; } }` — pill pulled its own breathing margin.
- Refactored to: `.xo-header__container { padding-top: 2rem; @include media('>md') { padding-top: 3rem; } }` — container owns the space; pill is unburdened.
- Why it matters: in absolute mode the pill's margin-top would propagate up to the header positioning (negative consequences for sticky behavior); container-owned padding stays contained.

### Rule 3 — Scope-style state values MUST mirror the equivalent primitive's variant SCSS

When step B mimics a primitive's visual via scope-style (instead of using the primitive snippet directly), every state's color/opacity/transition value MUST equal the primitive's variant SCSS. Drift causes visible inconsistency when both render side-by-side (e.g., header scope-style icons vs cart drawer close button rendered through the primitive on the same page).

Worked example (header port, 2026-05-28):
- `icon-button` primitive's ghost hover (per `src/snippets/icon-button/icon-button.global.scss`): `&:hover { background: color(background) }` (Folio cream tint).
- Initial header scope-style: `.xo-header__right .xo-header-action__item:hover { background: color(foreground, 0.06) }` (translucent black 6% = cool gray).
- Bug surfaced: user noticed the hover bubble color differed between the header search icon and other places where icon-button rendered directly.
- Fix: align scope-style to `color(background)` — mirror the primitive's variant value exactly.

Reflex when scope-styling to mimic a primitive: open the primitive's SCSS in a split view + copy hover/active/focus rules verbatim. Don't invent alternative tokens.

### Reflex checklist (Step B scope-style)

Before adding any property in scope-style:
1. Identify the primitive(s) the scope-style is mimicking. Open their `.global.scss`.
2. Grep `var(--` in the snippet's SCSS to enumerate schema-driven properties → AVOID overriding those.
3. For breathing space: use container padding, never child margin.
4. For state values (hover/active/focus): copy the primitive's exact token + opacity + transition.
5. Document non-obvious overrides with a comment explaining WHY (e.g., "intentional override of atomic op:0 because Folio overlay places result inline not floating").

**Concrete reflexes when porting any design header:**

1. **DO NOT create `src/sections/header/`** — open `src/groups/headers/header/` and read what's there first.
2. **DO NOT replace `header.liquid` markup** — it's already generic (3-column grid, logo position swap, mobile drawer modal trigger, sticky, absolute mode). Restyle SCSS instead.
3. **Find the right schema toggle BEFORE editing CSS** — sticky direction (`sticky: down`), action visibility (`show_currency: false`), absolute-over-hero per-template (`absolute_for__index: true`) — most "behavior" changes are settings, not code.
4. **Logo is text-fallback ready** — `src/snippets/logo/logo.liquid` renders `<span class="xo-logo__title">{{ shop.name }}</span>` when no image is uploaded. For wordmark-only designs (Folio "Folio" italic-serif), leave `default_logo` empty in settings and style `.xo-logo__title` in `header.global.scss`.
5. **Mobile drawer is `menu-hamburger` snippet** rendered inside `header-action` and triggered by `<xo-modal-trigger xo-name="xo-menu-hamburger-1">`. Restyle `menu-hamburger.global.scss`, don't write a new drawer.

### Worked example — button (illustrative; the actual variant set evolves)

> [!NOTE]
> **The variant names, hardcoded class strings, and behaviors below are a snapshot at the time of writing.** Re-audit the actual files when porting — don't memorize this mapping. The reasoning flow is what's portable.

Suppose the design wants a solid PILL primary CTA with restrained hover (opacity fade + small lift).

#### Step 1 — list variants

```bash
ls src/snippets/button/
```

Returns an entry-point dispatcher, a shared `button-base/`, and numbered variants. Each variant's `.liquid` paints a different visual.

#### Step 2 — read the design's intent

From the design's component SCSS: pill border-radius, md padding, primary variant fills the scheme's `button-background`, hover does an opacity fade + tiny `translateY(-0.1rem)`. No text animation.

#### Step 3 — trace hardcoded vs settings-driven (in each variant)

Read each variant's `container_class` string. Where you see `bdrs:s10|w` baked in, the radius is hardcoded and can't be overridden by a preset. Where the variant lets `button-base` resolve attrs via `border-attrs.liquid`, the radius falls through to `block.settings.border_radius` → `settings.border_radius` (theme).

(Don't memorize "variant N is hardcoded" — read the file.)

#### Step 4 — pick the closest match

Choose the variant whose hardcoded styles match the design AND whose settings-driven properties can be cascaded from the active preset.

#### Step 5 — escalate if needed

- A settings-driven variant exists → **step A**: set the right value in `preset-N.js`, pass `button_type: settings.buttons_type, variant: settings.button_variant` to the render. No snippet edit.
- The standard "primary CTA" variant hardcodes the wrong radius → consider **step B**: remove the hardcode so the variant respects `settings.border_radius`. Before editing, check whether other presets in `src/config/presets/` would visually break. If yes → ask the user.
- A genuinely new visual archetype is needed → **step C**: stop and ask the user before adding a new variant.

The audit is designed to land on step A whenever possible. The theme is written so most design intent is reachable through preset configuration.

## Restyling — fallback when the audit's escalation ladder finishes

The audit above usually lands you on **step A** (theme setting cascade) or **step B** (modify variant). The cases below are for residual small gaps that aren't worth a variant change.

When you render an existing snippet (e.g. `{% render 'product-card', product: … %}`) and a minor visual gap remains:

1. **First** — re-check the audit. Did you miss a snippet param (`card_color_scheme`, `corner_radius`, `style-1` / `style-2` / …)? **Most visual differences are one schema param away.**
2. **Second** — write section-scoped SCSS overrides in `<name>.global.scss`:
   ```scss
   .xo-<name> {
     .xo-product-card__title { font-size: …; }
     .xo-product-card__badge { background: …; }
   }
   ```
3. **Last resort** — add XO-CSS atomic class tweaks via a wrapper:
   ```liquid
   <div class="xo-<name>__card-wrap bdrs:s2">
     {% render 'product-card', product: product %}
   </div>
   ```
4. **Avoid** editing the snippet's liquid markup itself unless absolutely necessary — future design swaps will need to re-do the work.

## Schema Block

Note: this project's build pipeline **does NOT require a `{% schema %}` block** at the end of the liquid file — the schema is read from the sibling `schema.js` file at compile time. If you see other sections without `{% schema %}` at the bottom (e.g. `src/sections/product-list/product-list.liquid`), follow that pattern.

## Validate the schema.js after writing it

> [!IMPORTANT]
> **Every time you create or edit a section's `schema.js`, run the validator before reloading the Theme Editor.** Catches bugs the Shopify Editor would otherwise reject with hard-to-decode errors.
>
> Script lives WITH this skill: `.claude/skills/design-to-liquid/scripts/validate-schema.py`. From the project root:

```bash
# Default — validate one section's schema.js
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/

# Scan every section in the theme
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all

# Also validate a sibling preset against the schema (when one exists)
python .claude/skills/design-to-liquid/scripts/validate-schema.py --preset src/sections/<name>/preset-1.js
```

What the validator catches:

- `schema.js` fails to compile / dynamic-import (syntax error, wrong path, missing helper)
- Duplicate setting IDs inside `settings[]`
- Range settings without `min`/`max` (step optional, defaults 1)
- Select/radio settings without an `options` array
- **`inline_richtext` default contains a disallowed tag** (e.g. `<br>`, `<p>`, `<h1>-<h6>`, `<ul>`, `<ol>`, `<li>`, `<div>`, `<img>`). Allowed inline tags only: `em`, `strong`, `b`, `i`, `u`, `a`, `span`, `sup`, `sub`. For line breaks or paragraphs, switch the setting to `richtext` — its top-level node must itself be `<p>` / `<ul>` / `<ol>` / `<h1>-<h6>`. Or rely on CSS (`max-width: NNch` / `white-space: pre-wrap`) for the visual break.
- `richtext` default whose top-level node isn't `<p>` / `<ul>` / `<ol>` / `<h1>-<h6>`
- Block types declared in `schema.blocks: [...]` that don't resolve to any `src/blocks/**/<type>/` or `src/groups/**/<type>/` folder (and aren't `@theme` / `@app`)

Optional secondary modes (see `--help`):

- `--preset <path>` — cross-validate a section/block `preset-N.js` against its sibling `schema.js`. Catches *"Invalid preset: invalid block type 'product-media': undefined setting 'aspect_ratio'"* class of errors.
- `--theme` — sanity-check `shopify/config/settings_data.json` against `settings_schema.json`. Catches the `"current"-as-string` error and orphan color-scheme objects (see `./tokens-mapping.md`).

Script source: `.claude/skills/design-to-liquid/scripts/validate-schema.py` — moves with the skill when the `.claude/` folder is copied to another project. Resolves the project root by walking up to the nearest `package.json` + `src/` dir, so it works from any depth.

## SCSS Co-location

Section-scoped SCSS lives next to the section liquid, named to mirror the liquid file:

```
src/sections/<name>/<name>.liquid          # markup
src/sections/<name>/<name>.global.scss     # styles for it
```

The project's vite scss-glob plugin auto-imports every `*.global.scss` under `src/sections/` and `src/snippets/`. No manual `@import` needed.

For utility tweaks (margin, padding, color), prefer XO-CSS atomic classes inline (see the `xo-css` skill) over creating new SCSS.

## Pitfalls

| Pitfall                                                  | Fix                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------ |
| Hand-writing `<section class="xo-section">` + `<xo-container>` + padding + background | Don't. Use `{% render 'section', content: content %}` — see canonical anatomy above. |
| Forgetting `...sectionSchemaSettings()` spread in schema.js | The wrapper relies on settings (`color_scheme`, `bg_type`, `width`, padding, etc.). Without them, the merchant sees no chrome controls and CSS variables are blank. |
| Adding `{% schema %} {{ schema }} {% endschema %}` at the bottom | Not needed in this project — schema is auto-injected from `schema.js`. Match the existing sections' pattern. |
| Copying design's `data-section-path`                     | Design-time only — remove.                                         |
| Using design's `xo-component` data keys as render params | Read the src snippet's liquid-doc; key names usually differ.       |
| Forgetting `{{ block.shopify_attributes }}` on block roots | Required for Theme Editor block selection / highlighting.        |
| Putting copy with `<em>` in a `text` setting             | Use `inline_richtext` or `richtext` instead.                       |
| Hardcoding image URLs in the liquid                      | Lift to `image_picker` setting, render with the image snippet.     |
| Re-implementing a card snippet inside the section        | Render the existing snippet. SCSS override if look differs.        |
| For repeating items, hand-rolling a flexbox/grid wrapper | Use `{% render 'layout', content: items, context: section %}` and spread `...layoutSchemaSettings()` in your schema. |

## Related

- `./components-to-snippets.md` — rare case where a new snippet is needed
- `./data-to-settings.md` — designing the schema
- `./icons-and-images.md` — Lucide and image handling
- `schema` skill — `createSectionSchema` API
- `scss` / `xo-css` skills — the restyling toolkit
