#!/usr/bin/env python3
"""
更新指定文章：从 Obsidian 读取最新 Markdown，清洗后写入网站 JSON 和 site-data.js
"""

import os, re, json, hashlib, shutil
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================
OBSIDIAN_BASE = "/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian/Andy知识库"
SITE_DIR = "/Users/luoclaw/WorkBuddy/骆驼商业本质网站"

# ============================================================
# 内容清洗（同 generate_site_data.py）
# ============================================================
def remove_frontmatter(content):
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    content = content.lstrip('\n')
    return content

def convert_wikilinks(content):
    content = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', content)
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    return content

def remove_embed_links(content):
    # 1. Convert Obsidian image embeds ![[file.ext|size]] → Markdown ![](data/images/file.ext)
    content = re.sub(r'!\[\[([^\]]+\.\w+)(?:\|(\d+))?\]\]', r'![](data/images/\1)', content)
    # 2. Remove remaining non-image embeds
    content = re.sub(r'^!\[\[.*?\]\]\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'!\[\[.*?\]\]', '', content)
    return content

def remove_inline_tags(content):
    lines = content.split('\n')
    result = []
    for line in lines:
        if re.match(r'^\s*(#[\w\u4e00-\u9fff]+(\s+#[\w\u4e00-\u9fff]+)*)\s*$', line):
            continue
        if re.match(r'^\s*#{1,6}\s', line):
            result.append(line)
            continue
        line = re.sub(r'\s*#[\w\u4e00-\u9fff]+', '', line)
        result.append(line)
    return '\n'.join(result)

def remove_font_tags(content):
    content = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', content, flags=re.DOTALL)
    return content

def remove_navigation_lines(content):
    content = re.sub(r'^>\s*🔗.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^关联：\s*\[\[.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

def remove_obsidian_properties(content):
    property_fields = ['tags:', 'aliases:', 'created:', 'updated:', 'source:', 'source_note_id:', 'status:']
    lines = content.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        skip = False
        for field in property_fields:
            if stripped.startswith(field):
                skip = True
                break
        if not skip:
            result.append(line)
    return '\n'.join(result)

def remove_callout_syntax(content):
    content = re.sub(r'^>\s*\[!\w+\]\s*(.*)', r'> **\1**', content, flags=re.MULTILINE)
    return content

def remove_standalone_tag_words(content):
    lines = content.split('\n')
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not re.match(r'^#{1,6}\s', stripped) and not re.match(r'^[-*|>]', stripped):
            words = stripped.split()
            if 1 <= len(words) <= 3 and all(len(w) <= 8 for w in words):
                if i == 0 or (i > 0 and lines[i-1].strip() == ''):
                    continue
        result.append(line)
    return '\n'.join(result)

def clean_content(raw_content):
    content = raw_content
    content = remove_frontmatter(content)
    content = remove_navigation_lines(content)
    content = convert_wikilinks(content)
    content = remove_embed_links(content)
    content = remove_inline_tags(content)
    content = remove_font_tags(content)
    content = remove_obsidian_properties(content)
    content = remove_callout_syntax(content)
    content = remove_standalone_tag_words(content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    return content

# ============================================================
# 文章映射：文件名 → (obsidian路径, website_json_id)
# ============================================================
ARTICLES = [
    # (文件名前缀, obsidian_md路径(相对OBSIDIAN_BASE), website_json_id)
    ("西游记01",
     "01-哲学思想研究/一、传统哲学研究/（二）、《西游记》哲学思想研究/01-西游记01-三阶段旅程探寻.md",
     "一、传统哲学研究-（三）、《西游记》哲学思想研究-01-西游记01-三阶段旅程探寻-951ee7"),

    ("06-四念处",
     "01-哲学思想研究/二、佛学思想研究/（一）、佛陀的核心思想/06-四念处：深度止观四念处的解析.md",
     "二、佛学思想研究-（一）、佛陀的核心思想-06-四念处：深度止观四念处的解析-b40aeb"),

    ("02-四禅八定",
     "01-哲学思想研究/二、佛学思想研究/（五）、止观禅定/02-四禅八定.md",
     "二、佛学思想研究-（五）、止观禅定-02-四禅八定-b6169e"),

    ("08-深度止观训练",
     "01-哲学思想研究/二、佛学思想研究/（五）、止观禅定/08-深度止观训练：观（毗婆舍那）的系统解析.md",
     "二、佛学思想研究-（五）、止观禅定-08-深度止观训练：观（毗婆舍那）的系统解析-bdc523"),

    ("01-觉～空～慈悲心",
     "01-哲学思想研究/二、佛学思想研究/（七）、心与识/01-觉～空～慈悲心.md",
     "二、佛学思想研究-（七）、心与识-01-觉～空～慈悲心-c872e9"),

    ("02-破分别心",
     "01-哲学思想研究/二、佛学思想研究/（七）、心与识/02-破分别心：直击\u201c比较\u201d分别心的核心.md",
     "二、佛学思想研究-（七）、心与识-02-破分别心：直击\"比较\"分别心的核心-a9aa3b"),

    ("04-分别心的底层逻辑",
     "01-哲学思想研究/二、佛学思想研究/（七）、心与识/04-分别心的底层逻辑：从凡夫境界到佛法修证.md",
     "二、佛学思想研究-（七）、心与识-04-分别心的底层逻辑：从凡夫境界到佛法修证-728968"),

    ("05-人心与 AI",
     "01-哲学思想研究/二、佛学思想研究/（七）、心与识/05-人心与 AI 的终极对照与修行破法.md",
     "二、佛学思想研究-（七）、心与识-05-人心与 AI 的终极对照与修行破法-e7540a"),

    ("08-观心的原理",
     "01-哲学思想研究/二、佛学思想研究/（七）、心与识/08-观心的原理-破心之道.md",
     "二、佛学思想研究-（七）、心与识-08-观心的原理-破心之道-907e89"),

    ("07-从三破法",
     "01-哲学思想研究/二、佛学思想研究/（八）、修行方法/07-从三破法到漏尽通的终极圆满之路.md",
     "二、佛学思想研究-（八）、修行方法-07-从三破法到漏尽通的终极圆满之路-234d26"),

    ("二、世界500年霸权",
     "02-经济研究/二、宏观经济研究/（一）、500年全球大周期/二、世界500年霸权\u201c模式更迭\u201d.md",
     "二、宏观经济研究-（一）、500年全球大周期-二、世界500年霸权\"模式更迭\"-1810e3"),

    ("五、从管理维度",
     "02-经济研究/二、宏观经济研究/（一）、500年全球大周期/五、从\u201c管理维度\u201d看世界大国周期迭代.md",
     "二、宏观经济研究-（一）、500年全球大周期-五、从\"管理维度\"看世界大国周期迭代-38e42b"),

    ("04-美国搅动",
     "02-经济研究/三、国际金融研究/（二）、美国研究/04-美国搅动全球局势的战略与美元周期.md",
     "三、国际金融研究-（二）、美国研究-04-美国搅动全球局势的战略与美元周期-6d7275"),

    ("02-人生价值放大模型",
     "02-经济研究/四、中国经济观察/（二）、商业模式/02-人生价值放大模型.md",
     "四、中国经济观察-（二）、商业模式-02-人生价值放大模型-684606"),

    ("02-中国主要朝代开国皇帝",
     "02-经济研究/一、经济史研究/（二）、中国历史研究/02-中国主要朝代开国皇帝一览表.md",
     "一、经济史研究-（二）、中国历史研究-02-中国主要朝代开国皇帝一览表-27b124"),

    ("03-中国300年",
     "02-经济研究/一、经济史研究/（二）、中国历史研究/03-中国 300 年一次的朝代更替的原因：.md",
     "一、经济史研究-（二）、中国历史研究-03-中国 300 年一次的朝代更替的原因：-819940"),

    ("06-从几次亚洲金融危机",
     "02-经济研究/一、经济史研究/（二）、中国历史研究/06-从几次亚洲金融危机，看经济发展的规律.md",
     "一、经济史研究-（二）、中国历史研究-06-从几次亚洲金融危机，看经济发展的规律-95948c"),

    ("03-美国打压遏制日本",
     "02-经济研究/一、经济史研究/（一）、世界历史研究/03-美国打压遏制日本发展的历史.md",
     "一、经济史研究-（一）、世界历史研究-03-美国打压遏制日本发展的历史-e47b44"),
]

def main():
    print("=" * 60)
    print("骆驼商业本质 — 文章批量更新脚本")
    print("=" * 60)
    print(f"📂 Obsidian 源: {OBSIDIAN_BASE}")

    total = len(ARTICLES)
    success = 0
    errors = []

    for label, obsidian_rel, article_id in ARTICLES:
        obsidian_path = os.path.join(OBSIDIAN_BASE, obsidian_rel)
        json_path = os.path.join(SITE_DIR, "data", "articles", f"{article_id}.json")

        print(f"\n{'='*50}")
        print(f"📄 {label}")
        print(f"   Obsidian: {obsidian_rel}")

        # Step 1: Read Obsidian markdown
        if not os.path.isfile(obsidian_path):
            errors.append(f"{label}: Obsidian 文件不存在: {obsidian_path}")
            print(f"   ❌ 文件不存在！")
            continue

        try:
            with open(obsidian_path, 'r', encoding='utf-8') as f:
                raw = f.read()
        except Exception as e:
            errors.append(f"{label}: 读取失败: {e}")
            continue

        # Get file modification time
        mtime = os.path.getmtime(obsidian_path)
        date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

        # Step 2: Clean content
        cleaned = clean_content(raw)
        print(f"   清洗前: {len(raw)} 字符 → 清洗后: {len(cleaned)} 字符")

        # Step 3: Write JSON
        output = {"id": article_id, "content": cleaned}
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False)
            print(f"   ✅ JSON 已更新: data/articles/{article_id}.json")
        except Exception as e:
            errors.append(f"{label}: 写入 JSON 失败: {e}")
            continue

        success += 1

    # ============================================================
    # 更新 site-data.js 中的 date 字段
    # ============================================================
    print(f"\n{'='*50}")
    print("📝 更新 site-data.js 中的日期...")

    site_data_path = os.path.join(SITE_DIR, "site-data.js")
    try:
        with open(site_data_path, 'r', encoding='utf-8') as f:
            site_data_content = f.read()
    except Exception as e:
        print(f"   ❌ 读取 site-data.js 失败: {e}")
        errors.append(f"读取 site-data.js 失败: {e}")

    # Parse the JSON portion: extract the object between window.__ARTICLES__ =  and the trailing ;
    match = re.search(r'window\.__ARTICLES__\s*=\s*(\{.*?\});\s*$', site_data_content, re.DOTALL)
    if not match:
        print(f"   ❌ 无法解析 site-data.js 中的 JSON 数据")
        errors.append("无法解析 site-data.js")
    else:
        data = json.loads(match.group(1))

        # Update dates for our articles
        article_dates = {}
        for label, obsidian_rel, article_id in ARTICLES:
            obsidian_path = os.path.join(OBSIDIAN_BASE, obsidian_rel)
            if os.path.isfile(obsidian_path):
                mtime = os.path.getmtime(obsidian_path)
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                article_dates[article_id] = date_str

        updated_count = 0
        for a in data["articles"]:
            if a["id"] in article_dates:
                old_date = a.get("date", "")
                new_date = article_dates[a["id"]]
                if old_date != new_date:
                    print(f"   📅 {a['title']}: {old_date} → {new_date}")
                    a["date"] = new_date
                    updated_count += 1

        # Write back
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        new_site_data = f"// ============================================================\n// 骆驼商业本质 — 网站数据（静态维护，不自动同步）\n// ============================================================\n// 本文件是网站唯一数据源，包含文章元数据 + 模块结构。\n// 修改方法：直接编辑此文件，或重新运行 generate_site_data.py\n//\n// 相关文件：\n//   site-data.js         ← 你正在编辑的文件（元数据 + 模块结构）\n//   article-content.js   ← 文章正文（按ID索引）\n// ============================================================\n\nwindow.__ARTICLES__ = {json_str};\n"

        with open(site_data_path, 'w', encoding='utf-8') as f:
            f.write(new_site_data)
        print(f"   ✅ site-data.js 已更新，{updated_count} 篇文章日期已同步")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 统计:")
    print(f"   总文章: {total}")
    print(f"   成功更新: {success}")
    print(f"   错误数: {len(errors)}")
    if errors:
        print(f"\n❌ 错误详情:")
        for e in errors:
            print(f"   - {e}")

    print(f"\n{'='*60}")
    print(f"🏁 全部完成！")


if __name__ == "__main__":
    main()
