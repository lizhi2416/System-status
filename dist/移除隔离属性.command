#!/bin/bash
# -*- coding: utf-8 -*-
# 移除隔离属性脚本 - 双击运行即可

echo "=========================================="
echo "移除隔离属性工具"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/AppleStatusMonitor.app"

# 如果当前目录没有，尝试查找
if [ ! -d "$APP_PATH" ]; then
    # 尝试在常见位置查找
    if [ -d "$HOME/Downloads/AppleStatusMonitor.app" ]; then
        APP_PATH="$HOME/Downloads/AppleStatusMonitor.app"
    elif [ -d "$HOME/Desktop/AppleStatusMonitor.app" ]; then
        APP_PATH="$HOME/Desktop/AppleStatusMonitor.app"
    else
        echo "❌ 未找到 AppleStatusMonitor.app"
        echo ""
        echo "请将 AppleStatusMonitor.app 放在以下位置之一："
        echo "  - 与此脚本同一目录"
        echo "  - 下载文件夹 (~/Downloads)"
        echo "  - 桌面 (~/Desktop)"
        echo ""
        read -p "或者直接拖拽应用到此窗口，然后按回车: " DRAGGED_APP
        if [ -n "$DRAGGED_APP" ]; then
            # 移除拖拽时可能包含的引号
            APP_PATH=$(echo "$DRAGGED_APP" | sed "s/^['\"]//;s/['\"]$//")
        fi
    fi
fi

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 未找到应用，请确认路径是否正确"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo "找到应用: $APP_PATH"
echo ""
echo "正在移除隔离属性..."

# 移除隔离属性
xattr -cr "$APP_PATH" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 成功移除隔离属性！"
    echo ""
    echo "现在可以正常打开应用了："
    echo "  1. 双击 AppleStatusMonitor.app"
    echo "  2. 或者在 Finder 中右键点击应用，选择'打开'"
    echo ""
else
    echo "⚠️  移除隔离属性时出现问题"
    echo "但应用可能仍然可以运行，请尝试右键点击应用选择'打开'"
    echo ""
fi

read -p "按回车键退出..."
