# Skills (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### App 通过 Gateway 获取 skills——thin client 模式

macOS app **不解析** skills 配置，而是通过 Gateway 获取 skills 列表。这是 thin client 模式——app 只做 UI 展示，skill 的定义解析、权限检查、执行调度全在 Gateway。好处是**逻辑集中**：Gateway 更新 skill 格式，所有客户端（macOS app、WebChat、CLI）自动生效，不需要各自适配。

这跟 API gateway 后面的 microservices 是一个思路。Client 不关心后端有多少 service、数据怎么存，只调 gateway 的统一 API。OpenClaw 的 app 也是这样：不关心 skill 怎么定义、怎么执行，只调 Gateway 的 skill API 获取列表和触发执行。

### Gateway 拥有 skill catalog——control plane vs data plane

Gateway 是 skill catalog 的 control plane，负责：
- 解析 skill 定义（YAML/JSON）
- 检查 skill 权限
- 调度 skill 执行

App 是 data plane，负责：
- 展示 skill 列表
- 转发用户操作到 Gateway

这跟 Istio 的 control plane / data plane 是一个思路。Istio 的 Pilot 是 control plane（下发路由规则），Envoy 是 data plane（执行路由）。OpenClaw 也是这样：Gateway 下发 skill 定义，app 执行 skill 操作。
