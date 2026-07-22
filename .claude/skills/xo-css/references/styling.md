# Styling

Colors, typography, borders, backgrounds, shadows, opacity, cursor, and interaction utilities.

## Colors

### Text color

```html
<div class="c:primary">Primary color</div>
<div class="c:foreground">Foreground color</div>
<div class="c:background">Background color (for text on dark bg)</div>
```

`c` = `color`

### Background color

```html
<div class="bgc:primary">Primary background</div>
<div class="bgc:background">Background</div>
<div class="bgc:layer-1">Layer 1 (elevated surface)</div>
```

`bgc` = `background-color`

### Border color

```html
<div class="bdc:border">Border color</div>
<div class="bdc:primary">Primary border</div>

<!-- Per side -->
<div class="bdtc:primary">Border top color</div>
<div class="bdrc:primary">Border right color</div>
<div class="bdbc:primary">Border bottom color</div>
<div class="bdlc:primary">Border left color</div>
```

| Shortcut | Property              |
| -------- | --------------------- |
| `bdc`    | `border-color`        |
| `bdtc`   | `border-top-color`    |
| `bdrc`   | `border-right-color`  |
| `bdbc`   | `border-bottom-color` |
| `bdlc`   | `border-left-color`   |

### Color with opacity

```html
<div class="c:foreground.5">Color 50% opacity</div>
<div class="c:primary.8">Color 80% opacity</div>
<div class="bgc:background.2">Background 20% opacity</div>
```

Format: `token.opacity` (opacity 0–1, no leading zero).

### Color tokens

Common tokens (full list in `theme-config/theme.config.json`):

- `primary`, `secondary`, `tertiary` — brand colors
- `foreground`, `foreground-2` — text colors
- `background` — surface
- `button-text`, `button-background` — button colors
- `border`, `layer`, `overlay` — UI surfaces
- `error`, `warning`, `success` — status

> [!IMPORTANT]
> Always use color tokens. Never use `white`, `black`, `red`, `#fff`, etc.

## Typography

### Font size

```html
<div class="fz:h1">Heading 1 size</div>
<div class="fz:h2">Heading 2 size</div>
<div class="fz:1.4rem">Body size</div>
<div class="fz:1.2rem">Small size</div>
```

`fz` = `font-size`

> Body/small font-sizes are **direct rem** (`fz:1.4rem`) — the `bodySizes` token map was removed. Only heading sizes are tokens: `fz:h1`–`fz:h6` / `fz:d1`–`fz:d4`.

### Font family

```html
<div class="ff:heading">Heading font</div>
<div class="ff:body">Body font</div>
<div class="ff:mono">Monospace font</div>
```

`ff` = `font-family`

### Font weight

```html
<div class="fw:300">Light (300)</div>
<div class="fw:400">Regular (400)</div>
<div class="fw:500">Medium (500)</div>
<div class="fw:600">Semibold (600)</div>
<div class="fw:700">Bold (700)</div>
<div class="fw:800">Extra bold (800)</div>
```

`fw` = `font-weight`

### Line height

```html
<div class="lh:1.3">Line height 1.3</div>
<div class="lh:1.4">Line height 1.4</div>
<div class="lh:1.5">Line height 1.5</div>
```

`lh` = `line-height`

### Letter spacing

```html
<div class="lts:0.1rem">Letter spacing 0.1rem</div>
<div class="lts:0.2rem">Letter spacing 0.2rem</div>
<div class="lts:-0.02em">Tight tracking</div>
```

`lts` = `letter-spacing`

> [!CAUTION]
> The shortcut is `lts`, not `ls`. `ls` is `list-style`.

### Text alignment

```html
<div class="ta:left">Align left</div>
<div class="ta:center">Align center</div>
<div class="ta:right">Align right</div>
<div class="ta:justify">Justify</div>
```

`ta` = `text-align`

### Text transform

```html
<div class="tt:uppercase">UPPERCASE</div>
<div class="tt:lowercase">lowercase</div>
<div class="tt:capitalize">Capitalize</div>
<div class="tt:none">None</div>
```

`tt` = `text-transform`

### Text decoration

```html
<div class="td:underline">Underline</div>
<div class="td:line-through">Strikethrough</div>
<div class="td:none">No decoration</div>
```

`td` = `text-decoration`

### Common typography patterns

```html
<!-- Heading 1 -->
<h1 class="fz:h1 ff:heading fw:700 lh:1.4">
  Main heading
</h1>

<!-- Heading 2 -->
<h2 class="fz:h2 ff:heading fw:600 lh:1.4">
  Sub heading
</h2>

<!-- Body text -->
<p class="fz:1.4rem ff:body fw:400 lh:1.4 c:foreground">
  Body text with comfortable readability
</p>

<!-- Small text -->
<small class="fz:1.2rem c:foreground.7">
  Helper text
</small>

<!-- Uppercase label -->
<span class="fz:1.2rem tt:uppercase lts:0.1rem fw:600">
  Label
</span>
```

## Borders

### Border

