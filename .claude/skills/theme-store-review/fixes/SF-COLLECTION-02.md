# SF-COLLECTION-02 — Product cards show compare-at price with the Sale badge

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-COLLECTION-02`.
Check type: static + runtime

## Recipe (any theme)

Same root cause as SF-COLLECTION-01 — route all card price branches through the shared price snippet and keep the Sale badge on by default.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Same root cause as SF-COLLECTION-01: the `price_varies` branch skipped the `price` snippet, so the compare-at strikethrough never rendered next to the Sale badge.
- **Fix:** Same fix as SF-COLLECTION-01 (route both branches through the `price` snippet). Confirm the Sale badge setting is on by default.
- **Files:** `src/snippets/product-card/product-card-style-*/product-card-*.liquid`
- **Verify:** Runtime: a product on sale with varying prices shows badge + strikethrough on the card.
