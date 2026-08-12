#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
骆驼商业本质 → Dev.to 自动发布脚本
====================================
把 site-data.js 中的文章（含 article-content.js 的正文）自动发布到 Dev.to，
每篇带 canonical_url（指回原站，避免重复内容惩罚）和「回流《骆驼商业本质》」脚注。

特性：
- 自动跳过已发布的文章（状态存于 .workbuddy/devto_state.json）
- 限流保护：遇到 429 自动停止本轮
- 必须带 User-Agent 头（否则 Dev.to 返回 403 空 body）
- 中文正文直接发（Dev.to 原生支持 Markdown）

用法：
  python3 devto_publish.py --limit 2            # 发布下 2 篇
  python3 devto_publish.py --limit 2 --dry       # 只打印将要发什么，不真发
  python3 devto_publish.py --seed                # 仅把已发布文章写回状态（用于初始化）

API Key 来源（按顺序）：
  1. 环境变量 DEVTO_KEY
  2. 项目根目录 .devto_key 文件（单行）
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT, ".workbuddy", "devto_state.json")
KEY_FILE = os.path.join(ROOT, ".devto_key")
SITE_BASE = "https://clawluo6-dotcom.github.io/camel-business-review"

FOOTER = """

---

> 🐫 本文出自 **《骆驼商业本质》** —— 骆新中的跨领域独立研究手记（世界历史 · 哲学 · 经济学）。
> 阅读全部 160 篇原创文章，请访问 👉 [{base}]({base})
""".strip()

# 每篇文章顶部的署名 byline（作者真名 + 品牌 + 撰写日期，确保在显眼处标注）
BYLINE_TMPL = "> ✦ **作者：骆新中**　｜　来源：**《骆驼商业本质》**　——　跨领域独立研究（世界历史 · 哲学 · 经济学）　｜　撰写于 {date}"

def build_byline(date):
    return BYLINE_TMPL.format(date=date or "未知")

# Dev.to 标签（必须为其已知合法标签，否则发布失败）
# 按分类字符串中的关键词匹配
TAG_RULES = [
    ("传统哲学", ["philosophy", "culture"]),
    ("自然哲学", ["philosophy", "science"]),
    ("佛学", ["philosophy", "culture"]),
    ("儒家", ["philosophy", "culture"]),
    ("经济史", ["history", "economics"]),
    ("国际金融", ["economics", "society"]),
    ("宏观经济", ["economics", "society"]),
    ("中国经济", ["economics", "society"]),
    ("美国", ["economics", "society"]),
    ("AI", ["ai", "technology"]),
    ("科技", ["technology", "science"]),
]
FALLBACK_TAGS = ["philosophy", "thoughts"]


def build_tags(category):
    cat = category or ""
    for kw, tags in TAG_RULES:
        if kw in cat:
            return tags[:4]
    return FALLBACK_TAGS[:4]


def get_key():
    if os.environ.get("DEVTO_KEY"):
        return os.environ["DEVTO_KEY"].strip()
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            k = f.read().strip()
            if k:
                return k
    print("❌ 找不到 Dev.to API Key。请设置环境变量 DEVTO_KEY 或在项目根目录创建 .devto_key 文件。")
    sys.exit(1)


def load_articles():
    """读取 site-data.js 的 __ARTICLES__.articles 与 article-content.js 的 __D 正文表。"""
    import subprocess
    node = os.path.expanduser("~/.workbuddy/binaries/node/versions/22.22.2/bin/node")
    js = r"""
    const fs = require('fs'), vm = require('vm');
    const sd = fs.readFileSync('%s/site-data.js', 'utf8');
    const sb = { window: {} };
    vm.runInNewContext(sd, sb);
    const arts = sb.window.__ARTICLES__.articles;
    const ac = fs.readFileSync('%s/article-content.js', 'utf8');
    const ctx = { window: {} };
    vm.runInNewContext(ac, ctx);
    const __D = ctx.window.__ARTICLE_CONTENT__;
    const out = { articles: [], bodies: {} };
    arts.forEach(function(a){ out.articles.push({ short_id: a.short_id, id: a.id, title: a.title, date: a.date, pillar: a.pillar, category: a.category }); });
    if (__D) {
      Object.keys(__D).forEach(function(k){
        // key 形如 "data/xxx-<short_id>"
        var parts = k.split('/');
        var last = parts[parts.length-1];
        out.bodies[last] = __D[k];
      });
    }
    process.stdout.write(JSON.stringify(out));
    """ % (ROOT, ROOT)
    p = subprocess.run([node, "-e", js], capture_output=True, text=True, cwd=ROOT)
    if p.returncode != 0:
        print("❌ 读取文章数据失败:", p.stderr[:500])
        sys.exit(1)
    return json.loads(p.stdout)


