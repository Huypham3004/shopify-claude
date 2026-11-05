---
name: pull-live
argument-hint: "[1-3 | store name]"
description: Use when the user wants to pull the LIVE (published) theme of one of the Folio demo stores down into its local `demo-live/<Label>/` folder (same per-preset label folders `live-sync` uses). Trigger phrases include "/pull-live", "pull live", "pull live theme", "pull demo 3", "pull theme live về", "kéo theme live", "lấy theme live store về demo-live", "pull live x", "pull live <label>", "cập nhật demo-live từ store", "sync demo folder with live theme". The skill maps the demo number or preset label (1–3) to the correct store, runs `pnpm pulllive<x>` from the repo root with `--live` (auto-selects the published theme, skipping the interactive theme picker) and `--path=demo-live/<Label>` (so files land in the right demo folder instead of the repo root), and auto-confirms the "current Git directory has uncommitted changes → proceed?" warning with Yes. Do NOT use this for the pull-and-diff-into-preset-templates flow (that's `live-sync`, which pulls templates JSON only into `demo-live/<Label>/` and reconciles `src/pages/`), nor to pull into the tracked `shopify/` build folder (that's the root `pull` script) or to push a theme up.
---

# pull-live

Pull the **live/published** theme of a Folio demo store into its local `demo-live/<Label>/` folder.

## Store map

The `pulllive<x>` scripts live in the **root `package.json`** (`shopify theme pull -s <store>`):

| x | Label / folder | Store | pnpm script |
| - | ----------- | ----- | ----------- |
| 1 | `demo-live/Verso` | `verso-x1cydwte.myshopify.com` (Verso) | `pulllive1` |
| 2 | `demo-live/Timbre` | `timbre-cbtmc5nj.myshopify.com` (Timbre) | `pulllive2` |
| 3 | `demo-live/Wiggle` | `wiggle-duviydn1.myshopify.com` (Wiggle) | `pulllive3` |

> Sibling skill: `live-sync` pulls ONLY `templates/*.json` into `demo-live/<Label>/` and diffs them against `src/pages/**/*.preset-N.json`. `pull-live` pulls the FULL theme into `demo-live/<Label>/` and stops there — no diff, no writes to `src/`.

> `demo-live/` is git-ignored — pulled files never show up in the parent repo's `git status`, so this skill never produces a commit.

## Critical mechanics (why the naive command is wrong)

- **pnpm runs scripts from the repo root**, not from the directory you `cd` into. The `pulllive<x>` scripts have **no `--path`**, so `cd demo-live/<Label> && pnpm pulllive<x>` would pull the theme into the **repo root** — wrong and messy. Always pass **`--path=demo-live/<Label>`** so files land in the demo folder. (You do NOT need to `cd` first — run from the theme root.)
- **`--live` (`-l`)** pulls the published theme directly and **skips the interactive theme picker** — this is the "default to the store's live theme" behaviour the user wants. Never omit it, or the command stalls on a TTY theme-selection prompt.
- The **"The current Git directory has uncommitted changes. Do you want to proceed?"** warning defaults to **`(y) Yes, confirm`**. It fires because the *parent* repo (not `demo-live/`) is dirty. It must be answered Yes.

## Workflow

### Step 1 — Resolve `x`

- If the user gave a number (`3`) or store keyword (`verso`, `timbre`, `wiggle`), map it via the table.
- `all` → every row of the table (pulled one after another).
- If ambiguous or unspecified, ask which demo (1–3) via `AskUserQuestion`.

### Step 2 — Run the pull (from the theme root)

**Verified working command** (auto-confirms the git-dirty warning via `yes |`):

```bash
mkdir -p demo-live/<Label> && yes | pnpm pulllive<x> --live --path=demo-live/<Label>
```

- ⚠️ **`mkdir -p` first.** Shopify CLI refuses a `--path` that doesn't exist (`A path was explicitly provided but doesn't exist`) — it never creates the folder itself.
- **`all`** → run the command once per row of the store map, sequentially.

e.g. `yes | pnpm pulllive3 --live --path=demo-live/Wiggle`, which pnpm runs from the repo root as
`shopify theme pull -s wiggle-duviydn1.myshopify.com --live --path=demo-live/Wiggle`.

- ⚠️ **Do NOT use a `--` separator** (`pnpm pulllive<x> -- --live …`). This pnpm version forwards the `--` *literally*, so `shopify` receives `"--" "--live" "--path=…"` and dies with `Unexpected arguments`. Append the flags **directly** after the script name — pnpm passes them through.
- pnpm always runs the script from the **repo root**, so the **relative** `--path=demo-live/<Label>` resolves correctly no matter what the shell's current directory is. This is exactly why we go through pnpm instead of calling `shopify` directly.
- `yes |` feeds `y` to the "uncommitted changes → proceed?" prompt. In this environment it succeeded; the theme downloaded and reported `has been pulled`.

**If it errors as non-interactive, stalls, or asks for login** (Shopify prompts read the real TTY, which the agent's shell may not always provide), **fall back**: hand the user the exact command to run in their own terminal via the `!` prefix, and tell them to press **Enter** (Yes is the default) at the warning:

```
! pnpm pulllive<x> --live --path=demo-live/<Label>
```

> Direct-`shopify` alternative (only if pnpm is unavailable): it runs in the shell's *current* directory, so a relative `--path` can stack wrongly (e.g. `Verso/demo-live/Wiggle`). If you must call `shopify` directly, pass an **absolute** `--path` — `shopify theme pull -s <store> --live --path=<repo-root>/demo-live/<Label>`.

> Prerequisite: the user must already be authenticated with the Shopify CLI for that store (`shopify auth login` / a Theme Access password). If the run triggers a browser login, that's expected on first use — let the user complete it; this skill does not automate auth.

### Step 3 — Verify

After the pull, confirm files landed in the right place:

```bash
ls demo-live/<Label>/
```

Expect the standard theme tree (`assets/ config/ layout/ locales/ sections/ snippets/ templates/ blocks/`). Report what was pulled (store + demo folder + rough file count). If the folder is still empty, the pull didn't complete — surface the CLI output rather than claiming success.

## Hard rules

- ✅ Always run from the **theme root** with **`--path=demo-live/<Label>`** and **`--live`**.
- ✅ Default to the store's **live** theme (that's the whole point) — never drop into the interactive theme picker.
- ✅ Answer the git-dirty warning **Yes**.
- ❌ NEVER add `--path=shopify` or use the `pull` script here — those target the tracked build folder, not `demo-live/`.
- ❌ NEVER `git add`/commit anything under `demo-live/` — it's intentionally git-ignored.
- ❌ NEVER push a theme (`shopify theme push`) from this skill.
