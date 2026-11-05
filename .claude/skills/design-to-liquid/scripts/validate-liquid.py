#!/usr/bin/env python3
from __future__ import annotations
"""
Liquid anti-pattern validator for this Shopify theme.

Catches Liquid mistakes that COMPILE but misbehave at runtime — the kind a
schema validator can't see because they live in markup, not schema.js. Run it
after writing/editing ANY .liquid file, the same way validate-schema.py is run
after a schema edit.

v1 rule set (intentionally small — grow it as new classes of bug surface):

  assign-with-condition
    `{% assign x = a != blank %}` does NOT evaluate the comparison. Liquid's
    `assign` takes a single VALUE (a variable/literal, optionally piped through
    filters) — it is not an expression evaluator, so comparison / logical
    operators (== != <> > < >= <= , contains / and / or) are not understood on
    an assign's right-hand side. The variable does not become the boolean you
    expect.
    Fix A: branch — `assign x = false` then `if … / assign x = true / endif`.
    Fix B: skip the flag — put the comparison straight in `{% if … %}`.
    See the liquid skill: references/gotchas.md #31.

  render-arg-expression
    `{% render 'x', label: 'a.b' | t %}` / `{% render 'x', lazy: forloop.first
    == false %}` are HARD Liquid syntax errors ("Expected end_of_string but
    found pipe / comparison") — the template fails to compile and the
    storefront shows a red error box. A render/include/content_for argument
    parses as a single VALUE: a literal, or a variable with property/index
    access. No filters, comparisons, logic or arithmetic.
    Fix: resolve the value in the {% liquid %} prelude, pass the variable in.
    A comparison needs BOTH steps — an if/endif (see rule 1) AND a prelude
    variable. See the liquid skill: references/gotchas.md #33.

Both Liquid tag shapes are scanned for each rule:
  - tag form:    {% assign x = … %} / {% render 'x', … %}  (and the -%} forms)
  - prelude form: bare `assign x = …` / `render 'x', …` lines inside a
    {%- liquid … -%} block
Content inside {% comment %}…{% endcomment %} is skipped, so a snippet's
doc-block @example never trips a rule.

Usage:
  python scripts/validate-liquid.py src/sections/<name>/           # every .liquid under a dir
  python scripts/validate-liquid.py src/sections/<name>/x.liquid   # one file
  python scripts/validate-liquid.py --all                          # every .liquid under src/

Exit codes:
  0  no anti-patterns found
  1  at least one anti-pattern found
  2  missing files / bad invocation
"""
import argparse
import re
import sys
from pathlib import Path


# ─── project root (only needed for --all) ────────────────────────────────────
# An explicit file/dir target does NOT need a project root, so the validator
# stays usable in the portable .claude distribution repo (no package.json) and
# is self-testable against an ad-hoc fixture path.
def _find_src_root() -> Path | None:
    p = Path(__file__).resolve()
    for parent in (p, *p.parents):
        if (parent / "src").is_dir():
            return parent
    return None


