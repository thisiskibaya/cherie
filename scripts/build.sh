#!/bin/bash
# Build script: takes an HTTrack scrape and produces a deployable static site
# Usage: ./scripts/build.sh <path_to_httrack_scrape>
# Example: ./scripts/build.sh "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local"

set -e

SRC="${1:-/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Building static site from scrape ==="
echo "Source: $SRC"
echo "Project: $PROJECT_ROOT"

# Clean project directory
cd "$PROJECT_ROOT"
rm -rf about blog contact customer-favorites-most-loved-gifts-from-our-shop \
  customer-spotlight-the-stories-our-favorite-purchases hello-world \
  last-minute-gift-ideas-that-still-feel-personal our-best-selling-gifts-and-why-customers-love-them \
  our-customers-favorite-flavors-based-on-real-orders our-menu \
  pastry-pairings-what-to-eat-or-drink-with-your-favorite-bake privacy-policy \
  product product-category shop tag team terms-conditions testimonials \
  wp-content wp-includes index.html products.json vercel.json package.json .gitignore \
  index*.html xmlrpc*.php

# Copy fresh scrape
cp -r "$SRC"/* . 2>/dev/null
cp "$SRC"/.* . 2>/dev/null || true

# Remove HTTrack artifacts
find . -name "index*.html" ! -name "index.html" -type f -delete 2>/dev/null
rm -rf hts-cache/ hts-log.txt 2>/dev/null

# Remove server-side directories (fresh mirrors add nested feed/ dirs per page)
rm -rf wp-admin/ wp-json/ author/ comments/ feed/ my-account/ cart/ checkout/ 2>/dev/null
find . -type d -name feed -not -path './.git/*' -exec rm -rf {} + 2>/dev/null

# Remove wp-content/plugins/ (dynamic)
rm -rf wp-content/plugins/ 2>/dev/null

# Clean wp-includes
rm -rf wp-includes/js/jquery/ 2>/dev/null
rm -f wp-includes/js/comment-reply.min42a0.js wp-includes/js/zxcvbn-async.min5152.js 2>/dev/null
# Remove vendor/ contents but keep the directory; restore api-fetch separately
find wp-includes/js/dist/vendor/ -type f -delete 2>/dev/null
find wp-includes/js/dist/ -type f ! -path "*/script-modules/*" ! -path "*/vendor/*" -delete 2>/dev/null
rm -rf wp-includes/js/dist/script-modules/* 2>/dev/null

# Restore essential WP JS files
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/api-fetch.min9cd3.js" wp-includes/js/dist/ 2>/dev/null
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/hooks.min394d.js" wp-includes/js/dist/ 2>/dev/null
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/i18n.mineca5.js" wp-includes/js/dist/ 2>/dev/null
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/url.min3303.js" wp-includes/js/dist/ 2>/dev/null
cp -r "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/vendor/" wp-includes/js/dist/vendor/ 2>/dev/null
mkdir -p wp-includes/js/dist/script-modules/interactivity/
cp -r "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/script-modules/interactivity/" wp-includes/js/dist/script-modules/interactivity/ 2>/dev/null
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-includes/js/dist/script-modules/interactivity/index.min132d.js" wp-includes/js/dist/script-modules/interactivity/index.min132d.js 2>/dev/null

# Restore product JSON files for products.json generation
mkdir -p wp-json/wp/v2/product/
cp "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local/wp-json/wp/v2/product/"*.json wp-json/wp/v2/product/ 2>/dev/null

# Generate products.json
python3 -c "
import json, os, glob, re
products = []
for page in sorted(glob.glob('product/*/index.html')):
    with open(page) as f:
        html = f.read()
    title = re.search(r'<title>([^<]+)</title>', html)
    name = title.group(1).strip() if title else os.path.basename(os.path.dirname(page))
    link = f'/product/{os.path.basename(os.path.dirname(page))}/'
    price = ''
    images = []
    products.append({'id': len(products)+1, 'name': name, 'permalink': link, 'price': price, 'images': images})
