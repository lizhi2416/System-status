# -*- coding: utf-8 -*-
"""
配置文件
请根据实际情况修改以下配置
"""

# 监控配置
MONITOR_URL = "https://developer.apple.com/system-status/"
TARGET_SERVICE = "App Store - In-App Purchases"
CHECK_INTERVAL = 300  # 检测间隔（秒），1分钟 = 60秒
RETRY_COUNT = 3  # 请求失败重试次数
RETRY_DELAY = 5  # 重试间隔（秒）

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.sina.com',  # SMTP服务器地址（新浪邮箱）
    'smtp_port': 465,  # SMTP端口（新浪邮箱使用465 SSL或25非加密）
    'use_ssl': True,  # 是否使用SSL加密（新浪邮箱推荐使用SSL）
    'use_tls': False,  # 是否使用TLS加密（新浪邮箱使用SSL，不使用TLS）
    'from_email': 'lizhi100415@sina.com',  # 发件人邮箱（你的新浪邮箱）
    'password': 'jianglizhi2416',  # 新浪邮箱密码或授权码（需要在邮箱设置中开启SMTP服务）
    'to_email': '674194760@qq.com',  # 收件人邮箱
}

# 常用邮箱SMTP配置参考：
# Gmail: smtp.gmail.com:587, use_tls=True (需要开启"应用专用密码")
# 新浪邮箱: smtp.sina.com:465, use_ssl=True (需要在邮箱设置中开启SMTP服务)
# QQ邮箱: smtp.qq.com:587, use_tls=True (需要开启SMTP服务并使用授权码)
# 163邮箱: smtp.163.com:25 或 smtp.163.com:587, use_tls=True
# Outlook: smtp-mail.outlook.com:587, use_tls=True

