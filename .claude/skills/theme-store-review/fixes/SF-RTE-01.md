# SF-RTE-01 — RTE content is styled consistently everywhere

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-RTE-01`.
Check type: heuristic + runtime

## Recipe (any theme)

Define the full RTE element set (h1–h6, p, lists, blockquote, tables) once under `.rte` in a global stylesheet, and put `rte` on every wrapper that outputs merchant richtext.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** `.rte` defined only part of the heading ladder, so h1/h4–h6 fell back to theme heading tokens (h4 32px > rte h2 28px) and looked different per template.
- **Fix:** Define the full h1–h6 ladder (and blockquote/ul/ol) once under `.rte` in `src/styles/base/content.scss`, and make sure every merchant-content wrapper (article, product/collection description, page content, richtext settings) carries the `rte` class.
- **Files:** `src/styles/base/content.scss`, wrappers that output richtext
- **Verify:** Runtime: paste the same h1–h6 + lists content into an article, product description, collection description and a rich-text section; they must match.
