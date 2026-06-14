# Hooks

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 OpenClaw 有两种钩子而不是一种？

OpenClaw 有两种钩子：**内部钩子**（Gateway 内部事件触发的小脚本）和**类型化插件钩子**（通过 `api.on(...)` 注册的运行时中间件）。区别在于控制粒度。内部钩子像 systemd 的 unit 文件——`/new` 命令触发时运行脚本，适合操作者管理的副作用和命令自动化。类型化钩子像 Kubernetes 的 Admission Webhook——有显式契约、优先级、合并规则和阻止/取消语义，适合运行时生命周期控制。好处是操作者可以用文件脚本做快速自动化，插件作者可以用类型化接口做精细控制，两者不互相干扰。

第二个设计：事件总线模式。Gateway 定义了一组标准事件：`command:new`、`command:reset`、`session:compact:before/after`、`agent:bootstrap`、`gateway:startup`、`message:received`、`message:sent` 等。钩子订阅感兴趣的事件，Gateway 按注册顺序触发。这就像浏览器的 DOM 事件系统——元素触发 `click`、`submit`、`load` 事件，监听器按注册顺序执行。好处是松耦合：事件生产者不知道谁在监听，监听者不知道谁生产事件，通过事件类型解耦。

第三个边界：遥测与策略分离。诊断事件是独立的事件总线，不是策略钩子表面。遥测导出（如 OpenTelemetry）走诊断事件，不通过钩子中间件。这就像微服务的 observability 与控制流分离——日志、指标、追踪是横切关注点，不应影响请求路径的策略决策。好处是遥测可以独立扩展和部署，不会因为遥测失败导致请求被阻断。

---

钩子是在 Gateway 内部发生事件时运行的小脚本。它们可从目录发现并用 `openclaw hooks` 检查。Gateway 仅在启用钩子或配置至少一个钩子条目、钩子包、旧版处理器或额外钩子目录后加载内部钩子。

OpenClaw 有两种钩子：

- **内部钩子**（本页）：agent 事件触发时在 Gateway 内部运行，如 `/new`、`/reset`、`/stop` 或生命周期事件
- **Webhooks**：外部 HTTP 端点，让其他系统触发 OpenClaw 中的工作。参见 [Webhooks](/automation/cron-jobs#webhooks)

钩子也可捆绑在插件中。`openclaw hooks list` 显示独立钩子和插件管理的钩子。

## 选择正确的表面

OpenClaw 有几个看起来相似但解决不同问题的扩展表面：

| 如果你想... | 使用... | 为什么 |
| --- | --- | --- |
| 在 `/new` 时保存快照、记录 `/reset`、`message:sent` 后调用外部 API、或添加粗粒度操作者自动化 | 内部钩子（`HOOK.md`，本页） | 基于文件的钩子面向操作者管理的副作用和命令/生命周期自动化 |
| 重写提示、阻止工具、取消出站消息、或添加有序中间件/策略 | 类型化插件钩子（通过 `api.on(...)`） | 类型化钩子有显式契约、优先级、合并规则和阻止/取消语义 |
| 添加纯遥测导出或可观测性 | 诊断事件 | 可观测性是独立的事件总线，不是策略钩子表面 |

当需要行为类似小型已安装集成的自动化时使用内部钩子。当需要运行时生命周期控制时使用类型化插件钩子。

## 快速开始

```bash
# 列出可用钩子
openclaw hooks list

# 启用钩子
openclaw hooks enable session-memory

# 检查钩子状态
openclaw hooks check

# 获取详细信息
openclaw hooks info session-memory
```

## 事件类型

| 事件 | 触发时机 |
| --- | --- |
| `command:new` | `/new` 命令发出 |
| `command:reset` | `/reset` 命令发出 |
| `command:stop` | `/stop` 命令发出 |
| `command` | 任何命令事件（通用监听器） |
| `session:compact:before` | 压缩总结历史前 |
| `session:compact:after` | 压缩完成后 |
| `session:patch` | 会话属性被修改时 |
| `agent:bootstrap` | 工作区引导文件注入前 |
| `gateway:startup` | channel 启动和钩子加载后 |
| `gateway:shutdown` | Gateway 关闭开始时 |
| `gateway:pre-restart` | 预期的 Gateway 重启前 |
| `message:received` | 来自任何 channel 的入站消息 |
| `message:transcribed` | 音频转录完成后 |
| `message:preprocessed` | 媒体和链接预处理完成或跳过后 |
| `message:sent` | 出站消息已交付 |

## 编写钩子

### 钩子结构

每个钩子是一个包含两个文件的目录：

```
my-hook/
├── HOOK.md          # 元数据 + 文档
└── handler.ts       # 处理器实现
```

### `HOOK.md` 格式

```markdown
---
name: my-hook
description: "此钩子做什么的简短描述"
metadata:
  { "openclaw": { "emoji": "🔗", "events": ["command:new"], "requires": { "bins": ["node"] } } }
---

# My Hook

详细文档放在这里。
```

**元数据字段**（`metadata.openclaw`）：

| 字段 | 描述 |
| --- | --- |
| `emoji` | CLI 显示表情 |
| `events` | 要监听的事件数组 |
| `export` | 要使用的命名导出（默认 `"default"`） |
| `os` | 需要的平台（如 `["darwin", "linux"]`） |
| `requires` | 需要的 `bins`、`anyBins`、`env` 或 `config` 路径 |
| `always` | 绕过资格检查（布尔值） |
| `install` | 安装方法 |

### 处理器实现

```typescript
const handler = async (event) => {
  if (event.type !== "command" || event.action !== "new") {
    return;
  }

  console.log(`[my-hook] New command triggered`);
  // 你的逻辑在这里

  // 可选地在可回复表面发送回复
  event.messages.push("Hook executed!");
};

export default handler;
```

每个事件包括：`type`、`action`、`sessionKey`、`timestamp`、`messages`（仅在可回复表面推送回复）和 `context`（事件特定数据）。Agent 和工具插件钩子上下文还可包括 `trace`，只读的 W3C 兼容诊断追踪上下文，插件可将其传入结构化日志用于 OTEL 关联。

## 相关

- [Automation](/automation)：所有自动化机制概览
- [Standing orders](/automation/standing-orders)：常驻命令
- [Cron jobs](/automation/cron-jobs)：日程执行
- [Webhooks](/automation/cron-jobs#webhooks)：入站 HTTP 事件触发器
