@echo off
REM 打包脚本 - Windows版本
REM 将监控程序打包为桌面应用

echo ==========================================
echo Apple Developer Status Monitor - 打包脚本 (Windows)
echo 目標: 打包 tkinter 版本 (Python 3.12 / Tk 9.0)
echo ==========================================
echo.

REM 选择 Python 3.12，若不存在则使用 python
set PY_BIN=py -3.12
%PY_BIN% --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set PY_BIN=python
)
echo 使用 Python: 
%PY_BIN% --version

REM 检查是否安装了PyInstaller
%PY_BIN% -m PyInstaller --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 PyInstaller，正在安装...
    %PY_BIN% -m pip install pyinstaller
)

REM 检查依赖
echo [信息] 检查依赖...
%PY_BIN% -m pip install requests

echo.
echo [信息] 开始打包 (tkinter版本)...
echo.

REM 使用PyInstaller打包 tkinter 版本 (Windows)
REM Windows 使用 onefile + windowed 创建单个 .exe 文件
%PY_BIN% -m PyInstaller --onefile ^
    --windowed ^
    --name "AppleStatusMonitor" ^
    --add-data "config.py;." ^
    --hidden-import=requests ^
    --hidden-import=email ^
    --hidden-import=email.mime.text ^
    --hidden-import=email.mime.multipart ^
    --hidden-import=smtplib ^
    --hidden-import=monitor ^
    --hidden-import=config ^
    --clean ^
    monitor_gui_tkinter.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 打包成功！
    echo.
    echo [信息] 可执行文件位置: dist\AppleStatusMonitor.exe
    echo.
    echo [提示] 
    echo    - 可以将 dist\AppleStatusMonitor.exe 分发给其他 Windows 用户
    echo    - 首次运行时，Windows 可能会提示安全警告，点击"更多信息"然后"仍要运行"
    echo    - 用户可以直接在GUI界面中配置收件人邮箱
    echo    - 邮件SMTP设置需要在应用内或通过编辑配置文件设置
    echo.
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
    exit /b 1
)

pause
