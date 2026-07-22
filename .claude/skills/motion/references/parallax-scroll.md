# `xo-parallax-scroll` — continuous scroll-linked keyframes

Element transform/opacity changes **continuously** as the page scrolls past it — hero backdrops moving slower than foreground, layered editorial parallax, scale/rotate-through-scroll, cinema-style reveals where the user controls playback by scrolling.

**NOT for:** one-shot reveal on enter (→ `xo-animate`), mouse-tracking (→ `xo-parallax-hover`), simple hover transform (→ CSS `:hover`).

## HTML structure — the `<xo-parallax>` parent is required

```html
<!-- xo-parallax = container that defines the measurement area -->
<xo-parallax style="height: 200vh;">
  <xo-parallax-scroll
    xo-keyframes='{ "0%": { "y": 100, "opacity": 0 },
                    "100%": { "y": 0, "opacity": 1 } }'>
    <h2>Animates as the page scrolls past</h2>
  </xo-parallax-scroll>
</xo-parallax>
```

Without the `<xo-parallax>` ancestor it render-errors ("must be a child of xo-parallax").

## How keyframe percentages map to scroll

By default, `0%`→`100%` maps to the **`<xo-parallax>` ANCESTOR** passing the viewport:

- **0%** = the container's TOP edge touches the BOTTOM of the viewport (just entering from below)
- **100%** = the container's BOTTOM edge leaves the TOP of the viewport (just exited above)
- **50%** = the container is centered in the viewport
- Any percentage key works (`"33.33%"`, `"75%"`); interpolation is linear between adjacent keys
- Keys can also be JS expressions: `'this.offsetHeight / 2': { "y": 50 }` — evaluated with `this` / `window` / `document` / `container` / `offset()` in scope

When one `<xo-parallax>` wraps MANY `<xo-parallax-scroll>` children, they all share that ONE progress (good for synced choreography; wrong when each element should key to its own entry — then use `xo-start`/`xo-end`).

## 🛑 The `xo-start` / `xo-end` gotcha (the #1 cause of a reversed parallax)

`xo-start` / `xo-end` re-key the 0%→100% range. Each is a JS expression returning a **scroll-Y position in px**. From the component source:

```ts
getStart = (container) => xoStart ? eval(xoStart) : offset(container).top - window.innerHeight
getEnd   = (container) => xoEnd   ? eval(xoEnd) - window.innerHeight   // ← innerHeight SUBTRACTED
                                  : offset(container).top + container.offsetHeight
// progress 0→1 as scrollY goes from getStart → getEnd; keyframe % maps onto that.
```

- **Scope in the expression:** `container` = the nearest `<xo-parallax>` ancestor · `this` = the `<xo-parallax-scroll>` element · `offset(el).top` = element's absolute document-Y · plus `window` / `document`.
- 🛑 **`xo-end` has `window.innerHeight` SUBTRACTED for you; `xo-start` does NOT.** Whatever scroll-Y you want 100% to land on, the `xo-end` expression must return **that + window.innerHeight**. Forget it and `to` can fall **below** `from` → the range inverts → the animation runs **backwards / inaccurately**.

**Recipe — animate as the ELEMENT itself enters from the bottom** (per-element, independent of container length):

```html
<!-- 0% when this element's top is at the viewport bottom; 100% ~30% down the viewport -->
<xo-parallax-scroll
  xo-start="offset(this).top - window.innerHeight"
  xo-end="offset(this).top + window.innerHeight * 0.7"
  xo-keyframes="{ '0%': { 'x': '7rem' }, '100%': { 'x': 0 } }">
```

Math: `from = offset(this).top − ih`; `to = (offset(this).top + 0.7·ih) − ih = offset(this).top − 0.3·ih`. `from < to` ✓. Travel range = `0.7·ih` → **bigger `+ innerHeight * K` = slower/longer** reveal. Pick K by where 100% lands: `K=1` → element top at viewport top · `K=0.5` → centre · `K=0.3` → 70%-down (quick).

**Reversed / inaccurate checklist:** log `from` & `to` (or the rendered transform at 3 scroll points) → ensure `from < to` → remember `xo-end` already subtracted `innerHeight` → confirm `container` is the intended `<xo-parallax>` (not a stray ancestor).

## Supported keyframe properties

`x`, `y` (number = px, string e.g. `"50vh"` allowed) · `scale`, `scaleX`, `scaleY` · `rotate`, `rotateX`, `rotateY` · `skew`, `skewX`, `skewY` · `opacity` · `width`, `height` · `backgroundPositionY`, `backgroundSizeX`, `backgroundSizeY` · `brightness`, `hueRotate`, `contrast`, `blur`, `grayscale` · `borderRadius` · `color` (hex/rgb/rgba string) · `strokeDasharray` (SVG) · `d` (SVG path morph) · `videoTime` (sync video to scroll) · `groupImg` · `fontSize` · + any custom prop via `customEffects()`.

## Attributes

