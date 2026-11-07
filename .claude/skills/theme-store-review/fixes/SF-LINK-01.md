# SF-LINK-01 — Actionable text looks clickable

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-LINK-01`.
Check type: runtime

## Recipe (any theme)

Every actionable text (clear/remove-all, empty-state links) gets link affordance — underline or button style — on both collection and search templates.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Collection empty state passed `xo-link-empty` (no underline) into `use_fewer_filters_html`.
- **Fix:** Added `.xo-link-empty { text-decoration: underline }` in `main-collection.global.scss` (search page already used `td:underline`).
- **Files:** `main-collection.global.scss`
- **Verify:** Runtime: filter a collection to zero results; "remove all" is underlined.
