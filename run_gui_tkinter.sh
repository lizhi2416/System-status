#!/bin/bash
# -*- coding: utf-8 -*-
"""
GUI程序启动脚本（tkinter版本）
使用Python 3.12（Tk 9.0）以确保GUI正常显示
"""

echo "启动 Apple Developer Status Monitor GUI (tkinter版本)..."

# 优先使用Python 3.12
if command -v python3.12 &> /dev/null; then
    echo "使用 Python 3.12 (Tk 9.0)..."
    python3.12 monitor_gui_tkinter.py
elif command -v python3 &> /dev/null; then
    echo "使用系统 Python 3..."
    python3 monitor_gui_tkinter.py
else
    echo "错误: 未找到Python 3"
    exit 1
fi
