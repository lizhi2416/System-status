#!/bin/bash
# -*- coding: utf-8 -*-
# 打包脚本 - 将监控程序打包为桌面应用（tkinter 版本）
# 备注：macOS 使用 onedir + windowed 生成 .app bundle，避免 onefile/windowed 兼容问题

echo "=========================================="
echo "Apple Developer Status Monitor - 打包脚本 (macOS)"
echo "目标: 打包 tkinter 版本 (Python 3.12 / Tk 9.0)"
echo "=========================================="
echo ""

# 使用本地缓存目录，避免权限问题
export PYINSTALLER_CONFIG_DIR="$(pwd)/.pyinstaller"
export PYINSTALLER_CACHE_DIR="$(pwd)/.pyinstaller"

# 选择Python 3.12，若不存在则使用python3
PY_BIN="python3.12"
if ! command -v ${PY_BIN} &> /dev/null; then
    PY_BIN="python3"
fi
echo "使用 Python: $(${PY_BIN} --version 2>/dev/null)"

# 确保 PyInstaller 可用
if ! ${PY_BIN} -m PyInstaller --version &> /dev/null; then
    echo "❌ 未检测到 PyInstaller，正在安装..."
    ${PY_BIN} -m pip install --break-system-packages pyinstaller
fi

# 确保依赖
echo "📦 安装依赖..."
${PY_BIN} -m pip install --break-system-packages requests

echo ""
echo "🔨 开始打包 (tkinter版本)..."
echo ""

# 检测操作系统
OS_TYPE=$(uname -s)
echo "检测到操作系统: $OS_TYPE"

if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS: 使用 onedir + windowed 创建 .app bundle
    echo "使用 macOS 打包模式 (onedir + windowed = .app bundle)"
    ${PY_BIN} -m PyInstaller --onedir \
        --windowed \
        --name "AppleStatusMonitor" \
        --add-data "config.py:." \
        --hidden-import=requests \
        --hidden-import=email \
        --hidden-import=email.mime.text \
        --hidden-import=email.mime.multipart \
        --hidden-import=smtplib \
        --hidden-import=monitor \
        --hidden-import=config \
        --clean \
        monitor_gui_tkinter.py
    
    APP_PATH="dist/AppleStatusMonitor.app"
    EXE_NAME="AppleStatusMonitor.app"
else
    # Linux/其他: 使用 onefile
    echo "使用 Linux/通用打包模式 (onefile)"
    ${PY_BIN} -m PyInstaller --onefile \
        --name "AppleStatusMonitor" \
        --add-data "config.py:." \
        --hidden-import=requests \
        --hidden-import=email \
        --hidden-import=email.mime.text \
        --hidden-import=email.mime.multipart \
        --hidden-import=smtplib \
        --hidden-import=monitor \
        --hidden-import=config \
        --clean \
        monitor_gui_tkinter.py
    
    EXE_NAME="AppleStatusMonitor"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    if [ "$OS_TYPE" = "Darwin" ]; then
        APP_PATH="dist/AppleStatusMonitor.app"
        echo "📁 macOS应用位置: $APP_PATH"
        echo ""
        
        # 尝试代码签名（如果用户有开发者证书）
        SIGN_IDENTITY=""
        if [ -n "$MACOS_SIGN_IDENTITY" ]; then
            SIGN_IDENTITY="$MACOS_SIGN_IDENTITY"
        else
            # 尝试自动查找可用的签名证书
            SIGN_IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)".*/\1/')
        fi
        
        if [ -n "$SIGN_IDENTITY" ]; then
            echo "🔐 正在对应用进行代码签名..."
            codesign --force --deep --sign "$SIGN_IDENTITY" "$APP_PATH" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "✅ 代码签名成功！"
                # 验证签名
                codesign --verify --verbose "$APP_PATH" 2>/dev/null
                if [ $? -eq 0 ]; then
                    echo "✅ 签名验证通过！"
                fi
            else
                echo "⚠️  代码签名失败，将使用备用方案"
                SIGN_IDENTITY=""
            fi
        fi
        
        # 如果没有签名，移除隔离属性（临时解决方案）
        if [ -z "$SIGN_IDENTITY" ]; then
            echo ""
            echo "⚠️  应用未进行代码签名"
            echo "🔧 正在移除隔离属性（临时解决方案）..."
            xattr -cr "$APP_PATH" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "✅ 已移除隔离属性"
            fi
            
            # 创建用户友好的辅助工具
            echo ""
            echo "📦 正在创建用户友好的辅助工具..."
            
            # 创建 .command 脚本（双击运行）
            REMOVE_QUARANTINE_SCRIPT="dist/移除隔离属性.command"
            cat > "$REMOVE_QUARANTINE_SCRIPT" << 'EOFSCRIPT'
#!/bin/bash
# -*- coding: utf-8 -*-
# 移除隔离属性脚本 - 双击运行即可

echo "=========================================="
echo "移除隔离属性工具"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/AppleStatusMonitor.app"

