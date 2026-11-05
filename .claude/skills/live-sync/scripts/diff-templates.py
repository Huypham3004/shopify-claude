#!/usr/bin/env python3
"""Compare pulled live-theme templates against their per-preset source templates.

Live  : demo-live/<Label>/templates/<name>.json          (pulled by pull-live.sh)
Source: src/pages/**/<name>.<preset>.json                (per-preset)
        src/pages/**/<name>.all.json                     (shared by every preset)

Usage
  diff-templates.py                              report every preset in stores.json
  diff-templates.py --preset preset-1            one preset (--label Verso also works)
  diff-templates.py --json                       machine-readable report
  diff-templates.py --detail index.json --preset preset-1
  diff-templates.py --apply index.json page.about.json --preset preset-1
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "demo-live" / "stores.json"
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
MAX_VALUE = 110
MAX_DETAIL = 60


# ── config ────────────────────────────────────────────────────────────────────
def load_presets(selector: str | None) -> list[dict]:
    if not CONFIG.exists():
        sys.exit(f"error: {CONFIG.relative_to(ROOT)} not found — create it first (see SKILL.md).")
    entries = json.loads(CONFIG.read_text(encoding="utf-8")).get("presets", [])
    for e in entries:
        if not all(e.get(k) for k in ("preset", "label", "store")):
            sys.exit(f"error: incomplete entry in stores.json: {e!r}")
    if selector:
        s = selector.lower()
        entries = [e for e in entries if s in (e["preset"].lower(), e["label"].lower())]
        if not entries:
            sys.exit(f"error: no preset matched {selector!r} in stores.json")
    return entries


# ── json io ───────────────────────────────────────────────────────────────────
def read_json(path: Path):
    """Parse a Shopify template JSON, tolerating the /* */ comments Shopify allows."""
    raw = path.read_text(encoding="utf-8")
    stripped = BLOCK_COMMENT.sub("", raw)
    try:
        return json.loads(stripped), (stripped != raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path.relative_to(ROOT)} is not valid JSON — {exc}")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ── mapping ───────────────────────────────────────────────────────────────────
def source_for(stem: str, preset: str) -> tuple[list[Path], bool]:
    """Return (candidate source paths, shared) for a live template stem."""
    scoped = sorted((ROOT / "src" / "pages").rglob(f"{stem}.{preset}.json"))
    if scoped:
        return scoped, False
    shared = sorted((ROOT / "src" / "pages").rglob(f"{stem}.all.json"))
    return shared, bool(shared)


def live_templates(label: str) -> list[Path]:
    base = ROOT / "demo-live" / label / "templates"
    return sorted(p for p in base.rglob("*.json") if p.is_file()) if base.is_dir() else []


def stem_of(live_path: Path, label: str) -> str:
    rel = live_path.relative_to(ROOT / "demo-live" / label / "templates")
    return rel.name[: -len(".json")]


# ── diff ──────────────────────────────────────────────────────────────────────
def walk(live, src, path: str, out: list) -> None:
    if isinstance(live, dict) and isinstance(src, dict):
        for key in list(src) + [k for k in live if k not in src]:
            child = f"{path}.{key}" if path else key
            if key not in live:
                out.append(("-", child, None, src[key]))
            elif key not in src:
                out.append(("+", child, live[key], None))
            else:
                walk(live[key], src[key], child, out)
    elif isinstance(live, list) and isinstance(src, list):
        if live != src:
            if len(live) == len(src):
                if all(isinstance(v, (str, int, float)) for v in live) and sorted(map(str, live)) == sorted(map(str, src)):
                    out.append(("~", f"{path} (reordered)", live, src))
                else:
                    for i, (a, b) in enumerate(zip(live, src)):
                        walk(a, b, f"{path}[{i}]", out)
            elif all(isinstance(v, (str, int, float)) for v in live + src):
                # e.g. "order" — report the moved members, not the whole array
                for item in [v for v in live if v not in src]:
                    out.append(("+", f"{path}[{item}]", item, None))
                for item in [v for v in src if v not in live]:
                    out.append(("-", f"{path}[{item}]", None, item))
            else:
                out.append(("~", path, live, src))
    elif live != src:
        out.append(("~", path, live, src))


def diff(live, src) -> list[tuple]:
    out: list[tuple] = []
    walk(live, src, "", out)
    return out


def summarize(changes: list[tuple]) -> str:
    """One-line headline: what moved at the section level + everything else."""
    sec_add, sec_del, sec_mod, other, order = set(), set(), set(), 0, False
    for kind, path, _, _ in changes:
        parts = path.split(".")
        if parts[0] == "sections" and len(parts) >= 2:
            name = parts[1]
            (sec_add if kind == "+" and len(parts) == 2 else
             sec_del if kind == "-" and len(parts) == 2 else sec_mod).add(name)
        elif parts[0].startswith("order"):
            order = True
        else:
            other += 1
    bits = []
    if sec_add: bits.append(f"+{len(sec_add)} section")
    if sec_del: bits.append(f"-{len(sec_del)} section")
    if sec_mod: bits.append(f"~{len(sec_mod)} section")
    if order: bits.append("order changed")
    if other: bits.append(f"{other} other")
    return ", ".join(bits) or f"{len(changes)} change(s)"


def clip(value) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else repr(value)
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE] + "…"


# ── report ────────────────────────────────────────────────────────────────────
def scan(entry: dict) -> list[dict]:
    preset, label = entry["preset"], entry["label"]
    rows: list[dict] = []
    seen: set[Path] = set()

    for live_path in live_templates(label):
        stem = stem_of(live_path, label)
        candidates, shared = source_for(stem, preset)
        row = {"template": f"{stem}.json", "live": str(live_path.relative_to(ROOT)), "shared": shared}
        if not candidates:
            rows.append({**row, "status": "LIVE-ONLY", "src": None,
                         "note": f"no src/pages/**/{stem}.{preset}.json"})
            continue
        if len(candidates) > 1:
            rows.append({**row, "status": "AMBIGUOUS", "src": None,
                         "note": ", ".join(str(c.relative_to(ROOT)) for c in candidates)})
            continue
        src_path = candidates[0]
        seen.add(src_path)
        live_doc, _ = read_json(live_path)
        src_doc, _ = read_json(src_path)
        changes = diff(live_doc, src_doc)
        rows.append({**row,
                     "status": ("SAME" if not changes
                                else "SHARED-DIFF" if shared else "DIFF"),
                     "src": str(src_path.relative_to(ROOT)),
                     "count": len(changes),
                     "note": summarize(changes) if changes else ""})

    for src_path in sorted((ROOT / "src" / "pages").rglob(f"*.{preset}.json")):
        if src_path in seen:
            continue
        rows.append({"template": src_path.name.replace(f".{preset}.json", ".json"),
                     "status": "SRC-ONLY", "live": None,
                     "src": str(src_path.relative_to(ROOT)),
                     "shared": False, "note": "not present on the live theme"})
    return rows


ORDER = {"DIFF": 0, "SHARED-DIFF": 1, "AMBIGUOUS": 2, "LIVE-ONLY": 3, "SRC-ONLY": 4, "SAME": 5}


def print_report(entry: dict, rows: list[dict]) -> None:
    print(f"\n{entry['label']}  ({entry['preset']} · {entry['store']})")
    if not rows:
        print("  (nothing pulled yet — run pull-live.sh first)")
        return
    for row in sorted(rows, key=lambda r: (ORDER[r["status"]], r["template"])):
        target = row.get("src") or "—"
        note = f"  {row['note']}" if row["note"] else ""
        print(f"  {row['status']:<12} {row['template']:<34} → {target}{note}")
    tally = {}
    for row in rows:
        tally[row["status"]] = tally.get(row["status"], 0) + 1
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda kv: ORDER[kv[0]])))


def print_detail(entry: dict, template: str) -> None:
    stem = template[:-5] if template.endswith(".json") else template
    live_path = ROOT / "demo-live" / entry["label"] / "templates" / f"{stem}.json"
    if not live_path.exists():
        sys.exit(f"error: {live_path.relative_to(ROOT)} not pulled")
    candidates, shared = source_for(stem, entry["preset"])
    if len(candidates) != 1:
        sys.exit(f"error: {len(candidates)} source match(es) for {stem} / {entry['preset']}")
    live_doc, _ = read_json(live_path)
    src_doc, _ = read_json(candidates[0])
    changes = diff(live_doc, src_doc)
    print(f"\n{entry['label']} · {stem}.json → {candidates[0].relative_to(ROOT)}"
          + ("   [SHARED .all.json]" if shared else ""))
    if not changes:
        print("  identical")
        return
    print(f"  {len(changes)} change(s)   (+ live only · - src only · ~ different)")
    for kind, path, live_val, src_val in changes[:MAX_DETAIL]:
        print(f"  {kind} {path}")
        if kind in ("+", "~"):
            print(f"      live: {clip(live_val)}")
        if kind in ("-", "~"):
            print(f"      src : {clip(src_val)}")
    if len(changes) > MAX_DETAIL:
        print(f"  … {len(changes) - MAX_DETAIL} more")


def collapse_spf(written: list[Path]) -> None:
    """Restore the project's inline `spf_*` array convention.

    json.dumps(indent=2) explodes every array onto its own lines, which breaks
    the format `scripts/collapse-spf.cjs` maintains across src/**/*.json. Run it
    on exactly the files just written, so an apply never leaves the repo in a
    shape `npm run spf:check` would fail.
    """
    script = ROOT / "scripts" / "collapse-spf.cjs"
    if not written or not script.exists():
        return
    try:
        proc = subprocess.run(["node", str(script), *map(str, written)],
                              cwd=ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        print("  ! node not found — run `npm run spf` yourself to re-collapse spf_ arrays")
        return
    if proc.returncode != 0:
        print(f"  ! collapse-spf failed: {(proc.stderr or proc.stdout).strip()}")
        return
    tail = [l for l in proc.stdout.splitlines() if l.strip()]
    if tail:
        print(f"  · {tail[-1].strip()}")


def apply(entry: dict, templates: list[str]) -> None:
    written: list[Path] = []
    for template in templates:
        stem = template[:-5] if template.endswith(".json") else template
        live_path = ROOT / "demo-live" / entry["label"] / "templates" / f"{stem}.json"
        if not live_path.exists():
            print(f"  ✗ {stem}.json — not pulled ({live_path.relative_to(ROOT)})")
            continue
        candidates, shared = source_for(stem, entry["preset"])
        if len(candidates) != 1:
            print(f"  ✗ {stem}.json — {len(candidates)} source match(es), refusing to guess")
            continue
        live_doc, had_comment = read_json(live_path)
        write_json(candidates[0], live_doc)
        written.append(candidates[0])
        flags = []
        if shared: flags.append("SHARED .all.json — affects every preset")
        if had_comment: flags.append("live /* comment */ dropped")
        suffix = f"   [{'; '.join(flags)}]" if flags else ""
        print(f"  ✓ {stem}.json → {candidates[0].relative_to(ROOT)}{suffix}")
    collapse_spf(written)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", "--label", dest="selector", help="preset id or demo label")
    ap.add_argument("--detail", metavar="TEMPLATE", help="path-level diff for one template")
    ap.add_argument("--apply", nargs="+", metavar="TEMPLATE", help="overwrite src preset template(s) with live")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args()

    entries = load_presets(args.selector)

    if args.detail or args.apply:
        if len(entries) != 1:
            sys.exit("error: --detail / --apply need --preset (or --label) to pick ONE demo")
        if args.detail:
            print_detail(entries[0], args.detail)
        if args.apply:
            print(f"\n{entries[0]['label']} ({entries[0]['preset']}) — applying live → src")
            apply(entries[0], args.apply)
        return

    report = {e["label"]: scan(e) for e in entries}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    for e in entries:
        print_report(e, report[e["label"]])


if __name__ == "__main__":
    main()
