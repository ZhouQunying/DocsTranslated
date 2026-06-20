# Remote control

## 架构精读

> 跳过不影响阅读翻译正文。

### SSH tunnel vs WebSocket——两种传输方式的选择

Remote mode 支持两种传输方式:
1. **SSH tunnel**: 通过 SSH 端口转发连接远程 Gateway(SSH 是加密的远程登录协议,端口转发是它的一个功能)
2. **WebSocket**: 直接 WebSocket 连接(需要 wss://,加密的 WebSocket)

**SSH tunnel 适合什么场景?** 已经有 SSH 基础设施的环境(如公司有跳板机、服务器只能通过 SSH 访问)。SSH tunnel 复用已有的 SSH 通道,不需要额外开端口,加密和认证由 SSH 处理。缺点是**多一层跳转**——数据从 app → SSH → Gateway,延迟略高。

**WebSocket 适合什么场景?** 现代云部署(Gateway 有公网域名和 TLS 证书)。WebSocket 直连更快(没有 SSH 跳转),但需要 Gateway 暴露 wss:// 端口(通常是 1455)。

**为什么提供两种?** 因为不同环境的基础设施不同。强制用户用 SSH tunnel,但用户没有 SSH 服务器;强制用 WebSocket,但用户没有公网域名。提供选择 = 适配不同环境。

### Browser automation 归 CLI node host——执行在目标机器

Remote mode 下,browser automation(控制浏览器执行操作,如点击、填表单)由 **CLI node host**(Gateway 所在机器上运行的 CLI 进程)负责,不是本地 macOS app 的能力。

**为什么这样设计?** 因为 browser automation 需要在**目标机器**上执行。Remote mode 的场景是: Gateway 在远程服务器,app 在本地。如果 browser automation 在本地 app 执行,浏览器就在本地打开,但 Gateway 在远程——网络不通、权限不对、文件路径不一致。把 browser automation 放在 Gateway 所在的机器(CLI node host),浏览器就在那台机器打开,跟 Gateway 同网络、同用户、同文件系统。

**职责分离**: macOS app 负责 UI 和控制(用户点击"打开浏览器"),CLI node host 负责执行(实际打开浏览器并操作)。两者通过 node 协议通信。

这跟 Terraform 的 remote execution 是一个思路——Terraform 不在本地执行 cloud API 调用,而是在目标 cloud 环境执行(用 provider)。OpenClaw 的 remote browser automation 也是这样: 在 Gateway 所在机器执行,不在本地执行。

### Preconfiguration 跳过引导流程——批量部署的声明式配置

App 支持 **preconfigure**(预配置): 通过配置文件直接指定 Gateway 地址,跳过交互式引导流程(welcome flow,就是用户第一次打开 app 时的"欢迎+配置"向导)。

**适合什么场景?** CI/CD 或批量部署。想象你要在 100 台机器上部署 OpenClaw app,每台都要手动点引导流程——不现实。Preconfiguration 让你写一个配置文件,指定 Gateway 地址,部署时 app 读配置直接连接,不需要用户交互。

这跟 Terraform 的声明式配置是一个思路——Terraform 不问"你想创建什么资源?",而是读配置文件直接创建。OpenClaw 的 preconfiguration 也是这样: 不问"你想连哪个 Gateway?",配置文件里已经写了。
