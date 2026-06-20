# Gateway lifecycle on macOS

## 架构精读

> 跳过不影响阅读翻译正文。

### Launchd 的两个核心能力——开机自启 + 崩溃重启

macOS app 通过 launchd(macOS 的系统服务管理器,类似 Linux 的 systemd)管理 Gateway 生命周期,利用 launchd 的两个核心特性:
1. **开机自启**: 用户登录 macOS 时,launchd 自动启动 Gateway,不需要用户手动运行
2. **崩溃自动重启**: Gateway 进程崩溃后,launchd 自动重启它,不需要用户干预

**为什么这两个能力重要?** 没有开机自启,用户每次重启电脑都要手动启动 Gateway——对"后台服务"来说这是不可接受的。没有崩溃重启,Gateway 崩了就彻底挂了,直到用户发现问题手动重启。

这跟 Linux 的 systemd 的 `Restart=always` 配置是一个思路——systemd 管理的进程崩溃后自动重启。launchd 的 KeepAlive 是同样的语义,但 macOS 原生支持,不需要额外配置。

### Attach-first 策略——先检查再启动

App 启动时先做一件事: 检查 Gateway 是否已经在跑(通过检查配置的端口)。如果已经在跑,就**连接**到已运行的 Gateway;如果没有,才用 launchd 启动一个新的。

**为什么这样设计?** 避免**重复启动**。如果 Gateway 已经在跑(比如 launchd 开机时已经启动了,或者用户手动启动了),app 不应该再启动一个。两个 Gateway 同时跑会冲突——端口占用、状态不一致、命令路由混乱。

这跟 Kubernetes 的 leader election 是一个思路——多个 controller 启动时,只有一个成为 leader,其他的连接到 leader 而不是各自独立运行。OpenClaw 也是这样: app 发现 Gateway 已运行就连接,不重复启动。

### Disable-launchagent 标记——开发模式的逃生口

未签名的开发构建(开发者本地编译的 app,没有 Apple Developer 签名)会在 `~/.openclaw/disable-launchagent` 写一个标记文件。这个标记告诉 app: **不要用 launchd 管理 Gateway**,因为 launchd 配置会指向未签名的二进制文件,macOS 会拒绝运行。

正式签名的构建(App Store 或 Developer ID 签名)会自动清除这个标记,恢复 launchd 管理。

**为什么需要这个标记?** 因为开发者本地调试时,编译出来的 app 是未签名的。如果 launchd 指向未签名的 Gateway,macOS 会阻止运行,开发者就没法调试了。标记文件让开发者可以手动启动 Gateway,绕过 launchd 的签名检查。

这跟 feature flag(功能开关)是一个思路——用一个文件作为开关,控制是否启用 launchd 管理。开发模式下禁用 launchd(避免签名问题),production 模式下启用(获得开机自启和崩溃重启)。

### Remote mode——从不启动本地 Gateway

Remote mode 下,app **从不**启动本地 Gateway,而是通过 SSH tunnel 或 WebSocket 连接远程机器上的 Gateway。

**适合什么场景?** Gateway 跑在服务器或远程机器上,本地 app 只是 UI 控制面板。用户在本地 app 上操作,命令通过 SSH/WebSocket 转发到远程 Gateway 执行。

这跟 VS Code Remote 是一个思路——本地 VS Code 只是编辑器 UI,代码执行在远程机器上。OpenClaw 的 remote mode 也是这样: 本地 app 只是控制面板,Gateway 在远程运行。
