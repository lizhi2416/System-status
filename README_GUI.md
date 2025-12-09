# Apple Developer System Status Monitor - GUI版本

这是一个带有图形界面的Apple Developer系统状态监控程序，使用PySimpleGUI 4开发。

## 功能特性

- ✅ 可视化操作界面
- ✅ 可配置检测间隔（分钟）
- ✅ 可配置失败重试次数
- ✅ 可配置重试间隔（秒）
- ✅ 可配置收件人邮箱
- ✅ 开始/停止监控按钮
- ✅ 实时显示监控日志
- ✅ 支持导出为桌面应用

## 安装依赖

**注意**：由于PySimpleGUI 4已从PyPI移除，我们使用社区维护的 `xl-gui` 包（兼容PySimpleGUI 4）。

```bash
pip install -r requirements.txt
```

**macOS用户注意**：如果遇到tkinter相关错误，请使用系统Python（`/usr/bin/python3`）运行程序。

## 运行GUI版本

**重要**：为了确保GUI正常显示，建议使用Python 3.12（Tk 9.0）：

```bash
python3.12 monitor_gui_tkinter.py
```

或者使用启动脚本：

```bash
./run_gui.sh
```

**注意**：
- 旧版Python（如Python 3.9）的tkinter可能无法正常显示GUI内容
- 如果遇到GUI显示问题，请使用Python 3.12或更高版本
- 程序使用原生tkinter实现，不依赖PySimpleGUI

## 打包为桌面应用

### macOS/Linux

```bash
chmod +x build_app.sh
./build_app.sh
```

打包完成后，可执行文件位于 `dist/AppleStatusMonitor`

### Windows

双击运行 `build_app.bat` 或在命令行中执行：

```cmd
build_app.bat
```

打包完成后，可执行文件位于 `dist\AppleStatusMonitor.exe`

## 使用说明

1. **启动程序**：运行 `monitor_gui.py` 或打包后的可执行文件

2. **配置参数**：
   - **检测间隔（分钟）**：设置每次检测之间的间隔时间（分钟）
   - **失败重试次数**：当检测失败时，重试的次数
   - **重试间隔（秒）**：重试之间的等待时间（秒）
   - **收件人邮箱**：接收监控通知的邮箱地址

3. **开始监控**：点击"开始监控"按钮，程序将在后台运行监控任务

4. **查看日志**：监控日志会实时显示在日志区域，包括：
   - 检测开始时间
   - 检测结果
   - 服务状态变化
   - 错误信息

5. **停止监控**：点击"停止监控"按钮可以随时停止监控

6. **清空日志**：点击"清空日志"按钮可以清空日志显示区域

## 注意事项

1. **邮件配置**：首次使用前，需要在 `config.py` 中配置发件邮箱的SMTP设置：
   - `smtp_server`: SMTP服务器地址
   - `smtp_port`: SMTP端口
   - `from_email`: 发件人邮箱
   - `password`: 邮箱密码或授权码
   - `use_ssl` / `use_tls`: 加密方式

2. **收件人邮箱**：可以在GUI界面中直接配置，也可以在 `config.py` 中设置默认值

3. **监控服务**：默认监控 "App Store - In-App Purchases" 服务，可以在 `config.py` 中修改 `TARGET_SERVICE`

## 打包说明

打包后的应用包含所有依赖，可以在没有安装Python的机器上运行。但是：

- 用户仍然需要配置 `config.py` 中的邮件设置（如果使用默认配置）
- 或者直接在GUI界面中配置收件人邮箱（如果发件邮箱已在config.py中配置好）

## 技术栈

- Python 3.x
- PySimpleGUI 4.60.5
- requests
- PyInstaller (用于打包)

## 许可证

MIT License
