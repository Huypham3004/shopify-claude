# SF-MENU-01 — Nested menus are usable at every level on mobile

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-MENU-01`.
Check type: heuristic (3 levels rendered) + runtime

## Recipe (any theme)

Level-2/3 mobile panels must not live inside an ancestor with `transform`, `filter` or `overflow` (they become the containing block for `position: fixed`). Render nested panels as siblings/portals, size them with `100dvh`, give each a collision-free name.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The nested `<xo-modal>`s were rendered inside the parent drawer. The parent's leftover `transform` and `overflow-y: auto` became the containing block for their `position: fixed`, so the panels were offset and clipped.
- **Fix:** Render level-2/3 modals as siblings outside the scrolling body (or portal them), use `100dvh`, and make the modal names collision-free (`parent-child`, not `parentchild`).
- **Files:** mobile menu drawer snippet + its SCSS
- **Verify:** Runtime, 390px viewport: open a 3-level menu; every panel fills the screen, scrolls, and Back/Close work.
