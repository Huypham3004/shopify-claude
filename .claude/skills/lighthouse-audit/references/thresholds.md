# lighthouse-audit — thresholds & what the numbers mean

## Pass thresholds (per category)

Lighthouse colour-codes scores: **0–49 red, 50–89 orange, 90–100 green**. This skill's default **pass = 90+** (green) for every category — an **aspirational, internal** bar. The `parse-report.py --pass N` flag changes it if the user wants a softer bar (e.g. `--pass 80` for an early-stage port).

> [!IMPORTANT]
> **Internal bar ≠ Shopify Theme Store submission bar.** The actual Theme Store minimums (per the requirements doc — `design-to-liquid/references/theme-store-requirements.md` §8) are **Performance ≥ 60 (average)** and **Accessibility ≥ 90 (average)** across Product/Collection/Home on desktop + mobile — measured on Shopify's benchmark dataset, not an arbitrary URL. Best Practices and SEO have no numeric submission floor. So when the user's goal is *"will this pass Theme Store submission?"*, judge Performance against **60**, Accessibility against **90**, and treat our default 90-everywhere as the higher quality target. State which bar you're reporting against.

| Category | Pass | What a low score usually means for a theme port |
|----------|------|--------------------------------------------------|
| Performance | ≥ 90 | Heavy/oversized images, render-blocking CSS/JS, layout shift, slow LCP element. Often the most actionable for theme work — but see the app-script caveat below. |
| Accessibility | ≥ 90 | Contrast failures, missing alt/labels, bad heading order, missing landmarks — **rendered-DOM** checks (catches contrast that static markup audit can't). |
| Best Practices | ≥ 90 | Console errors, deprecated APIs, missing `doctype`, insecure requests, image aspect-ratio mismatch. |
| SEO | ≥ 90 | Missing meta description, non-crawlable links, missing `hreflang`, tap targets too small, missing `title`. |

State PASS/FAIL per category and per form-factor (mobile + desktop) explicitly — a theme can pass desktop and fail mobile.

## The 5 metrics (Performance)

Performance score is a weighted blend of these. Report each with its measured value and whether it clears the "good" bar (Core Web Vitals field thresholds, which Lighthouse lab values approximate):

| Metric | Means | Good (mobile lab) | Weight in LH 10+ score |
|--------|-------|-------------------|------------------------|
| **FCP** First Contentful Paint | time to first text/image painted | ≤ 1.8 s | 10% |
| **LCP** Largest Contentful Paint | time to the largest above-fold element (often a hero image) | ≤ 2.5 s | 25% |
| **TBT** Total Blocking Time | main-thread blocked time (lab proxy for INP/interactivity) | ≤ 200 ms | 30% |
| **CLS** Cumulative Layout Shift | visual stability; unitless | ≤ 0.1 | 25% |
| **Speed Index** | how quickly the page visually fills in | ≤ 3.4 s | 10% |

LCP and CLS are the two a theme port most directly controls: size the hero with `image_url` + width/height attributes, and reserve space for images/embeds to avoid shift.

## Shopify-specific perf caveat — separate theme issues from app/platform noise

A merchant's installed **third-party apps** (reviews, upsell, chat, analytics, cookie banners) inject their own render-blocking scripts and large payloads. These routinely drag the **Performance** score down **even on a perfectly built theme** — they are not the theme's fault and not fixable from `src/`.

When reporting, **split perf findings into two buckets**:

- **Theme-owned** — audits pointing at resources under the store's own theme assets, images served from `cdn.shopify.com/.../files|/s/files`, the theme's CSS/JS. These are actionable → hand to `design-to-liquid` / `polish`.
- **App / platform** — third-party domains, app-block scripts, Shopify-injected scripts (e.g. `shopify-features`, web pixels). Flag them as **"app/platform — not theme-owned"** and don't task them to a theme skill. Note them so the merchant knows the score isn't all the theme.

Use the failing-audit details (the offending URLs) to decide the bucket. When unsure, say so rather than mislabeling.

## What "passing" realistically looks like

A clean theme port commonly lands **Accessibility / Best Practices / SEO at 90–100** and **Performance lower on mobile** purely from apps + image weight. Don't treat a sub-90 mobile Performance as a theme defect by default — investigate the failing audits first and bucket them.
