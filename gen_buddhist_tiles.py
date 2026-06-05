#!/usr/bin/env python3
"""
扫描佛学文章，直接输出可粘贴到 build_all_articles.py 的 TILES 行。
"""
import os, re, json

ROOT = "/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian/Andy知识库"
FO_ROOT = os.path.join(ROOT, "01-哲学思想研究/佛学思想研究")

def extract_title(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^#\s+(.+)$', line.strip())
                if m:
                    return m.group(1).strip()
    except:
        pass
    return None

def clean_subcat(dirname):
    return re.sub(r'^[（(][^）)]+[）)]\s*', '', dirname).strip() or dirname

def gen_id(title, subcat):
    # 取标题前4个中文字符作为 id 基础
    chars = [c for c in title if '\u4e00' <= c <= '\u9fff']
    base = ''.join(chars[:4]) if chars else subcat[:4]
    # 转 ASCII-safe
    base = 'buddha' if not base else base
    return base[:12].lower()

def scan():
    rows = []
    for dirname in sorted(os.listdir(FO_ROOT)):
        dirpath = os.path.join(FO_ROOT, dirname)
        if not os.path.isdir(dirpath):
            continue
        if dirname.startswith('.'):
            continue
        subcat = clean_subcat(dirname)
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith('.md'):
                continue
            if fname.startswith('.'):
                continue
            fpath = os.path.join(dirpath, fname)
            title = extract_title(fpath)
            if not title:
                title = os.path.splitext(fname)[0]
            # file_fragment = 文件名去掉 .md
            ff = os.path.splitext(fname)[0]
            # id
            aid = gen_id(title, subcat)
            # 去重
            existing = set(r[0] for r in rows)
            if aid in existing:
                base = aid
                n = 1
                while aid in existing:
                    aid = base + str(n)
                    n += 1
            # tags
            tags = [subcat]
            rows.append((aid, 'worldview', '佛学思想研究', subcat, ff, tags, 3))
    return rows

def escape_python_string(s):
    """转义字符串用于 Python 源码"""
    return s.replace('\\', '\\\\').replace('"', '\\"')

def main():
    rows = scan()
    print('=' * 60)
    print('共扫描到 {} 篇佛学文章'.format(len(rows)))
    print('=' * 60)
    print()
    print('    # 佛学思想研究（自动生成，共 {} 篇）'.format(len(rows)))
    for r in rows:
        aid, pillar, cat, subcat, ff, tags, depth = r
        # 格式化 tags 列表
        tags_str = '[' + ', '.join('"' + escape_python_string(t) + '"' for t in tags) + ']'
        # 每行
        line = '    ("{}", "{}", "{}", "{}", "{}", {}, {}),'.format(
            escape_python_string(aid),
            pillar,
            escape_python_string(cat),
            escape_python_string(subcat),
            escape_python_string(ff),
            tags_str,
            depth
        )
        print(line)
    print()
    print('    # 请粘贴到 build_all_articles.py TILES 列表末尾')

if __name__ == '__main__':
    main()
