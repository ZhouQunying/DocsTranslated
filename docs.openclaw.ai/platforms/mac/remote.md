# Remote control

## 架构精读

> 跳过不影响阅读翻译正文。

### SSH tunnel vs WebSocket——两种传输的选择

Remote mode 支持两种传输：
1. **SSH tunnel**：通过 SSH 端口转发连接远程 Gateway
2. **WebSocket**：直接 WebSocket 连接（需要 wss://）

这跟 SOCKS proxy vs HTTPS 直连是一个思路。SSH tunnel 像 SOCKS proxy——复用已有通道、加密、但多一层跳转。WebSocket 直连更直接，但需要 Gateway 暴露 wss:// 端口。OpenClaw 让用户选择：已有 SSH 基础设施（如跳板机）就用 tunnel，现代云部署（Gateway 有公网域名）就用 WebSocket。

### Browser automation 归 CLI node host——关注点分离

Remote mode 下，browser automation 由 **CLI node host** 负责，不是 macOS app 原生能力。这跟 Kubernetes 的 control plane / data plane 分离是一个思路。Control plane 做决策，data plane 执行。OpenClaw 也是这样：macOS app 是 control plane（UI 和控制），CLI node host 是 data plane（执行 browser automation）。

分离的好处是**职责清晰**。macOS app 不需要实现 Chromium 控制逻辑，CLI node host 不需要实现 macOS UI。各自独立演进，通过 node 协议通信。

### Preconfiguration 跳过 welcome flow——声明式配置

文档支持 preconfigure app 跳过 welcome flow，直接连接指定 Gateway。这跟 Infrastructure as Code 是一个思路——Terraform 不交互式配置，而是声明式配置。OpenClaw 的 preconfiguration 也是这样：CI/CD 或批量部署时，不需要用户点 welcome flow，配置文件直接指定 Gateway 地址。
