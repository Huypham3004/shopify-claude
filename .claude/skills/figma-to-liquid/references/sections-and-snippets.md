# Sections & snippets — compose, audit, lift to settings

The downstream of a Figma port is the same as any port in this project: reuse existing snippets, compose a section with the project wrapper, and lift literals to schema settings. This reference is self-contained; invoke `Skill(liquid)` / `Skill(snippet)` / `Skill(schema)` for the syntax details.

## Section file layout

```
src/sections/<name>/
├── <name>.liquid          # markup — uses the {% render 'section' %} wrapper
├── <name>.global.scss     # scoped styles (scss-glob auto-imports *.global.scss)
└── schema.js              # createSectionSchema + ...sectionSchemaSettings({})
```

### The wrapper pattern (never hand-write `<section>`)

```liquid
{%- capture content -%}
  …inner markup, composing snippets via {% render %}…
{%- endcapture -%}

{% render 'section', content: content %}
```

`{% render 'section' %}` (from `src/snippets/_base/section/`) emits the outer element, `xo-section` class, color-scheme class, container, background, and padding — all driven by `sectionSchemaSettings(...)`. Don't reproduce container/padding markup yourself.

### schema.js shape

```js
import { createSectionSchema } from "../../create-schema.js";
import { sectionSchemaSettings } from "../../snippets/_base/section/schema.js";

export const schema = createSectionSchema({
  name: "Image text split",
  settings: [
    ...sectionSchemaSettings({}),   // the section chrome (width/height/color_scheme/padding/…)
    { type: "header", content: "Text" },
    { type: "inline_richtext", id: "eyebrow", label: "Eyebrow" },
    { type: "textarea", id: "heading", label: "Heading", default: "Image with text" },
    { type: "richtext", id: "body", label: "Content", default: "<p>Pair text with an image…</p>" },
    { type: "image_picker", id: "image", label: "Image" },
    // … button label/link, etc.
  ],
  presets: [{ name: "Image text split" }],
});
```

Verify `category: Category.Section.X` against `src/constants.js` before using it (`Section.Products` is plural, `Block.Product` singular). Run `validate-schema.py <dir>` after every edit.

## Reuse-first / snippet-variant audit (Step 2)

Every Figma **INSTANCE** (Button, Card, Badge, Price…) is a signal to reuse, not rebuild. Before rendering any primitive:

1. **Find** the matching `src/snippets/<name>/`. Its `{% comment %}` doc-block is the param contract — read it (don't guess param names).
2. **List its variants** (`*-1`, `*-2`, … under the snippet dir). Trace what each hardcodes vs reads from settings.
3. **Pick the closest** to the Figma intent. This is reasoning, not lookup — read the actual files.
4. **Escalate only if none match:**

| Step | Action | When |
| --- | --- | --- |
| A | Configure via theme settings (right value in `preset-N.js`) | a variant already reads the setting |
| B | Modify the closest variant (`<snippet>-N.liquid`/`.global.scss`) | change is universally beneficial / variant inconsistent AND no shipped preset breaks |
| C | **New numbered variant + dispatcher + global-schema** | genuinely new archetype AND modifying any variant breaks other presets — **STOP, ask the user first** |

The bulk of the effort is A (pick variant + pass params). Rebuilding a snippet or adding section-scoped CSS to hack a snippet's look is the anti-pattern.

> [!IMPORTANT]
> **Two-sided read.** Same NAME ≠ same RENDERING. A Figma "card" may be caption-below while the project's `collection-card` is overlay-on-image. Compare the Figma visual (`get_image`) against the snippet's actual render before declaring reuse. A one-sided reuse decision produces markup that compiles but doesn't match the frame.

## Lift literals to schema settings (Step 4)

Figma has **no hardcoded-vs-dynamic concept** — every value is literal. You decide what a merchant edits:

| Figma content | Setting type |
| --- | --- |
| Heading text | `textarea` (plain) or `inline_richtext` (if it has emphasis / `<em>`) |
| Body paragraph(s) | `richtext` — wrapper must be `<div class="… rte">`, **never `<p>`** (richtext emits its own `<p>`; `<p><p>…</p></p>` breaks) |
| Short inline copy with a styled word | `inline_richtext` (wrapper can be `<h2>`/`<p>`) |
| Image | `image_picker` + the project image snippet (`{% render 'image' %}`) |
| Link / CTA target | `url` |
| Count / columns / sizes | `range` (with min/max/step) |
| A/B choice, alignment | `select` |
| Toggle | `checkbox` (booleans need `allow_false: true` — see `snippet` skill) |

**Defaults are generic placeholders**, not the Figma copy: heading = section purpose, body = "Use this text to share information about your brand…", button = "Button label". The Figma literal text is the porting target, never persisted as a default.

Structural values (layout, spacing that's part of the design system, decoration) usually stay in markup/tokens, not settings — don't over-expose. Surface any non-obvious keep/lift decision in the port preview.

## Snippet output (when the frame IS a reusable primitive)

If the Figma selection is a single self-contained component that repeats (a card, a badge), it's a **snippet**, not a section — and it very likely already exists (audit first). If it's genuinely new, follow `Skill(snippet)` for the body shape (pure-param / context+schema / dispatched variant) and `Skill(liquid-doc)` for the `{% comment %} @param … %}` contract. Creating a new snippet is the exception (design-to-liquid's core assumption applies here too).
