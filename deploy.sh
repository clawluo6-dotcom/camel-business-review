#!/bin/bash
set -e

# ──────────────────────────────────────────
# 🐫 骆驼商业本质 · 一键部署脚本
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

# ── Step 2: 检测变更 ──────────────────
echo "🔍 Step 2: 检测变更..."
cd "$SITE_DIR"

# 先拉取远程更新
git pull "$GIT_REMOTE" "$GIT_BRANCH" --rebase 2>/dev/null || true

if git diff --quiet && git diff --cached --quiet; then
    echo "✅ 无变更，跳过部署"
    echo ""
    
    # ── 额外: 检查是否有未收录的新文章 ──
    python3 -c "
import os, sys
from pathlib import Path

vault = Path(r'''$VAULT''')
site_dir = Path(r'''$SITE_DIR''')

# 提取所有已收录的 filename_glob
globs = set()
with open(site_dir / 'build_all_articles.py', 'r') as f:
    content = f.read()

# 匹配 ARTICLES_SPEC 中的第5个参数（filename_glob），用引号括起来的
import re
# 找注释行之后的下一个元组
lines = content.split('\n')
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('#'):
        continue
    # 找元组中引号包裹的第5个参数
    # 格式: ("id", "pillar", "cat", "subcat", "filename_glob", [...]
    m = re.search(r'\(\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\".*?\"\s*,\s*\"(.*?)\"', stripped)
    if m:
        globs.add(m.group(1))

# 扫描 Andy知识库 内容目录
kb = vault / 'Andy知识库'
all_md = []
if kb.exists():
    for md in kb.rglob('*.md'):
        # 跳过索引文件、模板、README
        name = md.name
        if name.startswith('MOC-') or name.startswith('README') or '索引' in name or name.startswith('🗄️'):
            continue
        # 只扫描内容目录
        rel = str(md.relative_to(kb))
        parts = Path(rel).parts
        if parts[0] in ['01-哲学思想研究', '02-经济研究', '03-商业项目']:
            all_md.append(str(md))

# 检查是否已被收录
unmatched = []
for f in all_md:
    fname = Path(f).name
    matched = any(g in fname for g in globs)
    if not matched:
        unmatched.append(f)

if unmatched:
    print('📋 发现未收录文章 (Andy知识库 有但网站未收录):')
    for f in sorted(unmatched):
        try:
            rel = str(Path(f).relative_to(kb))
        except:
            rel = f
        print(f'   📄 {rel}')
    print(f'   共 {len(unmatched)} 篇，可手动添加到 build_all_articles.py 的 ARTICLES_SPEC')
" 2>/dev/null || true
    
    exit 0
fi

echo ""
echo "📋 变更文件："
git diff --stat --cached 2>/dev/null || git diff --stat
echo ""

# ── Step 3: 提交并推送 ────────────────
echo "📤 Step 3: 提交并推送..."
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
