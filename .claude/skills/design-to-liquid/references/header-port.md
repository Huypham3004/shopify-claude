# Header port — adapt the ONE header to the design

A design header is not ported like other sections. Other sections are usually written fresh into
`src/sections/<name>/`; the header already exists as shared infrastructure and the job is to make it
**match** the design — by picking/tuning a layout of the single `header` section, not by adding a section.

Footers follow the same model — see `./footer-port.md` (it reuses everything below except the
header-specific patterns in §6–§9).

## Contents

1. Why there is exactly one header section
2. Architecture — dispatcher + `layout` setting + layout snippets
3. Decision ladder A–D
4. Adding a new layout (step D, after the user approves)
5. Schema rules for the merged header schema
6. `header-action` — the shared right-side cluster
7. Mobile menu patterns
8. Mega-menu wiring
9. Absolute (float-over-hero) mode
10. Build / deploy gotchas
11. QA checklist

---

## 1. Why there is exactly one header section

Shopify's `limit: 1` is enforced **per section type**. If the theme ships `header`, `header-editorial` and
`header-overlay` as three section types, each with `limit: 1`, a merchant can still add or un-hide all three
at once. The Theme Store rejects that (ledger **SF-SECTION-01** in `theme-store-review`: "Multiple header or
footer sections cannot be added or activated simultaneously").

So the header group contains **one** header section type. The merchant switches the look with a `layout`
select inside it. The editor's "Add section" picker then shows `Header (1/1)` disabled — that is the
observable pass condition.

Consequence for porting: **never** create `src/sections/header-*`, and never create a second section folder
under `src/groups/headers/` for a header look. A new look is a new *layout* of the existing section.

## 2. Architecture — dispatcher + `layout` setting + layout snippets

```
src/groups/headers/header/
├── header.liquid        # dispatcher only
├── header.global.scss   # styles of the Default layout (+ shared .xo-header-section rules)
└── schema.js            # ONE merged schema: `layout` select first, per-layout settings guarded

src/snippets/header-layout/
├── header-default/header-default.liquid
├── header-editorial/header-editorial.liquid (+ .global.scss, .script-global.ts)
└── header-overlay/header-overlay.liquid   (+ .global.scss)
```

The dispatcher:

```liquid
{%- case section.settings.layout -%}
  {%- when 'editorial' -%}
    {% render 'header-editorial' %}
  {%- when 'overlay' -%}
    {% render 'header-overlay' %}
  {%- else -%}
    {% render 'header-default' %}
{%- endcase -%}

{% render 'header-ld-json' %}
```

- Layout snippets take **no parameters** — they read `section.settings` / `section.blocks` directly
  (`section` is available inside a snippet rendered from a section). Their doc header says so
  ("Takes no parameters") and names the `layout` value that renders them.
- Anything rendered once per header regardless of layout (`header-ld-json`) lives in the dispatcher, not in
  each snippet — otherwise it's easy to emit it twice or forget it in a new layout.
- Each layout keeps its own BEM root (`.xo-header`, `.xo-header-editorial`, `.xo-header-overlay`), so layout
  SCSS never collides. Don't style via the section wrapper class (`xo-section-header`) — it's shared by all
  layouts.

**Where each layout's SCSS lives:** the Default layout's styles stay in the section folder
(`src/groups/headers/header/header.global.scss` — historical, it predates the layout split); every other
layout's styles sit next to its snippet (`src/snippets/header-layout/header-<layout>/header-<layout>.global.scss`).
Restyling a layout = editing that one file.

Before touching anything, read the current `layout` options in `src/groups/headers/header/schema.js` — the
list grows over time; the three above are the state when this reference was written.

## 3. Decision ladder A–D

Survey the design header first (Step 1 still applies: read the design's `sections/header*/` HTML + SCSS
**and** every existing layout snippet + its SCSS). Then compare archetypes — what makes a header a
different layout is **structure**, not paint:

| Archetype signal | Example |
|---|---|
| Logo position + menu placement in one bar | Default (logo left/center, horizontal menu) |
| Two rows: brand bar + column nav | Editorial |
| Floating pucks + full-screen menu | Overlay |

| Step | Action | When |
|---|---|---|
| A | Change defaults in `src/groups/headers/header-group.json` (`layout`, sticky, color scheme, logo position, absolute…) | The design is an existing layout and an existing setting already produces it |
| B | Restyle the matching layout's SCSS in place (`header.global.scss` or `header-layout/header-<layout>/*.global.scss`) | Same structure, different paint: typography, color, spacing, pill/glass chrome. Most common. Follow "Scope-style mirror rules" in `./sections-to-liquid.md` |
| C | Add ONE setting to the merged schema (guarded by its layout) + read it in that layout's snippet | The design needs a toggle no setting covers |
| D | **STOP — ask the user** | The design's structure matches no layout → it needs a new layout (§4), or markup changes to an existing layout snippet that other presets use |

Why D stops: a new layout or markup change ships to every preset/store that uses the theme, adds settings
merchants see, and is expensive to undo. The user decides; the agent proposes (layout name by archetype,
what it reuses, which settings it needs).

**Restyle scope (step B) — replace the look, or add a sub-brand variant?** A layout snippet is shared by every
preset that selects it. Before editing its SCSS, check which presets/stores use that layout
(`header-group.json`, `demo-live/*/`, PLAN/PROGRESS notes):

- The design **is** the layout's look (no other preset relies on the current paint) → edit the layout SCSS in place.
- Another preset already uses this layout with a different look → scope the new paint under that preset's
  root class (`body.theme-<x> .xo-header-editorial …`, class from `settings.root_class_name`), leaving the
  existing look untouched.

When it's unclear, fold it into the Q1 question ("restyle Editorial for everyone, or only under theme-kids?").

**Q7 (CSS strategy) for a header/footer port** still fires. Because a layout snippet is shared markup, the
sensible default is **SCSS-first in the layout's `.global.scss`**; XO-CSS atomic classes would mean editing the
snippet's markup, which is step D territory. Say that in the question so the user isn't choosing blind.

**System-upgrade checkpoint** (SKILL.md "before modifying shared infrastructure"): this reference *is* the
documented pattern for header/footer, so the checkpoint is satisfied — don't stop for it. Only pause for it if
the port needs something this file doesn't cover (e.g. a new dispatcher mechanism).

**Design folder names don't decide anything.** The part after `header-` is whatever the designer typed — a
number (`header-1`), a preset (`header-kids`), or any arbitrary word (`header-aurora`, `header-v2-final`);
some designs don't use the prefix at all (`topbar`, `site-nav`). The name only identifies which design file
you're porting. Two differently-named design headers can share one layout
(`header-1` and `header-kids` both two-row → Editorial), and the same name in another design repo can mean a
different structure. Always map by structure, and never reuse the design folder name as a layout value
(`header-2` → a layout called `2`/`header-2` tells the next merchant nothing).

Sub-brand / numbered looks (`header-kids`, `header-sound`, `header-2`…) are **not** layouts by themselves. If a
sub-brand differs only in paint, it is step B (a `body.theme-*` cascade or preset defaults). It becomes a
layout only when its structure is new — and then it's named by archetype (`header-kids` → `editorial`,
`header-sound` → `overlay`), so it stays reusable by any preset.

