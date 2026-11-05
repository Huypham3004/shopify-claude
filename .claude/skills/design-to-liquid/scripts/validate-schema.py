#!/usr/bin/env python3
from __future__ import annotations
"""
Schema validator for this Shopify Liquid theme.

PRIMARY purpose: validate the schema.js you just wrote/edited for a section.

Usage:
  python scripts/validate-schema.py src/sections/<name>/             # default — validate that section's schema.js
  python scripts/validate-schema.py src/sections/<name>/schema.js    # same, full path
  python scripts/validate-schema.py --all                            # scan every src/sections/*/schema.js
  python scripts/validate-schema.py --preset src/sections/<name>/preset-1.js   # also validate a section/block preset
  python scripts/validate-schema.py --theme                          # also run theme-settings sanity (presets + current)

What gets checked on a section schema:
  - Compiles via dynamic ESM import (catches syntax / import errors)
  - All setting IDs unique inside settings[]
  - range settings have min + max (step optional, defaults 1 per Shopify)
  - range max < 10000 (Shopify rejects max >= 10000 at upload — compiler/theme-check miss it)
  - range step count (max - min) / step <= 101 (Shopify's discrete-step cap)
  - select / radio settings have a non-empty options[] array
  - Every block type declared resolves to src/blocks/** / src/groups/** / @theme / @app

Optional cross-validation (--preset):
  - Section/block preset-N.js setting values match the sibling schema's constraints
  - Recursively walks nested blocks, checking each block type is accepted by its parent

Optional theme-settings sanity (--theme):
  - shopify/config/settings_data.json 'current' is an object (NOT a string ref —
    Theme Editor preview rejects string form)
  - All color_schemes entries match the color_scheme_group definition
  - No orphan scheme-shaped objects at preset top level
  - Every preset value satisfies its range / step / select constraint

Exit codes:
  0  all checks pass
  1  at least one validation error
  2  missing files / system error
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Resolve project root by walking up until we find package.json + src/.
# The script lives inside .claude/skills/design-to-liquid/scripts/ — depth from
# project root is variable depending on where the skill folder is dropped.
def _find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in (p, *p.parents):
        if (parent / "package.json").exists() and (parent / "src").is_dir():
            return parent
    raise FileNotFoundError("project root (package.json + src/) not found above " + str(p))

ROOT = _find_project_root()
SHOPIFY_SCHEMA_JSON = ROOT / "shopify/config/settings_schema.json"
SHOPIFY_DATA_JSON   = ROOT / "shopify/config/settings_data.json"
SECTIONS_DIR        = ROOT / "src/sections"
BLOCKS_DIR          = ROOT / "src/blocks"
GROUPS_DIR          = ROOT / "src/groups"

# Shopify's permitted tags inside an inline_richtext default value.
# Block-level tags (<br>, <p>, <h1>-<h6>, <ul>, <ol>, <li>, <div>, <img>, …)
# are REJECTED by the Theme Editor at install time. For multi-line / break
# content use a `richtext` setting (whose top-level must be <p>/<ul>/<ol>/<h1>-<h6>)
# or rely on CSS (max-width / white-space: pre-wrap) for visual line breaks.
INLINE_RICHTEXT_ALLOWED_TAGS = {"em", "strong", "b", "i", "u", "a", "span", "sup", "sub"}

# Theme Store label-audit rules (see references/theme-store-requirements.md).
# Format: (case-insensitive needle, replacement guidance)
LABEL_BANNED_PHRASES = [
    ("cta",              "use 'Button label'"),
    ("x position",       "use 'Horizontal position'"),
    ("y position",       "use 'Vertical position'"),
    ("homepage",         "use 'home page'"),
    ("slider",           "use 'slideshow'"),
    ("sub-heading",      "use 'subheading'"),
    ("shortcut icon",    "use 'favicon'"),
    ("website icon",     "use 'favicon'"),
    ("button text",      "use 'Button label'"),
    ("button name",      "use 'Button label'"),
    ("ajaxify",          "use 'cart type'"),
    ("check out",        "use 'checkout'"),
    ("side bar",         "use 'sidebar'"),
    ("main text",        "use 'body text'"),
    ("social sharing",   "use 'social media'"),
]

# American English spelling — British forms banned.
LABEL_AME_SPELLING = [
    ("colour",      "color"),
    ("customise",   "customize"),
    ("customised",  "customized"),
    ("organise",    "organize"),
    ("organised",   "organized"),
    ("cancelled",   "canceled"),
    ("catalogue",   "catalog"),
    ("behaviour",   "behavior"),
    ("favourite",   "favorite"),
    ("theatre",     "theater"),
    ("centre",      "center"),
    ("centred",     "centered"),
    ("grey",        "gray"),
]

# Setting types that don't carry a `label` field.
LABEL_EXEMPT_TYPES = {"header", "paragraph"}

errors: list[str] = []
warnings_list: list[str] = []
STRICT = False


# ─── tiny logger ──────────────────────────────────────────────────────────────

def _color(code: int, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s

def err(msg: str) -> None:
    errors.append(msg)
    print(f"  {_color(31, '✗')} {msg}")

def warn(msg: str) -> None:
    warnings_list.append(msg)
    print(f"  {_color(33, '⚠')} {msg}")

def ok(msg: str) -> None:
    print(f"  {_color(32, '✓')} {msg}")

def heading(msg: str) -> None:
    print(f"\n{_color(1, msg)}")


# ─── node bridge: dynamically import a JS module and dump its export as JSON ──

def node_import(js_path: Path, export_name: str | None = None) -> tuple[dict | None, str | None]:
    """ESM-import a module. If `export_name` is given, dump that named export;
    otherwise tries `schema`, `preset1`, `presetFolio`, default, in order."""
    pick = (
        f"const m = await import('{js_path.resolve()}?t='+Date.now());"
        + (
            f"const out = m.{export_name};"
            if export_name
            else "const out = m.schema ?? m.preset1 ?? m.default ?? Object.values(m).find(v => v && typeof v === 'object');"
        )
        + "process.stdout.write(JSON.stringify(out));"
    )
    r = subprocess.run(
        ["node", "--input-type=module", "-e", pick],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if r.returncode != 0:
        return None, r.stderr.strip() or "unknown import error"
    try:
        return json.loads(r.stdout), None
    except Exception as e:
        return None, f"output not JSON: {e}\nstdout: {r.stdout[:400]}"


# ─── block folder resolver ────────────────────────────────────────────────────

def find_block_dir(block_type: str) -> Path | None:
    """Find src/blocks/**/<type>/ or src/groups/**/<type>/ that owns this block type."""
    if block_type.startswith("@"):
        return None  # @theme / @app are built-in
    for root in (BLOCKS_DIR, GROUPS_DIR):
        if not root.exists():
            continue
        for d in root.rglob(block_type):
            if d.is_dir() and (d / "schema.js").exists():
                return d
    return None


# ─── schema → constraint map ──────────────────────────────────────────────────

def schema_constraints(schema: dict) -> dict:
    """Flatten a schema's settings into {id: {kind, ...constraints}}."""
    cmap = {}
    for s in schema.get("settings", []):
        if not isinstance(s, dict) or not s.get("id"):
            continue
        sid = s["id"]
        t = s.get("type")
        if t == "range":
            cmap[sid] = {"kind": "range", "min": s["min"], "max": s["max"], "step": s.get("step", 1)}
        elif t in ("select", "radio"):
            cmap[sid] = {"kind": "select", "options": [o["value"] for o in s.get("options", []) if isinstance(o, dict)]}
        elif t == "color_scheme_group":
            cmap[sid] = {"kind": "color_scheme_group", "slots": [d["id"] for d in s.get("definition", []) if isinstance(d, dict)]}
        elif t == "checkbox":
            cmap[sid] = {"kind": "boolean"}
        else:
            cmap[sid] = {"kind": t}
    return cmap


