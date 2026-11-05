#!/usr/bin/env python3
"""
image-drift.py — which JSON templates still point at an image the design replaced?

Companion to design-diff.py. It exists because an image-only design change LOOKS
like a no-op and is not one:

  - A ported `.liquid` never hard-codes an image; it renders a merchant
    `image_picker` setting. So for sections, an image swap really is a no-op.
  - A page TEMPLATE does hard-code one — `"image": "shopify://shop_images/<basename>"`
    in `src/pages/**/*.json`. The reference is the image's FILENAME, and the
    filename is exactly what a design image swap changes.

So the same design commit is a no-op for `src/sections/` and actionable for
`src/pages/`. design-diff.py tiers by file path and cannot see this; this script
diffs the image urls themselves and matches them against the templates.

Usage
  python3 image-drift.py                 # baseline from .agent-state/DESIGN-SYNC.md
  python3 image-drift.py --since <ref>
  python3 image-drift.py --audit          # no diff: every template ref vs the design's current images
  python3 image-drift.py --json

Exit codes
  0  no drift (or audit finished)
  1  drift found — templates reference a basename the design no longer uses
  2  usage / repo error
  3  no baseline recorded and none supplied
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

URL_ATTR = re.compile(r'(?:src|poster|href|data-src)="(https?://[^"]+)"', re.I)
PICKER = re.compile(r'"([A-Za-z0-9_]+)"\s*:\s*"shopify://shop_images/([^"]+)"')
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg")


def _find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in (p, *p.parents):
        if (parent / "package.json").exists() and (parent / "src").is_dir():
            return parent
    print("error: project root not found (looking for package.json + src/)", file=sys.stderr)
    sys.exit(2)


def _git(design: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(design), *args],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _read_ledger_baseline(state_dir: Path):
    ledger = state_dir / "DESIGN-SYNC.md"
    if not ledger.exists():
        return None
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() in ("date", "") or set(cells[0]) <= {"-", ":", " "}:
            continue
        commit = cells[2].strip("`").strip()
        if commit:
            return {"date": cells[0], "version": cells[1].strip("`"), "commit": commit}
    return None


def _design_src(design: Path):
    """`design/src` or `design/<clone>/src` (a nested clone, as with bread)."""
    if (design / "src" / "pages").is_dir():
        return design / "src"
    if design.is_dir():
        for entry in sorted(os.listdir(design)):
            nested = design / entry / "src"
            if (nested / "pages").is_dir():
                return nested
    return None


def basename(url: str):
    b = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    return b if b.lower().endswith(IMG_EXT) else None


# ──────────────────────────────────────────────────────────────────────────────
# sides
# ──────────────────────────────────────────────────────────────────────────────

def template_refs(root: Path):
    """[{file, setting, basename}] — every shopify://shop_images/ ref under src/pages."""
    out = []
    pages = root / "src" / "pages"
    if not pages.is_dir():
        return out
    for dirpath, _dirs, files in os.walk(pages):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            path = Path(dirpath) / fn
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for setting, ref in PICKER.findall(text):
                out.append({
                    "file": str(path.relative_to(root)),
                    "setting": setting,
                    "basename": ref.split("?", 1)[0],
                })
    return out


SKIP_DIRS = {"dist", "node_modules", ".git", "vendor"}


