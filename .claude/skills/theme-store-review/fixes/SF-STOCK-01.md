# SF-STOCK-01 — Untracked inventory is not "Out of stock"

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-STOCK-01`.
Check type: heuristic

## Recipe (any theme)

Before showing "Out of stock", require tracked inventory (`inventory_management != blank`) and `inventory_policy != 'continue'`; use `<= 0`. Mirror the logic in the JS variant update. Also grep EVERY snippet for `inventory_quantity` — static variant data handed to JS (e.g. `product-static-data.liquid` → `sold_out` / `add_to_cart_text`) must use `variant.available`, which already folds in tracking and policy.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Inventory status branched on `inventory_quantity == 0` without checking whether inventory was tracked.
- **Fix:** `inventory-base.liquid` sets `untracked = true` when `current_variant.inventory_management == blank` or (`inventory_policy == 'continue'` and quantity <= 0) and renders a count-less "In stock, ready to ship" box; tracked out-of-stock check widened from `== 0` to `<= 0` (oversold stock goes negative).
- **Files:** `src/snippets/inventory-status/inventory-base/inventory-base.liquid`
- **Verify:** `scan-feedback.py --only SF-STOCK-01`; runtime: variant with untracked inventory.

### Folio — re-audit (2026-11-06)

- **Root cause:** The R1 fix covered only the PDP inventory box. `product-static-data.liquid` (static variant JSON for `xo-product-liquid-static`, rendered in the cart-drawer free-shipping suggestion carousel) still derived `sold_out` and `add_to_cart_text` from `inventory_quantity > 0`, so an untracked / continue-selling variant read "Sold out" after a variant switch there.
- **Fix:** Both branches now use `variant.available`.
- **Files:** `src/snippets/product-helpers/product-static-data.liquid`
- **Verify:** `scan-feedback.py --only SF-STOCK-01` → PASS. Runtime on `tesstttttt` (dev store): PDP correct for every variant (Cat/Dog "In stock, ready to ship" + Add to cart, Hotdog "Out of stock" + disabled Sold out). The suggestion carousel only renders with `enable_free_shipping_suggestions` + a suggestion collection set — enable it to see the path live.
- **Gotcha:** The scanner caught this file in R1 as a WARN too; a PASS on the PDP path does not clear other render paths.
