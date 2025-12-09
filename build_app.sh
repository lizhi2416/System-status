#!/bin/bash
# -*- coding: utf-8 -*-
# 打包脚本 - 将监控程序打包为桌面应用（tkinter 版本）
# 备注：macOS 使用 onedir + windowed 生成 .app bundle，避免 onefile/windowed 兼容问题

echo "=========================================="
echo "Apple Developer Status Monitor - 打包脚本 (macOS)"
echo "目标: 打包 tkinter 版本 (Python 3.12 / Tk 9.0)"
echo "=========================================="
echo ""

# 使用本地缓存目录，避免权限问题
export PYINSTALLER_CONFIG_DIR="$(pwd)/.pyinstaller"
export PYINSTALLER_CACHE_DIR="$(pwd)/.pyinstaller"

# 选择Python 3.12，若不存在则使用python3
PY_BIN="python3.12"
if ! command -v ${PY_BIN} &> /dev/null; then
    PY_BIN="python3"
fi
echo "使用 Python: $(${PY_BIN} --version 2>/dev/null)"

# 确保 PyInstaller 可用
if ! ${PY_BIN} -m PyInstaller --version &> /dev/null; then
    echo "❌ 未检测到 PyInstaller，正在安装..."
    ${PY_BIN} -m pip install --break-system-packages pyinstaller
fi

# 确保依赖
echo "📦 安装依赖..."
${PY_BIN} -m pip install --break-system-packages requests

echo ""
echo "🔨 开始打包 (tkinter版本)..."
echo ""

# 检测操作系统
OS_TYPE=$(uname -s)
echo "检测到操作系统: $OS_TYPE"

if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS: 使用 onedir + windowed 创建 .app bundle
    echo "使用 macOS 打包模式 (onedir + windowed = .app bundle)"
    ${PY_BIN} -m PyInstaller --onedir \
        --windowed \
        --name "AppleStatusMonitor" \
        --add-data "config.py:." \
        --hidden-import=requests \
        --hidden-import=email \
        --hidden-import=email.mime.text \
        --hidden-import=email.mime.multipart \
        --hidden-import=smtplib \
        --hidden-import=monitor \
        --hidden-import=config \
        --clean \
        monitor_gui_tkinter.py
    
    APP_PATH="dist/AppleStatusMonitor.app"
    EXE_NAME="AppleStatusMonitor.app"
else
    # Linux/其他: 使用 onefile
    echo "使用 Linux/通用打包模式 (onefile)"
    ${PY_BIN} -m PyInstaller --onefile \
        --name "AppleStatusMonitor" \
        --add-data "config.py:." \
        --hidden-import=requests \
        --hidden-import=email \
        --hidden-import=email.mime.text \
        --hidden-import=email.mime.multipart \
        --hidden-import=smtplib \
        --hidden-import=monitor \
        --hidden-import=config \
        --clean \
        monitor_gui_tkinter.py
    
    EXE_NAME="AppleStatusMonitor"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    if [ "$OS_TYPE" = "Darwin" ]; then
        echo "📁 macOS应用位置: dist/AppleStatusMonitor.app"
        echo ""
        echo "💡 使用说明："
        echo "   - 可以将 dist/AppleStatusMonitor.app 分发给其他 macOS 用户"
        echo "   - 首次运行时，如果 macOS 提示'无法打开，因为来自身份不明的开发者'"
        echo "     请在'系统设置 > 隐私与安全性'中点击'仍要打开'"
        echo "   - 或者右键点击应用，选择'打开'"
        echo "   - 用户可以直接在GUI界面中配置收件人邮箱"
        echo "   - 邮件SMTP设置需要在应用内或通过编辑配置文件设置"
    else
        echo "📁 可执行文件位置: dist/$EXE_NAME"
        echo ""
        echo "💡 使用说明："
        echo "   - 可以将 dist/$EXE_NAME 分发给其他用户"
        echo "   - 用户可以直接在GUI界面中配置收件人邮箱"
        echo "   - 邮件SMTP设置需要在应用内或通过编辑配置文件设置"
    fi
    echo ""
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
