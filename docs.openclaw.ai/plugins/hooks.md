# 插件钩子

## 架构精读

> 跳过不影响阅读翻译正文。

### 插件钩子和 operator 运维脚本有什么区别？

这是两套完全不同的扩展机制。插件钩子运行在 Gateway 进程内，是插件 SDK 的一部分，用 TypeScript 编写，能访问完整的运行时上下文。Operator `HOOK.md` 脚本是运维侧的小脚本，响应 `/new`、`/reset`、`gateway:startup` 等命令事件。前者面向插件开发者，后者面向运维人员。就像 Servlet Filter 和 crontab 脚本的区别——都在服务端执行，但抽象层级和受众完全不同。

第二个关键设计：顺序执行、优先级排序。钩子按 `priority` 降序运行，同优先级保持注册顺序。高优先级可终止链（`block: true` 是终结的），就像 Express.js 中间件——顺序决定行为，一个中间件可以短路整条链。好处是行为可预测，坏处是注册顺序变成了隐性依赖。

第三个边界：决策钩子和观察钩子严格分离。**粗体**钩子（`before_tool_call`、`before_agent_run` 等）可阻断、覆盖或请求审批；其余钩子只读。这就像 web 中间件的两种角色：修改请求的中间件和只记录日志的中间件。好处是观察钩子永远不能意外改变系统行为。

---

插件钩子是 OpenClaw 插件的进程内扩展点。当插件需要检查或修改 agent 运行、工具调用、消息流、会话生命周期、子 agent 路由、安装或 Gateway 启动时使用。

想要一个小型 operator 安装的 `HOOK.md` 脚本处理命令和 Gateway 事件（如 `/new`、`/reset`、`/stop`、`agent:bootstrap` 或 `gateway:startup`）时，改用 [internal hooks](/automation/hooks)。

## 快速开始

从插件入口用 `api.on(...)` 注册类型化插件钩子：

```typescript

export default definePluginEntry({
  id: "tool-preflight",
  name: "Tool Preflight",
  register(api) {
    api.on(
      "before_tool_call",
      async (event) => {
        if (event.toolName !== "web_search") {
          return;
        }

        return {
          requireApproval: {
            title: "运行网页搜索",
            description: `允许搜索查询：${String(event.params.query ?? "")}`,
            severity: "info",
            timeoutMs: 60_000,
            timeoutBehavior: "deny",
          },
        };
      },
      { priority: 50 },
    );
  },
});
```

钩子处理器按 `priority` 降序顺序运行。同优先级钩子保持注册顺序。

`api.on(name, handler, opts?)` 接受：

- `priority` - 处理器排序（高的先运行）。
- `timeoutMs` - 可选的每钩子预算。设置后，钩子运行器在该预算用完后中止该处理器并继续下一个，而不是让缓慢的设置或召回工作消耗调用者配置的模型超时。省略则使用钩子运行器通用应用的默认观察/决策超时。

Operator 也可不修改插件代码设置钩子预算：

```json
{
  "plugins": {
    "entries": {
      "my-plugin": {
        "hooks": {
          "timeoutMs": 30000,
          "timeouts": {
            "before_prompt_build": 90000,
            "agent_end": 60000
          }
        }
      }
    }
  }
}
```

`hooks.timeouts.<hookName>` 覆盖 `hooks.timeoutMs`，后者覆盖插件编写的 `api.on(..., { timeoutMs })` 值。每个配置值必须是正整数且不大于 600000 毫秒。已知慢钩子优先用每钩子覆盖，这样一个插件不会在所有地方获得更长预算。

每个钩子接收 `event.context.pluginConfig`，即注册该处理器的插件的已解析配置。用于需要当前插件选项的钩子决策；OpenClaw 按处理器注入而不修改其他插件看到的共享事件对象。

## 钩子目录

钩子按扩展的表面分组。**粗体**名称接受决策结果（阻断、取消、覆盖或请求审批）；其余仅观察。

**Agent turn**

