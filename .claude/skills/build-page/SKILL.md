---
name: build-page
argument-hint: "<design page> (e.g. home, collection) | --all"
description: Build the JSON page template(s) for a design page — the page/demo layer that design-to-liquid's Step 5 only gestures at. Use whenever the ask is about assembling a PAGE rather than porting one section — "/build-page", "build page", "build the home page", "dựng page", "dựng trang home", "tạo template", "tạo json template", "build demo", "dựng demo", "build các template theo design", "làm template theo design", "wire các section vào page", "ráp page theo design", "page này thiếu section nào", "template đã giống design chưa". It reads the design page, takes the ordered `<xo-include>` list inside `<main>` as the section order (everything outside `<main>` is a section GROUP and is excluded), resolves each design section to its ported `src/sections/<name>` (names drift — `plp-hero` shipped as `collection-page-title` — so it checks `.agent-state` for recorded renames), then writes `src/pages/<folder>/<template>.preset-N.json`. Settings are generated from each section's COMPILED schema defaults and then overridden with the design's copy and images, so a template can never carry a key its schema does not declare. Images follow the design's own handoff contract when it ships one (`HANDOFF-IMAGES.md` + `.shopify/images.json`: basename of the CDN url, query string dropped, verified against the manifest); when the design has no manifest it says so and asks rather than inventing references. STOPS AND ASKS on two gates — sections the design uses but `src/` has not ported, and any image it cannot resolve — and after writing it re-scans the template against the design and reports every remaining difference for the user to decide on. Do NOT use it to port a section from a design (that's `design-to-liquid`), to pull merchandising back from a live store (that's `live-sync`), or to diff the design repo for drift (that's `design-sync`).
---

# build-page

`design-to-liquid` ports **sections**. This builds the **page** that stacks them.

Step 5 of `design-to-liquid` is one sentence ("write the JSON template") because it is the tail of a per-section pipeline. Assembling a demo is the other direction: start from a design page, work out what it needs, and find out what is missing. That is this skill.

## Identity

One design page in → one (or more) `src/pages/**/<template>.preset-N.json` out, with **two mandatory stops** where the user decides, and **a verification pass** at the end that is allowed to fail loudly.

It never invents. Every section reference is a directory that exists in `src/sections/`; every settings key is declared by that section's compiled schema; every image is either verified against the design's manifest or escalated to the user.

## What it does NOT do

| Not this | That's |
| --- | --- |
| Port a design section into `src/sections/` | `design-to-liquid` |
| Pull merchandising back from a live store | `live-sync` |
| Diff the design repo for drift | `design-sync` |
| Author/modify `schema.js` or `.liquid` | `design-to-liquid` / `schema` / `snippet` |
| Track what's done across sessions | `planner` |

If the scan reports unported sections and the user wants them built, **hand off to `design-to-liquid` one section at a time** — do not port from inside this skill.

## Pipeline

### Step 1 — Scan the design page

```bash
python3 .claude/skills/build-page/scripts/scan-page.py --list
python3 .claude/skills/build-page/scripts/scan-page.py home
python3 .claude/skills/build-page/scripts/scan-page.py --all      # backlog sweep
```

The script is the mechanical half. It reports, per page:

- the ordered section list **inside `<main>`** — this is the template's `order`
- what sits **outside `<main>`** (header / footer / cart drawer / popups) — section **groups**, never template sections, always excluded
- for each design section: the ported `src/sections/<name>`, resolved by exact name → a rename recorded in `.agent-state` → unresolved
- every image url the section hard-codes, and whether it can become a picker reference

Read its output; do not re-derive any of it by hand.

> [!IMPORTANT]
> If the script prints `! no <main> found`, the page does not use the standard shell. Open it and establish the section boundary yourself before continuing — the order it printed is not trustworthy.

### Step 2 — GATE 1: unported sections (requirement 3)

If the scan lists any section as `not ported` or `ambiguous`, **stop and ask**. Never silently drop a section from the page, and never substitute a lookalike without saying so.

Present the missing list with what each one appears to be (read its design HTML first — one line each, so the choice is informed), and offer:

- **Port it now** — hand off to `design-to-liquid`, then re-run the scan
- **Substitute** — name an existing `src/sections/<x>` that covers it, and say what will differ
- **Skip for this pass** — build the template without it; it is recorded in the gap report at the end
- **Stop** — build nothing until the backlog is ported

For `ambiguous` (two recorded renames matched), show the candidates and ask which is meant.

### Step 3 — Decide the template target

`src/pages/<folder>/<template-name>.preset-N.json`, where `<template-name>` is the Shopify template and `<folder>` is the grouping bucket. Read the existing tree before choosing — it is the authority:

| Design page | Template file | Compiles to |
| --- | --- | --- |
| `home.html` | `src/pages/home/index.preset-N.json` | `templates/index.json` |
| `collection.html` | `src/pages/search-filters/collection.preset-N.json` | `templates/collection.json` |
| `product.html` | `src/pages/product/product.preset-N.json` | `templates/product.json` |
| `about.html` | `src/pages/page/page.about.preset-N.json` | `templates/page.about.json` |
| a second layout (`product-2`) | `…/product.<suffix>.preset-N.json` | an alternate template |

**Which `preset-N`:** `.env` `PRESET=preset-N` selects which one the build compiles. Write the preset that matches the design being built, and do not touch sibling presets unless asked — they belong to other demos. Say explicitly which presets you did and did not write.

A design page with no obvious Shopify template (`components.html`, `our-work.html`, a marketing one-off) → ask before inventing a template name.

### Step 4 — Write the template

**Generate settings from the compiled schema, then override.** Never hand-type a settings object — that is how orphan keys get in.

For each section, read `shopify/sections/<type>.liquid`, parse its `{% schema %}`, take every `id` with its `default`, then apply the design's values on top. Assert that every override key exists in the schema before writing. `references/template-shape.md` carries the exact recipe.

Order follows the design's `<main>`. Section keys are snake_case of the section type (`why_planner`), suffixed when a page uses one twice (`spacer_1`, `spacer_2`).

> [!IMPORTANT]
> **Editing an existing template: splice as text, never round-trip the JSON.** `json.load` → `json.dump` reformats lines you did not touch (inline arrays get exploded onto separate lines), which buries your change in noise. Generate the new block, then insert it at the right line. Verify with `diff` that the removed-line count is **0**.

### Step 5 — GATE 2: images (requirement 2)

Images are the part most likely to be silently wrong, so the rule is per-design, and the scan already told you which mode applies.

**Mode `manifest`** — the design ships `HANDOFF-IMAGES.md` + `.shopify/images.json`. Then the contract is mechanical and must be followed exactly:

```
src="https://cdn.shopify.com/s/files/1/.../files/bread-craft-video-1.webp?v=1789025051&width=100"
                                                  ^ basename, query string dropped
"thumb_one_image": "shopify://shop_images/bread-craft-video-1.webp"
```

- Keep the filename **byte-for-byte** — it is the only link between design and store.
- **Drop the query string.** `shopify://shop_images/` takes a filename and nothing else; sizing is `image_url`'s job.
- Every reference is cross-checked against the manifest. Anything the scan marks `NOT in manifest` is a **gate** — report it, do not guess.
- **Do not mix stores.** The handoff doc maps each demo to the store holding its files; a reference only resolves inside that store. Name the store in the final report, and flag it when it differs from what `npm run push` targets.

**Mode `none`** — the design's images are on hosts the store does not own (`s3.awe7.com`, `assets.lummi.ai`, another shop's CDN). There is **no mechanical mapping**. Say so plainly and ask:

