# Footer port — adapt the ONE footer to the design

Same model as the header (read `./header-port.md` §1–§5 and §10 first — the reasoning, decision ladder,
schema rules and build gotchas are shared). This file covers what is specific to the footer.

## 1. Architecture

```
src/groups/footers/footer/
├── footer.liquid        # dispatcher only
├── footer.global.scss   # styles of the Default layout
└── schema.js            # ONE merged schema: `layout` select first, per-layout settings guarded

src/snippets/footer-layout/
├── footer-default/footer-default.liquid    # letter cluster + newsletter + link columns + giant wordmark
├── footer-campaign/footer-campaign.liquid  # image banner + button, brand column + link columns
└── footer-compact/footer-compact.liquid    # brand mark + tagline + link columns + base row
```

```liquid
{%- case section.settings.layout -%}
  {%- when 'campaign' -%}
    {% render 'footer-campaign' %}
  {%- when 'compact' -%}
    {% render 'footer-compact' %}
  {%- else -%}
    {% content_for 'blocks' %}
    {% render 'footer-default' %}
{%- endcase -%}
```

**Where each layout's SCSS lives:** Default → `src/groups/footers/footer/footer.global.scss` (section folder,
historical); Campaign / Compact → `src/snippets/footer-layout/footer-<layout>/footer-<layout>.global.scss`.
Restyle scope (replace the look vs `body.theme-*` sub-brand variant), Q7 default (SCSS-first) and the
system-upgrade checkpoint follow `./header-port.md` §3 exactly.

Differences from the header dispatcher:

- **Each layout snippet owns its section wrapper** — it ends with `{% render 'section', content: content %}`
  (or `container: false` when the layout manages its own `<xo-container>`, like Campaign) and emits its own
  `<xo-sticky-hidden xo-name="sticky-hidden">`. That's why the wrapper stays in the snippet: layouts differ in
  whether they want the container.
- `{% content_for 'blocks' %}` stays in the dispatcher — it is not allowed inside a snippet.
- Design footer folders are named however the designer chose — `footer`, `footer-1`, `footer-parfum`, or any
  arbitrary `footer-<word>`, sometimes no prefix at all (`bottom-bar`). The name only identifies the design file; map each to
  a layout by **structure**, exactly like headers (`./header-port.md` §3), and never use the folder name as a
  layout value. Read the current `layout` options in `schema.js` before
  deciding — the list grows.

## 2. Decision ladder

Same A–D as `./header-port.md` §3, with footer targets:

| Step | Footer action |
|---|---|
| A | Change defaults on the single `footer` entry in `src/groups/footers/footer-group.json` (`layout`, copy, toggles, padding) |
| B | Restyle the layout's SCSS (`footer.global.scss` or `footer-layout/footer-<layout>/*.global.scss`) |
| C | Add ONE guarded setting + read it in that layout's snippet |
| D | **STOP — ask**: new layout (new structure) or markup change to an existing layout snippet |

Structure signals that separate footer layouts: is there a hero-like banner (Campaign)? a newsletter + letter
copy cluster and an oversized wordmark (Default)? just brand + columns + base row (Compact)? Paint-only
differences (palette, type, spacing) are step B.

## 3. Schema rules specific to the footer

Guards used in `footer/schema.js`:

```js
const IS_DEFAULT  = visible("layout", "default");
const IS_CAMPAIGN = visible("layout", "campaign");
const IS_COMPACT  = visible("layout", "compact");
const NOT_DEFAULT = visible("layout", "default", true);
const NOT_COMPACT = visible("layout", "compact", true);
```

- **Shared by every layout:** the `link_list` block type (one column per block), `show_currency`,
  `show_language`, `show_payment`, and `...sectionSchemaSettings()` (color scheme, width, padding, background).
- **Shared by some layouts — guard with the negative constant:** `show_social_media`, `show_follow_on_shop`
  (`NOT_COMPACT`); `logo_type`, `logo_image`, `logo_text` (`NOT_DEFAULT` — Campaign + Compact).
- **One layout only:** letter copy, `show_newsletter`, `wordmark_*`, `show_policy` (Default); `banner_*`,
  button settings via `buttonNormalSchemaSettings({ link_enabled: true, visible_if: IS_CAMPAIGN })`,
  `brand_note` (Campaign); `tagline`, `base_note` (Compact).
- Reusable helpers accept a `visible_if` input (`buttonNormalSchemaSettings`, most `_base/input-settings`) —
  pass the layout guard instead of re-declaring their settings by hand.
- `logo_text` was `text` in one layout and `inline_richtext` in another → kept `inline_richtext`.
- `sectionSchemaSettings()` has one set of defaults for all layouts. Compact wanted 80/40 padding; that value
  ships through the group JSON, not the schema default.

## 4. Footer-specific patterns

- **Newsletter** — Default renders `{% render 'email-signup-footer' %}`. The form's email input needs a
  validation `pattern` + `title` (`customer.subscribe.error_text`); see `theme-store-review` for the newsletter
  validation requirement. Check the snippet param name before passing attributes (`field-text` /
  `field-input` read `attrs`, not `attr`).
- **Link columns** — iterate `section.blocks` with `{% case block.type %}`, put `{{ block.shopify_attributes }}`
  on each column, and size the grid from the block count (`--xo-col-desktop` capped at 3–4).
- **Locale + payment row** — `currency-select` / `language-select` with `selector_position: 'footer'` (opens
  upward); payment icons via `shop.enabled_payment_types | payment_type_svg_tag`; policies via `shop.policies`.
- **Copyright** — `&copy; {{ 'now' | date: '%Y' }} {{ shop.name }}` + `{{ powered_by_link }}`.
- **Two-tone / italic wordmark** (e.g. roman brand + italic word) needs no new setting: `wordmark_text` /
  `logo_text` are `inline_richtext`, so the merchant italicises the word and the global heading-emphasis rule
  (`src/styles/base/content.scss`, `em` → sub font) styles it. Only add a setting if the design needs something
  `<em>` can't express.
- Text logo / wordmark falls back to `shop.name`; test with a very long store name (it must wrap or scale
  without overflowing the column on mobile).

## 5. QA checklist

Run `/editor-qa` on the footer and check:

- [ ] Footer group's "Add section" picker shows `Footer (1/1)` **disabled**, no other footer type listed.
- [ ] Each `layout` value shows only its own settings and renders its own markup.
- [ ] Adding/removing a link-list block changes the column count in every layout.
- [ ] Newsletter: an incomplete email (`abc@abc`) shows the validation message.
- [ ] Mobile (360px): columns stack per the design, no horizontal scroll, long store name doesn't overflow.
