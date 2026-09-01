# AGENTS.md — Post-processing HTTrack scrapes of WordPress sites

This directory is an **HTTrack Website Copier** mirror of a WordPress + WooCommerce
site ("Luqman Petroleum", Nairobi). The deploy target is `https://sherrie.page.gd`.
The notes below are generic enough to reuse for any similar scrape, with
`bakery.local` = the crawl host.

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

### 1. Rewrite the crawl host to root-relative URLs
Go straight to root-relative (`/path`). No staging-URL intermediate step.
Run from inside `bakery.local/`:

```bash
find . -type f -not -path './.git/*' -not -name '*.json' -print0 | xargs -0 perl -pi -e 's|http://bakery\.local|/|g'
find ./wp-json -name '*.json' -not -path './.git/*' -print0 | xargs -0 perl -pi -e 's|http://bakery\.local|/|g'
```

- Fixes ~15k absolute `http://bakery.local/...` URLs (assets, canonical, importmaps, `wp-json`).
- No bare `bakery.local` hrefs remain inside `bakery.local/`.

### 2. Strip HTTrack mirror comments
Remove `<!-- Mirrored from bakery.local/... -->` lines and `<!-- Created by HTTrack -->` lines.
Keep the `<meta charset>` wrapper from `<!-- Added by HTTrack --><meta ...><!-- /Added by HTTrack -->`.

### 3. Fix mixed content
Replace escaped `http:\/\/bakery.local` in `wp-json` JSON files:

```bash
find ./wp-json -name '*.json' -not -path './.git/*' -print0 | xargs -0 perl -pi -e 's|http://bakery\.local|/|g'
```

### 4. Strip `srcset`/`sizes` (fixes image 404s)
HTTrack downloads the main image but not every WP-generated thumbnail size.
Strip responsive attributes from HTML:

```bash
find . -type f -name '*.html' -not -path './.git/*' -print0 | xargs -0 perl -pi -e 's/\s+srcset="[^"]*"//g; s/\s+sizes="[^"]*"//g'
```

Note: `state.itemSrcset`/`state.itemSizes` in inline JS are not HTML attributes — leave them.

### 5. Silence backend/module 404 noise
WooCommerce ships ES-module scripts referenced by an import map + `modulepreload` links.
On a static site these 404. Remove them:

```bash
find . -type f -name '*.html' -not -path './.git/*' -print0 | xargs -0 perl -0777 -pi -e \
  's/<script id="wp-importmap" type="importmap">.*?<\/script>//gs;
   s/<script id="woocommerce\/[^"]*-js-module"[^>]*type="module"><\/script>//g;
   s/<link rel="modulepreload"[^>]*>//g' {} +
```

### 6. Replace contact details
Update all instances of old Sherrie Bakery contact info to the new Luqman Petroleum details:
- Phone: `+254 20-2222736 / +254737531346`
- Email: `info@luqmanpetroleum.com`
- Address: `Luqman Mall 3rd Flr, Othaya Road`
- `tel:+12135553890` → `tel:+254202222736`

### 7. Footer
Theme `bakly-block` v2 has native `.bakly-footer { padding-inline: var(--bakly-gutter) }`
with gradient background — footer stretches from end to end automatically.
No custom CSS padding needed.

## Verification

```bash
# No insecure references to the crawl host:
grep -rIoh 'http://bakery\.local' bakery.local/ | wc -l   # -> 0

# No loadable srcset left (JS state.itemSrcset leftovers are OK):
grep -rI 'srcset="' bakery.local/ | wc -l                                                  # -> 0

# Module machinery removed:
grep -rI 'id="wp-importmap"' bakery.local/ | wc -l                                            # -> 0
grep -rI 'type="module"'    bakery.local/ | wc -l                                             # -> 0

# Contact details updated:
grep -rI 'info@luqmanpetroleum' bakery.local/ | wc -l                                        # -> > 0
grep -rI 'info@sherrie' bakery.local/ | wc -l                                               # -> 0
```

## Known limitations of a static export
- **Cart / Checkout / My Account / mini-cart**: non-functional (need WooCommerce + PHP).
- **Contact Form 7**: the form renders but submission fails — it POSTs to the `/wp-json` REST API.
- **Missing assets**: if other 404s appear, re-scrape rather than hand-fix.

## Quick reference — this instance
- Crawl host: `bakery.local`
- Staging: `https://sherrie.page.gd` (HTTPS; free InfinityFree hosting)
- Theme: custom `bakly-block` (Swiper hero carousel, CF7 newsletter, WooCommerce 11)
- Contact: `info@luqmanpetroleum.com` / `+254 20-2222736 / +254737531346` / `Luqman Mall 3rd Flr, Othaya Road`
