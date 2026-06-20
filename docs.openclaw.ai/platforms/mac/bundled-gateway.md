# Gateway on macOS

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不再 bundle runtime——解耦 app 和 Gateway

OpenClaw.app 不再 bundle Node/Bun 或 Gateway runtime，而是期望外部 `openclaw` CLI 安装。这跟 VS Code 不再 bundle TypeScript/Node 是一个思路——编辑器是编辑器，运行时是运行时，解耦后各自独立更新。

bundle runtime 的问题是**版本锁定**。App 更新了但 runtime 没更新，或者 runtime 更新了但 app 要重新打包。解耦后用户可以 `npm install -g openclaw@latest` 独立更新 Gateway，app 通过版本兼容性检查确保匹配。

### LaunchAgent vs 子进程——为什么 launchd 更好

macOS app 不启动 Gateway 作为子进程，而是管理 per-user LaunchAgent。这给了三个关键收益：
1. **Auto-start at login**——launchd 在用户登录时自动启动 Gateway
2. **KeepAlive**——Gateway 崩溃后 launchd 自动重启
3. **App quit 不影响 Gateway**——launchd 保持 Gateway 运行，app 只是管理器

这跟 Docker Desktop 的架构是一个思路。Docker Desktop 不启动 Docker Engine 作为子进程，而是通过 HyperKit/WSL2 管理独立的 VM。Engine 崩溃了 VM 自动重启，Desktop 退出 Engine 继续运行。OpenClaw 也是这样：app 是控制面板，Gateway 是 launchd 管理的独立服务。

### Attach-only 模式——不管理，只连接

`--attach-only` 或 `--no-launchd` 让 app **从不**安装或管理 launchd，只 attach 到已运行的 Gateway。这适合高级用户——Gateway 自己管理（比如用 Homebrew services），app 只是客户端。

这跟 kubectl 的 `--kubeconfig` 是一个思路。kubectl 不管理集群，只连接到指定集群。OpenClaw app 的 attach-only 模式也是这样：不管理 Gateway，只连接到已运行的 Gateway。
