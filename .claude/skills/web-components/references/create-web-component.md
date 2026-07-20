# Building a new web component

The authoritative step-by-step for authoring a brand-new `xo-*` component into the project's `src/scripts/`. Read `xocomponent-api.md` for the full class API and `utils.md` for the helper catalog referenced below.

## The contract

A component you author MUST:

1. **Use `XoComponent`** and the helpers from `@xo/utils` — don't reimplement debounce, damp, gesture handling, video play/pause, money formatting, etc. when a util already exists (`utils.md`).
2. **Have an `xo-` prefixed tag name** — `xo-<thing>`. Register with the `@customElements("xo-...")` decorator.
3. **Be written in TypeScript**, `export`ed, and live at `src/scripts/<name>.ts`. It's auto-loaded via `src/utils/import-scripts.ts` (which globs `../scripts/**/*.ts`); `main.ts` imports that util, so no manual wiring.
4. **Not render layout HTML from TS.** The markup is authored later in HTML/Liquid by the section builder. The component *enhances* existing DOM: it queries its children, wires behavior, toggles classes/attributes/CSS vars. (Exception: tiny generated bits with no design surface — an SVG progress ring, an injected `<span>` cursor — may be created in TS.)
5. **Wire every interaction it needs** — hover, click, drag, scroll, animation — using `@xo/utils` helpers rather than raw math/rAF (`damp` / `createDampedValue`, `panGesture`, `frameManager`, `createAnimate`, `interpolate`, `debounce`, `throttle`).
6. **Clean up in `unmount()`** — abort listeners, disconnect observers, cancel animation frames. Use a single `AbortController` (see api ref §4).

A component MUST NOT:

- Create a demo `.html` file. No showcase, no demo page — the section that consumes it provides the markup.
- Hard-code styling. Styling happens in Liquid/SCSS via the `xo-css` skill. The component may toggle classes / set CSS custom properties (`this.style.setProperty("--progress", ...)`) so the stylesheet can react, but it does not own the look.
- Import `morph` (not exported).

## Step-by-step

### 1. Target file
The component is a flat file at `src/scripts/<name>.ts` — no subfolder, no `doc.md`. Auto-loaded via `src/utils/import-scripts.ts`; no manual registration.

### 2. Duplication guard (do this before writing anything)
Check the live component set: `mcp__xo-components__find_components("<use case>")` (or `list_components()`). If a pre-built `xo-*` component already covers the behavior, STOP — don't author a redundant one; tell the user the tag already exists (they'd place it in section markup via `design-to-liquid`). Only proceed when nothing fits, or the ask is a genuinely new interaction.

### 3. Name it
`xo-<kebab-thing>`, descriptive and specific: `xo-tilt-card`, `xo-scroll-progress`, `xo-split-text`. Avoid clashing with any existing `xo-*` tag (the MCP check in step 2 surfaces those). The file is `<name>.ts` (flat in `src/scripts/`, no subfolder).

### 4. Design the shape
Decide before coding:
- **Props** (`xo-*` attributes the section author will set) → `propTypes`, `defaultProps`, `observedProps`.
- **State** (internal, reactive) → `State` interface + `state` field.
- **Child elements** it queries (a play button, a track, slides) → query them in `mount()`.
- **Which utils** do the heavy lifting (`utils.md`).
- **What it reflects** — classes/attributes/CSS vars it sets so SCSS can style each state.

### 5. Write it
Skeleton — copy and adapt:

```typescript
// <xo-thing> — one-line purpose. Note what it enhances and what it reflects
// (classes / xo-* attrs / CSS vars) so the section author + SCSS know the contract.
import { XoComponent, customElements, GetProps } from "@xo/utils";

const propTypes = {
  xoSpeed: Number,
};
interface Props extends GetProps<typeof propTypes> {}

interface State {
  active: boolean;
}

@customElements("xo-thing")
export class Thing extends XoComponent<Props, State> {
  static propTypes = propTypes;
  static defaultProps: Partial<Props> = { xoSpeed: 300 };
  static observedProps: (keyof Props)[] = ["xoSpeed"];

  state: State = { active: false };

  private controller = new AbortController();
  private trigger = this.querySelector("xo-thing-trigger") as HTMLElement | null;

  private handleClick = () => {
    this.setState((prev) => ({ active: !prev.active }));
  };

  mount() {
    this.trigger?.addEventListener("click", this.handleClick, { signal: this.controller.signal });
  }

  stateUpdate(prevState: State) {
    if (prevState.active !== this.state.active) {
      this.classList.toggle("xo-thing--active", this.state.active); // SCSS reacts to this
    }
  }

  unmount() {
    this.controller.abort();
  }
}
```

For animation-heavy work, drive it through utils rather than a hand-rolled loop:

```typescript
import { createDampedValue } from "@xo/utils";
private damped = createDampedValue({ initialValue: 0 });
// this.damped.onUpdate((v) => this.style.setProperty("--x", `${v}px`));
// this.damped.setValue(targetX);   // in a pointermove handler
// this.damped.destroy();           // in unmount()
```

### 6. Verify it renders
After writing, run `mcp__xo-design__check_render_errors({ pages: [...] })` on any page that uses the tag (or omit `pages` to sweep all). A component whose class throws on mount renders nothing with no SCSS error — this catch is the only signal. Fix any reported render/console errors before finishing.

### 7. Hand off
Tell the user the tag name, its props, the child tags it expects, and which classes/attributes/CSS vars it reflects — so the section markup (HTML/Liquid) and `xo-css` styling can be authored against a known contract. If it's a compositional component (parent + child tags), give a minimal usage snippet.

## Common shapes

- **Toggle / reveal** — state boolean, click handler, reflect an `--active` class. (But check `xo-toggle` / `xo-collapse` first.)
- **Pointer-follow / tilt / magnetic** — `panGesture` or pointer events → `createDampedValue` → CSS vars. (Check `xo-magnetic` / `xo-cursor` first.)
- **Scroll-driven** — `frameManager` + `interpolate` mapping scroll progress to transforms. (Check `xo-parallax` / `xo-scroll-*` first.)
- **Media control** — `playVideo` / `pauseVideo`, reflect `xo-playing` attr for SCSS icon swap (see `src/snippets/product-video-card/product-video-card.script-global.ts` for the reference pattern).
