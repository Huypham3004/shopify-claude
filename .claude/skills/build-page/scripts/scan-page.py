#!/usr/bin/env python3
"""
scan-page.py — read a design page, report what a JSON template for it needs.

Mechanical half of the `build-page` skill. Answers three questions the agent
should never answer from memory:

  1. Which sections does this design page stack, in what order?
     (`<xo-include>` INSIDE `<main>` only — header/footer/overlays sit outside
     and are section GROUPS, never template sections.)
  2. Is each one ported to `src/sections/` yet, and under what name?
     (Ports get renamed — `plp-hero` shipped as `collection-page-title` — so a
     direct name match is only the first of three resolution passes.)
  3. What images does each section hard-code, and can they become
     `shopify://shop_images/` references on this design?

Usage
  python3 scan-page.py --list
  python3 scan-page.py home
  python3 scan-page.py home.html --json
  python3 scan-page.py --all

Run from the theme root (the directory holding `src/` and `design/`), or pass
--theme-root.
"""

import argparse
import json
import os
import re
import sys

SECTION_INCLUDE = re.compile(r'<xo-include\s+src="sections/([^"/]+)/([^"]+)"', re.I)
MAIN_OPEN = re.compile(r'<main\b', re.I)
MAIN_CLOSE = re.compile(r'</main>', re.I)
IMG_SRC = re.compile(r'src="(https?://[^"]+)"', re.I)
POSTER = re.compile(r'poster="(https?://[^"]+)"', re.I)


# --------------------------------------------------------------------------
# locating things
# --------------------------------------------------------------------------

def find_design_root(theme_root):
    """`design/src/pages` or one level down (`design/<clone>/src/pages`)."""
    base = os.path.join(theme_root, "design")
    direct = os.path.join(base, "src", "pages")
    if os.path.isdir(direct):
        return os.path.join(base, "src")
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            nested = os.path.join(base, entry, "src", "pages")
            if os.path.isdir(nested):
                return os.path.join(base, entry, "src")
    return None


def list_pages(design_src):
    pages_dir = os.path.join(design_src, "pages")
    return sorted(f for f in os.listdir(pages_dir) if f.endswith(".html"))


# --------------------------------------------------------------------------
# parsing a page
# --------------------------------------------------------------------------

def parse_page(path):
    """Ordered section names inside <main>, plus the ones outside it."""
    html = open(path, encoding="utf-8").read()

    m_open = MAIN_OPEN.search(html)
    m_close = MAIN_CLOSE.search(html)
    if m_open and m_close and m_close.start() > m_open.end():
        inside = html[m_open.end():m_close.start()]
        outside = html[:m_open.start()] + html[m_close.end():]
        bounded = True
    else:
        inside, outside, bounded = html, "", False

    def names(chunk):
        out = []
        for folder, filename in SECTION_INCLUDE.findall(chunk):
            # `header/header.home.html` -> variant "home" of section "header"
            stem = filename[:-5] if filename.endswith(".html") else filename
            variant = stem[len(folder) + 1:] if stem.startswith(folder + ".") else None
            out.append({"design_section": folder, "variant": variant})
        return out

    return {
        "in_main": names(inside),
        "outside_main": names(outside),
        "main_bounded": bounded,
    }


# --------------------------------------------------------------------------
# design section -> ported src/sections/<name>
# --------------------------------------------------------------------------

def load_state_text(theme_root):
    chunks = []
    state = os.path.join(theme_root, ".agent-state")
    if os.path.isdir(state):
        for fn in os.listdir(state):
            if fn.endswith(".md"):
                try:
                    chunks.append(open(os.path.join(state, fn), encoding="utf-8").read())
                except OSError:
                    pass
    return "\n".join(chunks)


def ported_sections(theme_root):
    d = os.path.join(theme_root, "src", "sections")
    if not os.path.isdir(d):
        return set()
    return {n for n in os.listdir(d) if os.path.isdir(os.path.join(d, n))}


def resolve(design_name, ported, state_text):
    """Three passes: exact name, then a rename recorded in .agent-state, else none."""
    if design_name in ported:
        return {"src_section": design_name, "how": "exact name match"}

    # A rename gets written down in either direction, so look for both:
    #   src ← design : "`collection-page-title` ← design `plp-hero`"
    #   design → src : "design `plp-hero` → RESTYLE of existing `collection-page-title`"
    # plus the PLAN row form: "| collection-page-title | `design/.../plp-hero/` |".
    esc = re.escape(design_name)
    patterns = [
        r'`([a-z0-9][a-z0-9-]*)`[^\n]{0,120}?(?:←|<-)[^\n]{0,120}?\b' + esc + r'\b',
        r'\b' + esc + r'\b[^\n]{0,120}?(?:→|->)[^\n]{0,120}?`([a-z0-9][a-z0-9-]*)`',
        r'^\|\s*([a-z0-9][a-z0-9-]*)\s*\|[^\n]*?/' + esc + r'/',
    ]
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, state_text, re.M):
            cand = m.group(1)
            if cand in ported and cand not in hits:
                hits.append(cand)
    if len(hits) == 1:
        return {"src_section": hits[0], "how": "renamed — recorded in .agent-state"}
    if len(hits) > 1:
        return {"src_section": None, "how": "ambiguous", "candidates": hits}
    return {"src_section": None, "how": "not ported"}


# --------------------------------------------------------------------------
# images
# --------------------------------------------------------------------------

