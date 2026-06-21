# Configuration — Agents

## 架构精读

> 跳过不影响阅读翻译正文。

### agents.defaults 的继承模型——为什么不是简单覆盖？

代理配置用 `defaults` + `list` 两层结构：

```json5
{
  agents: {
    defaults: { model: "gpt-4", workspace: "~/.openclaw/workspace" },
    list: [
      { id: "coding", model: "claude-opus-4-20250514" },  // 覆盖 defaults.model
      { id: "support" }  // 全部继承 defaults
    ]
  }
}
```

这跟 K8s Deployment 模板 + Pod 覆盖是一个思路——`template` 定义基线，`pod` 可以覆盖任意字段。`defaults` 是基线，`list` 里的每个代理可以覆盖 `defaults` 的任意字段。

关键设计是**DRY 原则**。10 个代理共享 9 个字段时，改一次 `defaults` 全部生效，不需要改 10 次。

### 上下文预算的分治——为什么不是一个总量？

系统有多个高容量提示预算，按子系统分治而非流过一个通用控制：

- `initializationMaxChars`：单个工作区初始化文件的截断阈值（默认 20000）
- `initializationTotalMaxChars`：所有初始化文件的总量上限（默认 60000）
- `compaction`：上下文压缩的令牌预算
- `contextPruning`：旧工具结果的缓存 TTL

这跟 Linux cgroup 的分治是一个思路——CPU/内存/IO 各自限制，防止一个子系统吃光所有资源。

### 多代理路由——为什么需要确定性匹配顺序？

多代理路由用绑定匹配字段（对端/服务器/账户/频道），匹配顺序是确定性的：

1. 对端（精确匹配对话另一方）
2. 服务器/团队（匹配服务器/群组）
3. 账户 ID（匹配频道账户）
4. 默认代理（兜底）

这跟 nginx location 匹配是一个思路——精确匹配优先于通配符，通配符优先于默认。确定性顺序防止“消息不知道该路由到哪个代理”的歧义。

### 会话作用域——按发送者还是全局？

会话配置的核心决策是作用域：

- **按发送者**（默认）：每个用户独立会话，对话历史隔离
- **全局**：所有用户共享会话（适合公告频道）

这跟 Redis 会话存储的作用域是一个思路——按用户会话隔离状态，全局会话共享状态。

代价是按发送者模式消耗更多存储（每个用户一份历史），全局模式有隐私风险（用户 A 看到用户 B 的对话）。

---

Agent-scoped configuration keys under `agents.*`, `multiAgent.*`, `session.*`, `messages.*`, and `talk.*`. For channels, tools, gateway runtime, and other top-level keys, see the configuration reference.

`agents.*`、`multiAgent.*`、`session.*`、`messages.*`、`talk.*` 下的 agent 作用域配置键。channels、tools、gateway 运行时和其他顶层键见 configuration reference。