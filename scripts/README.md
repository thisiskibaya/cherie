# Build Process for Sherrie Bakery Static Site

## Future Scrapes

### 1. Scrape the site with HTTrack
```bash
httrack http://bakery.local/ +*.png +*.gif +*.jpg +*.jpeg +*.css +*.js -O "/mnt/c/My Web Sites/Sherrie Bakery v3"
```

### 2. Rebuild the project
```bash
cd "/mnt/c/My Web Sites/Sherrie Bakery v3/cherie"
./scripts/build.sh "/mnt/c/My Web Sites/Sherrie Bakery v3/bakery.local"
```

### 3. Commit and push
```bash
cd "/mnt/c/My Web Sites/Sherrie Bakery v3/cherie"
git add -A
git commit -m "Update from fresh scrape"
git push origin main
```

### 4. Deploy to Vercel
```bash
# Either push triggers automatic deploy, or:
vercel --prod
```

## File Structure
- `scripts/build.sh` — Full build pipeline from HTTrack scrape
- `scripts/transform.py` — URL transformation step
- `scripts/repair.py` — Restores referenced assets from the mirror and fixes
  static-site conversion issues (interactivity import map, inline wp-emoji
  module removal, un-hashed asset URLs, links to removed pages, dead image
  src/srcset/`url(...)` references). Called automatically by `build.sh` and
  safe to run again on an existing deploy.
- `scripts/verify.py` — Sanity check: fails if any HTML page references a
  file that isn't in the deploy tree or still has known conversion leftovers.
- `products.json` — Static product data for search overlay
- `vercel.json` — Vercel configuration (CORS headers, immutable caching).
  NOTE: there is deliberately **no catch-all rewrite** — a missing file must
  404 instead of returning `index.html` (which previously made every missing
  JS/CSS/image "load" as HTML and triggered the `Unexpected token '<'` /
  MIME-type errors).

## Interactive Features Preserved
- Mobile menu (`@wordpress/interactivity` module)
- Hero product carousel (Swiper)
- Scroll-snap carousels (testimonials, products, social)
- Countdown timer
- Search overlay (fetches from `/products.json`)
- Header scroll fade
- Shop filters toggle
- Newsletter form (client-side)