def match_body(article, bodies):
    sid = article.get("short_id") or ""
    if not sid:
        return None
    # 精确：key 以 -<short_id> 结尾
    if sid in bodies:
        return bodies[sid]
    for k, v in bodies.items():
        if k.endswith("-" + sid) or k.endswith("/" + sid) or k == sid:
            return v
    # 模糊：key 包含 short_id
    for k, v in bodies.items():
        if sid in k:
            return v
    return None


def build_payload(article, body):
    base = "%s/article.html?id=%s" % (SITE_BASE, article["short_id"])
    title = article["title"]
    # 去掉正文中与标题重复的 H1
    lines = body.split("\n")
    cleaned = []
    for ln in lines:
        if ln.strip().startswith("# ") and article["title"] in ln:
            continue
        cleaned.append(ln)
    body = "\n".join(cleaned).strip()
    full = build_byline(article.get("date", "")) + "\n\n" + body + "\n\n" + FOOTER.format(base=SITE_BASE)
    return {
        "article": {
            "title": title,
            "body_markdown": full,
            "published": True,
            "canonical_url": base,
            "tags": build_tags(article.get("category", "")),
            "series": None,
            "main_image": None,
        }
    }


def publish_one(article, body, key):
    payload = build_payload(article, body)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://dev.to/api/articles",
        data=data,
        headers={
            "api-key": key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh) camel-publisher/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode())
            return True, resp.get("url") or resp.get("id")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return "RATELIMIT", None
        err = e.read().decode()[:300]
        return False, "HTTP %s: %s" % (e.code, err)
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": [], "last_run": None}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--seed", action="store_true")
    args = ap.parse_args()

    key = get_key()
    data = load_articles()
    articles = data["articles"]
    bodies = data["bodies"]
    state = load_state()
    published = set(state.get("published", []))

    print("🔍 文章总数: %d | 正文表条目: %d | 已发布: %d" % (len(articles), len(bodies), len(published)))

    # 匹配率统计
    matched = 0
    candidates = []
    for a in articles:
        b = match_body(a, bodies)
        if b:
            matched += 1
            if a["short_id"] not in published:
                candidates.append((a, b))
        else:
            if a.get("short_id"):
                print("  ⚠️ 未匹配正文（跳过）:", a.get("short_id"), a["title"][:30])
    print("✅ 可发布匹配: %d / %d" % (matched, len([a for a in articles if a.get("short_id")])))

    if args.seed:
        # 种子模式：把已发布但状态里没有的，尝试按标题回写（本脚本不联网查，仅保留现有）
        save_state(state)
        print("🌱 状态已保存（published=%d）" % len(published))
        return

    if not candidates:
        print("🎉 没有待发布文章了（全部已发或缺失正文）。")
        return

    # 按日期升序发（从最早开始，保持时间线）
    candidates.sort(key=lambda x: x[0].get("date", ""))

    print("\n📤 准备发布（limit=%d, dry=%s）:" % (args.limit, args.dry))
    sent = 0
    for a, b in candidates[: args.limit]:
        print("  → [%s] %s  (tags=%s)" % (a["short_id"], a["title"][:40], ",".join(build_tags(a.get("category", "")))))
        if args.dry:
            sent += 1
            continue
        ok, info = publish_one(a, b, key)
        if ok is True:
            published.add(a["short_id"])
            state["published"] = list(published)
            state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            save_state(state)
            print("     ✅ 已发布:", info)
            sent += 1
            time.sleep(2)
        elif ok == "RATELIMIT":
            print("     ⏸️ 触发限流（429），本轮停止。稍后自动化会再发。")
            break
        else:
            print("     ❌ 失败:", info)
            break

    print("\n✅ 本轮发送 %d 篇。累计已发布 %d 篇。" % (sent, len(published)))


if __name__ == "__main__":
    main()
