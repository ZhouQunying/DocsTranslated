# Agent Harness 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### harness 和 provider 的区别是什么？

Provider 插件回答"用哪个模型 API"——HTTP 端点、认证、模型元数据。Harness 回答"谁来执行这个回合"——原生线程、压缩、工具循环。就像汽车的发动机（provider）和底盘（harness）是分开的：发动机提供动力，底盘决定怎么开。当你有一个自带线程管理和压缩的原生编码 agent 服务器时，普通 HTTP provider 传输是错误的抽象——你需要 harness 来接管整个执行循环。好处是原生 agent 的全部能力都能用上，坏处是比 provider 插件复杂得多，且契约仍在实验中。

第二个关键：选择策略像负载均衡路由规则。模型级运行时策略优先级最高，provider 级次之，`auto` 模式问每个已注册 harness "你支持这个 provider/模型吗"，都不匹配就回退到内置运行时。就像 Nginx 的路由规则——精确匹配优先于通配符，通配符优先于默认。一旦 harness 认领了运行，OpenClaw 不会把同一回合重放到另一个运行时——那会改变认证/运行时语义或重复副作用。

第三个边界：runtimePlan 是宿主持有的策略包。Harness 可用它做需要与 OpenClaw 行为匹配的决策——工具 schema 归一化、会话记录清理、`NO_REPLY` 判断、模型回退分类。但不应修改它或在回合内用它切换 provider/模型。就像 Spring 的 `ApplicationContext`——bean 可以读取上下文做决策，但不应在运行时修改上下文本身。

---

**Agent harness** 是一个准备好的 OpenClaw agent 回合的底层执行器。它不是模型 provider、不是 channel、也不是工具注册表。关于面向用户的心智模型，参见 [Agent runtimes](/concepts/agent-runtimes)。

仅对捆绑或可信原生插件使用此表面。契约仍在实验中，因为参数类型故意镜像当前嵌入式运行器。

## 何时使用 harness

当模型家族有自己的原生会话运行时且普通 OpenClaw provider 传输是错误的抽象时注册 agent harness。

示例：

- 持有线程和压缩的原生编码 agent 服务器
- 必须流式传输原生计划/推理/工具事件的本地 CLI 或守护进程
- 除 OpenClaw 会话记录外还需要自己恢复 id 的模型运行时

**不要**仅仅为了添加新 LLM API 而注册 harness。对普通 HTTP 或 WebSocket 模型 API，构建 [provider 插件](/plugins/sdk-provider-plugins)。

## 核心仍持有的部分

在选择 harness 之前，OpenClaw 已经解析了：

- provider 和模型
- 运行时认证状态
- 思考级别和上下文预算
- OpenClaw 会话记录/会话文件
- 工作区、沙箱和工具策略
- channel 回复回调和流式回调
- 模型回退和实时模型切换策略

这个划分是有意的。Harness 运行一个准备好的尝试；它不挑选 provider、替换 channel 交付或静默切换模型。

准备好的尝试还包括 `params.runtimePlan`，OpenClaw 持有的策略包，用于必须在 OpenClaw 和原生 harness 之间共享的运行时决策：

- `runtimePlan.tools.normalize(...)` 和 `runtimePlan.tools.logDiagnostics(...)` 用于 provider 感知的工具 schema 策略
- `runtimePlan.transcript.resolvePolicy(...)` 用于会话记录清理和工具调用修复策略
- `runtimePlan.delivery.isSilentPayload(...)` 用于共享的 `NO_REPLY` 和媒体交付抑制
- `runtimePlan.outcome.classifyRunResult(...)` 用于模型回退分类
- `runtimePlan.observability` 用于已解析的 provider/模型/harness 元数据

Harness 可用 plan 做需要与 OpenClaw 行为匹配的决策，但仍应将其视为宿主持有的尝试状态。不要修改它或在回合内用它切换 provider/模型。

## 注册 harness

**导入：** `openclaw/plugin-sdk/agent-harness`

```typescript

const myHarness: AgentHarness = {
  id: "my-harness",
  label: "My native agent harness",

  supports(ctx) {
    return ctx.provider === "my-provider"
      ? { supported: true, priority: 100 }
      : { supported: false };
  },

  async runAttempt(params) {
    // 启动或恢复你的原生线程。
    // 使用 params.prompt、params.tools、params.images、params.onPartialReply、
    // params.onAgentEvent 和其他准备好的尝试字段。
    return await runMyNativeTurn(params);
  },
};

export default definePluginEntry({
  id: "my-native-agent",
  name: "My Native Agent",
  description: "Runs selected models through a native agent daemon.",
  register(api) {
    api.registerAgentHarness(myHarness);
  },
});
```

