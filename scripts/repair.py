#!/usr/bin/env python3
"""
repair.py — post-scrape repair for the static Vercel deploy (cherie/).

Run from the cherie/ project root (build.sh calls it too):
    python scripts/repair.py "<path to HTTrack mirror>"

Fixes the classes of failures seen on the deployed site:

  1. Restores static assets referenced by the HTML that exist in the fresh
     HTTrack mirror but were pruned during the build (jQuery, WooCommerce /
     Contact Form 7 plugin assets, wp-includes dist + block CSS, comment-reply,
     favicon PNGs, ...).
  2. Points the @wordpress/interactivity import map / modulepreload at the
     shipped interactivity/index.min132d.js (was index.min.js -> 404 -> HTML
     -> "Failed to load module script" / "Unexpected token '<'").
  3. Removes the inline wp-emoji module scripts and their settings block
     (they crash with "Cannot read properties of null (reading
     'textContent')" once the settings element is stripped).
  4. Fixes un-hashed script/CSS URLs left on team/ and testimonials/ pages.
  5. Retargets links to pages that were removed for the static build
     (my-account, cart, author/admin, query-page pagination, comment-reply).
  6. Repairs <img> src / srcset entries that point at files the mirror never
     had by substituting an existing variant of the same image and pruning
     dead srcset candidates.

Idempotent — safe to run repeatedly.
"""
import glob
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "bakery.local")
if not os.path.isabs(MIRROR):
    MIRROR = os.path.abspath(os.path.join(ROOT, MIRROR))


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def resolve(page_dir, url):
    """Resolve a URL (root- or page-relative) to an absolute filesystem path."""
    url = url.split("#", 1)[0]
    if url.startswith("//"):  # protocol-relative -> root-relative
        url = "/" + url.lstrip("/")
    if url.startswith("/"):
        return os.path.normpath(os.path.join(ROOT, url.lstrip("/")))
    return os.path.normpath(os.path.join(page_dir, url))


def posix(p):
    return p.replace("\\", "/")


def is_external(url):
    return bool(re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|data:|blob:)", url, re.I))


def skipped_path(path):
    """Refs that point at intentionally-removed or dynamic destinations."""
    return any(
        seg in path
        for seg in ("/my-account/", "/cart/", "/author/", "/wp-json/", "/wp-admin/")
    ) or "/feed" in path or re.search(r"/index[0-9a-f]{4}\.html", path)


# ---------------------------------------------------------------------------
# 1. Restore missing referenced assets from the mirror
# ---------------------------------------------------------------------------
REF_RE = re.compile(
    r"""(?:src|href|data-src|poster)\s*=\s*"([^"]+)"|srcset="([^"]+)"|url\(\s*["']?([^"')]+)["']?\s*\)""",
    re.I,
)


def iter_references(text):
    for m in REF_RE.finditer(text):
        group = m.group(1) if m.group(1) is not None else (m.group(2) if m.group(2) is not None else m.group(3))
        if group is None:
            continue
        if m.group(2) is not None:  # srcset — split on commas
            for part in group.split(","):
                part = part.strip().split(" ")[0]
                if part:
                    yield part
        else:
            yield group


