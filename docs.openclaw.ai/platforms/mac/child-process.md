# Gateway lifecycle on macOS

## 架构精读

> 跳过不影响阅读翻译正文。

### Launchd 作为生命周期管理器——auto-start + KeepAlive

macOS app 通过 launchd 管理 Gateway 生命周期，利用 launchd 的两个核心特性：
1. **Auto-start at login**——用户登录时自动启动 Gateway
2. **KeepAlive**——Gateway 崩溃后自动重启

这跟 systemd 的 `Restart=always` 是一个思路。systemd unit 可以配置 `Restart=always`，进程退出后自动重启。launchd 的 KeepAlive 是同样的语义，但 macOS 原生支持，不需要额外配置。

### Attach-first 策略——避免重复启动

App 先尝试 attach 到已运行的 Gateway（检查配置的端口），如果没有就启用 launchd service。这避免了**重复启动**——如果 Gateway 已经在跑（比如手动启动或 launchd 已启动），app 不会再启动一个。

这跟 Kubernetes 的 leader election 是一个思路。多个 controller 启动时，只有一个成为 leader，其他的 attach 到 leader 而不是各自独立运行。OpenClaw 也是这样：app 发现 Gateway 已运行就 attach，不重复启动。

### Disable-launchagent 标记——dev 模式的逃生口

Unsigned dev builds 写 `~/.openclaw/disable-launchagent` 标记，防止 launchd 指向未签名的 relay binary。Signed builds 自动清除这个标记。

这跟 feature flag 是一个思路——用一个文件作为开关，控制是否启用 launchd 管理。Dev 模式下禁用 launchd（避免签名问题），production 模式下启用（获得 auto-start 和 KeepAlive）。

### Remote mode——从不启动本地 Gateway

Remote mode 从不启动本地 Gateway，app 通过 SSH tunnel 连接远程 Gateway。这跟 VS Code Remote 是一个思路——本地 VS Code 只是 UI，代码执行在远程机器上。OpenClaw 的 remote mode 也是这样：本地 app 只是控制面板，Gateway 在远程运行。
