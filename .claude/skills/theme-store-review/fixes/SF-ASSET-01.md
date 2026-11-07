# SF-ASSET-01 — No minified CSS/JS shipped (except third-party / ES6)

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-ASSET-01`.
Check type: static (on the built `shopify/assets`)

## Recipe (any theme)

No `.min.css`/`.min.js` of our own in `assets/`: disable minification in the build for theme CSS/JS, ship our webcomponent CSS unminified under a non-`.min` name, update every `asset_url` reference (theme, password, gift card layouts). Check the BUILD output.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** Vite minified theme CSS, and the webcomponents CSS shipped as `.min.css`.
- **Fix:** Ship the unminified build of the xo-webcomponents CSS under a non-`.min` name, set `build.minify: false` (or `cssMinify: false`) for theme CSS, and update the `asset_url` references in `theme.liquid`, `password.liquid` and `gift_card.liquid`.
- **Files:** `vite.config.js`, `src/layout/{theme,password,gift_card}.liquid`
- **Verify:** `npm run build` then `scan-feedback.py --only SF-ASSET-01` (reads `shopify/assets`).
