# Liquid Gotchas

Things that work in isolation but break in the editor, preview, or production. Sorted by frequency.

---

## 1. `for` loop has a 50-iteration ceiling

```liquid
{% for product in collection.products %}…{% endfor %}
```

Stops after 50 items by default. Larger arrays need `{% paginate %}`:

```liquid
{% paginate collection.products by 24 %}
  {% for product in collection.products %}…{% endfor %}
{% endpaginate %}
```

**Workaround for "show 100 items without pagination":** there isn't a clean one — Shopify enforces this for performance. Use `paginate by 50` and render N pages, or stagger via JS fetch.

---

## 2. `paginate` must be at the section's top level

`paginate` can't be nested inside `{% for %}`, `{% if %}`, `{% case %}`, or `{% form %}`. It also can't appear inside a snippet rendered via `{% render %}`.

```liquid
{# BROKEN #}
{% if condition %}
  {% paginate collection.products by 24 %}…{% endpaginate %}
{% endif %}

{# OK — paginate at top, condition inside #}
{% paginate collection.products by 24 %}
  {% if condition %}
    {% for product in collection.products %}…{% endfor %}
  {% endif %}
{% endpaginate %}
```

If you need conditional pagination, paginate unconditionally and render the items only if the condition holds.

---

## 3. `{% render %}` is isolated — no caller scope

```liquid
{# Caller #}
{% assign label = 'Hello' %}
{% render 'greeting' %}

{# snippets/greeting.liquid — label is NIL here #}
<p>{{ label }}</p>     ← empty output
```

Snippets see only:
- Parameters you pass: `{% render 'greeting', label: label %}`
- Global objects: `section`, `block`, `settings`, `cart`, `customer`, `request`, `routes`, `shop`, `template`, `theme`, `linklists`, `recommendations`, …

To pass a local variable, name it explicitly:

```liquid
{% render 'greeting', label: label, color: accent_color %}
```

> `{% include %}` (deprecated) shared the caller's scope. That's why `render` was introduced — to make snippets predictable.

---

## 4. `inline_richtext` rejects block-level tags

`type: 'inline_richtext'` settings allow only **inline** HTML tags in the default value:

| Allowed | Rejected |
| --- | --- |
| `em`, `strong`, `b`, `i`, `u`, `a`, `span`, `sup`, `sub` | `br`, `p`, `h1`-`h6`, `ul`, `ol`, `li`, `div`, `img`, `section`, `article`, `aside`, `header`, `footer`, `nav` |

For line breaks: use CSS (`max-width: NNch` to wrap) or switch to `type: 'richtext'`.

For paragraphs/lists: `type: 'richtext'` whose default's top-level node MUST be `<p>` / `<ul>` / `<ol>` / `<h1>`–`<h6>`.

Validation: `python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/` catches these.

> The rule above is about the DEFAULT VALUE (schema side). For the WRAPPER ELEMENT that outputs a `richtext` field (Liquid side), see #32.

---

## 5. `settings_data.json` `current` must be an object, not a string

```json
// BROKEN — Theme Editor preview rejects this
{
  "current": "Folio",
  "presets": { "Folio": { ... } }
}

// OK — full object clone
{
  "current": { ... full preset object ... },
  "presets": { "Folio": { ... } }
}
```

In `src/config/settings_data.js`, use `JSON.parse(JSON.stringify(preset1))` to deep-clone:

```js
import { preset1 } from './presets/preset-1.js';
export const settingsData = {
  current: JSON.parse(JSON.stringify(preset1)),
  presets: { 'Folio': preset1 },
};
```

Run `validate-schema.py --theme` to catch this.

---

## 6. `image_url` requires `width` OR `height`

```liquid
{{ product | image_url }}              ← fails / returns invalid URL
{{ product | image_url: width: 800 }}  ← OK
```

Max value: 5760px. Don't request more than the display size needs (perf cost).

---

## 7. `image_url` returns a string; `image_tag` is the filter that wraps it

