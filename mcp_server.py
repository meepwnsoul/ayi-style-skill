import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ayi-style-skill")
BASE_DIR = Path(__file__).parent

@mcp.tool()
def get_style_guide() -> str:
    """获取写作风格的核心规则（SKILL.md）。在动笔写任何时评、随笔前必须先调用此工具。"""
    skill_path = BASE_DIR / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return "未找到 SKILL.md 文件。"

@mcp.tool()
def search_reference_articles(keywords: str, limit: int = 3) -> str:
    """
    根据话题关键词（多个词用空格分隔，如 '医院 专家' 或 '新能源 雷军'）检索历史原文作为 Few-Shot 范文。
    用于模仿切入角度、造梗方式和结尾收束节奏。
    """
    db_path = BASE_DIR / "articles.jsonl"
    if not db_path.exists():
        return "本地尚未生成 articles.jsonl，请先运行 scraper.py 或触发 GitHub Action 自动生成语料库。"
    
    kw_list = [k.strip() for k in keywords.split() if k.strip()]
    scored_articles = []
    
    with open(db_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            title = item.get("title", "")
            content = item.get("content", "")
            
            # 计算相关性得分：标题命中权重更高
            score = 0
            for kw in kw_list:
                if kw in title:
                    score += 5
                score += content.count(kw)
            
            if score > 0:
                scored_articles.append((score, item))
                
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_articles[:limit]
    
    if not top_matches:
        return f"未找到包含『{keywords}』的历史文章，请尝试更换更宽泛的社会常识词（如：领导、通报、专家、牛马、商K等）。"
    
    result_blocks = []
    for score, art in top_matches:
        result_blocks.append(
            f"### 原文参考：《{art['title']}》\n"
            f"链接：{art['url']}\n"
            f"正文节选：\n{art['content'][:2000]}\n"
        )
    return "\n---\n".join(result_blocks)

if __name__ == "__main__":
    mcp.run()
