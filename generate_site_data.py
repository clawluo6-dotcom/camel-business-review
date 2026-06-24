#!/usr/bin/env python3
"""
generate_site_data.py — 从 Obsidian 目录重新生成网站数据

规则：
  - 目录名：完全照抄 Obsidian 文件夹名（含序号、书名号、后缀）
  - 文章标题：完全照抄文件名（去掉 .md 后缀，保留序号）
  - 文章内容：保留原文，只去掉 Obsidian 专属元素
  - 不改任何 HTML/CSS/JS 文件

只修改的文件：site-data.js、article-content.js
"""

import os
import re
import subprocess
import sys
import json
import hashlib
from pathlib import Path

# ============================================================
# 配置
# ============================================================
OBSIDIAN_BASE = "/Users/luo/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian/Andy知识库"
OUTPUT_DIR = "/Users/luo/WorkBuddy/成果库/骆驼商业本质"

# 指定要扫描的新目录（带序号的）
# 结构: pillar -> module_dir -> [subcategory_dirs or None]
DIRECTORY_MAP = {
    "worldview": {
        "一、传统哲学研究": {
            "dir": "01-哲学思想研究/一、传统哲学研究",
            "subcategories": {
                "（一）、《内圣外王》哲学分析": "（一）、《内圣外王》哲学分析",
                "（二）、《西游记》哲学思想研究": "（二）、《西游记》哲学思想研究",
                "（三）、《豆豆三部曲》哲学思想": "（三）、《豆豆三部曲》哲学思想",
                "（四）、《世界的真相》感悟": "（四）、《世界的真相》感悟",
                "（五）、杂篇": "（五）、杂篇",
            }
        },
        "二、佛学思想研究": {
            "dir": "01-哲学思想研究/二、佛学思想研究",
            "subcategories": {
                "（一）、佛陀的核心思想": "（一）、佛陀的核心思想",
                "（二）、佛教思想": "（二）、佛教思想",
                "（三）、金刚经": "（三）、金刚经",
                "（四）、中观唯识": "（四）、中观唯识",
                "（五）、止观禅定": "（五）、止观禅定",
                "（六）、禅宗六祖": "（六）、禅宗六祖",
                "（七）、心与识": "（七）、心与识",
                "（八）、修行方法": "（八）、修行方法",
            }
        },
        "三、儒家思想研究": {
            "dir": "01-哲学思想研究/三、儒家思想研究",
            "subcategories": None  # 无子目录，文章直接在模块下
        },
        "四、自然哲学研究": {
            "dir": "01-哲学思想研究/四、自然哲学研究",
            "subcategories": None
        },
    },
    "social": {
        "一、经济史研究": {
            "dir": "02-经济研究/一、经济史研究",
            "subcategories": {
                "（一）、世界历史研究": "（一）、世界历史研究",
                "（二）、中国历史研究": "（二）、中国历史研究",
            }
        },
        "二、宏观经济研究": {
            "dir": "02-经济研究/二、宏观经济研究",
            "subcategories": {
                "（一）、500年全球大周期": "（一）、500年全球大周期",
                "（二）、经济周期": "（二）、经济周期",
            }
        },
        "三、国际金融研究": {
            "dir": "02-经济研究/三、国际金融研究",
            "subcategories": {
                "（一）、国际金融": "（一）、国际金融",
                "（二）、美国研究": "（二）、美国研究",
            }
        },
        "四、中国经济观察": {
            "dir": "02-经济研究/四、中国经济观察",
            "subcategories": {
                "（一）、经济观察": "（一）、经济观察",
                "（二）、商业模式": "（二）、商业模式",
            }
        },
    }
}

# 图标映射
ICON_MAP = {
    "一、传统哲学研究": "📜",
    "二、佛学思想研究": "🪷",
    "三、儒家思想研究": "🎓",
    "四、自然哲学研究": "🔬",
    "一、经济史研究": "📜",
    "二、宏观经济研究": "📊",
    "三、国际金融研究": "🌐",
    "四、中国经济观察": "🇨🇳",
}

# 跳过的文件模式
SKIP_PATTERNS = [
    re.compile(r'^MOC-', re.IGNORECASE),
    re.compile(r'^\.'),  # 隐藏文件
]


# ============================================================
# 内容清洗函数
# ============================================================

def remove_frontmatter(content):
    """去掉 YAML frontmatter（--- 到 --- 之间的内容）"""
    # 只匹配文件开头的 frontmatter
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    # 有时 frontmatter 后面还有空行
    content = content.lstrip('\n')
    return content


def convert_wikilinks(content):
    """转换双向链接 [[xxx|显示文本]] → 显示文本，[[xxx]] → xxx"""
    # [[xxx|显示文本]] → 显示文本
    content = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', content)
    # [[xxx]] → xxx
    content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)
    return content