```liquid
{# BROKEN — image_tag needs the URL string, not the image object directly #}
{{ product.featured_image | image_tag }}   ← may work but emits unstyled <img>

{# OK — chain image_url first #}
{{ product.featured_image | image_url: width: 800 | image_tag: alt: product.title }}
```

The project's `image` snippet handles this internally — prefer using it.

---

## 8. Deprecated filters — don't use

| Deprecated | Use instead |
| --- | --- |
| `img_url` | `image_url` |
| `img_tag` | `image_tag` |
| `product_img_url` | `image_url` (chain on `product.featured_image`) |
| `include` (tag) | `render` |

These can slip past the source-side validator since they're applied at runtime. Visual editor preview + a quick scan of the compiled `shopify/` output catches them.

---

## 9. `escape` is auto-applied in HTML text contexts only

`{{ user_input }}` inside HTML text content is auto-escaped:

```liquid
<p>{{ user_input }}</p>     ← safe: < becomes &lt;
```

But NOT inside attributes, `style=`, `href=` to non-Shopify URLs, or JSON contexts. **Apply `escape` explicitly:**

```liquid
<input value="{{ section.settings.placeholder | escape }}">
<a href="{{ url | escape }}">
<button aria-label="{{ play_label | strip_html | escape }}">
<script>var data = {{ data | json }};</script>   ← json filter handles escaping
```

---

## 10. `default` filter treats `false` as falsy

```liquid
{% assign show = block.settings.show_cta | default: true %}
```

If `show_cta` is `false` → result is `true` (default substituted). Use `allow_false: true`:

```liquid
{% assign show = block.settings.show_cta | default: true, allow_false: true %}
```

See `references/idioms.md` §2.

---

## 11. Empty string `""` is truthy in `{% if %}`

```liquid
{% if section.settings.heading %}     ← true even when heading is "" (empty)
  <h2>{{ heading }}</h2>              ← emits empty <h2>
{% endif %}
```

Use `!= blank` to check for "non-empty content":

```liquid
{% if section.settings.heading != blank %}
  <h2>{{ section.settings.heading }}</h2>
{% endif %}
```

`blank` is a special value matching `nil`, empty string, empty array, empty hash, and whitespace-only strings.

---

## 12. `money` filter takes subunit; format depends on currency

`product.price` is in the smallest unit of the currency:
- USD: cents → `1999` = $19.99
- JPY: yen → `100000` = ¥100,000 (no subunit, but Shopify multiplies by 100 internally — surface value reads `100000` but displays correctly via `money`)
- KRW: won → same as JPY

Always pipe through `money` (or related) — never compute display strings manually.

---

## 13. `t` translation: key must exist

```liquid
{{ 'general.cart.title' | t }}
```

If the key is missing from `locales/<lang>.json`, you get either a fallback to the default locale or the key name itself. Always define keys in all shipped locales before referencing them.

---

## 14. `block.shopify_attributes` is required

```liquid
{# BROKEN — block can't be selected in Theme Editor #}
<div class="card">…</div>

{# OK #}
<div class="card" {{ block.shopify_attributes }}>…</div>
```

Without `shopify_attributes`, the editor highlights nothing when the merchant clicks the block in the sidebar.

---

## 15. Don't modify `content_for_header`

```liquid
{# In theme.liquid <head> #}
{{ content_for_header }}     ← emit as-is, do not parse/modify
```

Shopify injects critical scripts here (analytics, Theme Editor connection, etc.). Theme Store rule.

---

## 16. `<html lang>` must use `request.locale.iso_code`

```liquid
<html lang="{{ request.locale.iso_code }}">
```

Hardcoded `lang="en"` fails multi-locale stores. Already set correctly in `src/layout/theme.liquid`.

---

## 17. `routes` only inside theme code, not in JSON templates

JSON page templates (`src/pages/<template>/*.json`) are static — they can't evaluate Liquid. Use the URL strings directly in `link_url` settings.

In Liquid files, always use `routes.X_url`:

```liquid
<a href="{{ routes.cart_url }}">Cart</a>
<a href="{{ routes.search_url }}?q={{ q | escape }}">Search</a>
```

