#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的GUI测试程序
"""

import PySimpleGUI as sg

# 设置主题
sg.theme('LightBlue3')

# 最简单的布局
layout = [
    [sg.Text('测试标题', font=('Arial', 16, 'bold'))],
    [sg.Text('这是一个测试文本')],
    [sg.Input('输入框测试', key='-INPUT-')],
    [sg.Button('测试按钮', key='-BUTTON-')],
    [sg.Multiline('多行文本测试\n第二行', key='-MULTI-', size=(50, 10))],
]

window = sg.Window('测试窗口', layout, size=(600, 400), finalize=True)

print("窗口已创建，等待事件...")

while True:
    event, values = window.read(timeout=100)
    
    if event == sg.WIN_CLOSED:
        break
    elif event == '-BUTTON-':
        print(f"按钮被点击！输入框内容: {values['-INPUT-']}")
        window['-MULTI-'].update(f"按钮被点击！\n输入框内容: {values['-INPUT-']}\n")

window.close()
print("窗口已关闭")
