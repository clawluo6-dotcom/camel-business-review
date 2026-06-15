#!/bin/bash
# 骆驼商业本质 — iCloud 备份脚本
# 用法: bash icloud-backup.sh
# 效果: 将成果库备份到 iCloud Drive，方便多设备访问

set -e

SRC="/Users/luoclaw/WorkBuddy/成果库/骆驼商业本质"
DST="$HOME/Library/Mobile Documents/com~apple~CloudDocs/骆驼商业本质-成果库备份"

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
echo "✅ iCloud 备份完成"
echo "📁 可在 iCloud Drive「骆驼商业本质-成果库备份」中查看"

# 显示目录大小
echo ""
echo "📊 备份大小: $(du -sh "$DST" | awk '{print $1}')"