## 4. Adding a new layout (step D, after the user approves)

1. **Snippet** — `src/snippets/header-layout/header-<archetype>/header-<archetype>.liquid` (+ its
   `.global.scss`, + `.script-global.ts` if it needs JS). Doc header: layout name + "Takes no parameters".
   Copy the shape of an existing layout snippet: `{% liquid %}` prelude reading `section.settings`, then markup.
   Don't include `header-ld-json` (the dispatcher renders it).
2. **Dispatcher** — add a `when '<archetype>'` branch in `header.liquid`.
3. **Schema** — add the option to the `layout` select and update its `info` text; add only the settings this
   layout genuinely needs, following §5.
4. **Group JSON** — if the design should ship with it, set `"layout": "<archetype>"` (and its settings) on the
   existing `header` entry in `header-group.json`. Never add a second header entry.
5. Validate + build + QA (§10, §11).

## 5. Schema rules for the merged header schema

- **`layout` comes first**, with a short `info` that says what each layout looks like (merchants pick from it).
- **Guards as named constants**, so intent is readable and conditions stay consistent:
  ```js
  const IS_DEFAULT = visible("layout", "default");
  const NOT_DEFAULT = visible("layout", "default", true); // third arg true → "!="
  ```
  Combine with `.and(...)`: `IS_DEFAULT.and("height_enabled", true)`. `visible_if` also works on
  `type: "header"` settings, so hide a whole heading group when its layout isn't selected.