def image_mode(design_src):
    """
    Does this design ship the image handoff contract?
      manifest -> a CDN url maps to shopify://shop_images/<basename> and every
                  reference can be verified against the manifest.
      none     -> images are on hosts the store does not own; they cannot be
                  turned into picker references without being uploaded first.
    """
    design_root = os.path.dirname(design_src)
    manifest = os.path.join(design_root, ".shopify", "images.json")
    handoff = os.path.join(design_root, "HANDOFF-IMAGES.md")
    if os.path.isfile(manifest):
        return {"mode": "manifest", "manifest": manifest,
                "handoff": handoff if os.path.isfile(handoff) else None}
    return {"mode": "none", "manifest": None, "handoff": None}


def manifest_filenames(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key in ("filename", "name"):
                val = node.get(key)
                if isinstance(val, str) and "." in val:
                    found.add(val)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return found


def section_images(design_src, design_name, variant):
    stem = design_name + ("." + variant if variant else "")
    path = os.path.join(design_src, "sections", design_name, stem + ".html")
    if not os.path.isfile(path):
        return []
    html = open(path, encoding="utf-8").read()
    urls = []
    for u in IMG_SRC.findall(html) + POSTER.findall(html):
        if u not in urls:
            urls.append(u)
    return urls


def to_picker(url):
    """CDN url -> picker reference: basename, query string dropped."""
    base = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    return "shopify://shop_images/" + base if base else None


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def build_report(theme_root, design_src, page_file):
    path = os.path.join(design_src, "pages", page_file)
    parsed = parse_page(path)
    ported = ported_sections(theme_root)
    state_text = load_state_text(theme_root)
    imode = image_mode(design_src)
    known = manifest_filenames(imode["manifest"]) if imode["manifest"] else set()

    rows = []
    for item in parsed["in_main"]:
        row = dict(item)
        row.update(resolve(item["design_section"], ported, state_text))
        imgs = []
        for url in section_images(design_src, item["design_section"], item["variant"]):
            ref = to_picker(url)
            fn = ref.rsplit("/", 1)[-1] if ref else None
            if imode["mode"] != "manifest":
                status = "unresolvable"
            elif fn in known:
                status = "verified"
            else:
                status = "NOT in manifest"
            imgs.append({"url": url, "picker": ref, "status": status})
        row["images"] = imgs
        rows.append(row)

    return {
        "page": page_file,
        "design_src": design_src,
        "main_bounded": parsed["main_bounded"],
        "groups_outside_main": [i["design_section"] for i in parsed["outside_main"]],
        "image_mode": imode["mode"],
        "sections": rows,
    }


def print_report(rep):
    print("\n─── design page: %s ───" % rep["page"])
    if not rep["main_bounded"]:
        print("  ! no <main> found — every xo-include was treated as a template section.")
        print("    Check the page by hand before trusting the order below.")

    total = len(rep["sections"])
    ok = [r for r in rep["sections"] if r["src_section"]]
    missing = [r for r in rep["sections"] if not r["src_section"]]

    print("  %d section(s) in <main> — %d ported, %d NOT ported" % (total, len(ok), len(missing)))
    print("  image mode: %s" % rep["image_mode"])
    if rep["groups_outside_main"]:
        print("  outside <main> (section groups, excluded): %s"
              % ", ".join(sorted(set(rep["groups_outside_main"]))))

    print("\n  #  design section          ->  src/sections/          how")
    print("  -- ----------------------      ---------------------  ---")
    for i, r in enumerate(rep["sections"], 1):
        label = r["design_section"] + ("." + r["variant"] if r["variant"] else "")
        target = r["src_section"] or "—"
        note = r["how"]
        if r.get("candidates"):
            note += " (" + " | ".join(r["candidates"]) + ")"
        mark = "  " if r["src_section"] else "!!"
        print("  %s %-22s  ->  %-21s  %s" % (mark, label[:22], target[:21], note))

    if missing:
        print("\n  !! NOT PORTED — a template cannot reference these:")
        for r in missing:
            print("     - %s" % r["design_section"])

    flagged = [(r, im) for r in rep["sections"] for im in r["images"]
               if im["status"] != "verified"]
    n_img = sum(len(r["images"]) for r in rep["sections"])
    print("\n  images: %d referenced, %d need a decision" % (n_img, len(flagged)))
    for r, im in flagged:
        print("     - %-20s %s" % (r["design_section"][:20], im["url"][:78]))
        print("       %s" % im["status"])


def main():
    ap = argparse.ArgumentParser(description="Report what a JSON template for a design page needs.")
    ap.add_argument("page", nargs="?", help="design page (e.g. home or home.html)")
    ap.add_argument("--theme-root", default=".")
    ap.add_argument("--list", action="store_true", help="list design pages and exit")
    ap.add_argument("--all", action="store_true", help="scan every design page")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()

    root = os.path.abspath(args.theme_root)
    design_src = find_design_root(root)
    if not design_src:
        sys.exit("No design/src/pages under %s — is this a theme root?" % root)

    pages = list_pages(design_src)

    if args.list:
        print("%d design page(s) in %s:" % (len(pages), os.path.join(design_src, "pages")))
        for p in pages:
            print("  " + p)
        return

    if args.all:
        targets = pages
    elif args.page:
        want = args.page if args.page.endswith(".html") else args.page + ".html"
        if want not in pages:
            sys.exit("No such design page: %s\nTry --list." % want)
        targets = [want]
    else:
        sys.exit("Pass a page name, --all, or --list.")

    reports = [build_report(root, design_src, p) for p in targets]

    if args.json:
        print(json.dumps(reports if args.all else reports[0], indent=2))
        return

    for rep in reports:
        print_report(rep)

    if args.all:
        miss = sorted({r["design_section"] for rep in reports
                       for r in rep["sections"] if not r["src_section"]})
        print("\n═══ across %d page(s): %d distinct unported section(s) ═══" % (len(reports), len(miss)))
        for m in miss:
            print("  - " + m)


if __name__ == "__main__":
    main()
