# XoComponent — Core API Reference

`XoComponent` is the base class for authoring `xo-*` web components in TypeScript. It gives you React-like Props, State, Context, lifecycle methods, and decorators over a native Custom Element. Import everything from `@xo/utils`.

> Decorators require `"experimentalDecorators": true` in `tsconfig.json` — the project template already sets this, so no action needed inside `projects/`.

## Table of contents
1. [Minimal component](#1-minimal-component)
2. [Props](#2-props)
3. [State](#3-state)
4. [Lifecycle](#4-lifecycle)
5. [Decorators](#5-decorators)
6. [Context (provider / consumer)](#6-context-provider--consumer)
7. [Events](#7-events)
8. [Lazy loading](#8-lazy-loading)
9. [API cheat-sheet](#9-api-cheat-sheet)

---

## 1. Minimal component

```typescript
import { XoComponent, customElements } from "@xo/utils";

@customElements("xo-hello")
export class Hello extends XoComponent {
  mount() {
    this.textContent = "Hello world";
  }
}
```

```html
<xo-hello></xo-hello>
```

`@customElements(name)` registers the element (idempotent — safe if the module loads twice). `export class` so Vite's `import.meta.glob` picks it up via `main.ts`.

---

## 2. Props

Props are read from `xo-*` attributes. Declare a `propTypes` object, derive the `Props` type with `GetProps`, and read them from `this.props`.

```typescript
import { XoComponent, customElements, GetProps } from "@xo/utils";

const propTypes = {
  xoName: String,
  xoCount: Number,
  xoOpen: XoComponent.Optional.Boolean,           // optional boolean
  xoItems: [String],                              // array of strings
  xoConfig: { xoValue: String },                  // nested object
  xoStatus: XoComponent.Union("idle", "loading", "done"), // string union
};

interface Props extends GetProps<typeof propTypes> {}

@customElements("xo-widget")
export class Widget extends XoComponent<Props> {
  static propTypes = propTypes;

  static defaultProps: Partial<Props> = {
    xoCount: 0,
    xoOpen: false,
  };

  // Only props listed here trigger propUpdate() / @propUpdate when they change.
  static observedProps = ["xoCount", "xoOpen"];

  mount() {
    const { xoName, xoCount, xoStatus } = this.props;
  }
}
```

```html
<xo-widget xo-name="Hero" xo-count="3" xo-open xo-status="loading"></xo-widget>
```

### Prop type forms
| Form | Attribute example |
|------|-------------------|
| `String` / `'string'` | `xo-name="John"` |
| `Number` / `'number'` | `xo-count="42"` |
| `Boolean` / `'boolean'` | `xo-open` or `xo-open="true"` |
| `[String]` / `'array'` | `xo-items='["a","b"]'` |
| `{ key: String }` / `'object'` | `xo-config='{"key":"a"}'` |
| `XoComponent.Optional.<T>` / `XoComponent.Optional(...)` | marks the prop optional |
| `XoComponent.Union("a","b")` | constrains to a string set |

### Setting props from code (reflects to attributes)
```typescript
this.setProps({ xoCount: 5 });
this.setProps((prev) => ({ xoCount: prev.xoCount + 1 }));
```

Reflecting a prop to an attribute lets SCSS react to state (e.g. `xo-playing` swaps a play/pause icon) — a common pattern: mutate state internally, then `setProps` a boolean so the stylesheet can respond.

---

## 3. State

State is internal (not attribute-driven). Declare a `State` interface and a `state` field.

```typescript
interface State {
  index: number;
  items: string[];
}

@customElements("xo-list")
export class List extends XoComponent<{}, State> {
  state: State = { index: 0, items: [] };

  mount() {
    this.setState({ index: 1 });
    this.setState((prev) => ({ index: prev.index + 1 }));       // functional form
    this.setState((prev) => ({ items: [...prev.items, "new"] })); // derive from prev
  }

  // Called after any state change (manual form).
  stateUpdate(prevState: State) {
    if (prevState.index !== this.state.index) this.render();
  }
}
```

Always use the functional form (`prev => ...`) when the next value derives from the current one — `setState` batches, so two plain `setState({ n: this.state.n + 1 })` calls can collapse.

---

## 4. Lifecycle

| Method | When | Use for |
|--------|------|---------|
| `mount()` | element added to DOM (like `connectedCallback`) | query children, attach listeners, read initial state |
| `unmount()` | element removed (like `disconnectedCallback`) | **cleanup** — remove listeners, disconnect observers, cancel loops |
| `stateUpdate(prevState)` | after `setState` | diff prev vs current, patch DOM |
| `propUpdate({ name, prevProp, nextProp })` | an `observedProps` prop changed | react to attribute changes |
| `contextValueUpdate({ prevState, nextState })` | provider context changed | react to shared state |
| `visibilityChange()` | `document` visibility changed | pause/resume video, timers |

Cleanup is mandatory. The cleanest pattern is a single `AbortController` whose signal is passed to every `addEventListener`, aborted in `unmount()`:

```typescript
private controller = new AbortController();

mount() {
  this.button?.addEventListener("click", this.handleClick, { signal: this.controller.signal });
}

unmount() {
  this.controller.abort(); // removes every listener at once
}
```

---

## 5. Decorators

Decorators replace hand-written diffing in `stateUpdate` / `propUpdate` with targeted callbacks.

```typescript
import { XoComponent, customElements, stateUpdate, propUpdate, UpdateParams, PropUpdateParams } from "@xo/utils";

@customElements("xo-decorated")
export class Decorated extends XoComponent<Props, State> {
  // Run only when `count` changes
  @stateUpdate<State>(["count"])
  private renderCount() { /* ... */ }

  // Run on a custom condition (e.g. count increased)
  @stateUpdate<State>((prev, next) => next.count > prev.count)
  private onIncrease() { /* ... */ }

  // Run when an observed prop changes
  @propUpdate<Props>(["xoSpeed"])
  private onSpeed({ nextProp }: PropUpdateParams<Props>) { /* ... */ }
}
```

- `@stateUpdate()` — all state changes · `@stateUpdate(["a","b"])` — those keys · `@stateUpdate((prev,next)=>bool)` — custom.
- `@propUpdate([...])` — prop keys (must be in `observedProps`).
- `@contextUpdate([...])` — context keys (see below).
- Manual `stateUpdate()` / `propUpdate()` still fire alongside decorators.

---

## 6. Context (provider / consumer)

Share reactive state down a subtree. Mark the provider with `{ isProvider: true }`; consumers call `queryContext`.

```typescript
// Provider
@customElements("app-provider", { isProvider: true })
export class AppProvider extends XoComponent<{}, { theme: "light" | "dark" }> {
  state = { theme: "light" as const };
  public setTheme(theme: "light" | "dark") { this.setState({ theme }); }
}

// Consumer
@customElements("theme-switcher")
export class ThemeSwitcher extends XoComponent {
  private context = this.queryContext<AppProvider>("app-provider");

  @contextUpdate<{ theme: string }>(["theme"])
  onTheme({ nextState }: ContextValueUpdateParams<{ theme: string }>) {
    this.className = `theme-${nextState.theme}`;
  }
}
```

```html
<app-provider>
  <theme-switcher></theme-switcher> <!-- must be a descendant of the provider -->
</app-provider>
```

The consumer element must be nested inside the provider for `queryContext` to resolve.

---

## 7. Events

Emit typed custom events with `this.emit`; listen with normal `addEventListener`.

```typescript
this.emit("item-selected", { detail: { id: 123 }, bubbles: true });
```

```typescript
document.querySelector("xo-widget")
  ?.addEventListener("item-selected", (e: CustomEvent) => console.log(e.detail));
```

---

## 8. Lazy loading

Set `observeOnMount = true` and `mount()` only fires when the element enters the viewport (with a large root margin) — ideal for heavy below-the-fold components.

```typescript
@customElements("xo-heavy")
export class Heavy extends XoComponent {
  static observeOnMount = true;
  mount() { this.loadContent(); } // runs when scrolled near
}
```

---

## 9. API cheat-sheet

**Instance methods**
| Method | Purpose |
|--------|---------|
| `setState(patch | fn)` | update internal state (batched) |
| `setProps(patch | fn)` | update props, reflects to attributes |
| `getProps()` | current props |
| `emit(name, options)` | dispatch a custom event |
| `queryContext<T>(selector)` | get a parent provider instance |
| `subscribe(listener)` | subscribe to state changes |

**Static fields**
| Field | Purpose |
|-------|---------|
| `propTypes` | prop schema (drives parsing + `GetProps`) |
| `defaultProps` | fallback prop values |
| `observedProps` | which props trigger `propUpdate` |
| `observeOnMount` | lazy-mount on viewport entry |

**Decorators:** `@customElements(name, options?)`, `@stateUpdate(cond?)`, `@propUpdate(keys?)`, `@contextUpdate(keys?)`.

**Types (import from `@xo/utils`):** `GetProps`, `PropTypes`, `PropUpdateParams`, `UpdateParams`, `ContextValueUpdateParams`, `ObservedProps`.

### React → XoComponent map
| React | XoComponent |
|-------|-------------|
| `componentDidMount` | `mount()` |
| `componentWillUnmount` | `unmount()` |
| `componentDidUpdate` | `stateUpdate()` |
| `useEffect(fn, [count])` | `@stateUpdate(["count"])` |
| `Context.Provider` | `@customElements(name, { isProvider: true })` |
| `useContext()` | `this.queryContext()` |