def restore_references():
    restored, scanned = 0, 0
    for page in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        page_dir = os.path.dirname(page)
        try:
            with open(page, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue
        for ref in iter_references(text):
            scanned += 1
            url = ref.split("?", 1)[0]
            if not url or is_external(url) or skipped_path(url):
                continue
            target = resolve(page_dir, url)
            if os.path.exists(target):
                continue
            rel = posix(os.path.relpath(target, ROOT))
            src = os.path.join(MIRROR, rel)
            if os.path.exists(src):
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(src, target)
                restored += 1
    return restored, scanned


def restore_tree(rel_dir):
    """Copy any missing files under MIRROR/rel_dir into ROOT/rel_dir."""
    src_root = os.path.join(MIRROR, rel_dir)
    if not os.path.isdir(src_root):
        return 0
    count = 0
    for root_dir, _dirs, files in os.walk(src_root):
        for fn in files:
            src = os.path.join(root_dir, fn)
            rel = os.path.relpath(src, MIRROR)
            dst = os.path.join(ROOT, rel)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                count += 1
    return count


# ---------------------------------------------------------------------------
# 2 & 4. Import map + un-hashed asset URL fixes
# ---------------------------------------------------------------------------
UNHASHED = {
    # (path fragment present in the URL) -> replacement basename
    "wp-includes/js/jquery/jquery.min.js": "jquery.minf43b.js",
    "wp-includes/js/jquery/jquery-migrate.min.js": "jquery-migrate.min5589.js",
    "wp-includes/js/dist/hooks.min.js": "hooks.min394d.js",
    "wp-includes/js/dist/i18n.min.js": "i18n.mineca5.js",
    "woocommerce/assets/client/blocks/woocommerce/customer-account.js": "customer-account85c0.js",
    "woocommerce/assets/js/frontend/add-to-cart.min.js": "add-to-cart.min5ae7.js",
    "woocommerce/assets/js/frontend/woocommerce.min.js": "woocommerce.min5ae7.js",
    "woocommerce/assets/js/frontend/order-attribution.min.js": "order-attribution.min5ae7.js",
    "woocommerce/assets/js/sourcebuster/sourcebuster.min.js": "sourcebuster.min5ae7.js",
    "woocommerce/assets/js/jquery-blockui/jquery.blockUI.min.js": "jquery.blockUI.mine7c9.js",
    "woocommerce/assets/js/js-cookie/js.cookie.min.js": "js.cookie.min6f96.js",
    "blocks/mobile-menu/view.js": "view3958.js",
    "wp-includes/blocks/navigation/style.min.css": "style.min42a0.css",
    "contact-form-7/includes/swv/js/index.js": "index36b6.js",
    "contact-form-7/includes/js/index.js": "index36b6.js",
    "themes/bakly-block/assets/vendor/swiper-bundle.min.js": "swiper-bundle.minb6eb.js",
    "themes/bakly-block/assets/js/interactions.js": "interactionsa024.js",
}


def fix_asset_url(value):
    """Replace an un-hashed WP asset basename with its versioned filename."""
    path = value.split("?", 1)[0]
    for fragment, hashed in UNHASHED.items():
        if path.endswith(fragment):
            head = path[: path.rfind("/") + 1]
            suffix = "?" + value.split("?", 1)[1] if "?" in value else ""
            return head + hashed + suffix
    return value


def fix_importmap(text):
    return text.replace(
        "/wp-includes/js/dist/script-modules/interactivity/index.min.js?ver=",
        "/wp-includes/js/dist/script-modules/interactivity/index.min132d.js?ver=",
    )


def fix_asset_attributes(text, depth):
    """Apply fix_asset_url + link retargeting to every src/href/data-src value.

    depth: number of directory levels between the HTML page and ROOT (0 for the
    home page, 1 for about/, 2 for product/x/, ...). Used to self-heal
    previously-mangled relative shop links.
    """

    def rewrite(value):
        # Never rewrite true absolute URLs (https://…, mailto:, data:, …)
        if re.match(r"^(?:https?|ftp|mailto|tel|data|blob|javascript|about):", value, re.I):
            return value
        v = fix_asset_url(value)
        v = re.sub(r"((?:\.\./)*)my-account/index\.html", r"\1shop/index.html", v)
        v = re.sub(r"((?:\.\./)*)cart/index\.html", r"\1shop/index.html", v)
        v = v.replace("//my-account/", "/shop/index.html").replace("/my-account/", "/shop/index.html")
        v = v.replace("//cart/", "/shop/index.html").replace("/cart/", "/shop/index.html")
        v = re.sub(r"(?:\.\./)*author/admin/index\.html", "#", v)
        v = re.sub(r"index[0-9a-f]{4}\.html\?replytocom=\d+", "#", v)
        # favicon size the mirror never crawled -> existing 180x180 icon
        v = re.sub(r"cropped-favicon-32x32-1-270x270\.png", "cropped-favicon-32x32-1-180x180.png", v)
        # self-heal: on non-root pages a bare shop/index.html is a mangled
        # relative link (the ../ prefix was lost) — restore the correct depth
        if depth > 0 and re.match(r"^shop/index\.html(?:\?.*)?$", v):
            v = "../" * depth + v
        return v

    def sub(m):
        prefix, quote, val = m.group(1), m.group(2), m.group(3)
        return prefix + quote + rewrite(val) + quote

    return re.sub(r"((?:src|href|data-src)=)([\"'])(.*?)\2", sub, text, flags=re.S)


def remove_pagination_links(text):
    """Drop anchors pointing at orphaned indexXXXX.html?query-page= artifacts."""
    return re.sub(
        r'<a\b[^>]*href="index[0-9a-f]{4}\.html\?query-page=[^"]*"[^>]*>\s*.*?\s*</a>',
        "",
        text,
        flags=re.S,
    )


def remove_emoji_blocks(text):
    text = re.sub(
        r'<script\s+id="wp-emoji-settings"[^>]*>.*?</script>', "", text, flags=re.S
    )
    text = re.sub(
        r'<script\s+type="module">.*?sourceURL=/wp-includes/js/wp-emoji-loader\.min\.js.*?</script>',
        "",
        text,
        flags=re.S,
    )
    return text


# ---------------------------------------------------------------------------
# 6. Image repair
# ---------------------------------------------------------------------------
ATTR_RE = re.compile(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("([^"]*)"|'([^']*)')""")


