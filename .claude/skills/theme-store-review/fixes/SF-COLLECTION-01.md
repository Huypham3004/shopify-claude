# SF-COLLECTION-01 — Product cards output unit price

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-COLLECTION-01`.
Check type: static

## Recipe (any theme)

Make every product-card style render price through the shared price snippet for BOTH `price_varies` branches, so unit price and compare-at come from one place.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Product cards for products with varying prices rendered only a bare "From $X" string, bypassing the `price` snippet that outputs unit price.
- **Fix:** In every product-card style, render `{% render 'price', product: product %}` for the `price_varies` branch too (it outputs "From", compare-at and `unit_price`), instead of hand-built `from_price_html`.
- **Files:** `src/snippets/product-card/product-card-style-*/product-card-*.liquid`
- **Verify:** `scan-feedback.py --only SF-COLLECTION-01`; runtime: a product with unit price (e.g. 100 ml) shows it on the collection card.
