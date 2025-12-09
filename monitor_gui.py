#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Developer System Status Monitor - GUI版本
使用PySimpleGUI 4创建可视化界面
"""

# 导入PySimpleGUI（xl-gui包提供了PySimpleGUI模块）
try:
    import PySimpleGUI as sg
except ImportError:
    # 如果直接导入失败，尝试其他方式
    try:
        from xl_gui import PySimpleGUI as sg
    except ImportError:
        raise ImportError("无法导入PySimpleGUI，请安装 xl-gui: pip install xl-gui==4.60.5")
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

# 设置PySimpleGUI主题
sg.theme('LightBlue3')

# 日志级别颜色映射
LOG_COLORS = {
    'INFO': 'black',
    'WARNING': 'orange',
    'ERROR': 'red',
    'DEBUG': 'gray'
}


class MonitorGUI:
    """监控程序GUI界面"""
    
    def __init__(self):
        self.monitor = None
        self.monitor_thread = None
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_running = False
        
        # 创建窗口
        self.window = self._create_window()
        
    def _create_window(self):
        """创建GUI窗口"""
        # 使用最简单的布局，移除所有可能有问题的参数
        layout = [
            [sg.Text('Apple Developer System Status Monitor', font=('Arial', 14, 'bold'))],
            [sg.Text('=' * 60)],
            [sg.Text('监控配置', font=('Arial', 12, 'bold'))],
            [sg.Text('检测间隔（分钟）:'), 
             sg.Input(str(config.CHECK_INTERVAL // 60), key='-CHECK_INTERVAL-', size=(10, 1))],
            [sg.Text('失败重试次数:'), 
             sg.Input(str(config.RETRY_COUNT), key='-RETRY_COUNT-', size=(10, 1))],
            [sg.Text('重试间隔（秒）:'), 
             sg.Input(str(config.RETRY_DELAY), key='-RETRY_DELAY-', size=(10, 1))],
            [sg.Text('收件人邮箱:'), 
             sg.Input(config.EMAIL_CONFIG.get('to_email', ''), key='-TO_EMAIL-', size=(30, 1))],
            [sg.Text('监控服务:'), 
             sg.Text(config.TARGET_SERVICE)],
            [sg.Text('监控URL:'), 
             sg.Text(config.MONITOR_URL)],
            [sg.Text('=' * 60)],
            [sg.Text('操作', font=('Arial', 12, 'bold'))],
            [sg.Button('开始监控', key='-START-', size=(12, 1)),
             sg.Button('停止监控', key='-STOP-', size=(12, 1), disabled=True),
             sg.Button('清空日志', key='-CLEAR-', size=(12, 1))],
            [sg.Text('=' * 60)],
            [sg.Text('监控日志', font=('Arial', 12, 'bold'))],
            [sg.Multiline('', key='-LOG-', size=(80, 15), disabled=True)],
            [sg.Text('=' * 60)],
            [sg.Text('状态: 未运行', key='-STATUS-')],
            [sg.Text('', key='-LAST_CHECK-')],
        ]
        
        window = sg.Window(
            'Apple Developer System Status Monitor',
            layout,
            size=(800, 700)
        )
        
        return window
    
    def _validate_inputs(self, values):
        """验证输入参数"""
        errors = []
        
        try:
            check_interval = int(values['-CHECK_INTERVAL-'])
            if check_interval <= 0:
                errors.append('检测间隔必须大于0')
        except ValueError:
            errors.append('检测间隔必须是数字')
        
        try:
            retry_count = int(values['-RETRY_COUNT-'])
            if retry_count < 0:
                errors.append('重试次数不能为负数')
        except ValueError:
            errors.append('重试次数必须是数字')
        
        try:
            retry_delay = int(values['-RETRY_DELAY-'])
            if retry_delay < 0:
                errors.append('重试间隔不能为负数')
        except ValueError:
            errors.append('重试间隔必须是数字')
        
        to_email = values['-TO_EMAIL-'].strip()
        if not to_email:
            errors.append('收件人邮箱不能为空')
        elif '@' not in to_email:
            errors.append('收件人邮箱格式不正确')
        
        return errors
    
    def _start_monitoring(self, values):
        """启动监控"""
        # 验证输入
        errors = self._validate_inputs(values)
        if errors:
            sg.popup_error('\n'.join(errors), title='输入错误')
            return
        
        # 获取配置参数
        check_interval_min = int(values['-CHECK_INTERVAL-'])
        check_interval = check_interval_min * 60  # 转换为秒
        retry_count = int(values['-RETRY_COUNT-'])
        retry_delay = int(values['-RETRY_DELAY-'])
        to_email = values['-TO_EMAIL-'].strip()
        
        # 禁用配置输入和开始按钮
        self.window['-CHECK_INTERVAL-'].update(disabled=True)
        self.window['-RETRY_COUNT-'].update(disabled=True)
        self.window['-RETRY_DELAY-'].update(disabled=True)
        self.window['-TO_EMAIL-'].update(disabled=True)
        self.window['-START-'].update(disabled=True)
        self.window['-STOP-'].update(disabled=False)
        
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
        
        # 更新状态
        self.window['-STATUS-'].update('状态: 运行中', text_color='green')
        self._add_log('INFO', '监控已启动')
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
        
        self.stop_event.set()
        self.is_running = False
        
        # 等待线程结束（最多等待5秒）
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # 恢复UI状态
        self.window['-CHECK_INTERVAL-'].update(disabled=False)
        self.window['-RETRY_COUNT-'].update(disabled=False)
        self.window['-RETRY_DELAY-'].update(disabled=False)
        self.window['-TO_EMAIL-'].update(disabled=False)
        self.window['-START-'].update(disabled=False)
        self.window['-STOP-'].update(disabled=True)
        
        # 更新状态
        self.window['-STATUS-'].update('状态: 已停止', text_color='red')
        self._add_log('INFO', '监控已停止')
    
    def _add_log(self, level, message):
        """添加日志到显示区域"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_text = self.window['-LOG-'].get()
        
        # 根据日志级别设置颜色（PySimpleGUI 4支持文本颜色）
        color = LOG_COLORS.get(level, 'black')
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        # 追加日志
        log_text += log_line
        self.window['-LOG-'].update(log_text)
        
        # 自动滚动到底部（PySimpleGUI 4兼容方式）
        try:
            # 尝试使用set_vscroll_position（如果支持）
            self.window['-LOG-'].set_vscroll_position(1.0)
        except:
            # 如果不支持，使用update的scroll_to_index参数
            try:
                lines = log_text.split('\n')
                self.window['-LOG-'].update(log_text, scroll_to_index=len(lines)-1)
            except:
                pass  # 如果都不支持，至少日志已经添加了
    
    def _process_log_queue(self):
        """处理日志队列中的消息"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self._add_log(log_entry['level'], log_entry['message'])
                
                # 更新最后检查时间
                if '开始检测' in log_entry['message']:
                    self.window['-LAST_CHECK-'].update(
                        f'最后检查: {log_entry["timestamp"]}'
                    )
        except queue.Empty:
            pass
    
    def _clear_logs(self):
        """清空日志"""
        self.window['-LOG-'].update('')
    
    def run(self):
        """运行GUI主循环"""
        while True:
            event, values = self.window.read(timeout=100)  # 100ms超时，用于处理日志队列
            
            if event == sg.WIN_CLOSED:
                break
            
            elif event == '-START-':
                self._start_monitoring(values)
            
            elif event == '-STOP-':
                self._stop_monitoring()
            
            elif event == '-CLEAR-':
                self._clear_logs()
            
            # 处理日志队列
            self._process_log_queue()
        
        # 关闭窗口前停止监控
        if self.is_running:
            self._stop_monitoring()
        
        self.window.close()


def main():
    """主函数"""
    try:
        app = MonitorGUI()
        app.run()
    except Exception as e:
        sg.popup_error(f'程序运行错误: {e}', title='错误')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