---

## 18. `paginate.parts` includes ellipsis entries

```liquid
{% for part in paginate.parts %}
  {% if part.is_link %}
    <a href="{{ part.url }}">{{ part.title }}</a>
  {% else %}
    <span>{{ part.title }}</span>     ← '…' between far-apart pages
  {% endif %}
{% endfor %}
```

`part.is_link` is `false` for the ellipsis "..." entries. Always guard your `<a>` emit with that check.

---

## 19. `cart.taxes_included` depends on store settings + customer country

Don't assume taxes are included in `cart.total_price`. Check the boolean:

```liquid
{% if cart.taxes_included %}
  <small>{{ 'cart.taxes_included' | t }}</small>
{% endif %}
```

Theme Store requires this indicator.

---

## 20. `section.blocks.size` not `.length`

In Liquid, the property is `.size`, not `.length`:

```liquid
{% if section.blocks.size > 0 %}        ← OK
{% if section.blocks.length > 0 %}       ← always 0 (no such property)
```

Same for `cart.items.size`, `collection.products.size`, etc.

---

## 21. `compare_at_price` can be lower than `price`

For products that have moved sale prices up (rare), `variant.compare_at_price` might be ≤ `variant.price`. Always check before displaying the strike-through:

```liquid
{% if variant.compare_at_price > variant.price %}
  <s>{{ variant.compare_at_price | money }}</s>
{% endif %}
```

---

## 22. `forloop.last` doesn't account for `break`

```liquid
{% for item in items %}
  {% if forloop.last %}…{% endif %}
  {% if item.special %}{% break %}{% endif %}
{% endfor %}
```

`forloop.last` is `true` only on the natural last iteration. After a `break`, no special "I'm leaving early" signal — handle manually.

---

## 23. Filtering chains with `where` are lazy until used

```liquid
{% assign filtered = collection.products | where: 'available', true %}
{# 'filtered' is not yet evaluated — wait until first read #}
```

This is normally fine, but if you have a sequence of `where` filters, all of them evaluate when first read. For repeated reads, capture into a `for` once.

---

## 24. Whitespace control matters for HTML attribute output

```liquid
<div class="
  card
  {% if active %}card--active{% endif %}
">
{# Emits: class=" card  card--active " with stray spaces #}
```

Use `{%-` / `-%}` and tight composition:

```liquid
{% liquid
  assign cls = 'card'
  if active
    assign cls = cls | append: ' card--active'
  endif
%}
<div class="{{ cls }}">
```

Or concise inline:

```liquid
<div class="card{% if active %} card--active{% endif %}">
```

---

## 25. `request.design_mode` is `nil` in production

Don't rely on it for production logic — only for editor-only fallbacks (placeholder images, dev hints).

```liquid
{%- if request.design_mode -%}
  <placeholder-image data-type="general"></placeholder-image>
{%- endif -%}
```

---

## 26. Rendering inside a `{% raw %}` block is intentional

`{% raw %}` outputs Liquid syntax literally — used for code samples in docs. Don't confuse with `{% comment %}` (which discards). If you see `{% raw %}` in production code, it's almost always a bug — Liquid should evaluate, not display as text.

---

## 27. `link_to_*` filters HTML-escape the link text — pass plain strings

```liquid
{{ 'Click <em>here</em>' | link_to: '/page' }}
{# Emits: <a href="/page">Click &lt;em&gt;here&lt;/em&gt;</a> ← escaped! #}
```

For richer markup, hand-write the `<a>`:

```liquid
<a href="/page">Click <em>here</em></a>
```

---

## 28. `t` filter doesn't auto-pluralize without `count:`

```liquid
{{ 'cart.items_count' | t: count: cart.item_count }}
```

Locale file must have `one` / `other` keys for the pluralization to work:

```json
{
  "cart": {
    "items_count": {
      "one": "{{ count }} item",
      "other": "{{ count }} items"
    }
  }
}
```

Without `count:`, you get the default form only.

---

## 29. Section `name` shows in Theme Editor — keep it merchant-friendly

