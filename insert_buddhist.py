#!/usr/bin/env python3
"""直接把佛学文章插入 build_all_articles.py 的 TILES 列表末尾"""
import os, re, json

BUILD = "/Users/luoclaw/WorkBuddy/成果库/骆驼商业本质/build_all_articles.py"
ROOT  = "/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian/Andy知识库"
FOOT = os.path.join(ROOT, "01-哲学思想研究/佛学思想研究")

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
    chars = [c for c in title if '\u4e00' <= c <= '\u9fff']
    base = ''.join(chars[:4]) if chars else subcat[:4]
    base = 'buddha' if not base else base
    return re.sub(r'[^a-z0-9]', '', base.lower())[:12] or 'buddha'

def scan():
    rows = []
    for dirname in sorted(os.listdir(FOOT)):
        dirpath = os.path.join(FOOT, dirname)
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
            ff = os.path.splitext(fname)[0]
            aid = gen_id(title, subcat)
            # 去重
            existing = set(r[0] for r in rows)
            if aid in existing:
                base = aid
                n = 1
                while aid in existing:
                    aid = base + str(n)
                    n += 1
            tags = [subcat]
            rows.append((aid, 'worldview', '佛学思想研究', subcat, ff, tags, 3))
    return rows

def format_tuple(r):
    aid, pillar, cat, subcat, ff, tags, depth = r
    tags_str = '[' + ', '.join('"' + t.replace('"', '\\"') + '"' for t in tags) + ']'
    # 用双引号包裹字符串（Python 源码格式）
    def q(s):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return "    (" + q(aid) + ", " + q(pillar) + ", " + q(cat) + ", " + q(subcat) + ", " + q(ff) + ", " + tags_str + ", " + str(depth) + "),"

def main():
    rows = scan()
    print(f"扫描到 {len(rows)} 篇佛学文章")

    # 读取原文件
    with open(BUILD, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到 TILES 的结束 ] （在 def find_file 之前）
    # 找最后一个 )，] 模式
    # 实际上找 "^]\s*$" 在 "def find_file" 之前
    lines = content.split('\n')
    insert_idx = None
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped == ']':
            # 确认后面是 def find_file 或空白后跟 def
            # 简单处理：找 TILES = [  对应的 ]
            insert_idx = i
            break

    if insert_idx is None:
        print("❌ 找不到 TILES 的结束 ]")
        return

    # 生成要插入的文本
    new_lines = []
    new_lines.append('')
    new_lines.append('    # 佛学思想研究（自动生成，共 {} 篇）'.format(len(rows)))
    for r in rows:
        new_lines.append(format_tuple(r))

    # 插入到 ] 之前
    out_lines = lines[:insert_idx] + new_lines + lines[insert_idx:]
    out = '\n'.join(out_lines) + '\n'

    with open(BUILD, 'w', encoding='utf-8') as f:
        f.write(out)

    print(f"✅ 已插入 {len(rows)} 篇佛学文章到 build_all_articles.py")
    print(f"   插入位置：第 {insert_idx + 1} 行（TILES 结束 ] 之前）")

if __name__ == '__main__':
    main()