- `before_model_resolve` - 会话消息加载前覆盖 provider 或模型
- `agent_turn_prepare` - 消费排队的插件 turn 注入并在 prompt 钩子前添加同 turn 上下文
- `before_prompt_build` - 模型调用前添加动态上下文或系统 prompt 文本
- `before_agent_start` - 仅兼容的组合阶段；优先用上面两个钩子
- **`before_agent_run`** - 模型提交前检查最终 prompt 和会话消息，可选阻断运行
- **`before_agent_reply`** - 用合成回复或沉默短路模型 turn
- **`before_agent_finalize`** - 检查自然最终答案并请求再一次模型通行
- `agent_end` - 观察最终消息、成功状态和运行时长
- `heartbeat_prompt_contribution` - 为后台监控和生命周期插件添加仅心跳上下文

**对话观察**

- `model_call_started` / `model_call_ended` - 观察已清理的 provider/模型调用元数据、计时、结果和有界请求 id 哈希，不含 prompt 或响应内容
- `llm_input` - 观察 provider 输入（系统 prompt、prompt、历史）
- `llm_output` - 观察 provider 输出、用量和可用时的已解析 `contextTokenBudget`

**工具**

- **`before_tool_call`** - 重写工具参数、阻断执行或请求审批
- `after_tool_call` - 观察工具结果、错误和时长
- `resolve_exec_env` - 向 `exec` 贡献插件持有的环境变量
- **`tool_result_persist`** - 重写从工具结果产生的 assistant 消息
- **`before_message_write`** - 检查或阻断进行中的消息写入（罕见）

**消息和投递**

- **`inbound_claim`** - agent 路由前认领入站消息（合成回复）
- `message_received` - 观察入站内容、发送者、线程和元数据
- **`message_sending`** - 重写出站内容或取消投递
- **`reply_payload_sending`** - 投递前变更或取消规范化回复负载
- `message_sent` - 观察出站投递成功或失败
- **`before_dispatch`** - channel 交接前检查或重写出站调度
- **`reply_dispatch`** - 参与最终回复调度管道

**会话和压缩**

- `session_start` / `session_end` - 追踪会话生命周期边界。事件的 `reason` 是 `new`、`reset`、`idle`、`daily`、`compaction`、`deleted`、`shutdown`、`restart` 或 `unknown` 之一。`shutdown` 和 `restart` 值在进程停止或重启时会话仍活跃时从 gateway 关闭终结器触发，让下游插件（如记忆或转录存储）可以终结否则会在重启间留在开放状态的幽灵行。终结器有界，慢插件不能阻塞 SIGTERM/SIGINT。
- `before_compaction` / `after_compaction` - 观察或注释压缩周期
- `before_reset` - 观察会话重置事件（`/reset`、编程式重置）

**子 agent**

- `subagent_spawned` / `subagent_ended` - 观察子 agent 启动和完成。
- `subagent_delivery_target` - 无核心会话绑定可投影路由时的完成投递兼容钩子。
- `subagent_spawning` - 已弃用兼容钩子。核心现在在 `subagent_spawned` 触发前通过 channel 会话绑定适配器准备 `thread: true` 子 agent 绑定。
- `subagent_spawned` 在 OpenClaw 已在启动前解析子会话原生模型时包含 `resolvedModel` 和 `resolvedProvider`。

**生命周期**

- `gateway_start` / `gateway_stop` - 随 Gateway 启停插件持有的服务
- `deactivate` - `gateway_stop` 的已弃用兼容别名；新插件用 `gateway_stop`
- `cron_changed` - 观察 gateway 持有的 cron 生命周期变更（added、updated、removed、started、finished、scheduled）
- **`before_install`** - 检查技能或插件安装上下文并可选阻断

## 调试运行时钩子

当插件需要为 agent turn 切换 provider 或模型时用 `before_model_resolve`。它在模型解析前运行；`llm_output` 仅在模型尝试产生 assistant 输出后运行。

要验证有效会话模型，检查运行时注册，然后用 `openclaw sessions` 或 Gateway 会话/状态表面。调试 provider 负载时，用 `--raw-stream` 和 `--raw-stream-path <path>` 启动 Gateway；这些标志将原始模型流事件写入 jsonl 文件。