```js
// schema.js
export const schema = createSectionSchema({
  name: 'Hero collage',     // shown in the "+ Add section" dialog
  …
});
```

Theme Store rules apply (no `&`, no `?`, sentence case, AmE spelling). The validator audits this.

---

## 30. `metafield` paths can return `nil` silently

```liquid
{{ product.metafields.specs.material }}
```

Returns `nil` if the namespace or key isn't set. Check explicitly:

```liquid
{% if product.metafields.specs.material %}
  <p>Material: {{ product.metafields.specs.material }}</p>
{% endif %}
```

For rich-text metafields, `.value` may need filtering through render helpers depending on type.

---

## 31. `assign` takes a value, not a condition

`{% assign %}` evaluates its right-hand side as a single **value** — a variable or literal, optionally piped through filters. It is **not** an expression evaluator: comparison and logical operators (`==`, `!=`, `<>`, `>`, `<`, `>=`, `<=`, `contains`, `and`, `or`) are only understood by tags that *take a condition* (`if` / `unless` / `elsif` / `case`-`when`). So you cannot fold a comparison into an assign and get a boolean back:

```liquid
{# WRONG — the `!= blank` is not evaluated; has_float_1 does not become a usable boolean #}
{%- liquid
  assign s = section.settings
  assign has_float_1 = s.float_1 != blank
-%}
```

Two correct forms:

```liquid
{# A — branch, assign an explicit true/false #}
{%- liquid
  assign s = section.settings
  assign has_float_1 = false
  if s.float_1 != blank
    assign has_float_1 = true
  endif
-%}
```

```liquid
{# B — skip the flag, put the comparison straight in the {% if %} #}
{%- if s.float_1 != blank -%}
  …
{%- endif -%}
```

Reach for **B** by default — when a condition is checked once, an intermediate boolean is just noise. Use **A** only when the same boolean gates several places (e.g. multiple blocks) and recomputing the comparison inline each time would be harder to read. This bites most inside the `{% liquid %}` prelude, where `has_x` flags sit next to real assigns and the value-vs-condition distinction is easy to forget — keep prelude assigns to values + filters, and move every comparison into an `if`.

---

## 32. `richtext` output wrapper must be `<div>`, never `<p>`

A `richtext` field outputs its own block-level tags (`<p>`, `<ul>`, `<h1>`-`<h6>`). So the element you wrap the output in must be one that can legally hold block-level children — a `<div>` — **not** a `<p>` (nor a bare `<h2>`).

```liquid
{# WRONG — richtext emits <p>, so this renders <p><p>…</p></p> #}
<p class="xo-x__text rte">{{ section.settings.body }}</p>

{# RIGHT #}
<div class="xo-x__text rte">{{ section.settings.body }}</div>
```

`<p>` cannot contain a block-level child, so the HTML parser auto-closes the outer `<p>` the instant it sees the inner `<p>` — the BEM class detaches from the content, spacing collapses, and the layout breaks silently. Schema validation can't catch it: the schema is valid and the Liquid compiles; only the rendered DOM is wrong.

This bites during ports: the design element is frequently `<p class="lead">…</p>`, and the reflex is to keep the `<p>` and just add the `rte` class. Don't — swap the wrapper to `<div>`.

Contrast with `inline_richtext` (#4): it emits inline tags only (no block wrapper), so a `<p>`/`<h2>` wrapper around an `inline_richtext` field is correct.

| Field type | Wrapper element |
| --- | --- |
| `richtext` | `<div>` only |
| `inline_richtext` | any — `<p>`, `<h1>`-`<h6>`, `<span>`, … |

Both field types' wrappers also carry the `rte` class — see AGENT.md § "rte wrapper class on richtext output".

---

## Related

- `references/tags.md` — tag syntax
- `references/filters.md` — filter syntax
- `references/objects.md` — what objects expose
- `references/idioms.md` — the project's preferred way
- `design-to-liquid/scripts/validate-schema.py` — source-side validation (catches inline_richtext, range bounds, etc)
