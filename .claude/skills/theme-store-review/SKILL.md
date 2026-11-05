---
name: theme-store-review
description: "Pre-submit gate for the Shopify Theme Store: re-checks a theme against EVERY comment Shopify's reviewers have sent back on any of our themes (stored in a theme-agnostic ledger), so the same rejection never happens twice. Two modes. AUDIT: run the static scanner + triage + optional runtime checks, report PASS/FAIL per ledger item with file:line evidence and fix direction (works on any theme on the shared base — Folio, Pawra, Hexon, Ronin, Stray). INGEST: read a new round of reviewer feedback, merge it into the ledger (new IDs or `Seen in` on existing ones) and add scanner checks. Triggers: `/theme-store-review`, 'check trước khi submit', 'kiểm tra trước khi submit lại', 'rà feedback shopify', 'theme đã đạt feedback chưa', 'so sánh theme với feedback shopify', 'pre-submit check', 'theme store review', 'shopify reviewer feedback', 'lưu feedback shopify', 'thêm feedback mới từ shopify', 'shopify trả về feedback', 'theme bị reject'. Do NOT use for Lighthouse scores (lighthouse-audit), general a11y/animation polish (polish), or live editor QA of one section (editor-qa) — this skill may hand items to those."
argument-hint: "[audit [theme-root]] | [ingest <feedback.md>]"
---

# theme-store-review

**"Would Shopify reject this theme again for something they already told us about?"**

```
references/feedback-ledger.md   ← every reviewer comment, generalised, stable IDs (SF-*)
scripts/scan-feedback.py        ← one static check per ledger ID
            │
   AUDIT ───┼─► scan → triage WARN/MANUAL → (runtime checks) → report → ask → fix
   INGEST ──┴─► raw feedback → ledger items → scanner checks → sync to other themes
```

The ledger is the memory. It is **theme-agnostic**: a requirement learned from the
Folio review is checked on Pawra too, because reviewers re-test the same list.

## Mode A — AUDIT (default)

### A1. Target
Theme root = the current repo unless the user names another (e.g. `../pawra`).
It must contain `src/`. For SF-ASSET-01 the build output `shopify/assets` must be
fresh. If `src/` is newer than `shopify/`, offer `npm run build` first (it does not touch `src/`).

### A2. Read the ledger
Read `references/feedback-ledger.md` in full (~250 lines). Every item has a
**Requirement**, **How to verify** and, often, a **Fix pattern** from a past fix.
Items with several `Seen in` rounds are repeat offenders. Check those hardest.

### A3. Run the scanner
```bash
python3 .claude/skills/theme-store-review/scripts/scan-feedback.py <theme-root> --max 15
```
Use `--only SF-A11Y-03,SF-ASSET-01` to re-check after a fix, or `--json` for machine use.
The script is read-only. It exits with code 1 when any item is FAIL.

Verdicts:
- `PASS`: static evidence satisfies the item.
- `FAIL`: static evidence violates it.
- `WARN`: candidates were found and each needs a look.
- `MANUAL`: the item can't be decided statically.

### A4. Triage. Never forward raw scanner output.
The scanner is a heuristic radar. False positives and negatives are expected. For each item:
- **FAIL / WARN:** open every evidence location and decide whether it is real. Drop false positives, saying why in one line. Examples: `tabindex="-1"` on a cloned marquee slide is intentional. A literal `id` in a snippet rendered only once on the page is fine.
- **PASS:** spot-check one evidence file. A reachable token is not proof that it renders, because it may sit behind a setting that defaults off. SF-COLLECTION-02 failed review with the code present.
- **MANUAL:** follow the ledger's *How to verify*. Read the code it points at. When the code alone can't settle the item, mark it **needs runtime**.

### A5. Runtime checks (only when a storefront is reachable)
Most runtime items need a browser: SF-MENU-01, SF-NEWSLETTER-01, SF-A11Y-01/02/05, SF-CONTRAST-01, SF-VARIANT-01, SF-I18N-01 locale switch, SF-RTE-02/03.
- Use the Playwright MCP against a storefront preview URL the user gives you.
- Dev stores are usually password-protected. Ask for the password or an unlocked tab. Never audit the `/password` splash page.
- Mobile checks use a 390×844 viewport.
- If no storefront is available, list these items under "Needs runtime" with exact click-paths. Don't guess a verdict.

