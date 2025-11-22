# -*- coding: utf-8 -*-
"""
配置文件示例
复制此文件为 config.py 并修改配置
"""

# 监控配置
MONITOR_URL = "https://developer.apple.com/system-status/"
TARGET_SERVICE = "App Store - In-App Purchases"
CHECK_INTERVAL = 600  # 检测间隔（秒），10分钟 = 600秒
RETRY_COUNT = 3  # 请求失败重试次数
RETRY_DELAY = 5  # 重试间隔（秒）

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # SMTP服务器地址
    'smtp_port': 587,  # SMTP端口
    'use_tls': True,  # 是否使用TLS加密
    'from_email': 'your_email@gmail.com',  # 发件人邮箱（需要修改）
    'password': 'your_app_password',  # 邮箱密码或应用专用密码（需要修改）
    'to_email': 'notify@example.com',  # 收件人邮箱（需要修改）
}

# 常用邮箱SMTP配置参考：
# Gmail: smtp.gmail.com:587 (需要开启"应用专用密码")
# QQ邮箱: smtp.qq.com:587 (需要开启SMTP服务并使用授权码)
# 163邮箱: smtp.163.com:25 或 smtp.163.com:587
# Outlook: smtp-mail.outlook.com:587