products.sort(key=lambda x: x['name'])
with open('products.json', 'w') as f:
    json.dump(products, f, indent=2)
print(f'Generated products.json with {len(products)} products')
" 2>/dev/null

# Run URL transformation (fail hard if transform.py errors)
python3 scripts/transform.py

# Fix index.html head section
python3 -c "
with open('index.html', 'r') as f:
    content = f.read()
# Add clean importmap
import_map = '<script id=\"wp-importmap\" type=\"importmap\">\n{\"imports\":{\"@wordpress/interactivity\":\"/wp-includes/js/dist/script-modules/interactivity/index.min132d.js?ver=efaa5193bbad9c60ffd1\"}}\n</script>\n'
script_idx = content.find('<script')
if script_idx >= 0 and 'wp-importmap' not in content:
    content = content[:script_idx] + import_map + content[script_idx:]
# Add modulepreload
if '@wordpress/interactivity-js-modulepreload' not in content:
    preload = '<link rel=\"modulepreload\" href=\"/wp-includes/js/dist/script-modules/interactivity/index.min132d.js\" id=\"@wordpress/interactivity-js-modulepreload\" data-wp-fetchpriority=\"low\">'
    importmap_end = content.find('</script>', content.find('wp-importmap'))
    if importmap_end >= 0:
        content = content[:importmap_end+9] + '\n' + preload + content[importmap_end+9:]
# Fix search overlay (bundle hash changes per scrape — discover it)
import glob as _glob
_matches = sorted(_glob.glob('wp-content/themes/bakly-block/assets/js/interactions*.js'))
if _matches:
    with open(_matches[0], 'r') as f:
        js = f.read()
    js = js.replace(\"/wp-json/wc/store/v1/products\", \"/products.json\")
    with open(_matches[0], 'w') as f:
        f.write(js)
else:
    print('WARNING: no interactions*.js found, search overlay fix skipped')
# Fix double-slash URLs
with open('index.html', 'r') as f:
    content = f.read()
content = content.replace('//wp-includes', '/wp-includes')
content = content.replace('//wp-content', '/wp-content')
with open('index.html', 'w') as f:
    f.write(content)
print('index.html head fixed')
"

# Repair: restore referenced assets from the mirror + fix static-site issues
# (import map, emoji module, un-hashed URLs, dead page links, dead image refs)
python3 scripts/repair.py "$SRC"

# Create deployment configs
# NOTE: must match the deployed config — no "framework" key (invalid value
# fails schema validation), "build": "true" in package.json triggers
# @vercel/static builder, and NO catch-all rewrite (a missing file
# must 404 instead of returning index.html as HTML/JS).
cat > vercel.json << 'VERCELJSON'
{
  "outputDirectory": ".",
  "headers": [
    { "source": "/(.*)", "headers": [
      { "key": "Access-Control-Allow-Origin", "value": "*" },
      { "key": "Access-Control-Allow-Methods", "value": "GET, POST, OPTIONS" },
      { "key": "Access-Control-Allow-Headers", "value": "Content-Type" }
    ]},
    { "source": "/wp-includes/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]},
    { "source": "/wp-content/uploads/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]},
    { "source": "/wp-content/plugins/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]},
    { "source": "/wp-content/themes/bakly-block/assets/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]}
  ],
  "rewrites": [
    { "source": "/(.*)/", "destination": "/$1/index.html" }
  ]
}
VERCELJSON

cat > package.json << 'PKGJSON'
{ "name": "cherie", "version": "1.0.0", "description": "Static site for layout review", "scripts": { "build": "true" } }
PKGJSON

cat > .gitignore << 'GITIGNORE'
node_modules/
.htaccess
wp-config.php
hts-cache/
hts-log.txt
*.log
.DS_Store
Thumbs.db
GITIGNORE

echo "=== Build complete! ==="
echo "Next steps:"
echo "  cd $PROJECT_ROOT"
echo "  git add -A"
echo "  git commit -m 'Update from fresh scrape'"
echo "  git push origin main"
