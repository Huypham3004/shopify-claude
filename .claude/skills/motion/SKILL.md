---
name: motion
argument-hint: "[what should move + how]"
description: "The project's authority on wiring MOTION in this Shopify theme using the existing xo-* web components — `xo-animate` (one-shot scroll reveal), `xo-parallax-scroll` (continuous scroll-linked keyframes), `xo-parallax-hover` (mouse-tracking / 3D tilt) — plus the CSS-`@keyframes` / `<xo-marquee>` fallbacks. Invoke WHENEVER someone is authoring or porting an animation, parallax, scroll-linked, or hover-motion effect in `src/`. Triggers: `/motion`, 'làm animation', 'thêm animation cho section', 'thêm parallax', 'hiệu ứng parallax', 'scroll effect', 'hiệu ứng cuộn', 'scroll-linked animation', 'fade up on scroll', 'reveal on scroll', 'animate this section', 'làm chuyển động', 'card nghiêng theo chuột', '3d tilt', 'hover tilt', 'parallax hero', 'add motion/parallax to this', 'xo-parallax', 'xo-animate'. It carries the decision tree (reveal vs scroll-linked vs mouse-tracking vs plain CSS), the full attribute references, and the sharp gotchas (the `xo-start`/`xo-end` innerHeight trap, transform-ownership conflicts, 3D depth via translateZ). DISAMBIGUATION: this skill USES existing DECLARATIVE xo-* motion components (HTML attributes, no code) — to BUILD a brand-new bespoke JS behaviour no xo-* covers use `web-components`; the finishing-pass reveal PROPOSAL (bare `xo-animate xo-cascade`) is `polish` (which defers here for the full family); pure CSS styling with no motion is `xo-css`/`scss`. Verify exact current attrs against the `xo-components` MCP."
---

# Motion — wiring `xo-animate` · `xo-parallax-scroll` · `xo-parallax-hover`

The reference for adding motion to this theme with the existing xo-* web components. It answers **which component** a given motion needs and **how to wire it correctly** — the components are declarative (HTML attributes, no code), and the mistakes that bite are subtle (a reversed parallax, a hover that silently does nothing, a flat-looking 3D tilt). This skill is knowledge, not a pipeline.

## When to use / when NOT to

- **Use** when authoring or porting any animation / parallax / scroll-linked / hover-motion effect in `src/`.
- **Bespoke JS behaviour** no xo-* component covers (a custom drag, a physics cursor, a split-text engine) → the **`web-components`** skill (it builds a new `xo-*` TS component). This skill only wires the *existing* declarative components.
- **The finishing-pass reveal proposal** (the bare `<xo-animate xo-cascade>` auto-mode, offered unprompted after a port) is **`polish`**'s job — `polish` defers HERE for anything beyond that bare cascade (a specific effect, any parallax, 3D).
- **Pure CSS styling** with no motion → `xo-css` / `scss`.

> [!IMPORTANT]
> The **`xo-components` MCP** is the live source-of-truth for exact current attributes: `mcp__xo-components__get_component` with name `xo-animate` / `xo-parallax-scroll` / `xo-parallax-hover`. The tables in this skill are the distilled fast-reference for judgment — verify any attribute you don't use daily against the MCP before writing it, rather than trusting memory.

## Decision tree — run this on every motion you see or plan

```
Motion
│
├─ One-shot reveal when the element enters the viewport
│  (opacity 0→1 + a small translate, plays ONCE, doesn't reverse on scroll-back)
│  → xo-animate                         → references/animate.md
│
├─ Transform tied CONTINUOUSLY to scroll position
│  (backdrop drifts as you scroll, layered parallax, scale/rotate-through-scroll,
│   horizontal scroll-storytelling)
│  → xo-parallax-scroll                 → references/parallax-scroll.md
│
├─ Element responds to MOUSE position
│  (card tilts toward cursor, floating image, 3D parallax on hover, magnetic float)
│  → xo-parallax-hover                  → references/parallax-hover.md
│
├─ Simple :hover state change
│  (color shift, scale 1.02, shadow grow on hover)
│  → plain CSS `:hover` + transition. No JS, no xo-*.
│
├─ Looping / continuous animation independent of scroll & mouse
│  (rotating badge, ticker, blinking caret)
│  → CSS `@keyframes` + `animation`. For a marquee specifically → `<xo-marquee>`.
│
└─ Click-triggered open/close (modal, drawer, accordion, tabs)
   → xo-modal · xo-toggle · xo-collapse · xo-tabs  (interaction tags, NOT motion tags)
```

