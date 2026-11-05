#!/usr/bin/env python3
from __future__ import annotations
"""
JSON template validator for this Shopify Liquid theme.

PRIMARY purpose: after editing a section/block `schema.js`, prove the page
templates that already ship values for it are still in sync.

`validate-schema.py` checks a schema against itself. This script checks the
OTHER direction — every `settings` key stored in `src/pages/**/*.json` must
still be declared by the schema of the section/block it belongs to. Dropping a
setting from a schema does NOT clean the templates that already wrote it, and
Shopify does not complain: unknown keys are ignored at render, so the drift is
invisible until a merchant saves in the Theme Editor (Shopify silently discards
them) and the next `/live-sync` shows a diff nobody authored.

Usage:
  python3 .../validate-templates.py src/pages/product/              # one page folder
  python3 .../validate-templates.py src/pages/product/product.preset-1.json
  python3 .../validate-templates.py --all                           # every src/pages/**/*.json

What gets checked:
  - The file is valid JSON
  - Every section `type` resolves to a schema (src/sections/*/, src/pages/*/*/,
    src/groups/*/*/)
  - Every section settings key is declared by that section's schema
  - Every block `type` resolves — an inline block in the parent schema's
    blocks[], a theme block under src/blocks/**, or @theme / @app
  - Every block settings key is declared by that block's schema
  - Nested blocks recurse with the same rules

Exit codes:
  0  all checks pass
  1  at least one validation error
  2  missing files / system error
"""
import argparse
import json
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
PAGES_DIR = ROOT / "src/pages"
BLOCKS_DIR = ROOT / "src/blocks"

# Where a section `type` in a template JSON can come from. The build flattens all
# of these into shopify/sections/<dirname>.liquid, so the folder name IS the type.
SECTION_ROOTS = [
    (ROOT / "src/sections", 1),   # src/sections/<type>/schema.js
    (ROOT / "src/pages", 2),      # src/pages/<page>/<type>/schema.js
    (ROOT / "src/groups", 2),     # src/groups/<group>/<type>/schema.js
]

errors: list[str] = []
warnings_list: list[str] = []


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


# ─── node bridge: import EVERY schema.js in one process ───────────────────────
# validate-schema.py spawns node per file, which is fine for one section. Here we
# need the whole schema surface to check a template, so a per-file spawn would
# mean 200+ node startups. One process, one JSON blob back.

_NODE_BRIDGE = r"""
const paths = JSON.parse(process.argv[1] ?? "[]");
const out = { schemas: {}, failed: {} };
for (const p of paths) {
  try {
    const m = await import(p + '?t=' + Date.now());
    const s = m.schema ?? m.default;
    if (s && typeof s === "object") out.schemas[p] = s;
  } catch (e) {
    out.failed[p] = String(e && e.message ? e.message : e).split("\n")[0];
  }
}
process.stdout.write(JSON.stringify(out));
"""


