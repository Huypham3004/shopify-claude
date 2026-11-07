# SF-RTE-03 — Links inside inline richtext keep word order and flow

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-RTE-03`.
Check type: heuristic + runtime

## Recipe (any theme)

Never output inline_richtext as a direct child of flex/grid or inside an inherited `direction: rtl`; wrap it in its own inline element. Never put richtext inside an `<a>` — use a full-bleed overlay link beside the text instead.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Marquee: `xo-marquee[xo-direction=rtl]{direction:rtl}` (webcomponent CSS) was inherited by an `inline-flex` phrase, so its text node + `<a>` became flex items laid out right-to-left. Card: the whole tile was an `<a>`; a merchant link in the inline_richtext title made `<a>` nested in `<a>`, the parser closed the card link early and the title/CTA fell out below the tile.
- **Fix:** Marquee: `xo-marquee[xo-direction="rtl"] xo-marquee-item > * { direction: ltr }` (+ `[dir="rtl"]` counterpart) in `src/styles/base/content.scss`. Card: tile root → `<div>`, card link → full-bleed overlay `<a>` (absolute, inset 0, visually-hidden label) under the text body; body `pointer-events: none` with `a { pointer-events: auto }`; hover/focus via `:has()`. Same fix in `_box-banner`.
- **Files:** `src/styles/base/content.scss`, promise-tiles section, `src/blocks/collection/_box-banner/*`
- **Verify:** `scan-feedback.py --only SF-RTE-03` (any `<a>` whose content outputs inline_richtext/richtext); runtime: add a link mid-text in a marquee, card and heading.
