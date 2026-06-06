#!/bin/bash
set -e

# ──────────────────────────────────────────
# 🐫 骆驼商业本质 · 一键部署脚本
#
# 用法: ./deploy.sh
# 自动完成: 构建 → 检测 → 提交 → 推送
# 同时检查 Obsidian 中是否有未收录的新文章
# ──────────────────────────────────────────

VAULT="/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian"
SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_SCRIPT="$SITE_DIR/build_all_articles.py"
GIT_REMOTE="origin"
GIT_BRANCH="main"

echo "🐫 骆驼商业本质 · 一键部署"
echo "============================"
echo ""

# ── Step 1: 构建 ──────────────────────
echo "📦 Step 1: 从 Obsidian 构建文章数据..."
cd "$SITE_DIR"
if ! python3 "$BUILD_SCRIPT"; then
    echo "❌ 构建失败，检查 build_all_articles.py 输出"
    exit 1
fi
echo "✅ 构建完成"
echo ""

# ── Step 2: 检查未收录文章 ─────────────
echo "🔎 Step 2: 检查未收录文章..."
python3 -c "
import os, sys, re
from pathlib import Path

vault = Path(r'''$VAULT''')
site_dir = Path(r'''$SITE_DIR''')

# 提取所有已收录的 filename_glob
globs = set()
with open(site_dir / 'build_all_articles.py', 'r') as f:
    for line in f:
        m = re.search(r'\(\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\"(.*?)\"', line)
        if m:
            globs.add(m.group(1))

# 扫描 Andy知识库 内容目录
kb = vault / 'Andy知识库'
if kb.exists():
    unmatched = []
    for md in kb.rglob('*.md'):
        name = md.name
        # 跳过索引和系统文件
        if name.startswith('MOC-') or name.startswith('README') or '索引' in name or name.startswith('🗄️') or name.startswith('🔗') or name.startswith('🏷️'):
            continue
        # 只扫描内容目录
        rel = str(md.relative_to(kb))
        parts = Path(rel).parts
        if parts[0] in ['01-哲学思想研究', '02-经济研究', '03-商业项目']:
            # 检查是否已被收录
            if not any(g in name for g in globs):
                unmatched.append(rel)

    if unmatched:
        print('📋 以下文章在 Obsidian 中但未被网站收录:')
        for f in sorted(unmatched):
            print(f'   📄 {f}')
        print(f'   共 {len(unmatched)} 篇，可手动添加到 ARTICLES_SPEC')
    else:
        print('✅ 所有文章已收录，无遗漏')
else:
    print('⚠️  未找到 Andy知识库 目录')
" 2>/dev/null || echo "⚠️  新文章检查失败（非致命）"
echo ""

# ── Step 3: 检测 Git 变更 ──────────────
echo "🔍 Step 3: 检测 Git 变更..."
cd "$SITE_DIR"

# 先拉取远程更新
git pull "$GIT_REMOTE" "$GIT_BRANCH" --rebase 2>/dev/null || true

if git diff --quiet && git diff --cached --quiet; then
    echo "✅ 无变更，跳过部署"
    echo ""
    exit 0
fi

echo "📋 变更文件："
git diff --stat --cached 2>/dev/null || git diff --stat
echo ""

# ── Step 4: 提交并推送 ────────────────
echo "📤 Step 4: 提交并推送..."
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git add -A
git commit -m "🔄 自动更新：$TIMESTAMP" 2>&1 || { echo "⚠️  无内容可提交"; exit 0; }
git push "$GIT_REMOTE" "$GIT_BRANCH"

echo ""
echo "════════════════════════════════════"
echo "✅ 部署完成！"
echo "🌐 https://clawluo6-dotcom.github.io/camel-business-review/"
echo "⏱️  GitHub Pages 约 1-2 分钟后刷新"
echo "════════════════════════════════════"
