#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邮件发送功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_email():
    """测试邮件发送"""
    print("=" * 60)
    print("测试邮件发送功能")
    print("=" * 60)
    
    smtp_config = config.EMAIL_CONFIG
    
    print(f"\n发件邮箱: {smtp_config['from_email']}")
    print(f"收件邮箱: {smtp_config['to_email']}")
    print(f"SMTP服务器: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
    print("\n正在发送测试邮件...")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = smtp_config['to_email']
        msg['Subject'] = 'Apple Developer Status Monitor - 测试邮件'
        
        body = f"""
这是一封测试邮件，用于验证邮件配置是否正确。

发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果你收到这封邮件，说明邮件配置正确，监控系统可以正常发送通知。

---
Apple Developer Status Monitor
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 根据配置选择SSL或TLS连接
        use_ssl = smtp_config.get('use_ssl', False)
        use_tls = smtp_config.get('use_tls', False)
        
        if use_ssl:
            # 使用SSL连接（如新浪邮箱）
            with smtplib.SMTP_SSL(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                server.login(smtp_config['from_email'], smtp_config['password'])
                server.send_message(msg)
        else:
            # 使用普通SMTP连接，可选TLS
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_config['from_email'], smtp_config['password'])
                server.send_message(msg)
        
        print("✅ 邮件发送成功！请检查收件箱。")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 邮件认证失败: {e}")
        print("\n提示：")
        if 'sina.com' in smtp_config['smtp_server']:
            print("1. 新浪邮箱需要在邮箱设置中开启SMTP服务")
            print("2. 登录新浪邮箱 -> 设置 -> 账户 -> POP3/SMTP服务 -> 开启")
            print("3. 如果提示需要授权码，请使用授权码而不是登录密码")
        elif 'gmail.com' in smtp_config['smtp_server']:
            print("1. Gmail需要使用应用专用密码，不是普通密码")
            print("2. 请访问 https://myaccount.google.com/apppasswords 生成应用专用密码")
            print("3. 确保已开启两步验证")
        else:
            print("1. 请检查邮箱和密码是否正确")
            print("2. 确认已在邮箱设置中开启SMTP服务")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送邮件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email()
    if success:
        print("\n" + "=" * 60)
        print("邮件测试成功！现在可以启动监控了。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("邮件测试失败，请检查配置后重试。")
        print("=" * 60)
        sys.exit(1)

