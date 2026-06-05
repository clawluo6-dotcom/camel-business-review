#!/usr/bin/env python3
"""
扫描 01-哲学思想研究/佛学思想研究/ 目录，
自动生成 build_all_articles.py 的 TILES 配置片段。
"""
import os, re, json

ROOT = "/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian/Andy知识库"
FO_ROOT = os.path.join(ROOT, "01-哲学思想研究/佛学思想研究")

# pillar/category 固定
PILLAR = "worldview"
CATEGORY = "佛学思想研究"

def extract_title(path):
    """从文件第一行提取 # 标题"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^#\s+(.+)$', line.strip())
                if m:
                    return m.group(1).strip()
    except:
        pass
    return os.path.splitext(os.path.basename(path))[0]

def frag_from_title(title):
    """从标题生成模糊匹配片段列表"""
    # 去掉序号前缀如 "01-" 或 "（一）"
    t = re.sub(r'^\d+[-–—]\s*', '', title)
    t = re.sub(r'^[（(][^）)]+[）)]\s*', '', t)
    # 取关键词
    parts = re.split(r'[：:·\-—–\s]+', t)
    frags = [p.strip() for p in parts if len(p.strip()) > 1]
    return frags[:4] if frags else [t[:6]]

def scan():
    items = []
    for dirname in sorted(os.listdir(FO_ROOT)):
        dirpath = os.path.join(FO_ROOT, dirname)
        if not os.path.isdir(dirpath):
            continue
        if dirname.startswith('.'):
            continue
        # 子分类名：去掉序号前缀
        sub = re.sub(r'^[（(][^）)]+[）)]\s*', '', dirname).strip()
        if not sub:
            sub = dirname
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith('.md'):
                continue
            if fname.startswith('.'):
                continue
            fpath = os.path.join(dirpath, fname)
            title = extract_title(fpath)
            if not title:
                title = os.path.splitext(fname)[0]
            # 生成 id：小写 + 下划线
            base = os.path.splitext(fname)[0]
            uid = re.sub(r'^\d+[-_]*', '', base)  # 去掉序号
            uid = re.sub(r'[（(][^）)]+[）)]', '', uid)  # 去掉中文序号
            uid = uid.lower().replace(' ', '-').replace('：', '-').replace('·', '-')[:40]
            uid = re.sub(r'[^a-z0-9-]', '', uid)
            if not uid:
                uid = base[:20]
            frags = frag_from_title(title)
            depth = 3  # 默认
            items.append({
                'id': uid,
                'pillar': PILLAR,
                'category': CATEGORY,
                'subcategory': sub,
                'file': fpath,
                'title': title,
                'frags': frags,
                'depth': depth,
            })
    return items

def gen_python(items):
    """生成 Python 配置片段"""
    lines = []
    lines.append("    # 佛学思想研究（自动生成，共 {} 篇）".format(len(items)))
    for it in items:
        frag_str = json.dumps(it['frags'], ensure_ascii=False)
        line = "    ('{}',  '{}', '{}', '{}',  {}, {}),".format(
            it['id'], it['pillar'], it['category'], it['subcategory'],
            json.dumps(it['title'], ensure_ascii=False),
            frag_str
        )
        # 去掉外层引号，直接嵌入
        # 实际上需要手动调整……先打印 title 和 frags
        print("  Title: {}  |  Subcat: {}  |  Frags: {}".format(it['title'], it['subcategory'], it['frags']))
    print("\n共 {} 篇文章".format(len(items)))

if __name__ == '__main__':
    items = scan()
    print("扫描到 {} 篇佛学文章：\n".format(len(items)))
    gen_python(items)