def get_csg(schema: list[dict]) -> dict | None:
    """Find the color_scheme_group definition across the whole flat schema list."""
    for group in schema:
        for s in group.get("settings", []):
            if isinstance(s, dict) and s.get("type") == "color_scheme_group":
                return {"slots": [d["id"] for d in s.get("definition", []) if isinstance(d, dict)]}
    return None


# ─── value validators ─────────────────────────────────────────────────────────

def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def validate_value(sid: str, value, c: dict | None, ctx: str = "") -> None:
    if c is None:
        err(f"{ctx}undefined setting '{sid}'")
        return
    kind = c["kind"]
    if kind == "range":
        if not _is_number(value):
            err(f"{ctx}{sid} = {value!r} (range expects number)")
            return
        if value < c["min"]:
            err(f"{ctx}{sid} = {value} (less than min {c['min']})")
            return
        if value > c["max"]:
            err(f"{ctx}{sid} = {value} (greater than max {c['max']})")
            return
        step = c["step"]
        ratio = (value - c["min"]) / step
        if abs(ratio - round(ratio)) > 0.001:
            err(f"{ctx}{sid} = {value} (not on step {step} from min {c['min']})")
    elif kind == "select":
        if value not in c["options"]:
            err(f"{ctx}{sid} = {value!r} (must be one of {c['options']})")
    elif kind == "boolean":
        if not isinstance(value, bool):
            err(f"{ctx}{sid} = {value!r} (checkbox expects boolean)")
    elif kind == "richtext":
        if not isinstance(value, str):
            err(f"{ctx}{sid} = {value!r} (richtext expects string)")
            return
        VALID = (("<p>", "</p>"), ("<ul>", "</ul>"), ("<ol>", "</ol>"),
                 *((f"<h{i}>", f"</h{i}>") for i in range(1, 7)))
        if not any(value.startswith(o) and value.endswith(c2) for o, c2 in VALID):
            err(f"{ctx}{sid}: richtext top-level must be <p>/<ul>/<ol>/<h1>-<h6>")
    elif kind == "text_alignment":
        if value not in ("left", "center", "right"):
            err(f"{ctx}{sid} = {value!r} (text_alignment must be left|center|right)")
    # other kinds (text, url, image_picker, color, font_picker, …) are not strictly validated


