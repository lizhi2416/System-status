# macOS 应用"已损坏"问题解决方案

## 问题原因

当你在其他 Mac 电脑上打开使用 `./build_app.sh` 构建的应用时，如果显示"已损坏"或"无法打开"，这是因为：

1. **未进行代码签名**：macOS 的 Gatekeeper 安全机制会检查应用的签名
2. **隔离属性**：从网络下载或通过其他方式传输的应用会被标记隔离属性（quarantine）

## 解决方案

### 方案一：临时解决方案（推荐用于测试）

**在接收应用的 Mac 上执行：**

```bash
# 移除隔离属性
xattr -cr /path/to/AppleStatusMonitor.app

# 或者如果应用在下载文件夹
xattr -cr ~/Downloads/AppleStatusMonitor.app
```

**或者通过右键菜单：**
1. 右键点击应用
2. 选择"打开"
3. 在弹出的警告中点击"打开"

### 方案二：代码签名（推荐用于分发）

#### 2.1 获取开发者证书

你需要：
- **免费方案**：使用个人 Apple ID 创建自签名证书（仅限个人使用）
- **付费方案**：Apple Developer Program ($99/年)，获得 "Developer ID Application" 证书（可分发）

#### 2.2 查看可用证书

```bash
# 查看所有可用的代码签名证书
security find-identity -v -p codesigning
```

#### 2.3 使用代码签名构建

**方法1：设置环境变量后构建**
```bash
# 设置签名证书（替换为你的证书名称）
export MACOS_SIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"

# 运行构建脚本
./build_app.sh
```

**方法2：使用个人 Apple ID 签名（免费）**
```bash
# 1. 在 Xcode 中登录你的 Apple ID
#    Xcode > Settings > Accounts > 添加 Apple ID

# 2. 创建证书（如果还没有）
#    Xcode > Settings > Accounts > 选择账户 > Manage Certificates
#    点击 + 号 > Apple Development

# 3. 使用证书签名
export MACOS_SIGN_IDENTITY="Apple Development: Your Name (TEAM_ID)"
./build_app.sh
```

#### 2.4 验证签名

```bash
# 验证应用签名
codesign --verify --verbose dist/AppleStatusMonitor.app

# 查看签名详情
codesign -dvv dist/AppleStatusMonitor.app
```

### 方案三：公证（仅限付费开发者）

如果你有 Apple Developer Program 账号，可以对应用进行公证：

```bash
# 1. 先进行代码签名（使用 Developer ID Application 证书）
export MACOS_SIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
./build_app.sh

# 2. 提交公证
xcrun notarytool submit dist/AppleStatusMonitor.app \
    --apple-id your@email.com \
    --team-id YOUR_TEAM_ID \
    --password YOUR_APP_SPECIFIC_PASSWORD \
    --wait

# 3. 装订公证票据
xcrun stapler staple dist/AppleStatusMonitor.app
```

## 更新后的构建脚本功能

更新后的 `build_app.sh` 脚本会自动：

1. **尝试代码签名**：如果设置了 `MACOS_SIGN_IDENTITY` 环境变量或检测到可用证书
2. **移除隔离属性**：如果没有签名证书，自动移除隔离属性
3. **提供详细说明**：在构建完成后显示使用说明

## 快速使用

### 对于开发者（有证书）

```bash
# 设置证书并构建
export MACOS_SIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
./build_app.sh
```

### 对于普通用户（无证书）

```bash
# 直接构建（会自动移除隔离属性）
./build_app.sh

# 分发时告知用户执行：
xattr -cr AppleStatusMonitor.app
```

## 常见问题

### Q: 为什么需要代码签名？
A: macOS 的 Gatekeeper 会阻止未签名或签名无效的应用运行，这是 macOS 的安全机制。

### Q: 免费方案和付费方案的区别？
A: 
- **免费方案**：只能在自己设备上使用，不能分发
- **付费方案**：可以分发，用户无需额外操作即可运行

### Q: 移除隔离属性后还是无法运行？
A: 可能需要：
1. 检查系统设置 > 隐私与安全性 > 允许从"任何来源"下载的应用
2. 使用 `sudo spctl --master-disable` 临时禁用 Gatekeeper（不推荐）

### Q: 如何查看应用的签名状态？
A: 
```bash
codesign -dvv dist/AppleStatusMonitor.app
spctl -a -vv dist/AppleStatusMonitor.app
```

## 参考链接

- [Apple 代码签名文档](https://developer.apple.com/documentation/security/code_signing_services)
- [Gatekeeper 说明](https://support.apple.com/zh-cn/HT202491)
- [PyInstaller macOS 打包指南](https://pyinstaller.org/en/stable/when-things-go-wrong.html#macos)
