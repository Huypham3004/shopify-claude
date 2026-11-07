# SF-FILTER-01 — Zero-result filter values must be disabled

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-FILTER-01`.
Check type: heuristic + runtime

## Recipe (any theme)

In the filter-value loop, disable every value with `count == 0` that is not active (real `disabled` on the input or the component's disabled attribute, not only CSS), and style the disabled state. Re-check after the AJAX re-render.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Filter values with `count == 0` stayed clickable.
- **Fix:** `fieldset-fields.liquid` adds `xo-disabled` on `<xo-filters-field>` when `value.count == 0 and value.active == false`. The checkbox SCSS greys it out.
- **Files:** `src/snippets/filters-form/**/fieldset-fields.liquid`, checkbox field SCSS
- **Verify:** Runtime: apply a filter so another value drops to 0; after the AJAX re-render it must still be disabled and not toggle with the keyboard.
