# Basics

XO-CSS syntax, tokens, and the rules every class must follow.

## Full Syntax

```
property:value|pseudo|pseudo@breakpoint!
```

| Segment        | Description                                                |
| -------------- | ---------------------------------------------------------- |
| `property`     | Property shortcut (see `./properties.md`)                  |
| `value`        | Token or literal CSS value                                 |
| `|pseudo`      | Pseudo-class/element (optional, see `./pseudo.md`)         |
| `@breakpoint`  | Responsive breakpoint (optional)                           |
| `!`            | `!important` flag (optional)                               |

## Examples

```html
<!-- Property + value -->
<div class="c:primary">Color primary</div>
<div class="p:1rem">Padding s6</div>

<!-- + Pseudo -->
<div class="c:primary|h">Color primary on hover</div>
<div class="bgc:background|f">Background on focus</div>

<!-- + Breakpoint -->
<div class="d:none@md">Hidden at ≥768px</div>
<div class="p:1.4rem@lg">Padding s8 at ≥992px</div>

<!-- + Pseudo + Breakpoint -->
<div class="c:primary|h@md">Hover color on desktop only</div>

<!-- + Important -->
<div class="pos:absolute!">Position absolute !important</div>
<div class="d:flex!@md">Flex !important at ≥768px</div>

<!-- Width / height with literal units -->
<div class="w:10rem h:10rem">Width and height in rem</div>

<!-- Dynamic via CSS variables -->
<div class="w:var(--width) h:var(--height)" style="--width: {{ width }}; --height: {{ height }}">
  Width and height from CSS variables
</div>
```

## Tokens

Tokens are defined in `theme-config/theme.config.json`.

### Spacing tokens

Apply to: `p`, `pt`, `pr`, `pb`, `pl`, `px`, `py`, `m`, `mt`, `mr`, `mb`, `ml`, `mx`, `my`, `gp` (gap), `rg`, `cg`, `t`, `r`, `b`, `l`, `ins`.

```html
<div class="p:1rem gp:1.4rem m:0.6rem">
  padding, gap, margin all using spacing tokens
</div>
```

**Where defined:** `space` in `theme-config/theme.config.json`.

### Color tokens

```html
<div class="c:primary bgc:background bdc:border">
  color, background-color, border-color
</div>
```

**With opacity:**

```html
<div class="c:foreground.5">color at 50% opacity</div>
<div class="bgc:primary.8">background at 80% opacity</div>
```

**Where defined:** `colors` in `theme-config/theme.config.json`.

### Typography tokens

```html
<div class="fz:h2 ff:heading lh:1.3 lts:0.2rem">
  font-size, font-family, line-height, letter-spacing
</div>
```

**Where defined:** `headingSizes`, `fonts` in `theme-config/theme.config.json`. Body font-sizes use direct rem values (e.g. `fz:1.4rem`) — no token map.

## Rules

### ✅ Do

```html
<!-- Use tokens -->
<div class="p:1rem gp:1.4rem c:primary">

<!-- CSS variables -->
<div class="w:var(--width)" style="--width: 10rem">

<!-- Viewport units / percentages -->
<div class="h:100vh w:100%">

<!-- CSS keywords -->
<div class="d:flex w:auto pos:relative">
```

### ❌ Don't

```html
<!-- Hardcoded lengths -->
<div class="p:10px gp:14px">

<!-- Hardcoded colors -->
<div class="c:white bgc:black c:#ff0000">

<!-- Dynamic class concatenation -->
{% assign gap = 's4' %}
<div class="{{ 'gp:' | append: gap }}">
```

## Allowed escape-hatch values

You can use these without defining tokens:

### CSS variables

```html
<div class="w:var(--width)" style="--width: 10rem"></div>
<div class="c:var(--color)" style="--color: red"></div>
```

### Viewport units / percentages

```html
<div class="h:100vh">Full viewport height</div>
<div class="w:100vw">Full viewport width</div>
<div class="w:50%">Half width</div>
```

### Keywords

