#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
social_pack.py — 「每日社交包」生成器（替代旧 multiplier.py 的空壳版）

它从文章【真实正文】里抽取硬货（首句钩子 + 带数字/结论的关键点），
生成三档可直接复制发布的文案：
  - ① 小红书卡片（结论 + 3 真实要点 + CTA）
  - ② X / Twitter 推文串（中文，面向海外华人）
  - ③ 公众号全文（完整文章，可发；文末带原文链接 + 『阅读原文』回链）

并维护一个「已投递」状态文件，保证每天不重复、按优先级铺。

用法：
  python3 social_pack.py --list                 # 列出全部文章 + 是否已投递社交包
  python3 social_pack.py --next [--out]        # 取下一个未投递的，打印/写出包
  python3 social_pack.py <short_id> [--out]    # 指定文章出包

状态文件：scripts/.social_state.json
优先级：scripts/.social_priority.txt（一行一个 short_id，优先铺这些；不存在则按 site-data 顺序）
"""
import os, re, sys, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ART = os.path.join(ROOT, "data", "articles")
SITE_BASE = "https://clawluo6-dotcom.github.io/camel-business-review"
STATE_FILE = os.path.join(ROOT, "scripts", ".social_state.json")
PRIORITY_FILE = os.path.join(ROOT, "scripts", ".social_priority.txt")
HAND_PACK_DIR = os.path.join(ROOT, "scripts", "multiplier_out")  # Nova 手写高质量包优先用


# ---------- 数据读取 ----------
def load_articles():
    p = os.path.join(ROOT, "site-data.js")
    txt = open(p, encoding="utf-8").read()
    m = re.search(r"window\.__ARTICLES__\s*=\s*(\{.*?\})\s*;", txt, re.DOTALL)
    if not m:
        print("❌ 无法解析 site-data.js"); sys.exit(1)
    return json.loads(m.group(1)).get("articles", [])


def load_body(sid):
    p = os.path.join(DATA_ART, sid + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8")).get("content")


def by_id(sid):
    for a in load_articles():
        if a.get("short_id") == sid:
            return a
    return None


# ---------- 文本清洗 / 抽取 ----------
def clean_inline(md):
    md = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md or "")
    md = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', md or "")
    md = re.sub(r'[`*_>#]', '', md or "")
    md = re.sub(r'\s+', ' ', md).strip()
    return md


def lead_sentence(md, cap=130):
    """文章第一段里的第一句（带结论感）。"""
    # 去掉标题行与分隔线
    body = re.sub(r'^#.*$', '', md or "", flags=re.M)
    body = re.sub(r'^---+$', '', body, flags=re.M)
    paras = [p.strip() for p in body.split("\n") if p.strip()]
    for para in paras:
        c = clean_inline(para)
        if len(c) >= 15:
            # 取第一个句号前（保留完整一句，最长 cap）
            seg = re.split(r'(?<=[。！？])', c)[0]
            if len(seg) > cap:
                seg = seg[:cap].rstrip(' ，,') + '…'
            return seg
    return ""


def extract_points(md, n=3):
    """从正文抽取带『数字/结论』的 2-3 级小标题，并补一句事实。"""
    lines = (md or "").split("\n")
    pts = []
    i = 0
    while i < len(lines) and len(pts) < n:
        m = re.match(r'^#{2,3}\s+(.+)$', lines[i])
        if m:
            h = m.group(1).strip()
            h = re.sub(r'^[\d一二三四五六七八九十]+[、.、]\s*', '', h)
            h = re.sub(r'[（(][^）)]*$', '', h).strip()
            h = re.sub(r'^[—–\-–]+', '', h).strip()   # 去前导破折号
            h = h.strip('。. "')
            if 5 <= len(h) <= 20 and not h.startswith('（'):
                fact = ""
                for j in range(i + 1, min(i + 7, len(lines))):
                    s = clean_inline(lines[j])
                    if re.search(r'\d', s) and 12 <= len(s) <= 70 and not s.startswith('#'):
                        fact = s
                        break
                pts.append((h, fact))
        i += 1
    return pts


# ---------- 三档文案 ----------
def gen_xhs(a, body):
    sid = a["short_id"]
    title = a.get("title", "")
    link = "%s/article/%s.html" % (SITE_BASE, sid)
    lead = lead_sentence(body)
    pts = extract_points(body, 3)
    L = ["📌 %s" % title, ""]
    if lead:
        L.append(lead)
        L.append("")
    L.append("几个被忽略的硬事实：")
    if pts:
        for i, (h, fact) in enumerate(pts, 1):
            L.append("%d️⃣ %s" % (i, h))
            if fact:
                L.append("   ↳ %s" % fact)
    else:
        L.append("（详见全文数据图表）")
    L.append("")
    L.append("👉 深挖原文 + 完整数据表：%s" % link)
    L.append("（配图用文内曲线/对比图，流量翻倍）")
    return "\n".join(L)


def gen_x(a, body):
    sid = a["short_id"]
    title = a.get("title", "")
    link = "%s/article/%s.html" % (SITE_BASE, sid)
    lead = lead_sentence(body)
    pts = extract_points(body, 3)
    L = ["🧵 %s" % title, ""]
    if lead:
        L.append(lead)
        L.append("")
    if pts:
        L.append("几个关键点：")
        for i, (h, fact) in enumerate(pts, 1):
            line = "%d. %s" % (i, h)
            if fact:
                line += " — %s" % fact
            L.append(line)
        L.append("")
    L.append("🔗 全文（含数据图表）：%s" % link)
    L.append("#骆驼商业本质 #%s" % (a.get("category", "商业") or "商业"))
    return "\n".join(L)


def gen_wechat_full(a, body):
    """公众号【全文可发版·品牌排版】：完整文章 + 顶部品牌栏 + 文末关注卡片。
    保留 markdown 真实标题层级（h2/h3 由主题美化为沉稳红色块/暖金条）、加粗、引用块（金句）；
    图片转「配图见原文」提示（微信不显示外链图），外链去壳保留文字。"""
    sid = a["short_id"]
    link = "%s/article/%s.html" % (SITE_BASE, sid)
    md = body or ""
    # 去 Obsidian 专属语法
    md = re.sub(r'!\[\[.*?\]\]', '', md)             # 嵌入附件
    md = re.sub(r'\[\[(.*?)\]\]', r'\1', md)         # wikilink → 文本
    md = re.sub(r'\^\w+', '', md)                     # 块引用锚 ^id
    md = re.sub(r'%%[\s\S]*?%%', '', md)              # callout/注释块
    # 图片 → 配图见原文（微信不显示外链图）
    md = re.sub(r'!\[([^\]]*)\]\(([^)]*)\)', r'（配图见原文：\2）', md)
    # 外链去壳保留文字（微信正文不可点，回链放文末+阅读原文）
    md = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'\1', md)
    # 行内代码去反引号保留内容
    md = re.sub(r'`([^`]+)`', r'\1', md)
    # 一级标题降级为二级（避免与微信草稿标题重复）
    md = re.sub(r'^(#{1,6})\s+(.+)$',
                lambda m: '#' * min(len(m.group(1)) + 1, 6) + ' ' + m.group(2),
                md, flags=re.M)
    # 折叠连续空行
    md = re.sub(r'\n{3,}', '\n\n', md).strip()
    L = []
    L.append("> 🐫 **骆驼商业本质** · 深度商业研究手记")
    L.append("")
    L.append(md)
    L.append("")
    L.append("---")
    L.append("")
    L.append("> 📎 **本文完整版**（含数据图表、延伸阅读）：%s" % link)
    L.append("> 👉 点公众号菜单「阅读原文」一键回站点看全本。")
    L.append("> ✦ 关注 **骆驼商业本质**，每周获取深度研究。")
    return "\n".join(L)


# ---------- 状态 ----------
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {"delivered": []}


def save_state(st):
    json.dump(st, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def load_priority():
    if os.path.exists(PRIORITY_FILE):
        return [l.strip() for l in open(PRIORITY_FILE, encoding="utf-8") if l.strip()]
    return []


def next_id():
    arts = load_articles()
    st = load_state()
    done = set(st.get("delivered", []))
    pri = load_priority()
    # 1) 优先队列中未投递的
    for sid in pri:
        if sid not in done and by_id(sid):
            return sid
    # 2) 否则按 site-data 顺序取第一个未投递
    for a in arts:
        sid = a.get("short_id")
        if sid and sid not in done:
            return sid
    return None


# ---------- 渲染 ----------
def render(sid):
    a = by_id(sid)
    if not a:
        print("❌ 找不到 short_id=%s" % sid); sys.exit(1)
    body = load_body(sid)
    wc = gen_wechat_full(a, body)
    # 优先用 Nova 手写高质量包（① ② 质量好），但公众号档统一替换为全文型
    hand = os.path.join(HAND_PACK_DIR, "%s.md" % sid)
    if os.path.exists(hand):
        txt = open(hand, encoding="utf-8").read()
        block = "\n\n## ③ 公众号全文（复制粘贴到公众号后台，可发完整文章，文末带原文链接）\n```\n%s\n```" % wc
        m = re.search(r'\n##\s*③', txt)
        if m:
            txt = txt[:m.start()] + block
        else:
            txt = txt.rstrip() + block
        return txt, True
    out = ["# 社交包 · %s" % a.get("title", ""), ""]
    out.append("> short_id: `%s` ｜ 分类: %s ｜ 链接: %s/article/%s.html" % (
        sid, a.get("category", ""), SITE_BASE, sid))
    out.append("")
    out.append("## ① 小红书卡片（复制发布）\n```\n%s\n```" % gen_xhs(a, body))
    out.append("")
    out.append("## ② X / Twitter 推文串（复制发布）\n```\n%s\n```" % gen_x(a, body))
    out.append("")
    out.append("## ③ 公众号全文（复制粘贴到公众号后台，可发完整文章，文末带原文链接）\n```\n%s\n```" % wc)
    return "\n".join(out), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sid", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--out", action="store_true")
    args = ap.parse_args()

    if args.list or (not args.sid and not args.next):
        arts = load_articles()
        st = load_state()
        done = set(st.get("delivered", []))
        print("共 %d 篇（✅=已投递社交包）：" % len(arts))
        for a in arts:
            sid = a.get("short_id", "")
            mark = "✅" if sid in done else "  "
            print("  %s %s  %s" % (mark, sid, a.get("title", "")))
        return

    sid = args.sid
    if args.next:
        sid = next_id()
        if not sid:
            print("🎉 所有文章都已投递过社交包。重置 scripts/.social_state.json 可重来。")
            return

    text, is_hand = render(sid)
    print(text)
    print("\n（来源：%s）" % ("Nova 手写高质量包" if is_hand else "social_pack.py 自动抽取"))

    if args.out:
        d = os.path.join(ROOT, "scripts", "social_pack_out")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "%s.md" % sid)
        open(p, "w", encoding="utf-8").write(text)
        # 记录状态
        st = load_state()
        if sid not in st.get("delivered", []):
            st.setdefault("delivered", []).append(sid)
            save_state(st)
        print("\n💾 已写 %s ｜ 状态已记录" % p)


if __name__ == "__main__":
    main()
