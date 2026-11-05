---
name: live-sync
argument-hint: "[preset|label] (empty = every demo)"
description: Pull the LIVE theme of each demo store into demo-live/<Label>/ and reconcile its template JSON back into the matching per-preset source template under src/pages/. Use whenever merchandising work was done directly in a demo store's Theme Editor and the repo is now behind — triggers "/live-sync", "pull theme live", "pull demo live", "kéo theme live về", "đồng bộ theme live", "so sánh json live với preset", "cập nhật preset từ store", "check demo live có gì thay đổi", "sync live templates". Maps each preset in src/config/settings_data.js (Verso→preset-1, Timbre→preset-2, Wiggle→preset-3) to its store via demo-live/stores.json, pulls templates/*.json from the live theme with `shopify theme pull --live --nodelete`, then diffs each live template against src/pages/**/<name>.<preset>.json (e.g. live index.json ↔ index.preset-1.json) and applies ONLY the files the user selects. Never pushes to a store, never edits liquid or schema. Do NOT use it to port a design (design-to-liquid), diff the design repo (design-sync), or commit (git).
---

# /live-sync — Live demo theme → preset templates

## Identity

One-way bridge: **live demo store → repo**. Merchants (and we) merchandise in the Theme Editor; those edits live only on the store's live theme until they're pulled back into the per-preset JSON that ships with the theme. This skill pulls them and reconciles them, file by file, with the user approving every write.

**NOT**: a deploy tool (never pushes), a design diff (`design-sync`), a porting pipeline (`design-to-liquid`), a commit workflow (`git`).

---

## Hard rules

1. **Pull only.** Every Shopify call is `shopify theme pull --live --nodelete`. Never `theme push`, never `theme publish`, never `--development` (dev themes are scratch, not the demo).
2. **Never auto-apply.** The diff report is produced first; the user multi-selects which templates get overwritten. No silent writes, no "apply all" shortcut.
3. **Preset isolation.** Live content from `Verso` may only ever land in `*.preset-1.json`. The mapping is `demo-live/stores.json` — never guess a store from memory.
4. **`.all.json` is shared.** A live template whose only source match is `<name>.all.json` feeds EVERY preset. Reported as `SHARED-DIFF` and applied only after the user is told it hits all demos.
5. **`demo-live/` is a throwaway artifact** — gitignored, like `shopify/`. Never hand-edit it, never make it the source of truth for anything but a diff.
6. **Scope = `templates/*.json` only.** Section groups (`src/groups/**/*group.preset-N.json`) and theme settings (`src/config/presets/preset-N.js`) are deliberately out of scope — see "Out of scope" at the end.
7. Don't touch `.env` `PRESET=`. It selects the build target and has nothing to do with which demo is being synced.

---

## Invocation

```
/live-sync                # pull + diff all demos in stores.json
/live-sync Verso          # one demo (label or preset id both work)
/live-sync --diff-only    # skip the pull, diff whatever is already in demo-live/
```

---

## Step 0 — Bootstrap `demo-live/stores.json` (first run only)

If `demo-live/stores.json` doesn't exist, build it and **show it to the user for confirmation before pulling anything**:

- Preset order + demo names → `src/config/settings_data.js` (`presets: { Verso: preset1, … }`).
- Store domains → `package.json` scripts (`push` → preset-1, `push2` → preset-2, `push3` → preset-3).

```json
{
  "presets": [
    { "preset": "preset-1", "label": "Verso",  "store": "verso-x1cydwte.myshopify.com" },
    { "preset": "preset-2", "label": "Timbre", "store": "timbre-cbtmc5nj.myshopify.com" },
    { "preset": "preset-3", "label": "Wiggle", "store": "wiggle-duviydn1.myshopify.com" }
  ]
}
```

`label` is the folder name under `demo-live/`; `preset` is the source-file suffix. A demo added later = one more entry — nothing else changes.

Also confirm `/demo-live` is in `.gitignore` (it is, added with this skill).

---

## Step 1 — Pull the live themes

```bash
bash .claude/skills/live-sync/scripts/pull-live.sh              # all
bash .claude/skills/live-sync/scripts/pull-live.sh Verso        # one
bash .claude/skills/live-sync/scripts/pull-live.sh --dry-run    # print commands only
```

Each preset lands in `demo-live/<Label>/templates/`. The script only requests `templates/*.json` (+ `templates/customers/*.json`), so a pull is small and fast.

**Auth**: the Shopify CLI needs an authenticated session per store. If a pull hangs waiting on a browser login, stop and tell the user to run it themselves — `! npx shopify theme pull --live --store=<store> --path=demo-live/<Label>` — or `! npx shopify auth logout && npx shopify theme list --store=<store>` to re-auth. Don't retry blind.

**Run it with a generous Bash timeout** (3 stores ≈ a couple of minutes) and report per-store failures rather than aborting the whole run — the script already continues past a failed store and exits non-zero at the end.

---

## Step 2 — Diff live vs preset sources

```bash
python3 .claude/skills/live-sync/scripts/diff-templates.py                    # all presets
python3 .claude/skills/live-sync/scripts/diff-templates.py --preset preset-1  # or --label Verso
python3 .claude/skills/live-sync/scripts/diff-templates.py --json             # machine-readable
```

The mapping the script applies:

