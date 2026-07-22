# Responsive

Breakpoints, mobile-first approach, and responsive patterns.

## Breakpoints

XO-CSS is mobile-first.

| Breakpoint | Min-width | Range                                                     |
| ---------- | --------- | --------------------------------------------------------- |
| `@sm`      | 576px     | ≥576px — small tablets portrait                           |
| `@md`      | 768px     | ≥768px — tablets portrait, large phones landscape         |
| `@lg`      | 992px     | ≥992px — tablets landscape, small laptops                 |
| `@xl`      | 1200px    | ≥1200px — desktops                                        |
| `@xxl`     | 1400px    | ≥1400px — large desktops                                  |

## Mobile-First Approach

Classes without a breakpoint apply at all sizes. Classes with a breakpoint apply at that breakpoint and up.

```html
<!-- Hidden on mobile, visible from tablet up -->
<div class="d:none d:block@md">
  Visible at ≥768px
</div>

<!-- Padding s4 on mobile, s8 on desktop -->
<div class="p:0.6rem p:1.4rem@lg">
  Responsive padding
</div>

<!-- Stack on mobile, row on desktop -->
<div class="d:flex fld:column fld:row@md">
  Responsive direction
</div>
```

## Max-Width Queries

The `@+breakpoint` form applies **until** that breakpoint:

```html
<!-- Visible only below 768px (mobile only) -->
<div class="d:block d:none@+md">
  Mobile only
</div>

<!-- Padding s8 until <992px, then s4 -->
<div class="p:1.4rem p:0.6rem@+lg">
  Larger padding on smaller screens
</div>
```

Syntax: `@+breakpoint` = max-width.

## Common Patterns

### Show / hide

```html
<!-- Mobile only -->
<div class="d:block d:none@md">Mobile only</div>

<!-- Desktop only -->
<div class="d:none d:block@md">Desktop only</div>

<!-- Tablet only (≥768 and <992) -->
<div class="d:none d:block@md d:none@lg">Tablet only</div>
```

### Responsive spacing

```html
<!-- Progressive padding -->
<div class="p:0.6rem p:1rem@md p:1.4rem@lg p:2rem@xl">
  More padding on larger screens
</div>

<!-- Gap grows with viewport -->
<div class="d:flex gp:0.2rem gp:0.6rem@md gp:1rem@lg">
  Responsive gap
</div>
```

### Responsive typography

```html
<!-- Heading scales with viewport -->
<h1 class="fz:h3 fz:h2@md fz:h1@lg">
  Responsive heading
</h1>

<!-- Body slightly larger on desktop -->
<p class="fz:1.4rem fz:1.6rem@md">
  Responsive text
</p>
```

### Responsive width

```html
<!-- Full width on mobile, constrained on desktop -->
<div class="w:100% w:80rem@md mx:auto">
  Centered container
</div>

<!-- Different fractions per breakpoint -->
<div class="w:100% w:50%@md w:33.333%@lg">
  Responsive width
</div>
```

### Responsive positioning

```html
<!-- Fixed on mobile, static on desktop -->
<div class="pos:fixed pos:static@md">
  Mobile sticky header
</div>

<!-- Different offsets per breakpoint -->
<div class="pos:absolute t:0.6rem t:1.4rem@md l:0.6rem l:1.4rem@lg">
  Responsive positioning
</div>
```

## Responsive Flexbox Examples

### Navigation

```html
<!-- Vertical on mobile, horizontal on desktop -->
<nav class="d:flex fld:column fld:row@md gp:0.6rem gp:1rem@md">
  <a href="#">Home</a>
  <a href="#">About</a>
  <a href="#">Contact</a>
</nav>
```

### Card layout

```html
<!-- Stacked on mobile, side-by-side on desktop -->
<div class="d:flex fld:column fld:row@md gp:0.6rem">
  <img src="image.jpg" class="w:100% w:200px@md">
  <div class="flx:1">
    <h3>Card Title</h3>
    <p>Card description</p>
  </div>
</div>
```

### Space-between

```html
<!-- Centered on mobile, space-between on desktop -->
<div class="d:flex jc:center jc:space-between@md ai:center">
  <div>Left</div>
  <div>Right</div>
</div>
```

## Combining Responsive With Pseudo

```html
<!-- Hover effect on desktop only -->
<div class="c:foreground c:primary|h@md">
  Hover effect on desktop only
</div>

<!-- Different hover backgrounds per breakpoint -->
<div class="bgc:transparent bgc:layer-1|h@md bgc:layer-2|h@lg">
  Progressive hover backgrounds
</div>
```

## Best Practices

### 1. Think mobile-first

```html
<!-- ✅ Start mobile, enhance up -->
<div class="p:0.6rem p:1.4rem@lg">

<!-- ❌ Start desktop, degrade down -->
<div class="p:1.4rem p:0.6rem@+lg">
```

### 2. Progressive enhancement

```html
<!-- ✅ Enhance as the screen grows -->
<h1 class="fz:h3 fz:h2@md fz:h1@lg">

<!-- ❌ Don't shrink at larger screens -->
<h1 class="fz:h1 fz:h2@md fz:h3@lg">
```

### 3. Keep related properties at the same breakpoint

```html
<!-- ✅ -->
<div class="d:flex fld:column fld:row@md gp:0.6rem gp:1rem@md">

<!-- ❌ -->
<div class="d:flex fld:column fld:row@md gp:0.6rem gp:1rem@lg">
```

### 4. Test every breakpoint

- Mobile: <576px
- Small tablet portrait: 576–767px
- Tablet landscape: 768–991px
- Desktop: 992–1199px
- Large desktop: ≥1200px

## Container Patterns

### Content container

```html
<div class="w:100% maw:1200px mx:auto px:0.6rem px:1rem@md px:1.4rem@lg">
  Contained content
</div>
```

### Section spacing

```html
<section class="py:2.8rem py:4.4rem@md py:8rem@lg">
  Section content
</section>
```

### Full-bleed mobile, contained desktop

```html
<div class="w:100vw w:100%@md ml:-s4 ml:0@md mr:-s4 mr:0@md">
  Full-bleed on mobile
</div>
```

## Debug Helper

Show the active breakpoint while testing:

```html
<div class="d:none d:block@sm">SM active (≥576px)</div>
<div class="d:none d:block@md">MD active (≥768px)</div>
<div class="d:none d:block@lg">LG active (≥992px)</div>
<div class="d:none d:block@xl">XL active (≥1200px)</div>
<div class="d:none d:block@xxl">XXL active (≥1400px)</div>
```

## Related

- `./basics.md` — syntax and tokens
- `./layout.md` — flex, grid, spacing
- `./styling.md` — colors, typography, borders
- `./advanced.md` — pseudo states and hover patterns
