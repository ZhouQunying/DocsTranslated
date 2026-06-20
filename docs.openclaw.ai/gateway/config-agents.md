# Configuration — agents

## 架构精读

> 跳过不影响阅读翻译正文。

### agents.defaults.workspace——每个 agent 独立的工作目录

每个 agent 有自己的 **workspace**(工作目录),存放 agent 的项目文件、临时数据、生成的内容:

```json
{
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace"
    }
  }
}
```

**为什么需要独立 workspace?** 因为不同 agent 处理不同项目,文件不应该混在一起:
- Coding agent 的 workspace 是项目代码目录
- Customer support agent 的 workspace 是知识库和 FAQ 文件
- 如果两个 agent 共享 workspace,可能互相覆盖文件

**默认值是 `~/.openclaw/workspace`**,但可以通过环境变量 `OPENCLAW_WORKSPACE_DIR` 或配置文件覆盖。多 agent 场景下,每个 agent 可以配不同的 workspace 路径。

**这跟 Docker 的 WORKDIR 是一个思路**——每个 container 有自己的工作目录,container 之间不共享。OpenClaw 的 agent workspace 也是同样: 每个 agent 有自己的目录,互不干扰。

### agents.defaults.skills——skill 目录和加载

Skills 是 agent 可以使用的预定义能力(如"搜索 web"、"执行 shell 命令"、"操作文件")。每个 agent 可以配置自己的 skill 目录:

```json
{
  agents: {
    defaults: {
      skills: ["~/.openclaw/skills", "~/my-custom-skills"]
    }
  }
}
```

**为什么 skill 目录是可配置的?** 因为用户可能需要自定义 skill(如公司内部的 API 调用、特定工作流的自动化)。把 skill 目录配置化,用户可以:
- 使用 OpenClaw 内置的 skill(默认目录)
- 添加自己的 skill(自定义目录)
- 多个目录叠加(内置 + 自定义,自定义覆盖内置同名 skill)

**这跟 PATH 环境变量是一个思路**——shell 按 PATH 里的目录顺序查找可执行文件,先找到的优先。OpenClaw 的 skill 目录也是同样: 按配置顺序查找 skill,后加载的覆盖先加载的同名 skill。

### 多 agent 路由——不同消息发给不同 agent

OpenClaw 支持配置多个 agent,每个 agent 处理不同类型的消息:

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

**为什么需要多 agent?** 因为不同场景需要不同的 agent 配置:
- Coding agent: 用 GPT-4,允许执行 shell 命令,workspace 是代码目录
- Support agent: 用 GPT-3.5,只允许搜索知识库,workspace 是 FAQ 文件

如果只有一个 agent,要么配置得太宽松(安全风险),要么太严格(功能受限)。多 agent 让每个场景用最合适的配置。

**路由规则怎么工作?** 消息到达时,Gateway 按路由规则匹配:
1. 检查消息来源(channel 是 slack 还是 whatsapp)
2. 检查消息内容(是否包含特定关键词)
3. 匹配到第一个符合条件的 agent,就转发给它

**这跟 nginx 的 location 匹配是一个思路**——nginx 按 URL 路径匹配不同的 upstream,OpenClaw 按消息属性匹配不同的 agent。都是"根据请求特征,路由到不同的后端"。

### Session 管理——对话的隔离和持久化

每个 agent 的每个对话都有一个独立的 **session**(会话),存储:
- 对话历史(用户说了什么,agent 回了什么)
- 当前选择的模型和 auth profile
- Tool 调用结果(如 agent 执行了什么命令,读取了什么文件)

**为什么需要 session?** 因为 agent 需要"记忆"——用户说"继续刚才的话题",agent 需要知道"刚才的话题"是什么。Session 持久化对话历史,agent 可以读取之前的消息。

**Session 隔离**: 不同 agent 的 session 互不干扰。Coding agent 的 session 不会出现在 support agent 里。这跟浏览器的 tab 隔离是一个思路——每个 tab 有自己的 session,不共享 cookie、history。

### agents.defaults.skipBootstrap——跳过初始上下文加载

Bootstrap 是 agent 启动时加载的初始上下文(如系统 prompt、skill 列表、工具说明)。`skipBootstrap: true` 跳过这些加载:

**什么时候用?** 几个场景:
- **测试**: 想测试 agent 的纯能力,不想被 bootstrap 上下文影响
- **快速启动**: bootstrap 加载慢(如 skill 很多),想快速启动 agent
- **自定义上下文**: 用户想完全自己控制 agent 的初始上下文,不用 OpenClaw 默认的

**这跟 Docker 的 `--entrypoint` 是一个思路**——默认 entrypoint 是启动时执行的命令,`--entrypoint` 可以覆盖。OpenClaw 的 `skipBootstrap` 也是同样: 默认加载 bootstrap,`skipBootstrap` 可以跳过。
