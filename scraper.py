import json
import re
import time
import urllib.request
from bs4 import BeautifulSoup

# 目录页挂在 wang54，文章正文实际在 wangwusiwj 等子博客上
BASE = "https://wang54.blogspot.com"
SEED_URLS = [
    BASE + "/2020/01/2020.html",                 # 25-26年
    BASE + "/2016/09/blog-post.html",            # 23-24年
    BASE + "/2016/09/blog-post_74.html",         # 21-22年
    BASE + "/2018/08/blog-post.html",            # 19-20年
    BASE + "/2016/09/blog-post_22.html",         # 17-18年
    BASE + "/2016/09/blog-post_17.html",         # 15-16年
    BASE + "/2017/01/blog-post.html",            # 2014年前
    BASE + "/2018/01/blog-post.html",            # 文章精选
]

# 任意 xxx.blogspot.<任意后缀>/YYYY/MM/xxx.html 的文章链接
ARTICLE_RE = re.compile(r'^https://[\w-]+\.blogspot\.com/\d{4}/\d{2}/[^/]+\.html$')
# 目录里的标题带日期前缀，如 "09-30  标题" 或 "2024- 12-31  标题"
DATE_PREFIX_RE = re.compile(r'^\s*(\d{4}\s*-\s*)?\d{1,2}\s*-\s*\d{1,2}\s+')


def norm_url(u):
    if not u:
        return ""
    u = u.split('#')[0].split('?')[0].strip()
    u = u.replace("http://", "https://")
    # blogspot.com.au / .com.tw / .jp 等国家域名统一成 .com
    u = re.sub(r'\.blogspot\.[a-z.]+/', '.blogspot.com/', u)
    return u


def fetch_html(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def clean_title(t):
    t = re.sub(r'\s+', ' ', t).strip()
    return DATE_PREFIX_RE.sub('', t).strip()


def clean_article_text(raw_text):
    for marker in ["打赏王五四的二维码", "王五四文章精选：", "敬告转发的公众号"]:
        if marker in raw_text:
            raw_text = raw_text.split(marker)[0]
    return raw_text.strip()


def main():
    index_pages = [norm_url(u) for u in SEED_URLS]
    index_set = set(index_pages)
    print(f"1. 开始扫描 {len(index_pages)} 个目录页提取文章链接...")

    article_links = {}
    for page_url in index_pages:
        print(f" -> 正在扫描目录: {page_url}")
        try:
            soup = BeautifulSoup(fetch_html(page_url), 'html.parser')
        except Exception as e:
            print(f"    !! 目录页抓取失败（后面会是 0 篇的主要原因）: {e}")
            continue
        # 只看目录正文区，天然避开顶部导航、侧边栏、上一篇/下一篇
        scope = soup.select('.post-body') or [soup]
        found = 0
        for body in scope:
            for a in body.find_all('a', href=True):
                href = norm_url(a['href'])
                title = clean_title(a.get_text(" ", strip=True))
                if not ARTICLE_RE.match(href) or href in index_set or len(title) < 2:
                    continue
                if href not in article_links:
                    article_links[href] = title
                    found += 1
        print(f"    找到 {found} 个新链接")

    print(f"2. 共提取到 {len(article_links)} 篇独立文章，开始抓取并清洗正文...")
    if not article_links:
        print("没有拿到任何文章链接，不写文件。先确认上面的目录页能否正常访问。")
        return

    saved_count = 0
    with open("articles.jsonl", "w", encoding="utf-8") as f:
        for idx, (url, title) in enumerate(article_links.items(), 1):
            try:
                art_soup = BeautifulSoup(fetch_html(url), 'html.parser')
                bodies = art_soup.select('.post-body')
                if not bodies:
                    print(f"[{idx}/{len(article_links)}] 无正文: {title}")
                    continue
                main_body = max(bodies, key=lambda b: len(b.get_text()))
                text = clean_article_text(main_body.get_text("\n", strip=True))

                if len(text) > 200:
                    f.write(json.dumps({"title": title, "url": url, "content": text},
                                       ensure_ascii=False) + "\n")
                    f.flush()
                    saved_count += 1
                    print(f"[{idx}/{len(article_links)}] 已收录: {title} ({len(text)}字)")
                else:
                    print(f"[{idx}/{len(article_links)}] 正文过短跳过: {title} ({len(text)}字)")
            except Exception as e:
                print(f"[{idx}/{len(article_links)}] 抓取跳过 {title}: {e}")
            time.sleep(0.3)

    print(f"全部完成！共成功收录 {saved_count} 篇原文至 articles.jsonl")


if __name__ == "__main__":
    main()