- **One id per concept, shared across layouts**: `sticky`, `color_scheme`, `menu`, `show_currency`,
  `show_language`, `show_search`, `show_account`, `customer_account_menu`, `show_cart`, and the absolute group
  (§9). A shared id keeps the merchant's value when they switch layout.
- **Layout-specific settings are guarded**: e.g. `header_style`, `logo_position`, `menu_type`, `event_type`,
  `inverse_logo` → Default only; `logo_type`, `wordmark`, `logo_width` → not Default; `meta_text` (tagline) →
  Editorial only.
- **Same id, different type across layouts** → keep the more permissive type. `wordmark` was `text` in one
  layout and `inline_richtext` in another → `inline_richtext` (plain text is still valid input; the liquid
  just outputs it).
- **Different defaults across layouts** (e.g. Overlay wanted `sticky: none`, `absolute: true`) can't coexist in
  one schema. Keep the Default layout's defaults; ship the other layout's values via the group JSON when it's
  the active layout.
- **Blocks can't be hidden per layout.** If a block type only works in one layout (Default's `bubble`), add a
  `paragraph` setting inside the block saying so.
- **`deviceSetting()` before every per-device range.** A range with `devices: ["desktop","mobile"]` only splits
  into `<id>_desktop` / `<id>_mobile` when a setting whose id starts with `device` precedes it
  (`getDeviceField()` in `create-schema.js` walks backwards). Without it the liquid reads ids that never exist
  and the width silently does nothing. With two device ranges in one schema, give one an `idSuffix`
  (`deviceSetting({ idSuffix: "_size" })` → `device_size`) — each range pairs with the nearest preceding one.
- Run `validate-schema.py src/groups/headers/header/` after every edit, and `validate-templates.py --all`
  after removing/renaming a setting (the group JSON stores setting values too).

## 6. `header-action` — the shared right-side cluster

`src/snippets/header/header-action/` renders currency / language / search / account / cart — icons only.
Every layout renders its right side through it:

```liquid
{% render 'header-action',
  show_search: show_search, show_account: show_account, customer_account_menu: customer_account_menu,
  show_cart: show_cart, show_currency: show_currency, show_language: show_language %}
```

The hamburger and its menu belong to the **layout**, not to `header-action`: Default renders
`xo-menu-hamburger-1` + `menu-hamburger`; Editorial its own drawer trigger; Overlay its MENU trigger. Don't
hand-write search/cart/account buttons in a layout. Currency/language inside `header-action` are desktop-only;
on mobile they live in the layout's menu (§7).

Icon names: the `icon` dispatcher uses `account` (not `user`), `hamburger` (lucide `menu`), `close` (lucide
`x`), `cart-bag` (lucide `shopping-bag`).

## 7. Mobile menu patterns

