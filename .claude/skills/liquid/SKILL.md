---
name: liquid
description: "MUST be invoked (via Skill tool) BEFORE authoring, editing, or reviewing any Liquid markup in `src/sections/`, `src/snippets/`, `src/blocks/`, `src/groups/`, `src/layout/`, or any `.liquid` file — and BEFORE writing a section/block/group `.liquid` body during a design-to-liquid port. Memory of Shopify Liquid semantics is unreliable on the dangerous edge cases (e.g. `assign` takes a value, not a condition — see `references/gotchas.md` #31); skipping this skill = silent runtime bugs that compile fine. The single source of truth for Shopify Liquid syntax in this project — tags, filters, objects/drops, section blocks (inline vs theme, render patterns, dispatch, preset defaults), render-isolation rules, paginate, image_url sizing, inline_richtext vs richtext tag whitelists. Project-specific idioms ({% liquid %} prelude conventions, `default | allow_false: true`, `{%- capture content -%}` + `{% render 'section' %}` wrapper, `{{ block.shopify_attributes }}` on block roots) are codified in `references/idioms.md`. Common pitfalls (for-loop 50 ceiling, paginate at-top-level only, render-scope isolation, inline_richtext rejected tags) in `references/gotchas.md`. Self-contained — material distilled from shopify.dev/docs/api/liquid via context7. Defers to `snippet` for snippet-body shapes, `schema` for `schema.js`, `liquid-doc` for `{% comment %} @param … %}` headers, `design-to-liquid` for the porting pipeline."
---

# Liquid

Project's Liquid reference — syntax, semantics, project idioms. Self-contained; no external plugin required.

## Scope

**In scope** (this skill answers these):
- Tag syntax + parameters + examples (`render`, `paginate`, `section`, `sections`, `content_for`, `form`, `capture`, `if/case/for`, `assign`, `liquid` block, `layout`, `schema`, `comment`, `raw`, `echo`, `cycle`, `tablerow`, `increment`, `decrement`).
- Filter syntax + return type + examples (media: `image_url`/`image_tag`/`asset_url` · money: `money`/`money_with_currency` · string: `escape`/`strip_html`/`default` with `allow_false` · array: `where`/`sort`/`map`/`join` · math: `plus`/`minus`/`times` · URL: `link_to`/`url_for_type` · translation: `t`/`json`/`format_address`/`time_tag`).
- Object/drop properties (`product`, `variant`, `cart`, `customer`, `order`, `article`, `blog`, `collection`, `section`, `block`, `settings`, `request`, `routes`, `shop`, `paginate`, `image`, `metafield`, `metaobject`, `template`).
- Project-specific idioms — see `references/idioms.md`.
- Common pitfalls — see `references/gotchas.md`.

**Out of scope** (other skills own these):
- Snippet body shapes (pure / context+schema / variant dispatcher) → `snippet` skill.
- `schema.js` authoring (createSectionSchema, sectionSchemaSettings, visible, deviceSetting) → `schema` skill.
- `{% comment %} @param … %}` doc header at the top of every snippet → `liquid-doc` skill.
- Section porting pipeline (Step 0 tokens → Step 6 restyle) → `design-to-liquid` skill.
- SCSS framework (`color()`, `fz()`, BEM) → `scss` skill.
- Atomic class syntax (`p:1rem c:primary|h`) → `xo-css` skill.

## When to invoke

