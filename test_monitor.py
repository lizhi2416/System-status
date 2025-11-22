#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试监控脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from monitor import AppleStatusMonitor
import logging

# 设置日志级别为DEBUG以便查看详细信息
logging.basicConfig(level=logging.DEBUG)

# 临时修改配置以便测试
import config
config.CHECK_INTERVAL = 10  # 测试时使用10秒间隔
config.EMAIL_CONFIG['from_email'] = 'test@example.com'  # 测试邮箱，不会真正发送

print("=" * 60)
print("测试监控脚本")
print("=" * 60)

monitor = AppleStatusMonitor()

# 执行一次检测
print("\n执行一次检测...")
monitor._check_and_notify()

print("\n测试完成！")