def node_import_many(js_paths: list[Path]) -> tuple[dict, dict]:
    """ESM-import many modules in one node process.
    Returns ({abs path: schema}, {abs path: error message})."""
    arg = json.dumps([str(p.resolve()) for p in js_paths])
    r = subprocess.run(
        ["node", "--input-type=module", "-e", _NODE_BRIDGE, "--", arg],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if r.returncode != 0:
        print(_color(31, "✗ node bridge failed:"))
        print(r.stderr.strip()[:2000])
        sys.exit(2)
    try:
        data = json.loads(r.stdout)
    except Exception as e:
        print(_color(31, f"✗ node bridge output not JSON: {e}"))
        print(r.stdout[:400])
        sys.exit(2)
    return data.get("schemas", {}), data.get("failed", {})


# ─── schema registry ──────────────────────────────────────────────────────────

def collect_schema_paths() -> tuple[dict[str, Path], dict[str, Path]]:
    """Map section type → schema.js and theme-block type → schema.js.
    The folder name is the type in both cases."""
    sections: dict[str, Path] = {}
    for root, depth in SECTION_ROOTS:
        if not root.exists():
            continue
        for schema in root.glob("/".join(["*"] * depth) + "/schema.js"):
            sections.setdefault(schema.parent.name, schema)
    blocks: dict[str, Path] = {}
    if BLOCKS_DIR.exists():
        for schema in BLOCKS_DIR.rglob("schema.js"):
            blocks.setdefault(schema.parent.name, schema)
    return sections, blocks


def declared_ids(schema: dict) -> set[str]:
    """Setting IDs a compiled schema declares. Builder helpers (deviceSetting,
    paddingAttrsSchemaSettings, …) have already expanded to concrete ids by the
    time the module is imported, so a flat pass over settings[] is enough."""
    return {s["id"] for s in (schema.get("settings") or []) if isinstance(s, dict) and s.get("id")}


def inline_block_def(schema: dict, block_type: str) -> dict | None:
    for b in schema.get("blocks") or []:
        if isinstance(b, dict) and b.get("type") == block_type:
            return b
    return None


def accepts_theme_blocks(schema: dict) -> bool:
    return any(
        isinstance(b, dict) and b.get("type") in ("@theme", "@app")
        for b in schema.get("blocks") or []
    )


# ─── template walk ────────────────────────────────────────────────────────────

class Registry:
    def __init__(self) -> None:
        section_paths, block_paths = collect_schema_paths()
        self.section_paths = section_paths
        self.block_paths = block_paths
        loaded, failed = node_import_many(
            list(section_paths.values()) + list(block_paths.values())
        )
        self.by_path = loaded
        self.failed = failed

    def section(self, stype: str) -> dict | None:
        p = self.section_paths.get(stype)
        return self.by_path.get(str(p.resolve())) if p else None

    def theme_block(self, btype: str) -> dict | None:
        p = self.block_paths.get(btype)
        return self.by_path.get(str(p.resolve())) if p else None

    def import_error(self, type_name: str) -> str | None:
        for table in (self.section_paths, self.block_paths):
            p = table.get(type_name)
            if p:
                return self.failed.get(str(p.resolve()))
        return None


def check_blocks(blocks: dict, parent_schema: dict, ctx: str, reg: Registry) -> None:
    """Validate a template `blocks` map against the schema that accepts them."""
    for bid, blk in (blocks or {}).items():
        if not isinstance(blk, dict):
            continue
        btype = blk.get("type") or ""
        if btype.startswith("@"):
            continue  # @app blocks carry app-owned settings — not ours to check

        # A block type can be declared three ways, and a bare `{ type: "x" }`
        # entry is ambiguous between the last two — it is a theme-block
        # REFERENCE when src/blocks/** owns that name, otherwise an inline block
        # that simply has no settings (article title / content / share / …),
        # whose allowed-id set is empty rather than unknown.
        inline = inline_block_def(parent_schema, btype)
        theme = reg.theme_block(btype)
        if inline is not None and inline.get("settings") is not None:
            bschema = inline
        elif theme is not None:
            bschema = theme
        elif inline is not None:
            bschema = inline
        else:
            if accepts_theme_blocks(parent_schema):
                # parent takes @theme blocks but this one's schema.js is missing
                reason = reg.import_error(btype) or "no schema.js found"
                warn(f"{ctx} block '{bid}' type '{btype}' — settings unchecked ({reason})")
            else:
                err(f"{ctx} block '{bid}' declares type '{btype}' the parent schema does not accept")
            continue

        allowed = declared_ids(bschema)
        for key in (blk.get("settings") or {}):
            if key not in allowed:
                err(f"{ctx} block '{bid}' ({btype}): orphan setting '{key}'")

        nested = blk.get("blocks")
        if nested:
            check_blocks(nested, bschema, f"{ctx} {btype}#{bid} >", reg)


def check_template(path: Path, reg: Registry) -> None:
    rel = path.relative_to(ROOT)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        heading(f"─── Template: {rel} ───")
        err(f"invalid JSON: {e}")
        return

    sections = data.get("sections")
    if not isinstance(sections, dict):
        return  # not a section-shaped template (locale file, settings blob, …)

    heading(f"─── Template: {rel} ───")
    before = len(errors)
    n_blocks = 0

    for sid, sec in sections.items():
        if not isinstance(sec, dict):
            continue
        stype = sec.get("type") or ""
        schema = reg.section(stype)
        if schema is None:
            reason = reg.import_error(stype)
            if reason:
                warn(f"section '{sid}' type '{stype}' — unchecked ({reason})")
            else:
                err(f"section '{sid}' declares type '{stype}' — no schema.js found for it")
            continue

        allowed = declared_ids(schema)
        for key in (sec.get("settings") or {}):
            if key not in allowed:
                err(f"section '{sid}' ({stype}): orphan setting '{key}'")

        blocks = sec.get("blocks") or {}
        n_blocks += len(blocks)
        check_blocks(blocks, schema, f"section '{sid}' ({stype})", reg)

    if len(errors) == before:
        ok(f"{len(sections)} section(s), {n_blocks} block(s) — all settings declared")


# ─── cli ──────────────────────────────────────────────────────────────────────

def gather_targets(arg: str | None, scan_all: bool) -> list[Path]:
    if scan_all:
        if not PAGES_DIR.exists():
            print(_color(31, f"✗ {PAGES_DIR} not found"))
            sys.exit(2)
        return sorted(PAGES_DIR.rglob("*.json"))
    p = (ROOT / arg).resolve() if not Path(arg).is_absolute() else Path(arg)
    if p.is_dir():
        return sorted(p.rglob("*.json"))
    if p.is_file():
        return [p]
    print(_color(31, f"✗ not found: {arg}"))
    sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("target", nargs="?",
                    help="a src/pages/<page>/ folder or a single .json template")
    ap.add_argument("--all", action="store_true",
                    help="validate every JSON template under src/pages/")
    args = ap.parse_args()

    if not args.target and not args.all:
        print(_color(33, "\nNothing to validate — pass a template path or --all."))
        sys.exit(0)

    targets = gather_targets(args.target, args.all)
    reg = Registry()

    for t in targets:
        check_template(t, reg)

    print()
    if warnings_list:
        print(_color(33, f"⚠ {len(warnings_list)} warning(s) (schema could not be read)"))
    if errors:
        print(_color(31, f"✗ {len(errors)} validation error(s) in {len(targets)} template file(s)"))
        sys.exit(1)
    print(_color(32, f"✅ All checks passed ({len(targets)} template file(s) scanned)"))


if __name__ == "__main__":
    main()
