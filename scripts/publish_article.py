#!/usr/bin/env python3
"""
骆驼商业本质 — 文章发布脚本
用法: python3 scripts/publish_article.py /path/to/article.md

流程:
  1. 读取 Obsidian Markdown 文章
  2. 转换图片语法 ![[image]] → ![desc](data/images/...)
  3. 复制图片到 data/images/
  4. 生成 article ID 和 short_id (md5[:6])
  5. 插入元数据到 site-data.js
  6. 插入正文到 article-content.js
  7. 验证 JS 语法
  8. 提示手动 git add && commit && push
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DATA_JS = REPO_ROOT / "site-data.js"
ARTICLE_CONTENT_JS = REPO_ROOT / "article-content.js"
DATA_IMAGES = REPO_ROOT / "data" / "images"
OBSIDIAN_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian"
ATTACHMENTS_DIR = OBSIDIAN_VAULT / "附件"

PILLAR_MAP = {
    "01-哲学思想研究": "worldview",
    "02-经济研究": "social",
    "03-商业项目": "social",
    "04-中国经济观察": "social",
}


def find_article(md_path):
    """查找文章文件"""
    p = Path(md_path)
    if p.exists():
        return p
    vault = OBSIDIAN_VAULT / "Andy知识库"
    matches = list(vault.rglob(f"*{md_path}*"))
    if matches:
        return matches[0]
    print(f"ERROR: 找不到文章: {md_path}")
    sys.exit(1)


def parse_category_from_path(md_path):
    """从文件路径解析 category 和 subcategory"""
    parts = md_path.parts
    category = None
    subcategory = None
    for part in parts:
        if re.match(r'^[一二三四五六七八九十]+、', part):
            if category is None:
                category = part
            elif subcategory is None:
                subcategory = part
    if not category:
        print(f"ERROR: 无法从路径解析分类: {md_path}")
        sys.exit(1)
    return category, subcategory or ""


def detect_pillar(category):
    """根据分类检测 pillar"""
    for key, pillar in PILLAR_MAP.items():
        if key in category:
            return pillar
    print(f"WARNING: 无法自动检测 pillar，默认用 social")
    return "social"


def make_article_id(category, subcategory, filename):
    """生成文章 ID 和 short_id"""
    name = filename.replace(".md", "")
    parts = [category, subcategory, name] if subcategory else [category, name]
    id_base = "-".join(parts)
    short_id = hashlib.md5(id_base.encode("utf-8")).hexdigest()[:6]
    return f"{id_base}-{short_id}", short_id


def convert_images(content, md_path):
    """转换 Obsidian 图片语法 ![[image]] → ![desc](data/images/...)"""
    def replace_embed(m):
        filename = m.group(1)
        desc = m.group(2) if m.group(2) else filename

        src = ATTACHMENTS_DIR / filename
        if not src.exists():
            matches = list(OBSIDIAN_VAULT.rglob(filename))
            if matches:
                src = matches[0]
            else:
                print(f"  WARNING: 找不到图片 {filename}，保留原语法")
                return m.group(0)

        dest_name = filename
        dest = DATA_IMAGES / dest_name
        if not dest.exists():
            DATA_IMAGES.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"  图片复制: {filename}")
        else:
            print(f"  图片已存在，跳过: {filename}")

        return f"![{desc}](data/images/{dest_name})"

    pattern = r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
    return re.sub(pattern, replace_embed, content)


def add_byline(content):
    """在标题后添加作者署名"""
    title_match = re.match(r'^(# .+)$', content, re.MULTILINE)
    if title_match:
        today = datetime.now().strftime("%Y年%m月%d日")
        byline = f"\n\n**作者：骆新中-骆驼商业本质**　|　{today}"
        insert_pos = title_match.end()
        content = content[:insert_pos] + byline + content[insert_pos:]
    return content


def find_obsidian_summary(md_path):
    """从 frontmatter 或第一段提取 summary"""
    text = md_path.read_text(encoding="utf-8")
    fm_match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.split("\n"):
            if line.strip().startswith("summary:"):
                return line.split(":", 1)[1].strip()
    today = datetime.now().strftime("%Y年%m月%d日")
    return f"作者：骆新中-骆驼商业本质 | {today}"


def add_to_site_data(article_id, short_id, pillar, category, subcategory, title, date, summary, importance=3):
    """在 site-data.js 中添加文章元数据"""
    text = SITE_DATA_JS.read_text(encoding="utf-8")

    if short_id in text:
        print(f"  WARNING: short_id {short_id} 已存在于 site-data.js，跳过")
        return False

    new_entry = json.dumps({
        "id": article_id,
        "pillar": pillar,
        "category": category,
        "subcategory": subcategory,
        "title": title,
        "date": date,
        "summary": summary,
        "importance": importance,
        "short_id": short_id
    }, ensure_ascii=False, indent=6)

    new_entry = "    " + new_entry.replace('\n', '\n    ') + ","

    marker = "  ]\n};"
    if "  ]\n};" in text:
        text = text.replace("  ]\n};", new_entry + "\n  ]\n};", 1)
        SITE_DATA_JS.write_text(text, encoding="utf-8")
        print(f"  site-data.js: 已添加 {short_id}")
        return True
    else:
        print("  ERROR: 找不到 site-data.js 的插入点")
        return False


def add_to_article_content(article_id, content):
    """在 article-content.js 中添加文章正文"""
    text = ARTICLE_CONTENT_JS.read_text(encoding="utf-8")

    if article_id in text:
        print(f"  WARNING: {article_id} 已存在于 article-content.js，跳过")
        return False

    js_string = json.dumps(content, ensure_ascii=False)
    new_line = f'  __D["{article_id}"] = {js_string};\n'

    marker = "window.__ARTICLE_CONTENT__ = __D;"
    if marker in text:
        text = text.replace(marker, new_line + marker)
        ARTICLE_CONTENT_JS.write_text(text, encoding="utf-8")
        print(f"  article-content.js: 已添加 {len(content)} 字")
        return True
    else:
        print("  ERROR: 找不到 article-content.js 的插入点")
        return False


def validate_js(filepath):
    """验证 JS 语法"""
    result = subprocess.run(
        ["node", "-e", f"const fs=require('fs');const vm=require('vm');try{{vm.runInNewContext(fs.readFileSync('{filepath}','utf-8'),{{window:{{}}}});console.log('OK')}}catch(e){{console.error(e.message);process.exit(1)}}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  语法验证通过: {filepath.name}")
        return True
    else:
        print(f"  语法错误: {result.stderr}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/publish_article.py /path/to/article.md")
        print("示例: python3 scripts/publish_article.py 09-美元资本流动（三流）")
        sys.exit(1)

    md_path = find_article(sys.argv[1])
    print(f"\n=== 发布文章 ===")
    print(f"文件: {md_path}")

    category, subcategory = parse_category_from_path(md_path)
    pillar = detect_pillar(category)
    title = md_path.name.replace(".md", "")
    article_id, short_id = make_article_id(category, subcategory, md_path.name)
    date = datetime.now().strftime("%Y-%m-%d")
    summary = find_obsidian_summary(md_path)

    print(f"分类: {category} > {subcategory}")
    print(f"Pillar: {pillar}")
    print(f"标题: {title}")
    print(f"ID: {article_id}")
    print(f"Short ID: {short_id}")
    print(f"日期: {date}")

    content = md_path.read_text(encoding="utf-8")
    content = re.sub(r'^---\n.*?\n---\n*', '', content, flags=re.DOTALL)
    content = add_byline(content)
    content = convert_images(content, md_path)

    print(f"\n--- 写入 site-data.js ---")
    add_to_site_data(article_id, short_id, pillar, category, subcategory, title, date, summary)

    print(f"\n--- 写入 article-content.js ---")
    add_to_article_content(article_id, content)

    print(f"\n--- 语法验证 ---")
    ok1 = validate_js(SITE_DATA_JS)
    ok2 = validate_js(ARTICLE_CONTENT_JS)

    if ok1 and ok2:
        print(f"\n=== 发布准备完成 ===")
        print(f"下一步:")
        print(f"  1. 浏览器打开 social.html 预览 (Cmd+Shift+R)")
        print(f"  2. git add site-data.js article-content.js data/images/")
        print(f"  3. git commit -m '新增 {title}'")
        print(f"  4. git push")
        print(f"\n如需回滚:")
        print(f"  git checkout -- site-data.js article-content.js")
    else:
        print(f"\n!!! 语法验证失败，请检查文件 !!!")
        print(f"回滚: git checkout -- site-data.js article-content.js")
        sys.exit(1)


if __name__ == "__main__":
    main()
