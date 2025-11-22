#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Developer System Status Monitor
监控 App Store - In-App Purchases 服务状态
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import logging
from datetime import datetime
import json
import os
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


class AppleStatusMonitor:
    """Apple Developer System Status 监控器"""
    
    def __init__(self):
        self.url = config.MONITOR_URL
        self.target_service = config.TARGET_SERVICE
        self.check_interval = config.CHECK_INTERVAL  # 10分钟 = 600秒
        self.retry_count = config.RETRY_COUNT  # 3次重试
        self.retry_delay = config.RETRY_DELAY  # 重试间隔（秒）
        
        # 邮件配置
        self.smtp_config = config.EMAIL_CONFIG
        
        # 状态记录文件
        self.state_file = Path(__file__).parent / "state.json"
        self.last_status = self._load_last_status()
        
        # 页面结构变化检测
        self.page_structure_hash = self._load_structure_hash()
        
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
    
    def _load_structure_hash(self) -> Optional[str]:
        """加载页面结构哈希"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get('page_structure_hash')
            except Exception as e:
                logger.warning(f"加载结构哈希失败: {e}")
        return None
    
    def _save_status(self, status: str, timestamp: str):
        """保存当前状态"""
        try:
            state = {
                'last_status': status,
                'last_check_time': timestamp,
                'page_structure_hash': self.page_structure_hash
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def _fetch_page_with_retry(self) -> Optional[str]:
        """
        获取页面内容，带重试机制
        返回: HTML内容或None
        """
        for attempt in range(1, self.retry_count + 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(
                    self.url, 
                    headers=headers, 
                    timeout=30,
                    allow_redirects=True
                )
                response.raise_for_status()
                logger.info(f"页面获取成功 (尝试 {attempt}/{self.retry_count})")
                return response.text
                
            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时 (尝试 {attempt}/{self.retry_count}): {e}"
                logger.warning(error_msg)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.ConnectionError as e:
                error_msg = f"连接错误 (尝试 {attempt}/{self.retry_count}): {e}"
                logger.warning(error_msg)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP错误 (尝试 {attempt}/{self.retry_count}): {e}"
                logger.warning(error_msg)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                error_msg = f"未知错误 (尝试 {attempt}/{self.retry_count}): {e}"
                logger.warning(error_msg)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
        
        logger.error(f"页面获取失败，已达到最大重试次数 ({self.retry_count}次)")
        return None
    
    def _calculate_page_structure_hash(self, html_content: str) -> str:
        """计算页面结构哈希值，用于检测页面结构变化"""
        import hashlib
        # 提取关键结构元素（去除动态内容）
        soup = BeautifulSoup(html_content, 'html.parser')
        # 获取所有服务列表的结构
        structure_str = ""
        try:
            # 查找服务列表容器
            services = soup.find_all(['div', 'li', 'tr', 'td'], 
                                    string=lambda text: text and 'App Store' in text)
            for service in services[:5]:  # 只取前5个作为结构样本
                parent = service.parent
                if parent:
                    structure_str += str(parent.get('class', []))
                    structure_str += str(parent.name)
        except:
            pass
        
        # 如果无法提取结构，使用整个页面的关键部分
        if not structure_str:
            try:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    structure_str = str(main_content.get('class', []))
            except:
                structure_str = html_content[:1000]  # 使用前1000字符作为备用
        
        return hashlib.md5(structure_str.encode('utf-8')).hexdigest()
    
    def _try_selenium_fetch(self) -> Optional[str]:
        """尝试使用Selenium获取页面（如果可用）"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            import time
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)
            time.sleep(5)  # 等待JavaScript渲染
            html_content = driver.page_source
            driver.quit()
            logger.info("使用Selenium成功获取页面")
            return html_content
        except ImportError:
            logger.debug("Selenium未安装，跳过Selenium方法")
            return None
        except Exception as e:
            logger.warning(f"Selenium获取页面失败: {e}")
            return None
    
    def _parse_service_status(self, html_content: str) -> Dict[str, Any]:
        """
        解析服务状态
        返回: {
            'status': 'Available' | 'Unavailable' | None,
            'error_type': 错误类型,
            'error_message': 错误信息
        }
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 方法1: 通过文本内容查找服务（支持部分匹配）
            # 先尝试在主要内容区域查找（排除页脚、导航等）
            main_content = soup.find('main') or soup.find('body')
            search_area = main_content if main_content else soup
            
            # 尝试完整匹配，但排除页脚和导航区域
            service_elements = []
            all_matches = soup.find_all(string=lambda text: text and self.target_service in text)
            logger.debug(f"找到 {len(all_matches)} 个包含服务名称的文本节点（包括页脚等）")
            
            for text_node in all_matches:
                # 检查是否在页脚或导航区域
                parent = text_node.parent
                is_excluded = False
                exclusion_path = []
                
                for level in range(10):  # 向上查找10层
                    if parent:
                        classes = str(parent.get('class', [])).lower()
                        tag = parent.name.lower()
                        exclusion_path.append(f"{tag}.{classes[:50]}")
                        
                        # 排除页脚、导航等区域
                        if any(exclude in classes for exclude in ['footer', 'nav', 'navigation', 'header', 'breadcrumb', 'directory']):
                            is_excluded = True
                            logger.debug(f"排除页脚/导航元素: {' -> '.join(exclusion_path[-3:])}")
                            break
                        parent = parent.parent
                    else:
                        break
                
                if not is_excluded:
                    service_elements.append(text_node)
                    logger.debug(f"保留服务元素，路径: {' -> '.join(exclusion_path[-3:])}")
            
            # 如果完整匹配失败，尝试部分匹配
            if not service_elements:
                logger.debug("完整匹配未找到，尝试部分匹配 'in-app purchase'...")
                all_partial_matches = soup.find_all(string=lambda text: text and 'in-app purchase' in text.lower())
                logger.debug(f"找到 {len(all_partial_matches)} 个部分匹配的文本节点")
                
                for text_node in all_partial_matches:
                    parent = text_node.parent
                    is_excluded = False
                    
                    for level in range(10):
                        if parent:
                            classes = str(parent.get('class', [])).lower()
                            if any(exclude in classes for exclude in ['footer', 'nav', 'navigation', 'header', 'breadcrumb', 'directory']):
                                is_excluded = True
                                break
                            parent = parent.parent
                        else:
                            break
                    
                    if not is_excluded:
                        service_elements.append(text_node)
            
            if not service_elements:
                # 检查页面是否可能通过JavaScript动态加载
                # 如果页面包含很少的服务相关文本，可能是动态加载
                all_text = soup.get_text().lower()
                if 'app store' in all_text and len(all_text) < 5000:
                    # 页面可能是动态加载的，尝试使用Selenium
                    logger.info("检测到页面可能是动态加载，尝试使用Selenium...")
                    selenium_html = self._try_selenium_fetch()
                    if selenium_html:
                        return self._parse_service_status(selenium_html)
                    
                    return {
                        'status': None,
                        'error_type': '页面结构变化',
                        'error_message': f'未找到服务 "{self.target_service}"，页面可能是JavaScript动态加载的。建议安装Selenium: pip install selenium'
                    }
                
                return {
                    'status': None,
                    'error_type': '页面结构变化',
                    'error_message': f'未找到服务 "{self.target_service}"，页面结构可能已发生变化'
                }
            
            # 找到服务元素后，查找其状态
            logger.info(f"找到 {len(service_elements)} 个匹配的服务元素")
            
            for idx, service_text in enumerate(service_elements):
                try:
                    # 记录服务文本内容
                    service_text_content = service_text.strip() if service_text else ""
                    logger.debug(f"处理服务元素 {idx+1}: {service_text_content[:100]}")
                    
                    # 获取父元素
                    parent = service_text.parent
                    if not parent:
                        logger.debug(f"服务元素 {idx+1} 没有父元素，跳过")
                        continue
                    
                    # 记录父元素信息
                    parent_tag = parent.name
                    parent_classes = parent.get('class', [])
                    logger.debug(f"服务元素 {idx+1} 父元素: <{parent_tag} class=\"{parent_classes}\">")
                    
                    # 向上查找包含状态的容器
                    container = parent
                    found_status = False
                    
                    for level in range(5):  # 增加查找层级
                        if container:
                            # 获取容器及其所有子元素的文本
                            container_text = container.get_text().strip()
                            container_text_lower = container_text.lower()
                            
                            # 记录容器信息
                            container_tag = container.name
                            container_classes = container.get('class', [])
                            container_id = container.get('id', '')
                            
                            logger.debug(f"  层级 {level} - <{container_tag} class=\"{container_classes}\" id=\"{container_id}\">")
                            logger.debug(f"  文本内容: {container_text[:200]}...")
                            
                            # 方法1: 检查容器类名
                            classes = str(container_classes).lower()
                            
                            # 方法2: 查找状态指示器元素
                            status_elements = container.find_all(
                                ['span', 'div', 'td', 'li', 'svg'],
                                class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['available', 'status', 'green', 'circle', 'indicator'])
                            )
                            
                            # 方法3: 查找包含"Available"文本的元素
                            status_texts = container.find_all(string=lambda text: text and 'available' in text.lower())
                            
                            # 方法4: 检查样式属性中的颜色
                            colored_elements = container.find_all(style=lambda x: x and ('green' in x.lower() or 'rgb' in x.lower()))
                            
                            # 记录找到的状态元素
                            if status_elements:
                                logger.debug(f"  找到状态元素: {len(status_elements)} 个")
                                for se in status_elements[:3]:
                                    logger.debug(f"    - <{se.name} class=\"{se.get('class', [])}\"> {se.get_text()[:50]}")
                            
                            if status_texts:
                                logger.debug(f"  找到状态文本: {len(status_texts)} 个")
                                for st in status_texts[:3]:
                                    logger.debug(f"    - \"{st.strip()[:50]}\"")
                            
                            if colored_elements:
                                logger.debug(f"  找到颜色元素: {len(colored_elements)} 个")
                            
                            # 判断状态
                            # 如果找到Available文本或绿色指示器，认为是可用
                            if status_texts or any('available' in str(elem.get('class', [])).lower() for elem in status_elements):
                                # 检查是否有异常状态指示
                                if any(keyword in container_text_lower for keyword in ['unavailable', 'degraded', 'down', 'error', 'outage']):
                                    logger.warning(f"检测到异常状态关键词")
                                    return {
                                        'status': 'Unavailable',
                                        'error_type': '服务状态异常',
                                        'error_message': f'服务状态异常，检测到异常关键词'
                                    }
                                logger.info(f"✅ 找到明确的状态指示: Available (层级 {level})")
                                found_status = True
                                return {
                                    'status': 'Available',
                                    'error_type': None,
                                    'error_message': None
                                }
                            
                            # 如果找到异常状态指示
                            if any(keyword in container_text_lower for keyword in ['unavailable', 'degraded', 'down', 'error', 'outage', 'maintenance']):
                                found_keywords = [k for k in ["unavailable", "degraded", "down", "error", "outage", "maintenance"] if k in container_text_lower]
                                logger.warning(f"检测到异常状态关键词: {found_keywords}")
                                return {
                                    'status': 'Unavailable',
                                    'error_type': '服务状态异常',
                                    'error_message': f'服务状态异常，检测到异常关键词: {found_keywords[:3]}'
                                }
                            
                            # 检查类名中的状态
                            if any(keyword in classes for keyword in ['unavailable', 'degraded', 'down', 'error']):
                                logger.warning(f"检测到异常状态类名: {classes}")
                                return {
                                    'status': 'Unavailable',
                                    'error_type': '服务状态异常',
                                    'error_message': f'服务状态异常，检测到异常类名'
                                }
                            
                            container = container.parent
                        else:
                            break
                    
                    # 如果遍历完所有层级都没找到明确状态，检查服务行的整体结构
                    logger.debug("未在容器层级找到状态，检查服务行整体结构...")
                    service_row = parent
                    for row_level in range(7):
                        if service_row:
                            row_text = service_row.get_text().strip()
                            row_text_lower = row_text.lower()
                            row_classes = str(service_row.get('class', [])).lower()
                            
                            logger.debug(f"  服务行层级 {row_level}: <{service_row.name} class=\"{service_row.get('class', [])}\">")
                            logger.debug(f"  文本内容: {row_text[:200]}...")
                            
                            # 如果包含Available，认为是可用
                            if 'available' in row_text_lower or 'available' in row_classes:
                                logger.info(f"✅ 在服务行中找到状态: Available (行层级 {row_level})")
                                found_status = True
                                return {
                                    'status': 'Available',
                                    'error_type': None,
                                    'error_message': None
                                }
                            
                            service_row = service_row.parent
                        else:
                            break
                    
                    # 如果找到了服务但无法确定状态，记录详细信息
                    if not found_status:
                        # 检查是否在页脚或导航区域
                        is_footer = False
                        check_parent = parent
                        for _ in range(5):
                            if check_parent:
                                classes = str(check_parent.get('class', [])).lower()
                                if any(exclude in classes for exclude in ['footer', 'nav', 'navigation', 'directory']):
                                    is_footer = True
                                    break
                                check_parent = check_parent.parent
                            else:
                                break
                        
                        if is_footer:
                            logger.warning(f"⚠️ 警告：找到的服务元素位于页脚/导航区域，不是实际的状态页面")
                            logger.warning(f"  原因：页面可能是JavaScript动态加载的，服务状态列表未在初始HTML中")
                            logger.warning(f"  服务文本: {service_text_content}")
                            logger.warning(f"  位置: <{parent_tag} class=\"{parent_classes}\"> (页脚/导航)")
                            logger.warning(f"  建议：安装Selenium以获取JavaScript渲染后的页面内容")
                            logger.warning(f"  当前处理：默认认为服务可用（通常页面只显示异常状态）")
                        else:
                            logger.warning(f"⚠️ 警告：找到服务但无法确定状态")
                            logger.warning(f"  服务文本: {service_text_content}")
                            logger.warning(f"  父元素: <{parent_tag} class=\"{parent_classes}\">")
                            logger.warning(f"  父元素文本: {parent.get_text().strip()[:200]}...")
                            logger.warning(f"  原因：未找到明确的状态指示器（Available/Unavailable等）")
                            logger.warning(f"  当前处理：默认认为可用（通常页面只显示异常状态）")
                    
                    return {
                        'status': 'Available',
                        'error_type': None,
                        'error_message': None
                    }
                    
                except Exception as e:
                    logger.error(f"解析服务元素 {idx+1} 时出错: {e}", exc_info=True)
                    continue
            
            # 如果所有方法都失败，返回结构变化错误
            return {
                'status': None,
                'error_type': '页面结构变化',
                'error_message': f'无法解析服务 "{self.target_service}" 的状态，页面结构可能已发生变化'
            }
            
        except Exception as e:
            logger.error(f"解析页面时发生异常: {e}", exc_info=True)
            return {
                'status': None,
                'error_type': '解析错误',
                'error_message': f'解析页面时发生错误: {str(e)}'
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
            msg['To'] = self.smtp_config['to_email']
            msg['Subject'] = subject
            
            # 构建邮件正文
            email_body = f"""