- The mobile menu is the layout's own `<xo-modal>` (drawer or full-screen); its content is scheme-driven with
  its own `color-{{ color_scheme }}` class (modals portal out of the header subtree, so they don't inherit it).
- Currency/language on mobile go **inside** that modal:
  `{% render 'currency-select', selector_position: 'footer', popover_name: '<layout>-currency-mobile' %}`
  (a unique `popover_name` + the `footer` position avoid id/trigger collisions with the desktop instances).
- A link with sub-links → `<xo-collapse-provider>` / `<xo-collapse-trigger>` / `<xo-collapse>` accordion, and
  render **grandchildren too** (level 3), not just children.
- A link with a mega-menu → a drill-in slide modal containing `<xo-mega-menu>`. Mega wins when both exist;
  since mega presence is only known at runtime, gate with CSS:
  `.__item:has(.__mega:not(:empty)) > .__collapse-trigger { display: none }` (+ show the mega trigger).
- Many top-level items: let desktop columns wrap (`repeat(auto-fit, minmax(14rem, 1fr))`) and hand off to the
  mobile menu earlier (`<lg`). Don't use `xo-scroll-carousel` for nav — its `overflow: hidden` clips drop-downs.

## 8. Mega-menu wiring

Desktop: emit `<xo-mega-menu xo-name="header-mega-menu" xo-index="{{ forloop.index0 }}"></xo-mega-menu>` per
top-level link, exactly like `menu-horizontal`. It reuses the `megamenu-*` sections already in
`header-group.json` (keyed by `index_nav`) — full dispatch model in `./mega-menu.md`. For a full-bleed panel,
use `xo-measure` + `xo-measure-parent-selector` on the `<li>`. When the mega panel has content, hide the plain
text drop-down (`.__mega:not(:empty) ~ .__col-panel { display: none }`).

## 9. Absolute (float-over-hero) mode

All layouts share one settings group (ids identical across layouts): `absolute`, `absolute_for_all`,
`absolute_for__index` / `__product` / `__collection` / `__list-collections` / `__blog` / `__other`,
`target_pages`, `color_scheme_absolute`, `background_opacity`, `background_blur`.

- Per-page toggles are guarded `visible("absolute", true).and("absolute_for_all", false)` — they're
  meaningless when "All" is on. (The merged schema initially kept the Default layout's looser guard; editor-qa
  caught it.)
- Each layout snippet computes `header_absolute` in its prelude by walking `template.name` against
  `index,product,collection,list-collections,blog` (`section.settings['absolute_for__' | append: suffix]`) plus
  `target_pages` for "other" — copy the prelude from an existing layout, don't re-derive it.
- Positioning: a relative `-section` wrapper stays in flow; only the inner element gets `--absolute`
  (`position: absolute; top: 0; left: 0; right: 0`). Never put `position: absolute` on the outer wrapper.
- The translucent bar paints from inline `--bg-color` (opacity) + `--bg-overlay-blur`, consumed only under
  `--absolute`.

## 10. Build / deploy gotchas

- Layout snippets **must live under `src/snippets/`**. The snippet processor only scans `src/snippets/**` and
  `src/pages/*/snippets/**`; a `snippets/` folder under `src/groups/` is ignored (and excluded from section
  processing), so the render silently finds nothing.
- `{% content_for 'blocks' %}` is not allowed inside a snippet — keep it in the section/dispatcher.
- `*.global.scss` under `src/snippets/**` is auto-imported into `src/styles/global.scss` on build;
  `*.ts` under `src/snippets/**` is loaded by `src/utils/import-snippets.ts`. Moving a layout's files from
  `src/groups/` to `src/snippets/` needs no import edits.
- `npm run build` does **not** delete compiled files of a removed section. Delete the stale
  `shopify/sections/<old>.liquid` locally, and remember `npm run push*` uses `-n` (no-delete): a removed
  section type stays on the store — and stays addable — until it is deleted there (Edit code) or pushed once
  without `-n`. `shopify theme dev` mirrors deletions to the dev theme.
- When consolidating sections in `header-group.json`, carry the removed entries' configured values into the
  remaining `header` entry (they're dormant until that layout is chosen) and drop the old keys from `order`.
  Keep the file's existing formatting (one-line string arrays) so the diff shows only real changes.

## 11. QA checklist

Run `/editor-qa` on the header after any layout/schema change and check:

- [ ] Header group's "Add section" picker shows `Header (1/1)` **disabled**, and no other header type is listed.
- [ ] For each `layout` value: the panel shows only that layout's settings (no Default-only fields under
      Editorial, no Tagline under Overlay, etc.), and the preview renders that layout.
- [ ] `logo_type = image` reveals Device + width; the width reaches the logo (`--w-desktop` / `--w-mobile`).
- [ ] Absolute on → header floats over the first section (`position: absolute`, transparent at opacity 0).
- [ ] **Mobile (360px) with a very long store name** — Theme Store reviewers test with one. Logo must not
      overlap or touch the actions; no horizontal scroll. (Overlay's logo puck broke here: a ~60-char name
      wrapped into a 178px-tall puck flush against the menu puck.)
- [ ] Mobile menu opens, sub-links expand to level 3, currency/language present inside it.
- [ ] Switching layouts back leaves Save disabled (no stray staged changes) when values were restored.