# ─── tiny logger (mirrors validate-schema.py) ─────────────────────────────────
def _color(code: int, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s

def heading(msg: str) -> None:
    print(f"\n{_color(1, msg)}")

def err_line(msg: str) -> None:
    print(f"  {_color(31, '✗')} {msg}")

def ok(msg: str) -> None:
    print(f"  {_color(32, '✓')} {msg}")


# ─── rule: assign-with-condition ──────────────────────────────────────────────
_STRING_RE = re.compile(r"'[^']*'|\"[^\"]*\"")

def _clean_rhs(rhs: str) -> str:
    """Neutralise everything that could carry an operator-looking character
    WITHOUT being an operator: string literals (`'>'`, `'#fff'`, `'a and b'`)
    and trailing `#` line-comments inside a {% liquid %} block. Strings go
    first so a `#` inside a hex literal is gone before the comment split."""
    s = _STRING_RE.sub(" ", rhs)
    s = s.split("#", 1)[0]
    return s

# Multi-char operators first so `>=` isn't mis-reported as `>`.
_COMPARISON_OPS = ["==", "!=", "<>", ">=", "<=", ">", "<"]
_WORD_OPS = ["contains", "and", "or"]

def _offending_op(rhs: str) -> str | None:
    clean = _clean_rhs(rhs)
    for op in _COMPARISON_OPS:
        if op in clean:
            return op
    for w in _WORD_OPS:
        if re.search(r"\b" + w + r"\b", clean):
            return w
    return None


_LIQUID_BLOCK_RE = re.compile(r"\{%-?\s*liquid\b(.*?)-?%\}", re.DOTALL)
_INNER_ASSIGN_RE = re.compile(r"^[ \t]*assign\s+\w+\s*=\s*(.*)$", re.MULTILINE)
_TAG_ASSIGN_RE   = re.compile(r"\{%-?\s*assign\s+\w+\s*=\s*(.*?)\s*-?%\}")

def _lineno(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1

def scan_text(text: str) -> list[tuple[int, str, str]]:
    """Return sorted unique (lineno, operator, snippet) for each offending assign."""
    hits: set[tuple[int, str, str]] = set()

    # prelude form — bare `assign` lines inside {%- liquid … -%}
    for block in _LIQUID_BLOCK_RE.finditer(text):
        inner, base = block.group(1), block.start(1)
        for a in _INNER_ASSIGN_RE.finditer(inner):
            op = _offending_op(a.group(1))
            if op:
                hits.add((_lineno(text, base + a.start()), op, a.group(0).strip()))

    # tag form — {% assign x = … %}
    for a in _TAG_ASSIGN_RE.finditer(text):
        op = _offending_op(a.group(1))
        if op:
            hits.add((_lineno(text, a.start()), op, a.group(0).strip()))

    return sorted(hits)


# ─── rule: render-arg-expression ──────────────────────────────────────────────
# A render/include/content_for argument is a VALUE slot, not an expression slot.
# Anything operator-shaped there is a compile error, so this rule is a hard fail
# rather than a runtime-behaviour warning like rule 1.

_COMMENT_BLOCK_RE = re.compile(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", re.DOTALL)
_RAW_BLOCK_RE     = re.compile(r"\{%-?\s*raw\s*-?%\}.*?\{%-?\s*endraw\s*-?%\}", re.DOTALL)

_RENDER_TAG_RE    = re.compile(r"\{%-?\s*(?:render|include|content_for)\s(.*?)-?%\}", re.DOTALL)
_RENDER_INNER_RE  = re.compile(r"^[ \t]*(?:render|include)\s+(.*)$", re.MULTILINE)


def _blank_comments(text: str) -> str:
    """Replace {% comment %} / {% raw %} bodies with same-length whitespace so
    line numbers stay truthful while doc-block examples stop matching."""
    def _keep_newlines(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    return _RAW_BLOCK_RE.sub(_keep_newlines, _COMMENT_BLOCK_RE.sub(_keep_newlines, text))


def _split_top_level(text: str) -> list[str]:
    """Split on commas that sit outside quoted strings."""
    out: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return out


def _blank_strings(text: str) -> str:
    """Whitespace-out string CONTENTS (and their quotes) so an operator-looking
    character inside a literal never counts — `addition_class: 'bdrs:sm|w'` is a
    valid xo-css class, not a filter pipe."""
    out: list[str] = []
    quote: str | None = None
    for ch in text:
        if quote:
            out.append(" ")
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


# Arithmetic requires whitespace on BOTH sides so a negative literal
# (`offset: -1`) is not mistaken for subtraction.
_ARG_OFFENDERS = [
    (re.compile(r"\|"),                                     "a filter pipe"),
    (re.compile(r"(==|!=|<>|>=|<=|>|<)"),                    "a comparison"),
    (re.compile(r"(?<![\w.])(?:and|or|contains)(?![\w.])"),  "a logic operator"),
    (re.compile(r"\s[-+*/]\s"),                             "an arithmetic operator"),
]


def _offending_arg(value: str) -> str | None:
    clean = _blank_strings(value)
    for rx, kind in _ARG_OFFENDERS:
        if rx.search(clean):
            return kind
    return None


def _scan_arg_list(arglist: str) -> list[tuple[str, str, str]]:
    """(key, kind, 'key: value') for each offending argument. The first
    comma-separated segment is the snippet name (plus any `for … as …` /
    `with … as …` clause) and is never an argument."""
    found: list[tuple[str, str, str]] = []
    for seg in _split_top_level(arglist)[1:]:
        if ":" not in seg:
            continue
        key, value = seg.split(":", 1)
        kind = _offending_arg(value)
        if kind:
            found.append((key.strip(), kind, " ".join(seg.split())))
    return found


def scan_render_args(text: str) -> list[tuple[int, str, str, str]]:
    """(lineno, key, kind, snippet) for each offending render argument."""
    hits: set[tuple[int, str, str, str]] = set()
    scan = _blank_comments(text)

    # tag form — {% render 'x', … %}
    for tag in _RENDER_TAG_RE.finditer(scan):
        line = _lineno(scan, tag.start())
        for key, kind, seg in _scan_arg_list(tag.group(1)):
            hits.add((line, key, kind, seg))

    # prelude form — bare `render 'x', …` inside {%- liquid … -%}
    for block in _LIQUID_BLOCK_RE.finditer(scan):
        inner, base = block.group(1), block.start(1)
        for call in _RENDER_INNER_RE.finditer(inner):
            line = _lineno(scan, base + call.start())
            for key, kind, seg in _scan_arg_list(call.group(1)):
                hits.add((line, key, kind, seg))

    return sorted(hits)


# ─── driver ───────────────────────────────────────────────────────────────────
def gather_targets(target: str | None, do_all: bool) -> list[Path]:
    if do_all:
        root = _find_src_root()
        if root is None:
            print(_color(31, "✗ --all needs a project root containing src/ — none found above this script"),
                  file=sys.stderr)
            sys.exit(2)
        return sorted((root / "src").rglob("*.liquid"))
    p = Path(target).resolve()
    if p.is_dir():
        return sorted(p.rglob("*.liquid"))
    if p.is_file():
        return [p]
    print(_color(31, f"✗ not found: {p}"), file=sys.stderr)
    sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("target", nargs="?",
                    help="A .liquid file or a directory to scan recursively.")
    ap.add_argument("--all", action="store_true",
                    help="Scan every .liquid under src/.")
    args = ap.parse_args()

    if not args.target and not args.all:
        ap.print_help()
        print(_color(33, "\nNothing to validate — pass a .liquid file, a directory, or --all."))
        sys.exit(2)

    files = gather_targets(args.target, args.all)
    if not files:
        print(_color(33, "No .liquid files found at the given target."))
        sys.exit(0)

    n_assign = 0
    n_render = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            heading(f"─── {f} ───")
            err_line(f"could not read: {e}")
            continue

        assign_hits = scan_text(text)
        render_hits = scan_render_args(text)
        if not assign_hits and not render_hits:
            continue

        try:
            label = f.relative_to(Path.cwd())
        except ValueError:
            label = f
        heading(f"─── {label} ───")

        # One merged, line-ordered report per file — reading a file top-to-bottom
        # beats grouping by rule when the point is "go fix line N".
        merged = [(l, "assign", (op, snip)) for l, op, snip in assign_hits]
        merged += [(l, "render", (key, kind, snip)) for l, key, kind, snip in render_hits]
        for lineno, rule, payload in sorted(merged, key=lambda h: (h[0], h[1])):
            if rule == "assign":
                op, snippet = payload
                n_assign += 1
                err_line(f"L{lineno}: assign with `{op}` — `assign` takes a value, not a condition.")
                print(f"      {snippet}")
                print(f"      fix: branch with if/assign true|false, or put `{op}` straight in {{% if %}}. "
                      f"(liquid gotchas.md #31)")
            else:
                key, kind, snippet = payload
                n_render += 1
                err_line(f"L{lineno}: render argument `{key}:` contains {kind} "
                         f"— an argument takes a bare value. THIS DOES NOT COMPILE.")
                print(f"      {snippet}")
                print(f"      fix: resolve it in the {{% liquid %}} prelude, pass the variable in. "
                      f"(liquid gotchas.md #33)")

    print()
    total = n_assign + n_render
    if total:
        parts = []
        if n_assign:
            parts.append(f"{n_assign} assign-with-condition")
        if n_render:
            parts.append(f"{n_render} render-arg-expression")
        print(_color(31, f"✗ {total} error(s) — {', '.join(parts)} — across {len(files)} file(s) scanned"))
        sys.exit(1)
    print(_color(32, f"✅ No Liquid anti-patterns found ({len(files)} file(s) scanned)"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