```html
<div class="w:auto">Auto width</div>
<div class="d:inherit">Inherit display</div>
<div class="pos:relative">Relative</div>
<div class="ov:hidden">Overflow hidden</div>
```

### Literal values

```html
<div class="fz:14px">Font size 14px (discouraged)</div>
<div class="w:200px">Width 200px (discouraged)</div>
```

> [!NOTE]
> Prefer tokens over literal values for maintainability.

## Common Mistakes

### 1. Concatenating dynamic class names

```liquid
<!-- ❌ -->
{% assign spacing = 's6' %}
{% assign class = 'p:' | append: spacing %}
<div class="{{ class }}">

<!-- ✅ — case statement -->
{% case spacing %}
  {% when 's4' %}{% assign class = 'p:0.6rem' %}
  {% when 's6' %}{% assign class = 'p:1rem' %}
  {% when 's8' %}{% assign class = 'p:1.4rem' %}
{% endcase %}
<div class="{{ class }}">

<!-- ✅ — CSS variable -->
<div class="p:var(--spacing)" style="--spacing: {{ spacing_value }}">
```

### 2. Hardcoded colors

```html
<!-- ❌ -->
<div class="c:white bgc:black">
<div class="c:#ff0000">

<!-- ✅ -->
<div class="c:foreground bgc:background">
<div class="c:primary">
```

### 3. Hardcoded spacing

```html
<!-- ❌ -->
<div class="p:10px gp:20px">

<!-- ✅ -->
<div class="p:1rem gp:1.4rem">
```

### 4. Wrong syntax

```html
<!-- ❌ -->
<div class="padding:s6">         <!-- must use the shortcut `p` -->
<div class="color:primary">      <!-- must use the shortcut `c` -->
<div class="c:primary:hover">    <!-- use `|` for pseudo, not `:` -->

<!-- ✅ -->
<div class="p:1rem">
<div class="c:primary">
<div class="c:primary|h">
```

### 5. `|` is the pseudo separator — use `_` for spaces in a value

The `|` character is **the pseudo-class separator**, never a value separator. Anything after `|` is parsed as a pseudo shortcut (see `./pseudo.md`); if it doesn't match, the class fails silently. To put a **space inside a value** (multi-value grid, multi-arg function, box-shadow, transition list) use an **underscore `_`** — the framework replaces every `_` in the value with a space (see the core's `getValue`). So multi-value IS atomic.

```html
<!-- ❌ — `|...` is parsed as a pseudo and the rest is dropped -->
<div class="gtc:1.4fr|1fr">           <!-- `|1fr` → pseudo "1fr" → dropped; use `_` -->
<div class="fz:body|1.4">             <!-- `|1.4` → pseudo; also fz:body is not a token — use direct rem -->

<!-- ✅ — underscore `_` = space; multi-value IS atomic -->
<div class="gtc:1.4fr_1fr">                    <!-- grid-template-columns: 1.4fr 1fr -->
<div class="gtc:minmax(28rem,36rem)_1fr">      <!-- grid-template-columns: minmax(28rem,36rem) 1fr -->
<div class="bxsh:0_2px_12px_rgba(0,0,0,0.18)"><!-- box-shadow: 0 2px 12px rgba(0,0,0,0.18) -->
<div class="fz:1.4rem">                        <!-- single value: no separator needed -->
```

> Very long / complex values (multi-stop gradients, long transition lists) MAY be kept in the `<name>.global.scss` sidecar for readability — that's a preference, not a limitation; they're all expressible atomically via `_`.

### 6. Duplicate property on the same element

```html
<!-- ❌ — second `p:` overrides the first; multi-value padding can't be atomic this way -->
<div class="p:2rem p:2.4rem">

<!-- ✅ — use the direction shortcuts -->
<div class="py:2rem px:2.4rem">         <!-- 2-value padding: vertical / horizontal -->
<div class="pt:2rem pr:2.4rem pb:2.8rem pl:3.2rem">  <!-- 4-value padding: top/right/bottom/left -->
```

### 7. Using full CSS property names as atomic class names