## 工具调用策略

`before_tool_call` 接收：

- `event.toolName`
- `event.params`
- 可选 `event.toolKind` 和 `event.toolInputKind`，host 权威判别器，用于有意共享名称的工具；例如外层 code-mode `exec` 调用使用 `toolKind: "code_mode_exec"` 并在输入语言已知时包含 `toolInputKind: "javascript" | "typescript"`
- 可选 `event.derivedPaths`，包含已知工具信封（如 `apply_patch`）的最佳 host 派生目标路径提示；存在时这些路径可能不完整或可能过度近似工具实际触及的内容（例如格式错误或部分输入）
- 可选 `event.runId`
- 可选 `event.toolCallId`
- 上下文字段如 `ctx.agentId`、`ctx.sessionKey`、`ctx.sessionId`、`ctx.runId`、`ctx.jobId`（cron 驱动运行设置）、`ctx.toolKind`、`ctx.toolInputKind` 和诊断 `ctx.trace`

可返回：

```typescript
type BeforeToolCallResult = {
  params?: Record<string, unknown>;
  block?: boolean;
  blockReason?: string;
  requireApproval?: {
    title: string;
    description: string;
    severity?: "info" | "warning" | "critical";
    timeoutMs?: number;
    timeoutBehavior?: "allow" | "deny";
    allowedDecisions?: Array<"allow-once" | "allow-always" | "deny">;
    pluginId?: string;
    onResolution?: (
      decision: "allow-once" | "allow-always" | "deny" | "timeout" | "cancelled",
    ) => Promise<void> | void;
  };
};
```

类型化生命周期钩子的守卫行为：

