# Fix playbooks

One file per ledger ID: **how** a requirement was actually fixed, so the next theme on the
same base can apply it in minutes instead of re-investigating. The ledger says *what* Shopify
requires; this folder says *what we changed to meet it*.

Playbooks are shared by all themes: a fix first recorded on Folio is the starting point
on Pawra, Hexon and every later theme. Read a playbook **before** fixing a FAIL. Write to it **after** the fix is verified (SKILL.md
step A8).

## Format

```markdown
# SF-<AREA>-<NN> — <requirement title from the ledger>

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-<AREA>-<NN>`.
Check type: static | heuristic | runtime | manual

## Recipe (any theme)

<theme-agnostic steps: what to look for and what to change, no theme-specific names>

## History

<one-paragraph note on how to use the entries>

### <Theme> — R<n> (<YYYY-MM-DD>)

- **Root cause:** why the theme failed (the mechanism, not the symptom).
- **Fix:** what changed — enough detail to repeat it; snippet names, settings, CSS rules.
- **Files:** paths touched (shared-base paths are what make this reusable).
- **Verify:** the `scan-feedback.py --only <ID>` call and/or the runtime click-path.
- **Gotcha:** (optional) what went wrong on the first attempt.
```

Rules:

- **Append, don't rewrite.** A second theme fixing the same item adds a new `### <Theme> — R<n>`
  entry at the top of **History**. Keep the **Recipe** current: if a theme needed a step the
  Recipe lacked, add it there so every later theme gets it. If the fix was identical, a one-line entry ("same as Folio R1, files X")
  is enough — that itself is useful: it confirms the recipe transfers.
- Keep root cause separate from fix. Root cause is what lets an agent recognise the same
  bug when it shows up in a different-looking file.
- If the fix exposed a scanner blind spot, fix `scripts/scan-feedback.py` in the same pass and
  say so under **Gotcha**.
