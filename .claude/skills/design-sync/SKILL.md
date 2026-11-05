---
name: design-sync
argument-hint: "(no args — diff design HEAD vs baseline)"
description: Use when the design source has been updated and the ported Shopify theme may now be behind. The design/ folder is a SEPARATE git repo (cloned from the upstream Folio HTML template) versioned via design/package.json; pulling a new version advances its git HEAD. As its pre-flight step this skill now brings the design clone up to date ITSELF (git fetch → show incoming commits → confirm → `git -C design pull --ff-only`), rather than assuming you pre-pulled. Then it diffs the current design HEAD against the last synced baseline (recorded in .agent-state/DESIGN-SYNC.md), buckets what changed (tokens/foundation, sections, components, pages), cross-references PROGRESS.md to find which changed units are ALREADY PORTED, and reports ONLY those as a re-sync worklist (a severity-sorted impact table + batched re-port handoffs to design-to-liquid). Net-new sections (added in the design but never ported) are auto-registered into the PLAN.md backlog as ⚪ pending items, deduped against existing backlog and already-ported units so re-runs never duplicate — the actual porting still belongs to design-to-liquid, not here. Invoke this for "/design-sync", "I pulled a new design", "design có bản mới", "design update / cập nhật design", "check design changes", "đồng bộ design", "what changed in the design since last time", "design version bumped", "re-port what's stale", or at the start of a session right after a `git -C design pull`. Also runs a TEMPLATE IMAGE DRIFT pass on every sync (`scripts/image-drift.py`): when the design swaps an image, the ported `.liquid` is unaffected (it renders a merchant image_picker) but `src/pages/**/*.json` is NOT — a template hard-codes `shopify://shop_images/<basename>` and the basename is exactly what changed, so the reference silently reads blank. It reports every template setting still pointing at an image the design no longer uses, with the likely replacements, and asks per row — repoint / clear / keep / defer — never rewriting a reference on its own. Do NOT use it to port a brand-new section from scratch (that's design-to-liquid) or to track src-side progress (that's planner) — design-sync is the bridge that turns "design moved forward" into "here's the re-port worklist". After it reports, it updates the DESIGN-SYNC.md baseline ledger only once the user confirms a batch is actually synced.
---

# design-sync

Turn **"the design repo moved forward"** into **"here's exactly what to re-port, in priority order."**

## Why this exists

`design/` is a separate git repo (clone of the upstream Folio HTML template, see `design/.clone-source`), versioned by `design/package.json`. When the user pulls a new version, design's git HEAD advances — but the ported theme under `src/` doesn't know it's now stale. Nothing records *which design commit the port was aligned to*, so "what changed and what do I redo?" has been a guessing game.

This skill closes that loop:

1. A **baseline** — the design version + commit the port is currently aligned to — lives in `.agent-state/DESIGN-SYNC.md`.
2. The engine diffs `baseline..HEAD` and buckets every changed file.
3. **You** (the judgment layer) find the changed units that are *already ported* — that is the re-sync set. Changes to not-yet-ported units are counted and set aside, not worked here.
4. You produce an impact table of the re-sync set and propose **batches** that hand off to `design-to-liquid`.
5. After the user confirms a batch is synced, you advance the ledger.

The `version` in `package.json` is the human-facing headline ("are we behind?"). The git commits are the precise diff. Use both — and never trust version alone, because a pull can land many commits under the same version number.

## Pre-flight — Pull the design repo first (always, before everything)

design-sync diffs against `design`'s **current HEAD**, so a stale local clone poisons the whole report: it would diff an old HEAD, miss the very changes you ran this for, and can falsely declare "up to date". So before anything else — before bootstrap, before the engine — bring the clone current.

The project's `git` skill is **commit-only by design and never pulls**, so design-sync does the pull itself with a plain command. **Do not invoke the `git` skill for this.**

1. Fetch and check whether the local clone is behind its upstream:
   ```bash
   git -C design fetch
   git -C design status -sb | head -1        # e.g. "## main...origin/main [behind 7]"
   git -C design log --oneline HEAD..@{u}     # the incoming commit subjects, if any
   ```
