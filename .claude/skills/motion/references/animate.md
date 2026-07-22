# `xo-animate` — one-shot scroll-reveal

Element enters the viewport → animates in once → settles at the final state. Most "fade up / slide in / zoom in on scroll" patterns, plus cascading staggers across siblings.

**NOT for:** continuous scroll-linked motion (→ `xo-parallax-scroll`), looping animation (→ CSS `@keyframes`), mouse-tracking (→ `xo-parallax-hover`).

## HTML

```html
<xo-animate xo-type="fade-up" xo-duration="500">
  <h2>Reveals on scroll</h2>
</xo-animate>
```

### Cascading stagger across siblings — the default for groups

```html
<xo-animate xo-type="fade-up" xo-cascade xo-constant="100"><div>Item 1</div></xo-animate>
<xo-animate xo-type="fade-up" xo-cascade xo-constant="100"><div>Item 2</div></xo-animate>
<xo-animate xo-type="fade-up" xo-cascade xo-constant="100"><div>Item 3</div></xo-animate>
```

`xo-cascade` auto-assigns increasing order among sibling `xo-animate` elements; delay between each = `xo-constant` ms (default 75). Prefer this over hand-setting `xo-order` — it inherits the global rhythm and needs no magic numbers.

## Attributes

| Attr | Type | Default | Description |
|---|---|---|---|
| `xo-type` | string | `fade-up` | Effect (see list below) |
| `xo-duration` | number | `500` | Duration (ms) |
| `xo-order` | number | `0` | Stagger index (`delay = order * xo-constant`). Not needed with `xo-cascade`. |
| `xo-constant` | number | `75` | Stagger step (ms) |
| `xo-strength` | number | `1` | Intensity multiplier for directional/rotate types |
| `xo-cascade` | boolean | `false` | Auto-stagger across siblings |
| `xo-easing` | string | `easeLight` | Named easing (see list below) |
| `xo-disabled` | boolean | `false` | Render visible immediately (no animation) |
| `xo-item-used` | boolean | `false` | Animate `<xo-animate-item>` children individually instead of the container |
| `xo-scroll-forced` | boolean | `false` | Force scroll trigger even inside carousel/modal/popover/tabs |

**`xo-type` values:** `none` · `fade` · `fade-up` · `fade-down` · `fade-left` · `fade-right` · `zoom-in` · `zoom-out` · `rotate-left-up` · `rotate-right-up` · `width-increment` · `snake-up` · `snake-down` · `snake-left` · `snake-right` · `3d-up` · `goo-1` … `goo-7`

**`xo-easing` values:** `easeLight` · `easeInOut` · `easeOut` · `easeIn` · `ease` · `easeInBack` · `easeOutBack` · `easeInOutBack` · `easeInCirc` · `easeOutCirc` · `easeInOutCirc` · `easeInCubic` · `easeOutCubic` · `easeInOutCubic` · `easeInExpo` · `easeOutExpo` · `easeInOutExpo` · `easeInQuad` · `easeOutQuad` · `easeInOutQuad` · `easeInQuart` · `easeOutQuart` · `easeInOutQuart` · `easeInQuint` · `easeOutQuint` · `easeInOutQuint` · `easeInSine` · `easeOutSine` · `easeInOutSine` · `easeInBounce` · `easeOutBounce` · `linear` · `spring`

> Verify any `xo-type` / `xo-easing` you don't use daily against `mcp__xo-components__get_component` name `xo-animate` before writing it — the sets evolve.

## Behaviour notes

- Plays **once**, doesn't reverse on scroll-back (one-shot).
- Auto-disables on `prefers-reduced-motion` / mobile-reduced-motion devices.
- Inside `<xo-carousel>` / `<xo-modal>` / `<xo-popover>` / `<xo-tabs-pane>` it plays when the parent becomes visible, not on scroll.
- Sets a `xo-visible` attribute when complete — useful for chaining reveals via `xo-visible-binding="<selector>"`.

## Archetype × motion matrix (taste defaults)

A starting point per Jung brand archetype — override when the brief calls for it.

| Archetype | Reveal (`xo-type`) | Easing | Duration | Parallax appetite |
|---|---|---|---|---|
| Sage / Ruler / Lover (luxury) | `fade` / `fade-up` (strength 0.5) | `easeOutQuart` | 600–800ms | Minimal — restrained backdrop drift only |
| Caregiver / Innocent | `fade-up` | `easeOutCubic` | 500ms | Light hover-tilt (`xo-3d` strength 30) |
| Creator / Magician | `zoom-in`, `rotate-*-up`, `goo-*` | `easeOutBack` | 600–900ms | Heavy multi-layer parallax encouraged |
| Hero / Explorer | `fade-up` strength 1.5, `snake-up` | `easeOutQuart` / `spring` | 500–700ms | Mid — scroll-linked headings |
| Outlaw / Jester | `3d-up`, `goo-1..3` | `easeInOutBack` / `spring` | 700–1000ms | Heavy, intentionally over-the-top |
| Everyperson | `fade` (strength 1) | `easeOut` | 400ms | None / minimal |

## Translating a described motion → `xo-keyframes` JSON

You won't see motion in a static Figma frame or a screenshot — but the **user may describe it** ("the heading fades up and settles as you scroll past"), or a **Figma prototype / smart-animate** may imply it. When the motion is continuous-scroll-linked (→ `xo-parallax-scroll`), turn the described frames into keyframes:

```
Frame 0 (off-screen):   opacity 0,    translateY(80px)
Frame 1 (entering):     opacity 0.3,  translateY(50px)
Frame 2 (centered):     opacity 0.8,  translateY(10px)
Frame 3 (above center): opacity 1.0,  translateY(0)
```

becomes

```json
{ "0%": { "y": 80, "opacity": 0 }, "33%": { "y": 50, "opacity": 0.3 },
  "66%": { "y": 10, "opacity": 0.8 }, "100%": { "y": 0, "opacity": 1 } }
```

Trim intermediate keys when linear interpolation fits (drop 33%/66% if 0→100 is a straight line); keep them when the curve is non-linear (common for design-driven motion). If the motion is a one-shot reveal instead, it's just `xo-animate` — no keyframes needed.
