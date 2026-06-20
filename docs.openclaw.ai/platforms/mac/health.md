# Health

## 架构精读

> 跳过不影响阅读翻译正文。

### 三色状态——把复杂状态压缩成直觉信号

macOS app 的健康状态用三色表示:
- **绿色**: 一切正常(Gateway 运行中,所有 node 连接正常,所有 provider 可用)
- **橙色**: 有问题但还能用(Gateway 慢、某个 node 断连、某个 provider rate-limited)
- **红色**: 不可用(Gateway 挂了、认证失败、所有 provider 都不可用)

**为什么用三色而不是更详细的状态?** 因为内部状态太复杂——可能有几十种状态(Gateway 连接中、auth 过期、node 离线、provider rate-limited、canvas 渲染失败……),用户不需要知道细节。三色是 **UX 抽象层**: 绿色="正常工作,别管它",橙色="需要注意,可能有问题",红色="停止工作,需要干预"。

**没有三色状态会怎样?** 用户只能看到一个开关(Gateway 在/不在),不知道"Gateway 在但 provider rate-limited"或"Gateway 在但 node 断连"这种中间状态。三色让用户知道"系统有没有问题"和"问题严不严重"。

这跟 Kubernetes 的 Pod phase 是一个思路——Pod 有 Pending/Running/Succeeded/Failed/Unknown 五种状态,但 kubectl 用颜色简化显示(绿色 Running,红色 Failed,黄色 Pending)。OpenClaw 也是这样: 内部状态复杂,但用户只需看三色。

### 探针机制——被动监听 + 主动探测,双重保险

Health 状态通过两种方式获取:
1. **被动监听**: Gateway 主动推送事件(如"node 断连了"、"provider rate-limited"),app 收到事件就更新状态
2. **主动探测**: 每 60 秒调一次 `openclaw health --json`,主动问 Gateway "你现在状态怎么样"

**为什么需要两种方式?** 被动监听实时但**可能漏事件**——如果 app 和 Gateway 之间的连接断了,app 收不到事件,但不知道是"没事件"还是"连接断了"。主动探测延迟(每 60 秒一次)但**不会漏**——即使连接断了,探测也会失败,app 知道"Gateway 不可达"。

两种方式互补: 被动监听负责实时更新,主动探测负责兜底检测。

这跟 Prometheus 的 scrape + pushgateway 是一个思路——Prometheus 默认主动 scrape target(主动探测),但也支持 pushgateway 让 target 主动上报(被动监听)。OpenClaw 也是这样: 被动监听事件,主动探测兜底。

### Settings 健康卡片——给普通用户的诊断界面

Settings 里的健康卡片显示 Gateway 版本、连接状态、node 列表。

**为什么需要这个?** 因为 CLI 用户可以用 `openclaw health --json` 获取机器可读的诊断结果,但 GUI 用户需要可视化展示。健康卡片是**用户友好的诊断界面**——普通用户看到"Gateway: 运行中"、"Nodes: 2 个连接"就知道系统正常,不需要学命令行。

**卡片显示什么?**
- Gateway 版本和运行状态
- 连接的 node 列表(macOS、Windows、Android、iOS 各一个)
- 如果有问题,显示具体问题(如"Provider OpenAI rate-limited")

这跟 AWS Console 的 Health Dashboard 是一个思路——把系统状态以卡片形式展示,用户可以快速定位问题。OpenClaw 的健康卡片不是给开发者看的 debug 信息,而是给普通用户看的"系统是否正常"的判断依据。
