# Configuration — Agents

## 架构精读

> 跳过不影响阅读翻译正文。

### agents.defaults 的继承模型——为什么不是简单覆盖？

Agent 配置用 defaults + list 两层结构：

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

这跟 K8s Deployment template + pod override 是一个思路——template 定义基线，pod 可以覆盖任意字段。defaults 是基线，list 里的每个 agent 可以覆盖 defaults 的任意字段。

关键设计是**DRY 原则**。10 个 agent 共享 9 个字段时，改一次 defaults 全部生效，不需要改 10 次。

### Context budget 的分治——为什么不是一个总量？

系统有多个高容量 prompt budget，按子系统分治而非流过一个通用控制：

- `initializationMaxChars`：单个 workspace 初始化文件的截断阈值（默认 20000）
- `initializationTotalMaxChars`：所有初始化文件的总量上限（默认 60000）
- `compaction`：上下文压缩的 token budget
- `contextPruning`：旧 tool result 的缓存 TTL

这跟 Linux cgroup 的分治是一个思路——CPU/memory/IO 各自限制，防止一个子系统吃光所有资源。

### Multi-agent routing——为什么需要确定性匹配顺序？

多 agent 路由用绑定匹配字段（peer/guild/account/channel），匹配顺序是确定性的：

1. peer（精确匹配对话对端）
2. guild/team（匹配 server/group）
3. accountId（匹配 channel account）
4. default agent（兜底）

这跟 nginx location 匹配是一个思路——精确匹配优先于通配符，通配符优先于默认。确定性顺序防止"消息不知道该路由到哪个 agent"的歧义。

### Session 作用域——per-sender vs global？

Session 配置的核心决策是作用域：

- **per-sender**（默认）：每个用户独立 session，对话历史隔离
- **global**：所有用户共享 session（适合公告频道）

这跟 Redis session store 的作用域是一个思路——per-user session 隔离状态，global session 共享状态。

代价是 per-sender 消耗更多存储（每个用户一份历史），global 有隐私风险（用户 A 看到用户 B 的对话）。

---

Agent-scoped configuration keys under `agents.*`, `multiAgent.*`, `session.*`, `messages.*`, and `talk.*`. For channels, tools, gateway runtime, and other top-level keys, see the configuration reference.

`agents.*`、`multiAgent.*`、`session.*`、`messages.*`、`talk.*` 下的 agent 作用域配置键。channels、tools、gateway 运行时和其他顶层键见 configuration reference。