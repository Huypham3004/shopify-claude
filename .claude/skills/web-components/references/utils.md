# @xo/utils — Helper Catalog

Helpers importable via `import { x } from "@xo/utils"` — prefer them over hand-rolling logic when building an `xo-*` web component. They are thin facades over `window.XotinyUtils` (populated by `xo-critical.js`), resolved by a Vite alias, so a plain `import` just works inside `src/scripts/`.

> `morph` is **not exported** by the facade (commented out) — don't import it. `checkAttr` / `throwError` are web-component-core internals; you rarely call them directly.

## Animation & Easing

| Import | Signature | Use for |
|--------|-----------|---------|
| `createAnimate` | `createAnimate(): animated & { onStart, onUpdate, onEnd }` — call `animated({ from, to, duration?, easing?, iterations?, alternate?, ... })` | Tween a numeric value over time (width, opacity, etc.) with easing, looping, and start/update/end callbacks. |
| `createDampedValue` | `createDampedValue(options?: { threshold?, initialValue? }): DampedValue` | High-level auto-managed damped value (setValue/setLambda/onUpdate/onComplete/destroy) — smooth scroll, cursor-follow, parallax; uses FrameManager internally so no manual rAF. |
| `easings` | `easings.<name>(t: number): number` (e.g. `easings.spring`) | Easing curves to pass into `createAnimate` / `interpolate`. |

## Math & Interpolation

| Import | Signature | Use for |
|--------|-----------|---------|
| `damp` | `damp(current, target, lambda, deltaTime): number` | Frame-rate-independent smoothing toward a target; call once per rAF frame with per-frame `deltaTime` (in seconds). |
| `interpolate` | `interpolate({ value, inputRange: number[], outputRange: number[], easing? }): number` | Map a value from one numeric range to another (scroll → rotate/scale), optionally eased. |
| `clamp` | `clamp(value, min, max): number` | Constrain a number to the `[min, max]` range. |
| `rubberBandClamp` | `rubberBandClamp(value, min, max): number` | Clamp that stretches elastically past the bounds instead of hard-stopping (iOS overscroll feel). |
| `wrapAroundRange` | `wrapAroundRange(value, min, max): number` | Wrap a number around a range (past max → min, below min → max) — carousels, infinite indices. |
| `random` | `random(min, max): number` | Random number in `[min, max]` inclusive. |

## Events & Gestures

| Import | Signature | Use for |
|--------|-----------|---------|
| `panGesture` | `panGesture({ element, onStart?, onMove?, onEnd? }): { setValue, destroy }` | Drag/pan an element with `dx/dy` distance and `vx/vy` velocity in gesture state; drag-to-move, swipe, slider handles. |
| `Emitter` | `new Emitter<Events>()` → `.emit(name, ...args)`, `.on(name, fn): id`, `.off(id)` | Typed pub/sub event bus (pair with `CreateEvents<{...}>` type helper) for component-internal events. |

## DOM & Viewport

| Import | Signature | Use for |
|--------|-----------|---------|
| `DOMLoaded` | `DOMLoaded(cb: () => void): void` | Run a callback once the DOM is ready. |
| `inViewport` | `inViewport(el, options?): boolean` | Test / observe whether an element is in the viewport. |
| `offset` | `offset(el): { top, left }` | Get an element's document-relative top/left offset. |
| `popper` | `popper(el, { placement, offset }): { top, left, width, height }` | Measure where to position a floating element (tooltip/dropdown) relative to an anchor by placement + offset. |
| `getScrollbarWidth` | `getScrollbarWidth(): number` | Measure scrollbar width (compensate layout shift when locking scroll). |
| `imagesLoaded` | `imagesLoaded(urls: string[]): Promise<void>` | Await until all given image URLs have finished loading. |
| `playPauseVideo` exports | `playVideo(el)`, `pauseVideo(el)`, `isYoutube(src)`, `isVimeo(src)` | Play/pause a video, auto-detecting HTML5 / YouTube / Vimeo. |
| `cssInJs` exports | `createCssInJs<ClassNames>(scope)` → tagged template → `{ cssText, classes }`; `appendStyle(cssText, target)` | Author scoped CSS in JS with hashed class names and inject it — component-local styling (rare; prefer the `xo-css` skill in Liquid). |
| `SVGPath` | `SVGPath.toString(segments[]): string`, `SVGPath.toArray(d: string): segments[]` | Convert between SVG path `d` strings and structured `{ type, values }` arrays. |
| `isMobile` | `isMobile.any: boolean` (+ device flags) | Detect whether the current device is mobile. |
| `loadStyle` / `loadScript` | `loadStyle(input): Promise<void>` · `loadScript(input): Promise<void>` | Lazily inject an external stylesheet / script once. |

## Data & Objects