def variant_candidates(path):
    """Existing same-image variants in path's directory."""
    d, base = os.path.dirname(path), os.path.basename(path)
    m = re.match(r"^(.*?)(?:-\d{2,4}x\d{2,4}|-scaled)?(\.[A-Za-z0-9]+)$", base)
    if not m:
        return []
    slug, ext = m.group(1), m.group(2)
    if not os.path.isdir(d):
        return []
    out = []
    for fn in os.listdir(d):
        if fn == base:
            continue
        if fn.startswith(slug) and fn.endswith(ext):
            out.append(fn)
    return out


def best_variant(path):
    cands = variant_candidates(path)
    if not cands:
        # Loose fallback: the referenced filename may have a subtly different
        # hash token than the crawled file (e.g. …-vdx5hXFk-unsplash.jpg vs
        # …-vdx5hPQhXFk-unsplash-scaled.jpg). Drop the trailing name segments
        # until matching files are found.
        d, base = os.path.dirname(path), os.path.basename(path)
        m = re.match(r"^(.*?)(?:-\d{2,4}x\d{2,4}|-scaled)?(\.[A-Za-z0-9]+)$", base)
        if m and os.path.isdir(d):
            stem = re.sub(r"-unsplash$", "", m.group(1))
            parts = [p for p in stem.split("-") if p]
            for i in range(len(parts) - 1, 0, -1):
                prefix = "-".join(parts[:i]).lower()
                cands = [f for f in os.listdir(d)
                         if f.lower().startswith(prefix + "-") or f.lower().startswith(prefix + ".")]
                if cands:
                    break
    if not cands:
        return None

    def score(fn):
        s = 0
        if "-scaled" in fn:
            s += 10000
        m2 = re.search(r"-(\d{2,4})x(\d{2,4})\.", fn)
        if m2:
            s += int(m2.group(1)) * int(m2.group(2))
        else:
            s += 5000
        return s

    return max(cands, key=score)


def find_variant_url(url, page_dir):
    """URL to an existing variant of the same image, in the same relative
    style (root-relative vs page-relative) as the input URL."""
    target = resolve(page_dir, url)
    best = best_variant(target)
    if not best:
        return None
    new_path = os.path.join(os.path.dirname(target), best)
    if url.startswith("/"):
        return "/" + posix(os.path.relpath(new_path, ROOT))
    return posix(os.path.relpath(new_path, page_dir))


def srcset_existing_entries(entries, page_dir):
    kept = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        url = entry.split(" ")[0].split("?", 1)[0]
        if url and os.path.exists(resolve(page_dir, url)):
            kept.append(entry)
    return kept


