#!/bin/bash
# 骆驼商业本质 — iCloud 备份脚本
# 用法: bash icloud-backup.sh
# 效果: 将成果库 + WorkBuddy 记忆/技能备份到 iCloud Drive，方便多设备访问

set -e

SRC="$HOME/WorkBuddy/成果库/骆驼商业本质"
DST="$HOME/Library/Mobile Documents/com~apple~CloudDocs/骆驼商业本质-成果库备份"
WB_SYNC="$HOME/Library/Mobile Documents/com~apple~CloudDocs/WorkBuddy-sync"

echo "=========================================="
echo "🐫 骆驼商业本质 → iCloud 备份"
echo "=========================================="
echo ""
echo "来源: $SRC"
echo "目标: $DST"
echo ""

# 创建目标目录
mkdir -p "$DST"

# 同步文件（排除 git 和缓存）
rsync -av --delete \
  --exclude='.git' \
  --exclude='.workbuddy' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  --exclude='node_modules' \
  --exclude='_archived' \
  --exclude='*.bak-*' \
  "$SRC/" "$DST/"

echo ""
echo "=========================================="
echo "📝 同步 WorkBuddy 记忆/技能到 iCloud"
echo "=========================================="

# 复制用户级核心文件（MEMORY.md + 身份文件）
cp "$HOME/.workbuddy/MEMORY.md" "$WB_SYNC/MEMORY.md"
cp "$HOME/.workbuddy/SOUL.md" "$WB_SYNC/SOUL.md"
cp "$HOME/.workbuddy/IDENTITY.md" "$WB_SYNC/IDENTITY.md"
cp "$HOME/.workbuddy/USER.md" "$WB_SYNC/USER.md"

# 复制项目级 memory 到 iCloud（记忆 + 技能 symlink 已自动同步）
mkdir -p "$WB_SYNC/project-memory"
cp -R "$SRC/.workbuddy/memory/" "$WB_SYNC/project-memory/骆驼商业本质/"
echo "📁 记忆/身份文件已同步到 iCloud Drive「WorkBuddy-sync」"

echo ""
echo "✅ 全部备份完成"
echo "📁 成果库: iCloud Drive「骆驼商业本质-成果库备份」"
echo "📁 记忆/技能: iCloud Drive「WorkBuddy-sync」"

# 显示目录大小
echo ""
echo "📊 备份大小: $(du -sh "$DST" | awk '{print $1}')"
