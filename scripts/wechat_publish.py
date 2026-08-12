#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wechat_publish.py — 《骆驼商业本质》公众号每日分发器

每天取一篇「还没发过公众号」的网站文章，生成公众号可发全文（含原文回链），
并尝试通过 md2wechat 同步到公众号【草稿箱】（需 ~/.workbuddy/config/wechat.env 凭证）。

与 social_pack.py 的「每日社交包」(小红书/X/公众号三合一) 不同，本脚本用独立的
.wechat_state.json 追踪，专门按「一天一篇」节奏把全部文章铺到公众号。

用法：
  python3 wechat_publish.py publish --limit 1          # 生成一篇公众号全文（手动模式，写出 md 文件）
  python3 wechat_publish.py publish --limit 1 --auto   # 生成并尝试同步到草稿箱（自动模式）
  python3 wechat_publish.py --list                      # 列出全部文章 + 是否已发公众号
  python3 wechat_publish.py status                      # 已发/剩余统计

状态：scripts/.wechat_state.json  {"delivered": [short_id, ...]}
"""
import os, re, sys, json, argparse, subprocess, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from social_pack import load_articles, load_body, by_id, gen_wechat_full  # noqa

STATE_FILE = os.path.join(ROOT, "scripts", ".wechat_state.json")
OUT_DIR = os.path.join(ROOT, "scripts", "wechat_out")
CRED_ENV = os.path.expanduser("~/.workbuddy/config/wechat.env")
SITE_BASE = "https://clawluo6-dotcom.github.io/camel-business-review"

# md2wechat 工具链（node workspace 内已 npm install）
NODE = "/Users/luo/.workbuddy/binaries/node/versions/22.22.2/bin/node"
MD2W = "/Users/luo/.workbuddy/binaries/node/workspace/node_modules/md2wechat/dist/cli/index.js"


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


def next_id():
    arts = load_articles()
    done = set(load_state().get("delivered", []))
    for a in arts:
        sid = a.get("short_id")
        if sid and sid not in done:
            return sid
    return None


def list_articles():
    arts = load_articles()
    st = load_state()
    done = set(st.get("delivered", []))
    print("共 %d 篇（✅=已发公众号）：" % len(arts))
    for a in arts:
        sid = a.get("short_id", "")
        mark = "✅" if sid in done else "  "
        print("  %s %s  %s" % (mark, sid, a.get("title", "")))


def status():
    arts = load_articles()
    total = len(arts)
    done = len(load_state().get("delivered", []))
    print("公众号分发进度：已发 %d 篇 / 共 %d 篇，剩余 %d 篇待发。" % (done, total, total - done))


# ---------- 生成 + 发布 ----------
def load_creds():
    cfg = {}
    if os.path.exists(CRED_ENV):
        for line in open(CRED_ENV, encoding="utf-8"):
            m = re.match(r"^([A-Z_]+)=(.+)$", line.strip())
            if m:
                cfg[m.group(1)] = m.group(2).strip()
    return cfg.get("WECHAT_APP_ID"), cfg.get("WECHAT_APP_SECRET")


def ensure_theme():
    """把项目内品牌主题覆盖到 md2wechat 的 themes 目录（重装包也不丢）。"""
    src = os.path.join(ROOT, "scripts", "wechat_theme")
    # MD2W = .../node_modules/md2wechat/dist/cli/index.js -> themes 在 ../../themes
    themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(MD2W))), "themes")
    basic_src = os.path.join(src, "basic.css")
    default_src = os.path.join(src, "default.css")
    try:
        if os.path.exists(basic_src):
            shutil.copy(basic_src, os.path.join(themes_dir, "basic.css"))
        if os.path.exists(default_src):
            md_dir = os.path.join(themes_dir, "markdown")
            os.makedirs(md_dir, exist_ok=True)
            shutil.copy(default_src, os.path.join(md_dir, "default.css"))
    except Exception as e:
        print("⚠️ 主题覆盖失败（不影响发布）：%s" % e)


def gen_md(sid):
    ensure_theme()  # 确保品牌主题已就位（手动/自动生成前都覆盖一次）
    a = by_id(sid)
    if not a:
        print("❌ 找不到 short_id=%s" % sid)
        sys.exit(1)
    body = load_body(sid)
    text = gen_wechat_full(a, body)
    os.makedirs(OUT_DIR, exist_ok=True)
    md_path = os.path.join(OUT_DIR, "%s.md" % sid)
    open(md_path, "w", encoding="utf-8").write(text)
    return a, text, md_path


def publish_one_auto(sid):
    """自动模式：同步到公众号草稿箱。返回 (success: bool, msg: str)。"""
    a, text, md_path = gen_md(sid)
    title = a.get("title", "")
    ensure_theme()
    app_id, app_secret = load_creds()
    if not app_id or not app_secret:
        return False, "未找到公众号凭证（~/.workbuddy/config/wechat.env），无法自动发布。"
    # 写临时 .env 供 md2wechat 读取（用完即删，不把密钥留在项目里）
    env_path = os.path.join(OUT_DIR, ".env")
    open(env_path, "w", encoding="utf-8").write(
        "WECHAT_APP_ID=%s\nWECHAT_APP_SECRET=%s\n" % (app_id, app_secret)
    )
    try:
        env = dict(os.environ)
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            env.pop(k, None)
        cmd = [NODE, MD2W, "sync-md", md_path, "-t", title]
        r = subprocess.run(cmd, cwd=OUT_DIR, env=env,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0 and ("media_id" in out or "草稿" in out or "成功" in out or "draft" in out.lower()):
            return True, out.strip().splitlines()[-1] if out.strip() else "已同步草稿箱"
        # 即便 returncode=0 也要看输出判断是否真成功；失败则返回错误
        return False, "md2wechat 返回异常：\n" + (out[-1500:] if out else "(无输出)")
    except subprocess.TimeoutExpired:
        return False, "md2wechat 同步超时（120s）"
    except Exception as e:
        return False, "执行异常：%s" % e
    finally:
        try:
            os.remove(env_path)
        except Exception:
            pass


def publish(sid, auto):
    if auto:
        ok, msg = publish_one_auto(sid)
        a = by_id(sid)
        if ok:
            st = load_state()
            if sid not in st.get("delivered", []):
                st.setdefault("delivered", []).append(sid)
                save_state(st)
            print("✅ 已发公众号草稿箱：《%s》" % a.get("title", ""))
            print("   ↳ %s" % msg)
            print("   链接：%s/article/%s.html" % (SITE_BASE, sid))
        else:
            print("❌ 公众号自动发布失败：《%s》" % a.get("title", ""))
            print("   ↳ %s" % msg)
            print("   已生成可手动粘贴的全文：scripts/wechat_out/%s.md" % sid)
    else:
        a, text, md_path = gen_md(sid)
        print("📝 已生成公众号全文：《%s》" % a.get("title", ""))
        print("   文件：%s" % md_path)
        print("   链接：%s/article/%s.html" % (SITE_BASE, sid))
        print("   （手动模式：复制到公众号后台即可发布）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", nargs="?", default="publish",
                    choices=["publish", "list", "status"])
    ap.add_argument("sid", nargs="?")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    if args.action == "list":
        list_articles()
        return
    if args.action == "status":
        status()
        return

    # publish
    count = 0
    while count < args.limit:
        sid = args.sid or next_id()
        if not sid:
            print("🎉 所有文章都已发过公众号。重置 scripts/.wechat_state.json 可重来。")
            return
        publish(sid, args.auto)
        count += 1
        if not args.sid:
            # 自动模式失败时不标记，循环会继续取同一篇；为避免死循环，手动模式才继续取下一篇
            st = load_state()
            if args.auto and sid in st.get("delivered", []):
                continue
            elif args.auto:
                # 自动失败，停止（今天不再试下一篇，等用户处理）
                break


if __name__ == "__main__":
    main()
