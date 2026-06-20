# Skills (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### App 通过 Gateway 获取 skills——thin client 模式

macOS app **不解析** skills 配置，而是通过 Gateway 获取 skills 列表。这跟 SPA 的 API client 是一个思路——前端不解析业务逻辑，调后端 API 获取数据。OpenClaw 的 macOS app 是 thin client：UI 展示 skills，但 skill 定义、权限检查、执行调度都在 Gateway。

Thin client 的好处是**逻辑集中**。Skill 的解析和执行在 Gateway，app 只是展示层。Gateway 更新了 skill 格式，app 不需要改。这跟 Kubernetes 的 client-go 库是一个思路：client 不解析 API schema，只序列化/反序列化，schema 演进由 server 控制。

### Gateway 拥有 skill catalog——control plane vs data plane

Gateway 是 skill catalog 的 control plane，负责：
- 解析 skill 定义（YAML/JSON）
- 检查 skill 权限
- 调度 skill 执行

App 是 data plane，负责：
- 展示 skill 列表
- 转发用户操作到 Gateway

这跟 Istio 的 control plane / data plane 是一个思路。Istio 的 Pilot 是 control plane（下发路由规则），Envoy 是 data plane（执行路由）。OpenClaw 也是这样：Gateway 下发 skill 定义，app 执行 skill 操作。
