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

def test_error_email():
    """测试发送异常邮件（带HTML格式和按钮）"""
    print("=" * 60)
    print("测试异常邮件发送功能（HTML格式）")
    print("=" * 60)
    
    smtp_config = config.EMAIL_CONFIG
    target_service = config.TARGET_SERVICE
    monitor_url = config.MONITOR_URL
    
    print(f"\n发件邮箱: {smtp_config['from_email']}")
    print(f"收件邮箱: {smtp_config['to_email']}")
    print(f"SMTP服务器: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
    print("\n正在发送异常测试邮件...")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = smtp_config['to_email']
        msg['Subject'] = '⚠️ 服务状态异常 - ' + target_service
        
        # 模拟异常信息
        error_type = "服务状态异常"
        body = "状态数据接口显示存在未解决事件: Maintenance [2025-01-15 10:00:00 - 进行中] 系统维护中，部分功能可能暂时不可用"
        
        # 构建纯文本邮件正文（作为备选）
        email_body_plain = f"""
监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
监控服务: {target_service}
监控URL: {monitor_url}

异常类型: {error_type}

详细信息:
{body}

查看具体状态: https://developer.apple.com/system-status/

---
此邮件由 Apple Developer Status Monitor 自动发送
"""
        
        # 构建HTML邮件正文
        status_url = "https://developer.apple.com/system-status/"
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        email_body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 2px solid #007AFF;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .header h2 {{
            margin: 0;
            color: #007AFF;
            font-size: 20px;
        }}
        .info-item {{
            margin: 15px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 3px solid #007AFF;
            border-radius: 4px;
        }}
        .info-label {{
            font-weight: bold;
            color: #555;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #333;
        }}
        .error-type {{
            background-color: #fff3cd;
            border-left-color: #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .error-type .info-label {{
            color: #856404;
        }}
        .details {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .status-button {{
            display: inline-block;
            padding: 14px 32px;
            background-color: #007AFF;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            transition: background-color 0.3s;
            box-shadow: 0 2px 4px rgba(0,122,255,0.3);
        }}
        .status-button:hover {{
            background-color: #0051D5;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🍎 Apple Developer System Status Monitor</h2>
        </div>
        
        <div class="info-item">
            <div class="info-label">监控时间</div>
            <div class="info-value">{check_time}</div>
        </div>
        
        <div class="info-item">
            <div class="info-label">监控服务</div>
            <div class="info-value">{target_service}</div>
        </div>
        
        <div class="info-item">
            <div class="info-label">监控URL</div>
            <div class="info-value">{monitor_url}</div>
        </div>
        
        <div class="error-type">
            <div class="info-label">异常类型</div>
            <div class="info-value">{error_type}</div>
        </div>
        
        <div class="info-item">
            <div class="info-label">详细信息</div>
            <div class="details">{body}</div>
        </div>
        
        <div class="button-container">
            <a href="{status_url}" class="status-button">查看具体状态</a>
        </div>
        
        <div class="footer">
            此邮件由 Apple Developer Status Monitor 自动发送
        </div>
    </div>
</body>
</html>
"""
        
        # 添加HTML和纯文本两种格式（邮件客户端会自动选择）
        msg.attach(MIMEText(email_body_plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(email_body_html, 'html', 'utf-8'))
        
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
        
        print("✅ 异常邮件发送成功！请检查收件箱。")
        print("   邮件包含HTML格式和'查看具体状态'按钮。")
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
    # 测试异常邮件（带HTML格式和按钮）
    success = test_error_email()
    if success:
        print("\n" + "=" * 60)
        print("异常邮件测试成功！请检查收件箱查看HTML格式和按钮效果。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("异常邮件测试失败，请检查配置后重试。")
        print("=" * 60)
        sys.exit(1)

