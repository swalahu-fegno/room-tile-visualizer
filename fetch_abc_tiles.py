"""Build abc-tiles.json from the ABC Emporio catalogue (Surface category).

Usage: python3 fetch_abc_tiles.py [pages]      (20 products per page; default: all pages)

Steps: list products -> read each product's images -> take the flat tile scan
(last image) -> measure its shape -> keep known tile shapes and guess the size.
Room photos (~3:2) and branded catalogue cards (Qutone) are skipped.
"""
import json, math, os, subprocess, sys, tempfile, urllib.parse
from concurrent.futures import ThreadPoolExecutor

API = "https://abcemporio.com/api/v1/catalogue/products/"
THUMB = "https://www.abcemporio.com/_next/image?url={}&w=256&q=60"
# image width/height ratio -> tile size in metres (width, length)
SHAPES = [(1.0, (.6, .6)), (2.0, (1.2, .6)), (0.5, (.6, 1.2)), (0.67, (.8, 1.2)),
          (6.0, (1.2, .2)), (0.167, (.2, 1.2)), (4.0, (1.2, .3)), (0.25, (.3, 1.2))]
SKIP_BRANDS = {"Qutone"}


def curl(url, out=None):
    # curl uses the system certificates (this Python install has none)
    args = ["curl", "-sf", "--retry", "2", "--max-time", "40", url] + (["-o", out] if out else [])
    r = subprocess.run(args, capture_output=True)
    if r.returncode:
        raise RuntimeError(url)
    return r.stdout


def get(url):
    return json.loads(curl(url))


def list_products(pages):
    first = get(f"{API}?category_path__startswith=000A&page=1")
    total = math.ceil(first["count"] / 20)
    pages = min(pages or total, total)
    def page(p):
        try:
            return get(f"{API}?category_path__startswith=000A&page={p}")["results"]
        except Exception:
            return []
    with ThreadPoolExecutor(6) as ex:
        rest = list(ex.map(page, range(2, pages + 1)))
    items = first["results"] + [x for r in rest for x in r]
    print(f"{len(items)} products from {pages} pages", flush=True)
    return items


def detail(it):
    brand = (it.get("brand") or {}).get("title", "")
    if brand in SKIP_BRANDS:
        return None
    try:
        d = get(f"{API}{it['slug']}/")
    except Exception:
        return None
    if not (d.get("product_type") or {}).get("is_tile", True):
        return None
    imgs = [u for u in d.get("images", []) if u.startswith("https://abcemporio-live")]
    if not imgs:
        return None
    return {"id": "abc_" + it["slug"], "name": d["title"].title()[:40], "brand": d.get("brand") or brand,
            "img": imgs[-1], "url": f"https://www.abcemporio.com/product/{it['slug']}"}


def measure(x, tmp):
    f = os.path.join(tmp, x["id"] + ".img")
    try:
        curl(THUMB.format(urllib.parse.quote(x["img"], safe="")), f)
        o = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", f], capture_output=True, text=True).stdout.split()
        w, h = int(o[o.index("pixelWidth:") + 1]), int(o[o.index("pixelHeight:") + 1])
    except Exception:
        return None
    ar = w / h
    for r, (tw, th) in SHAPES:
        if abs(ar - r) / r < .04:
            return {**x, "w": tw, "h": th}
    return None


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    items = list_products(pages)
    with ThreadPoolExecutor(8) as ex:
        found = [x for x in ex.map(detail, items) if x]
    seen, uniq = set(), []
    for x in found:
        if x["img"] not in seen:
            seen.add(x["img"]); uniq.append(x)
    print(f"{len(uniq)} unique tile images; measuring shapes...", flush=True)
    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(8) as ex:
        tiles = [x for x in ex.map(lambda x: measure(x, tmp), uniq) if x]
    names = set(); out = []
    for t in tiles:  # same tile listed under several names/sizes -> keep first
        if t["name"] not in names:
            names.add(t["name"]); out.append(t)
    json.dump(out, open("abc-tiles.json", "w"), indent=1)
    print(f"saved {len(out)} tiles to abc-tiles.json")


if __name__ == "__main__":
    main()