### A6. Report (in the user's language)
```
## Theme Store pre-submit — <theme> (<date>)
FAIL n · Needs runtime n · PASS n

| ID | Item | Status | Evidence | Fix direction |
|----|------|--------|----------|---------------|
| SF-BLOG-01 | blog.title by default | ❌ | src/sections/blog-header/blog-header.liquid — no blog.title | render blog.title in the heading; title setting on by default |
```
- Order: ❌ → ❓ (needs runtime) → ⚠️ (accepted risk, with reason) → ✅.
- Every ❌ cites `file:line` and a fix direction, reusing the ledger's *Fix pattern* when there is one.

### A7. Fix only on approval
- Ask which items to fix. Then follow the project's own rules: the group override ladder for `src/groups/**`, asking before editing shared snippet markup, and validators after `.liquid` and `schema.js` edits.
- Re-run the scanner with `--only <ids>` to confirm each fix.
- Hand off when it fits better elsewhere: a11y markup → `polish`, perf and score items → `lighthouse-audit`, responsive or editor checks → `editor-qa`.

## Mode B — INGEST new reviewer feedback

Use this when the user pastes or points to a new feedback file (canonical inbox:
`themes/shopify-feedback/*.md`).

1. **Parse** every bullet into `{stage, area, reviewer text, links}`.
2. **Match** each one against the existing ledger:
   - **Same requirement:** append `R<n> <Theme>` to its `Seen in` line. Add new reviewer examples or root causes.
   - **New requirement:** create `SF-<AREA>-<NN>` using the template below.
   - **Generalise it:** write the requirement so it applies to any theme. Keep theme-specific details (file names, demo copy) only as *Reviewer example* or *Fix pattern*.
3. **Add the round** to the ledger's *Sources* table.
4. **Add a scanner check** for any new item that can be detected statically (`static` or `heuristic`), registered in `CHECKS` with the same ID. Otherwise add it as `manual(...)` with a grep hint. Run the scanner on the current theme to confirm the new check fires on the known-bad case.
5. **Show** the user the diff summary: new IDs, IDs seen again, and checks added.
6. **Sync:** offer to copy the updated skill folder to the sibling themes (see below).

Ledger item template:
```markdown
### SF-<AREA>-<NN> — <one-line requirement>
- **Seen in:** R<n> <Theme>
- **Check:** static | heuristic | runtime | manual
- **Requirement:** <theme-agnostic rule, citing Shopify's wording>
- **Reviewer example:** <what they saw>
- **How to verify:** <static signal + runtime steps>
- **Fix pattern (<Theme>):** <what fixed it, once known>
- Docs: <shopify.dev link>
```
Never delete items. Mark obsolete ones `Status: retired`.

## Using it on another theme (Pawra, Hexon, …)

- **Audit another theme from here:**
  `python3 .claude/skills/theme-store-review/scripts/scan-feedback.py ../pawra`
- **Install the skill in another theme** so it works from that repo: copy the whole folder.
  `rsync -a --delete .claude/skills/theme-store-review/ ../<theme>/.claude/skills/theme-store-review/`
- The ledger and scanner are the same in every copy. After an INGEST, sync the copies so no theme misses a lesson. When copies diverge, the one with the most `Seen in` rounds is canonical.

## Gotchas
- **SF-ASSET-01** reads the **build output**. A clean `src/` still fails if vite minifies on build (`build.minify: true`). The fix belongs in the build config and the asset names, not in `shopify/` by hand.
- **Reachability checks** (SF-PRODUCT-01, SF-COLLECTION-01/02, SF-BLOG-01) follow literal `{% render 'x' %}` chains from the sections listed in the shipped `src/pages/<page>/*.json`.
  - A dynamic render or `content_for 'blocks'` produces WARN "not reachable". Trace it by hand.
  - Quick-view-only code does not count for the product page.
- **SF-I18N-01** compares the **built** `shopify/locales`, which are merged and namespaced, when it exists. Rebuild before trusting key parity. Strings in TypeScript are not scanned, so grep `src/scripts` for English literals as well.
- Several header or footer section *types* each with `limit: 1` can still coexist (SF-SECTION-01). Verify that in the editor.
