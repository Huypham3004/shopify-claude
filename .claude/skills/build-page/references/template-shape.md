# Template shape + the settings recipe

Everything in here is mechanical. Follow it rather than typing JSON by hand.

## 1. File layout

```
src/pages/<folder>/<template-name>.preset-N.json   →   shopify/templates/<template-name>.json
```

`<folder>` groups related templates; `<template-name>` is what Shopify sees.
`home/` is the one irregular case — its template is `index`, not `home`.

Which preset compiles is `.env`:

```
PRESET=preset-1
```

## 2. JSON shape

```json
{
  "sections": {
    "<section_key>": {
      "type": "<directory name under src/sections/>",
      "name": "<label shown in the editor sidebar>",
      "settings": { "...": "every id the schema declares" },
      "blocks":   { "<block_key>": { "type": "...", "settings": {} } },
      "block_order": ["<block_key>", "..."]
    }
  },
  "order": ["<section_key>", "..."]
}
```

- `order` is the render order and must mirror the design's `<main>` stacking order.
- `section_key` is snake_case, unique per template, and stable — the Theme Editor keys merchant edits off it. Suffix repeats: `spacer_1`, `spacer_2`.
- `blocks` needs `block_order`; a block present in `blocks` but absent from `block_order` never renders.

## 3. Generating `settings` from the compiled schema

The compiled schema is the only source of truth for which ids exist. Read it, seed defaults, override, assert.

```python
import json, re, collections

src = open('shopify/sections/<type>.liquid', encoding='utf-8').read()
schema = json.loads(re.search(r'\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}', src, re.S).group(1))

settings = collections.OrderedDict()
for s in schema['settings']:
    if s.get('id'):                       # header rows carry no id
        settings[s['id']] = s.get('default', '')

overrides = { ... }                       # the design's copy, images, padding
bad = [k for k in overrides if k not in settings]
assert not bad, "not in schema: %s" % bad
settings.update(overrides)
```

Why this and not hand-typing:

- builder helpers generate ids you would not guess — `deviceSetting()`, `paddingAttrsSchemaSettings()`, suffixed forms like `aspect_ratio_width_feature`
- seeding from defaults means the template is complete, matching how the Theme Editor writes it
- the assert makes an orphan key impossible, which is exactly what `validate-templates.py` checks for afterwards

## 4. Inserting into an existing template

A JSON round-trip rewrites formatting across the whole file. Generate the block, then splice it as text.

```python
body  = json.dumps(entry, indent=2, ensure_ascii=False)
block = '    "<key>": ' + "\n".join(
    (("    " + ln) if i else ln) for i, ln in enumerate(body.splitlines())
) + ",\n"

lines = open(path, encoding='utf-8').read().splitlines(keepends=True)
assert lines[idx].rstrip('\n') == '    "<the section it goes before>": {'
lines.insert(idx, block)
```

Then prove it was additive:

```bash
diff -u <backup> <file> | grep -c "^-[^-]"      # must print 0
```

`ensure_ascii=False` keeps em-dashes and accented copy readable.

## 5. Padding, scheme, width

`sectionSchemaSettings()` supplies these on every section. Map the design's
inline `--section-pt` / `--section-pb` onto them:

```json
"color_scheme": "background-1",
"device_padding": "desktop",
"inherit_desktop_padding": false,
"top_padding_desktop": 120,
"bottom_padding_desktop": 96,
"top_padding_mobile": 72,
"bottom_padding_mobile": 64
```

Range is **0–200 at step 2** — odd numbers are rejected by the validator.
`inherit_desktop_padding` must be `false` or the mobile values are ignored.

## 6. Resource settings

```json
"spf_collection": "shopify://collections/<handle>",
"spf_product":    "shopify://products/<handle>",
"spf_blog":       "news"
```

These resolve only if the handle exists on the target store. A wrong handle
renders empty with no error, so list them in the final report for the user to
confirm against the store.

## 7. Pitfalls

| Symptom | Cause |
| --- | --- |
| Section missing from the page | in `sections` but not in `order` |
| Block invisible | missing from `block_order` |
| Image blank | raw `https://` url in an `image_picker`, or a file on a different store |
| Mobile padding ignored | `inherit_desktop_padding: true` |
| Validator: orphan key | settings hand-typed instead of generated from the schema |
| Huge diff on a one-line change | JSON round-trip instead of a text splice |
| Header/footer duplicated | a group section pulled in from outside `<main>` |