def validate_settings_map(settings_map: dict, cmap: dict, ctx: str) -> None:
    if not isinstance(settings_map, dict):
        return
    for sid, value in settings_map.items():
        validate_value(sid, value, cmap.get(sid), ctx)


# ─── color scheme validators ──────────────────────────────────────────────────

def validate_color_schemes(name: str, schemes, csg: dict, ctx: str) -> None:
    if not isinstance(schemes, dict) or not schemes:
        err(f"{ctx}color_schemes empty or not an object")
        return
    required = set(csg["slots"])
    scheme_ids = sorted(schemes.keys())
    ok(f"{ctx}color_schemes = {scheme_ids}")
    for sid, scheme in schemes.items():
        if not isinstance(scheme, dict) or "settings" not in scheme:
            err(f"{ctx}color_schemes.{sid}: missing 'settings' key")
            continue
        slots = scheme["settings"]
        if not isinstance(slots, dict):
            err(f"{ctx}color_schemes.{sid}.settings: not an object")
            continue
        missing = required - set(slots.keys())
        extra = set(slots.keys()) - required
        if missing:
            err(f"{ctx}color_schemes.{sid}: missing slots {sorted(missing)}")
        if extra:
            err(f"{ctx}color_schemes.{sid}: extra slots {sorted(extra)}")


SCHEME_HINT_SLOTS = {"primary", "background", "text", "button_text", "button_background", "secondary", "tertiary", "layer", "border", "overlay"}

def validate_orphan_schemes(preset: dict, ctx: str) -> None:
    for k, v in preset.items():
        if k in ("color_schemes", "sections", "current"):
            continue
        if isinstance(v, dict) and "settings" in v and isinstance(v["settings"], dict):
            hits = set(v["settings"].keys()) & SCHEME_HINT_SLOTS
            if len(hits) >= 3:
                err(f"{ctx}top-level key '{k}' looks like a color scheme (slots: {sorted(hits)}). Move it inside color_schemes.")


# ─── theme settings mode ──────────────────────────────────────────────────────