```html
<!-- All sides -->
<div class="bd:s1 bdc:border">1px solid border</div>
<div class="bd:s2 bdc:primary">2px solid primary</div>

<!-- Per side -->
<div class="bdt:s1 bdtc:border">Border top</div>
<div class="bdr:s1 bdrc:border">Border right</div>
<div class="bdb:s1 bdbc:border">Border bottom</div>
<div class="bdl:s1 bdlc:border">Border left</div>
```

| Shortcut | Property        |
| -------- | --------------- |
| `bd`     | `border`        |
| `bdt`    | `border-top`    |
| `bdr`    | `border-right`  |
| `bdb`    | `border-bottom` |
| `bdl`    | `border-left`   |

### Border style

```html
<div class="bds:solid">Solid</div>
<div class="bds:dashed">Dashed</div>
<div class="bds:dotted">Dotted</div>
<div class="bds:none">None</div>
```

`bds` = `border-style`

### Border radius

```html
<div class="bdrs:s1">Border radius s1</div>
<div class="bdrs:s2">Border radius s2</div>
<div class="bdrs:50%">Circle</div>
<div class="bdrs:max">Pill shape</div>

<!-- Per corner -->
<div class="bdrstl:s1">Top-left radius</div>
<div class="bdrstend:s1">Top-right radius</div>
<div class="bdrsbl:s1">Bottom-left radius</div>
<div class="bdrsbend:s1">Bottom-right radius</div>
```

| Shortcut    | Property                      |
| ----------- | ----------------------------- |
| `bdrs`      | `border-radius`               |
| `bdrstl`    | `border-top-left-radius`      |
| `bdrstend`  | `border-top-right-radius`     |
| `bdrsbl`    | `border-bottom-left-radius`   |
| `bdrsbend`  | `border-bottom-right-radius`  |

### Common border patterns

```html
<!-- Card with border -->
<div class="bd:s1 bds:solid bdc:border bdrs:s1 p:1rem">
  Card content
</div>

<!-- Divider via border-bottom -->
<div class="bdb:s1 bds:solid bdc:border pb:0.6rem mb:0.6rem">
  Content with divider below
</div>

<!-- Outline button -->
<button class="bd:s1 bds:solid bdc:primary bdrs:s1 p:0.6rem">
  Outline button
</button>
```

## Backgrounds

### Background color

```html
<div class="bgc:primary">Primary background</div>
<div class="bgc:transparent">Transparent</div>
```

### Background image

```html
<div class="bgi:var(--bg)" style="--bg: url('/path/to/image.jpg')">
  Background image
</div>
```

`bgi` = `background-image`

### Background size

```html
<div class="bgz:cover">Cover</div>
<div class="bgz:contain">Contain</div>
<div class="bgz:100%_auto">Custom size</div>
```

`bgz` = `background-size`

### Background position

```html
<div class="bgp:center">Center</div>
<div class="bgp:top">Top</div>
<div class="bgp:bottom">Bottom</div>
<div class="bgp:left_center">Left center</div>
```

`bgp` = `background-position`

### Background repeat

```html
<div class="bgr:no-repeat">No repeat</div>
<div class="bgr:repeat">Repeat</div>
<div class="bgr:repeat-x">Repeat x</div>
<div class="bgr:repeat-y">Repeat y</div>
```

`bgr` = `background-repeat`

### Common background patterns

```html
<!-- Hero with background image -->
<div
  class="bgi:var(--bg) bgz:cover bgp:center h:500px"
  style="--bg: url('/hero.jpg')"
></div>

<!-- Repeating pattern -->
<div
  class="bgi:var(--bg) bgz:auto bgr:repeat"
  style="--bg: url('/pattern.svg')"
></div>
```

## Shadows

```html
<div class="bxsh:s1/primary">Box shadow s1 with primary color</div>
<div class="bxsh:s2/secondary">Box shadow s2 with secondary</div>
<div class="bxsh:s3/tertiary">Box shadow s3 with tertiary</div>
<div class="bxsh:none">No shadow</div>
```

`bxsh` = `box-shadow`

## Opacity

```html
<div class="op:1">Fully opaque</div>
<div class="op:0.8">80% opacity</div>
<div class="op:0.5">50% opacity</div>
<div class="op:0">Fully transparent</div>
```

`op` = `opacity`

## Cursor

```html
<div class="cur:pointer">Pointer (hand)</div>
<div class="cur:default">Default arrow</div>
<div class="cur:text">Text cursor</div>
<div class="cur:move">Move</div>
<div class="cur:not-allowed">Not allowed</div>
```

`cur` = `cursor`

## Pointer Events

```html
<div class="pe:none">Pointer events none</div>
<div class="pe:auto">Pointer events auto</div>
```

`pe` = `pointer-events`

## User Select

```html
<div class="us:none">Cannot select</div>
<div class="us:auto">Can select (default)</div>
<div class="us:all">Select all on click</div>
```

`us` = `user-select`

## Related

- `./basics.md` — syntax and tokens
- `./layout.md` — flex, grid, spacing
- `./responsive.md` — breakpoints
- `./advanced.md` — pseudo states, transforms, transitions
