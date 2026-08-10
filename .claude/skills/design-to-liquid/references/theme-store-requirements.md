# Theme Store Requirements — Porting Checklist

Distilled from the canonical source — **<https://shopify.dev/docs/storefronts/themes/store/requirements.md>** (Shopify serves a `.md` version of its docs for agents; that URL is the source of truth).

This reference is **scoped to what matters while porting** (schemas, sections, snippets, copy). Submission-only items (theme name uniqueness, demo store, documentation/support contact form, Lighthouse benchmarks, browser matrix, the `.scss` ban, Skeleton-only codebase) are out of scope here — see §8, revisit at submission.

The schema validator (`scripts/validate-schema.py`) enforces most of the label/terminology rules as warnings. Use `--strict` to escalate warnings to errors for CI.

> [!NOTE]
> **Reconcile protocol — don't fetch the live doc on every port.** This local file is the daily driver: offline, cheap, mapped to this project's conventions, and paired with the executable validator. The full live `.md` is large and **mostly submission-scope** (browser matrix, demo stores, support SLAs, naming rules…), so loading it into every port is noise. Instead:
> - **Periodically reconcile** — `/system-upgrade` (or a "check theme store requirements" ask) fetches the live `.md`, diffs it against this file, and updates the distilled subset below.
> - **Fetch the full live doc on demand ONLY at real submission-QA time**, when you need the complete required-features checklist (accelerated checkout, faceted filtering, `<shopify-account>`, Follow-on-Shop `login_button`, unit pricing, Shop Pay Installments, rich media, predictive search, etc.).
> - _Last reconciled: 2026-08-10._

## 1. Setting labels — terminology rules

Every setting except `header` / `paragraph` MUST have a non-empty `label`.

### Shopify-approved terms (use these)

| Use | Don't use |
| - | - |
| heading | title |
| subheading | sub-heading |
| body text | main text |
| home page | homepage |
| slideshow | slider |
| favicon | shortcut icon, website icon |
| sidebar | side bar |
| signup | sign-up, sign up |
| navigation | menus, menu |
| main menu | primary nav |
| secondary menu | secondary nav |
| footer menu | navigation menu |
| button label | button text, button name, CTA label |
| Horizontal position | X position |
| Vertical position | Y position |
| social media | social, social sharing |
| social media icons | social media buttons |
| top bar | meta-nav, search bar |
| bottom bar | below footer, legal |
| heading (HTML) | title (HTML) |
| checkout | check out |
| cart type | Ajax, Ajaxify |
| .png | PNG, png |
| use (file-upload / actionable) | show, enable |
| show (basic hide/show) | use, enable |
| enable (apps / major layout) | use, show |

### Phrasing rules

- **Sentence case** — capitalize first word + proper nouns only. (`"Background image"` not `"Background Image"`.)
- **No questions** — `"Use a custom logo"`, not `"Use a custom logo?"`.
- **No ampersands** — write `"Food and beverage"`, not `"Food & beverage"`.
- **Declarative + active voice** — buttons/actions start with a verb.
- **State subject once per section heading** — avoid `"slideshow"`, `"slideshow color"`, `"slideshow image"`. Use one header `"Slideshow"`, then `"Color"`, `"Image"`.
- **No "Lorem Ipsum"** style placeholder defaults — write realistic demo copy.
- **No numbered options for multi-option settings** (exception: colors). Prefer `"First"`, `"Second"`, `"Closing"` or other descriptive ordinals.

### American English spelling (UK forms banned)

| Use | Don't use |
| - | - |
| canceled | cancelled |
| catalog | catalogue |
| center, centered | centre, centred |
| color | colour |
| customize | customise |
| gray | gray |
| organize | organise |
| favorite | favourite |
| behavior | behaviour |
| theater | theatre |

### Technical-spec format

When a label references a size/format requirement, use this exact form:

- Image size: `[N] x [N]px (required/recommended)`
- Aspect ratio: `[N]:[N] aspect ratio (required/recommended)`
- File format: `[N] x [N]px .[ext] (required/recommended)`
- Word count: `[N] words (max)`

Better to put format hints in the `info` field rather than the `label`.

## 2. Setting defaults & resource references