## 选择策略

OpenClaw 在 provider/模型解析后选择 harness：

1. 模型级运行时策略优先。
2. provider 级运行时策略次之。
3. `auto` 询问已注册 harness 是否支持已解析的 provider/模型。
4. 如果没有已注册 harness 匹配，OpenClaw 使用其嵌入式运行时。

插件 harness 失败作为运行失败浮出。在 `auto` 模式下，仅当没有已注册插件 harness 支持已解析的 provider/模型时才使用嵌入式后备。一旦插件 harness 认领了运行，OpenClaw 不会把同一回合重放到另一个运行时，因为那会改变认证/运行时语义或重复副作用。

全会话和全 agent 运行时固定被选择忽略。这包括过期的会话 `agentHarnessId` 值、`agents.defaults.agentRuntime`、`agents.list[].agentRuntime` 和 `OPENCLAW_AGENT_RUNTIME`。`/status` 显示从 provider/模型路由选择的有效运行时。如果选择的 harness 出乎意料，启用 `agents/harness` 调试日志并检查 gateway 的结构化 `agent harness selected` 记录。它包括选择的 harness id、选择原因、运行时/回退策略，以及 `auto` 模式下每个插件候选的支持结果。

捆绑 Codex 插件以 `codex` 作为其 harness id 注册。核心将其视为普通插件 harness id；Codex 特定别名属于插件或 operator 配置，不在共享运行时选择器中。

## Provider 加 harness 配对

大多数 harness 应同时注册 provider。Provider 让模型 ref、认证状态、模型元数据和 `/model` 选择对 OpenClaw 其余部分可见。Harness 然后在 `supports(...)` 中认领该 provider。

捆绑 Codex 插件遵循此模式：

- 首选用户模型 ref：`openai/gpt-5.5`
- 兼容 ref：遗留 `codex/gpt-*` ref 仍被接受，但新配置不应将它们用作普通 provider/模型 ref
- harness id：`codex`
- 认证：合成 provider 可用性，因为 Codex harness 持有原生 Codex 登录/会话
- app-server 请求：OpenClaw 将裸模型 id 发送给 Codex，让 harness 与原生 app-server 协议对话

Codex 插件是增量的。官方 OpenAI provider 上的普通 `openai/gpt-*` agent ref 默认选择 Codex harness。旧 `codex/gpt-*` ref 仍选择 Codex provider 和 harness 以保持兼容。

关于 operator 设置、模型前缀示例和仅 Codex 配置，参见 [Codex Harness](/plugins/codex-harness)。

OpenClaw 要求 Codex app-server `0.125.0` 或更新。Codex 插件检查 app-server 初始化握手并阻止旧版或无版本服务器，OpenClaw 只针对已测试的协议表面运行。`0.125.0` 下限包括 Codex `0.124.0` 中落地的原生 MCP 钩子负载支持，同时将 OpenClaw 固定到更新的已测试稳定线。

### 工具结果中间件

捆绑插件可在 manifest 声明目标运行时 id 到 `contracts.agentToolResultMiddleware` 时通过 `api.registerAgentToolResultMiddleware(...)` 附加运行时无关的工具结果中间件。此可信接缝用于必须在 OpenClaw 或 Codex 将工具输出送回模型前运行的异步工具结果变换。

遗留捆绑插件仍可使用 `api.registerCodexAppServerExtensionFactory(...)` 用于仅 Codex app-server 的中间件，但新结果变换应使用运行时无关 API。仅嵌入式运行器的 `api.registerEmbeddedExtensionFactory(...)` 钩子已移除；嵌入式工具结果变换必须使用运行时无关中间件。

### 终止结果分类

持有自己协议投影的原生 harness 可在已完成回合未产生可见助手文本时使用 `openclaw/plugin-sdk/agent-harness-runtime` 的 `classifyAgentHarnessTerminalOutcome(...)`。helper 返回 `empty`、`reasoning-only` 或 `planning-only`，OpenClaw 的回退策略可据此决定是否在不同模型上重试。它故意不分类提示错误、进行中的回合和如 `NO_REPLY` 的有意静默回复。

### 原生 Codex harness 模式

