# SF-VARIANT-01 — Swatch availability uses the current selection correctly

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-VARIANT-01`.
Check type: runtime

## Recipe (any theme)

Compute each option value's state from the selected values of the PRECEDING options only (top-down), not from Shopify's full-selection `value.available`; pass the state to every swatch/button/select renderer.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Shopify's `value.available` / `value.variant` reflect the FULL current selection, which struck through values that are valid with a different second option.
- **Fix:** New `product-variant-value-state` snippet computes each value top-down (prefix of preceding selected options + this value → `unavailable` / `disabled` / ''); `product-variant-value` passes `has_state` + `state` to `field-variant-image`, `field-toggle`, `field-select-2-option`.
- **Files:** `src/snippets/product-variant/*`, `field-variant-image`, `field-toggle`, `field-select-2`
- **Verify:** Runtime: product with 2+ options and sparse availability; click through combinations.
- **Gotcha (follow-up, same round):**
  - On real Shopify the captured `{% render %}` of a snippet that starts with a `{% comment %}` doc block carries a leading `"\n"` → `state == 'disabled'` never matched. Always `| strip` the captured state (liquidjs/local preview does not reproduce this).
  - The webcomponent's `getVariantStatus()` reads the FIRST checked input with `xo-unavailable`/`xo-disabled`. With `Hotdog` (sold out, top-down `disabled`) + `M/L` (no variant), Hotdog masked M/L and the button said "Sold out". Fix: a SELECTED value that is `disabled` reports `unavailable` when the full current selection matches no variant.
  - The sold-out / unavailable add-to-cart wrappers only faded the button; the inner `<button>` stayed focusable/clickable by keyboard. `add-to-cart.liquid` now injects `disabled` (`| replace: '<button', '<button disabled'`).
- **Files (follow-up):** `src/snippets/product-variant/product-variant-value-state.liquid`, `product-variant-value.liquid`, `src/snippets/add-to-cart/add-to-cart.liquid`
- **Verify (follow-up):** product with A/B options where one combo has no variant and another is sold out → button reads Unavailable vs Sold out respectively, `button.disabled === true`. Headless Playwright: shim `requestAnimationFrame` with `setTimeout` (hidden tab pauses rAF, so the picker never re-morphs).
