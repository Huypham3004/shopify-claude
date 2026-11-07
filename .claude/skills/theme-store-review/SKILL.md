---
name: theme-store-review
description: "Pre-submit gate for the Shopify Theme Store: re-checks a theme against EVERY comment Shopify's reviewers have sent back on any of our themes (stored in a theme-agnostic ledger), so the same rejection never happens twice. Two modes. AUDIT: run the static scanner + triage + optional runtime checks, report PASS/FAIL per ledger item with file:line evidence and fix direction (works on any theme on the shared base — Folio, Pawra, Hexon, Ronin, Stray). Every reviewer round is kept verbatim in `feedback/R<n>-<date>-<theme>.md` and every audit re-checks all rounds; each fix is recorded as a reusable playbook in `fixes/<ID>.md` so the next theme fixes it faster. INGEST: save a new round of reviewer feedback, map each bullet into the ledger (new IDs or `Seen in` on existing ones) and add scanner checks. Triggers: `/theme-store-review`, 'check trước khi submit', 'kiểm tra trước khi submit lại', 'rà feedback shopify', 'theme đã đạt feedback chưa', 'so sánh theme với feedback shopify', 'pre-submit check', 'theme store review', 'shopify reviewer feedback', 'lưu feedback shopify', 'thêm feedback mới từ shopify', 'shopify trả về feedback', 'theme bị reject', 'feedback lần 2', 'lưu cách fix', 'ghi lại cách fix'. Do NOT use for Lighthouse scores (lighthouse-audit), general a11y/animation polish (polish), or live editor QA of one section (editor-qa) — this skill may hand items to those."
argument-hint: "[audit [theme-root]] | [ingest <feedback.md>]"
---

# theme-store-review

**"Would Shopify reject this theme again for something they already told us about?"**

```
feedback/R<n>-<date>-<theme>.md ← every reviewer round, verbatim; each bullet marked → SF-<ID>
references/feedback-ledger.md   ← the generalised requirements, stable IDs (SF-*)
fixes/<ID>.md                   ← how each item was fixed, per theme (root cause, files, steps)
scripts/scan-feedback.py        ← one static check per ID + per-round coverage table
            │
   AUDIT ───┼─► scan → triage → (runtime checks) → report → ask → fix (playbook first) → record
   INGEST ──┴─► save round file → map bullets → ledger items → scanner checks → sync
```

Three layers of memory, each with one job:
- **`feedback/`** is the evidence: what Shopify actually wrote, round by round, **for every
  theme we submit** (Folio, Pawra, Hexon, …). The theme in a file name only says where the
  feedback was raised; the requirement applies to **every** theme, past and future. The
  scanner reads every round on each audit, so the audited theme is checked against all
  feedback ever received on any theme. Format and naming: `feedback/README.md`.
- **The ledger** turns those bullets into theme-agnostic requirements. A requirement learned
  from the Folio review is checked on Pawra too, because reviewers re-test the same list.
- **`fixes/`** is what makes the next theme fast: a theme-agnostic **Recipe** per item, then a
  history of each theme where it was fixed (root cause, files, change). The next fix is
  "apply the recipe", not "investigate again".

Keep everything here theme-agnostic. Theme names appear only as the *source* of a round,
a `Seen in` line, a reviewer example or a history entry — never as a condition on whether a
requirement applies.

## Mode A — AUDIT (default)

### A1. Target
Theme root = the current repo unless the user names another (e.g. `../pawra`).
It must contain `src/`. For SF-ASSET-01 the build output `shopify/assets` must be
fresh. If `src/` is newer than `shopify/`, offer `npm run build` first (it does not touch `src/`).

### A2. Read the ledger
Read `references/feedback-ledger.md` in full (~230 lines). Every item has a
**Requirement**, **How to verify** and a **Fix playbook** link.
Items with several `Seen in` rounds are repeat offenders. Check those hardest.
You don't need to read the `feedback/` round files here — the scanner covers them — unless
a ledger item is ambiguous and you want the reviewer's exact words.

### A3. Run the scanner
```bash
python3 .claude/skills/theme-store-review/scripts/scan-feedback.py <theme-root> --max 15
```
Use `--only SF-A11Y-03,SF-ASSET-01` to re-check after a fix, or `--json` for machine use.
The script is read-only. It exits with code 1 when any item is FAIL.

The output has three parts: the per-ID table (with the rounds each ID was raised in and
whether a playbook exists), a **Reviewer rounds** table (per round: how many of its items
FAIL / WARN / MANUAL / PASS now), and the evidence. If it prints **ROUNDS ✗**, a round file
has a bullet with no `→ SF-<ID>` marker — that round was never fully ingested, so run
Mode B on it before trusting the audit.

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

| ID | Item | Rounds | Status | Evidence | Fix direction | Playbook |
|----|------|--------|--------|----------|---------------|----------|
| SF-BLOG-01 | blog.title by default | R1 | ❌ | src/sections/blog-header/blog-header.liquid — no blog.title | render blog.title in the heading; title setting on by default | fixes/SF-BLOG-01.md |