| Trigger | Where to look |
| --- | --- |
| "What's the syntax of `paginate` / `content_for 'blocks'` / `form 'X'` / `image_url:`?" | `references/tags.md` or `references/filters.md` |
| "What properties does `product` / `cart` / `section` / `paginate` expose?" | `references/objects.md` |
| "Inline block vs theme block? When to use `{% content_for 'blocks' %}` vs manual `{% for block in section.blocks %}`?" | `references/blocks.md` |
| "How do I dispatch on `block.type` cleanly — `if/elsif` vs `case/when`?" | `references/blocks.md` — §3 dispatch patterns |
| "How do I ship default block instances in a section preset (including nested theme blocks)?" | `references/blocks.md` — §5 preset defaults |
| "Why won't my `inline_richtext` default save?" | `references/gotchas.md` — inline_richtext tag whitelist |
| "How do I wrap my section markup so the `section` snippet handles padding/bg/scheme?" | `references/idioms.md` — capture+render wrapper pattern |
| "Why does my `for product in collection.products` cut off at 50?" | `references/gotchas.md` — for-loop ceiling, use paginate |
| "How do I make a boolean setting default to `false` survive the `\| default:` filter?" | `references/idioms.md` — `default | allow_false: true` |
| "Can I put `\| t` or `== false` directly in a `{% render %}` argument?" | `references/gotchas.md` #33 — no; assign in the prelude first |
| "Which image width should I pass to `image_url`?" | `references/idioms.md` — responsive image sizing |
| "Should this `.liquid` string be `\| t`, a schema setting, or hardcoded? Where do I add the key?" | `references/translations.md` — decision + `src/locales/NN-<ns>.json` convention |

## Navigation

- **`references/tags.md`** — every tag, grouped (control flow / iteration / variable / theme / other), with syntax + parameters + minimal example + gotchas.
- **`references/filters.md`** — every filter, grouped (media / money / string / array / math / URL / translation), with input → output + chain examples.
- **`references/objects.md`** — global objects + drops, grouped (page context / commerce / content / theme / media / metadata), with top properties + use examples.
- **`references/blocks.md`** — section blocks deep-dive. Inline block vs theme block · three render patterns (manual `for`, `content_for 'blocks'`, `content_for 'block'` static) · `if/elsif` vs `case/when` dispatch · `limit` / `max_blocks` / 50-ceiling · **preset defaults** (block arrays + nested theme blocks). **Read before any section that has a `blocks` array.**
- **`references/idioms.md`** — project-specific patterns. **Read this before adding new sections or snippets.** Includes the canonical `{%- capture content -%} {% render 'section', content: content %}` wrapper, the `{% liquid %}` prelude convention, `default | allow_false` for booleans, image responsive sizing recipe.
- **`references/gotchas.md`** — common pitfalls. Read when something works in isolation but breaks in the editor / preview.
- **`references/translations.md`** — the `| t` filter + this project's `src/locales/NN-<namespace>.json` source convention. **Read before hardcoding any visible string in a `.liquid` body** — decides `| t` vs schema setting vs hardcode, key reuse/add procedure, `_html` no-escape, pluralization. (Markup strings only — schema labels/defaults are out of scope.)

## Project Liquid conventions (cheatsheet)

> [!IMPORTANT]
> The patterns below are the project's working conventions. Every existing `src/sections/` and `src/snippets/` file follows them. Don't break the pattern without good reason.

### 1. Prelude — `{% liquid %}` block at the top

Use the `{% liquid %}` block to bunch all `assign`s + variable setup. Each tag on its own line; no `{% %}` delimiters inside. Use `echo` to output.

```liquid
{% liquid
  assign overline = section.settings.overline
  assign heading  = section.settings.heading
  assign image    = section.settings.image
  assign show_cta = section.settings.show_cta | default: true, allow_false: true
%}
```

Reasoning: the alternative — long chain of `{% assign … %}` tags each on its own line — is visually noisy. The `liquid` block is the project standard.

### 2. Section markup — capture + wrapper

```liquid
{%- capture content -%}
  <!-- inner markup, no <section> tag here -->
  <div class="xo-<name>__inner">…</div>
{%- endcapture -%}

{% render 'section', content: content %}
```

The `section` snippet (`src/snippets/_base/section/section.liquid`) emits the outer `<section class="xo-section xo-section--<id>">`, color-scheme class, container, padding, background — driven by `sectionSchemaSettings()` in your `schema.js`. **Don't hand-write `<section>` + `<xo-container>` + padding inline.**

### 3. Block iteration — `{{ block.shopify_attributes }}` required

```liquid
{%- for block in section.blocks -%}
  <div class="xo-<name>__item" {{ block.shopify_attributes }}>
    {%- render 'X', settings: block.settings -%}
  </div>
{%- endfor -%}
```