捆绑 `codex` harness 是嵌入式 OpenClaw agent 回合的原生 Codex 模式。先启用捆绑 `codex` 插件，如果配置使用限制允许列表则在 `plugins.allow` 中包含 `codex`。原生 app-server 配置应使用 `openai/gpt-*`；OpenAI agent 回合默认选择 Codex harness。遗留 Codex 模型 ref 路由应用 `openclaw doctor --fix` 修复，遗留 `codex/*` 模型 ref 保持为原生 harness 的兼容别名。

当此模式运行时，Codex 持有原生线程 id、恢复行为、压缩和 app-server 执行。OpenClaw 仍持有聊天 channel、可见会话记录镜像、工具策略、审批、媒体交付和会话选择。需要证明只有 Codex app-server 路径能认领运行时使用 provider/模型 `agentRuntime.id: "codex"`。显式插件运行时做 fail closed；Codex app-server 选择失败和运行时失败不通过另一个运行时重试。

## 运行时严格性

默认 OpenClaw 使用 `auto` provider/模型运行时策略：已注册插件 harness 可认领 provider/模型对，嵌入式运行时在没有匹配时处理回合。官方 OpenAI provider 上的 OpenAI agent ref 默认到 Codex。当缺失 harness 选择应该失败而非路由到嵌入式运行时时使用显式 provider/模型插件运行时如 `agentRuntime.id: "codex"`。选中的插件 harness 失败总是硬失败。这不阻止显式 provider/模型 `agentRuntime.id: "openclaw"`。

仅 Codex 嵌入式运行：

```json
{
  "models": {
    "providers": {
      "openai": {
        "agentRuntime": {
          "id": "codex"
        }
      }
    }
  },
  "agents": {
    "defaults": {
      "model": "openai/gpt-5.5"
    }
  }
}
```

如果想为一个标准模型使用 CLI 后端，将运行时放在该模型条目上：

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-8",
      "models": {
        "anthropic/claude-opus-4-8": {
          "agentRuntime": {
            "id": "claude-cli"
          }
        }
      }
    }
  }
}
```

按 agent 覆盖使用相同的模型级形态：

```json
{
  "agents": {
    "list": [
      {
        "id": "codex-only",
        "model": "openai/gpt-5.5",
        "models": {
          "openai/gpt-5.5": {
            "agentRuntime": { "id": "codex" }
          }
        }
      }
    ]
  }
}
```

如下遗留全 agent 运行时示例被忽略：

```json
{
  "agents": {
    "defaults": {
      "agentRuntime": {
        "id": "codex"
      }
    }
  }
}
```

使用显式插件运行时，当请求的 harness 未注册、不支持已解析的 provider/模型或在产生回合副作用前失败时会话早期失败。这对仅 Codex 部署和必须证明 Codex app-server 路径真正在使用的实时测试是有意的。

此设置仅控制嵌入式 agent harness。它不禁用图片、视频、音乐、TTS、PDF 或其他 provider 特定模型路由。

## 原生命令和会话记录镜像

Harness 可持有原生命令 id、线程 id 或守护进程侧恢复 token。保持该绑定与 OpenClaw 会话显式关联，并继续将用户可见的助手/工具输出镜像到 OpenClaw 会话记录。

OpenClaw 会话记录仍是以下内容的兼容层：

- channel 可见会话历史
- 会话记录搜索和索引
- 在后续回合切换回内置 OpenClaw harness
- 通用 `/new`、`/reset` 和会话删除行为

如果你的 harness 存储 sidecar 绑定，实现 `reset(...)`，OpenClaw 可在所属 OpenClaw 会话重置时清除它。

## 工具和媒体结果

核心构建 OpenClaw 工具列表并传入准备好的尝试。当 harness 执行动态工具调用时，通过 harness 结果形态返回工具结果，而非自己发送 channel 媒体。

这保持文本、图片、视频、音乐、TTS、审批和消息工具输出在与 OpenClaw 支持的运行相同的交付路径上。

## 当前限制

- 公共导入路径是通用的，但一些尝试/结果类型别名仍携带遗留名称以保持兼容。
- 第三方 harness 安装是实验性的。优先使用 provider 插件，直到需要原生会话运行时。
- Harness 切换支持跨回合。不要在回合中途原生工具、审批、助手文本或消息发送已开始后切换 harness。

## 相关

- [SDK Overview](/plugins/sdk-overview)
- [Runtime Helpers](/plugins/sdk-runtime)
- [Provider Plugins](/plugins/sdk-provider-plugins)
- [Codex Harness](/plugins/codex-harness)
- [Model Providers](/concepts/model-providers)
