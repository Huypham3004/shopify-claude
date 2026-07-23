---
name: git
description: Scoped commit workflow for this Shopify theme port. Scans dirty files, groups them by scope (skill / section / snippet / block / config / state / root), drafts a Conventional-Commit message in the project's style, runs light pre-commit gates, then commits ONE scope per invocation after user approval. Always surfaces a preview and asks before committing — never silent. After committing it asks (via AskUserQuestion) whether to PUSH, commit the next scope, or stop. NEVER amends or bypasses hooks, and never pushes automatically — push runs only on your explicit choice in that prompt (never `--force`). Invoke whenever the user says "/git", "commit", "let's commit", "make a commit", "stage and commit", "tạo commit", or wants to checkpoint work before continuing.
argument-hint: "[scope-fuzzy] | --all"
---

# /git — Scoped Commit Workflow

## Identity

Commit captain for the base-3 Shopify theme port. One scope per commit. Surfaces every decision, never assumes. Designed so the user can `git push` confidently later because every commit is small, well-scoped, and on-message.

**NOT**: a general git wrapper. No push, no branch management, no rebase, no stash automation, no PR creation. Use plain `git` for those.

---

## Invocation

```
/git                       # scan, ask which scope, commit one scope
/git --all                 # batch — multi-select scopes, commit each sequentially
/git subscribe             # fuzzy-match scope (e.g. matches `sections/subscribe`)
/git .claude/planner       # exact scope
/git design                # nested-repo mode — commit the design/ clone (see end)
```

---

## Hard rules