def remove_embed_links(content):
    """删除嵌入链接 ![[...]]"""
    # 删除整行如果只有嵌入链接
    content = re.sub(r'^!\[\[.*?\]\]\s*$', '', content, flags=re.MULTILINE)
    # 行内的也删除
    content = re.sub(r'!\[\[.*?\]\]', '', content)
    return content


def remove_inline_tags(content):
    """删除行内标签 #标签（但不删除 markdown 标题的 #）"""
    lines = content.split('\n')
    result = []
    for line in lines:
        # 如果整行只有标签，删除整行
        if re.match(r'^\s*(#[\w\u4e00-\u9fff]+(\s+#[\w\u4e00-\u9fff]+)*)\s*$', line):
            continue
        # 行内标签（不在标题行里）：#标签 → 删除
        # 先标记标题行（以 # 开头的），不处理
        if re.match(r'^\s*#{1,6}\s', line):
            result.append(line)
            continue
        # 非标题行，去掉 #标签
        line = re.sub(r'\s*#[\w\u4e00-\u9fff]+', '', line)
        result.append(line)
    return '\n'.join(result)


def remove_font_tags(content):
    """清理 <font> 标签：<font color="...">文本</font> → 文本"""
    content = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', content, flags=re.DOTALL)
    return content


def remove_navigation_lines(content):
    """删除系列导航行（> 🔗 开头的引用块）"""
    # 删除 > 🔗 **系列导航：** 整行
    content = re.sub(r'^>\s*🔗.*$', '', content, flags=re.MULTILINE)
    # 删除 > 🔗 **跨领域关联：** 整行
    content = re.sub(r'^>\s*🔗.*$', '', content, flags=re.MULTILINE)
    # 清理关联行（只有双链的行）
    content = re.sub(r'^关联：\s*\[\[.*$', '', content, flags=re.MULTILINE)
    # 清理空行残留
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


def remove_obsidian_properties(content):
    """删除行内的 Obsidian 属性字段"""
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
    """转换 Obsidian Callout 语法：> [!type] 标题 → > **标题**"""
    # > [!summary] 核心观点 → > **核心观点**
    content = re.sub(r'^>\s*\[!\w+\]\s*(.*)', r'> **\1**', content, flags=re.MULTILINE)
    return content


def remove_standalone_tag_words(content):
    """删除双链转换后残留的独立标签词行（如 '思考 哲学' 单独一行）"""
    lines = content.split('\n')
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 如果整行只有1-3个短词（没有标点、没有标题标记），且不是第一行（可能是标题下的空行）
        # 这类行是 [[思考]] [[哲学]] 被转换后的残留
        if stripped and not re.match(r'^#{1,6}\s', stripped) and not re.match(r'^[-*|>]', stripped):
            # 只包含短词和空格的行（1-3个词，每个词2-6个字）
            words = stripped.split()
            if 1 <= len(words) <= 3 and all(len(w) <= 8 for w in words):
                # 检查是不是有意义的内容（如果上一行是标题，下一行是正文，这行可能是无意义的标签残留）
                # 安全起见，只在行首出现时删除
                if i == 0 or (i > 0 and lines[i-1].strip() == ''):
                    continue
        result.append(line)
    return '\n'.join(result)


def clean_content(raw_content):
    """完整的清洗流程"""
    content = raw_content

    # 1. 去掉 YAML frontmatter
    content = remove_frontmatter(content)

    # 2. 删除系列导航行
    content = remove_navigation_lines(content)

    # 3. 转换双向链接 [[...]]
    content = convert_wikilinks(content)

    # 4. 删除嵌入链接 ![[...]]
    content = remove_embed_links(content)

    # 5. 删除行内标签
    content = remove_inline_tags(content)

    # 6. 清理 <font> 标签
    content = remove_font_tags(content)

    # 7. 删除行内属性字段
    content = remove_obsidian_properties(content)

    # 8. 转换 Callout 语法
    content = remove_callout_syntax(content)

    # 9. 删除双链转换后残留的独立标签词行
    content = remove_standalone_tag_words(content)

    # 10. 清理多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content


def extract_summary(content, max_length=120):
    """从文章内容中提取摘要（取第一段前N个字符）"""
    if not content:
        return ""
    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()
        # 跳过空行、标题行、引用行
        if not stripped or stripped.startswith('#') or stripped.startswith('>'):
            continue
        # 去掉 Markdown 格式符号
        summary = re.sub(r'[*_`#>\-\[\]]', '', stripped)
        summary = re.sub(r'\s+', ' ', summary).strip()
        if summary:
            return summary[:max_length]
    return ""


def should_skip(filename):
    """判断是否应该跳过此文件"""
    for pattern in SKIP_PATTERNS:
        if pattern.search(filename):
            return True
    if not filename.endswith('.md'):
        return True
    return False


