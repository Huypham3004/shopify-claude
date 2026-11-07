# SF-RTE-02 — Lists keep markers next to text when alignment changes

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-RTE-02`.
Check type: heuristic + runtime

## Recipe (any theme)

`.rte ul, .rte ol { list-style-position: inside; padding-inline-start: 0 }`, `.rte li > p:first-child { display: inline }`, re-indent nested lists; `rte` on every merchant-content wrapper.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** UA `padding-inline-start: 40px` pushed centred lists off-axis, and `<p>` inside `<li>` dropped the marker onto its own line.
- **Fix:** `.rte ul, .rte ol { list-style-position: inside; padding-inline-start: 0 }` + `.rte li > p:first-child { display: inline }` + nested lists re-indented. Every merchant-content wrapper (`page.content`, descriptions) must carry `rte`.
- **Files:** `src/styles/base/content.scss`
- **Verify:** Runtime: a list in a rich-text section aligned left/center/right.
