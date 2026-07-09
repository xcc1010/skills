#!/usr/bin/env python3
# 爬内网博客 -> 生成 sitemap.xml（零依赖，仅用 Python3 标准库）
# 用法:
#   python3 blog2sitemap.py http://你的博客/                     # 全站爬
#   python3 blog2sitemap.py http://你的博客/ --include /post/    # 只收 URL 含 /post/ 的
#   python3 blog2sitemap.py http://你的博客/ --exclude /tag/ --exclude /category/ --max 2000
# 产出: 当前目录 sitemap.xml + urls.txt(便于你先核对)
import sys, re, time, argparse
from urllib.parse import urljoin, urldefrag, urlparse
from urllib.request import urlopen, Request
from html.parser import HTMLParser

ap = argparse.ArgumentParser()
ap.add_argument("start", help="博客起始 URL，如 http://blog.intra/")
ap.add_argument("--include", action="append", default=[], help="只保留 URL 含该子串(可多次)")
ap.add_argument("--exclude", action="append",
                default=["/tag/", "/tags/", "/category", "/categories", "/author",
                         "/page/", "/feed", "/rss", "/search", "/wp-admin", "/wp-login",
                         "?replytocom", "#"],
                help="排除 URL 含该子串(可多次)")
ap.add_argument("--max", type=int, default=3000, help="最多抓取页面数")
ap.add_argument("--delay", type=float, default=0.3, help="每页间隔秒(别把博客压垮)")
ap.add_argument("--depth", type=int, default=6, help="最大爬取深度")
args = ap.parse_args()

start = args.start
host = urlparse(start).netloc
ASSET = re.compile(r"\.(png|jpe?g|gif|svg|webp|ico|css|js|json|xml|pdf|zip|gz|mp4|mp3|woff2?|ttf)(\?|$)", re.I)

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v: self.hrefs.append(v)

def fetch(url):
    req = Request(url, headers={"User-Agent": "blog2sitemap/1.0"})
    with urlopen(req, timeout=20) as r:
        ct = r.headers.get("Content-Type", "")
        if "text/html" not in ct: return None
        data = r.read(3_000_000)
    try: return data.decode("utf-8", "ignore")
    except Exception: return None

def keep(u):
    if urlparse(u).netloc != host: return False
    if ASSET.search(u): return False
    if any(x in u for x in args.exclude): return False
    if args.include and not any(x in u for x in args.include): return False
    return True

seen, pages, queue = set(), [], [(start, 0)]
seen.add(urldefrag(start)[0])
while queue and len(pages) < args.max:
    url, d = queue.pop(0)
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  skip {url} ({e})"); continue
    if html is None: continue
    if keep(url): pages.append(url); print(f"[{len(pages)}] {url}")
    if d >= args.depth: continue
    p = Links();
    try: p.feed(html)
    except Exception: pass
    for h in p.hrefs:
        nu = urldefrag(urljoin(url, h))[0]
        if nu not in seen and urlparse(nu).netloc == host and not ASSET.search(nu):
            seen.add(nu); queue.append((nu, d + 1))
    time.sleep(args.delay)

# 去重、排序
pages = sorted(set(pages))
with open("urls.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(pages) + "\n")
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for u in pages:
        f.write(f"  <url><loc>{u}</loc></url>\n")
    f.write("</urlset>\n")
print(f"\n完成: {len(pages)} 个 URL -> sitemap.xml / urls.txt")
print("先看 urls.txt 是否都是文章页; 有杂页就用 --include/--exclude 收窄后重跑。")
