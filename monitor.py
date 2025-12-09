#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Developer System Status Monitor
监控 App Store - In-App Purchases 服务状态
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
from datetime import datetime
import json
import re
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any
import config

# 配置日志
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别以显示详细解析信息
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def _log_to_queue(log_queue, level, message):
    """将日志消息发送到队列（用于GUI显示）"""
    if log_queue:
        try:
            log_queue.put_nowait({
                'level': level,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except:
            pass  # 队列已满，忽略


class AppleStatusMonitor:
    """Apple Developer System Status 监控器"""
    
    def __init__(self, check_interval=None, retry_count=None, retry_delay=None, 
                 to_email=None, log_queue=None, stop_event=None):
        self.url = config.MONITOR_URL
        self.target_service = config.TARGET_SERVICE
        # 支持从外部传入参数，如果没有则使用config中的默认值
        self.check_interval = check_interval if check_interval is not None else config.CHECK_INTERVAL
        self.retry_count = retry_count if retry_count is not None else config.RETRY_COUNT
        self.retry_delay = retry_delay if retry_delay is not None else config.RETRY_DELAY
        self.status_data_url = getattr(config, 'STATUS_DATA_URL', None)
        self.normalized_target = self._normalize_service_name(self.target_service)
        
        # 邮件配置（支持从外部传入收件人邮箱）
        self.smtp_config = config.EMAIL_CONFIG.copy()
        if to_email:
            self.smtp_config['to_email'] = to_email
        
        # 状态记录文件
        self.state_file = Path(__file__).parent / "state.json"
        self.last_status = self._load_last_status()
        
        # GUI支持：日志队列和停止事件
        self.log_queue = log_queue
        self.stop_event = stop_event
        self._running = False
        
    def _load_last_status(self) -> Optional[str]:
        """加载上次的状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get('last_status')
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        return None
    
    def _save_status(self, status: str, timestamp: str):
        """保存当前状态"""
        try:
            state = {
                'last_status': status,
                'last_check_time': timestamp
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def _normalize_service_name(self, text: Optional[str]) -> str:
        """统一服务名称便于匹配"""
        if not text:
            return ""
        normalized = unicodedata.normalize('NFKC', str(text))
        normalized = normalized.replace('–', '-').replace('—', '-')
        normalized = normalized.lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()
    
    def _is_event_active(self, event: Dict[str, Any]) -> bool:
        """判断事件是否仍在进行"""
        status = (event.get('eventStatus') or '').strip().lower()
        resolved_status = {'resolved', 'completed', 'closed'}
        if status in resolved_status:
            return False
        epoch_end = event.get('epochEndDate')
        end_date = (event.get('endDate') or '').strip()
        if status == '' and (epoch_end not in (None, 0) or end_date):
            return False
        return True
    
    def _format_event_summary(self, event: Dict[str, Any]) -> str:
        """构建事件摘要（用于告警信息）"""
        status_label = (event.get('statusType') or event.get('eventStatus') or 'Unknown').strip()
        start = (event.get('startDate') or event.get('datePosted') or '').strip()
        end = (event.get('endDate') or '').strip()
        if not end:
            end = '进行中'
        message = (event.get('message') or '').strip()
        return f"{status_label} [{start or '未知开始'} - {end}] {message}"
    
    def _fetch_status_from_api(self) -> Dict[str, Any]:
        """通过官方数据接口获取服务状态"""
        if not self.status_data_url:
            return {
                'status': None,
                'error_type': '配置错误',
                'error_message': '未配置 STATUS_DATA_URL，无法调用状态数据接口'
            }
        
        last_error = None
        data = None
        
        for attempt in range(1, self.retry_count + 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(self.status_data_url, headers=headers, timeout=30)
                response.raise_for_status()
                payload = response.text.strip()
                
                if payload.startswith('jsonCallback('):
                    payload = payload[len('jsonCallback('):]
                    if payload.endswith(');'):
                        payload = payload[:-2]
                
                data = json.loads(payload)
                break
            except Exception as e:
                last_error = e
                logger.warning(f"调用状态数据接口失败 (尝试 {attempt}/{self.retry_count}): {e}")
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
        
        if data is None:
            return {
                'status': None,
                'error_type': '数据接口错误',
                'error_message': f'状态数据接口请求失败: {last_error}'
            }
        
        services = data.get('services', [])
        for service in services:
            service_name = service.get('serviceName', '')
            if self._normalize_service_name(service_name) == self.normalized_target:
                events = service.get('events') or []
                active_events = [event for event in events if self._is_event_active(event)]
                
                if active_events:
                    summaries = [self._format_event_summary(event) for event in active_events[:3]]
                    logger.warning(f"状态数据接口显示存在未解决事件: {' | '.join(summaries)}")
                    return {
                        'status': 'Unavailable',
                        'error_type': '服务状态异常',
                        'error_message': f"状态数据接口显示存在未解决事件: {' | '.join(summaries)}"
                    }
                
                logger.info("状态数据接口返回：服务正常")
                return {
                    'status': 'Available',
                    'error_type': None,
                    'error_message': None
                }
        
        return {
            'status': None,
            'error_type': '服务未找到',
            'error_message': f'状态数据接口中未找到服务: {self.target_service}'
        }
    
    def _send_email(self, subject: str, body: str, error_type: str = None):
        """发送邮件通知"""
        # 检查邮件配置是否已设置
        if (self.smtp_config.get('from_email') == 'your_email@gmail.com' or 
            self.smtp_config.get('to_email') == 'notify@example.com' or
            self.smtp_config.get('password') == 'your_app_password' or
            self.smtp_config.get('password') == 'your_sina_password'):
            logger.warning("邮件配置未设置，跳过邮件发送。请在config.py中配置邮件信息。")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            # 支持多个收件人（逗号分隔）
            to_emails = self.smtp_config['to_email']
            if isinstance(to_emails, str):
                # 如果是字符串，可能是多个邮箱用逗号分隔
                to_emails = [e.strip() for e in to_emails.split(',')]
            elif not isinstance(to_emails, list):
                to_emails = [to_emails]
            msg['To'] = ', '.join(to_emails)  # 邮件头使用逗号分隔
            msg['Subject'] = subject
            
            # 构建纯文本邮件正文（作为备选）
            email_body_plain = f"""
监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
监控服务: {self.target_service}
监控URL: {self.url}

"""
            
            if error_type:
                email_body_plain += f"异常类型: {error_type}\n\n"
            
            email_body_plain += f"详细信息:\n{body}\n\n"
            email_body_plain += f"查看具体状态: https://developer.apple.com/system-status/\n\n"
            email_body_plain += f"---\n此邮件由 Apple Developer Status Monitor 自动发送"
            
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
            <div class="info-value">{self.target_service}</div>
        </div>
        
        <div class="info-item">
            <div class="info-label">监控URL</div>
            <div class="info-value">{self.url}</div>
        </div>
"""
            
            if error_type:
                email_body_html += f"""
        <div class="error-type">
            <div class="info-label">异常类型</div>
            <div class="info-value">{error_type}</div>
        </div>
"""
            
            email_body_html += f"""
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
            use_ssl = self.smtp_config.get('use_ssl', False)
            use_tls = self.smtp_config.get('use_tls', False)
            
            # 准备收件人列表
            to_emails = self.smtp_config['to_email']
            if isinstance(to_emails, str):
                to_emails = [e.strip() for e in to_emails.split(',')]
            elif not isinstance(to_emails, list):
                to_emails = [to_emails]
            
            if use_ssl:
                # 使用SSL连接（如新浪邮箱）
                with smtplib.SMTP_SSL(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                    server.login(self.smtp_config['from_email'], self.smtp_config['password'])
                    server.sendmail(self.smtp_config['from_email'], to_emails, msg.as_string())
            else:
                # 使用普通SMTP连接，可选TLS
                with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                    if use_tls:
                        server.starttls()
                    server.login(self.smtp_config['from_email'], self.smtp_config['password'])
                    server.sendmail(self.smtp_config['from_email'], to_emails, msg.as_string())
            
            logger.info(f"邮件通知发送成功: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"邮件认证失败，请检查邮箱和密码配置: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def _check_and_notify(self):
        """执行一次检测并发送通知"""
        check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"开始检测 [{check_time}]"
        logger.info(log_msg)
        _log_to_queue(self.log_queue, 'INFO', log_msg)
        
        # 仅使用官方状态数据接口
        result = self._fetch_status_from_api()
        
        # 记录检测结果总结（包含判断依据）
        summary_lines = [
            "=" * 80,
            f"检测结果总结 [{check_time}]",
            f"  服务名称: {self.target_service}",
            f"  检测状态: {result['status'] if result['status'] else 'Unknown'}",
            "  数据来源: 状态数据接口"
        ]
        if result['error_type']:
            summary_lines.append(f"  异常类型: {result['error_type']}")
        if result['error_message']:
            summary_lines.append(f"  详细信息: {result['error_message']}")
        summary_lines.append("=" * 80)
        
        for line in summary_lines:
            logger.info(line)
            _log_to_queue(self.log_queue, 'INFO', line)
        
        # 记录日志
        if result['status'] is None:
            # 接口或配置问题
            error_msg = f"检测失败: {result['error_message']}"
            logger.error(error_msg)
            _log_to_queue(self.log_queue, 'ERROR', error_msg)
            self._send_email(
                subject=f"⚠️ {result['error_type']} - {self.target_service}",
                body=result['error_message'],
                error_type=result['error_type']
            )
            self._save_status("Unknown", check_time)
            
        elif result['status'] == 'Unavailable':
            # 服务不可用
            warn_msg = f"服务状态异常: {result['error_message']}"
            logger.warning(warn_msg)
            _log_to_queue(self.log_queue, 'WARNING', warn_msg)
            # 只在状态变化时发送通知
            if self.last_status != 'Unavailable':
                self._send_email(
                    subject=f"⚠️ 服务状态异常 - {self.target_service}",
                    body=result['error_message'],
                    error_type=result['error_type']
                )
            self._save_status('Unavailable', check_time)
            self.last_status = 'Unavailable'
            
        else:
            # 服务正常
            info_msg = f"服务状态正常: {result['status']}"
            logger.info(info_msg)
            _log_to_queue(self.log_queue, 'INFO', info_msg)
            # 如果从异常恢复到正常，也发送通知
            if self.last_status == 'Unavailable':
                self._send_email(
                    subject=f"✅ 服务已恢复正常 - {self.target_service}",
                    body=f"服务状态已恢复为 Available",
                    error_type="状态恢复"
                )
            self._save_status('Available', check_time)
            self.last_status = 'Available'
    
    def run(self):
        """运行监控循环"""
        self._running = True
        startup_lines = [
            "=" * 60,
            "Apple Developer System Status Monitor 启动",
            f"监控服务: {self.target_service}",
            f"检测间隔: {self.check_interval}秒 ({self.check_interval // 60}分钟)",
            f"重试次数: {self.retry_count}",
            "=" * 60
        ]
        for line in startup_lines:
            logger.info(line)
            _log_to_queue(self.log_queue, 'INFO', line)
        
        try:
            while self._running and (self.stop_event is None or not self.stop_event.is_set()):
                self._check_and_notify()
                wait_msg = f"等待 {self.check_interval}秒后进行下次检测..."
                logger.info(wait_msg)
                _log_to_queue(self.log_queue, 'INFO', wait_msg)
                
                # 使用可中断的sleep
                if self.stop_event:
                    for _ in range(self.check_interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                else:
                    time.sleep(self.check_interval)
            
            stop_msg = "监控已停止"
            logger.info(stop_msg)
            _log_to_queue(self.log_queue, 'INFO', stop_msg)
                
        except KeyboardInterrupt:
            stop_msg = "监控已停止（用户中断）"
            logger.info(stop_msg)
            _log_to_queue(self.log_queue, 'INFO', stop_msg)
        except Exception as e:
            error_msg = f"监控过程发生未预期错误: {e}"
            logger.error(error_msg, exc_info=True)
            _log_to_queue(self.log_queue, 'ERROR', error_msg)
            raise
        finally:
            self._running = False
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self.stop_event:
            self.stop_event.set()


if __name__ == "__main__":
    monitor = AppleStatusMonitor()
    monitor.run()

