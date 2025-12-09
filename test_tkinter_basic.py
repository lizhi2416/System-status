#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最基础的tkinter测试
"""

import tkinter as tk

print("开始创建窗口...")

root = tk.Tk()
root.title('基础测试')
root.geometry('400x300')

print("窗口已创建")

label = tk.Label(root, text='这是测试文本\n如果你看到这个，说明tkinter工作正常', 
                font=('Arial', 14), bg='yellow', fg='black')
label.pack(pady=20)

button = tk.Button(root, text='点击我', command=lambda: print('按钮被点击！'))
button.pack(pady=10)

entry = tk.Entry(root, width=30)
entry.pack(pady=10)
entry.insert(0, '这是输入框')

print("所有组件已创建，准备显示窗口...")
print("如果窗口没有显示，请检查终端是否有错误信息")

try:
    root.mainloop()
    print("窗口已关闭")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
