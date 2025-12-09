#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Developer System Status Monitor - GUI版本（使用tkinter）
使用Python 3.12 (Tk 9.0) 以确保GUI正常显示
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from monitor import AppleStatusMonitor
import config


class MonitorGUI:
    """监控程序GUI界面（使用tkinter）"""
    
    def __init__(self):
        self.monitor = None
        self.monitor_thread = None
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_running = False
        
        # 创建主窗口
        print("正在创建主窗口...")
        self.root = tk.Tk()
        self.root.title('Apple Developer System Status Monitor')
        self.root.geometry('900x750')
        self.root.resizable(True, True)
        
        print("窗口基础设置完成，开始创建界面组件...")
        
        # 创建界面
        self._create_widgets()
        
        print("界面组件创建完成，窗口应该已显示")
        
        # 确保窗口显示在前台
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.update()
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        self.root.deiconify()
        self.root.focus_force()
        
        # 启动日志处理
        self._process_log_queue()
        
        # 添加初始日志
        self._add_log('INFO', 'GUI界面已启动，等待配置...')
        
    def _create_widgets(self):
        """创建界面组件 - 优化后的美观界面"""
        # 设置主题颜色
        bg_color = '#F5F5F5'  # 浅灰色背景
        frame_bg = '#FFFFFF'  # 白色框架背景
        title_color = '#2C3E50'  # 深蓝灰色标题
        accent_color = '#3498DB'  # 蓝色强调色
        success_color = '#27AE60'  # 绿色成功色
        danger_color = '#E74C3C'  # 红色危险色
        
        # 主框架
        main_frame = tk.Frame(self.root, bg=bg_color, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg=bg_color)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, 
                              text='🍎 Apple Developer System Status Monitor', 
                              font=('Arial', 18, 'bold'), 
                              bg=bg_color, 
                              fg=title_color)
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, 
                                 text='实时监控 Apple Developer 系统状态', 
                                 font=('Arial', 10), 
                                 bg=bg_color, 
                                 fg='#7F8C8D')
        subtitle_label.pack(pady=(5, 0))
        
        # 配置区域 - 使用卡片式设计
        config_frame = tk.Frame(main_frame, bg=frame_bg, relief=tk.RAISED, bd=1, padx=15, pady=15)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_title = tk.Label(config_frame, 
                               text='⚙️ 监控配置', 
                               font=('Arial', 13, 'bold'), 
                               bg=frame_bg, 
                               fg=title_color)
        config_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 配置项 - 使用网格布局
        config_grid = tk.Frame(config_frame, bg=frame_bg)
        config_grid.pack(fill=tk.X)
        
        # 检测间隔
        tk.Label(config_grid, text='检测间隔（分钟）:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').grid(row=0, column=0, sticky=tk.W, padx=5, pady=8)
        self.check_interval_var = tk.StringVar(value=str(config.CHECK_INTERVAL // 60))
        self.check_interval_entry = ttk.Entry(config_grid, textvariable=self.check_interval_var, width=20, font=('Arial', 10))
        self.check_interval_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=8)
        
        # 重试次数
        tk.Label(config_grid, text='失败重试次数:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
        self.retry_count_var = tk.StringVar(value=str(config.RETRY_COUNT))
        self.retry_count_entry = ttk.Entry(config_grid, textvariable=self.retry_count_var, width=20, font=('Arial', 10))
        self.retry_count_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        
        # 重试间隔
        tk.Label(config_grid, text='重试间隔（秒）:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').grid(row=2, column=0, sticky=tk.W, padx=5, pady=8)
        self.retry_delay_var = tk.StringVar(value=str(config.RETRY_DELAY))
        self.retry_delay_entry = ttk.Entry(config_grid, textvariable=self.retry_delay_var, width=20, font=('Arial', 10))
        self.retry_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=8)
        
        # 收件人邮箱（支持多个，逗号分隔）
        tk.Label(config_grid, text='收件人邮箱:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').grid(row=3, column=0, sticky=tk.W, padx=5, pady=8)
        email_hint = tk.Label(config_grid, text='(多个邮箱用逗号分隔)', 
                             font=('Arial', 8), bg=frame_bg, fg='#95A5A6')
        email_hint.grid(row=3, column=1, sticky=tk.W, padx=5, pady=(0, 2))
        self.to_email_var = tk.StringVar(value=config.EMAIL_CONFIG.get('to_email', ''))
        self.to_email_entry = ttk.Entry(config_grid, textvariable=self.to_email_var, width=50, font=('Arial', 10))
        self.to_email_entry.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=8)
        config_grid.columnconfigure(1, weight=1)
        
        # 监控服务信息
        info_frame = tk.Frame(config_frame, bg=frame_bg)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(info_frame, text='监控服务:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').pack(side=tk.LEFT)
        service_label = tk.Label(info_frame, text=config.TARGET_SERVICE, 
                                font=('Arial', 10), fg=accent_color, bg=frame_bg)
        service_label.pack(side=tk.LEFT, padx=5)
        
        url_info_frame = tk.Frame(config_frame, bg=frame_bg)
        url_info_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(url_info_frame, text='监控URL:', 
                font=('Arial', 10), bg=frame_bg, fg='#34495E', width=18, anchor='w').pack(side=tk.LEFT)
        url_label = tk.Label(url_info_frame, text=config.MONITOR_URL, 
                            font=('Arial', 9), fg=accent_color, bg=frame_bg, cursor='hand2')
        url_label.pack(side=tk.LEFT, padx=5)
        
        # 运行状态指示器
        status_indicator_frame = tk.Frame(main_frame, bg=frame_bg, relief=tk.RAISED, bd=1, padx=15, pady=12)
        status_indicator_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_indicator_title = tk.Label(status_indicator_frame, 
                                          text='📊 运行状态', 
                                          font=('Arial', 13, 'bold'), 
                                          bg=frame_bg, 
                                          fg=title_color)
        status_indicator_title.pack(side=tk.LEFT, padx=(0, 15))
        
        # 状态指示器（圆形）
        self.status_indicator = tk.Canvas(status_indicator_frame, width=20, height=20, bg=frame_bg, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        self.status_indicator.create_oval(5, 5, 15, 15, fill='#95A5A6', outline='')  # 初始灰色
        
        self.status_text_label = tk.Label(status_indicator_frame, 
                                        text='未运行', 
                                        font=('Arial', 12, 'bold'), 
                                        bg=frame_bg, 
                                        fg='#7F8C8D')
        self.status_text_label.pack(side=tk.LEFT)
        
        # 按钮区域 - 使用卡片式设计
        button_frame = tk.Frame(main_frame, bg=frame_bg, relief=tk.RAISED, bd=1, padx=15, pady=15)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_title = tk.Label(button_frame, 
                               text='🎮 操作控制', 
                               font=('Arial', 13, 'bold'), 
                               bg=frame_bg, 
                               fg=title_color)
        button_title.pack(anchor=tk.W, pady=(0, 10))
        
        button_container = tk.Frame(button_frame, bg=frame_bg)
        button_container.pack()
        
        # 使用自定义样式的按钮 - 优化文字对比度
        self.start_button = tk.Button(button_container, 
                                     text='▶ 开始监控', 
                                     command=self._start_monitoring,
                                     font=('Arial', 12, 'bold'),
                                     bg=success_color,
                                     fg='#FFFFFF',  # 纯白色，确保对比度
                                     activebackground='#229954',
                                     activeforeground='#FFFFFF',
                                     relief=tk.RAISED,
                                     bd=3,
                                     padx=25,
                                     pady=10,
                                     cursor='hand2',
                                     highlightthickness=0)
        self.start_button.pack(side=tk.LEFT, padx=8)
        
        self.stop_button = tk.Button(button_container, 
                                    text='⏹ 停止监控', 
                                    command=self._stop_monitoring, 
                                    state=tk.DISABLED,
                                    font=('Arial', 12, 'bold'),
                                    bg=danger_color,
                                    fg='#FFFFFF',  # 纯白色，确保对比度
                                    activebackground='#C0392B',
                                    activeforeground='#FFFFFF',
                                    relief=tk.RAISED,
                                    bd=3,
                                    padx=25,
                                    pady=10,
                                    cursor='hand2',
                                    highlightthickness=0,
                                    disabledforeground='#FFFFFF')  # 禁用时也保持白色
        self.stop_button.pack(side=tk.LEFT, padx=8)
        
        self.clear_button = tk.Button(button_container, 
                                     text='🗑 清空日志', 
                                     command=self._clear_logs,
                                     font=('Arial', 12, 'bold'),
                                     bg='#34495E',  # 深灰色，提高对比度
                                     fg='#FFFFFF',  # 纯白色
                                     activebackground='#2C3E50',
                                     activeforeground='#FFFFFF',
                                     relief=tk.RAISED,
                                     bd=3,
                                     padx=25,
                                     pady=10,
                                     cursor='hand2',
                                     highlightthickness=0)
        self.clear_button.pack(side=tk.LEFT, padx=8)
        
        # 日志区域 - 使用卡片式设计
        log_frame = tk.Frame(main_frame, bg=frame_bg, relief=tk.RAISED, bd=1, padx=15, pady=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        log_title = tk.Label(log_frame, 
                            text='📋 监控日志', 
                            font=('Arial', 13, 'bold'), 
                            bg=frame_bg, 
                            fg=title_color)
        log_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 日志文本框
        log_container = tk.Frame(log_frame, bg=frame_bg)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_container, 
                                                  width=80, 
                                                  height=18, 
                                                  font=('Consolas', 9), 
                                                  state=tk.DISABLED,
                                                  bg='#2C3E50',
                                                  fg='#ECF0F1',
                                                  insertbackground='white',
                                                  selectbackground=accent_color,
                                                  relief=tk.SUNKEN,
                                                  bd=2,
                                                  wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏 - 使用卡片式设计（显示详细信息）
        status_frame = tk.Frame(main_frame, bg=frame_bg, relief=tk.RAISED, bd=1, padx=15, pady=10)
        status_frame.pack(fill=tk.X)
        
        status_title = tk.Label(status_frame, 
                               text='ℹ️ 详细信息', 
                               font=('Arial', 11, 'bold'), 
                               bg=frame_bg, 
                               fg=title_color)
        status_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.status_label = tk.Label(status_frame, 
                                    text='状态: 未运行', 
                                    font=('Arial', 10), 
                                    fg='#7F8C8D', 
                                    bg=frame_bg)
        self.status_label.pack(anchor=tk.W)
        
        self.last_check_label = tk.Label(status_frame, 
                                         text='', 
                                         font=('Arial', 9), 
                                         fg='#95A5A6', 
                                         bg=frame_bg)
        self.last_check_label.pack(anchor=tk.W)
        
        # 设置窗口背景
        self.root.configure(bg=bg_color)
        
    def _validate_inputs(self):
        """验证输入参数"""
        errors = []
        
        try:
            check_interval = int(self.check_interval_var.get())
            if check_interval <= 0:
                errors.append('检测间隔必须大于0')
        except ValueError:
            errors.append('检测间隔必须是数字')
        
        try:
            retry_count = int(self.retry_count_var.get())
            if retry_count < 0:
                errors.append('重试次数不能为负数')
        except ValueError:
            errors.append('重试次数必须是数字')
        
        try:
            retry_delay = int(self.retry_delay_var.get())
            if retry_delay < 0:
                errors.append('重试间隔不能为负数')
        except ValueError:
            errors.append('重试间隔必须是数字')
        
        to_email = self.to_email_var.get().strip()
        if not to_email:
            errors.append('收件人邮箱不能为空')
        else:
            # 支持多个邮箱，用逗号分隔
            emails = [e.strip() for e in to_email.split(',')]
            for email in emails:
                if not email:
                    errors.append('邮箱地址不能为空')
                elif '@' not in email or '.' not in email.split('@')[-1]:
                    errors.append(f'邮箱格式不正确: {email}')
        
        return errors
    
    def _start_monitoring(self):
        """启动监控"""
        # 验证输入
        errors = self._validate_inputs()
        if errors:
            messagebox.showerror('输入错误', '\n'.join(errors))
            return
        
        # 获取配置参数
        check_interval_min = int(self.check_interval_var.get())
        check_interval = check_interval_min * 60
        retry_count = int(self.retry_count_var.get())
        retry_delay = int(self.retry_delay_var.get())
        to_email = self.to_email_var.get().strip()  # 支持多个邮箱，逗号分隔
        
        # 禁用输入框和开始按钮
        self.check_interval_entry.config(state=tk.DISABLED)
        self.retry_count_entry.config(state=tk.DISABLED)
        self.retry_delay_entry.config(state=tk.DISABLED)
        self.to_email_entry.config(state=tk.DISABLED)
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 创建监控实例
        self.monitor = AppleStatusMonitor(
            check_interval=check_interval,
            retry_count=retry_count,
            retry_delay=retry_delay,
            to_email=to_email,
            log_queue=self.log_queue,
            stop_event=self.stop_event
        )
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()
        self.is_running = True
        
        # 更新状态指示器
        self.status_indicator.delete('all')
        self.status_indicator.create_oval(5, 5, 15, 15, fill='#27AE60', outline='')  # 绿色
        self.status_text_label.config(text='运行中', fg='#27AE60')
        
        # 更新状态
        self.status_label.config(text='状态: 运行中', fg='#27AE60')
        self._add_log('INFO', '监控已启动')
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
        
        self.stop_event.set()
        self.is_running = False
        
        # 等待线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # 恢复UI状态
        self.check_interval_entry.config(state=tk.NORMAL)
        self.retry_count_entry.config(state=tk.NORMAL)
        self.retry_delay_entry.config(state=tk.NORMAL)
        self.to_email_entry.config(state=tk.NORMAL)
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 更新状态指示器
        self.status_indicator.delete('all')
        self.status_indicator.create_oval(5, 5, 15, 15, fill='#95A5A6', outline='')  # 灰色
        self.status_text_label.config(text='已停止', fg='#7F8C8D')
        
        # 更新状态
        self.status_label.config(text='状态: 已停止', fg='#E74C3C')
        self._add_log('INFO', '监控已停止')
    
    def _add_log(self, level, message):
        """添加日志到显示区域"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _process_log_queue(self):
        """处理日志队列中的消息"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self._add_log(log_entry['level'], log_entry['message'])
                
                # 更新最后检查时间
                if '开始检测' in log_entry['message']:
                    self.last_check_label.config(text=f"最后检查: {log_entry['timestamp']}")
        except queue.Empty:
            pass
        
        # 每100ms检查一次
        self.root.after(100, self._process_log_queue)
    
    def _clear_logs(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def run(self):
        """运行GUI主循环"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            # 关闭窗口前停止监控
            if self.is_running:
                self._stop_monitoring()


def main():
    """主函数"""
    try:
        app = MonitorGUI()
        app.run()
    except Exception as e:
        messagebox.showerror('错误', f'程序运行错误: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