# 如果当前目录没有，尝试查找
if [ ! -d "$APP_PATH" ]; then
    # 尝试在常见位置查找
    if [ -d "$HOME/Downloads/AppleStatusMonitor.app" ]; then
        APP_PATH="$HOME/Downloads/AppleStatusMonitor.app"
    elif [ -d "$HOME/Desktop/AppleStatusMonitor.app" ]; then
        APP_PATH="$HOME/Desktop/AppleStatusMonitor.app"
    else
        echo "❌ 未找到 AppleStatusMonitor.app"
        echo ""
        echo "请将 AppleStatusMonitor.app 放在以下位置之一："
        echo "  - 与此脚本同一目录"
        echo "  - 下载文件夹 (~/Downloads)"
        echo "  - 桌面 (~/Desktop)"
        echo ""
        read -p "或者直接拖拽应用到此窗口，然后按回车: " DRAGGED_APP
        if [ -n "$DRAGGED_APP" ]; then
            # 移除拖拽时可能包含的引号
            APP_PATH=$(echo "$DRAGGED_APP" | sed "s/^['\"]//;s/['\"]$//")
        fi
    fi
fi

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 未找到应用，请确认路径是否正确"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo "找到应用: $APP_PATH"
echo ""
echo "正在移除隔离属性..."

# 移除隔离属性
xattr -cr "$APP_PATH" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 成功移除隔离属性！"
    echo ""
    echo "现在可以正常打开应用了："
    echo "  1. 双击 AppleStatusMonitor.app"
    echo "  2. 或者在 Finder 中右键点击应用，选择'打开'"
    echo ""
else
    echo "⚠️  移除隔离属性时出现问题"
    echo "但应用可能仍然可以运行，请尝试右键点击应用选择'打开'"
    echo ""
fi

read -p "按回车键退出..."
EOFSCRIPT
            chmod +x "$REMOVE_QUARANTINE_SCRIPT"
            
            # 创建用户使用指南文档
            USER_GUIDE="dist/用户使用指南.txt"
            cat > "$USER_GUIDE" << 'EOFGUIDE'
==========================================
AppleStatusMonitor 用户使用指南
==========================================

如果首次打开应用时显示"已损坏"或"无法打开"，请按照以下方式之一解决：

方法一：右键打开（最简单）⭐ 推荐
----------------------------------------
1. 在 Finder 中找到 AppleStatusMonitor.app
2. 右键点击应用图标
3. 选择菜单中的"打开"
4. 在弹出的警告对话框中，点击"打开"按钮

> 注意：不要直接双击应用，必须使用右键菜单中的"打开"选项。

方法二：使用移除隔离属性工具（一键解决）
----------------------------------------
1. 找到"移除隔离属性.command"文件
2. 双击该文件
3. 如果提示"无法打开"，请：
   - 右键点击"移除隔离属性.command"
   - 选择"打开" > "打开"
4. 按照提示操作即可

方法三：系统设置中允许（一次性设置）
----------------------------------------
1. 打开"系统设置"（或"系统偏好设置"）
2. 进入"隐私与安全性"
3. 在"安全性"部分，找到关于应用的提示
4. 点击"仍要打开"或"允许"

正常使用
----------------------------------------
移除隔离属性后，以后就可以直接双击应用正常使用了。

常见问题
----------------------------------------
Q: 为什么会出现"已损坏"的提示？
A: 这是 macOS 的安全机制。当应用通过网络传输（下载、邮件等）时，
   系统会自动添加隔离属性。移除隔离属性后即可正常运行。

Q: 每次都需要这样操作吗？
A: 不需要。只需要在首次运行时操作一次，之后就可以正常使用了。

Q: 有没有更简单的方法？
A: 如果开发者使用了代码签名，就不需要这些操作了。
   但对于未签名的应用，这是最安全的方式。

技术支持
----------------------------------------
如果以上方法都无法解决问题，请联系开发者获取帮助。
EOFGUIDE
            
            echo "✅ 已创建辅助工具："
            echo "   - $REMOVE_QUARANTINE_SCRIPT"
            echo "   - $USER_GUIDE"
        fi
        
        echo ""
        echo "💡 使用说明："
        echo "   - 可以将 $APP_PATH 分发给其他 macOS 用户"
        if [ -z "$SIGN_IDENTITY" ]; then
            echo "   - ⚠️  由于应用未签名，其他用户需要执行以下操作之一："
            echo "     1. 右键点击应用，选择'打开'（首次）⭐ 最简单"
            echo "     2. 双击运行'移除隔离属性.command'工具 ⭐ 推荐"
            echo "     3. 查看'用户使用指南.txt'了解详细步骤"
            echo ""
            echo "   📦 辅助工具已自动生成在 dist/ 目录："
            echo "      - 移除隔离属性.command（双击运行）"
            echo "      - 用户使用指南.txt（详细说明）"
            echo ""
            echo "   📝 如需代码签名，请设置环境变量："
            echo "      export MACOS_SIGN_IDENTITY='Developer ID Application: Your Name (TEAM_ID)'"
            echo "      然后重新运行此脚本"
        else
            echo "   - ✅ 应用已签名，可以直接运行"
        fi
        echo "   - 用户可以直接在GUI界面中配置收件人邮箱"
        echo "   - 邮件SMTP设置需要在应用内或通过编辑配置文件设置"
    else
        echo "📁 可执行文件位置: dist/$EXE_NAME"
        echo ""
        echo "💡 使用说明："
        echo "   - 可以将 dist/$EXE_NAME 分发给其他用户"
        echo "   - 用户可以直接在GUI界面中配置收件人邮箱"
        echo "   - 邮件SMTP设置需要在应用内或通过编辑配置文件设置"
    fi
    echo ""
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
