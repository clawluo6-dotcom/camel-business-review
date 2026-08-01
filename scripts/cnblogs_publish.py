#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
骆驼商业本质 → 博客园(cnblogs) 自动发布脚本
============================================
通过 MetaWeblog API (XML-RPC) 把文章自动发布到博客园。
复用 Dev.to 脚本的文章抽取逻辑（从 site-data.js / article-content.js 读取）。

与 Dev.to 的差异：
- 博客园 description 字段要 HTML（Dev.to 要 Markdown），正文用 markdown 库转 HTML
- 认证用博客园独立的 MetaWeblog 访问密码（后台「设置→开放服务」生成）

凭证来源（.cnblogs_key.json，已 gitignore）：
  { "blog_name": "你的博客名", "username": "登录账号", "password": "MetaWeblog访问密码" }
也可环境变量 CNBLOGS_BLOG / CNBLOGS_USER / CNBLOGS_PASS

用法：
  python3 cnblogs_publish.py --limit 2            # 发布下 2 篇
  python3 cnblogs_publish.py --limit 2 --dry      # 只打印将要发什么 + HTML 转换结果，不联网
  python3 cnblogs_publish.py --seed               # 仅把已发布文章写回状态（用于初始化）
"""

import os
import sys
import json
import time
import argparse
import re
import subprocess
import markdown
from xmlrpc.client import ServerProxy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT, ".workbuddy", "cnblogs_state.json")
KEY_FILE = os.path.join(ROOT, ".cnblogs_key.json")
SITE_BASE = "https://clawluo6-dotcom.github.io/camel-business-review"

FOOTER = """
---

> 🐫 本文出自 **《骆驼商业本质》** —— 骆新中的跨领域独立研究手记（世界历史 · 哲学 · 经济学）。
> 阅读全部 168 篇原创文章，请访问 👉 {base}
"""
BYLINE_TMPL = "> ✦ **作者：骆新中**　｜　来源：**《骆驼商业本质》**　——　跨领域独立研究（世界历史 · 哲学 · 经济学）　｜　撰写于 {date}"

# pillar -> 大类（分类兜底）
PILLAR_MAP = {"worldview": "世界观", "social": "社会与经济逻辑"}
FALLBACK_CAT = "骆驼商业本质"

def build_byline(date):
    return BYLINE_TMPL.format(date=date or "未知")

def clean_category(cat, pillar):
    if not cat:
        return [PILLAR_MAP.get(pillar, FALLBACK_CAT)]
    c = re.sub(r'^[一二三四五六七八九十]+、', '', cat).strip()
    if not c:
        c = PILLAR_MAP.get(pillar, FALLBACK_CAT)
    return [c]

# ---------- 文章抽取（复用 Dev.to 逻辑） ----------
def load_articles():
    node = "/Users/luoclaw/.workbuddy/binaries/node/versions/22.22.2/bin/node"
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
    if sid in bodies:
        return bodies[sid]
    for k, v in bodies.items():
        if k.endswith("-" + sid) or k.endswith("/" + sid) or k == sid:
            return v
    for k, v in bodies.items():
        if sid in k:
            return v
    return None

# ---------- Markdown -> HTML ----------
def md_to_html(md):
    return markdown.markdown(
        md,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html",
    )

def build_html(article, body):
    base = "%s/article.html?id=%s" % (SITE_BASE, article["short_id"])
    title = article["title"]
    lines = body.split("\n")
    cleaned = []
    for ln in lines:
        if ln.strip().startswith("# ") and article["title"] in ln:
            continue
        cleaned.append(ln)
    body = "\n".join(cleaned).strip()
    md = build_byline(article.get("date", "")) + "\n\n" + body + "\n\n" + FOOTER.format(base=SITE_BASE)
    return md_to_html(md)

# ---------- 凭证 ----------
def get_creds():
    eb = os.environ.get("CNBLOGS_BLOG")
    eu = os.environ.get("CNBLOGS_USER")
    ep = os.environ.get("CNBLOGS_PASS")
    if eb and eu and ep:
        return eb.strip(), eu.strip(), ep.strip()
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("blog_name"), d.get("username"), d.get("password")
    print("❌ 找不到博客园凭证。请创建 .cnblogs_key.json（参考 .cnblogs_key.json.example）或设置环境变量 CNBLOGS_BLOG/USER/PASS。")
    sys.exit(1)

# ---------- 发布 ----------
def publish_one(article, body, creds):
    blog_name, username, password = creds
    html = build_html(article, body)
    cats = clean_category(article.get("category", ""), article.get("pillar", ""))
    rpc_url = "https://rpc.cnblogs.com/metaweblog/" + (blog_name or "")
    try:
        server = ServerProxy(rpc_url, allow_none=True)
        post = {
            "title": article["title"],
            "description": html,
            "categories": cats,
        }
        postid = server.metaWeblog.newPost(blog_name or "", username, password, post, True)
        return True, str(postid)
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)

# ---------- 状态 ----------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": [], "last_run": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ---------- 主流程 ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=2)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--seed", action="store_true")
    args = ap.parse_args()

    data = load_articles()
    articles = data["articles"]
    bodies = data["bodies"]
    state = load_state()
    published = set(state.get("published", []))

    creds = None
    if not args.dry:
        creds = get_creds()

    print("🔍 文章总数: %d | 正文表条目: %d | 已发布: %d" % (len(articles), len(bodies), len(published)))

    matched = 0
    candidates = []
    for a in articles:
        b = match_body(a, bodies)
        if b:
            matched += 1
            if a["short_id"] not in published:
                candidates.append((a, b))
        elif a.get("short_id"):
            print("  ⚠️ 未匹配正文（跳过）:", a.get("short_id"), a["title"][:30])

    print("✅ 可发布匹配: %d / %d" % (matched, len([a for a in articles if a.get("short_id")])))

    if args.seed:
        save_state(state)
        print("🌱 状态已保存（published=%d）" % len(published))
        return

    if not candidates:
        print("🎉 没有待发布文章了（全部已发或缺失正文）。")
        return

    candidates.sort(key=lambda x: x[0].get("date", ""))

    print("\n📤 准备发布（limit=%d, dry=%s）:" % (args.limit, args.dry))
    sent = 0
    for a, b in candidates[: args.limit]:
        cats = clean_category(a.get("category", ""), a.get("pillar", ""))
        print("  → [%s] %s  (分类=%s)" % (a["short_id"], a["title"][:40], ",".join(cats)))
        if args.dry:
            html = build_html(a, b)
            print("      HTML 长度: %d | 含 <h1>:%s <blockquote>:%s <img>:%s" % (
                len(html), "<h1>" in html, "<blockquote>" in html, "<img" in html))
            sent += 1
            continue
        ok, info = publish_one(a, b, creds)
        if ok is True:
            published.add(a["short_id"])
            state["published"] = list(published)
            state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            save_state(state)
            url = "https://www.cnblogs.com/%s/p/%s.html" % (creds[0] or "", info)
            print("     ✅ 已发布:", url)
            sent += 1
            time.sleep(3)
        else:
            print("     ❌ 失败:", info)
            break

    print("\n✅ 本轮发送 %d 篇。累计已发布 %d 篇。" % (sent, len(published)))

if __name__ == "__main__":
    main()