def make_article_id(category, subcategory, filename):
    """生成文章 ID：category-subcategory-filename-hash"""
    # 去掉 .md 后缀
    name = filename.replace('.md', '')
    # 构造 ID 的 key 部分
    parts = [category, subcategory, name] if subcategory else [category, name]
    id_base = '-'.join(parts)
    # 加 hash 防止重复
    hash_val = hashlib.md5(id_base.encode('utf-8')).hexdigest()[:6]
    return f"{id_base}-{hash_val}"


def extract_title(filename):
    """从文件名提取标题：去掉 .md 后缀，其他完全保留（含序号）"""
    return filename.replace('.md', '')


def read_file_safe(filepath):
    """安全读取文件，处理编码问题"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read()
        except:
            return ""


def get_file_modified_time(filepath):
    """获取文件修改时间，格式 YYYY-MM-DD"""
    try:
        mtime = os.path.getmtime(filepath)
        from datetime import datetime
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except:
        return ""


# ============================================================
# 主流程
# ============================================================

def scan_directory():
    """扫描 Obsidian 目录，生成文章数据"""
    articles = []
    article_contents = {}
    pillar_modules = {"worldview": [], "social": []}
    total = 0
    skipped = 0

    for pillar, modules in DIRECTORY_MAP.items():
        for module_name, module_config in modules.items():
            module_dir = os.path.join(OBSIDIAN_BASE, module_config["dir"])

            # 构建 pillarModules 条目
            icon = ICON_MAP.get(module_name, "📄")
            subcat_list = []

            subcategories = module_config["subcategories"]

            if subcategories:
                # 有子目录
                for subcat_name, subcat_dir_name in subcategories.items():
                    subcat_list.append(subcat_name)
                    subcat_path = os.path.join(module_dir, subcat_dir_name)

                    if not os.path.isdir(subcat_path):
                        print(f"  ⚠️ 子目录不存在: {subcat_path}")
                        continue

                    # 扫描子目录下的 .md 文件
                    files = sorted(os.listdir(subcat_path))
                    for filename in files:
                        if should_skip(filename):
                            skipped += 1
                            continue

                        filepath = os.path.join(subcat_path, filename)
                        if not os.path.isfile(filepath):
                            continue

                        title = extract_title(filename)
                        article_id = make_article_id(module_name, subcat_name, filename)
                        date = get_file_modified_time(filepath)
                        raw_content = read_file_safe(filepath)
                        cleaned = clean_content(raw_content)
                        summary = extract_summary(cleaned)

                        articles.append({
                            "id": article_id,
                            "pillar": pillar,
                            "category": module_name,
                            "subcategory": subcat_name,
                            "title": title,
                            "date": date,
                            "summary": summary,
                            "importance": 3,
                        })
                        article_contents[article_id] = cleaned
                        total += 1
            else:
                # 无子目录，文章直接在模块下
                subcat_list.append(module_name)

                if not os.path.isdir(module_dir):
                    print(f"  ⚠️ 模块目录不存在: {module_dir}")
                    continue

                files = sorted(os.listdir(module_dir))
                for filename in files:
                    if should_skip(filename):
                        skipped += 1
                        continue

                    filepath = os.path.join(module_dir, filename)
                    if not os.path.isfile(filepath):
                        continue

                    title = extract_title(filename)
                    article_id = make_article_id(module_name, "", filename)
                    date = get_file_modified_time(filepath)
                    raw_content = read_file_safe(filepath)
                    cleaned = clean_content(raw_content)
                    summary = extract_summary(cleaned)

                    articles.append({
                            "id": article_id,
                            "pillar": pillar,
                            "category": module_name,
                            "subcategory": module_name,
                            "title": title,
                            "date": date,
                            "summary": summary,
                            "importance": 3,
                        })
                    article_contents[article_id] = cleaned
                    total += 1

            pillar_modules[pillar].append({
                "module": module_name,
                "icon": icon,
                "subcategories": subcat_list,
            })

    print(f"\n✅ 扫描完成: {total} 篇文章, 跳过 {skipped} 个文件")
    return articles, article_contents, pillar_modules


def chinese_numeral_sort_key(title):
    """提取标题中的中文数字序号用于排序，'一'→1、'十二'→12"""
    cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    m = __import__('re').match(r'^([一二三四五六七八九十]+)[、，,\s·]*', title)
    if m:
        s = m.group(1)
        if len(s) == 1:
            return cn.get(s, 0)
        if len(s) == 2:
            if s[0] == '十':
                return 10 + cn.get(s[1], 0)
            if s[1] == '十':
                return cn.get(s[0], 0) * 10
        if len(s) == 3 and s[1] == '十':
            return cn.get(s[0], 0) * 10 + cn.get(s[2], 0)
    return 999  # 无中文序号时排最后


def generate_site_data_js(articles, pillar_modules):
    """生成 site-data.js"""
    # 按 category -> subcategory -> 中文数字序号 排序
    articles.sort(key=lambda a: (a["category"], a["subcategory"], chinese_numeral_sort_key(a["title"])))

    header = '''// ============================================================
// 骆驼商业本质 — 网站数据（静态维护，不自动同步）
// ============================================================
// 本文件是网站唯一数据源，包含文章元数据 + 模块结构。
// 修改方法：直接编辑此文件，或重新运行 generate_site_data.py
//
// 相关文件：
//   site-data.js         ← 你正在编辑的文件（元数据 + 模块结构）
//   article-content.js   ← 文章正文（按ID索引）
// ============================================================
'''

    data = {
        "pillarModules": pillar_modules,
        "articles": articles,
    }

    # 手动格式化 JSON，确保中文可读
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    js_content = f'{header}window.__ARTICLES__ = {json_str};\n'
    return js_content


def generate_article_content_js(article_contents):
    """生成 article-content.js — 逐条赋值，单篇异常不影响整体"""
    header = '''// ============================================================
// 骆驼商业本质 — 文章正文数据（静态维护，不自动同步）
// ============================================================
// 本文件包含所有文章正文，按ID索引。
// 仅 article.html 加载此文件。
// ============================================================
'''

    entries = []
    failed = []
    for aid, content in article_contents.items():
        try:
            content_json = json.dumps(content, ensure_ascii=False)
            entries.append(f'  __D[{json.dumps(aid, ensure_ascii=False)}] = {content_json};')
        except Exception as e:
            failed.append(aid)
            print(f'  ⚠️ 跳过问题文章: {aid} ({e})')

    # IIFE 隔离：单条赋值出错不影响 window.__ARTICLE_CONTENT__ 的最终赋值
    body = '\n'.join(entries)
    js_content = f'''{header}(function() {{
var __D = {{}};
{body}
window.__ARTICLE_CONTENT__ = __D;
}})();
'''
    if failed:
        print(f'  ⚠️ 共跳过 {len(failed)} 篇问题文章')
    return js_content


def main():
    print("=" * 60)
    print("骆驼商业本质 — 数据生成脚本")
    print("=" * 60)
    print(f"\n📂 Obsidian 源: {OBSIDIAN_BASE}")
    print(f"📁 输出目录: {OUTPUT_DIR}\n")

    # 扫描
    articles, article_contents, pillar_modules = scan_directory()

    # 生成 site-data.js
    print("\n📝 生成 site-data.js ...")
    site_data_js = generate_site_data_js(articles, pillar_modules)
    site_data_path = os.path.join(OUTPUT_DIR, "site-data.js")
    with open(site_data_path, 'w', encoding='utf-8') as f:
        f.write(site_data_js)
    size_kb = os.path.getsize(site_data_path) / 1024
    print(f"   ✅ {site_data_path} ({size_kb:.1f} KB)")

    # 生成 article-content.js
    print("📝 生成 article-content.js ...")
    article_content_js = generate_article_content_js(article_contents)
    article_content_path = os.path.join(OUTPUT_DIR, "article-content.js")
    with open(article_content_path, 'w', encoding='utf-8') as f:
        f.write(article_content_js)
    size_mb = os.path.getsize(article_content_path) / 1024 / 1024
    print(f"   ✅ {article_content_path} ({size_mb:.1f} MB)")

    # 统计
    print(f"\n{'=' * 60}")
    print(f"📊 统计:")
    print(f"   总文章数: {len(articles)}")
    print(f"   pillarModules:")
    for pillar, modules in pillar_modules.items():
        for m in modules:
            count = sum(1 for a in articles if a["category"] == m["module"])
            subcats = ", ".join(m["subcategories"])
            print(f"     {m['icon']} {m['module']}: {count}篇 ({subcats})")

    # 抽检输出
    print(f"\n🔍 抽检（前5篇）:")
    for a in articles[:5]:
        content_preview = article_contents.get(a["id"], "")[:80].replace('\n', ' ')
        print(f"   [{a['id']}]")
        print(f"     标题: {a['title']}")
        print(f"     分类: {a['category']} > {a['subcategory']}")
        print(f"     内容预览: {content_preview}...")

    print(f"\n✅ 全部完成！")

    # ── 语法验证 ──────────────────────────────────────────
    print("\n🔍 语法验证 ...")
    for f in ['site-data.js', 'article-content.js']:
        path = os.path.join(OUTPUT_DIR, f)
        r = subprocess.run(['node', '--check', path], capture_output=True, text=True)
        if r.returncode != 0:
            print(f'   ❌ {f} 语法错误！')
            print(f'      {r.stderr.strip()}')
            sys.exit(1)
        else:
            print(f'   ✅ {f} 通过')


if __name__ == "__main__":
    main()
