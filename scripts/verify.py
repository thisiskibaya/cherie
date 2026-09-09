#!/usr/bin/env python3
"""
verify.py — sanity check for the repaired static site (cherie/).

Run: python scripts/verify.py   (from the cherie/ project root)

Checks every HTML page for:
  1. references (src/href/srcset/data-src/poster, CSS url()) to files that
     don't exist in the deploy tree,
  2. import-map / modulepreload entries still pointing at index.min.js,
  3. leftover inline wp-emoji module blocks or wp-emoji-settings scripts,
  4. leftover query-page pagination / un-hashed WP asset URLs.

Exits non-zero when problems are found.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_PAGE_LINKS = (
    # intentional: retargeted / removed static pages
    re.compile(r"(?:\.\./)*my-account/index\.html"),
    re.compile(r"(?:\.\./)*cart/index\.html"),
    re.compile(r"(?:\.\./)*author/admin/index\.html"),
    re.compile(r"/index[0-9a-f]{4}\.html"),
    re.compile(r"/wp-json/"),
    re.compile(r"/wp-admin/"),
    re.compile(r"/feed"),
    # placeholders / fragments that are not real lookups
    re.compile(r"^#"),
    re.compile(r"^javascript:"),
)

REF_RE = re.compile(
    r"""(?:src|href|data-src|poster)\s*=\s*"([^"]+)"|srcset="([^"]+)"|url\(\s*["']?([^"')]+)["']?\s*\)""",
    re.I,
)


def is_external(url):
    return bool(re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|data:|blob:)", url, re.I))


def resolve(page_dir, url):
    url = url.split("#", 1)[0]
    if url.startswith("//"):
        url = "/" + url.lstrip("/")
    if url.startswith("/"):
        return os.path.normpath(os.path.join(ROOT, url.lstrip("/")))
    return os.path.normpath(os.path.join(page_dir, url))


def main():
    problems = []

    for page in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        page_dir = os.path.dirname(page)
        rel_page = os.path.relpath(page, ROOT)
        with open(page, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        if "wp-emoji-settings" in text or "sourceURL=/wp-includes/js/wp-emoji-loader" in text:
            problems.append("%s: inline wp-emoji module/settings still present" % rel_page)
        if "query-page" in text:
            problems.append("%s: query-page pagination link still present" % rel_page)
        if "/wp-includes/js/dist/script-modules/interactivity/index.min.js?" in text:
            problems.append("%s: import map still points at index.min.js" % rel_page)
        if re.search(r"(?:src|href)=\"[^\"]*/(?:jquery\.min|hooks\.min|i18n\.min|customer-account|view)\.js\?", text):
            problems.append("%s: un-hashed WP asset URL present" % rel_page)

        for m in REF_RE.finditer(text):
            group = m.group(1) if m.group(1) is not None else (m.group(2) if m.group(2) is not None else m.group(3))
            if group is None:
                continue
            refs = [part.strip().split(" ")[0] for part in group.split(",")] if m.group(2) is not None else [group]
            for ref in refs:
                if not ref or is_external(ref):
                    continue
                url = ref.split("?", 1)[0]
                if any(p.search(url) for p in SKIP_PAGE_LINKS):
                    continue
                target = resolve(page_dir, url)
                if not os.path.exists(target):
                    problems.append("%s: missing ref %s" % (rel_page, ref))

    if problems:
        print("verify.py: %d problem(s) found" % len(problems))
        for p in problems[:200]:
            print("  - " + p)
        sys.exit(1)
    print("verify.py: OK — no missing references or leftover issues across %d pages"
          % len(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)))


if __name__ == "__main__":
    main()