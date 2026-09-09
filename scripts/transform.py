"""Transform HTTrack mirror URLs to root-relative paths."""
import re, glob, os

all_files = (glob.glob('**/*.html', recursive=True) +
             glob.glob('**/*.js', recursive=True) +
             glob.glob('**/*.css', recursive=True) +
             glob.glob('**/*.json', recursive=True) +
             glob.glob('**/*.xml', recursive=True))
all_files = [f for f in all_files if not f.startswith('./.git')]

for filepath in all_files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content

    # Replace bakery.local URLs
    content = re.sub(r'http://bakery\.local', '/', content)
    content = re.sub(r'https://bakery\.local', '/', content)
    content = re.sub(r'http%3A%2F%2Fbakery\.local%2F', '/', content)
    content = re.sub(r'http:\/\/bakery\.local\/', '/', content)

    # Fix protocol-relative URLs
    content = re.sub(r'//wp-admin', '/wp-admin', content)
    content = re.sub(r'//wp-content', '/wp-content', content)
    content = re.sub(r'//wp-includes', '/wp-includes', content)
    content = re.sub(r'//wp-json', '/wp-json', content)
    content = re.sub(r'//wp-comments-post', '/#', content)

    # Remove HTTrack comments
    content = re.sub(r'<!--.*?-->', '', content)
    content = re.sub(r'<!--.*?-->\n?', '', content)

    # Remove oEmbed link tags
    content = re.sub(r'<link rel="alternate" title="oEmbed[^>]*>\n?', '', content)
    content = re.sub(r'<link rel="alternate" title="JSON"[^>]*>\n?', '', content)
    content = re.sub(r'<link[^>]*href="[^"]*wp-json[^"]*"[^>]*>\n?', '', content)
    content = re.sub(r'<link[^>]*rel="EditURI"[^>]*>\n?', '', content)
    content = re.sub(r'<link[^>]*rel="rsd"[^>]*>\n?', '', content)
    content = re.sub(r'<link[^>]*rel="shortlink"[^>]*>\n?', '', content)

    # Remove plugin CSS/JS refs
    content = re.sub(r'<link[^>]*href="[^"]*plugins/woocommerce[^"]*"[^>]*>\n?', '', content)
    content = re.sub(r'<link[^>]*href="[^"]*plugins/contact-form-7[^"]*"[^>]*>\n?', '', content)

    # Remove noscript blocks
    content = re.sub(r'<noscript>.*?</noscript>\n?', '', content, flags=re.DOTALL)

    # Remove wp-emoji scripts
    content = re.sub(r'<script[^>]*src="[^"]*wp-emoji-loader[^"]*"[^>]*>\n?', '', content)
    content = re.sub(r'<script[^>]*src="[^"]*wp-emoji-release[^"]*"[^>]*>\n?', '', content)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)

# Fix index.html head
with open('index.html', 'r') as f:
    content = f.read()

import_map = '<script id="wp-importmap" type="importmap">\n{"imports":{"@wordpress/interactivity":"/wp-includes/js/dist/script-modules/interactivity/index.min.js?ver=efaa5193bbad9c60ffd1"}}\n</script>\n'
script_idx = content.find('<script')
if script_idx >= 0 and 'wp-importmap' not in content:
    content = content[:script_idx] + import_map + content[script_idx:]

if '@wordpress/interactivity-js-modulepreload' not in content:
    preload = '<link rel="modulepreload" href="/wp-includes/js/dist/script-modules/interactivity/index.min132d.js" id="@wordpress/interactivity-js-modulepreload" data-wp-fetchpriority="low">'
    importmap_end = content.find('</script>', content.find('wp-importmap'))
    if importmap_end >= 0:
        content = content[:importmap_end+9] + '\n' + preload + content[importmap_end+9:]

# Fix double slashes
content = content.replace('//wp-includes', '/wp-includes')
content = content.replace('//wp-content', '/wp-content')
content = content.replace('//wp-admin', '/wp-admin')

with open('index.html', 'w') as f:
    f.write(content)

# Fix search overlay in interactionsa024.js
with open('wp-content/themes/bakly-block/assets/js/interactionsa024.js', 'r') as f:
    js = f.read()
js = js.replace('/wp-json/wc/store/v1/products', '/products.json')
with open('wp-content/themes/bakly-block/assets/js/interactionsa024.js', 'w') as f:
    f.write(js)

print('Transform complete')
