# Apple Developer System Status Monitor

监控 Apple Developer System Status 页面中 "App Store - In-App Purchases" 服务的状态。

## 功能特性

- ✅ 直接使用苹果官方开发者系统状态数据接口，避免页面结构变化导致误报
- ✅ 可配置检测间隔与重试策略，失败自动重试
- ✅ 服务状态异常与恢复都会邮件通知
- ✅ 详细日志输出，方便审计与排查
- ✅ 依赖极少，部署轻量

## 快速开始

### 1. 安装依赖

使用虚拟环境（推荐）：
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

复制配置文件并修改：
```bash
cp config.example.py config.py
```

编辑 `config.py`，修改以下配置：
- **邮件SMTP配置**：设置发件人邮箱、密码、收件人邮箱
- **监控配置**：确认监控URL和服务名称（默认已配置）
- **STATUS_DATA_URL**：状态数据接口地址（默认指向苹果官方开发者系统状态JSON）

**重要**：如果使用Gmail，需要：
1. 开启两步验证
2. 生成应用专用密码：https://myaccount.google.com/apppasswords
3. 在 `config.py` 中使用应用专用密码

### 3. 测试运行

先测试一次检测（不会进入循环）：
```bash
python test_monitor.py
```

### 4. 正式运行

#### 方式1：使用启动脚本（推荐）
```bash
./run.sh
```

#### 方式2：直接运行
```bash
python monitor.py
```

### 后台运行（Linux/Mac）
```bash
nohup python monitor.py > /dev/null 2>&1 &
```

### 使用 systemd（推荐）

创建服务文件 `/etc/systemd/system/apple-status-monitor.service`：

```ini
[Unit]
Description=Apple Developer Status Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/System-status
ExecStart=/usr/bin/python3 /path/to/System-status/monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable apple-status-monitor
sudo systemctl start apple-status-monitor
sudo systemctl status apple-status-monitor
```

## 文件说明

- `monitor.py` - 主监控脚本
- `config.py` - 配置文件（需要根据实际情况修改）
- `config.example.py` - 配置文件示例
- `requirements.txt` - Python依赖包
- `run.sh` - 启动脚本（自动创建虚拟环境并运行）
- `logs/` - 日志目录（自动创建）
- `state.json` - 状态记录文件（自动创建，记录上次检测状态）

## 日志

日志文件保存在 `logs/` 目录下，按日期命名：`monitor_YYYYMMDD.log`

## 邮件通知

### Gmail配置
1. 开启两步验证
2. 生成应用专用密码：https://myaccount.google.com/apppasswords
3. 在 `config.py` 中使用应用专用密码

### QQ邮箱配置
1. 开启SMTP服务
2. 获取授权码
3. 在 `config.py` 中使用授权码作为密码

## 异常类型说明

监控脚本会识别以下异常类型：

- **数据接口错误** - 无法从官方状态数据接口获取信息
- **服务未找到** - 接口数据中缺少目标服务
- **服务状态异常** - 服务状态非 Available
- **状态恢复** - 服务从异常状态恢复到正常

## 注意事项

1. 确保服务器可以访问 `https://www.apple.com/support/systemstatus/data/developer/system_status_en_US.js`
2. 邮件配置需要正确，建议先测试邮件发送功能
3. 定期检查日志文件，确保监控正常运行

