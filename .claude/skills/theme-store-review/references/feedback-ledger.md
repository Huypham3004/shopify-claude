# Shopify Theme Store review — feedback ledger

Every comment Shopify's theme reviewers have sent back on one of our themes, one
entry per requirement. The ledger is **theme-agnostic**: an item recorded from
the Folio review applies to every theme built on the same base (Pawra, Hexon,
Ronin, Stray…), because reviewers re-test the same requirements on each submission.

**Rules for this file**

- Never delete an item. If Shopify stops flagging something, mark it `retired` in `Status`.
- New feedback round → append new items, or add a `Seen in` line to an existing
  item when the same requirement is flagged again (that raises its priority).
- IDs are stable: `SF-<AREA>-<NN>`. The scanner (`scripts/scan-feedback.py`) keys its
  checks on these IDs. Keep the two in sync.
- `Check` says how the item is verified: `static` (scanner can decide), `heuristic`
  (scanner flags candidates, a human/agent confirms), `runtime` (needs a browser —
  storefront or editor).

Sources:

| Round | Theme | Date received | Raw feedback |
|---|---|---|---|
| R1 | Folio | 2026-11 | `themes/shopify-feedback/shopify-feedback.md` |

---

## Stage 1 — Features and OS 2.0 compatibility

### SF-FILTER-01 — Zero-result filter values must be disabled
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** Collection and search pages support faceted filtering (availability, price, type, vendor, variant options). Filter values with `count == 0` must be disabled (not clickable). Selecting one must never lead to a "No products found" dead end. Values that are already active stay enabled so they can be unchecked.
- **Reviewer example:** `Digital product (boolean): No (0)` was selectable.
- **How to verify:** In the filter-value loop, look for a `value.count == 0` branch that sets `disabled` (or the component's disabled attribute). At runtime, apply a filter that makes another value drop to 0 and confirm it is still disabled **after the AJAX re-render**. Keyboard users must not be able to toggle it either (`input.disabled`, not only `pointer-events: none`).
- **Fix pattern (Folio):** `fieldset-fields.liquid` adds `xo-disabled` on `<xo-filters-field>` when `value.count == 0 and value.active == false`. The checkbox SCSS greys it out.
- Docs: https://shopify.dev/docs/themes/navigation-search/filtering

### SF-I18N-01 — Every storefront string goes through `| t`
- **Seen in:** R1 Folio
- **Check:** heuristic (hardcoded text) + static (locale key parity)
- **Requirement:** When the storefront language is switched, every theme interface string must translate. Reviewers checked the cart drawer and the cart page: titles, column headers, the tax/shipping notice ("Tax included. Shipping calculated at checkout.") and the "Check out" button. Shopify expects a full audit of all templates.
- **How to verify:**
  - No literal English text nodes in `.liquid` files. JS-rendered strings (cart drawer re-renders, aria-live messages) must come from translated data attributes or `window` strings, not hardcoded in TS.
  - Every key used with `| t` exists in the default locale, and every default-locale key exists in all other locale files.
  - Runtime: switch to a non-English locale and walk the cart drawer, cart page, product page, collection/search (filters, sort, pagination), account pages and 404.
- Docs: https://shopify.dev/docs/themes/markets/multiple-currencies-languages#the-language-selector · https://shopify.dev/docs/themes/markets/country-language-ux

### SF-MENU-01 — Nested menus are usable at every level on mobile
- **Seen in:** R1 Folio
- **Check:** heuristic (3 levels rendered) + runtime
- **Requirement:** Menus support 3 levels (`link.links` → `childlink.links`). The 2nd- and 3rd-level **mobile** panels must be responsive: full viewport, scrollable, not clipped or offset.
- **How to verify:** On a 390px viewport, open a menu with 3 levels. Every panel must fill the screen, scroll on its own, and have working Back and Close buttons.
- **Known root cause (Folio):** The nested `<xo-modal>`s were rendered inside the parent drawer. The parent's leftover `transform` and `overflow-y: auto` became the containing block for their `position: fixed`, so the panels were offset and clipped. Fix: render level-2/3 modals as siblings outside the scrolling body (or portal them), use `100dvh`, and make the modal names collision-free (`parent-child`, not `parentchild`).
- Docs: https://shopify.dev/docs/themes/navigation-search/navigation

### SF-NEWSLETTER-01 — Newsletter email input validates
- **Seen in:** R1 Folio
- **Check:** static + runtime
- **Requirement:** Newsletter signup (`{% form 'customer' %}` with `contact[tags]=newsletter`) must show a validation warning for an incomplete email (e.g. `abc@`).
- **How to verify:** The input is `type="email"` and `required`, and the form does **not** carry `novalidate` unless the JS validates and shows an error message itself. Runtime: submit `abc@` and see a visible error (native bubble or theme message), not a silent submit.
- Docs: https://shopify.dev/docs/themes/customer-engagement/email-consent#newsletter-sign-up-form

---

## Stage 3 — Technical requirements

### SF-PRODUCT-01 — Product page shows a "taxes included" notice
- **Seen in:** R1 Folio
- **Check:** static
- **Requirement:** The product page uses `cart.taxes_included` to say taxes are included when the store uses tax-inclusive prices. Usually Shopify's `products.product.include_taxes` string, plus the shipping policy link.
- **How to verify:** `cart.taxes_included` is referenced in the product-info / price area of the product template, not only in the cart.
- **Fix pattern (Folio):** the notice existed only in quick view. Added `{% if cart.taxes_included %}<p class="…__tax">{{ 'products.product.price.include_tax' | t }}</p>{% endif %}` inside the `price` block of `product-info-content.liquid`, inside `<xo-product-will-change>`, so it survives variant re-renders. The locale key already existed in every language.

### SF-COLLECTION-01 — Product cards output unit price
- **Seen in:** R1 Folio
- **Check:** static
- **Requirement:** Collection product cards render `variant.unit_price` (with `unit_price_measurement`) when the variant has one, as Dawn does.
- **How to verify:** The product-card / card-price snippet renders a unit-price snippet. Having one only in the cart does not count.

### SF-COLLECTION-02 — Product cards show compare-at price with the Sale badge
- **Seen in:** R1 Folio
- **Check:** static + runtime
- **Requirement:** When a product is on sale, the card shows the strikethrough `compare_at_price` (`product.compare_at_price_max` or the variant's) next to the Sale badge.
- **How to verify:** The card's price output has a compare-at branch (`<s>` / `<del>`), and it is not hidden by a card setting defaulted to off or by CSS.

### SF-BLOG-01 — Blog template outputs `blog.title` by default
- **Seen in:** R1 Folio
- **Check:** heuristic
- **Requirement:** The blog page renders `blog.title` out of the box. A hardcoded custom-content heading ("Notes from the shelf.") with the native Title toggle off fails.
- **How to verify:** In the shipped `blog.*.json` templates, the section that outputs `blog.title` is present and its title setting is **on** by default. No demo copy replaces it.
- **Fix pattern (Folio):** the `blog-header` section gained a `use_blog_title` checkbox (default `true`, also set in every `blog.preset-N.json`). When it is on and `blog` exists, the section passes `blog.title | escape` to `section-heading` through the new optional `title_override` param. The custom heading stays as the off-state and as the fallback outside blog templates.

### SF-RTE-01 — RTE content is styled consistently everywhere
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** `h1`–`h6`, `blockquote`, `ul` and `ol` inside rich-text output look the same in every template: article body, product description, collection description, page content, and rich-text sections.
- **How to verify:** Every richtext output carries the shared `rte` class. No section restyles `.rte h2` etc. in a way that diverges. Runtime: put the same RTE sample in each place and compare.

### SF-ASSET-01 — No minified CSS/JS shipped (except third-party / ES6)
- **Seen in:** R1 Folio
- **Check:** static (on the built `shopify/assets`)
- **Requirement:** Themes must not include minified `.css` or `.js`. Shopify minifies them itself. Exceptions are third-party libraries and ES6+ modules. Our own `xo-webcomponents.min.css` is **not** exempt and must ship unminified.
- **How to verify:** No `*.min.css` in `assets/`. No theme-authored CSS/JS file whose lines run to thousands of characters (the vite `build.minify` output). `*.min.js` must be justified as ES6+/third-party.
- **Fix pattern:** Ship the unminified build of the xo-webcomponents CSS under a non-`.min` name, set `build.minify: false` (or `cssMinify: false`) for theme CSS, and update the `asset_url` references in `theme.liquid`, `password.liquid` and `gift_card.liquid`.

### SF-A11Y-01 — Everything is keyboard reachable, including dropdown navigation
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** Tabbing reaches every interactive element: mega-menu/dropdown items, drawer contents, carousels, swatches, filters. Nothing is skipped.
- **How to verify:** Flag `tabindex="-1"` on links, buttons or inputs, and clickable `div`/`span` without `role` + `tabindex="0"`. Runtime: Tab through the header (dropdowns must open on Enter/Space or focus), a product page and a collection page.
- **Fix pattern (Folio):** Custom-element triggers (`<xo-tabs-trigger>` in notes-pyramid / tab-title) had no `tabindex`, so Tab skipped them. Add `role="button" tabindex="0"`; the theme's global keydown handler turns Enter/Space on `role=button` into a click. Sweep `<xo-*-trigger|prev|next>` without tabindex and without a focusable child.

### SF-A11Y-02 — Visible focus state on every focusable element
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** Each focusable element shows a visible focus indicator during keyboard navigation.
- **How to verify:** Look for a global `:focus-visible` outline rule. Flag `outline: none` / `outline: 0` with no matching `:focus-visible` replacement. Runtime: Tab through links in the header, footer and cards.
- **Fix pattern (Folio):** The global ring was `color(primary)`, invisible on primary bands/buttons (manifesto marquee, brown CTAs). Now `outline: 0.2rem solid color(foreground)` + `box-shadow: 0 0 0 0.2rem color(background)` halo in `src/styles/base/focus.scss`. Inside `overflow` scrollers draw it inset. Also drop atomic `o:none|fv` (quantity input had it).

### SF-A11Y-03 — All images have an `alt` attribute
- **Seen in:** R1 Folio
- **Check:** static
- **Requirement:** Every `<img>` has `alt`. Product images use `image.alt` or `image_tag: alt:`. Decorative images use `alt=""`.
- **How to verify:** No raw `<img` without `alt=`. An explicit `alt: ''` on product imagery is a fail.
- **Fix pattern (Folio):** `image` snippet fell back to the literal `'Image'`, so product thumbnails got `alt="Image"`. `media` snippet now takes `fallback_alt`; product media pass `fallback_alt: product.title` (uses `media.alt` first). Hardcoded `alt: 'Image'` in `_image-2` → `image.alt`.

### SF-A11Y-04 — Unique input IDs with matching `<label for>`
- **Seen in:** R1 Folio
- **Check:** heuristic
- **Requirement:** Every form input has a unique `id`, and its label has a `for` that matches it. Snippets rendered several times on one page (filters, quantity inputs, newsletter in both footer and popup, variant pickers) must suffix IDs with a section, block or loop id.
- **How to verify:** Flag hardcoded literal `id="…"` on inputs inside snippets and blocks, `<label for="…">` with no matching id in the same file, and inputs with neither a label nor `aria-label`.
- **Fix pattern (Folio):** Quantity input (PDP, cart drawer, cart page) had only `aria-label`; discount/zip field wrapped the input in a `<label>` with an empty `id`. Quantity now gets `id="Quantity-<section>-<line|variant>-<suffix>"` + visually-hidden `<label for>` (`line`/`id_suffix` params for mobile/desktop/sticky copies). `field-input` generates `Input-<section>-<block>-<name>` and the label gets `for`. Price filter `min-value`/`max-value` → `Filter-price-<section>[-drawer]-min/max`.

### SF-A11Y-05 — Touch targets at least 24×24 CSS px
- **Seen in:** R1 Folio
- **Check:** runtime
- **Requirement:** Pointer targets (icon buttons, swatches, carousel dots, close ×, quantity ±, pagination) measure at least 24×24. Inline text links are exempt.
- **How to verify:** Look for small `width`/`height` on dots and swatches. Runtime: `getBoundingClientRect()` on all `button, a, [role=button], input[type=radio|checkbox] + label` and list any under 24px.
- **Fix pattern (Folio):** Colour swatches were 15×15 (preset `swatches_width/height: 15`). `.xo-variant-image { min-width/min-height: 2.4rem }`; the visual chip keeps the preset size.

### SF-A11Y-06 — Headings h1–h6 are visually distinct
- **Seen in:** R1 Folio
- **Check:** static (type scale) + runtime
- **Requirement:** Each heading level differs visibly (size, weight or style) from the next.
- **How to verify:** The heading type-scale tokens (`h1`…`h6`) have strictly decreasing sizes, with no duplicates, in every preset.
- **Fix pattern (Folio):** `.rte` h4–h6 were 18/16/15px at one weight (≈ body). h5 now bold, h6 small bold uppercase-tracked, h4 bumped.

---

## Design / UX

### SF-SECTION-01 — Header and footer limited to one instance
- **Seen in:** R1 Folio
- **Check:** static
- **Requirement:** Header and footer section schemas declare `"limit": 1`, so a merchant cannot add or activate two at once.
- **How to verify:** Every header-type and footer-type section in the header/footer groups has `limit: 1`. If the theme ships **several** header variants (header, header-editorial, header-overlay…), each `limit: 1` still lets two different types coexist, so confirm in the editor that only one can be added. Otherwise restrict the extra variants with `enabled_on`/`disabled_on` or collapse them into one section with a style setting.

### SF-RTE-02 — Lists keep markers next to text when alignment changes
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** With text alignment set to center or right, `ul`/`ol` markers must stay attached to their text, without a big gap.
- **How to verify:** RTE/text styles set `list-style-position: inside` (or equivalent) when the container is not left-aligned. Runtime: every section with an alignment setting plus richtext gets center and right alignment and a bulleted and numbered list.
- **Fix pattern (Folio):** `.rte ul, .rte ol { list-style-position: inside; padding-inline-start: 0 }` (the UA 40px start padding pushes a centred list off-axis) + `.rte li > p:first-child { display: inline }` (a `<p>` inside `<li>` drops the marker onto its own line) + nested lists re-indented. Every merchant-content wrapper (`page.content`, descriptions) must carry `rte`.

### SF-RTE-03 — Links inside inline richtext keep word order and flow
- **Seen in:** R1 Folio
- **Check:** heuristic + runtime
- **Requirement:** Adding a hyperlink to inline text must not reorder words (marquee: "Built to last" became "to lastBuilt") or split and displace part of the text (card heading).
- **Root cause:** `inline_richtext` output dropped directly into a `display: flex`/`grid` container (or a marquee that clones or animates children). Each text node and `<a>` becomes a separate flex item, so the items reorder or wrap apart.
- **How to verify:** Every `inline_richtext` output sits inside its own inline wrapper (`<span>`/`<p>`), never as the direct child of a flex or grid element. Runtime: add a link to the middle of the text in a marquee, card and heading.
- **Fix pattern (Folio):** root cause was `xo-marquee[xo-direction=rtl]{direction:rtl}` (webcomponent CSS) inherited by an `inline-flex` phrase → its text node + `<a>` became flex items laid out right-to-left. Fix: `xo-marquee[xo-direction="rtl"] xo-marquee-item > * { direction: ltr }` (+ `[dir="rtl"]` counterpart) in `src/styles/base/content.scss`.

### SF-SETTINGS-01 — No demo resource handles in setting defaults
- **Seen in:** R1 Folio
- **Check:** static
- **Requirement:** `url`, `product`, `collection`, `blog`, `page` and `link_list` settings must not default to store-specific handles (e.g. `/products/morning-oil`). Allowed: blank, `/collections/all`, `/`, or `shopify://` routes that exist on every store.
- **How to verify:** Scan `schema.js` defaults and the shipped template/group JSON for `/products/…`, `/collections/<handle>`, `/blogs/…`, `/pages/…`, and `shopify://products|collections|blogs|pages/…`.

### SF-LINK-01 — Actionable text looks clickable
- **Seen in:** R1 Folio
- **Check:** runtime
- **Requirement:** Controls such as "remove all" (empty filter/search state) must have link or button affordance: underline, button style, or a hover state.
- **How to verify:** Check the empty-state and clear-filter markup for a styled link or button class. Runtime: view the empty search state.

### SF-STOCK-01 — Untracked inventory is not "Out of stock"
- **Seen in:** R1 Folio
- **Check:** heuristic
- **Requirement:** Inventory status must respect `variant.inventory_management` and `inventory_policy`. A variant with untracked inventory (`inventory_management` blank) or `continue` policy is purchasable and must not say "Out of stock".
- **How to verify:** Any branch on `inventory_quantity <= 0` must first check `variant.available` / `inventory_management != blank`. The JS variant-change update must do the same.

### SF-CONTRAST-01 — Modal close button has enough contrast
- **Seen in:** R1 Folio
- **Check:** runtime
- **Requirement:** The modal/drawer close (×) control meets contrast (3:1 for non-text UI) against its background in every color scheme.
- **How to verify:** Open quick view, the cart drawer, search, popups and the menu drawer in each color scheme and measure the icon colour against the background.

### SF-VARIANT-01 — Swatch availability uses the current selection correctly
- **Seen in:** R1 Folio
- **Check:** runtime
- **Requirement:** A swatch is struck through or disabled only when **no** available variant exists for that value combined with the *other currently selected* options. Reviewer case: with `Cat` and `M/L` selected, `Dog` was struck through although `Dog / S/M` was available. Do not mark it unavailable when only the exact current pair is missing. Prefer Shopify's `product_option_value.available` (option-value drops) over custom JS.
- **How to verify:** Read the variant-picker availability logic (Liquid and JS). Runtime: on a product with 2+ options and sparse availability, click through combinations.

---

## Reminders (no automated check)

### SF-LICENSE-01 — Licenses for third-party plugins and images
- **Seen in:** R1 Folio
- **Check:** manual
- **Requirement:** Have the licenses for every bundled third-party library, font and demo image before submitting.