Rounds re-checked on <audited theme>:
R1 (raised on Folio, 2026-11-05) — 25 items: ❌ 1 · ❓ 11 · ⚠️ 2 · ✅ 11
R2 (raised on Pawra, …)          — …
```
- Order: ❌ → ❓ (needs runtime) → ⚠️ (accepted risk, with reason) → ✅.
- Every ❌ cites `file:line` and a fix direction. When `fixes/<ID>.md` exists, take the
  direction from its newest entry and say so — that is the fastest route to a passing fix.

### A7. Fix only on approval
- Ask which items to fix.
- **Read `fixes/<ID>.md` before touching code** — whichever theme it was first fixed on.
  Start from the **Recipe**; the history entries show the concrete files on the shared base
  (usually the same paths). Investigate from scratch only when the root cause differs.
- Then follow the project's own rules: the group override ladder for `src/groups/**`, asking before editing shared snippet markup, and validators after `.liquid` and `schema.js` edits.
- Re-run the scanner with `--only <ids>` to confirm each fix.
- Hand off when it fits better elsewhere: a11y markup → `polish`, perf and score items → `lighthouse-audit`, responsive or editor checks → `editor-qa`.

### A8. Record the fix
A fix that isn't written down gets re-investigated on the next theme. After each item is
verified, append a `### <Theme> — R<n> (<date>)` entry under **History** to `fixes/<ID>.md` (create the file
from the format in `fixes/README.md` if missing) with **Root cause**, **Fix**, **Files** and
**Verify**. If the recipe from an earlier theme worked unchanged, a one-line entry saying so
is enough — it proves the recipe transfers. If this theme needed something the Recipe
didn't say, update the Recipe so it stays correct for every theme.

If the reviewer's issue was something the scanner reported as PASS or only WARN, the scanner
has a blind spot: tighten the check in `scripts/scan-feedback.py`, confirm it now FAILs on the
pre-fix code (e.g. `git stash` the fix, re-run `--only <ID>`, `git stash pop`), and note it
under **Gotcha**. Example: SF-SETTINGS-01 read only `default:` lines, so demo links in preset
block settings slipped through until R1.

## Mode B — INGEST new reviewer feedback

Use this when the user pastes new reviewer feedback or points to a file (e.g. one dropped in
`themes/shopify-feedback/`). The permanent copy always goes into `feedback/` (step 0).

0. **Save the round** verbatim as `feedback/R<n>-<YYYY-MM-DD>-<theme>.md` (next free `n`
   across all themes — never restart numbering for a new theme; `<theme>` = the theme the
   feedback was raised on; date received) and add its row to `feedback/README.md`. Don't edit the
   reviewer's text.
1. **Parse** every bullet into `{stage, area, reviewer text, links}`.
2. **Match** each one against the existing ledger:
   - Mark each top-level bullet in the round file with ` → SF-<ID>` (several: `→ SF-A, SF-B`).
   - **Same requirement:** append `R<n> <Theme>` to its `Seen in` line. Add new reviewer examples or root causes.
   - **New requirement:** create `SF-<AREA>-<NN>` using the template below.
   - **Generalise it:** write the requirement so it applies to any theme — a new round on
     Pawra adds checks that Folio and every later theme must also pass. Keep theme-specific details (file names, demo copy) only as *Reviewer example* or *Fix pattern*.
3. **Add the round** to the ledger's *Sources* table, linking `../feedback/<file>`.
4. **Add a scanner check** for any new item that can be detected statically (`static` or `heuristic`), registered in `CHECKS` with the same ID. Otherwise add it as `manual(...)` with a grep hint. Run the scanner on the current theme to confirm the new check fires on the known-bad case.
5. **Re-run the scanner.** It must print no **ROUNDS ✗** line — every bullet mapped.
   **Show** the user the diff summary: new IDs, IDs seen again, and checks added.
6. **Sync:** offer to copy the updated skill folder to the sibling themes (see below).

Ledger item template:
```markdown
### SF-<AREA>-<NN> — <one-line requirement>
- **Seen in:** R<n> <Theme>
- **Check:** static | heuristic | runtime | manual
- **Requirement:** <theme-agnostic rule, citing Shopify's wording>
- **Reviewer example:** <what they saw>
- **How to verify:** <static signal + runtime steps>
- **Fix playbook:** `fixes/SF-<AREA>-<NN>.md`
- Docs: <shopify.dev link>
```
Never delete items. Mark obsolete ones `Status: retired`.

## Using it on another theme (Pawra, Hexon, …)

- **Audit another theme from here:**
  `python3 .claude/skills/theme-store-review/scripts/scan-feedback.py ../pawra`
- **Share it through the `.claude` distribution repo** (`long-hp/shopify-claude`). After an
  INGEST or a new playbook entry, run `pnpm pr-claude "<what changed>"`; other themes pick it
  up with `pnpm update-claude`. That keeps one canonical ledger, `feedback/` and `fixes/` for
  all themes instead of drifting copies.
- Without the distribution repo, copy the folder:
  `rsync -a .claude/skills/theme-store-review/ ../<theme>/.claude/skills/theme-store-review/`
  (no `--delete`: round files and playbook entries are append-only, so merge — take the union —
  when two copies have both gained entries).
- After a new round is ingested, the new items apply to every theme: re-audit the sibling
  themes, not only the one the feedback was raised on.

## Gotchas
- **SF-ASSET-01** reads the **build output**. A clean `src/` still fails if vite minifies on build (`build.minify: true`). The fix belongs in the build config and the asset names, not in `shopify/` by hand.
- **Reachability checks** (SF-PRODUCT-01, SF-COLLECTION-01/02, SF-BLOG-01) follow literal `{% render 'x' %}` chains from the sections listed in the shipped `src/pages/<page>/*.json`.
  - A dynamic render or `content_for 'blocks'` produces WARN "not reachable". Trace it by hand.
  - Quick-view-only code does not count for the product page.
- **SF-I18N-01** compares the **built** `shopify/locales`, which are merged and namespaced, when it exists. Rebuild before trusting key parity. Strings in TypeScript are not scanned, so grep `src/scripts` for English literals as well.
- Several header or footer section *types* each with `limit: 1` can still coexist (SF-SECTION-01). Verify that in the editor.