def validate_theme_settings() -> None:
    heading("─── Theme settings validation ───")
    if not SHOPIFY_SCHEMA_JSON.exists():
        err(f"missing {SHOPIFY_SCHEMA_JSON} — run a build first")
        return
    if not SHOPIFY_DATA_JSON.exists():
        err(f"missing {SHOPIFY_DATA_JSON} — run a build first")
        return

    schema_groups = json.loads(SHOPIFY_SCHEMA_JSON.read_text())
    cmap = {}
    for group in schema_groups:
        cmap.update(schema_constraints(group))
    csg = get_csg(schema_groups)

    data = json.loads(SHOPIFY_DATA_JSON.read_text())

    cur = data.get("current")
    print()
    if isinstance(cur, str):
        err(f"settings_data.json: 'current' is string ref {cur!r} — Theme Editor preview requires an object (deep clone of the active preset).")
    elif isinstance(cur, dict):
        ok("settings_data.json: 'current' is an object")
        _validate_preset_chunk("current", cur, cmap, csg)
    else:
        err(f"settings_data.json: 'current' invalid type {type(cur).__name__}")

    for name, preset in (data.get("presets") or {}).items():
        print(f"\n[preset] {name}")
        _validate_preset_chunk(name, preset, cmap, csg)


def _validate_preset_chunk(name: str, preset: dict, cmap: dict, csg: dict | None) -> None:
    ctx = f"[{name}] "
    if "color_schemes" in preset and csg:
        validate_color_schemes(name, preset["color_schemes"], csg, ctx)
    validate_orphan_schemes(preset, ctx)
    for key, value in preset.items():
        if key in ("color_schemes", "sections"):
            continue
        validate_value(key, value, cmap.get(key), ctx)


# ─── section schema sanity mode ───────────────────────────────────────────────

def _check_inline_richtext_default(sid: str | None, value) -> None:
    """Reject block-level / disallowed tags in an inline_richtext default."""
    if not isinstance(value, str):
        err(f"setting '{sid}' (inline_richtext): default must be string, got {type(value).__name__}")
        return
    tags = [t.lower() for t in re.findall(r"<\s*/?\s*([A-Za-z][A-Za-z0-9]*)", value)]
    bad = sorted({t for t in tags if t not in INLINE_RICHTEXT_ALLOWED_TAGS})
    if bad:
        err(f"setting '{sid}' (inline_richtext): default contains disallowed tag(s) {bad}. "
            f"Allowed: {sorted(INLINE_RICHTEXT_ALLOWED_TAGS)}. "
            f"For line breaks / paragraphs, use a `richtext` setting or rely on CSS (max-width).")


def _audit_label_text(field: str, owner: str, value) -> None:
    """Theme Store label-hygiene checks (issued as warnings).
    `field` is "label" or "content"; `owner` identifies which setting / header."""
    if not isinstance(value, str) or not value.strip():
        return
    # No ampersands in labels (use the word "and")
    if "&" in value and "&amp;" not in value and "&middot;" not in value:
        warn(f"{owner}: {field}={value!r} contains '&' — Theme Store rule: write 'and' instead")
    # No question marks
    if value.rstrip().endswith("?"):
        warn(f"{owner}: {field}={value!r} ends with '?' — Theme Store rule: use a declarative statement")
    low = value.lower()
    # Banned phrases (use word boundaries to avoid false positives like 'Practice')
    for needle, hint in LABEL_BANNED_PHRASES:
        if re.search(r"\b" + re.escape(needle) + r"\b", low):
            warn(f"{owner}: {field}={value!r} contains '{needle}' — {hint}")
    # American English spelling
    for ame_bad, ame_good in LABEL_AME_SPELLING:
        if re.search(r"\b" + re.escape(ame_bad) + r"\b", low):
            warn(f"{owner}: {field}={value!r} uses British spelling '{ame_bad}' — Theme Store rule: '{ame_good}'")
    # 'Title' as a label is discouraged in favour of 'Heading'
    if value.strip() == "Title":
        warn(f"{owner}: {field}='Title' — Theme Store rule: use 'Heading'")


def _audit_setting_label(setting: dict, owner_prefix: str) -> None:
    """Check that a setting has a label (or content for headers) and that
    label/content text follows Theme Store rules."""
    stype = setting.get("type")
    sid = setting.get("id")
    name = sid or stype or "?"
    owner = f"{owner_prefix}'{name}'"
    if stype in LABEL_EXEMPT_TYPES:
        # headers / paragraphs use `content` instead of `label`
        content = setting.get("content")
        if not content or not isinstance(content, str) or not content.strip():
            warn(f"{owner}: {stype} has no 'content' text")
            return
        _audit_label_text("content", owner, content)
        return
    label = setting.get("label")
    if not isinstance(label, str) or not label.strip():
        warn(f"{owner}: missing or empty 'label' — Theme Store requires every setting to have a label")
        return
    _audit_label_text("label", owner, label)


