# Gateway on macOS

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不再 bundle runtime——解耦 app 和 Gateway

OpenClaw.app 不再把 Node/Bun 或 Gateway runtime 打包进 app,而是要求用户单独安装 `openclaw` CLI。

**为什么这样设计?** 因为打包会导致**版本锁定**。想象一个场景:
- App 更新了(用户从 App Store 自动更新)
- 但打包的 Gateway runtime 还是旧版(有 bug)
- 用户报 bug,开发者发现是新 app + 旧 runtime 的组合问题

或者反过来:
- Gateway runtime 发布了紧急安全修复
- 但 app 没更新,用户还在用打包的旧 runtime
- 安全漏洞持续存在

**解耦的好处是独立更新**: 用户可以用 `npm install -g openclaw@latest` 更新 Gateway,不用等 app 更新。App 更新时也不用重新打包 Gateway。两者的发布周期完全独立。

App 通过版本兼容性检查确保 app 和 Gateway 版本匹配,避免"app 太新,Gateway 太旧"或反过来。

### LaunchAgent vs 子进程——为什么 launchd 更好

macOS app 不把 Gateway 作为子进程启动,而是用 macOS 原生的 **LaunchAgent**(系统服务管理器,每个用户有自己的 LaunchAgent)来管理 Gateway。这给了三个关键收益:

1. **开机自启**: 用户登录 macOS 时,LaunchAgent 自动启动 Gateway,不需要用户手动运行 app
2. **崩溃自动重启**: Gateway 崩溃后,LaunchAgent 自动重启它,不需要用户干预
3. **App 退出不影响 Gateway**: 用户退出 macOS app,LaunchAgent 保持 Gateway 运行(Gateway 是独立服务,不是 app 的子进程)

**为什么子进程模式不好?** 如果 app 把 Gateway 当子进程启动:
- App 退出 → 子进程被杀 → Gateway 挂了 → 所有连接 Gateway 的设备(node、channel)都断开
- App 崩溃 → 同上
- 用户必须保持 app 运行,Gateway 才能工作

LaunchAgent 模式让 Gateway 成为**真正的后台服务**——app 只是管理界面,不是 Gateway 的"父进程"。用户可以打开 app 看看状态、配置一下,然后退出,Gateway 继续工作。

这跟 Docker Desktop 和 Docker Engine 的关系类似——Desktop 是 GUI,Engine 是后台服务,Desktop 退出 Engine 继续跑。但 OpenClaw 更彻底: Gateway 完全由 launchd 管理,app 不持有 Gateway 进程。

### Attach-only 模式——不管理,只连接

`--attach-only` 或 `--no-launchd` 让 app **从不**安装或管理 LaunchAgent,只连接到已经运行的 Gateway。

**适合什么场景?** 高级用户自己管理 Gateway(比如用 Homebrew services、launchd 手动配置、systemd),app 只是客户端 UI。用户不需要 app 帮他们启动 Gateway——他们已经启动了,app 只需要连接。

**为什么有这个选项?** 因为有些用户觉得"app 帮我管理 Gateway"是多余的——他们有自己的服务管理方案,app 不应该干涉。Attach-only 模式让 app 退化为"纯客户端",不碰 LaunchAgent 配置。

这跟 kubectl 的 `--kubeconfig` 类似——kubectl 不帮你管理集群,只连接到你指定的集群。OpenClaw app 的 attach-only 也是这样: 不管理 Gateway,只连接到已运行的 Gateway。