- `block: true` 是终结的，跳过更低优先级处理器。
- `block: false` 被视为无决策。
- `params` 重写执行的工具参数。
- `requireApproval` 暂停 agent 运行并通过插件审批询问用户。`/approve` 命令可同时审批 exec 和插件审批。在 Codex app-server report-mode 原生 `PreToolUse` 中继中，这延迟到匹配的 app-server 审批请求；详见 [Codex harness runtime](/plugins/codex-harness-runtime#hook-boundaries)。
- 更低优先级的 `block: true` 仍可在更高优先级钩子请求审批后阻断。
- `onResolution` 接收已解析的审批决策 - `allow-once`、`allow-always`、`deny`、`timeout` 或 `cancelled`。

审批路由、决策行为和何时用 `requireApproval` 代替可选工具或 exec 审批见 [Plugin permission requests](/plugins/plugin-permission-requests)。

需要 host 级策略的捆绑插件可用 `api.registerTrustedToolPolicy(...)` 注册受信工具策略。这些在普通 `before_tool_call` 钩子和外部插件决策前运行。仅用于 host 受信门控，如工作区策略、预算执行或保留工作流安全。外部插件应用普通 `before_tool_call` 钩子。

### Exec 环境钩子

`resolve_exec_env` 让插件在基础 exec 环境构建后、命令运行前向 `exec` 工具调用贡献环境变量。它接收：

- `event.sessionKey`
- `event.toolName`，当前始终为 `"exec"`
- `event.host`，`"gateway"`、`"sandbox"` 或 `"node"` 之一
- 上下文字段如 `ctx.agentId`、`ctx.sessionKey`、`ctx.messageProvider` 和 `ctx.channelId`

返回 `Record<string, string>` 合并到 exec 环境。处理器按优先级顺序运行，后面的钩子结果覆盖前面钩子对同一键的结果。

钩子输出在合并前通过 host exec 环境键策略过滤。无效键、`PATH` 和危险 host 覆盖键如 `LD_*`、`DYLD_*`、`NODE_OPTIONS`、代理变量和 TLS 覆盖变量被丢弃。过滤后的插件 env 包含在 gateway 审批/审计元数据中并转发给 node-host 执行请求。

### 工具结果持久化

工具结果可包含结构化 `details` 用于 UI 渲染、诊断、媒体路由或插件持有的元数据。将 `details` 视为运行时元数据而非 prompt 内容：

- OpenClaw 在 provider 回放和压缩输入前剥离 `toolResult.details`，这样元数据不会成为模型上下文。
- 持久化会话条目仅保留有界 `details`。超大 details 被替换为紧凑摘要和 `persistedDetailsTruncated: true`。
- `tool_result_persist` 和 `before_message_write` 在最终持久化上限前运行。钩子仍应保持返回的 `details` 小，避免仅在 `details` 中放置 prompt 相关文本；将模型可见的工具输出放在 `content` 中。

## Prompt 和模型钩子

新插件使用阶段专用钩子：

- `before_model_resolve`：仅接收当前 prompt 和附件元数据。返回 `providerOverride` 或 `modelOverride`。
- `agent_turn_prepare`：接收当前 prompt、已准备会话消息和该会话排空的恰好一次排队注入。返回 `prependContext` 或 `appendContext`。
- `before_prompt_build`：接收当前 prompt 和会话消息。返回 `prependContext`、`appendContext`、`systemPrompt`、`prependSystemContext` 或 `appendSystemContext`。
- `heartbeat_prompt_contribution`：仅对心跳 turn 运行，返回 `prependContext` 或 `appendContext`。适用于需要总结当前状态而不改变用户发起 turn 的后台监控。

`before_agent_start` 保留用于兼容。优先使用上面的显式钩子，这样插件不依赖遗留组合阶段。

`before_agent_run` 在 prompt 构建后、任何模型输入前运行，包括 prompt 本地图片加载和 `llm_input` 观察。它接收当前用户输入为 `prompt`，加上 `messages` 中的已加载会话历史和活跃系统 prompt。返回 `{ outcome: "block", reason, message? }` 在模型读取 prompt 前停止运行。`reason` 是内部的；`message` 是用户面向的替换。唯一支持的 outcome 是 `pass` 和 `block`；不支持的决策形态失败关闭。

运行被阻断时，OpenClaw 仅存储 `message.content` 中的替换文本加上非敏感阻断元数据如阻断插件 id 和时间戳。原始用户文本不保留在转录或未来上下文中。内部阻断原因被视为敏感并从转录、历史、广播、日志和诊断负载中排除。可观测性应使用已清理字段如阻断者 id、outcome、时间戳或安全类别。

`before_agent_start` 和 `agent_end` 在 OpenClaw 可识别活跃运行时包含 `event.runId`。同一值也可在 `ctx.runId` 上获得。Cron 驱动运行还暴露 `ctx.jobId`（发起的 cron 作业 id），这样插件钩子可将指标、副作用或状态限定到特定调度作业。

Channel 发起的运行中，`ctx.messageProvider` 是 provider 表面如 `discord` 或 `telegram`，`ctx.channelId` 是 OpenClaw 可从会话键或投递元数据派生时的对话目标标识符。

`agent_end` 是观察钩子。Gateway 和持久化 harness 路径在 turn 后 fire-and-forget 运行它，而短生命周期一次性 CLI 路径在进程清理前等待钩子 promise，这样受信插件可刷新终端可观测性或捕获状态。钩子运行器应用 30 秒超时，卡住的插件或嵌入端点不能让钩子 promise 永远待处理。超时被记录，OpenClaw 继续；它不取消插件持有的网络工作，除非插件也使用自己的 abort 信号。

`model_call_started` 和 `model_call_ended` 用于不应接收原始 prompt、历史、响应、头、请求体或 provider 请求 ID 的 provider 调用遥测。这些钩子包含稳定元数据如 `runId`、`callId`、`provider`、`model`、可选 `api`/`transport`、终端 `durationMs`/`outcome` 和 OpenClaw 可派生有界 provider 请求 id 哈希时的 `upstreamRequestIdHash`。运行时已解析上下文窗口元数据时，钩子事件和上下文还包含 `contextTokenBudget`（模型/配置/agent 上限后的有效 token 预算），加上应用更低上限时的 `contextWindowSource` 和 `contextWindowReferenceTokens`。

`before_agent_finalize` 仅在 harness 即将接受自然最终 assistant 答案时运行。它不是 `/stop` 取消路径，用户中止 turn 时不运行。返回 `{ action: "revise", reason }` 请求 harness 在最终化前再一次模型通行，`{ action: "finalize", reason? }` 强制最终化，或省略结果继续。Codex 原生 `Stop` 钩子作为 OpenClaw `before_agent_finalize` 决策中继到此钩子。

返回 `action: "revise"` 时，插件可包含 `retry` 元数据让额外模型通行有界且重放安全：

```typescript
type BeforeAgentFinalizeRetry = {
  instruction: string;
  idempotencyKey?: string;
  maxAttempts?: number;
};
```

`instruction` 追加到发给 harness 的修订原因。`idempotencyKey` 让 host 跨等价最终化决策计数同一插件请求的重试，`maxAttempts` 限制 host 在继续自然最终答案前允许的额外通行数。

需要原始对话钩子（`before_model_resolve`、`before_agent_reply`、`llm_input`、`llm_output`、`before_agent_finalize`、`agent_end` 或 `before_agent_run`）的非捆绑插件必须设置：

```json
{
  "plugins": {
    "entries": {
      "my-plugin": {
        "hooks": {
          "allowConversationAccess": true
        }
      }
    }
  }
}
```

Prompt 变更钩子和持久下一 turn 注入可用 `plugins.entries.<id>.hooks.allowPromptInjection=false` 按插件禁用。

### 会话扩展和下一 turn 注入

工作流插件可用 `api.registerSessionExtension(...)` 持久化小 JSON 兼容会话状态，并通过 Gateway `sessions.pluginPatch` 方法更新。会话行通过 `pluginExtensions` 投影已注册的扩展状态，让 Control UI 和其他客户端无需了解插件内部即可渲染插件持有的状态。

当插件需要持久上下文恰好一次到达下一个模型 turn 时用 `api.enqueueNextTurnInjection(...)`。OpenClaw 在 prompt 钩子前排空排队注入，丢弃过期注入，并按 `idempotencyKey` 每插件去重。这是审批恢复、策略摘要、后台监控增量和命令延续的正确接缝——应在下一 turn 对模型可见但不应成为永久系统 prompt 文本。

清理语义是契约的一部分。会话扩展清理和运行时生命周期清理回调接收 `reset`、`delete`、`disable` 或 `restart`。Host 在 reset/delete/disable 时移除所属插件的持久会话扩展状态和待处理下一 turn 注入。restart 保留持久会话状态，同时清理回调让插件释放调度作业、运行上下文和旧运行时世代的其他带外资源。

## 消息钩子

消息钩子用于 channel 级路由和投递策略：

- `message_received`：观察入站内容、发送者、`threadId`、`messageId`、`senderId`、可选运行/会话关联和元数据。
- `message_sending`：重写 `content` 或返回 `{ cancel: true }`。
- `reply_payload_sending`：重写规范化 `ReplyPayload` 对象（包括 `presentation`、`delivery`、媒体引用和文本）或返回 `{ cancel: true }`。
- `message_sent`：观察最终成功或失败。

纯音频 TTS 回复中，`content` 可能包含隐藏口语转录，即使 channel 负载无可见文本/标题。重写该 `content` 仅更新钩子可见转录；不渲染为媒体标题。

消息钩子上下文在可用时暴露稳定关联字段：`ctx.sessionKey`、`ctx.runId`、`ctx.messageId`、`ctx.senderId`、`ctx.trace`、`ctx.traceId`、`ctx.spanId`、`ctx.parentSpanId` 和 `ctx.callDepth`。入站和 `before_dispatch` 上下文还在 channel 有可见性过滤引用消息数据时暴露回复元数据：`replyToId`、`replyToBody` 和 `replyToSender`。优先使用这些一等字段再读遗留元数据。

优先使用类型化 `threadId` 和 `replyToId` 字段再用 channel 专用元数据。

决策规则：

- `message_sending` 带 `cancel: true` 是终结的。
- `message_sending` 带 `cancel: false` 被视为无决策。
- 重写的 `content` 继续到更低优先级钩子，除非后面的钩子取消投递。
- `reply_payload_sending` 在负载规范化后、channel 投递前运行，包括路由回发起 channel 的回复。处理器顺序运行，每个处理器看到更高优先级处理器产生的最新负载。
- `reply_payload_sending` 负载不暴露运行时信任标记如 `trustedLocalMedia`；插件可编辑负载形态但不能授予本地媒体信任。
- `message_sending` 可在取消时返回 `cancelReason` 和有界 `metadata`。新消息生命周期 API 将此暴露为原因 `cancelled_by_message_sending_hook` 的已抑制投递 outcome；遗留直接投递为兼容继续返回空结果数组。
- `message_sent` 仅观察。处理器失败被记录且不改变投递结果。

## 安装钩子

`before_install` 在 operator 持有的 `security.installPolicy` 检查（已配置时）后运行。`builtinScan` 字段保留在事件负载中用于兼容，但 OpenClaw 不再运行内置安装时危险代码阻断，所以它是空 `ok` 结果。返回额外发现或 `{ block: true, blockReason }` 阻止安装。

`block: true` 是终结的。`block: false` 被视为无决策。处理器失败失败关闭阻断安装。

## Gateway 生命周期

`gateway_start` 用于需要 Gateway 持有状态的插件服务。上下文暴露 `ctx.config`、`ctx.workspaceDir` 和 `ctx.getCron?.()` 用于 cron 检查和更新。用 `gateway_stop` 清理长时间运行资源。

不要依赖内部 `gateway:startup` 钩子做插件持有的运行时服务。

`cron_changed` 为 gateway 持有的 cron 生命周期事件触发，带类型化事件负载覆盖 `added`、`updated`、`removed`、`started`、`finished` 和 `scheduled` 原因。事件携带 `PluginHookGatewayCronJob` 快照（包括 `state.nextRunAtMs`、`state.lastRunStatus` 和存在时的 `state.lastError`）加上 `not-requested` | `delivered` | `not-delivered` | `unknown` 的 `PluginHookGatewayCronDeliveryStatus`。Removed 事件仍携带已删除作业快照，外部调度器可协调状态。同步外部唤醒调度器时用运行时上下文中的 `ctx.getCron?.()` 和 `ctx.config`，保持 OpenClaw 作为到期检查和执行的唯一真相源。

## 即将弃用

一些钩子相邻表面已弃用但仍支持。在下一个大版本前迁移：

- **`inbound_claim` 和 `message_received` 处理器中的明文 channel 信封**。读 `BodyForAgent` 和结构化用户上下文块而不是解析扁平信封文本。见 [Plaintext channel envelopes → BodyForAgent](/plugins/sdk-migration#active-deprecations)。
- **`before_agent_start`** 保留用于兼容。新插件应用 `before_model_resolve` 和 `before_prompt_build` 代替组合阶段。
- **`subagent_spawning`** 保留用于兼容旧插件，但新插件不应从中返回线程路由。核心在 `subagent_spawned` 触发前通过 channel 会话绑定适配器准备 `thread: true` 子 agent 绑定。
- **`deactivate`** 保留为已弃用清理兼容别名直到 2026-08-16 后。新插件应用 `gateway_stop`。
- **`before_tool_call` 中的 `onResolution`** 现在使用类型化 `PluginApprovalResolution` 联合（`allow-once` / `allow-always` / `deny` / `timeout` / `cancelled`）而非自由格式 `string`。

完整列表——记忆能力注册、provider 思考档案、外部 auth provider、provider 发现类型、任务运行时访问器和 `command-auth` → `command-status` 重命名——见 [Plugin SDK migration → Active deprecations](/plugins/sdk-migration#active-deprecations)。

## 相关

- [Plugin SDK migration](/plugins/sdk-migration) - 活跃弃用和移除时间线
- [Building plugins](/plugins/building-plugins)
- [Plugin SDK overview](/plugins/sdk-overview)
- [Plugin entry points](/plugins/sdk-entrypoints)
- [Internal hooks](/automation/hooks)
- [Plugin architecture internals](/plugins/architecture-internals)
