# SF-BLOG-01 — Blog template outputs `blog.title` by default

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-BLOG-01`.
Check type: heuristic

## Recipe (any theme)

The blog template's heading must output `blog.title` by default (setting default on, in schema AND every shipped blog template JSON). A custom heading may exist only as an opt-in override.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The blog template shipped with the native title off and a hardcoded custom heading.
- **Fix:** The `blog-header` section gained a `use_blog_title` checkbox (default `true`, also set in every `blog.preset-N.json`). When it is on and `blog` exists, the section passes `blog.title | escape` to `section-heading` through the new optional `title_override` param. The custom heading stays as the off-state and as the fallback outside blog templates.
- **Files:** `blog-header` section liquid + schema, `src/snippets/section-heading/section-heading/*`, `src/pages/blog/blog.preset-*.json`
- **Verify:** `scan-feedback.py --only SF-BLOG-01`; runtime: blog page shows the blog's own title.