监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
监控服务: {self.target_service}
监控URL: {self.url}

"""
            
            if error_type:
                email_body += f"异常类型: {error_type}\n\n"
            
            email_body += f"详细信息:\n{body}\n\n"
            email_body += f"---\n此邮件由 Apple Developer Status Monitor 自动发送"
            
            msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
            
            # 根据配置选择SSL或TLS连接
            use_ssl = self.smtp_config.get('use_ssl', False)
            use_tls = self.smtp_config.get('use_tls', False)
            
            if use_ssl:
                # 使用SSL连接（如新浪邮箱）
                with smtplib.SMTP_SSL(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                    server.login(self.smtp_config['from_email'], self.smtp_config['password'])
                    server.send_message(msg)
            else:
                # 使用普通SMTP连接，可选TLS
                with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
                    if use_tls:
                        server.starttls()
                    server.login(self.smtp_config['from_email'], self.smtp_config['password'])
                    server.send_message(msg)
            
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
        logger.info(f"开始检测 [{check_time}]")
        
        # 获取页面内容
        html_content = self._fetch_page_with_retry()
        
        if html_content is None:
            logger.warning("页面获取失败，跳过本次检测")
            return
        
        # 检测页面结构变化
        current_hash = self._calculate_page_structure_hash(html_content)
        if self.page_structure_hash is not None and current_hash != self.page_structure_hash:
            logger.warning("检测到页面结构变化")
            self._send_email(
                subject=f"⚠️ 页面结构变化通知 - {self.target_service}",
                body=f"页面结构哈希值已变化，可能需要更新解析逻辑。\n旧哈希: {self.page_structure_hash}\n新哈希: {current_hash}",
                error_type="页面结构变化"
            )
        self.page_structure_hash = current_hash
        
        # 解析服务状态
        result = self._parse_service_status(html_content)
        
        # 记录日志
        if result['status'] is None:
            # 解析失败（页面结构变化）
            logger.error(f"解析失败: {result['error_message']}")
            self._send_email(
                subject=f"⚠️ {result['error_type']} - {self.target_service}",
                body=result['error_message'],
                error_type=result['error_type']
            )
            self._save_status("Unknown", check_time)
            
        elif result['status'] == 'Unavailable':
            # 服务不可用
            logger.warning(f"服务状态异常: {result['error_message']}")
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
            logger.info(f"服务状态正常: {result['status']}")
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
        logger.info("=" * 60)
        logger.info("Apple Developer System Status Monitor 启动")
        logger.info(f"监控服务: {self.target_service}")
        logger.info(f"检测间隔: {self.check_interval}秒 ({self.check_interval // 60}分钟)")
        logger.info(f"重试次数: {self.retry_count}")
        logger.info("=" * 60)
        
        try:
            while True:
                self._check_and_notify()
                logger.info(f"等待 {self.check_interval}秒后进行下次检测...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止（用户中断）")
        except Exception as e:
            logger.error(f"监控过程发生未预期错误: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    monitor = AppleStatusMonitor()
    monitor.run()

