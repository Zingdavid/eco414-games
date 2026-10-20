"""Build the ECO 414 games app.

Writes docs/ (served by GitHub Pages as an installable offline app) and a single self-contained
file `ECO414 Games (offline).html` that can be copied to lab computers by USB and opened directly.
Bump CACHE on every change so installed copies pick up the new version.
"""
import base64
import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

CACHE = "eco414-games-v1"
ROOT = pathlib.Path(__file__).parent
DOCS = ROOT / "docs"
(DOCS / "icons").mkdir(parents=True, exist_ok=True)

html = (ROOT / "src" / "app.html").read_text(encoding="utf-8")
for tag, lib in [("<!--VENDOR_QRCODE-->", "qrcode.js"), ("<!--VENDOR_JSQR-->", "jsQR.js")]:
    code = (ROOT / "vendor" / lib).read_text(encoding="utf-8").replace("</script", "<\\/script")
    html = html.replace(tag, f"<script>\n{code}\n</script>")
(DOCS / "index.html").write_text(html, encoding="utf-8")


def icon(size, pad, name):
    im = Image.new("RGBA", (size, size), "#2563eb")
    d = ImageDraw.Draw(im)
    s = size - 2 * pad
    # two unequal shares of a pie: the game in one picture
    box = [pad + s * 0.12, pad + s * 0.12, pad + s * 0.88, pad + s * 0.88]
    d.pieslice(box, -90, 90 + 36, fill="#ffffff")
    d.pieslice(box, 90 + 36, 270, fill="#d97706")
    im.save(DOCS / "icons" / name)


icon(192, 0, "icon-192.png")
icon(512, 0, "icon-512.png")
icon(512, 64, "maskable-512.png")
icon(180, 0, "apple-touch-icon.png")

# single-file copy for lab computers: no manifest, icon embedded, so nothing is looked up next to it
b64 = base64.b64encode((DOCS / "icons" / "icon-192.png").read_bytes()).decode()
single = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
single = single.replace('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n', "")
single = single.replace('href="icons/icon-192.png"', f'href="data:image/png;base64,{b64}"')
assert "icons/" not in single and "manifest.webmanifest" not in single
(ROOT / "ECO414 Games (offline).html").write_text(single, encoding="utf-8")

manifest = {
    "name": "ECO 414 Classroom Games",
    "short_name": "ECO414 Games",
    "description": "Ultimatum and Dictator games for the classroom. Works offline.",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#f6f6f4",
    "theme_color": "#2563eb",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(DOCS / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

sw = """// Offline support: serve the app from cache, refresh it in the background.
const CACHE = "%s";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/maskable-512.png", "icons/apple-touch-icon.png"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(caches.open(CACHE).then(async (cache) => {
    const cached = await cache.match(req, { ignoreSearch: true });
    const network = fetch(req).then((res) => { if (res && res.ok) cache.put(req, res.clone()); return res; }).catch(() => cached);
    return cached || network;
  }));
});
""" % CACHE
(DOCS / "sw.js").write_text(sw, encoding="utf-8")
print("built", DOCS, "and offline file;", len(html) // 1024, "KB")
