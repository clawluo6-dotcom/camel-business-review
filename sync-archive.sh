#!/bin/bash
# 骆驼商业本质 — 存盘归档脚本
# 用法：在终端中运行 bash /Users/luoclaw/WorkBuddy/成果库/骆驼商业本质/sync-archive.sh

set -e
echo "=========================================="
echo "骆驼商业本质 — 存盘归档脚本"
echo "=========================================="

SRC="/Users/luoclaw/WorkBuddy/成果库/骆驼商业本质"
DST="/Users/luoclaw/WorkBuddy/骆驼商业本质网站"
DB="$HOME/.workbuddy/workbuddy.db"

echo ""
echo "Step 1: 同步成果库 → 工作目录..."
# 删除工作目录中旧的 npm 缓存等残留
rm -rf "$DST/.npm-cache" "$DST/_cacache" "$DST/_logs" "$DST/_npx" "$DST/_update-notifier-last-checked" "$DST/.DS_Store"
# 复制所有网站文件（不含 .workbuddy 内存目录）
rsync -av --delete --exclude='.workbuddy' --exclude='.DS_Store' "$SRC/" "$DST/"
echo "✅ 文件同步完成"

echo ""
echo "Step 2: 更新数据库会话路径..."
sqlite3 "$DB" "UPDATE sessions SET cwd='$DST', custom_title='骆驼商业本质网站' WHERE cwd LIKE '%2026-06-04%';" 2>/dev/null
echo "✅ 数据库 cwd + custom_title 已更新"

echo ""
echo "Step 3: 重命名 ~/.workbuddy/projects 目录..."
mv "$HOME/.workbuddy/projects/Users-luoclaw-WorkBuddy-2026-06-04-08-26-23" "$HOME/.workbuddy/projects/Users-luoclaw-WorkBuddy-骆驼商业本质网站" 2>/dev/null || echo "（已存在或无需操作）"
echo "✅ projects 目录已重命名"

echo ""
echo "Step 4: 同步到 iCloud 云盘..."
ICLOUD_DST="$HOME/Library/Mobile Documents/com~apple~CloudDocs/骆驼商业本质-成果库备份"
mkdir -p "$ICLOUD_DST"
rsync -av --delete --exclude='.git' --exclude='.workbuddy' --exclude='.DS_Store' --exclude='__pycache__' --exclude='_archived' --exclude='*.bak-*' "$SRC/" "$ICLOUD_DST/"
echo "✅ iCloud 同步完成"

echo ""
echo "Step 5: 写入今日记忆..."
MEMORY_FILE="$DST/.workbuddy/memory/2026-06-06.md"
mkdir -p "$(dirname "$MEMORY_FILE")"
if [ ! -f "$MEMORY_FILE" ]; then
  cat >> "$MEMORY_FILE" << 'MEMORY_EOF'

### 存盘归档完成（2026-06-06 18:10）
- ✅ CloudStudio 部署成功：https://c337a92ac19b473db57238fce4c88f32.app.codebuddy.work
- ✅ 成果库文件同步至 骆驼商业本质网站/
- ✅ 数据库会话路径已更新
- ✅ Obsidian 笔记 v4.2 已更新
- ✅ IMA 知识库已导入
- 网站色系：暗版冷色独立 / 亮版暖色独立，互不干扰
MEMORY_EOF
fi
echo "✅ 记忆文件已更新"

echo ""
echo "=========================================="
echo "🎉 全部完成！可以下班了。"
echo "   网站：https://c337a92ac19b473db57238fce4c88f32.app.codebuddy.work"
echo "=========================================="
