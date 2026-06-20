# Health

## 架构精读

> 跳过不影响阅读翻译正文。

### 三色状态——可观测性的极简抽象

macOS app 的健康状态用三色表示：
- **绿色**：一切正常
- **橙色**：有问题但可用（如 Gateway 慢或 node 断连）
- **红色**：不可用（Gateway 挂了或认证失败）

这跟 Kubernetes 的 Pod phase 是一个思路。Pod 有 Pending/Running/Succeeded/Failed/Unknown 五种状态，但 kubectl 用颜色简化显示（绿色 Running，红色 Failed，黄色 Pending）。OpenClaw 也是这样：内部状态复杂，但用户只需看三色。可观测性的关键是**状态压缩**——把复杂系统压缩成直觉可理解的信号。

### 探针机制——被动监听 vs 主动探测

Health 状态通过两种方式获取：
1. **被动监听**：Gateway 事件推送（WebSocket 连接状态）
2. **主动探测**：每 60 秒调一次 `openclaw health --json`

这跟 Prometheus 的 scrape + pushgateway 是一个思路。Prometheus 默认主动 scrape target，但也支持 pushgateway 让 target 主动上报。OpenClaw 也是这样：被动监听事件，主动探测兜底。两种机制互补——被动监听实时但可能漏事件，主动探测延迟但不会漏。

### Settings 健康卡片——把诊断结果暴露给用户

Settings 里的健康卡片显示 Gateway 版本、连接状态、node 列表。这跟 AWS Console 的 Health Dashboard 是一个思路——把系统状态以卡片形式展示，用户可以快速定位问题。OpenClaw 的健康卡片不是给开发者看的 debug 信息，而是给普通用户看的"系统是否正常"的判断依据。
