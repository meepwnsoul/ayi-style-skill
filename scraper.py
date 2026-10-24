import json
import time
import urllib.request
from bs4 import BeautifulSoup

# 预设所有年份目录页与精选页，确保 2014-2026 全量收录
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
def fetch_html(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def main():
    print("1. 正在扫描主导航栏，获取所有年份目录页...")
    year_pages = set(SEED_URLS)
    try:
        main_soup = BeautifulSoup(fetch_html(SEED_URLS[0]), 'html.parser')
        for a in main_soup.select('a[href*="wang54.blogspot.com"]'):
            href = a.get('href', '').split('#')[0]
            text = a.get_text(strip=True)
            if any(k in text for k in ['年', '精选']):
                year_pages.add(href)
    except Exception as e:
        print(f"读取主导航失败: {e}")

    print(f"共发现 {len(year_pages)} 个目录索引页，开始提取文章链接...")
    article_links = {}
    for page_url in sorted(year_pages):
        print(f" -> 正在扫描目录: {page_url}")
        try:
            soup = BeautifulSoup(fetch_html(page_url), 'html.parser')
            for a in soup.select('.post-body a[href*="wang54.blogspot.com"]'):
                href = a.get('href', '').split('#')[0]
                title = a.get_text(strip=True)
                if href and title and href not in year_pages and len(title) > 2:
                    article_links[href] = title
        except Exception as e:
            print(f"跳过目录 {page_url}: {e}")

    print(f"2. 共发现 {len(article_links)} 篇独立文章，开始抓取正文...")
    saved_count = 0
    with open("articles.jsonl", "w", encoding="utf-8") as f:
        for idx, (url, title) in enumerate(article_links.items(), 1):
            try:
                art_soup = BeautifulSoup(fetch_html(url), 'html.parser')
                body = art_soup.select_one('.post-body')
                if not body:
                    continue
                text = body.get_text("\n", strip=True)
                # 过滤掉纯目录或过短无效页
                if len(text) > 150:
                    record = {
                        "title": title,
                        "url": url,
                        "content": text
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    saved_count += 1
                    print(f"[{idx}/{len(article_links)}] 已收录: {title} ({len(text)}字)")
                time.sleep(0.3)
            except Exception as e:
                print(f"[{idx}/{len(article_links)}] 抓取跳过 {title}: {e}")

    print(f"全部完成！共成功收录 {saved_count} 篇原文至 articles.jsonl")

if __name__ == "__main__":
    main()
