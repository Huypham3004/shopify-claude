# SF-PRODUCT-01 — Product page shows a "taxes included" notice

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-PRODUCT-01`.
Check type: static

## Recipe (any theme)

Render the `cart.taxes_included` notice (existing `products.product.*include*tax*` key) inside the product page's price block, inside whatever wrapper re-renders on variant change.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The tax notice existed only in quick view.
- **Fix:** Added `{% if cart.taxes_included %}<p class="…__tax">{{ 'products.product.price.include_tax' | t }}</p>{% endif %}` inside the `price` block of `product-info-content.liquid`, inside `<xo-product-will-change>`, so it survives variant re-renders. The locale key already existed in every language.
- **Files:** `src/pages/product/snippets/product-info-content/product-info-content.liquid` (+ `.global.scss`)
- **Verify:** `scan-feedback.py --only SF-PRODUCT-01`; runtime with tax-inclusive prices enabled.
