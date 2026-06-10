# Agent send

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 不一定是"等用户说话才动"的——怎么从脚本主动触发？

正常流程：用户发消息 → agent 回复。但很多场景是反过来的：cron 脚本、CI 流水线、监控告警想让 agent 主动干活再把结果发到某个通道。

`openclaw agent` 的设计就是这个入口：命令行发一条消息,走 Gateway 跑一轮 agent,拿到回复。加 `--deliver` 就把回复投递到 WhatsApp、Slack、Telegram 等通道。

跟 HTTP API 的 webhook 一个道理：外部系统通过标准接口触发内部流程。区别是这里触发的不是一个 API handler,而是一整个 agent 轮次。

另一个关键：session 路由。`--to` 从目标(手机号、chat id)推导 session key;`--session-key` 精确指定。这保证同一个用户的上下文被正确复用,不同用户的上下文隔离。

---

> `openclaw agent` runs a single agent turn from the command line without needing
> an inbound chat message. Use it for scripted workflows, testing, and
> programmatic delivery.

`openclaw agent` 从命令行跑单次 agent 轮次,不需要入站聊天消息。用它做脚本化工作流、测试、和编程式投递。

## 快速开始

> <Step title="Run a simple agent turn">

[步骤 1: 跑一次简单的 agent 轮次]

```bash
openclaw agent --agent main --message "What is the weather today?"
```

> This sends the message through the Gateway and prints the reply.

把消息发给 Gateway,打印回复。

> <Step title="Target a specific agent or session">

[步骤 2: 指定 agent 或会话]

```bash
# 指定 agent
openclaw agent --agent ops --message "Summarize logs"

# 指定手机号(推导 session key)
openclaw agent --to +15555550123 --message "Status update"

# 复用已有会话
openclaw agent --session-id abc123 --message "Continue the task"

# 精确 session key
openclaw agent --session-key agent:ops:incident-42 --message "Summarize status"
```

> <Step title="Deliver the reply to a channel">

[步骤 3: 把回复投递到通道]

```bash
# 投递到 WhatsApp(默认通道)
openclaw agent --to +15555550123 --message "Report ready" --deliver

# 投递到 Slack
openclaw agent --agent ops --message "Generate report" \
  --deliver --reply-channel slack --reply-to "#reports"
```

## 标志

> | Flag | Description |

| 标志                          | 说明                                                  |
| ----------------------------- | ----------------------------------------------------- |
| `--message <文本>`            | 要发的消息(必填)                                    |
| `--to <目标>`                 | 从目标(手机号、chat id)推导 session key             |
| `--session-key <key>`         | 使用精确的 session key                                |
| `--agent <id>`                | 指定 agent(用它的 `main` 会话)                      |
| `--session-id <id>`           | 复用已有会话(按 id)                                 |
| `--local`                     | 强制本地嵌入式运行时(跳过 Gateway)                  |
| `--deliver`                   | 把回复发到聊天通道                                    |
| `--channel <名称>`            | 投递通道(whatsapp、telegram、discord、slack 等)     |
| `--reply-to <目标>`           | 投递目标覆盖                                          |
| `--reply-channel <名称>`      | 投递通道覆盖                                          |
| `--reply-account <id>`        | 投递账户 id 覆盖                                      |
| `--thinking <级别>`           | 设思考级别                                            |
| `--verbose <on\|full\|off>`   | 设 verbose 级别                                       |
| `--timeout <秒>`              | 覆盖 agent 超时                                       |
| `--json`                      | 输出结构化 JSON                                       |

## 行为

> - By default, the CLI goes through the Gateway. Add `--local` to force the embedded runtime on the current machine.
> - If the Gateway is unreachable, the CLI falls back to the local embedded run.

- 默认走 Gateway。加 `--local` 强制在本机跑嵌入式运行时。
- Gateway 不可达时,CLI 回退到本地嵌入式运行。

> - Session selection: `--to` derives the session key (group/channel targets preserve isolation; direct chats collapse to `main`).

- 会话选择:`--to` 推导 session key(群 / 通道目标保持隔离;私聊折叠到 `main`)。

> - `--session-key` selects an explicit key. Agent-prefixed keys must use `agent:<agent-id>:<session-key>`, and `--agent` must match that agent id when both are supplied. Bare non-sentinel keys are scoped to `--agent` when supplied; for example, `--agent ops --session-key incident-42` routes to `agent:ops:incident-42`. Without `--agent`, bare non-sentinel keys are scoped to the configured default agent. Literal `global` and `unknown` remain unscoped only when no `--agent` is supplied; in that case, embedded fallback and store ownership use the configured default agent.

- `--session-key` 精确选择。带 agent 前缀的 key 必须用 `agent:<agent-id>:<session-key>` 格式,两个都给时 `--agent` 必须匹配。裸的非哨兵 key 在给了 `--agent` 时被限定作用域,如 `--agent ops --session-key incident-42` 路由到 `agent:ops:incident-42`。没给 `--agent` 时裸 key 限定到默认 agent。字面 `global` 和 `unknown` 只在没给 `--agent` 时保持无作用域;此时嵌入式回退和存储归属用默认 agent。

> - Thinking and verbose flags persist into the session store.
> - Output: plain text by default, or `--json` for structured payload + metadata.
> - With `--json --deliver`, the JSON includes delivery status for sent, suppressed, partial, and failed sends.

- thinking 和 verbose 标志持久化到会话存储。
- 输出:默认纯文本;`--json` 给结构化载荷 + 元数据。
- `--json --deliver` 时,JSON 含投递状态(sent、suppressed、partial、failed)。见 [JSON 投递状态](/cli/agent#json-delivery-status)。

## 例子

```bash
# 简单轮次,JSON 输出
openclaw agent --to +15555550123 --message "Trace logs" --verbose on --json

# 带思考级别的轮次
openclaw agent --session-id 1234 --message "Summarize inbox" --thinking medium

# 精确 session key
openclaw agent --session-key agent:ops:incident-42 --message "Summarize status"

# 限定到 agent 的旧式 key
openclaw agent --agent ops --session-key incident-42 --message "Summarize status"

# 投递到跟会话不同的通道
openclaw agent --agent ops --message "Alert" --deliver --reply-channel telegram --reply-to "@admin"
```

## 相关

> - Agent CLI reference
> - Sub-agents
> - Sessions
> - Slash commands

- [Agent CLI 参考](/cli/agent) —— 完整的 `openclaw agent` 标志和选项参考。
- [Sub-agents](/tools/subagents) —— 后台子 agent 孵化。
- [会话](/concepts/session) —— session key 怎么工作,`--to`、`--agent`、`--session-id` 怎么解析。
- [Slash 命令](/tools/slash-commands) —— agent 会话内用的原生命令目录。