| Attr | Type | Default | Description |
|---|---|---|---|
| `xo-keyframes` | JSON object | — | **Required.** Keys `"<pct>%"`, values = CSS-prop objects |
| `xo-breakpoints` | JSON object | — | Responsive override: `{ "1000": { "0%":{…}, "100%":{…} } }` (key = max-width) |
| `xo-lerp-ease` | number | `0.08` | Smoothing (lower = smoother/slower; higher = snappier). Auto-set to `1` on mobile |
| `xo-backface-visibility` | string | `hidden` | CSS backface-visibility |
| `xo-fit-content` | boolean | `true` | Element width fits content |
| `xo-start` | JS-expr string | `offset(container).top - innerHeight` | Scroll-Y for 0%. Used verbatim. |
| `xo-end` | JS-expr string | `offset(container).top + container.offsetHeight` | Scroll-Y for 100%. ⚠ result has `innerHeight` SUBTRACTED internally — add it back |
| `xo-step-mode` | boolean | `false` | Step interp — JUMPS to the crossed keyframe (no lerp). Only for discrete threshold reveals + a CSS transition |
| `xo-mobile-disabled` | boolean | `false` | Disable on mobile |
| `xo-observed` | string | — | Changing it re-inits the parallax (Shopify design mode) |

## Computed keyframe VALUES — layout math in the attr, no JS file

Keyframe **values** (not only keys) can be JS-expression STRINGS, evaluated with `window` / `document` / `container` (the `<xo-parallax>`) / `offset()` / `this` (the `<xo-parallax-scroll>`). Drive transforms from live geometry with zero `.ts`:

```html
<!-- cards gather to the row centre, then spread to their natural slots on scroll -->
<div xo-parallax class="cards" style="position:relative;">   <!-- offsetParent + measurement area -->
  <xo-parallax-scroll xo-step-mode xo-fit-content="false"
    xo-keyframes="{ '0%': { 'x': 'container.clientWidth/2 - this.offsetLeft - this.clientWidth/2', 'scale': 0.72 },
                    '22%': { 'x': 0, 'scale': 1 }, '100%': { 'x': 0, 'scale': 1 } }">
    <a class="card">…</a>
  </xo-parallax-scroll>
  <!-- …more cards, same expression — each converges to centre then returns… -->
</div>
```

- `this.offsetLeft` resolves against the nearest positioned ancestor → make the `<xo-parallax>` container `position: relative`.
- Re-evaluated on resize (the component recalculates start/end + values) → responsive without manual math.
- Single quotes inside the attr are fine here (parsed as a JS object, not strict JSON).

## `xo-step-mode` + CSS transition = "snap, but smooth"

`xo-step-mode` does NOT interpolate — it JUMPS to the value of the keyframe step the scroll has crossed (an instant teleport on its own). Pair it with a CSS `transition` on the animated element so each jump ANIMATES:

```scss
.card { transition: transform 0.7s var(--out-quart); }  /* plays each step snap as a reveal */
```

Keyframes `{ 0% cluster · 22% spread · 100% spread }` + step-mode → cards hold clustered until scroll passes 22%, then snap → the transition plays the snap as a one-shot reveal; re-clusters on scroll-up.

**Use step-mode** for discrete state/threshold reveals (cluster→spread, snap-to-slot). **Do NOT** use it on continuous scroll-linked motion (backdrop drift, layered parallax, scale-through-scroll) — that wants the default smooth lerp; step-mode there is janky.

## Custom effects (non-standard props)

```html
<xo-parallax style="height:200vh;">
  <xo-parallax-scroll class="parallax-custom"
    xo-keyframes='{"33.33%":{"opacityCustom":0},"100%":{"opacityCustom":1}}'>
    <div>XO</div>
  </xo-parallax-scroll>
</xo-parallax>
```

```ts
const el = document.querySelector('.parallax-custom');
el.addEventListener('xo:parallax-scroll:init', () => {
  el.customEffects(({ element, createValue, EMPTY }) => {
    const v = createValue('opacityCustom');
    if (v !== EMPTY) element.style.setProperty('opacity', `${v}`);
  });
});
```

## Common patterns

```html
<!-- Hero backdrop slower than foreground -->
<xo-parallax style="height:120vh;">
  <xo-parallax-scroll xo-keyframes='{"0%":{"y":0},"100%":{"y":-200}}'>
    <img src="hero-bg.jpg">
  </xo-parallax-scroll>
</xo-parallax>

<!-- Heading scales + fades through scroll -->
<xo-parallax style="height:200vh;">
  <xo-parallax-scroll xo-keyframes='{
    "33%": { "y": 0, "scale": 1, "opacity": 1 },
    "100%": { "y": 200, "scale": 50, "opacity": 0 } }'>
    <h1>XO</h1>
  </xo-parallax-scroll>
</xo-parallax>
```

Sticky section-stacking (sticky cards revealing over each other) uses the same `<xo-parallax>` → `<xo-parallax-scroll>` structure scoped to a `.xo-section`.

## Events

- `xo:parallax-scroll:init` (bubbles) — fires when initialized.
- `xo:parallax:end` — listened by the component to recalculate start/end positions.
