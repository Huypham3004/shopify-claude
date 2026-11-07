# SF-SECTION-01 — Header and footer limited to one instance

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-SECTION-01`.
Check type: static

## Recipe (any theme)

Exactly ONE header section type and ONE footer section type (`limit: 1` is per type). Alternative looks become a `layout` select dispatching to layout snippets, with layout-only settings guarded by `visible_if`. Remove old section files from src, build output and the store.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The theme shipped several header section types (`header`, `header-editorial`, `header-overlay`) and footer types, each with `limit: 1`. The limit is per type, so merchants could activate two headers at once.
- **Fix:** Merge into ONE `header` and ONE `footer` section. Each gets a `layout` select first in the schema; the section liquid becomes a dispatcher (`{% case section.settings.layout %}` → `{% render 'header-<layout>' %}`), each former section's markup moves to `src/snippets/header-layout/header-<layout>/` (`footer-layout/…`), and layout-only settings are guarded with `visible_if` (`visible("layout","default")`). `{% content_for 'blocks' %}` stays in the dispatcher (not allowed in snippets). Merge the group JSON into one entry per section, delete the old section folders AND the stale `shopify/sections/*.liquid` build output, and remove them from the store (`push -n` does not delete).
- **Files:** `src/groups/headers/header/*`, `src/groups/footers/footer/*`, `src/snippets/{header,footer}-layout/**`, `header-group.json`, `footer-group.json`
- **Verify:** Editor: the header/footer group's Add section picker shows `Header (1/1)` / `Footer (1/1)` disabled and no other header/footer type. Details: `design-to-liquid/references/header-port.md`.