```html
<!-- ❌ — not atomic shortcuts -->
<div class="grid-row:1 grid-col:1">
<div class="margin-top:s6">

<!-- ✅ — use shortcuts (see ./properties.md) -->
<div class="grs:1 gcs:1">           <!-- grid-row-start / grid-column-start -->
<div class="mt:1rem">                  <!-- margin-top -->
```

### 8. Adding `bds:solid` after `bd:sN` / `bdt:sN` / etc.

The project's `css.border` map in `theme.config.json` stores **full shorthand** including the `solid` keyword:

```json
"border": { "s0": "none", "s1": "0.1rem solid", "s2": "0.2rem solid" }
```

So `bd:s1` already compiles to `border: 0.1rem solid` — width + style + (inherited color) in one go. Adding `bds:solid` is redundant AND can side-effect: `bds:` sets `border-style` on **all 4 sides**, which overrides any per-side style. With `bdt:s1 bds:solid`, the 3 sides without explicit width get `solid` style applied too (rendered invisible because width=0, but the rule is set — surfaces if any parent provides border-color inheritance or `currentColor` swap).

```html
<!-- ❌ — redundant; `bds:solid` blankets all 4 sides -->
<div class="bdt:s1 bds:solid bdc:border">
<div class="bd:s1 bds:solid bdc:border">

<!-- ✅ — single token; solid is already in the config shorthand -->
<div class="bdt:s1 bdc:border">
<div class="bd:s1 bdc:border">

<!-- ✅ — `bds:` is legitimate to OVERRIDE the baked-in solid -->
<div class="bd:s1 bds:dashed bdc:border">   <!-- dashed override -->
<div class="bd:s1 bds:dotted bdc:border">   <!-- dotted override -->

<!-- ✅ — `bds:var(...)` is legitimate for runtime CSS-var-driven style -->
<div class="bdt:s1 bds:var(--bds) bdc:border" style="--bds: dashed">
```

Setting values stored as `bds:solid` / `bds:dashed` in schema `select` options (e.g. `border-attrs.schema.js`) are also legitimate — they flow through a `--bds` custom property via an adapter snippet, not directly as a class.

## Translating from design SCSS

When migrating a design's `.scss` to atomic XO-CSS (i.e. user picks "XO-CSS-first" strategy in clarify-protocol Q7), categorise each CSS rule into one of three tiers — then route accordingly. Tier-3 rules automatically fall through to a `<name>.global.scss` sidecar; there is no separate "Hybrid" strategy because the sidecar is already part of "XO-CSS-first".

### Three tiers

| Tier | What | Output |
|------|------|--------|
| 1 | Single-value tokens — layout (`display`, `flex-*`, `grid` items), spacing (`padding`/`margin`/`gap` with one value), color, simple typography, simple state | XO-CSS class in liquid |
| 2 | `xo-*` attributes from design markup (`xo-hover`, `xo-abs`, `xo-effect`, `xo-grid` paired with `xo-grid-block` class, …) | Copy attribute verbatim. NO CSS needed — XO-CSS framework drives the behavior. See `./advanced.md` |
| 3 | What CAN'T be expressed atomically — see expanded list below | Keep in component `.global.scss` SCSS file |

### Tier-3 expanded list

These always land in SCSS even under "XO-CSS-first" strategy:

1. **`@keyframes`** — no atomic equivalent.
2. **Multi-target chained selectors** — `&:hover .child`, `.is-active .child`, `& > .x + .y`.
3. **Pseudo-elements** — `::before`, `::after` with their own content/positioning.
4. **SCSS framework function calls with arguments** — `color(foreground, 0.553)` where the opacity-suffix `c:foreground.55` rounding isn't precise enough. (Most opacity cases ARE atomic via the `.<pct>` suffix.)

**NOT tier-3 — these ARE atomic (write internal spaces as `_`):**