`shopify_attributes` is required by the Theme Editor for block selection / highlighting. Don't drop it.

### 4. Snippet doc header

Every snippet starts with a `{% comment %} … {% endcomment %}` block describing `@param`s. See the `liquid-doc` skill.

### 5. Image rendering — use the project `image` snippet

```liquid
{%- render 'image',
  image: section.settings.image,
  aspect_ratio: '16/9',
  class: 'xo-<name>__media',
  alt: section.settings.image_alt
-%}
```

The `image` snippet (`src/snippets/_base/image/image.liquid`) handles `image_url` sizing, lazy-load, focal point, placeholder fallback. Don't write raw `{{ image | image_url: width: X | image_tag: … }}` unless you need a non-standard pattern.

### 6. Render isolation

`{% render 'X', param: value %}` is **isolated** from the calling scope. The snippet sees only the params you pass + global objects (`section`, `block`, `settings`, `cart`, `request`, etc.). It does NOT see local variables from the caller. This is intentional — keeps snippets reusable. See `references/gotchas.md`.

Each argument is a **bare value** — a literal or a variable. No filters, no comparisons, no arithmetic: `aria_label: 'a.b' | t` and `lazyload: forloop.first == false` are hard Liquid syntax errors, not silent no-ops. Compute in the `{% liquid %}` prelude, pass the variable in. See `references/gotchas.md` #33.

### 7. Translatable strings — `| t`, keyed in `src/locales/`

Theme-owned visible strings in `.liquid` markup (button/UI labels, a11y `aria-label`/`visually-hidden`, status/error/empty messages) go through `'<namespace>.<path>' | t`, with the key authored in `src/locales/NN-<namespace>.json` (NOT the compiled `shopify/locales/...`). Merchant-edited content is a schema setting instead; schema labels/defaults are never `| t`.

```liquid
<button>{{ 'general.cart.add_to_cart' | t }}</button>
<button aria-label="{{ 'products.product.quick_view' | t }}">…</button>
```

**Reuse-first:** `grep -rin "<text>" src/locales/` before adding a key. Full decision + add-a-key procedure + `_html` no-escape + pluralization → `references/translations.md`.

## Project layout — where `.liquid` lives

| Path | Owner | Build target |
| --- | --- | --- |
| `src/layout/theme.liquid` | layout shell — `<html>`, `<head>`, `{% content_for_layout %}` | `shopify/layout/theme.liquid` |
| `src/sections/<name>/<name>.liquid` | section markup — wrapped by `{% render 'section' %}` | `shopify/sections/<name>.liquid` |
| `src/snippets/<name>/<name>/<name>.liquid` | reusable snippet body | `shopify/snippets/<name>.liquid` |
| `src/blocks/<group>/<name>/<name>.liquid` | block markup (rendered via `{% content_for 'blocks' %}`) | `shopify/blocks/<name>.liquid` |
| `src/groups/<group>/<name>/` | section groups (header / footer / popups) | `shopify/sections/` |
| `src/pages/<template>/index.preset-N.json` | JSON page template referencing sections | `shopify/templates/<template>.json` |

The compiled output in `shopify/` is generated by the build pipeline — never hand-edit.

## Validation

The project's source-side validator `.claude/skills/design-to-liquid/scripts/validate-schema.py` catches `schema.js` bugs (compile errors, range/step violations, undefined select options, disallowed `inline_richtext` tags, unresolved block types, theme-store label hygiene). Run it after every `schema.js` edit:

```bash
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all --strict
```

Post-build native theme-check on compiled `shopify/` output isn't currently wired into the project workflow. If needed, install `@shopify/theme-check` or the Shopify CLI separately — they're independent of this skill.

## Related skills

- `snippet` — snippet body shapes + class composition
- `schema` — `schema.js` (createSectionSchema, sectionSchemaSettings, visible)
- `liquid-doc` — `{% comment %} @param … %}` header
- `design-to-liquid` — port pipeline (Step 0 → Step 6)
- `scss` — BaseHTML SCSS framework (`color()`, `fz()`, `media()`, BEM)
- `xo-css` — atomic class syntax
- `git` — `/git` scoped commit workflow