2. **Already current** (no incoming commits) → say "design clone already current at `<short HEAD>`" and continue to Step 0 (bootstrap) / Step 1 (engine) with this HEAD.
3. **Behind** → show the incoming commit subjects (the commit messages are the best summary of what changed — the same signal Step 3 leans on) and **ask the user before pulling**. On confirm:
   ```bash
   git -C design pull --ff-only
   ```

> [!IMPORTANT]
> Pull with `--ff-only` so a pull that isn't a clean fast-forward **fails loudly** instead of silently creating a merge commit in a repo you don't own. If it fails (local edits in the design tree, or diverged history), **stop and hand it back to the user** to resolve manually (inspect, or `git -C design stash`) — never force, reset, or merge the design clone yourself (AGENT.md: surgical changes; don't touch what you don't own).

After a successful pull, design HEAD has advanced — that advanced HEAD is what the engine diffs `baseline..HEAD` against in Step 1, and what the Step 0 clean-slate guardrail (don't baseline on top of unported drift) then evaluates. That's the intent: every downstream step reasons about the freshest design.

## Step 0 — Bootstrap (only when no ledger exists yet)

If `.agent-state/DESIGN-SYNC.md` is absent, there's no baseline. The engine exits with code 3 and prints `NO_BASELINE`. Establish a baseline before anything else.

Ask the user which baseline they want (use `AskUserQuestion`):

- **Clean slate (recommended)** — baseline = current design HEAD. Future pulls are tracked from here; existing already-ported work is assumed in sync. Pick this when the port is roughly current and they just want forward tracking.
- **Backfill audit** — baseline = an older commit (e.g. the design HEAD around the last big port session — cross-check dates in `PROGRESS.md`). The first report then surfaces the full backlog of drift since then. Pick this when they suspect the port already lags the design.

> [!IMPORTANT]
> **Clean-slate guardrail — never baseline on top of unported drift.** Clean slate assumes everything up to HEAD is already ported. That is FALSE when the latest design commit(s) — often the very release that bumped `package.json` — modified already-ported sections; baselining at HEAD then buries those changes inside the baseline (`baseline..HEAD` is empty → the next report wrongly says "up to date"). Before writing a clean-slate baseline at HEAD, verify HEAD isn't already ahead of the port:
> 1. Run `python .claude/skills/design-sync/scripts/design-diff.py --since HEAD~5` (widen the range if the port lagged further; cross-check `PROGRESS.md` dates for the last port session).
> 2. Cross-check the 🟠 list against already-ported sections (grep `PROGRESS.md` "Files touched"). If any ported section shows as modified/removed, HEAD is ahead of the port — clean-slate-at-HEAD would hide it.
> 3. In that case record the baseline at the **parent of the earliest commit that touched a ported section** (`<sha>~1`), NOT HEAD, so the drift surfaces on the first real report. Only baseline at HEAD when no recent commit touches a ported unit.

Then create the ledger from the template in `references/ledger-format.md` and record the chosen baseline. Stop here on first run unless the user picked Backfill (in which case continue to Step 1 with that commit).

## Step 1 — Run the engine

```bash
python .claude/skills/design-sync/scripts/design-diff.py
# or, to diff from a specific commit instead of the ledger baseline:
python .claude/skills/design-sync/scripts/design-diff.py --since <ref>
# add --json when you want to reason over structured data
```

The engine reads `design/package.json` version + HEAD, the ledger baseline, runs `git -C design diff --name-status --find-renames baseline..HEAD`, and emits a report grouped by severity tier:

| Tier | Meaning | Default action |
| --- | --- | --- |
| 🔴 **Foundation** | `src/styles/` tokens, `design-system.md`, `head.html`, fonts | Re-check **Step 0 token mapping** — a variable change ripples to every ported section |
| 🟠 **Units** | sections & components | Re-sync if already ported; **ignore if not yet ported** (counted in the footnote, not worked here) |
| 🟡 **Pages/blueprints** | page templates, `blueprint-*.md` | Informational — tells you which sections appear where |
| ⚫ **Infra** | build config, lockfiles | Usually ignore |

If the engine says **up to date**, report that and stop — there's nothing to re-port.

Each 🟠 unit carries a **PROGRESS mentions** hint (how many times the design unit's name appears in `PROGRESS.md`). High count ≈ likely ported; `0` ≈ likely new. **This is a hint, not proof** — design names rarely match src names 1:1 (`header` design → `src/groups/headers/header/`; `hero` design → an `image-banner`-style section), so resolve truth in Step 2.

## Step 2 — Resolve true port state (the judgment layer)

The engine can't know whether a design unit was ported, because the mapping is fuzzy. You resolve it per 🟠 unit and per 🔴 foundation change:

**For each 🔴 foundation change:** open the changed file's diff (`git -C design diff <baseline>..HEAD -- <path>`) and judge whether a token/variable the theme's Step 0 mapping depends on actually moved (color, font, type scale, radius, spacing). If yes, the fix is in `src/config/presets/preset-N.js` / global-schema — not in any one section. Flag it as the top priority; everything else is downstream of it.

**For each 🟠 modified/removed unit, decide ported-or-not:**

1. Grep `PROGRESS.md` for the design unit name and read the surrounding "Files touched" / "Goal" lines — they name the real `src/` target (e.g. searching `header` surfaces `src/groups/headers/header/header.global.scss`).
2. Cross-check `INVENTORY.md` and, when still unsure, grep `src/` for distinctive strings from the design unit (a class name, a heading copy).
3. Classify:
   - **Ported + modified** → *candidate* re-sync. Before calling it actionable, read the actual design diff (`git -C design diff <baseline>..HEAD -- src/sections/<unit>/`) and confirm the change touches the **ported surface**, not a sibling. A "modified" flag is often a sub-brand block being moved out (e.g. `header` showed up modified, but the diff was just `header-sound` announce CSS relocating to a new `announcement-bar-sound` section — the ported Folio base header was untouched). Only the part of the diff that hits the ported surface is real re-sync work; capture the resolved `src/` path for it.
   - **Ported + removed/renamed** → the src version may now be orphaned or misnamed; flag for the user (don't delete anything yourself — AGENT.md surgical-changes rule).
   - **Net-new (added, never ported)** → not a re-sync, but don't let it vanish. Resolve only enough to NAME the unit and propose a candidate `src/` target path stub (e.g. design `testimonial-marquee` → `src/sections/testimonial-marquee/`), then queue it for the PLAN.md backlog write in **Step 3.5**. Don't deep-resolve or port — name + type + candidate path is enough.
   - **Not-yet-ported but modified** → out of scope; lightly tally, don't deep-resolve. Porting it is `design-to-liquid` work, not a re-sync.

> [!IMPORTANT]
> **An image-only change is a no-op for `src/sections/`, and actionable for `src/pages/`.** Do not stop at "the diff only swaps `img src` urls, and the port drives images from merchant `image_picker` settings" — that is true of the `.liquid`, and false of the JSON templates. A page template hard-codes `"image": "shopify://shop_images/<basename>"`, and the basename is precisely what an image swap changes. The reference silently reads blank; nothing errors. (This is why the 2026-08-20 ledger entry dismissed ~55 image-swap units as zero-actionable — correct for the sections, incomplete for the templates.) Resolve it in Step 2.5, not by eye.

Keep this fast — you only need enough to confidently bucket *ported* vs *net-new* vs *not-yet-ported-modified*. Stop resolving a unit the moment it's confidently NOT ported (0 mentions + `added` → trust it, queue it for the backlog, move on); spend deeper judgment only on the ported set.

## Step 2.5 — Template image drift (always run)

Sections re-sync through `design-to-liquid`; templates do not — nothing else in the system looks at them. Run this on every sync, even when the 🟠 list looks like pure asset churn:

```bash
python3 .claude/skills/design-sync/scripts/image-drift.py            # baseline from the ledger
python3 .claude/skills/design-sync/scripts/image-drift.py --since <ref>
python3 .claude/skills/design-sync/scripts/image-drift.py --audit    # broad sweep, ignores history
python3 .claude/skills/design-sync/scripts/image-drift.py --json
```

It collects every `shopify://shop_images/<basename>` under `src/pages/`, diffs the design's image urls over the baseline window, and reports only references whose basename the design **no longer uses anywhere**. A url vanishing from one file is not enough — a renamed or deleted design page moves urls around while the image stays in use, so each candidate is confirmed against the design's current state before it is reported. Build output (`dist/`) is excluded, being a stale copy of the same pages.

Exit code `1` means drift was found; `0` means clean.

Each row names the stale basename, the design unit that dropped it, the images added in that same unit (the likely replacements), and every template file + setting id still pointing at it.

**`--audit` vs the default:** the default is precise — only what moved in this sync window. `--audit` compares every template reference against the design's images with no history, so it also surfaces references that were always store-only (merchant-picked, never from the design). Those are legitimate. Use `--audit` to take stock, the default during a sync.

> [!IMPORTANT]
> **Never rewrite a reference automatically.** Old→new pairing is a judgment call the script deliberately does not make: a unit that dropped one image and added four gives no reliable mapping, and guessing wrong points a live demo at the wrong picture. Propose, let the user choose.

For each drift row offer:

- **Repoint** to the replacement the user names — a one-key text edit in the template, then re-run to confirm the row is gone
- **Clear it** — leave the picker empty so the merchant picks in the editor
- **Keep it** — the store image is deliberate and independent of the design
- **Defer** — record it in the report; nothing changes

Whatever is chosen, the file must still be uploaded to the store the demo ships on, or the reference resolves blank. When the design carries an image handoff contract (`HANDOFF-IMAGES.md` + `.shopify/images.json`), verify the new basename against that manifest and name the store — see the `build-page` skill, which owns the url→picker mapping rules.

## Step 3 — Build the impact table

Present a single table the user can act on — **only foundation (🔴) + already-ported-and-modified/removed (✅) rows.** Order foundation-first, then ported-and-modified. Not-yet-ported changes never become rows here.

```
| # | Design change | Type | Ported? | src target | Action | Batch |
| - | ------------- | ---- | ------- | ---------- | ------ | ----- |
| 1 | src/styles/base/variables.scss | 🔴 token | foundation | preset-1.js | Re-check Step 0 mapping | A |
| 2 | header (modified)              | 🟠 sect | ✅ ported | groups/headers/header/ | Re-sync SCSS/settings | A |
| 3 | footer (modified)             | 🟠 sect | ✅ ported | groups/footers/footer/ | Re-sync SCSS | A |

| 4 | headphones.png (dropped)      | 🖼 image | template | pages/home/index.preset-2.json | Repoint or clear | A |

_(N net-new sections registered to the PLAN.md backlog in Step 3.5 — listed there, not here; M not-yet-ported-modified units tallied, out of scope.)_
_Image-drift rows (🖼) come from Step 2.5 and are template edits, NOT `design-to-liquid` re-ports._
```

Always include the new design commit subjects (from the engine) above the table — the commit messages are the best summary of intent ("sound stack — 4 new sections + violet palette"). The re-sync table stays focused on foundation + already-ported-modified rows; net-new sections don't become rows here — they feed the backlog write in Step 3.5 instead.

## Step 3.5 — Register net-new sections into the PLAN.md backlog

A newly-added design section that nobody ports is the easiest thing to lose — it's not a re-sync (so it never reaches the impact table) and a bare footnote count evaporates the moment the report scrolls away. So every net-new ADDED section resolved in Step 2 gets **auto-appended** to the PLAN.md backlog as a ⚪ pending row, capturing: the design unit name, the candidate `src/` target path, and a short provenance note (e.g. `net-new from design sync v2.4.0 / a1b2c3d`).

**Dedup first — this is what makes re-running `/design-sync` safe.** Without a guard, every run would re-append the same units and the backlog would fill with duplicates. Before appending a unit:

1. Grep `PLAN.md` for the unit name and the candidate `src/` path — skip it if it's already a ⚪/🔵 backlog row.
2. Cross-check it isn't already ported — grep `PROGRESS.md` "Files touched" and `INVENTORY.md` for the same name/path. A unit that turns out ported was misclassified in Step 2; drop it from the net-new set rather than backlog it.

Append only the units that survive both checks. Then **report to the user explicitly**: which net-new units were appended, and which were skipped as already-tracked — so the write is visible, not silent.

Architecture note: `PLAN.md` is `planner`'s document. design-sync only **appends ⚪ pending backlog rows** — it never reorders, rewrites, or re-prioritises existing PLAN content, and never marks anything done. Porting these rows is a separate `/design-to-liquid` action the user triggers later.

## Step 4 — Propose batches + hand off

Group the actionable rows into **batches** the user can take one at a time, and recommend the handoff:

- **Batch ordering:** foundation (🔴) first — re-mapping a moved token may auto-fix downstream sections via the CSS-variable cascade, shrinking the rest of the list. Then ported-and-modified sections grouped by area (header/footer chrome together, PLP family together, etc.).
- For each batch, name the concrete next command: *"Run `/design-to-liquid` on `<unit>` — it's an override re-sync of `src/groups/headers/header/`"*. Respect the group override ladder vs section port ladder per AGENT.md. (Batches are re-sync of already-ported units only.)
- Re-sync batches contain already-ported units only. Net-new sections aren't folded in here — they were already written to the PLAN.md backlog in Step 3.5, and the user picks them up via `/design-to-liquid` when ready. (Not-yet-ported *modified* units stay out of scope — neither re-synced nor backlogged automatically; mention them if the user asks.)

Do **not** start porting yourself — design-sync's job ends at the worklist + handoff. The user picks a batch; `design-to-liquid` does the actual re-port.

## Step 5 — Advance the ledger (only after confirmed sync)

When the user confirms a batch (or the whole set) is actually re-ported and verified, update `.agent-state/DESIGN-SYNC.md`: add a new TOP row with today's date (ask the user for the date — you cannot read the clock reliably), the new design version, the new short SHA, and a one-line note of what was synced. The TOP row is always the live baseline the next `/design-sync` diffs from.

**Never advance the ledger automatically just because you ran the report** — that would silently mark un-done work as done and the drift would vanish from the next report. Advance only what the user confirms.

If the user re-ports just part of the worklist, advance the ledger only if the remaining items are net-new backlog (tracked in PLAN) rather than un-synced modifications — otherwise the modified-but-skipped units would disappear. When in doubt, leave the baseline where it is and note the partial progress instead.

## Reference

- `references/ledger-format.md` — the `DESIGN-SYNC.md` table format + bootstrap template.
- `scripts/image-drift.py` — Step 2.5 template image-drift detector.
- The `build-page` skill — owns the design-url → `shopify://shop_images/` mapping rules and the per-design image handoff contract.

## Guardrails

- This skill is **read-and-report + ledger + backlog-append**, not a porter. It writes exactly two agent-state files: `.agent-state/DESIGN-SYNC.md` (the baseline ledger — advanced only on confirmed sync, Step 5) and `.agent-state/PLAN.md` (⚪ pending net-new backlog rows — auto-appended on detection, deduped, Step 3.5). It only ever APPENDS pending rows to PLAN — never edits/reorders existing PLAN entries, never marks anything done. All `src/` changes still go through `design-to-liquid`.
- PROGRESS-mention counts are heuristics — always confirm ported state with the grep/read pass before calling something "✅ ported".
- If the design repo is shallow or the baseline ref is missing, the engine errors — tell the user to `git -C design fetch` and retry.
- Foundation changes are the highest leverage: re-mapping one moved token can resolve many downstream "modified" sections at once. Always handle 🔴 before 🟠.
- **Image-drift rows are the one kind of change this skill resolves in `src/` itself** — a template `image` value is data, not a port, so it never goes through `design-to-liquid`. It is still user-approved per row, and the ledger does not advance until the user confirms the repoints alongside the rest of the batch.
