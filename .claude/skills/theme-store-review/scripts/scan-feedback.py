#!/usr/bin/env python3
"""
Static pre-submit scanner for Shopify Theme Store review feedback.

Runs one check per ledger item in ../references/feedback-ledger.md (IDs must
match) against a theme root that follows the shared base layout:

    <root>/src/{sections,snippets,blocks,groups,pages,layout,locales,styles,scripts}
    <root>/shopify/assets   (build output — run `npm run build` first for SF-ASSET-01)

Verdicts:
  PASS    — the static evidence satisfies the requirement
  FAIL    — the static evidence violates it (fix before resubmitting)
  WARN    — candidates found; a human/agent must confirm each one
  MANUAL  — cannot be decided statically; runtime check needed (hints given)

Usage:
  python3 scan-feedback.py [theme-root] [--only SF-A11Y-03,SF-ASSET-01] [--json] [--max N]

Read-only. Never edits the theme.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

# ----------------------------------------------------------------- helpers

COMMENT_RE = re.compile(r"{%-?\s*comment\s*-?%}.*?{%-?\s*endcomment\s*-?%}", re.S)
SCHEMA_RE = re.compile(r"{%-?\s*schema\s*-?%}.*?{%-?\s*endschema\s*-?%}", re.S)
RAW_RE = re.compile(r"{%-?\s*raw\s*-?%}.*?{%-?\s*endraw\s*-?%}", re.S)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
RENDER_RE = re.compile(r"(?:render|include)\s+['\"]([\w\-/]+)['\"]")


def strip_noise(text: str) -> str:
    """Blank out comments/schema/raw while keeping line numbers stable."""
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    for rx in (COMMENT_RE, SCHEMA_RE, RAW_RE, HTML_COMMENT_RE):
        text = rx.sub(blank, text)
    return text


def liquid_blank(text: str) -> str:
    """Blank {{ }} / {% %} spans (line-preserving) so only literal HTML remains."""
    return re.sub(r"{{.*?}}|{%.*?%}", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


class Theme:
    def __init__(self, root: Path):
        self.root = root
        self.src = root / "src"
        self.build = root / "shopify"
        self._cache: dict[Path, str] = {}
        self.liquid = sorted(self.src.rglob("*.liquid")) if self.src.exists() else []
        self.snippet_by_name: dict[str, Path] = {}
        for p in self.liquid:
            self.snippet_by_name.setdefault(p.stem, p)

    def read(self, p: Path) -> str:
        if p not in self._cache:
            try:
                self._cache[p] = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                self._cache[p] = ""
        return self._cache[p]

    def clean(self, p: Path) -> str:
        return strip_noise(self.read(p))

    def rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.root))
        except ValueError:
            return str(p)

    def files(self, base: Path, *globs: str) -> list[Path]:
        out: list[Path] = []
        if base.exists():
            for g in globs:
                out.extend(base.rglob(g))
        return sorted(set(out))

    def reachable(self, starts: list[Path], depth: int = 4) -> set[Path]:
        """Files reachable through {% render %} / {% include %} from `starts`."""
        seen = set(starts)
        q = deque((s, 0) for s in starts)
        while q:
            p, d = q.popleft()
            if d >= depth:
                continue
            for name in RENDER_RE.findall(self.clean(p)):
                t = self.snippet_by_name.get(name.split("/")[-1])
                if t and t not in seen:
                    seen.add(t)
                    q.append((t, d + 1))
        return seen


RESULTS: list[dict] = []


def report(sid: str, verdict: str, summary: str, evidence: list[str] | None = None):
    RESULTS.append({"id": sid, "verdict": verdict, "summary": summary, "evidence": evidence or []})


def grep(theme: Theme, files: list[Path], rx: re.Pattern, clean: bool = True) -> list[tuple[Path, int, str]]:
    hits = []
    for p in files:
        text = theme.clean(p) if clean else theme.read(p)
        for m in rx.finditer(text):
            ln = line_of(text, m.start())
            snippet = theme.read(p).splitlines()[ln - 1].strip() if theme.read(p) else ""
            hits.append((p, ln, snippet[:140]))
    return hits


def fmt(theme: Theme, hits, limit: int) -> list[str]:
    out = [f"{theme.rel(p)}:{ln}  {s}" for p, ln, s in hits[:limit]]
    if len(hits) > limit:
        out.append(f"… +{len(hits) - limit} more")
    return out


def token_reach(theme: Theme, starts: list[Path], rx: re.Pattern) -> tuple[list[Path], list[Path]]:
    """(files reachable from starts that match rx, all files in src that match rx)."""
    reach = theme.reachable(starts)
    anywhere = [p for p in theme.liquid if rx.search(theme.clean(p))]
    return [p for p in anywhere if p in reach], anywhere


# ----------------------------------------------------------------- checks

def check_filter(t: Theme, n: int):
    loops = [p for p in t.liquid if re.search(r"in\s+filter\.values", t.clean(p))]
    if not loops:
        return report("SF-FILTER-01", "MANUAL", "No `filter.values` loop found — confirm faceted filtering exists at all.")
    ok = [p for p in t.liquid
          if re.search(r"(value|filter_value)\.count\s*(==\s*0|<\s*1)", t.clean(p))
          and re.search(r"disabled", t.clean(p))]
    if ok:
        report("SF-FILTER-01", "PASS", "Zero-count values get a disabled branch (still verify after AJAX + keyboard).",
               [t.rel(p) for p in ok])
    else:
        report("SF-FILTER-01", "FAIL", "Filter value loop has no `count == 0` → disabled branch.",
               [t.rel(p) for p in loops])


def flatten(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            out.update(flatten(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def load_locales(t: Theme) -> tuple[str | None, dict[str, dict]]:
    langs: dict[str, dict] = {}
    default = None
    loc = t.src / "locales"
    built = t.build / "locales"
    # Prefer the BUILT locales: the build merges/namespaces split source files.
    if not (built.exists() and any(built.glob("*.default.json"))) and loc.exists() \
            and any(p.is_dir() for p in loc.iterdir()):
        for d in sorted(p for p in loc.iterdir() if p.is_dir()):
            merged = {}
            for f in sorted(d.glob("*.json")):
                if "schema" in f.name:
                    continue
                try:
                    merged.update(flatten(json.loads(t.read(f))))
                except json.JSONDecodeError:
                    pass
            langs[d.name] = merged
        default = "en" if "en" in langs else next(iter(langs), None)
    else:
        bl = t.build / "locales"
        for f in sorted(bl.glob("*.json")) if bl.exists() else []:
            if ".schema." in f.name:
                continue
            name = f.name.split(".")[0]
            try:
                langs[name] = flatten(json.loads(t.read(f)))
            except json.JSONDecodeError:
                continue
            if ".default." in f.name:
                default = name
    return default, langs


TEXT_NODE_RE = re.compile(r">\s*([A-Za-z][A-Za-z'’,.!?&-]*(?:\s+[A-Za-z'’,.!?&-]+)+)\s*<")
ATTR_TEXT_RE = re.compile(r"\b(aria-label|placeholder|title|alt)=\"([A-Za-z][^\"{}]*)\"")
T_KEY_RE = re.compile(r"['\"]([a-z0-9_]+(?:\.[a-z0-9_]+)+)['\"]\s*\|\s*t\b")


def check_i18n(t: Theme, n: int):
    ev: list[str] = []
    verdict = "PASS"
    default, langs = load_locales(t)
    if default:
        base = langs[default]
        used = set()
        for p in t.liquid:
            used.update(T_KEY_RE.findall(t.clean(p)))
        missing_default = sorted(k for k in used if k not in base and not any(x.startswith(k + ".") for x in base))
        if missing_default:
            verdict = "FAIL"
            ev.append(f"{len(missing_default)} `| t` keys missing from '{default}': " + ", ".join(missing_default[:n]))
        for lang, keys in langs.items():
            if lang == default:
                continue
            same = [k for k, v in base.items() if isinstance(v, str) and len(v) > 12 and keys.get(k) == v]
            if same:
                ev.append(f"locale '{lang}': {len(same)} long values identical to '{default}' (untranslated?), e.g. "
                          + ", ".join(same[:4]))
            miss = [k for k in base if k not in keys]
            if miss:
                verdict = "FAIL"
                ev.append(f"locale '{lang}' lacks {len(miss)} keys, e.g. " + ", ".join(miss[:5]))
    else:
        ev.append("No locales found.")
        verdict = "WARN"

    hard = []
    for p in t.liquid:
        if "/icons/" in str(p) or p.name.startswith("icon-"):
            continue
        text = SCRIPT_STYLE_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), t.clean(p))
        text = re.sub(r"{{.*?}}|{%.*?%}", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
        for m in TEXT_NODE_RE.finditer(text):
            hard.append((p, line_of(text, m.start()), m.group(1).strip()[:80]))
        for m in ATTR_TEXT_RE.finditer(text):
            hard.append((p, line_of(text, m.start()), f'{m.group(1)}="{m.group(2)[:60]}"'))
    # cart surfaces first — that is where the reviewer looked
    hard.sort(key=lambda h: (0 if "cart" in str(h[0]) else 1, str(h[0]), h[1]))
    if hard:
        if verdict == "PASS":
            verdict = "WARN"
        ev.append(f"{len(hard)} possible hardcoded English strings (cart files first):")
        ev.extend(fmt(t, hard, n))
    report("SF-I18N-01", verdict,
           "Locale key parity + hardcoded text. Also check TS-rendered strings and do a runtime locale switch.", ev)


def check_menu(t: Theme, n: int):
    hits = [p for p in t.liquid if "menu" in str(p).lower()
            and len(re.findall(r"for\s+\w+\s+in\s+\w+\.links", t.clean(p))) >= 2]
    if not hits:
        return report("SF-MENU-01", "FAIL", "No menu snippet loops 2+ nested levels of `.links`.")
    report("SF-MENU-01", "MANUAL",
           "Nested levels are rendered. Verify mobile level-2/3 panels at 390px (full viewport, scroll, back/close).",
           [t.rel(p) for p in hits])


def check_newsletter(t: Theme, n: int):
    forms = [p for p in t.liquid if re.search(r"form\s+['\"]customer['\"]", t.clean(p))]
    if not forms:
        return report("SF-NEWSLETTER-01", "FAIL", "No `{% form 'customer' %}` newsletter form found.")
    verdict, ev = "PASS", []
    for p in forms:
        reach = t.reachable([p], 4)
        body = "\n".join(t.clean(x) for x in reach)
        problems = []
        own = re.sub(r"<input[^>]*type=\"hidden\"[^>]*>", "", t.clean(p))
        if not re.search(r"<input|render\s+['\"]field", own) and re.search(r"{{-?\s*content\b|render\s+['\"]group['\"][^%]*content", own):
            ev.append(f"{t.rel(p)}: input injected by caller — verified at the call sites instead")
            continue
        if not re.search(r"type=\"email\"|type:\s*['\"]email['\"]", body):
            problems.append("no type=\"email\"")
            verdict = "FAIL"
        if not re.search(r"\brequired\b", body):  # attr or `required: true` param
            problems.append("no `required`")
            verdict = "FAIL" if verdict == "FAIL" else "WARN"
        if re.search(r"\bnovalidate\b", t.clean(p)):
            problems.append("form has `novalidate` — JS must show its own error")
            verdict = "FAIL" if verdict == "FAIL" else "WARN"
        ev.append(f"{t.rel(p)}: " + ("ok" if not problems else "; ".join(problems)))
    if verdict == "PASS":  # markup is fine, but the reviewer's failure was runtime (JS-submitted form)
        verdict = "MANUAL"
    report("SF-NEWSLETTER-01", verdict, "Markup checked. Runtime: submit `abc@` in every newsletter form "
                                        "(footer, section, popup, password page) and see a visible warning.", ev)


def reach_check(t: Theme, sid: str, starts: list[Path], rx: re.Pattern, label: str, where: str):
    if not starts:
        return report(sid, "MANUAL", f"Could not locate {where} entry files — check {label} by hand.")
    hit, anywhere = token_reach(t, starts, rx)
    if hit:
        report(sid, "PASS", f"{label} reachable from {where}.", [t.rel(p) for p in hit])
    elif anywhere:
        report(sid, "WARN", f"{label} exists but is not reachable from {where} via literal renders "
                            "(dynamic render, or only used elsewhere).", [t.rel(p) for p in anywhere][:10])
    else:
        report(sid, "FAIL", f"{label} not found anywhere in src/.")


def template_starts(t: Theme, page: str) -> list[Path]:
    """Section liquid files referenced by the shipped src/pages/<page>/*.json templates."""
    out: list[Path] = []
    for j in t.files(t.src / "pages" / page, "*.json"):
        try:
            secs = (json.loads(t.read(j)).get("sections") or {}).values()
        except json.JSONDecodeError:
            continue
        for sec in secs:
            f = t.snippet_by_name.get(str(sec.get("type", "")))
            if f and f not in out:
                out.append(f)
    return out


def card_starts(t: Theme) -> list[Path]:
    return [p for p in t.liquid if "product-card" in str(p) and "compare" not in str(p)]


def check_product_tax(t: Theme, n: int):
    starts = template_starts(t, "product")
    reach_check(t, "SF-PRODUCT-01", starts, re.compile(r"cart\.taxes_included"),
                "`cart.taxes_included`", "the product template")


def check_unit_price(t: Theme, n: int):
    reach_check(t, "SF-COLLECTION-01", card_starts(t), re.compile(r"unit_price"),
                "`unit_price`", "product cards")


def check_compare_at(t: Theme, n: int):
    reach_check(t, "SF-COLLECTION-02", card_starts(t), re.compile(r"compare_at_price"),
                "`compare_at_price`", "product cards")


def check_blog(t: Theme, n: int):
    starts = template_starts(t, "blog")
    hit, _ = token_reach(t, starts, re.compile(r"blog\.title|dynamic-title|page_title"))
    ev = [t.rel(p) for p in hit]
    off = []
    for j in t.files(t.src / "pages" / "blog", "*.json"):
        try:
            data = json.loads(t.read(j))
        except json.JSONDecodeError:
            continue
        for sid, sec in (data.get("sections") or {}).items():
            for k, v in (sec.get("settings") or {}).items():
                if "title" in k and v is False:
                    off.append(f"{t.rel(j)}: sections.{sid}.settings.{k} = false")
    if not hit:
        report("SF-BLOG-01", "FAIL", "Nothing outputs `blog.title` from the blog template.", ev)
    elif off:
        report("SF-BLOG-01", "FAIL", "Title output exists but shipped blog template turns it off.", ev + off)
    else:
        report("SF-BLOG-01", "WARN", "`blog.title` is output — confirm no custom heading replaces it by default.", ev)


def check_rte(t: Theme, n: int):
    styles = t.files(t.src, "*.scss", "*.css")
    rx = re.compile(r"\.rte[^{,]*\b(h[1-6]|ul|ol|blockquote)\b")
    owners = sorted({p for p, _, _ in grep(t, styles, rx, clean=False)})
    v = "WARN" if len(owners) > 1 else "MANUAL"
    report("SF-RTE-01", v, "RTE element styles should live in ONE shared place; others are divergence candidates. "
                           "Runtime: same RTE sample in article / product / collection / page / rich-text.",
           [t.rel(p) for p in owners][:n])


def check_minified(t: Theme, n: int):
    assets = [t.build / "assets", t.src / "assets"]
    ev_fail, ev_warn = [], []
    found_any = False
    for d in assets:
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if p.suffix not in (".css", ".js"):
                continue
            found_any = True
            text = t.read(p)
            lines = text.splitlines() or [""]
            longest = max(len(l) for l in lines)
            if p.name.endswith(".min.css"):
                ev_fail.append(f"{t.rel(p)}  (*.min.css is never exempt)")
            elif p.name.endswith(".min.js"):
                ev_warn.append(f"{t.rel(p)}  (*.min.js — only OK if third-party or ES6+; justify it)")
            elif longest > 2000 and len(text) > 5000:
                ev_fail.append(f"{t.rel(p)}  (minified content: longest line {longest} chars)")
    if not found_any:
        return report("SF-ASSET-01", "MANUAL", "No built assets found — run `npm run build` and re-scan.")
    v = "FAIL" if ev_fail else ("WARN" if ev_warn else "PASS")
    report("SF-ASSET-01", v, "Shipped CSS/JS must not be minified (Shopify minifies itself).", ev_fail + ev_warn)


def check_keyboard(t: Theme, n: int):
    rx = re.compile(r"<(a|button|input|select|textarea|summary)\b[^>]*tabindex=\"-1\"", re.S)
    rx2 = re.compile(r"<(div|span|li)\b[^>]*(onclick|@click)[^>]*>", re.S)
    hits = grep(t, t.liquid, rx) + grep(t, t.liquid, rx2)
    report("SF-A11Y-01", "WARN" if hits else "MANUAL",
           "Interactive elements removed from tab order (verify each is intentional, e.g. a duplicated slide). "
           "Runtime: Tab through header dropdowns, drawers, carousels, swatches, filters.", fmt(t, hits, n))


def check_focus(t: Theme, n: int):
    styles = t.files(t.src, "*.scss", "*.css")
    fv = [p for p in styles if ":focus-visible" in t.read(p)]
    kills = grep(t, styles, re.compile(r"outline\s*:\s*(none|0)\s*(;|!|$|})", re.M), clean=False)
    kills = [h for h in kills if ":focus-visible" not in t.read(h[0])]
    if not fv:
        report("SF-A11Y-02", "FAIL", "No `:focus-visible` rule anywhere in styles.", fmt(t, kills, n))
    elif kills:
        report("SF-A11Y-02", "WARN", f"`:focus-visible` used in {len(fv)} files, but these remove outlines "
                                     "without a focus-visible replacement in the same file:", fmt(t, kills, n))
    else:
        report("SF-A11Y-02", "MANUAL", "Focus rules present — verify visually by tabbing links.", [t.rel(p) for p in fv][:5])


def check_img_alt(t: Theme, n: int):
    hits = []
    for p in t.liquid:
        text = liquid_blank(t.clean(p))
        for m in re.finditer(r"<img\b[^>]*>", text, re.S):
            if not re.search(r"\balt\s*=", m.group(0)):
                hits.append((p, line_of(text, m.start()), m.group(0)[:100].replace("\n", " ")))
        raw = t.clean(p)
        for m in re.finditer(r"image_tag[^%}]*\balt:\s*(''|\"\")", raw):
            if "product" in str(p):
                hits.append((p, line_of(text, m.start()), "image_tag with empty alt on product imagery"))
    report("SF-A11Y-03", "FAIL" if hits else "PASS", "Every <img> needs alt; product images use image.alt.",
           fmt(t, hits, n))


def check_labels(t: Theme, n: int):
    hits = []
    scope = [p for p in t.liquid if any(s in str(p) for s in ("/snippets/", "/blocks/", "/pages/"))]
    for p in scope:
        text = t.clean(p)
        ids = set(re.findall(r"\bid=\"([^\"]+)\"", text))
        for m in re.finditer(r"<(input|select|textarea)\b[^>]*>", text, re.S):
            tag = m.group(0)
            if re.search(r"type=\"(hidden|submit)\"", tag):
                continue
            idm = re.search(r"\bid=\"([^\"]*)\"", tag)
            if idm and "{{" not in idm.group(1):
                hits.append((p, line_of(text, m.start()), f'literal id="{idm.group(1)}" — duplicates if rendered twice'))
            elif not idm and "aria-label" not in tag:
                hits.append((p, line_of(text, m.start()), f"<{m.group(1)}> without id or aria-label"))
        for m in re.finditer(r"<label\b[^>]*\bfor=\"([^\"{}]+)\"", text):
            if m.group(1) not in ids:
                hits.append((p, line_of(text, m.start()), f'label for="{m.group(1)}" has no matching id in file'))
    report("SF-A11Y-04", "WARN" if hits else "PASS",
           "Inputs need unique ids (suffix with section/block/loop id) and matching <label for>.", fmt(t, hits, n))


def check_section_limit(t: Theme, n: int):
    groups = [t.src / "groups" / "headers", t.src / "groups" / "footers"]
    ev, verdict, variants = [], "PASS", defaultdict(list)
    for g in groups:
        if not g.exists():
            continue
        for d in sorted(x for x in g.iterdir() if x.is_dir()):
            kind = "header" if d.name.startswith("header") else "footer" if d.name.startswith("footer") else None
            if not kind:
                continue
            schema = d / "schema.js"
            if not schema.exists():
                continue
            variants[kind].append(d.name)
            if not re.search(r"\blimit\s*:\s*1\b", t.read(schema)):
                verdict = "FAIL"
                ev.append(f"{t.rel(schema)}: missing `limit: 1`")
    for kind, names in variants.items():
        if len(names) > 1:
            if verdict == "PASS":
                verdict = "WARN"
            ev.append(f"{len(names)} {kind} section types ({', '.join(names)}): each limit:1 still lets two "
                      "DIFFERENT types coexist — verify in editor.")
    if not variants:
        return report("SF-SECTION-01", "MANUAL", "No header/footer group sections found.")
    report("SF-SECTION-01", verdict, "Header/footer must be single-instance.", ev)


def check_list_align(t: Theme, n: int):
    styles = t.files(t.src, "*.scss", "*.css")
    hits = grep(t, styles, re.compile(r"list-style-position\s*:\s*inside"), clean=False)
    if hits:
        report("SF-RTE-02", "MANUAL", "`list-style-position: inside` present — verify center/right aligned lists at runtime.",
               fmt(t, hits, n))
    else:
        report("SF-RTE-02", "FAIL", "No `list-style-position: inside` rule — centered/right lists will detach markers.")


def inline_richtext_ids(t: Theme, schema: Path) -> set[str]:
    text = t.read(schema)
    ids = set()
    for m in re.finditer(r"inline_richtext", text):
        window = text[max(0, m.start() - 300): m.start() + 300]
        ids.update(re.findall(r"\bid\s*:\s*['\"]([\w-]+)['\"]", window))
    return ids


def check_inline_links(t: Theme, n: int):
    hits = []
    flexy = re.compile(r"(d:(flex|inline-flex|grid)|\bflex\b|\bgrid\b|marquee)", re.I)
    for schema in t.files(t.src, "schema.js"):
        ids = inline_richtext_ids(t, schema)
        if not ids:
            continue
        for lq in schema.parent.glob("*.liquid"):
            text = t.clean(lq)
            for sid in ids:
                for m in re.finditer(r"{{-?\s*(section|block)\.settings\." + re.escape(sid) + r"\b", text):
                    before = text[:m.start()]
                    open_tag = re.findall(r"<([a-z][\w-]*)\b([^<>]*)>\s*$", before[-400:], re.S)
                    if open_tag and flexy.search(open_tag[-1][1]) or (open_tag and "marquee" in open_tag[-1][0]):
                        hits.append((lq, line_of(text, m.start()), f"`{sid}` is a direct child of <{open_tag[-1][0]}> "
                                                                    "flex/grid/marquee container"))
    report("SF-RTE-03", "WARN" if hits else "MANUAL",
           "inline_richtext directly inside flex/grid/marquee splits/reorders when a link is added — wrap it in a span. "
           "Runtime: add a link mid-text in marquee, cards, headings.", fmt(t, hits, n))


DEMO_URL_RE = re.compile(
    r"['\"](/(?:products|pages)/[\w-]+|/blogs/(?!news['\"/])[\w-]+|/collections/(?!all['\"/])[\w-]+|"
    r"shopify://(?:products|collections|blogs|pages)/[\w-]+)")


def check_demo_handles(t: Theme, n: int):
    fails, warns = [], []
    for schema in t.files(t.src, "schema.js", "*.js"):
        if "node_modules" in str(schema):
            continue
        text = t.read(schema)
        for m in DEMO_URL_RE.finditer(text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            if re.search(r"\bdefault\s*:", text[line_start:m.start()]):
                fails.append((schema, line_of(text, m.start()), m.group(1)))
    for j in t.files(t.src, "*.json"):
        if "/locales/" in str(j):
            continue
        text = t.read(j)
        for m in DEMO_URL_RE.finditer(text):
            if m.group(1).startswith("/") and "collections/all" not in m.group(1):
                warns.append((j, line_of(text, m.start()), m.group(1)))
    v = "FAIL" if fails else ("WARN" if warns else "PASS")
    ev = (["schema defaults (must be blank):"] + fmt(t, fails, n) if fails else []) + \
         (["shipped template/group JSON (hard-coded store paths):"] + fmt(t, warns, n) if warns else [])
    report("SF-SETTINGS-01", v, "No store-specific handles in setting defaults.", ev)


def check_stock(t: Theme, n: int):
    files = t.liquid + t.files(t.src, "*.ts", "*.js")
    hits = []
    for p in files:
        text = t.read(p)
        if re.search(r"inventory_quantity|inventoryQuantity", text) and not re.search(
                r"inventory_management|inventoryManagement|inventory_policy|inventoryPolicy", text):
            m = re.search(r"inventory_quantity|inventoryQuantity", text)
            hits.append((p, line_of(text, m.start()), "uses inventory quantity without inventory_management/policy"))
    report("SF-STOCK-01", "WARN" if hits else "PASS",
           "Untracked / continue-selling variants must not read 'Out of stock'.", fmt(t, hits, n))


def manual(sid: str, summary: str, hint_rx: str | None = None):
    def run(t: Theme, n: int):
        ev = []
        if hint_rx:
            ev = fmt(t, grep(t, t.liquid + t.files(t.src, "*.ts"), re.compile(hint_rx)), min(n, 8))
        report(sid, "MANUAL", summary, ev)
    return run


CHECKS = [
    ("SF-FILTER-01", check_filter),
    ("SF-I18N-01", check_i18n),
    ("SF-MENU-01", check_menu),
    ("SF-NEWSLETTER-01", check_newsletter),
    ("SF-PRODUCT-01", check_product_tax),
    ("SF-COLLECTION-01", check_unit_price),
    ("SF-COLLECTION-02", check_compare_at),
    ("SF-BLOG-01", check_blog),
    ("SF-RTE-01", check_rte),
    ("SF-ASSET-01", check_minified),
    ("SF-A11Y-01", check_keyboard),
    ("SF-A11Y-02", check_focus),
    ("SF-A11Y-03", check_img_alt),
    ("SF-A11Y-04", check_labels),
    ("SF-A11Y-05", manual("SF-A11Y-05", "Measure pointer targets ≥24×24 at runtime (dots, swatches, ×, ±).")),
    ("SF-A11Y-06", manual("SF-A11Y-06", "Render h1–h6 side by side in every preset; each level must differ.")),
    ("SF-SECTION-01", check_section_limit),
    ("SF-RTE-02", check_list_align),
    ("SF-RTE-03", check_inline_links),
    ("SF-SETTINGS-01", check_demo_handles),
    ("SF-LINK-01", manual("SF-LINK-01", "Empty filter/search state: 'remove all' / clear links need link or button styling.",
                          r"remove_all|clear_all|filters\.clear")),
    ("SF-STOCK-01", check_stock),
    ("SF-CONTRAST-01", manual("SF-CONTRAST-01", "Modal/drawer close × contrast ≥3:1 in every color scheme.")),
    ("SF-VARIANT-01", manual("SF-VARIANT-01", "Swatch availability must use the OTHER selected options; click through sparse combos.",
                             r"option_value\.available|\.available\b.*swatch|strikethrough|xo-unavailable")),
    ("SF-LICENSE-01", manual("SF-LICENSE-01", "Confirm licenses for bundled libraries, fonts and demo images.")),
]

ORDER = {"FAIL": 0, "WARN": 1, "MANUAL": 2, "PASS": 3}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="theme root (contains src/)")
    ap.add_argument("--only", default="", help="comma-separated ledger IDs")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max", type=int, default=12, help="max evidence lines per item")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if not (root / "src").exists():
        print(f"error: {root}/src not found — pass the theme root", file=sys.stderr)
        return 2
    t = Theme(root)
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    for sid, fn in CHECKS:
        if only and sid not in only:
            continue
        try:
            fn(t, a.max)
        except Exception as e:  # a broken heuristic must not hide the other results
            report(sid, "MANUAL", f"scanner error: {e!r} — check by hand")

    if a.json:
        print(json.dumps({"root": str(root), "results": RESULTS}, indent=2, ensure_ascii=False))
        return 0

    counts = defaultdict(int)
    for r in RESULTS:
        counts[r["verdict"]] += 1
    print(f"# Theme Store pre-submit scan — {root.name}\n")
    print(" · ".join(f"{k} {counts[k]}" for k in ("FAIL", "WARN", "MANUAL", "PASS")) + "\n")
    print("| ID | Verdict | Summary |\n|---|---|---|")
    for r in sorted(RESULTS, key=lambda r: (ORDER[r["verdict"]], r["id"])):
        print(f"| {r['id']} | {r['verdict']} | {r['summary']} |")
    print()
    for r in sorted(RESULTS, key=lambda r: (ORDER[r["verdict"]], r["id"])):
        if r["evidence"]:
            print(f"## {r['id']} — {r['verdict']}")
            for e in r["evidence"]:
                print(f"- {e}")
            print()
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