def design_current_basenames(design_src: Path):
    """Every image basename the design references TODAY, across all source html.

    Build output (`dist/`) is skipped: it is a stale copy of the same pages and
    would mask a genuine removal."""
    found = set()
    for dirpath, dirs, files in os.walk(design_src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            try:
                text = (Path(dirpath) / fn).read_text(encoding="utf-8")
            except OSError:
                continue
            for url in URL_ATTR.findall(text):
                b = basename(url)
                if b:
                    found.add(b)
    return found


def diff_basenames(design: Path, baseline: str):
    """Basenames REMOVED and ADDED between baseline..HEAD, per design unit."""
    raw = _git(design, "diff", "-U0", "--find-renames", f"{baseline}..HEAD", "--", "*.html")
    removed, added, unit_of = {}, {}, {}
    unit = None
    for line in raw.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            path = line[6:]
            parts = path.split("/")
            if "sections" in parts:
                unit = parts[parts.index("sections") + 1] if len(parts) > parts.index("sections") + 1 else None
            elif "components" in parts:
                unit = parts[parts.index("components") + 1] if len(parts) > parts.index("components") + 1 else None
            else:
                unit = parts[-1]
            continue
        if line.startswith("-") and not line.startswith("---"):
            bucket = removed
        elif line.startswith("+") and not line.startswith("+++"):
            bucket = added
        else:
            continue
        for url in URL_ATTR.findall(line):
            b = basename(url)
            if b:
                bucket.setdefault(b, set()).add(unit)
                unit_of.setdefault(b, unit)
    return removed, added, unit_of


# ──────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Find templates pointing at images the design replaced.")
    ap.add_argument("--design", default=None)
    ap.add_argument("--since", default=None, help="baseline ref (overrides the ledger)")
    ap.add_argument("--audit", action="store_true",
                    help="ignore git history; compare every template ref against the design's current images")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = _find_project_root()
    design = Path(args.design) if args.design else root / "design"
    if not design.is_dir():
        print("error: no design repo at %s" % design, file=sys.stderr)
        return 2
    dsrc = _design_src(design)
    if dsrc is None:
        print("error: no design src/pages under %s" % design, file=sys.stderr)
        return 2

    refs = template_refs(root)
    by_basename = {}
    for r in refs:
        by_basename.setdefault(r["basename"], []).append(r)

    rows = []

    if args.audit:
        current = design_current_basenames(dsrc)
        for b, users in sorted(by_basename.items()):
            if b not in current:
                rows.append({"basename": b, "replacement": None, "unit": None,
                             "reason": "not referenced anywhere in the design",
                             "used_by": users})
        mode = "audit"
    else:
        ledger = _read_ledger_baseline(root / ".agent-state")
        baseline = args.since or (ledger or {}).get("commit")
        if not baseline:
            print("error: no baseline in .agent-state/DESIGN-SYNC.md and no --since given.",
                  file=sys.stderr)
            return 3
        if not _git(design, "rev-parse", "--verify", f"{baseline}^{{commit}}"):
            print("error: baseline ref '%s' not found in %s" % (baseline, design), file=sys.stderr)
            return 2
        removed, added, unit_of = diff_basenames(design, baseline)
        # A basename disappearing from one file is not enough: the page may have
        # been renamed while the image is still used elsewhere in the design.
        # Only a basename the design no longer references AT ALL is real drift.
        still_used = design_current_basenames(dsrc)
        gone = {b for b in removed if b not in added and b not in still_used}
        for b in sorted(gone):
            if b not in by_basename:
                continue
            unit = unit_of.get(b)
            # a plausible replacement = something added in the same design unit
            repl = sorted(x for x in added if unit and unit in added[x])
            rows.append({"basename": b, "replacement": repl or None, "unit": unit,
                         "reason": "removed from the design since the baseline",
                         "used_by": by_basename[b]})
        mode = "diff since %s" % baseline

    if args.json:
        print(json.dumps({"mode": mode, "template_refs": len(refs), "drift": rows}, indent=2))
        return 1 if rows else 0

    print("\n─── template image drift (%s) ───" % mode)
    print("  %d shopify://shop_images/ reference(s) across src/pages/" % len(refs))
    if not rows:
        print("  ✅ none of them points at an image the design dropped.")
        return 0

    print("  ⚠️  %d reference(s) need a decision:\n" % len(rows))
    for row in rows:
        print("  %s" % row["basename"])
        print("     %s" % row["reason"])
        if row["unit"]:
            print("     design unit: %s" % row["unit"])
        if row["replacement"]:
            print("     added in the same unit: %s" % ", ".join(row["replacement"][:4]))
        for u in row["used_by"]:
            print("     ← %s  [%s]" % (u["file"], u["setting"]))
        print()
    print("  These are template edits, not section re-ports. Do NOT rewrite them")
    print("  automatically — old/new pairing is a judgment call; take it to the user.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
