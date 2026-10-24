import json
import re
import time
import urllib.request
from bs4 import BeautifulSoup

BASE = "https://" + "wang54.blogspot.com"
SEED_URLS = [
    BASE + "/2020/01/2020.html",
    BASE + "/2023/03/20232024.html",
    BASE + "/2022/01/20212022.html",
    BASE + "/2020/01/20192020.html",
    BASE + "/2020/01/20172018.html",
    BASE + "/2020/01/20152016.html",
    BASE + "/2020/01/2014.html",
    BASE + "/2015/09/blog-post_72.html",
]

def norm_url(u):
    if not u:
        return ""
    u = u.split('#')[0].split('?')[0].strip()
    return u.replace("http://", "https://")

def fetch_html(url):
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def clean_article_text(raw_text):
    # 截断每篇文章底部自带的“打赏二维码”及“王五四文章精选”目录尾巴
    for marker in ["打赏王五四的二维码", "王五四文章精选：", "敬告转发的公众号"]:
        if marker in raw_text:
            raw_text = raw_text.split(marker)[0]
    return raw_text.strip()

def main():
    year_pages = {norm_url(u) for u in SEED_URLS}
    print(f"1. 开始扫描 {len(year_pages)} 个历年目录页提取文章链接...")
    
    article_links = {}
    for page_url in sorted(year_pages):
        print(f" -> 正在扫描目录: {page_url}")
        try:
            soup = BeautifulSoup(fetch_html(page_url), 'html.parser')
            for a in soup.select('a[href*="wang54.blogspot.com"]'):
                href = norm_url(a.get('href', ''))
                title = a.get_text(" ", strip=True)
                # 排除目录页自身、导航链接和非文章页
                if (href and href not in year_pages 
                    and re.search(r'/\d{4}/\d{2}/', href) 
                    and len(title) > 3
                    and not any(k in title for k in ['交流群', '年', '文章精选', '较新的博文', '较早的博文'])):
                    article_links[href] = title
        except Exception as e:
            print(f"跳过目录 {page_url}: {e}")

    print(f"2. 共提取到 {len(article_links)} 篇独立文章，开始抓取并清洗正文...")
    saved_count = 0
    with open("articles.jsonl", "w", encoding="utf-8") as f:
        for idx, (url, title) in enumerate(article_links.items(), 1):
            try:
                art_soup = BeautifulSoup(fetch_html(url), 'html.parser')
                # 取页面上字数最多的 post-body（即为文章主正文）
                bodies = art_soup.select('.post-body')
                if not bodies:
                    continue
                main_body = max(bodies, key=lambda b: len(b.get_text()))
                text = clean_article_text(main_body.get_text("\n", strip=True))
                
                if len(text) > 200:
                    record = {
                        "title": title,
                        "url": url,
                        "content": text
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    saved_count += 1
                    print(f"[{idx}/{len(article_links)}] 已收录: {title} ({len(text)}字)")
                time.sleep(0.2)
            except Exception as e:
                print(f"[{idx}/{len(article_links)}] 抓取跳过 {title}: {e}")

    print(f"全部完成！共成功收录 {saved_count} 篇纯净原文至 articles.jsonl")

if __name__ == "__main__":
    main()
