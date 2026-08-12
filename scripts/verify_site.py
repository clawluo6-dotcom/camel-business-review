#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_site.py — 发布前校验闸门（防"图文化文章线上空白"复发）

问题背景：
  过去多次出现「文章线上不显示/空白」——根因是文章正文引用的图片
  (data/images/xxx) 在本地/线上都不存在（Obsidian 附件未导入，或原图已丢失）。
  这类问题过去只有等读者/用户发现才暴露。

本脚本作用：
  扫描全部文章引用的图片，确认每张都真实存在于 data/images/。
  一旦发现缺失（或空文件），打印清晰报告并以 非零码退出，
  从而在任何 `gh api` 部署之前拦截，避免坏图文章上线。

用法：
  python3 scripts/verify_site.py            # 严格模式：缺图即非零退出
  python3 scripts/verify_site.py --quiet    # 仅输出结论与缺失清单

白名单：
  已知永久丢失、且对应文章有文字正文不影响阅读的图片，可列入仓库根的
  .verify_allow_missing.txt（每行一个文件名，# 开头为注释），脚本会放行这些，
  但仍会拦截任何新增的缺失图片。
"""

import os
import re
import sys
import json
import glob

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(SITE_DIR, "data", "images")
ARTICLES_DIR = os.path.join(SITE_DIR, "data", "articles")
ALLOW_FILE = os.path.join(SITE_DIR, ".verify_allow_missing.txt")

IMG_RE = re.compile(r'!\[[^\]]*\]\(data/images/([^)\s]+)\)')
EMBED_RE = re.compile(r'!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]')


def load_allowlist():
    allow = set()
    if os.path.exists(ALLOW_FILE):
        with open(ALLOW_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    allow.add(line)
    return allow


def load_contents():
    """从 data/articles/*.json 读取 {article_id: content}"""
    contents = {}
    if not os.path.isdir(ARTICLES_DIR):
        return contents
    for f in glob.glob(os.path.join(ARTICLES_DIR, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        aid = d.get("id") or os.path.splitext(os.path.basename(f))[0]
        contents[aid] = d.get("content", "")
    return contents


def referenced_images(content):
    imgs = set()
    for m in IMG_RE.finditer(content or ""):
        imgs.add(os.path.basename(m.group(1)))
    for m in EMBED_RE.finditer(content or ""):
        imgs.add(os.path.basename(m.group(1)))
    return imgs


def main():
    quiet = "--quiet" in sys.argv[1:]
    allow = load_allowlist()
    contents = load_contents()

    total_refs = 0
    missing_by_article = {}
    missing_set = set()

    for aid, content in contents.items():
        refs = referenced_images(content)
        total_refs += len(refs)
        for img in refs:
            if img in allow:
                continue
            path = os.path.join(IMG_DIR, img)
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                missing_by_article.setdefault(aid, []).append(img)
                missing_set.add(img)

    if not quiet:
        print(f"📊 校验: {len(contents)} 篇文章, {total_refs} 处图片引用"
              + (f"（白名单放行 {len(allow)} 张）" if allow else ""))

    if missing_by_article:
        print(f"\n❌ 发现 {len(missing_set)} 张缺失/空图片（涉及 {len(missing_by_article)} 篇文章）：")
        for aid, imgs in missing_by_article.items():
            print(f"   • {aid}")
            for i in imgs:
                print(f"       └ 缺图: {i}")
        print("\n🔧 修复方式（二选一）：")
        print("   1) 从 Obsidian「附件/」目录找回原图，拷入 data/images/ 后重跑 generate_site_data.py；")
        print("   2) 若该图确已永久丢失且文章有文字正文，把文件名加入 .verify_allow_missing.txt 白名单。")
        print("   ⛔ 发布前必须消除所有缺失图片，否则线上可能出现空白文章。")
        sys.exit(1)
    else:
        print("✅ 全部引用图片均存在，可安全发布。")
        sys.exit(0)


if __name__ == "__main__":
    main()