def _check_richtext_default(sid: str | None, value) -> None:
    """richtext top-level node must be <p>, <ul>, <ol>, or <h1>-<h6>."""
    if not isinstance(value, str):
        err(f"setting '{sid}' (richtext): default must be string, got {type(value).__name__}")
        return
    v = value.strip()
    VALID = (("<p>", "</p>"), ("<ul>", "</ul>"), ("<ol>", "</ol>"),
             *((f"<h{i}>", f"</h{i}>") for i in range(1, 7)))
    if not any(v.startswith(o) and v.endswith(c) for o, c in VALID):
        err(f"setting '{sid}' (richtext): default top-level must be <p>/<ul>/<ol>/<h1>-<h6>")


def validate_section_schema(path: str) -> None:
    p = Path(path).resolve()
    if p.is_dir():
        p = p / "schema.js"
    heading(f"─── Section schema: {p.relative_to(ROOT)} ───")
    if not p.exists():
        err(f"file not found: {p}")
        return
    schema, e = node_import(p, "schema")
    if schema is None:
        err(f"failed to import: {e}")
        return
    ok(f"compiles — name = {schema.get('name')!r}, class = {schema.get('class')!r}")

    # Section / preset display name audit (merchant-facing)
    sec_name = schema.get("name")
    if isinstance(sec_name, str) and sec_name.strip():
        _audit_label_text("name", f"section '{sec_name}'", sec_name)
    else:
        warn(f"schema missing 'name' — every section must have a display name")

    # Unique setting IDs
    ids = [s["id"] for s in schema.get("settings", []) if isinstance(s, dict) and s.get("id")]
    dups = sorted({sid for sid in ids if ids.count(sid) > 1})
    if dups:
        err(f"duplicate setting IDs: {dups}")
    else:
        ok(f"{len(ids)} setting IDs, all unique")

    # range / select / inline_richtext / richtext sanity + label audit
    for s in schema.get("settings", []):
        if not isinstance(s, dict):
            continue
        stype = s.get("type")
        sid   = s.get("id")
        _audit_setting_label(s, owner_prefix="setting ")
        if stype == "range":
            for k in ("min", "max"):
                if k not in s:
                    err(f"setting '{sid}' (range): missing '{k}'")
            # step is optional per Shopify spec (defaults to 1) — no error
            # Shopify rejects a range whose `max` is >= 10000 at upload time
            # ("Invalid schema: max must be less than 10000"). The compiler and
            # theme-check don't catch it; only the upload does.
            smax = s.get("max")
            if _is_number(smax) and smax >= 10000:
                err(f"setting '{sid}' (range): max = {smax} — Shopify requires range max < 10000. "
                    f"Lower it (e.g. 9000 or 9999).")
            # Shopify also caps the number of discrete steps at 101:
            # (max - min) / step must be <= 101, else the editor rejects the range.
            smin, sstep = s.get("min"), s.get("step", 1)
            if _is_number(smin) and _is_number(smax) and _is_number(sstep) and sstep > 0:
                n_steps = (smax - smin) / sstep
                if n_steps > 101:
                    err(f"setting '{sid}' (range): {n_steps:.0f} steps ((max-min)/step) exceeds "
                        f"Shopify's 101-step limit. Increase step or narrow min/max.")
                # Shopify also rejects a range with too FEW positions: the number of
                # selectable values (max-min)/step + 1 must be at least 3 ("Range
                # settings must have at least 3 steps" at upload). So (max-min)/step >= 2,
                # i.e. max >= min + 2*step. The compiler and theme-check miss it.
                if n_steps < 2:
                    n_values = int(n_steps) + 1
                    err(f"setting '{sid}' (range): only {n_values} selectable value(s) "
                        f"((max-min)/step + 1) — Shopify requires at least 3. "
                        f"Widen max (>= min + 2*step = {smin + 2 * sstep:g}) or reduce step.")
        elif stype in ("select", "radio"):
            if not s.get("options"):
                err(f"setting '{sid}' ({stype}): missing 'options' array")
            else:
                # Audit each option label too. Skip options whose value references
                # a CSS color-slot variable (var(--color-button-text), …): those
                # labels describe a color slot name from the scheme, not a CTA.
                for opt in s["options"]:
                    if not isinstance(opt, dict):
                        continue
                    olbl = opt.get("label")
                    oval = opt.get("value")
                    if isinstance(oval, str) and oval.startswith("var(--color"):
                        continue
                    if isinstance(olbl, str) and olbl.strip():
                        _audit_label_text("label", f"setting '{sid}' option '{oval if oval is not None else '?'}'", olbl)
        elif stype == "inline_richtext" and "default" in s:
            _check_inline_richtext_default(sid, s["default"])
        elif stype == "richtext" and "default" in s:
            _check_richtext_default(sid, s["default"])

    # Block display names + each block's settings labels
    for b in schema.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        bname = b.get("name")
        btype = b.get("type", "?")
        if isinstance(bname, str) and bname.strip():
            _audit_label_text("name", f"block '{btype}'", bname)
        # Inline blocks expose their settings here — audit those labels too
        for bs in b.get("settings") or []:
            if isinstance(bs, dict):
                _audit_setting_label(bs, owner_prefix=f"block '{btype}' setting ")

    # Block types declared resolve
    # Two valid forms (Shopify supports both):
    #   - Inline section blocks: { type, name, settings: [...] }  → block owned by section, no folder needed
    #   - Theme-block reference: { type }                          → block file required at src/blocks/<group>/<type>/
    blocks = schema.get("blocks", []) or []
    inline_count = 0
    theme_ref_count = 0
    unresolved = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        btype = b.get("type", "")
        if btype.startswith("@"):
            continue
        # Inline block — has its own settings array, no external file needed
        if isinstance(b.get("settings"), list):
            inline_count += 1
            continue
        # Theme-block reference — must have a folder under src/blocks/**
        theme_ref_count += 1
        if find_block_dir(btype) is None:
            unresolved.append(btype)
    if unresolved:
        err(f"theme-block reference(s) without folder under src/blocks/** or src/groups/**: {unresolved}")
    elif blocks:
        parts = []
        if inline_count:
            parts.append(f"{inline_count} inline")
        if theme_ref_count:
            parts.append(f"{theme_ref_count} theme-block ref")
        ok(f"{len(blocks)} block(s) declared ({', '.join(parts)}), all resolve")
    else:
        ok("0 block type(s) declared, all resolve")