- **Resource defaults** (image_picker, collection, product, blog, etc.) must reference resources that exist in **every** store. Don't ship a default pointing at `shopify://products/xyz`.
- **`link_list` defaults** must be `main-menu` (Header) or `footer` (Footer).
- **`metaobject_type`** must be a standard definition only — never an app-owned or custom-defined metaobject.
- **No demo-store metafields** in shipped `.json` files (custom metafields don't exist in fresh installs).
- **No Lorem Ipsum / onboarding copy** — write realistic defaults.

## 3. Required global theme settings

Lives in `src/config/global-schema/*.js` compiled into `settings_schema.json`.

- **Colors** — minimum 4 colors. Every background color must have a foreground color counterpart.
- **Fonts** — use `font_picker` only (no custom font upload). Provide a default like `default: 'work_sans_n6'`. Load bold/italic/bold-italic variants via the `font_modify` filter in CSS.
- **`theme_info` section** in `settings_schema.json` (theme name, version, author, docs URL).
- **Favicon** image picker.
- **Logo** image picker supporting varied aspect ratios (landscape + portrait).

## 4. Required architectural elements

- **Custom Liquid section** available on every section-supporting template (with a `type: 'liquid'` setting).
- **Custom Liquid blocks** in any section where `@app` blocks might be used.
- **`@app` block support** in main product and featured product sections.
- **Header / footer** rendered inside section groups (not hardcoded in layout).
- **Multi-level (nested) menus**, faceted search filtering, newsletter signup, search template + predictive search, country/currency + language selectors when international.

## 5. HTML / accessibility (per-template / per-snippet)

- `<html lang="{{ request.locale.iso_code }}">` in `theme.liquid` — already done.
- All `<img>` need `alt` (use `image | image_url | image_tag: alt: ...`). The project's `image` snippet handles this.
- **Form inputs** need a unique `id` AND a `<label for="...">` matching that id. `aria-label` alone is not sufficient per Shopify's accessibility checklist.
- Headings `h1`–`h6` visually distinct.
- Body text ≥ 4.5:1 contrast; non-text and ≥18pt text ≥ 3:1.
- Keyboard accessible; focus visible; tab order matches DOM order.
- Touch targets ≥ 24×24 CSS px (with WCAG 2.2 exceptions).

## 6. Performance (run at submission time)

Average Lighthouse score (across product/collection/home, desktop+mobile):
- Performance ≥ 60
- Accessibility ≥ 90

## 7. Validator coverage

`scripts/validate-schema.py` enforces:

- ✅ Compile (catches syntax / import / helper errors)
- ✅ Unique setting IDs
- ✅ range `min`/`max` present
- ✅ select/radio `options` array present
- ✅ `inline_richtext` default contains only inline tags
- ✅ `richtext` default top-level is `<p>` / `<ul>` / `<ol>` / `<h1>`–`<h6>`
- ✅ Block type resolution
- ✅ Color scheme group sanity (`--theme` mode)
- ✅ Preset values match schema constraints (`--preset` mode)
- ⚠️ **NEW** Label presence (every non-header setting needs a label)
- ⚠️ **NEW** Label hygiene — no `&`, no `?`, AmE spelling, banned phrases (CTA, X/Y position, homepage, slider, sub-heading, shortcut icon, "Title"→"Heading")

Run:

```bash
# Single section
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/

# All sections + presets
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all

# Escalate warnings to errors (CI-friendly)
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all --strict

# Theme settings sanity
python .claude/skills/design-to-liquid/scripts/validate-schema.py --theme
```

## 8. Out of scope for porting (revisit at submission)

- Theme name + preset name uniqueness audit (1–2 words, < 30 chars, no industry/company names)
- **Lighthouse benchmark testing** against the Shopify benchmark dataset — submission bar is **Performance ≥ 60 (avg)** and **Accessibility ≥ 90 (avg)** across Product/Collection/Home on desktop + mobile. (Our `/lighthouse-audit` skill uses a stricter aspirational 90+ across all four categories — see its `thresholds.md`.)
- **No `.scss` at submission** — Shopify's rule: "must not use Sass, or include `.scss` / `.scss.liquid` files; native CSS only." This project authors `.global.scss` but the build pipeline (scss-glob + xo-css plugin) **compiles to `.css` in `shopify/`** before shipping, so the shipped output is compliant. At submission, verify `shopify/` contains no `.scss` / `.scss.liquid`.
- **Approved codebase** — Shopify accepts only the **Skeleton Theme** as the Theme Store starting codebase (no themes derived from Dawn/Horizon). This project is custom source under `src/` compiled to `shopify/`, not derived — just record it at submission.
- Browser/device compatibility QA · Demo store buildout + transfer · Documentation portal + support contact form (reply-within-2-business-days SLA)
- SEO metadata snippet + Open Graph / Twitter card tags + Google rich product snippets
- Theme-level required features: accelerated checkout buttons, faceted search filtering, `<shopify-account>` in header, Follow-on-Shop (`login_button`), Shop Pay Installments banner, Pickup availability, Selling plans, unit pricing, rich product media, predictive search, product recommendations, country/language selector
- App block opt-ins on product/featured-product sections · Multi-language + multi-currency UX

These are systemic/submission-level features; checking them off requires holistic work after the section port is complete. When you reach submission QA, **fetch the live `.md`** (see the Reconcile protocol at the top) for the authoritative, current list — it evolves.