def fix_image_tag(tag, page_dir):
    """Repair a single <img ...> or <source ...> tag."""
    attrs = {}
    for name, _q, double, single in ATTR_RE.findall(tag):
        if name.lower() not in attrs:
            attrs[name.lower()] = double if double is not None else single

    if tag.lower().startswith("<img"):
        src = attrs.get("src")
        if src and not os.path.exists(resolve(page_dir, src.split("?", 1)[0])):
            repl = find_variant_url(src, page_dir)
            if repl:
                tag = re.sub(
                    r'src=("[^"]*"|\'[^\']*\')',
                    lambda m: 'src="' + repl + '"',
                    tag,
                    count=1,
                )
        dsrc = attrs.get("data-src")
        if dsrc and not os.path.exists(resolve(page_dir, dsrc.split("?", 1)[0])):
            repl = find_variant_url(dsrc, page_dir)
            if repl:
                tag = re.sub(
                    r'data-src=("[^"]*"|\'[^\']*\')',
                    lambda m: 'data-src="' + repl + '"',
                    tag,
                    count=1,
                )

    # WooCommerce product gallery: thumbnails live in data-thumb /
    # data-thumb-srcset attributes on <div>s
    if re.search(r"\sdata-thumb\s*=", tag, re.I):
        th = attrs.get("data-thumb")
        if th and not os.path.exists(resolve(page_dir, th.split("?", 1)[0])):
            repl = find_variant_url(th, page_dir)
            if repl:
                tag = re.sub(
                    r'data-thumb=("[^"]*"|\'[^\']*\')',
                    lambda m: 'data-thumb="' + repl + '"',
                    tag,
                    count=1,
                )
        mth = re.search(r'data-thumb-srcset=("[^"]*"|\'[^\']*\')', tag)
        if mth:
            sep = mth.group(1)[0]
            raw = mth.group(1)[1:-1]
            entries = srcset_existing_entries([e for e in raw.split(",") if e.strip()], page_dir)
            if entries:
                new_attr = "data-thumb-srcset=" + sep + ",".join(entries) + sep
                tag = tag.replace(mth.group(0), new_attr, 1)
            else:
                tag = re.sub(r'\s+data-thumb-srcset=("[^"]*"|\'[^\']*\')', "", tag, count=1)

    m = re.search(r'srcset=("[^"]*"|\'[^\']*\')', tag)
    if m:
        sep = m.group(1)[0]
        raw = m.group(1)[1:-1]
        entries = srcset_existing_entries([e for e in raw.split(",") if e.strip()], page_dir)
        if entries:
            new_attr = "srcset=" + sep + ",".join(entries) + sep
            tag = tag.replace(m.group(0), new_attr, 1)
        else:
            tag = re.sub(r'\s+srcset=("[^"]*"|\'[^\']*\')', "", tag, count=1)
    return tag


def repair_images(text, page_dir):
    return re.sub(
        r"<img\b[^>]*>|<source\b[^>]*>|<div\b[^>]*data-thumb[^>]*>",
        lambda m: fix_image_tag(m.group(0), page_dir),
        text,
    )


def repair_css_urls(text, page_dir):
    """Substitute missing background-image:url(...) refs with an existing
    variant of the same image (used by style attributes like the mobile
    drawer background)."""

    def fix(m):
        quote, url = m.group(1), m.group(2)
        if not url or is_external(url) or re.match(r"^(?:data:|#|javascript:)", url, re.I):
            return m.group(0)
        if os.path.exists(resolve(page_dir, url.split("?", 1)[0])):
            return m.group(0)
        repl = find_variant_url(url, page_dir)
        if repl:
            return "url(" + quote + repl + quote + ")"
        return m.group(0)

    return re.sub(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", fix, text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def process_html(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    original = content
    page_dir = os.path.dirname(path)
    rel = os.path.relpath(page_dir, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1

    content = remove_pagination_links(content)
    content = remove_emoji_blocks(content)
    content = fix_importmap(content)
    content = fix_asset_attributes(content, depth)
    content = repair_images(content, page_dir)
    content = repair_css_urls(content, page_dir)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    log("repair.py")
    log("  ROOT   : %s" % ROOT)
    log("  MIRROR : %s" % MIRROR)
    if not os.path.isdir(MIRROR):
        log("  ERROR: mirror path does not exist: %s" % MIRROR)
        sys.exit(1)

    # 1. restore missing referenced assets (whole-tree only for plugin/upload
    #    sibling dirs; wp-includes/* is covered by the reference sweep so
    #    unreferenced files like zxcvbn-async are not resurrected)
    n = restore_tree(os.path.join("wp-content", "plugins"))
    log("  restored %d plugin files from mirror" % n)
    n = restore_tree(os.path.join("wp-content", "uploads", "2026", "09"))
    log("  restored %d uploads/2026/09 files from mirror" % n)
    restored, scanned = restore_references()
    log("  reference sweep: scanned %d refs, restored %d files" % (scanned, restored))

    # 2-6. per-page fixes
    pages = glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
    changed = 0
    for page in pages:
        if process_html(page):
            changed += 1
    log("  repaired %d of %d HTML pages" % (changed, len(pages)))

    log("repair complete")


if __name__ == "__main__":
    main()