# ─── section / block preset mode ──────────────────────────────────────────────

def validate_section_preset(preset_path_str: str) -> None:
    preset_path = Path(preset_path_str).resolve()
    heading(f"─── Preset: {preset_path.relative_to(ROOT)} ───")
    if not preset_path.exists():
        err(f"file not found: {preset_path}")
        return

    schema_path = preset_path.parent / "schema.js"
    if not schema_path.exists():
        err(f"sibling schema.js not found: {schema_path}")
        return

    schema, e = node_import(schema_path, "schema")
    if schema is None:
        err(f"failed to import schema.js: {e}")
        return
    ok(f"schema.js loaded — name = {schema.get('name')!r}")

    preset, e = node_import(preset_path)
    if preset is None:
        err(f"failed to import preset: {e}")
        return
    preset_name = preset.get("name", preset_path.stem)
    ok(f"preset loaded — name = {preset_name!r}")

    schema_cmap = schema_constraints(schema)
    ctx = f"[{preset_name}] "

    validate_settings_map(preset.get("settings", {}), schema_cmap, ctx)

    blocks = preset.get("blocks", {})
    if blocks:
        _validate_block_tree(blocks, schema, ctx, {})


def _validate_block_tree(blocks: dict, parent_schema: dict, ctx: str, cache: dict) -> None:
    """Recursively validate a preset's block tree against parent's accepted block types."""
    if not isinstance(blocks, dict):
        return
    parent_blocks = [b for b in (parent_schema.get("blocks") or []) if isinstance(b, dict) and b.get("type")]
    accepted_types = {b["type"] for b in parent_blocks}
    # Inline section blocks carry their own `settings` array and are scoped to
    # this parent — they intentionally have NO folder under src/blocks/**.
    # Resolve them from the parent, never via find_block_dir().
    inline_blocks = {b["type"]: b for b in parent_blocks if isinstance(b.get("settings"), list)}

    for block_id, block in blocks.items():
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if not btype:
            err(f"{ctx}block '{block_id}': missing 'type'")
            continue

        # Acceptance check against parent
        if accepted_types and not btype.startswith("@") and btype not in accepted_types and "@theme" not in accepted_types:
            err(f"{ctx}block '{btype}' not accepted by parent (parent accepts: {sorted(accepted_types)})")

        # Resolve block schema
        if btype.startswith("@"):
            continue  # built-in, skip validation
        # Inline block — parent owns the schema. NOT cached: `cache` is keyed by
        # bare type and inline types are parent-scoped, so two sections may each
        # declare a different `title` block.
        if btype in inline_blocks:
            bschema = inline_blocks[btype]
            bcmap = schema_constraints(bschema)
            validate_settings_map(block.get("settings", {}), bcmap, f"{ctx}block '{btype}' (inline): ")
            nested = block.get("blocks", {})
            if nested:
                _validate_block_tree(nested, bschema, f"{ctx}{btype} > ", cache)
            continue
        if btype not in cache:
            d = find_block_dir(btype)
            if not d:
                err(f"{ctx}block '{btype}': not declared inline by parent and "
                    f"no src/blocks/**/{btype}/ folder")
                cache[btype] = None
                continue
            bschema, e = node_import(d / "schema.js", "schema")
            if bschema is None:
                err(f"{ctx}block '{btype}': failed to import schema.js — {e}")
                cache[btype] = None
                continue
            cache[btype] = bschema
        bschema = cache[btype]
        if bschema is None:
            continue

        # Validate block's settings
        bcmap = schema_constraints(bschema)
        validate_settings_map(block.get("settings", {}), bcmap, f"{ctx}block '{btype}': ")

        # Recurse nested
        nested = block.get("blocks", {})
        if nested:
            _validate_block_tree(nested, bschema, f"{ctx}{btype} > ", cache)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("target", nargs="?",
                    help="Section folder or schema.js path (e.g. src/sections/subscribe/). Default target.")
    ap.add_argument("--all", action="store_true",
                    help="Scan every section under src/sections/ (each schema.js + any preset-*.js)")
    ap.add_argument("--preset", help="Also validate this section/block preset-N.js against its sibling schema.js")
    ap.add_argument("--theme", action="store_true",
                    help="Also run theme-settings sanity (shopify/config/settings_data.json + settings_schema.json)")
    ap.add_argument("--strict", action="store_true",
                    help="Treat label/copy warnings as errors (CI-friendly).")
    args = ap.parse_args()

    global STRICT
    STRICT = args.strict

    did_work = False

    if args.target:
        validate_section_schema(args.target)
        # Back-stop: also validate any sibling preset-*.js so the section/dir
        # command (the one the porting workflow actually runs) catches
        # preset↔schema id mismatches — e.g. a preset key `padding_top` that
        # matches no emitted setting ID (the real ids are top_padding_desktop,
        # …). Previously only --preset / --all checked presets, so dir-mode
        # passed while the preset silently shipped dead keys. Mirrors --all.
        _tp = Path(args.target).resolve()
        _sec_dir = _tp if _tp.is_dir() else _tp.parent
        for _preset in sorted(_sec_dir.glob("preset-*.js")):
            validate_section_preset(_preset)
        did_work = True
    if args.preset:
        validate_section_preset(args.preset)
        did_work = True
    if args.theme:
        validate_theme_settings()
        did_work = True
    if args.all:
        for sec in sorted(SECTIONS_DIR.iterdir()):
            if not sec.is_dir():
                continue
            if (sec / "schema.js").exists():
                validate_section_schema(sec)
            for p in sorted(sec.glob("preset-*.js")):
                validate_section_preset(p)
        did_work = True

    if not did_work:
        ap.print_help()
        print(_color(33, "\nNothing to validate — pass a section path, --all, --preset, or --theme."))
        sys.exit(2)

    print()
    if warnings_list:
        print(_color(33, f"⚠ {len(warnings_list)} warning(s) (Theme Store label / copy hygiene)"))
    if errors:
        print(_color(31, f"✗ {len(errors)} validation error(s)"))
        sys.exit(1)
    if STRICT and warnings_list:
        print(_color(31, "✗ --strict: warnings escalated to errors"))
        sys.exit(1)
    print(_color(32, "✅ All checks passed"))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(_color(31, f"✗ {e}"), file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
