# SF-SETTINGS-01 — No demo resource handles in setting defaults

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-SETTINGS-01`.
Check type: static

## Recipe (any theme)

Clear store-specific links (`/products/…`, `/collections/<handle>`, `/pages/…`, `shopify://…`) from schema `default:`s AND preset section/block settings; leave them blank and make sure the liquid hides the link when blank — never `| default: '#'`. Review shipped template JSON links too: the Theme Store packager strips `shopify://` references, so every resource link ships blank and only plain paths survive (and 404).

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Reviewer saw `Caption link` default to `/products/morning-oil` in the "Social video" block. The schema setting had no default — the handles were in the section **preset** (`preset-1.js` block `settings.link`), which the old scanner did not read.
- **Fix:** Remove store-specific links from schema defaults AND from preset block/section settings (`createPreset({... blocks: [{ settings: { link } }] })`). Leave the url blank; the liquid must already hide the link when blank (`{% if block.settings.link != blank %}`). Allowed: blank, `/collections/all`, `/`. Template JSON (`src/pages/**`) links to `/pages/…`, `/products/…` are demo content — clear them too when the target won't exist on a fresh store.
- **Files:** `src/sections/social-video/preset-1.js` (any `preset-*.js`, `schema.js`), `src/pages/**/*.json`
- **Verify:** `scan-feedback.py --only SF-SETTINGS-01` (preset + schema defaults → FAIL, template JSON → WARN).

### Folio (Lotio package) — runtime re-audit (2026-11-06)

- **Root cause:** On the uploaded package, 9 links 404'd: plain store paths in template JSON (`/products/radiance-recover-serum`, `/pages/shipping|returns|…`, `/collections/the-edit`, `/blogs/journal`, `/blogs/news/tagged/<tag>`). The Theme Store packager strips `shopify://` references (images, products, collections, `shopify://collections/all`) from templates but keeps plain paths — so plain paths 404 on every store, and every `shopify://` link arrives blank. Liquid that did `href="{{ link | default: '#' }}"` then shipped dead `#` links, and the 404 CTA (link stripped) rendered as an inert `<button>`.
- **Fix:** Cleared every plain store path in `src/pages/**/*.json` (kept `/blogs/news`, `/collections/all`). Liquid renders no `<a>` when the link is blank: promise-tiles (overlay + CTA), before-after credit (`<span>`), contact shortcuts and blog topic pills (plain text), hero-parallax secondary link, social-video button, box-banner frame/CTA, category-cards (`<div>` card), feature-rows button. 404 CTA falls back to `routes.all_products_collection_url`.
- **Files:** `src/pages/{blog,home,page,product}/*.json`, `src/sections/{promise-tiles,before-after,hero-parallax,social-video,category-cards,feature-rows}/*.liquid`, `src/pages/page/contact/contact.liquid`, `src/pages/404/main-404/main-404.liquid`, `src/blocks/collection/_box-banner/_box-banner.liquid`
- **Gotcha:** Scanner allowed anything under `/blogs/news/…` (tag pages slipped) and never looked at `| default: '#'`. Both now WARN; confirmed against the pre-fix code with `git stash`. Test the **packaged** theme, not `src`: crawl every internal link on the preview (`curl` with the storefront password + `?preview_theme_id=`) and expect no 404.
- **Verify:** `scan-feedback.py --only SF-SETTINGS-01` → PASS; re-upload the package and re-crawl links.