| Live file | Source file |
| --- | --- |
| `demo-live/Verso/templates/index.json` | `src/pages/home/index.preset-1.json` |
| `demo-live/Timbre/templates/page.about.json` | `src/pages/page/page.about.preset-2.json` |
| `demo-live/Wiggle/templates/product.json` | `src/pages/product/product.preset-3.json` |

(The source file is found by `rglob` on the stem, so a page's folder never has to be hardcoded. This mirrors the build: `vite-xotiny` copies `src/pages/**/*.<PRESET>.json` → `shopify/templates/<name>.json`.)

Comparison is **structural** — both sides are parsed, so indentation and key order never register as a change. Statuses:

| Status | Meaning | Action |
| --- | --- | --- |
| `SAME` | Structurally identical | nothing |
| `DIFF` | Live differs from the preset source | candidate for apply |
| `SHARED-DIFF` | Only match is a `.all.json` | apply hits **every** preset — say so before asking |
| `LIVE-ONLY` | Live template has no source for this preset | **never** auto-create — report; creating it is a decision (which folder? which presets?) for the user |
| `SRC-ONLY` | Source template not on the live theme | report only — usually a template never published, sometimes a deletion done in the editor |
| `AMBIGUOUS` | Two source files share the stem | report both paths; fix the collision manually |

Read `DIFF` rows before proposing anything:

```bash
python3 .claude/skills/live-sync/scripts/diff-templates.py --detail index.json --preset preset-1
```

`+` = present only on live · `-` = present only in src · `~` = different. Section-level adds/removes, changed settings, and `order` moves are each called out, so you can describe *what* the merchant changed, not just *that* something changed.

---

## Step 3 — Review each file, apply only what the user picks

Summarise per demo in the user's language, then ask with `AskUserQuestion` (multi-select, one question per demo when several have diffs):

```
Verso (preset-1) — 3 templates differ
  index.json        +1 section (manifesto), hero colour_scheme background-2 → background-9
  page.about.json   order changed (founder_letter moved above about_values)
  product.json      ~4 settings on main_product
```

Call out anything that smells like it should NOT come back:

- **A file whose changes are ALL `-` (src-only).** That is not merchandising — it means the live theme was published from an **older build** whose schema didn't have those settings yet. Applying it *deletes* settings from the repo. Exclude these from the proposal by default and say so: the fix is `theme push`, not `theme pull`. (Verify by grepping one of the missing ids — if a `.liquid` still reads it, deleting is a regression.)
- **`+` runs of schema defaults.** The Theme Editor materialises every setting's default the moment a merchant saves a section, so one real text edit can arrive with 30 lines of `use_parallax: false` / `bg_ov: none` / `top_padding_desktop: 80`. Harmless to render, but it bloats the shipped preset and freezes defaults that `schema.js` may later change. Worth telling the user the ratio (e.g. "6 real changes, 31 materialised defaults") before they choose.
- test/placeholder content, a section pointing at a draft product, a `LIVE-ONLY` scratch template — a live theme accumulates experiments, and pulling them into the shipped preset is how a demo gets shipped with junk.
- a diff that is *only* `order (reordered)` when the user didn't expect editor work on that page.

Then apply exactly the selected files:

```bash
python3 .claude/skills/live-sync/scripts/diff-templates.py --apply index.json page.about.json --preset preset-1
```

`--apply` overwrites the source template with the live document, re-serialised at the project's 2-space indent with `ensure_ascii=False` (non-ASCII copy stays readable), then automatically runs `node scripts/collapse-spf.cjs` on exactly the files it wrote — `json.dumps(indent=2)` explodes every array onto its own lines, which would break the inline `spf_*` convention the rest of `src/**/*.json` follows and fail `npm run spf:check`. If `node` is missing the script says so; run `npm run spf` yourself in that case.

Every live template carries Shopify's auto-generated `/* … */` header comment. It's a live-theme artifact, not content — it's dropped on apply and the script reports it. Expected, not a warning.

---

## Step 4 — Verify, then hand off

1. Re-run the report — every applied file must now read `SAME`.
2. `git diff --stat src/pages/` — confirm only the approved templates moved.
3. Spot-check one applied file for references that don't exist in the repo build: `shopify://shop_images/...` (fine — resolved per store), but a `type:` naming a section that isn't under `src/sections/` means the live theme is ahead of the code. Flag it; that's a porting job for `design-to-liquid`, not a template copy.
4. Hand off to `/git` — scope `pages` (or `config`). This skill never commits.

**PROGRESS.md**: applying live merchandising into shipped preset templates *is* `src/` work — log it (one line: which demos, which templates). A pull that found no differences is not worth an entry.

---

## Out of scope (and how to extend)

Deliberately not synced today:

- **Section groups** — `shopify/sections/*-group.json` ↔ `src/groups/**/*group.preset-N.json`. Header/footer/overlay groups are currently **shared** files with no preset suffix, so pulling one demo's header would silently rewrite all three. Needs its own decision before automating.
- **Theme settings** — live `config/settings_data.json` ↔ `src/config/presets/preset-N.js`. The source is JavaScript, not JSON; overwriting it mechanically would flatten the file's structure. A diff-only report is the sensible first step here.

If the user asks for either, treat it as a change to this skill (route through `system-upgrade` → `skill-creator`), not as an ad-hoc pull.
