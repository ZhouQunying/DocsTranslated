# LLM task

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 想调另一个 LLM 做子任务——但不是聊天，是"给输入、要 JSON 输出"

场景：Lobster 工作流某一步需要"从这段文本提取结构化数据"。不需要对话、不需要工具、不需要历史——就是"输入 → JSON 输出"。

`llm-task` 就干这一件事：调一次 LLM，强制 JSON 输出，可选 Schema 验证。没有对话上下文，没有工具注入，纯函数调用语义。

为什么不直接内联到主 Agent 的上下文里？因为主 Agent 的上下文已经很贵了。用一次独立的便宜模型调用来做子任务，主模型的上下文不受污染，还能用 Schema 保证输出格式正确。

跟微服务拆分一个意思：能独立处理的逻辑就拆出去，别挤在一个大进程里。

---

> `llm-task` is an **optional plugin tool** that runs a JSON-only LLM task and
> returns structured output (optionally validated against JSON Schema).

`llm-task` 是一个**可选的插件工具**,跑只输出 JSON 的 LLM 任务,返回结构化输出(可选用 JSON Schema 校验)。

> This is ideal for workflow engines like Lobster: you can add a single LLM step
> without writing custom OpenClaw code for each workflow.

它特别适合 Lobster 这种工作流引擎:不用为每个工作流写自定义 OpenClaw 代码,就能加一步 LLM。

## 启用插件

> 1. Enable the plugin:

1. 启用插件:

```json
{
  "plugins": {
    "entries": {
      "llm-task": { "enabled": true }
    }
  }
}
```

> 2. Allow the optional tool:

2. 把这个可选工具放进 allow:

```json
{
  "tools": {
    "alsoAllow": ["llm-task"]
  }
}
```

> Use `tools.allow` only when you want restrictive allowlist mode.

只有想要严格的白名单模式时才用 `tools.allow`。

## 配置(可选)

```json
{
  "plugins": {
    "entries": {
      "llm-task": {
        "enabled": true,
        "config": {
          "defaultProvider": "openai-codex",
          "defaultModel": "gpt-5.5",
          "defaultAuthProfileId": "main",
          "allowedModels": ["openai/gpt-5.4"],
          "maxTokens": 800,
          "timeoutMs": 30000
        }
      }
    }
  }
}
```

> `allowedModels` is an allowlist of `provider/model` strings. If set, any request
> outside the list is rejected.

`allowedModels` 是 `provider/model` 字符串的白名单。设了之后,任何不在列表里的请求都会被拒。

## 工具参数

> - `prompt` (string, required)
> - `input` (any, optional)
> - `schema` (object, optional JSON Schema)
> - `provider` (string, optional)
> - `model` (string, optional)
> - `thinking` (string, optional)
> - `authProfileId` (string, optional)
> - `temperature` (number, optional)
> - `maxTokens` (number, optional)
> - `timeoutMs` (number, optional)

- `prompt`(string,必填)
- `input`(任意,可选)
- `schema`(object,可选 JSON Schema)
- `provider`(string,可选)
- `model`(string,可选)
- `thinking`(string,可选)
- `authProfileId`(string,可选)
- `temperature`(number,可选)
- `maxTokens`(number,可选)
- `timeoutMs`(number,可选)

> `thinking` accepts the standard OpenClaw reasoning presets, such as `low` or `medium`.

`thinking` 接受标准的 OpenClaw 推理预设,如 `low`、`medium`。

## 输出

> Returns `details.json` containing the parsed JSON (and validates against
> `schema` when provided).

返回 `details.json`,内含解析出的 JSON(给了 `schema` 就用它校验)。

## 示例:Lobster 工作流步骤

### 重要限制

> The example below assumes the **standalone Lobster CLI** is running in an environment where `openclaw.invoke` already has the correct gateway URL/auth context.

下面例子假定**独立 Lobster CLI** 跑在 `openclaw.invoke` 已经拿到正确 gateway URL 和认证上下文的环境里。

> For the bundled **embedded** Lobster runner inside OpenClaw, this nested CLI pattern is **not currently reliable**:

对 OpenClaw 里内置的**嵌入式** Lobster 运行器,这种嵌套 CLI 模式**目前不可靠**:

```lobster
openclaw.invoke --tool llm-task --action json --args-json '{ ... }'
```

> Until embedded Lobster has a supported bridge for this flow, prefer either:
>
> - direct `llm-task` tool calls outside Lobster, or
> - Lobster steps that do not rely on nested `openclaw.invoke` calls.

在嵌入式 Lobster 支持这条流程之前,优先用:

- Lobster 外面直接调 `llm-task` 工具,或
- 不依赖嵌套 `openclaw.invoke` 调用的 Lobster 步骤。

> Standalone Lobster CLI example:

独立 Lobster CLI 例子:

```lobster
openclaw.invoke --tool llm-task --action json --args-json '{
  "prompt": "Given the input email, return intent and draft.",
  "thinking": "low",
  "input": {
    "subject": "Hello",
    "body": "Can you help?"
  },
  "schema": {
    "type": "object",
    "properties": {
      "intent": { "type": "string" },
      "draft": { "type": "string" }
    },
    "required": ["intent", "draft"],
    "additionalProperties": false
  }
}'
```

## 安全提示

> - The tool is **JSON-only** and instructs the model to output only JSON (no
>   code fences, no commentary).
> - No tools are exposed to the model for this run.
> - Treat output as untrusted unless you validate with `schema`.
> - Put approvals before any side-effecting step (send, post, exec).

- 工具**只发 JSON**,会指示模型只输出 JSON(不要代码围栏、不要解释)。
- 这一次运行不给模型暴露任何工具。
- 没用 `schema` 校验的话,把输出当作不可信。
- 任何有副作用的步骤(发、贴、exec)之前放审批。

## 相关

> - [Thinking levels](/tools/thinking)
> - [Sub-agents](/tools/subagents)
> - [Slash commands](/tools/slash-commands)

- [思考级别](/tools/thinking)
- [Sub-agents](/tools/subagents)
- [Slash 命令](/tools/slash-commands)