| Import | Signature | Use for |
|--------|-----------|---------|
| `cloneDeep` | `cloneDeep<T>(value: T): T` | Deep-clone an object/array to a fresh reference, avoiding mutation. |
| `equal` | `equal(a, b): boolean` | Deep-compare two arrays or objects for equality. |
| `objectKeys` | `objectKeys<T>(obj: T): (keyof T)[]` | `Object.keys` with correct typed return. |
| `objectValues` | `objectValues<T>(obj: T): T[keyof T][]` | `Object.values` with correct typed return. |
| `objectParse` | `objectParse(objStr: string): object` | Parse a loose object-literal string (unquoted keys) into a real object. |
| `typeOf` | `typeOf(value): string` | Accurate runtime type string (`'object'`, `'array'`, …) for any JS value. |
| `namingConvention` | `namingConvention.snakeToCamel / camelToSnake / pascalToSnake(str): string` | Convert identifier strings between snake/camel/pascal case. |
| `getAttrs` | `getAttrs(el, { types, pick }): Attrs` | Read element attributes into a typed object with type coercion and snake→camel key mapping. |
| `attrBoolean` | `attrBoolean.set(el, name, boolean)`, `attrBoolean.get(el, name): boolean` | Get/set a boolean HTML attribute (presence-based). |
| `fastLoop` exports | `each / map / filter / reduce / findIndex(arr, fn)` | Faster array iteration primitives than native methods. |
| `range` | `range(...)` | Generate a numeric range array. |

## Shopify & Money

| Import | Signature | Use for |
|--------|-----------|---------|
| `formatMoney` | `formatMoney(amount: number, format: string): string` | Format an amount into a currency string via a Shopify money format template (e.g. `{{amount_no_decimals}}`). |
| `imageUrl` | `imageUrl(url, { width, height }): string` | Append width/height query params to a (Shopify) image URL. |
| `getRootRoute` | `getRootRoute(): string` | Get the site's root Shopify route (locale/root path prefix). |
| `getShopifySectionId` | `getShopifySectionId(): string` | Get the current Shopify section's id. |
| `queryString` | `queryString.parse(str, asObject?)`, `queryString.stringify(obj | URLSearchParams): string` | Parse/serialize URL query strings (array of pairs or object). |

## Timing

| Import | Signature | Use for |
|--------|-----------|---------|
| `debounce` | `debounce(fn, wait: number): fn` | Collapse rapid repeated calls into one after quiet period — input/search handlers. |
| `throttle` | `throttle(fn, wait: number): fn` | Limit a function to run at most once per interval — scroll/resize/click spam. |
| `delay` | `delay(ms: number): Promise<void>` | `await`-able pause. |
| `frameManager` | `frameManager.add(fn, loop?)`, `.remove(fn)`, `.clear()` | Schedule callbacks on a shared 60fps rAF loop (pass `true` to run every frame); central animation scheduler. |
| `createCache` | `createCache(cooldownMs): { set(factory), get, has, clear, forceSet, remainingCooldown }` | Cooldown cache that only recomputes after the cooldown but `get()` never expires — debounce expensive DOM measurements, avoid layout thrash. |
| `requestIdleCallback` / `cancelIdleCallback` | polyfilled `requestIdleCallback` pair | Defer non-urgent work to browser idle time. |

## Misc

| Import | Signature | Use for |
|--------|-----------|---------|
| `XOStore` | `new XOStore<State>({ logger? })` → `.create(key, { initialState, useStorage? })`, `.get`, `.set`, `.subscribe(key, cb): unsubscribe` | App-wide reactive state store with optional persistence, logging, and per-key subscriptions. |
| `storage` | `storage.setItem/getItem/removeItem/clear/key` | localStorage-compatible API that degrades safely when cookies/storage are disabled. |
| `getBreakpointsOptions` | `getBreakpointsOptions(breakpoints: Record<number, Options>): Options` | Resolve the options object matching the current viewport width from a breakpoint map (slider `perView`, etc.). |
| `isBot` | `isBot(): boolean` | Detect crawler user-agents (skip expensive effects for bots). |
| `logger` | `logger.log/warn/error(...)` | Namespaced console logging. |

## Notes

- `frameManager` is the shared rAF scheduler (add/remove/clear frames at 60fps); `createDampedValue` and `createAnimate` build their loops on top of it, so prefer them over hand-rolling `requestAnimationFrame`.
- `damp()` is the low-level primitive — call it every frame with a per-frame `deltaTime` (seconds); reach for `createDampedValue()` when you want the frame loop, dynamic lambda, multi-subscriber `onUpdate`, `onComplete`, and `destroy()` handled for you.
- `easings` + `interpolate` compose with `createAnimate` (pass an easing, map the animated value through `interpolate`).
- State: `XOStore` for structured, subscribable app state; `storage` for cookie-safe localStorage; `createCache` is a cooldown (not TTL) cache — `get()` always keeps the last value, ideal for debouncing DOM reads.
- Some source docs are Vietnamese-only — identifiers here are verbatim, descriptions translated.
