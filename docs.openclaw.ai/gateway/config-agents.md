# Configuration — agents

## 架构精读

> 跳过不影响阅读翻译正文。

### agents.defaults.workspace

**问题**: 多个 agent 处理不同项目,文件混在一起?

**方案**: 每个 agent 独立 workspace (工作目录):
```json
{
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace"
    }
  }
}
```

**洞察**: 不同 agent 用不同 workspace,互不干扰。

**权衡**:
- ✓ 隔离: 文件不混
- ✓ 灵活: 每个 agent 配不同路径

**模式**: Docker WORKDIR——每个 container 有自己的工作目录。

**默认值**: `~/.openclaw/workspace`,可通过 `OPENCLAW_WORKSPACE_DIR` 或配置文件覆盖。

### agents.defaults.skills

**问题**: 用户需要自定义 skill (如公司内部 API)?

**方案**: Skill 目录可配置:
```json
{
  agents: {
    defaults: {
      skills: ["~/.openclaw/skills", "~/my-custom-skills"]
    }
  }
}
```

**洞察**: 多目录叠加,后加载覆盖先加载的同名 skill。

**权衡**:
- ✓ 灵活: 内置 + 自定义
- ✓ 可扩展: 用户可添加自己的 skill

**模式**: PATH 环境变量——按顺序查找,先找到优先。

### 多 agent 路由

**问题**: 不同场景需要不同 agent 配置?

**方案**: 多 agent + 路由规则:
```json
{
  multiAgent: {
    routing: [
      { agent: "coding", match: { channels: ["slack"] } },
      { agent: "support", match: { channels: ["whatsapp"] } }
    ]
  }
}
```

**洞察**: 按消息属性 (来源、内容) 路由到不同 agent。

**权衡**:
- ✓ 灵活: 每个场景用最合适的 agent
- ✓ 安全: 不同 agent 有不同权限

**模式**: nginx location 匹配——按 URL 路径匹配不同 upstream。

**路由规则**:
1. 检查消息来源 (channel)
2. 检查消息内容 (关键词)
3. 匹配第一个符合条件的 agent

### Session 管理

**问题**: Agent 需要"记忆"对话历史?

**方案**: 每个 agent 的每个对话有独立 session:
- 对话历史
- 当前模型和 auth profile
- Tool 调用结果

**洞察**: Session 持久化对话历史,agent 可以读取之前的消息。

**权衡**:
- ✓ 记忆: agent 知道"刚才的话题"
- ✓ 隔离: 不同 agent 的 session 互不干扰

**模式**: 浏览器 tab 隔离——每个 tab 有自己的 session、cookie、history。

### agents.defaults.skipBootstrap

**问题**: 想跳过 agent 启动时的初始上下文加载?

**方案**: `skipBootstrap: true` 跳过 bootstrap (系统 prompt、skill 列表、工具说明)。

**洞察**: 测试、快速启动、自定义上下文时使用。

**权衡**:
- ✓ 快: 跳过加载
- ✗ 无默认: 需要自己提供初始上下文

**模式**: Docker `--entrypoint`——覆盖默认 entrypoint。
