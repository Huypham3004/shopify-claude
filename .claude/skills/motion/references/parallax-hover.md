# `xo-parallax-hover` — mouse-tracking movement

Element follows the mouse position within its `<xo-parallax>` container — floating product images, 3D tilt cards, magnetic hover.

**NOT for:** scroll-linked motion (→ `xo-parallax-scroll`), one-shot reveal (→ `xo-animate`), simple hover state (→ CSS `:hover`).

## HTML — requires the `<xo-parallax>` parent

```html
<!-- Translate-based (default) -->
<xo-parallax>
  <xo-parallax-hover xo-strength="20">
    <img src="floating-element.png">
  </xo-parallax-hover>
</xo-parallax>

<!-- 3D tilt -->
<xo-parallax>
  <xo-parallax-hover xo-strength="50" xo-3d>
    <div class="card">Tilts toward cursor</div>
  </xo-parallax-hover>
</xo-parallax>
```

## Attributes

| Attr | Type | Default | Description |
|---|---|---|---|
| `xo-strength` | number | `100` | Movement multiplier — higher = more movement |
| `xo-reset-position` | boolean | `true` | Return to center when the mouse leaves the container |
| `xo-3d` | boolean | `false` | 3D perspective rotation instead of translation |
| `xo-inner-width` | string | `fit-content` | CSS width for the inner shadow-DOM wrapper |

## Real 3D depth with `xo-3d` — layer children at different `translateZ`

`xo-parallax-hover xo-3d` tilts content with `perspective(2000px) rotateX/rotateY`. Tilting ONE flat plane reads weak. Depth comes from layering children at different `translateZ` so they parallax against each other on tilt (front shifts more than back) — e.g. image at Z0, title floated to Z≈+60px.

- The transform + `transform-style: preserve-3d` are applied **inside the component's shadow DOM** (`xo-parallax-hover-inner`), NOT on the host — the host stays `transform: none`. Debug there: `ph.shadowRoot.querySelector('xo-parallax-hover-inner')`.
- Slotted light-DOM children inherit that preserve-3d space, so a child with `transform: translateZ(4rem)` floats forward under the hover perspective (visually flat at rest — no perspective until hover).
- **Wrapper trick** — if a layer's own `transform` is already occupied (e.g. its title is an `xo-parallax-scroll` using transform for a fade), wrap it in a plain `<div>` that carries ONLY the `translateZ`; the inner keeps its own transform.
- Prefer Z-layering over brute `xo-strength` — a modest strength (~50–90) with a forward title beats a violent tilt.

```html
<xo-parallax-hover xo-3d xo-strength="90">
  <div class="xo-image"><img …></div>                <!-- base plane, Z0 -->
  <div class="title-3d">                              <!-- CSS: transform: translateZ(4rem) -->
    <xo-parallax-scroll class="title" xo-keyframes="…fade…">New In</xo-parallax-scroll>
  </div>
</xo-parallax-hover>
```

## Nesting scroll + hover on one card

A card can scroll-animate AND hover-tilt at once — nest two providers; each `xo-parallax-*` binds to its NEAREST `<xo-parallax>` ancestor via `closest('xo-parallax, [xo-parallax]')`:

```
<div xo-parallax>                       ← scroll measurement area
  <xo-parallax-scroll>                  ← cluster→spread (binds to outer)
    <a>
      <xo-parallax class="tilt">        ← hover measurement area
        <xo-parallax-hover xo-3d>…</xo-parallax-hover>   ← binds to .tilt
```

(`xo-parallax-scroll`'s tag is not `xo-parallax`, so `closest()` skips it and finds the real provider.)

## Transform-ownership conflict (a parallax owns the transform)

If you bake a resting transform (e.g. each card's fan `rotate`) INTO the scroll keyframes, `xo-parallax-scroll` writes inline `transform` every frame → a CSS `:hover { transform }` on the SAME element is overridden and silently does nothing. To keep a hover move (straighten / lift):

- apply the hover transform on a CHILD (e.g. the inner `<a>`) — counter-rotate by the opposite of the fan angle to stand it upright;
- raise `z-index` on `:hover` (on the card itself, a flex/positioned item) so the lifted card sits above its overlapping neighbours.

> [!IMPORTANT]
> The general rule: **whoever writes inline `transform` every frame wins.** A parallax component always beats a CSS rule on the same element. Put the competing transform on a different element (a child or wrapper).