- ✅ 1 commit = 1 scope (never straddle scopes — leaks pollute history)
- ✅ Always `AskUserQuestion` before staging or committing — surface, don't assume
- ✅ Commit message follows the project's existing style — verify by reading recent `git log`
- ✅ Always specific paths to `git add` — never `-A` / `.`
- ⚠️ **Push only on EXPLICIT user confirmation — never automatic, never silent.** After committing, the post-commit prompt (Step 11) offers **Push**; run `git push` only when the user picks it, after showing what will be pushed, and always plain `git push` — **never `--force` / `--force-with-lease`**. The `/git design` push step is the same gated confirmation. Never push without the user choosing it.
- ❌ NEVER `git commit --amend` (always create a NEW commit)
- ❌ NEVER `--no-verify` / `--no-gpg-sign` (no hook bypass)
- ❌ NEVER auto-commit secret files (`.env`, `*.key`, `credentials*`, `*.pem`)
- ❌ NEVER bundle `shopify/` compiled output silently — always warn (it's typically built, not authored)

---

## Step 0 — Index pre-flight (clean state required)

Before scanning anything, verify the git index is empty. If files are already staged from prior operations (user ran `git add .` manually, or another tool auto-staged), `git commit` would pick them up and leak across scopes.

```bash
PRESTAGED=$(git diff --cached --name-only)
[ -n "$PRESTAGED" ] && echo "Already staged:" && echo "$PRESTAGED"
```

If index is non-empty:
- **BLOCK** — show the staged files to the user
- `AskUserQuestion`:
  - `unstage all and proceed` → `git restore --staged .`, then continue to Step 1
  - `commit the existing index first` → suggest `git commit` manually then re-run /git; out of scope
  - `cancel`

This guards against scope-leak: the moment user clicks "commit" in the preview, anything pre-staged would be in the new commit even though the skill didn't intend to include it.

---

## Step 1 — Scan dirty files

```bash
git status --porcelain
```

Each line is `XY path` where `X`=index status, `Y`=worktree status. Bucket by scope using the mapping below.

---

## Step 2 — Scope mapping

Match each dirty path against this table top-down. First match wins.

| Path prefix                                              | Scope name                |
| -------------------------------------------------------- | ------------------------- |
| `.claude/skills/<name>/...`                              | `.claude/<name>`          |
| `.claude/AGENT.md`, `.claude/settings*.json`, `.claude/*.md` | `.claude`             |
| `.agent-state/...`                                       | `agent-state`             |
| `src/sections/<name>/...`                                | `sections/<name>`         |
| `src/snippets/<name>/...` (skip if `<name>` is `_base`)  | `snippets/<name>`         |
| `src/snippets/_base/...`                                 | `snippets/_base`          |
| `src/blocks/<group>/<name>/...`                          | `blocks/<name>`           |
| `src/groups/<group>/<name>/...`                          | `groups/<name>`           |
| `src/layout/...`                                         | `layout`                  |
| `src/pages/<template>/...`                               | `pages/<template>`        |
| `src/config/global-schema/...`                           | `config/global-schema`    |
| `src/config/presets/...`                                 | `config/presets`          |
| `src/config/settings_data.js`, `settings_schema.*`       | `config`                  |
| `src/styles/...`                                         | `styles`                  |
| `src/main.ts`, `src/update-product.ts`, `src/constants.js`, `src/create-schema.js`, `src/schema.types.ts` | `src` |
| `src/scripts/...`                                        | `scripts`                 |
| `theme-config/...`                                       | `theme-config`            |
| `shopify/...`                                            | `shopify-build` ⚠         |
| `design/...`                                             | — (gitignored nested repo; never in the parent scan — commit it via `/git design`, see end) |
| Root files: `CLAUDE.md`, `package.json`, `package-lock.json`, `vite.config.js`, `.mcp.json`, `.gitignore`, `tsconfig*.json`, `xo-css.vite-plugin.js`, `xo-css.vscode.cjs` | `root` |

The `⚠` marker on `shopify-build` signals a pre-commit warning (Step 7) because compiled output usually shouldn't be committed.

### Build the picker list

```
Pick scope to commit:
  · .claude/planner (4 files)
  · .claude/snippet (5 files)
  · sections/subscribe (3 files)
  · snippets/button-1 (1 file)
  · config/presets (1 file)
  · agent-state (3 files)
  · root (2 files)
  · shopify-build ⚠ (12 files)
  · cancel
```

If nothing dirty across all paths → bail with `"Nothing to commit."`

---

## Step 3 — Pick scope

If user passed `<scope-fuzzy>` arg → match case-insensitive substring against the list. Ambiguous match → present the subset via `AskUserQuestion`.

Else → `AskUserQuestion` (single-select) with the full list. Always include `cancel`.

For `--all` → `AskUserQuestion` (multi-select) and process picks sequentially through Steps 4–9. After each commit, return to Step 4 for the next pick (NOT re-scan — the user already chose).

---

## Step 4 — Read diff for the chosen scope

```bash
FILES=( "<files belonging to this scope>" )

git diff --stat -- "${FILES[@]}"
git diff --unified=0 -- "${FILES[@]}" | head -200
```

For untracked files in the scope, `cat` a brief preview (first 30 lines each) so the commit message reflects what's new, not just what changed.

---

## Step 5 — Suggest commit type

| Diff signal                                                            | Type       |
| ---------------------------------------------------------------------- | ---------- |
| Only untracked files (new section / new snippet / new skill / new template) | `feat` |
| Mix of new + modified, with new being primary                          | `feat`     |
| Bug-fix wording in diff (revert, restore, repair, regression, hotfix); removing buggy code | `fix` |
| Restructure / rename / split / merge without behavior change           | `refactor` |
| Only `*.scss` / `*.css` files, no liquid / schema change               | `style`    |
| Only `*.md` files                                                      | `docs`     |
| `package.json`, `.gitignore`, lockfiles, config that isn't theme settings | `chore` |
| Lazy-load, debounce, cache, bundle-size reduction                      | `perf`     |
| Adding tests / validators                                              | `test`     |

If signals conflict (e.g. a new section file + a bug fix in another file in the same scope) → `AskUserQuestion` with the top-2 candidates.

---

## Step 6 — Draft commit message

### Format

```
<type>(<scope>): <summary>
```

### Scope prefix rules

| Scope source                                | Prefix in message               |
| ------------------------------------------- | ------------------------------- |
| Skill-level (e.g. `.claude/planner`)        | `<type>(.claude/planner):`      |
| `.claude` (non-skill files)                 | `<type>(.claude):`              |
| `agent-state`                               | `<type>(state):` (short form)   |
| `sections/<name>`                           | `<type>(sections/<name>):`      |
| `snippets/<name>`                           | `<type>(snippets/<name>):`      |
| `blocks/<name>`                             | `<type>(blocks/<name>):`        |
| `pages/<template>`                          | `<type>(pages/<template>):`    |
| `config/...`                                | `<type>(config):` or `<type>(config/presets):` (keep slash if helpful) |
| `styles`                                    | `<type>(styles):`               |
| `layout`                                    | `<type>(layout):`               |
| `theme-config`                              | `<type>(theme-config):`         |
| `shopify-build`                             | `<type>(build):` (short form)   |
| `root`                                      | `<type>:` (no scope — like `chore: bump deps`) |

### Summary rules

- ≤ 70 characters total (incl. prefix)
- Lowercase summary, no trailing period
- Don't list filenames — describe the change in domain terms
- Style by archetype:
  - **feat** — list the main additions joined by ` + ` (max 3, condense if more)
    - `feat(sections/subscribe): inline_richtext heading + form snippet reuse`
    - `feat(.claude/planner): PLAN/PROGRESS/INVENTORY tri-doc state system`
  - **fix** — name the regression then ` — <what was restored>`
    - `fix(config/presets): preset-1 mobile_font_size_6 step + case_X raw value`
  - **refactor** — name the restructure
    - `refactor(.claude): rename port-planner → planner, move state → .agent-state/`
  - **docs** — describe what got documented
    - `docs(.claude/design-to-liquid): codify variant audit + escalation ladder`
  - **chore(state)** — for agent-state updates
    - `chore(state): session 3 — subscribe port + validator + audit workflow`

### Verify against recent log

Before showing the draft, run:

```bash
git log --oneline -10
```

Align tone, length, and conventions with what's already in the project. If recent commits use a different convention (e.g. all lowercase, no scope), match that instead of imposing this template.

---

## Step 7 — Pre-commit gates

Run on the scoped files only. Gates are light — they warn or block, but don't enforce CI-level strictness. The user gets the final call on warnings.

| Gate                       | Trigger                                                                                  | Action                                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Secret-file block**      | Any of: `.env` `.env.*` `*.key` `*.pem` `credentials*` `*-secret*` `id_rsa*` in scope    | **BLOCK** — surface to user, require explicit `force` answer to proceed                          |
| **Shopify build warning**  | Scope is `shopify-build` OR any `shopify/...` file in scope                              | **WARN** — `"shopify/ is usually compiled output. Commit anyway?"` y/n                            |
| **Schema mismatch**        | `schema.js` edited but Python validator finds errors                                     | **WARN** — run `python .claude/skills/design-to-liquid/scripts/validate-schema.py <section-dir>` and surface output; ask y/n |
| **Settings JSON sync**     | `src/config/settings_data.js` edited but `shopify/config/settings_data.json` NOT in scope, OR vice versa | **WARN** — they're often updated in lockstep; offer to add the missing one or proceed |
| **Empty staging**          | After matching scope, nothing to stage                                                   | **BLOCK** — `"Scope is clean."`                                                                   |
| **Cross-scope leak**       | Resolved file list contains a path outside the scope                                     | **BLOCK** — internal bug, surface and abort                                                       |
| **Large diff**             | Total diff lines > 500                                                                   | Show diff `--stat` only in preview; offer `view full diff` option (don't block)                  |

---

## Step 8 — Preview + confirm

Show the user a compact preview block:

```
Scope:    sections/subscribe
Type:     feat
Files:    1 modified, 2 new
  M  src/sections/subscribe/schema.js
  A  src/sections/subscribe/subscribe.liquid
  A  src/sections/subscribe/subscribe.global.scss

Gates:    ✓ no secrets   ✓ no build files   ✓ schema valid
Message:
  feat(sections/subscribe): port Folio newsletter section with inline_richtext heading
```

`AskUserQuestion` with options:

- `commit` — proceed to Step 9
- `edit message` — accept new message via a free-form follow-up
- `change type` — re-pick the conventional-commit type
- `view full diff` — print the full diff and re-ask
- `skip` (only in `--all`) — drop this scope, continue to next
- `cancel` (single mode) / `abort all` (--all) — bail without staging

---

## Step 9 — Stage + commit

```bash
git add -- "${FILES[@]}"
```

### Post-stage leak check (mandatory)

```bash
SCOPE_PREFIX="<scope's path prefix, e.g. src/sections/subscribe/>"
LEAK=$(git diff --cached --name-only | grep -v "^${SCOPE_PREFIX}" || true)
[ -n "$LEAK" ] && echo "❌ LEAK:" && echo "$LEAK"
```

> The `|| true` is critical — `grep -v` returns exit code 1 when nothing matches (the desirable no-leak case). Without `|| true`, the line would fail under `set -e`.

If `$LEAK` is non-empty:
- **ABORT** before commit
- `git restore --staged $LEAK` to unstage the leaked paths
- Surface to user — "scope leak detected, X files outside scope were in index"
- Do NOT commit until index has only the intended scope

This catches the failure mode where Step 0 missed pre-staged content (e.g. user staged something during the AskUserQuestion wait). Belt-and-suspenders with Step 0.

### Commit

Pass the message via HEREDOC (single-line subject; if a body is needed for context, add it after a blank line):

```bash
git commit -m "$(cat <<'EOF'
<your drafted message>
EOF
)"
```

> **No Co-Authored-By trailer.** Commits are attributed to the user's configured git identity only. The skill never adds a Claude / AI co-author trailer — the user wants the project history to look like their own work.

After commit:

```bash
git status --porcelain | head -20
```

### If pre-commit hook fails

- Read hook output carefully
- Fix the underlying issue (don't bypass)
- Re-stage if needed (the failed commit didn't happen, so files may need re-adding)
- Create a NEW commit (do NOT `--amend` — that would modify the previous commit, which may not exist or may be unrelated)

---

## Step 10 — Report

### Single mode

```
✓ Committed a1b2c3d
  feat(sections/subscribe): port Folio newsletter section with inline_richtext heading

Remaining dirty scopes:
  · .claude/planner (4 files)
  · agent-state (3 files)
```

### `--all` mode

```
✓ Committed 4 / 4 selected scopes:
  · sections/subscribe     a1b2c3d  feat(sections/subscribe): ...
  · .claude/planner        e4f5g6h  feat(.claude/planner): ...
  · agent-state            i7j8k9l  chore(state): session 3 ...
  · config/presets         m0n1o2p  fix(config/presets): ...

Skipped: 0
Remaining dirty: 0
```

After the report, go to **Step 11** — don't dead-end and don't push silently.

---

## Step 11 — Post-commit: push / commit next / stop

After the commit(s) land and the report is shown, **always** ask the user what to do next with a single `AskUserQuestion`. This is what replaces the old "run `/git` again / `git push` manually" dead-end.

Build the options from state:

```bash
git status --porcelain          # any dirty scopes left?
git status -sb | head -1        # "## main...origin/main [ahead N]" — how far ahead
```

`AskUserQuestion` (single-select), options in this order:

- **Commit tiếp / Commit next** — *include ONLY if dirty scopes remain.* → return to **Step 3** (re-scan, pick the next scope(s)).
- **Push** → the push flow below.
- **Dừng / Stop** → end. If the branch is ahead of upstream, remind: "N commit chưa push — chạy `git push` khi sẵn sàng."

Localise the labels to the user's language (per AGENT.md). Lead with the most likely next action: if scopes remain, "Commit next" first; if the tree is clean but ahead of upstream, "Push" first.

### Push flow (only when the user picks "Push")

Push is gated behind this explicit choice — never automatic (see Hard rules).

1. **Show what will be pushed** before doing anything:
   ```bash
   git status -sb | head -1                 # branch + ahead/behind
   git log --oneline @{u}..HEAD             # the exact commits that will go up
   ```
   If there's nothing ahead → tell the user "already up to date, nothing to push" and stop.
2. **Confirm the target** (branch → `origin/<branch>`). If the branch has **no upstream** (`@{u}` fails), don't guess — surface it and ask whether to `git push -u origin <branch>` (set upstream) before running it.
3. **Push** — plain, never forced:
   ```bash
   git push                                 # or: git push -u origin <branch> if no upstream (after asking)
   ```
   **Never `--force` / `--force-with-lease`.** If the push is rejected (non-fast-forward, remote ahead), STOP and surface the error — tell the user to reconcile (`git pull --rebase` / inspect) manually; do NOT force.
4. After a successful push, report the range pushed (`<old>..<new>  <branch> -> <branch>`), then optionally re-ask Step 11 if scopes still remain (commit next) or end.

---

## `/git design` — nested design repo mode

`design/` is a **separate git clone** (the upstream Folio HTML template) with its own `.git`, and it's **gitignored by the parent repo** — so its files never show up in the parent's `git status` and the normal `/git` flow can never touch them. `/git design` is the dedicated path for committing inside that nested repo.

**The only change is the target: every git command runs with `git -C design …`** (status, log, diff, add, commit, push) so it operates on design's own index/worktree, never the parent's. Everything else — the whole pipeline (Step 0 pre-flight → Step 1 scan → Step 3 pick → Step 4 diff → Step 5 type → Step 6 message → Step 7 gates → Step 8 preview → Step 9 stage+commit), one-scope-per-commit, preview+confirm, the post-stage leak-check, multi-select for batch, no AI co-author trailer — applies unchanged.

Entry pre-flight: confirm `design/.git` exists; if not, bail with "`design/` is not a nested git repo here" and stop.

**Design scope map** (use this instead of the Step 2 table for this mode):

| Path prefix (inside `design/`)       | Scope name          |
| ------------------------------------ | ------------------- |
| `src/components/<name>/...`          | `components/<name>` |
| `src/sections/<name>/...`            | `sections/<name>`   |
| `blueprint-*.md`                     | `blueprints`        |
| `design-system.md` (+ top-level docs)| `docs`              |
| `package.json`, `.gitignore`         | `root`              |
| `xo-design/...`                      | `xo-design`         |
| anything else                        | its top-level dir   |

**Message style follows the DESIGN repo's own convention, not the parent's.** Verify with `git -C design log --oneline -10` (the same "match existing style" rule). Design uses `<type>: <summary>` with **no `(scope)` parenthesis** — name the area in the summary prose instead. E.g. `feat: button hover restyle + signature bump`, `chore: cascade blueprint copy edits`. Leak-check prefix is relative to the design repo root.

**Push step (after the selected scopes are committed).** Push is allowed here but never automatic. Show how far ahead local is — `git -C design status -sb` (or `git -C design log --oneline @{u}..`) — then **ask**: "Push design repo to `origin/<branch>`?" Only on an explicit yes run `git -C design push` (never `--force`). If declined, remind the user they can `git -C design push` later. This follows the same gated-push rule as Step 11 — explicit ask, never automatic, never forced (just targeting `design/` instead of the parent repo).

---

## Karpathy self-check (run after each commit)

1. ✅ Single scope — `git diff <hash>~..<hash> --name-only` paths all share the scope's prefix
2. ✅ Message ≤ 70 chars on subject line
3. ✅ Type matches diff signal (not just whatever was suggested first)
4. ✅ No secret files in commit
5. ✅ Hook didn't get bypassed (no `--no-verify` in command history)
6. ✅ Not an amend (commit hash is new vs. `HEAD~1`)
7. ✅ Author = current git user (no AI co-author trailer)
8. ✅ If a push happened — it was an explicit user "Push" choice, plain `git push` (no `--force`), and the pushed range was shown

If any fails → surface to user, do NOT claim success.

---

## Edge cases

| Case                                                       | Behavior                                                                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Repo fully clean                                           | Bail: `"Nothing to commit."`                                                             |
| Only 1 dirty scope                                         | Still ask (preview + confirm) — never silently commit                                    |
| User passes `/git xxx` matching nothing                    | Show available scopes, ask to pick                                                       |
| User passes `/git xxx` matching multiple                   | Subset picker via `AskUserQuestion`                                                      |
| `.gitignore` changed                                       | Scope = `root`, type usually `chore`                                                     |
| `package.json` + lockfile change together                  | Single scope = `root`, type `chore`                                                      |
| `src/config/settings_data.js` + `shopify/config/settings_data.json` paired change | Treat as two scopes (`config` + `shopify-build`); preview will show the pairing and let user decide |
| Renaming a file across scopes (`R old → new` with different scope prefixes) | Treat as cross-scope leak → BLOCK, ask user to resolve manually (often: commit old-side delete first, then new-side add) |
| Deleted file only (`D`)                                    | Same scope mapping applies; type often `chore` or `refactor` |
| Mode-change only (chmod)                                   | Skip — usually noise, suggest `git update-index --chmod` separately |
| Commit message rejected by hook (e.g. commitlint)          | Read the hook error, propose a fix to the message, re-ask user                          |
| Submodule pointer change                                   | This project has no submodules — if one appears, treat as `root` scope and surface to user |

---

## Integration

- **`.claude/AGENT.md`** — `/git` is the canonical commit path for this project. Other skills should NOT auto-invoke `/git`. Manual trigger only.
- **`planner` skill** — when finishing a session, the planner skill writes a PROGRESS.md entry but does NOT commit. The user runs `/git` separately to commit the state file along with whatever work was done.
- **`design-to-liquid` skill** — after porting a section, the user runs `/git` separately to commit. Pre-commit gate `Schema mismatch` automatically runs the validator for any section whose `schema.js` is in the scope.

---

## Why this design

- **One scope per commit** because port work spans many concerns (a single session may touch a section, two snippets, a preset, and the state docs). Mixing them in one commit makes `git log` and `git blame` useless for debugging "where did this regression come from?".
- **Always preview + confirm** because the cost of asking is 2 seconds and the cost of an unintended commit is `git reset --soft HEAD~1` + reconciliation. Surface, don't assume.
- **Push only on an explicit choice** because pushing is a publishing act with consequences (CI, deployments, teammates pulling). The skill never pushes automatically — after committing it *offers* Push in the Step 11 prompt, shows exactly what would go up, and only pushes plain (never forced) when the user picks it. The judgment stays with the user; the skill just saves the extra step.
- **Light gates over strict CI** because this is a development theme being actively iterated. Hard blocks on every stylistic issue would interrupt flow; warnings let the user decide.