**Quick rule:** motion **stops when scroll stops** → `xo-parallax-scroll`. Motion **plays once and stays** at the end state → `xo-animate`. Motion **follows the mouse** → `xo-parallax-hover`. Motion **independent of scroll/mouse/click** → CSS `@keyframes`.

## `xo-animate` — one-shot scroll reveal (quick summary)

Element enters viewport → animates in once → settles. Most "fade up / slide in / zoom in on scroll" patterns. Default to the **auto-cascade** form for grouped reveals — it inherits the global motion rhythm and auto-orders siblings, no magic numbers:

```html
<xo-animate xo-type="fade-up" xo-cascade>
  <div>…content…</div>
</xo-animate>
```

It already **respects `prefers-reduced-motion`** (and mobile-reduced-motion) and **auto-plays inside** `<xo-carousel>` / `<xo-modal>` / `<xo-popover>` / `<xo-tabs-pane>` when the parent becomes visible (not on scroll). Full effect list (`fade-*`, `zoom-*`, `rotate-*-up`, `snake-*`, `3d-up`, `goo-1..7`), the easing set, stagger controls, and the archetype × motion matrix → **`references/animate.md`**.

## The two parallax components require a `<xo-parallax>` parent

Both `<xo-parallax-scroll>` and `<xo-parallax-hover>` **must** be children of a `<xo-parallax>` container (it defines the measurement area) — otherwise they render-error ("must be a child of xo-parallax"). Only wrap elements that actually need parallax; the container has a real performance cost, so don't blanket the page in `<xo-parallax>` "for safety".

- Continuous scroll-linked keyframes, the **`xo-start`/`xo-end` innerHeight gotcha**, computed keyframe values, step-mode → **`references/parallax-scroll.md`**.
- Mouse-tracking, 3D tilt with real `translateZ` depth, nesting scroll+hover, transform-ownership conflicts → **`references/parallax-hover.md`**.

## Anti-patterns (the ones that actually bite)

- ❌ **`xo-parallax-scroll` for a fade-in-on-enter** — it plays IN REVERSE when the user scrolls back up. One-shot reveals want `xo-animate`.
- ❌ **`xo-animate` AND `xo-parallax-scroll` on the same element** — they fight over `transform`. Pick one.
- ❌ **Unquoted keyframe keys** — `xo-keyframes` is JSON: `{"0%": {...}}`, never `{0%: {...}}`.
- ❌ **Forgetting the `<xo-parallax>` parent** — render error for both parallax components.
- ❌ **`xo-step-mode` on continuous parallax** — it teleports between keyframes; continuous motion needs the default smooth lerp. Step-mode is ONLY for discrete threshold reveals + a CSS transition.
- ❌ **Expecting `:hover { transform }` to work on an element whose transform is driven by a parallax** — it's overwritten every frame; put the hover move on a CHILD (see parallax-scroll/hover refs → transform-ownership).
- ❌ **Wrapping every section in `<xo-parallax>`** — measurement cost adds up; wrap only what needs it.

## References

- `references/animate.md` — `xo-animate` full attributes + easing list + cascade + behaviour + archetype×motion matrix + "described motion → keyframes JSON" recipe.
- `references/parallax-scroll.md` — `xo-parallax-scroll` structure, keyframe↔scroll mapping, the `xo-start`/`xo-end` gotcha + per-element recipe, computed keyframe values, step-mode, custom effects, events.
- `references/parallax-hover.md` — `xo-parallax-hover` translate + 3D tilt, real `translateZ` depth layering, nesting scroll+hover, transform-ownership conflict.

## Related skills

- `web-components` — build a NEW bespoke `xo-*` JS behaviour when no existing component fits.
- `polish` — finishing-pass reveal proposal (bare `xo-animate xo-cascade`); defers here for the full family.
- `xo-css` / `scss` — the styling the motion reflects (states, transitions). `figma-to-liquid` / `design-to-liquid` — invoke this skill when porting a design's motion.
