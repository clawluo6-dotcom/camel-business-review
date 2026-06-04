#!/usr/bin/env python3
"""
批量导入 Obsidian 文章到 articles.json
自动按文件名匹配，不手动拼路径，避免引号问题
"""

import json, os, re
from datetime import datetime
from pathlib import Path

VAULT = Path("/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian")
OUT   = "/Users/luoclaw/WorkBuddy/2026-06-04-08-26-23/AI_Frontier_Daily/articles.json"

# ── 文章清单：用 (id, pillar, category, subcategory, filename_glob, tags, importance)
# filename_glob 只需能唯一匹配文件名片段即可
ARTICLES_SPEC = [
    # 🌌 世界观
    ("consciousness-slicing",   "worldview", "世界观",   "意识哲学",   "C03 · 意识切片世界观",
     ["意识","哲学","切片"], 5),
    ("world-essence-full",      "worldview", "世界观",   "世界的真相", "2-世界的本质-完整版",
     ["世界本质","真相","哲学"], 5),
    ("world-fake",              "worldview", "世界观",   "世界的真相", "5-理解",
     ["世界是假的","认知"], 4),
    ("break-all-forms",          "worldview", "世界观",   "世界的真相", "6-破一切相",
     ["破相","哲学"], 4),
    ("ding-jing-kong",          "worldview", "世界观",   "世界的真相", "7-分别",
     ["定","净","空","哲学"], 3),
    ("mind-appears-form",        "worldview", "世界观",   "世界的真相", "8-一念花开",
     ["一念花开","心相一体"], 4),
    ("nature-reality",           "worldview", "世界观",   "性相不二",   "9-世界是虚妄的本质",
     ["性相不二","虚妄","世界观"], 4),
    ("karma-nature",            "worldview", "世界观",   "世界的真相", "10-性相+业力",
     ["业力","性相","世界原理"], 4),
    ("mind-gives-form",          "worldview", "世界观",   "世界的真相", "起心显相",
     ["起心显相","意识"], 3),
    ("force-unification",        "worldview", "世界观",   "力与物理",   "S02 · 力统一理论",
     ["力统一","物理","三圈模型"], 5),
    ("worldview-panorama",      "worldview", "世界观",   "意识哲学",   "MOC-世界观全景图",
     ["全景图","世界观","MOC"], 3),

    # 🏛️ 社会逻辑
    ("wealth-delusion",          "social",    "社会逻辑", "宏观经济",   "01-财富的谬论",
     ["财富","谬论","经济"], 5),
    ("wealth-delusion-summary",  "social",    "社会逻辑", "宏观经济",   "02-财富的谬论",
     ["财富","总结"], 4),
    ("500-overview",             "social",    "社会逻辑", "500年大周期","一、世界500年大周期概述",
     ["500年","大周期","概述"], 5),
    ("500-mode-iteration",       "social",    "社会逻辑", "500年大周期","二、世界500年霸权",
     ["霸权","模式更迭"], 5),
    ("500-iteration-essence",    "social",    "社会逻辑", "500年大周期","三、世界500年大周期",
     ["迭代","周期本质"], 4),
    ("500-cycle-logic",          "social",    "社会逻辑", "500年大周期","四、世界统治霸权",
     ["周期循环","霸权逻辑"], 4),
    ("500-management",           "social",    "社会逻辑", "500年大周期","五、从管理维度",
     ["管理维度","大国周期"], 4),
    ("500-industry",             "social",    "社会逻辑", "500年大周期","六、500年大周期产业维度",
     ["产业维度","预测"], 4),
    ("500-core-hegemony",       "social",    "社会逻辑", "500年大周期","七、核心霸权周期",
     ["核心霸权","预测"], 5),
    ("500-france1",             "social",    "社会逻辑", "500年大周期","九、法国为什么没有崛起",
     ["法国","霸权"], 3),
    ("500-france2",             "social",    "社会逻辑", "500年大周期","十、法国没有成为霸主",
     ["法国","霸主"], 3),
    ("500-china-us",            "social",    "社会逻辑", "500年大周期","十一、中美未来争霸",
     ["中美","争霸","未来"], 5),
    ("500-key-nodes",           "social",    "社会逻辑", "500年大周期","十二、500年霸权周期重要节点",
     ["重要节点","霸权周期"], 4),
    ("500-five-dimensions",      "social",    "社会逻辑", "500年大周期","十三、总结世界大周围",
     ["五维霸权","总结"], 5),
    ("500-control-system",       "social",    "社会逻辑", "500年大周期","十四、全球霸权控制体系",
     ["霸权控制","全球体系"], 4),
    ("500-three-layer",          "social",    "社会逻辑", "500年大周期","十五、三层霸权模型图解",
     ["三层模型","霸权图解"], 4),
    ("500-moc",                 "social",    "社会逻辑", "500年大周期","MOC-500年全球大周期全景图",
     ["MOC","全景图"], 3),
    ("500-germany",             "social",    "社会逻辑", "500年大周期","八、德国没有崛起的原因",
     ["德国","崛起","霸权"], 3),
    ("us-strategy-dollar",       "social",    "社会逻辑", "全球地缘",   "美国搅动全球局势的战略与美元周期",
     ["美国","美元","地缘"], 5),
    ("us-global-looting",       "social",    "社会逻辑", "全球地缘",   "美国全球掠夺",
     ["美国","掠夺","全球"], 4),
    ("us-2026-policy",          "social",    "社会逻辑", "全球地缘",   "2026美国对外政策",
     ["美国","2026","对外政策"], 4),
    ("us-2017-2026-sanctions", "social",    "社会逻辑", "全球地缘",   "20017-2026美国对外制裁",
     ["美国","制裁","2017-2026"], 3),
    ("china-astock",            "social",    "社会逻辑", "产业经济",   "中国A股资产分析",
     ["A股","资产结构","中国股市"], 5),

    # 🧘 思想与修行
    ("human-essence",           "practice",   "思想与修行", "人的本质",   "1-人的本质",
     ["人的本质","人性","修身"], 5),
    ("one-thought-flower",       "practice",   "思想与修行", "心性修养", "8-一念花开",
     ["一念花开","心性","修行"], 4),
    ("inner-sage-outer-king",   "practice",   "思想与修行", "内圣外王", "01-内圣外王的核心思想",
     ["内圣外王","儒家","修身"], 5),
    ("inner-sage-dao",          "practice",   "思想与修行", "内圣外王", "02-内圣外王儒道区别",
     ["儒道","内圣外王","区别"], 4),
    ("inner-sage-laozi",        "practice",   "思想与修行", "内圣外王", "03-从",
     ["老子","内圣外王","道家"], 4),
    ("inner-sage-mind-form",     "practice",   "思想与修行", "内圣外王", "04-从",
     ["心相一体","内圣外王"], 4),
    ("nature-form-equal-practice","practice",   "思想与修行", "处世实践", "9-世界是虚妄的本质",
     ["性相不二","处世","实践"], 4),
    ("dou-dou-core",            "practice",   "思想与修行", "文化修行", "解读豆豆三部曲核心思想",
     ["豆豆三部曲","文化","修行"], 3),
    ("dou-dou-meaning",         "practice",   "思想与修行", "文化修行", "豆豆三部曲想表达什么",
     ["豆豆三部曲","文化"], 3),
]