- **Leave the picker empty** — the section renders its placeholder; merchant picks in the editor (usually right for a theme that ships to real merchants)
- **Reuse** an image already referenced by a sibling template in this repo
- **Upload first**, then re-run — the filenames become resolvable
- **Point at a manifest** if one exists somewhere the scan did not look

Never write a raw `https://` url into an `image_picker` setting. It is not a valid value; the setting will read blank and the failure is invisible until someone opens the page.

Alt text comes from the section's own HTML (context-specific), not the manifest's generic `alt`.

> [!NOTE]
> **This mapping is load-bearing after the page ships.** Because a template stores the image's *filename*, a later design image swap makes the stored reference stale and it reads blank with no error. `design-sync` Step 2.5 is what catches that; it applies the same basename rule in reverse. If you change how urls map to picker references here, change it there too.

### Step 6 — Verify (requirement 4)

Not optional, and it runs **after** writing.

```bash
python3 .claude/skills/design-to-liquid/scripts/validate-templates.py src/pages/<folder>/
npm run build
python3 .claude/skills/build-page/scripts/scan-page.py <page>      # re-scan
```

Then compare the written template against the design, and **report every difference**:

| Check | Pass condition |
| --- | --- |
| Section set | every `<main>` section present, none extra |
| Order | template `order` matches the design's stacking order exactly |
| Settings keys | `validate-templates.py` clean — no key the schema doesn't declare |
| Images | every `image_picker` either a manifest-verified reference or a decision the user made at Gate 2 |
| Compile | `npm run build` clean, and `shopify/templates/<name>.json` carries the section |
| Groups | nothing from outside `<main>` leaked into the template |

If anything fails, **do not quietly fix and move on** — report the mismatch and let the user choose: fix now / accept the difference and record it / revert the template.

Close with a short gap report: what was skipped at Gate 1, what images are unresolved, which presets were left untouched. State plainly that it has not been opened in a live Theme Editor unless it has.

## Conventions this skill must respect

- **`<main>` is the boundary.** Header, footer, cart drawer, popups, announcement bar are section **groups** under `src/groups/` and are wired through `*-group.json`, never a page template.
- **A template references a section `type`**, which is the directory name under `src/sections/` — not the design's name for it.
- **Presets are demos.** `index.preset-1.json` / `.preset-2` / `.preset-3` are different stores. Writing one is not writing the others.
- **Templates carry real demo copy**, not schema placeholders. Schema `default`s stay generic; the page template is where the design's actual words belong.
- **Resource settings** (`collection`, `product`, `blog`) take `shopify://collections/<handle>` and only resolve if that handle exists on the store.

## Related skills

- `design-to-liquid` — ports the sections this skill stacks; hand off to it at Gate 1
- `planner` — PLAN/PROGRESS; log the page built and the gaps left
- `live-sync` — the reverse bridge, store → repo
- `design-sync` — design repo drift. It owns the **reverse** direction of the image rule here: when the design swaps an image, `scripts/image-drift.py` finds the templates still pointing at the old basename. Same mapping, opposite trigger — keep the two in step if the rule ever changes.
- `editor-qa` — drive the built page in a real Theme Editor
- `git` — commit when the page is done
