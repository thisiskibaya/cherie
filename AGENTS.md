# AGENTS.md — Post-processing HTTrack scrapes of WordPress sites

This directory is an **HTTrack Website Copier** mirror of a WordPress + WooCommerce
site ("Sherrie Bakery", Nairobi). The live staging target for this instance is
`https://sherrie.page.gd`. The notes below are generic enough to reuse for any
similar scrape, with `bakery.local` = the crawl host and `<STAGING>` = the real
destination domain.

## Layout of an HTTrack scrape

```
<Root>/
├── index.html            # HTTrack wrapper: redirects to bakery.local/index.html (DISCARD)
├── backblue.gif          # HTTrack wrapper styling (DISCARD)
├── fade.gif              # HTTrack wrapper styling (DISCARD)
├── cookies.txt           # HTTrack session cookies (DISCARD, not served)
├── hts-log.txt           # HTTrack crawl log (DISCARD)
├── hts-cache/            # HTTrack cache (DISCARD)
├── *.whtt                # HTTrack project file (DISCARD)
└── bakery.local/         # THE REAL SITE — this is what you deploy
```

**Deploy rule:** upload the *contents* of `bakery.local/` to the domain root.
Do **not** upload the wrapper files. The real entry page becomes `bakery.local/index.html`
→ `https://<STAGING>/index.html`.

## Post-processing checklist

### 1. Rewrite the crawl host to the staging domain
Two passes, in this order (run from inside `bakery.local/`):

```bash
find bakery.local -type f -exec sed -i \
  -e 's#http://bakery.local#https://<STAGING>#g' \
  -e 's#bakery.local#<STAGING>#g' \
  {} +
```

- Pass 1 fixes the ~15k absolute `http://bakery.local/...` URLs (assets, canonical,
  importmaps, `wp-json`).
- Pass 2 fixes bare `bakery.local` (HTTrack `<!-- Mirrored from -->` comments and
  URL-encoded `http%3A%2F%2Fbakery.local` inside saved oEmbed JSON). There are no
  navigable bare `href="bakery.local..."` links inside `bakery.local/`.

> The root wrapper `index.html` (outside `bakery.local/`) is discarded, so its bare
> `bakery.local` links don't matter.

### 2. Fix mixed content (CRITICAL, easy to miss)
The original WordPress `home` URL is often the **real** `http://<STAGING>` (not the
crawl host). HTTrack keeps that domain and WordPress emits it **backslash-escaped**
inside inline JS config objects (`wpcf7`, `wpApiSettings` REST root):

```
http:\/\/<STAGING>\/wp-json\/contact-form-7\/v1\/...
```

A plain `grep 'http://'` **misses these** because the slashes are escaped. They cause
`Mixed Content` console errors when the page is served over HTTPS. Replace the escaped
form (and defensively the plain form) across all served files:

```bash
find bakery.local -type f -exec sed -i \
  -e 's#http:\\/\\/<STAGING>#https:\\/\\/<STAGING>#g' \
  -e 's#http:\\/\\/bakery.local#https:\\/\\/<STAGING>#g' \
  -e 's#http://<STAGING>#https://<STAGING>#g' \
  -e 's#http://bakery.local#https://<STAGING>#g' \
  {} +
```

### 3. Strip `srcset`/`sizes` (fixes image 404s)
HTTrack usually downloads the main image but not every WP-generated thumbnail size
(`-100x100.jpg`, `-768x1156.jpg`, …). Those only appear in `srcset`/`sizes`, so they
404 on the live side. The main `src` images exist, so strip the responsive attributes:

```bash
find bakery.local -name '*.html' -exec sed -i -E \
  -e 's/srcset="[^"]*"//g' -e "s/srcset='[^']*'//g" \
  -e 's/sizes="[^"]*"//g'  -e "s/sizes='[^']*'//g" \
  {} +
```

Note: `srcset=\"…\"` leftovers inside JSON/`data-*` attributes and CSS `sizes=auto`
selectors are harmless — the browser never fetches them as responsive images.

### 4. Silence backend/module 404 noise
WooCommerce ships ES-module scripts referenced by an import map + `modulepreload`
links. On a static site these 404 (and free hosts like InfinityFree inject a custom
404 page that cascades). They are non-functional without PHP anyway, so remove them:

```bash
find bakery.local -name '*.html' -exec perl -0pi -e \
  's/<script id="wp-importmap" type="importmap">.*?<\/script>//gs;
   s/<script[^>]*type="module"[^>]*>.*?<\/script>//gs;
   s/<link rel="modulepreload"[^>]*>//g' {} +
```

Expected remaining 404s (inherent, ignore): `wp-admin/admin-ajax.php` and
`wp-comments-post.php` (no PHP backend). The regular WooCommerce scripts
(`woocommerce.min.js`, `add-to-cart.min.js`) resolve fine and can stay.

## Verification

```bash
# No insecure references to the crawl host or staging domain (any form):
grep -rIoh 'http://(bakery\.local|<STAGING>)[^"'"'"' )>\\]*' bakery.local/ | wc -l   # -> 0

# No loadable srcset left (JSON-escaped leftovers are OK):
grep -rI 'srcset="' bakery.local/ | wc -l                                                     # -> 0

# Module machinery removed:
grep -rI 'id="wp-importmap"' bakery.local/ | wc -l                                            # -> 0
grep -rI 'type="module"'    bakery.local/ | wc -l                                             # -> 0
```

> False positive: `index36b6.js` (Contact Form 7) contains `a="http://"+a` — that is
> string code that prepends `http://` to a *user-typed* URL field, never fetched. Not
> mixed content.

## Known limitations of a static export
- **Cart / Checkout / My Account / mini-cart**: non-functional (need WooCommerce + PHP).
- **Contact Form 7**: the form renders but submission fails — it POSTs to the
  `/wp-json` REST API, which doesn't exist statically. Shows a `fetch_error` in console.
  To remove that noise, strip the form's JS wiring or replace it with a `mailto:`/static
  message.
- **Missing assets**: if other 404s appear, they are files HTTrack failed to download
  (regenerate the sizes, or re-run the crawl). Re-scrape rather than hand-fix.
- **Host scheme**: if the staging host is HTTP-only, do NOT hardcode `https://`; use
  protocol-relative `//<STAGING>/...` instead so assets inherit the page scheme.

## Quick reference — this instance
- Crawl host: `bakery.local`
- Staging: `https://sherrie.page.gd` (HTTPS; free InfinityFree hosting injects
  `errors.infinityfree.net/errors/404` for every missing file)
- Theme: custom `bakly-block` (Swiper hero carousel, CF7 newsletter, WooCommerce 11)
