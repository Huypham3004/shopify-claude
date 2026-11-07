# SF-CONTRAST-01 — Modal close button has enough contrast

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-CONTRAST-01`.
Check type: runtime

## Recipe (any theme)

Webcomponent overlays (lightbox, modals, drawers) must not paint controls a fixed `#fff`/`#000`; use scheme colors (foreground ink on a background chip) and check ≥3:1 in every scheme. Check the icon's **rendered** paint, not `color`: an SVG with a `fill="#fff"` / `stroke` attribute ignores `color`, so also set `svg { fill: currentColor }` (or `stroke`) on the control.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The PDP lightbox (`xo-gallery-portal`) uses the theme background as backdrop but the webcomponent paints close/prev/next/counter `#fff`.
- **Fix:** Override in `product-info-media-base.global.scss`: ink `color(foreground)` + a `color(background, 0.85)` round chip behind close/arrows/counter.
- **Files:** `src/pages/product/snippets/product-info-media/product-info-media-base/product-info-media-base.global.scss`
- **Verify:** Runtime: open lightbox, quick view, cart drawer, search, popups, menu in each color scheme; measure ≥3:1.

- **Follow-up (2026-11-06):** the R1 override only set `color`; the `xo-gallery-close/prev/next` SVGs carry a hard-coded `fill="#fff"` attribute, so the icons still painted white on the light theme backdrop (computed `color` read black, which hid the bug). Fix: `xo-gallery-close svg, xo-gallery-prev svg, xo-gallery-next svg { fill: currentColor; }` in the same file. Verify: `getComputedStyle(svg).fill` (not `.color`) is the foreground; lightbox screenshot at 1440 and 390.
