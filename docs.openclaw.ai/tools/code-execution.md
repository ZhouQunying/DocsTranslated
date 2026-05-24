# Code execution

> `code_execution` runs sandboxed remote Python analysis on xAI's Responses API. It is registered by the bundled `xai` plugin (under the `tools` contract) and dispatches to the same `https://api.x.ai/v1/responses` endpoint used by `x_search`.

`code_execution` 在 xAI 的 Responses API 上跑沙箱化的远程 Python 分析。它由内置的 `xai` 插件(在 `tools` 契约下)注册,发到跟 `x_search` 同一个端点 `https://api.x.ai/v1/responses`。

| 属性                | 值                                                                                |
| ------------------- | --------------------------------------------------------------------------------- |
| 工具名              | `code_execution`                                                                  |
| Provider 插件       | `xai`(内置,`enabledByDefault: true`)                                            |
| 认证                | xAI 认证 profile、`XAI_API_KEY`、或 `plugins.entries.xai.config.webSearch.apiKey` |
| 默认模型            | `grok-4-1-fast`                                                                   |
| 默认超时            | 30 秒                                                                             |
| 默认 `maxTurns`     | 不设(xAI 自己内部限制)                                                          |

> This is different from local [`exec`](/tools/exec):
>
> - `exec` runs shell commands on your machine or paired node.
> - `code_execution` runs Python in xAI's remote sandbox.

它跟本地的 [`exec`](/tools/exec) 不一样:

- `exec` 在你的机器上或配对节点上跑 shell 命令。
- `code_execution` 在 xAI 的远程沙箱里跑 Python。

> Use `code_execution` for:
>
> - Calculations.
> - Tabulation.
> - Quick statistics.
> - Chart-style analysis.
> - Analyzing data returned by `x_search` or `web_search`.

什么时候用 `code_execution`:

- 计算。
- 列表统计。
- 简单统计。
- 类图表式分析。
- 分析 `x_search` 或 `web_search` 返回的数据。

> Do **not** use it when you need local files, your shell, your repo, or paired devices. Use [`exec`](/tools/exec) for that.

需要本地文件、你的 shell、你的仓库、配对设备时,**别**用它。那些用 [`exec`](/tools/exec)。

## 配置

> <Step title="Provide xAI credentials">

[步骤 1: 准备 xAI 凭证]

> Sign in with Grok OAuth using an eligible SuperGrok or X Premium subscription,
> use the remote-friendly device-code flow, or store an API key. OAuth works
> for `code_execution` and `x_search`; `XAI_API_KEY` or plugin web-search
> config can also power Grok `web_search`.

用合格的 SuperGrok 或 X Premium 订阅走 Grok OAuth 登录、走对远程友好的 device-code 流程,或者存一个 API key。OAuth 对 `code_execution` 和 `x_search` 都管用;`XAI_API_KEY` 或插件的 web-search 配置也能给 Grok `web_search` 供能。

```bash
openclaw models auth login --provider xai --method oauth
openclaw models auth login --provider xai --device-code
```

> During a fresh install, the same auth choices are available inside
> onboarding:

全新安装时,同样的认证选择在 onboarding 里也能用:

```bash
openclaw onboard --install-daemon
openclaw onboard --install-daemon --auth-choice xai-device-code
```

> Or use an API key:

或者用 API key:

```bash
openclaw models auth login --provider xai --method api-key
export XAI_API_KEY=xai-...
```

> Or via config:

或者通过配置:

```json5
{
  plugins: {
    entries: {
      xai: {
        config: {
          webSearch: {
            apiKey: "xai-...",
          },
        },
      },
    },
  },
}
```

> <Step title="Enable and tune code_execution">

[步骤 2: 启用并调整 code_execution]

> `code_execution` is available when xAI credentials are available. Set
> `plugins.entries.xai.config.codeExecution.enabled` to `false` to disable it,
> or use the same block to tune the model and timeout.

xAI 凭证有了之后,`code_execution` 就可用。把 `plugins.entries.xai.config.codeExecution.enabled` 设成 `false` 关掉,或者在同一块里调模型和超时。

```json5
{
  plugins: {
    entries: {
      xai: {
        config: {
          codeExecution: {
            enabled: true,
            model: "grok-4-1-fast", // 覆盖默认的 xAI code-execution 模型
            maxTurns: 2,            // 可选:限制内部工具轮次
            timeoutSeconds: 30,     // 请求超时(默认 30)
          },
        },
      },
    },
  },
}
```

> <Step title="Restart the Gateway">

[步骤 3: 重启 Gateway]

```bash
openclaw gateway restart
```

> `code_execution` shows up in the agent's tool list once the xAI plugin re-registers with `enabled: true`.

xAI 插件以 `enabled: true` 重新注册后,`code_execution` 就会出现在 agent 的工具列表里。

## 怎么用

> Ask naturally and make the analysis intent explicit:

自然提问,并把分析意图说清楚:

```text
Use code_execution to calculate the 7-day moving average for these numbers: ...
```

```text
Use x_search to find posts mentioning OpenClaw this week, then use code_execution to count them by day.
```

```text
Use web_search to gather the latest AI benchmark numbers, then use code_execution to compare percent changes.
```

> The tool takes a single `task` parameter internally, so the agent should send the full analysis request and any inline data in one prompt.

工具内部只接受一个 `task` 参数,所以 agent 应该把完整的分析请求和任何内联数据放在一个 prompt 里发。

## 错误

> When the tool runs without auth, it returns a structured `missing_xai_api_key` error pointing at the auth-profile, env var, and config options. The error is JSON, not a thrown exception, so the agent can self-correct:

工具在没认证的情况下跑,会返回一个结构化的 `missing_xai_api_key` 错误,指向认证 profile、环境变量、配置三个选项。错误是 JSON,不是抛异常,所以 agent 能自我纠正:

```json
{
  "error": "missing_xai_api_key",
  "message": "code_execution needs xAI credentials. Run `openclaw onboard --auth-choice xai-oauth` to sign in with Grok, run `openclaw onboard --auth-choice xai-api-key`, set `XAI_API_KEY` in the Gateway environment, or configure `plugins.entries.xai.config.webSearch.apiKey`.",
  "docs": "https://docs.openclaw.ai/tools/code-execution"
}
```

## 限制

> - This is remote xAI execution, not local process execution.
> - Treat results as ephemeral analysis, not a persistent notebook session.
> - Do not assume access to local files or your workspace.
> - For fresh X data, use [`x_search`](/tools/web#x_search) first and pipe the result into `code_execution`.

- 这是 xAI 远程执行,不是本地进程执行。
- 把结果当作临时分析,不是持久 notebook 会话。
- 不要假设能访问本地文件或你的工作区。
- 要新鲜的 X 数据,先用 [`x_search`](/tools/web#x_search),再把结果导给 `code_execution`。

## 相关

> - Exec tool — Local shell execution on your machine or paired node.
> - Exec approvals — Allow/deny policy for shell execution.
> - Web tools — `web_search`, `x_search`, and `web_fetch`.
> - xAI provider — Grok models, web/x search, and code execution config.

- [Exec tool](/tools/exec) —— 本地机器或配对节点上的 shell 执行。
- [Exec approvals](/tools/exec-approvals) —— shell 执行的允许 / 拒绝策略。
- [Web tools](/tools/web) —— `web_search`、`x_search`、`web_fetch`。
- [xAI provider](/providers/xai) —— Grok 模型、web/x 搜索、code execution 配置。
