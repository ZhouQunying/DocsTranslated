# Skills (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### App 通过 Gateway 获取 skills——瘦客户端模式

macOS app **不解析** skills 配置,而是通过 Gateway 获取 skills 列表。这是 **thin client**(瘦客户端)模式——app 只做 UI 展示,skill 的定义解析、权限检查、执行调度全在 Gateway。

**为什么这样设计?** 因为 skill 的逻辑复杂(需要解析 YAML/JSON 定义、检查权限、调度执行),如果每个客户端(macOS app、WebChat、CLI)都自己实现,就是三套代码,bug fix 要改三次。把逻辑集中在 Gateway,所有客户端只调 Gateway 的统一 API,bug fix 一次生效。

**好处是逻辑集中**: Gateway 更新 skill 格式(如从 YAML 改成 JSON,或添加新字段),所有客户端自动生效,不需要各自适配。

这跟 API gateway 后面的 microservices 是一个思路——client 不关心后端有多少 service、数据怎么存,只调 gateway 的统一 API。OpenClaw 的 app 也是同样: 不关心 skill 怎么定义、怎么执行,只调 Gateway 的 skill API 获取列表和触发执行。

### Gateway 管理 skill catalog——控制平面 vs 数据平面

Gateway 是 skill catalog 的**控制平面**(control plane,负责管理和决策),负责:
- 解析 skill 定义(YAML/JSON 文件,描述 skill 能做什么、需要什么权限)
- 检查 skill 权限(用户是否允许 agent 使用这个 skill)
- 调度 skill 执行(把用户的操作转发给对应的 skill handler)

App 是**数据平面**(data plane,负责执行和展示),负责:
- 展示 skill 列表(从 Gateway 获取,显示在 UI 上)
- 转发用户操作到 Gateway(用户点击"执行 skill X",app 调 Gateway API)

**为什么分离?** 因为控制逻辑(解析、权限、调度)应该集中管理,避免分散。如果每个 app 都自己做控制逻辑,就会出现"macOS app 允许 skill X,但 WebChat 不允许"的不一致。控制平面集中 = 策略一致。

这跟 Istio(服务网格,管理微服务之间的通信)的 control plane / data plane 是一个思路——Istio 的 Pilot 是 control plane(下发路由规则),Envoy 是 data plane(执行路由)。OpenClaw 也是同样: Gateway 下发 skill 定义和权限策略,app 执行 skill 操作。
