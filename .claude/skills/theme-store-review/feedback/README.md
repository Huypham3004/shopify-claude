# Reviewer feedback rounds

One file per round of feedback Shopify's Theme Store reviewers sent back **on any of our
themes**, kept **verbatim**. Every requirement in every round applies to every theme — the
theme in the file name only records where it was raised.
This folder is the evidence; `../references/feedback-ledger.md` is the generalised checklist
derived from it. The scanner reads every file here on each audit, so a theme is always checked
against every round ever received on any theme, not only its own or the latest one.

## Naming

`R<n>-<YYYY-MM-DD>-<theme>.md`

- `<n>` counts rounds **across all themes**: R1 Folio, R2 Pawra, R3 Folio, … It matches the
  `Seen in: R<n> <Theme>` lines in the ledger.
- `<theme>` is the theme the feedback was raised on (lowercase).
- The date is the day the feedback was received.

## File format

```markdown
# R<n> — <Theme> — <YYYY-MM-DD>

<!-- comment saying the text is verbatim -->

…reviewer text pasted unchanged…
- <top-level reviewer bullet> → SF-FILTER-01
  - <sub-bullet, belongs to its parent — no marker needed>
- <bullet covered by two items> → SF-RTE-01, SF-A11Y-06
```

Rules:

- Never edit the reviewer's wording. The only addition is the ` → SF-<ID>` marker at the end of
  each **top-level** bullet (lines starting with `- ` at column 0).
- Every top-level bullet must carry a marker. The scanner reports an unmapped bullet as
  `ROUNDS ✗ not ingested`, so a round can't be half-processed by accident.
- Never delete a round file, even when its items are all fixed. It is the history that shows
  which requirements are repeat offenders.

## Rounds

| Round | Raised on | Received | File | Bullets | Status on that theme |
|---|---|---|---|---|---|
| R1 | Folio | 2026-11-05 | `R1-2026-11-05-folio.md` | 26 | fixes applied, awaiting resubmission |
