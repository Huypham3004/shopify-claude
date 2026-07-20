---
name: web-components
description: "Author (create) a NEW xo-* custom web component in TypeScript with XoComponent + @xo/utils, writing the .ts file into the project's src/scripts/. Standalone, manually invoked. Use this WHENEVER the user wants to BUILD a new custom interactive front-end behavior for a Shopify theme that no existing component covers — e.g. 'tạo web component', 'làm một xo-... component', 'create/build a web component', 'build a custom slider/toggle/cursor/tilt/split-text/scroll effect from scratch', 'viết component xử lý hover/drag/scroll', 'code a JS behavior for this section', 'I need a bespoke countdown/marquee/parallax thing that doesn't exist yet'. This skill CREATES components only — it does NOT wire up or place already-existing xo-* tags (using a pre-built component in markup is design-to-liquid, not this). NOT for styling (that's the xo-css skill), NOT a pipeline step."
argument-hint: "<what the component should do> (e.g. 'a card that tilts toward the cursor')"
---

# /web-components — XO Web Component Authoring

## Identity

Standalone, manually-invoked skill with ONE job: **author a brand-new `xo-*` web component** in TypeScript (`XoComponent` + `@xo/utils`) into the project's `src/scripts/`. It builds new interactive behavior from scratch.

This skill does NOT use, place, or wire pre-built components — dropping an existing `xo-*` tag into a section is the section author's job (`design-to-liquid`). Before authoring, it does one quick **duplication guard** against the live `xo-components` MCP: if the behavior already exists as a pre-built component, this skill bows out and points the user at that tag rather than building a redundant one.

This is the behavior/JS layer only. Layout markup is authored in HTML/Liquid by the section builder; visual styling is the `xo-css` skill's job. A component you write enhances existing DOM — it queries children, wires interactions, toggles classes/attributes/CSS vars so SCSS can react. It does not own layout or look.

NOT a pipeline step. NOT auto-run during a `design-to-liquid` port. Invoked only when the user explicitly wants to create a new web component / custom interactive behavior.

## When to use

- "Create/make a web component", "tạo/làm web component", "viết một xo-... component".
- "Build a custom [slider / toggle / cursor / tilt / split-text / scroll-progress / drag] from scratch."
- A section needs bespoke pointer / scroll / drag / animation behavior that no existing `xo-*` component provides, and you need to write the JS for it.

## When NOT to use

- **Using / placing a pre-built `xo-*` component** in section markup → `design-to-liquid`. This skill authors new components; it does not wire up existing ones.
- **Styling / SCSS** → `xo-css` skill.
- **Building a whole section's markup** → `design-to-liquid`.
- **A reusable project primitive** (button, product-card…) already covers it → render the existing snippet with `{% render 'snippet' %}` (audit `src/snippets/` variants first — see `design-to-liquid`'s snippet-variant audit).

## Reference files (progressive disclosure)

Load what the task needs — don't read all three up front.

| File | Read when |
|------|-----------|
| `references/create-web-component.md` | Authoring a new component — the build contract + step-by-step + skeletons |
| `references/xocomponent-api.md` | Need the full `XoComponent` API — props, state, lifecycle, decorators, context, events, lazy-load |
| `references/utils.md` | Choosing helpers — 50+ `@xo/utils` exports (damp, panGesture, frameManager, createAnimate, debounce…) |

## Workflow

```
1. Duplication guard → xo-components MCP (find_components / list_components)
                       ├─ existing xo-* already does this → STOP, tell the user it exists
                       └─ nothing covers it              → author (continue)
2. Resolve target   → src/scripts/<name>.ts
3. Design shape     → props / state / child tags / which @xo/utils helpers / what it reflects
4. Write .ts        → XoComponent + @customElements("xo-..."), per create-web-component.md contract
5. Verify           → mcp__xo-design__check_render_errors (a throwing component renders blank silently)
6. Hand off         → report tag name, props, child tags, reflected classes/attrs/CSS vars
```

### Step 1 — Duplication guard (mandatory)
Check whether the requested behavior already exists as a pre-built component: `mcp__xo-components__find_components("<use case>")` (or `list_components()`). Carousel, modal, tabs, collapse, popover, marquee, parallax, sticky, tooltip, toast, countdown, magnetic, cursor, ripple, image-zoom, and the whole product/cart family already exist. If one already does the job, DON'T author a redundant component — stop and tell the user the tag already exists (they can place it in section markup via `design-to-liquid`). Only continue to authoring when nothing covers the need. Building a duplicate of an existing component is the most common failure mode.

### Step 2 — Target file
The component is a flat file at `src/scripts/<name>.ts` — no per-component subfolder, no `doc.md`. It's auto-loaded via `src/utils/import-scripts.ts` (which globs `../scripts/**/*.ts`); `main.ts` imports that util, so no manual registration is needed.

### Step 3-5 — Design, write, verify
Follow `references/create-web-component.md` (the contract) and `references/xocomponent-api.md` (the API). Core rules, condensed:

- Tag is `xo-`-prefixed; register with `@customElements("xo-...")`; `export` the class.
- Prefer a `@xo/utils` helper over hand-rolled logic (`references/utils.md`). Don't reimplement damp / gesture / rAF / debounce / video / money.
- Don't render layout HTML from TS — enhance existing DOM (query children, toggle classes/attrs/CSS vars). Tiny generated bits (SVG ring, injected cursor span) are the only exception.
- Wire every needed interaction (hover/click/drag/scroll/animation) via utils.
- Clean up in `unmount()` — one `AbortController` for all listeners; `destroy()` any damped values / cancel frames.
- No demo `.html` file. No styling — the section's SCSS (`xo-css`) styles the states you reflect.
- Never import `morph` (not exported by the `@xo/utils` facade).

### Step 5 — Verify render
Run `mcp__xo-design__check_render_errors({ pages: [...] })` (or omit `pages` to sweep all) on any page using the new tag. A component whose class throws on mount renders BLANK with no SCSS error — this is the only signal. Fix reported errors before finishing.

### Step 6 — Hand off
Report the contract so the section markup + `xo-css` styling can be written against it: tag name, props (`xo-*` attrs + types), required child tags (if compositional), and the classes/attributes/CSS custom properties the component reflects for styling.

## Minimal example — a from-scratch component

```typescript
// src/scripts/xo-scroll-progress.ts
// <xo-scroll-progress> — sets --progress (0→1) on itself as the page scrolls.
// SCSS reads var(--progress) to size a bar. Reflects nothing else.
import { XoComponent, customElements, frameManager, clamp } from "@xo/utils";

@customElements("xo-scroll-progress")
export class ScrollProgress extends XoComponent {
  private update = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const p = max > 0 ? clamp(window.scrollY / max, 0, 1) : 0;
    this.style.setProperty("--progress", `${p}`);
  };

  mount() {
    frameManager.add(this.update, true); // shared 60fps rAF loop
  }

  unmount() {
    frameManager.remove(this.update);
  }
}
```

```liquid
{%- comment -%} section author writes the markup; xo-css styles var(--progress) {%- endcomment -%}
<xo-scroll-progress></xo-scroll-progress>
```