- **Multi-value CSS properties** — `grid-template-columns: 1.4fr 1fr` → `gtc:1.4fr_1fr`; `grid-template-columns: minmax(28rem,36rem) 1fr` → `gtc:minmax(28rem,36rem)_1fr`; `box-shadow: 0 2px 12px rgba(0,0,0,0.18)` → `bxsh:0_2px_12px_rgba(0,0,0,0.18)`; `transition: transform 0.4s, box-shadow 0.3s` → `trs:transform_0.4s,box-shadow_0.3s`; `background: linear-gradient(180deg,#a,#b)` → `bg:linear-gradient(180deg,#a,#b)`. (`padding: 2rem 2.2rem` → use direction shortcuts `py:2rem px:2.4rem`.)
- **Function-based values** — `calc()` / `min()` / `max()` / `clamp()` / `minmax()` are expressible via `_` for their internal spaces, e.g. `top:calc(var(--top)_+_1rem)`. A bare `var(--x)` is escape-hatch atomic too.

Keep any of these in the SCSS sidecar **only by preference** when the value is very long/complex and reads better there — not because it's impossible atomically.

### Font-size translation (common confusion)

Body font-sizes use **direct rem values** in atomic — no token map. The build pipeline emits them literally as `font-size: <value>`.

| Design SCSS | XO-CSS atomic | Notes |
|------------|---------------|-------|
| `font-size: 1.2rem` | `fz:1.2rem` | direct literal |
| `font-size: 1.4rem` | `fz:1.4rem` | direct literal |
| `fz(body, 1.4)` (legacy SCSS) | `fz:1.4rem` | translate multiplier × `1rem` → direct rem |
| `var(--font-heading-4-size)` | `fz:h4` | heading sizes ARE tokenized via `headingSizes` |
| responsive clamp | `fz:pfs(1.2,1.4)` | use `pfs()` helper directly when mobile/desktop differ |

Heading sizes (`fz:h1`–`h6`, `fz:d1`–`d4`) remain tokenized via `headingSizes`. Only body sizes are direct.

### Translation worked example

Design SCSS:

```scss
.xo-thing {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.2rem 1.2rem 0;
  font-size: fz(body, 1.5);
  background: color(layer);
  color: color(foreground);
}

.xo-thing:hover .xo-thing__child {
  transform: scale(1.04);
}

@keyframes pulse { … }
```

Translation result:

```liquid
<div class="xo-thing d:flex fld:column gp:1rem pt:1.2rem px:1.2rem pb:0rem fz:1.5rem bgc:layer c:foreground">
  <div class="xo-thing__child">…</div>
</div>
```
```scss
// xo-thing.global.scss — tier-3 sidecar only
.xo-thing:hover .xo-thing__child {
  transform: scale(1.04);
}
@keyframes pulse { … }
```

## Liquid Integration

### Safe patterns

```liquid
<!-- Static classes — best -->
<div class="p:1rem c:primary">

<!-- Conditional class -->
<div class="{% if condition %}p:s6{% else %}p:s4{% endif %}">

<!-- Multiple conditional classes -->
<div class="c:primary {% if active %}bgc:background{% endif %}">

<!-- Case statement for dynamic values -->
{% case size %}
  {% when 'small' %}
    {% assign padding_class = 'p:0.6rem' %}
  {% when 'medium' %}
    {% assign padding_class = 'p:1rem' %}
  {% when 'large' %}
    {% assign padding_class = 'p:1.4rem' %}
{% endcase %}
<div class="{{ padding_class }}">
```

### Unsafe patterns

```liquid
<!-- NEVER concatenate strings into class names -->
{% assign class = 'p:' | append: spacing_token %}  <!-- ❌ -->
{% assign class = 'c:' | append: color_name %}     <!-- ❌ -->
```

## Related

- `./layout.md` — flex, grid, spacing, positioning
- `./styling.md` — colors, typography, borders
- `./responsive.md` — breakpoints and mobile-first
- `./advanced.md` — pseudo states, group hover, parent selectors
- `./properties.md` — full property-shortcut map
- `./pseudo.md` — full pseudo-shortcut map
- `./debugging.md` — when a class isn't generating