def find_file(glob_fragment, vault_root):
    """在 vault 中递归搜索包含 glob_fragment 的 .md 文件，返回第一个匹配"""
    candidates = []
    for p in vault_root.rglob("*.md"):
        if glob_fragment in p.name:
            candidates.append(p)
    if candidates:
        # 优先返回最短路径匹配（最精确）
        candidates.sort(key=lambda p: len(p.name))
        return str(candidates[0].relative_to(vault_root))
    return None


def read_file(rel_path):
    try:
        with open(vault / rel_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️  读取失败: {rel_path} -> {e}")
        return ""


def clean_md(text):
    text = re.sub(r'^---\n.*?\n---', '', text, flags=re.DOTALL)
    text = re.sub(r'!\[$$.*?$$\]\(.*?\)', '', text)
    text = re.sub(r'#\d+ ', '# ', text)
    return text.strip()


def extract_title(content, fallback):
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def file_mtime(rel_path):
    try:
        ts = os.path.getmtime(vault / rel_path)
        return datetime.fromtimestamp(ts).strftime('%Y-%m')
    except:
        return '2026-06'


# ── 主流程 ─────────────────────────────────────────
vault = VAULT
print(f"🔍 Vault: {VAULT}")

articles = []
not_found = []

for (aid, pillar, category, subcategory, glob_frag, tags, importance) in ARTICLES_SPEC:
    rel = find_file(glob_frag, vault)
    if not rel:
        not_found.append((aid, glob_frag))
        print(f"  ❌ 未找到: [{aid}] {glob_frag}")
        continue

    content = read_file(rel)
    if not content:
        print(f"  ⚠️  空内容: {rel}")
        continue

    title    = extract_title(content, aid)
    date_str = file_mtime(rel)
    summary  = content[:200].replace('\n', ' ').replace('#', '')[:120]

    articles.append({
        "id":           aid,
        "pillar":       pillar,
        "category":     category,
        "subcategory":  subcategory,
        "title":        title,
        "date":         date_str,
        "summary":      summary + "...",
        "tags":         tags,
        "importance":   importance,
        "content":      clean_md(content),
        "wordCount":    len(content),
        "sourcePath":   rel,
    })
    print(f"  ✅ {aid}: {title[:35]} ({len(content)}字)")

if not_found:
    print(f"\n⚠️  未匹配到 {len(not_found)} 篇：")
    for (aid, frag) in not_found:
        print(f"     {aid} <- {frag}")

out = {
    "meta": {
        "version":   "1.0",
        "generated": datetime.now().isoformat(),
        "count":     len(articles)
    },
    "articles": articles
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# Also generate articles.js for script-tag loading (compatible with file:// protocol)
js_data = json.dumps(out, ensure_ascii=False, indent=2)
with open("articles.js", "w", encoding="utf-8") as f:
    f.write(f"window.__ARTICLES__ = {js_data};")

size_kb = os.path.getsize(OUT) // 1024
js_size_kb = os.path.getsize("articles.js") // 1024
print(f"\n✅ 完成！共 {len(articles)} 篇文章 → {OUT}")
print(f"   articles.json: {size_kb} KB")
print(f"   articles.js: {js_size_kb} KB")
