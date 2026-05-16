# Broadcast groups

> <Note>
>   **Status:** Experimental. Added in 2026.1.9.
> </Note>

> **状态**：实验功能。从 2026.1.9 开始引入。

---

> ## Overview

## 概述

> Broadcast Groups enable multiple agents to process and respond to the same message simultaneously. This allows you to create specialized agent teams that work together in a single WhatsApp group or DM — all using one phone number.

广播组（Broadcast Groups）让多个 agent 同时处理并回应同一条消息。这样在一个 WhatsApp 群或私聊里就能组建一支专业 agent 队伍协同工作 —— 全程只用一个手机号。

> Current scope: **WhatsApp only** (web channel).

当前范围：**仅支持 WhatsApp**（web channel）。

> Broadcast groups are evaluated after channel allowlists and group activation rules. In WhatsApp groups, this means broadcasts happen when OpenClaw would normally reply (for example: on mention, depending on your group settings).

广播组的判断顺序在通道白名单和群激活规则之后。在 WhatsApp 群里这意味着：原本 OpenClaw 会回复的时候才会触发广播（比如被 @ 时，取决于你的群设置）。

---

> ## Use cases

## 应用场景

> [展开: 1. Specialized agent teams]
>
> Deploy multiple agents with atomic, focused responsibilities:
>
> ```
> Group: "Development Team"
> Agents:
>   - CodeReviewer (reviews code snippets)
>   - DocumentationBot (generates docs)
>   - SecurityAuditor (checks for vulnerabilities)
>   - TestGenerator (suggests test cases)
> ```
>
> Each agent processes the same message and provides its specialized perspective.

[展开：1. 专业化 agent 团队]

部署多个职责单一、聚焦的 agent：

```
群："开发团队"
Agents：
  - CodeReviewer（代码片段审查）
  - DocumentationBot（生成文档）
  - SecurityAuditor（查漏洞）
  - TestGenerator（建议测试用例）
```

每个 agent 处理同一条消息，给出自己专业视角下的回应。

> [展开: 2. Multi-language support]
>
> ```
> Group: "International Support"
> Agents:
>   - Agent_EN (responds in English)
>   - Agent_DE (responds in German)
>   - Agent_ES (responds in Spanish)
> ```

[展开：2. 多语言支持]

```
群："国际化支持"
Agents：
  - Agent_EN（用英文回）
  - Agent_DE（用德文回）
  - Agent_ES（用西文回）
```

> [展开: 3. Quality assurance workflows]
>
> ```
> Group: "Customer Support"
> Agents:
>   - SupportAgent (provides answer)
>   - QAAgent (reviews quality, only responds if issues found)
> ```

[展开：3. 质量保证工作流]

```
群："客户支持"
Agents：
  - SupportAgent（给出答案）
  - QAAgent（质量复审，只在发现问题时才回）
```

> [展开: 4. Task automation]
>
> ```
> Group: "Project Management"
> Agents:
>   - TaskTracker (updates task database)
>   - TimeLogger (logs time spent)
>   - ReportGenerator (creates summaries)
> ```

[展开：4. 任务自动化]

```
群："项目管理"
Agents：
  - TaskTracker（更新任务数据库）
  - TimeLogger（记录工时）
  - ReportGenerator（生成总结报告）
```

---

> ## Configuration

## 配置

> ### Basic setup

### 基础配置

> Add a top-level `broadcast` section (next to `bindings`). Keys are WhatsApp peer ids:
>
> * group chats: group JID (e.g. `120363403215116621@g.us`)
> * DMs: E.164 phone number (e.g. `+15551234567`)

在顶层加一个 `broadcast` 段（和 `bindings` 同级）。key 是 WhatsApp 的 peer id：

- 群聊：群 JID（如 `120363403215116621@g.us`）
- 私聊：E.164 电话号码（如 `+15551234567`）

> ```json
> {
>   "broadcast": {
>     "120363403215116621@g.us": ["alfred", "baerbel", "assistant3"]
>   }
> }
> ```

```json
{
  "broadcast": {
    "120363403215116621@g.us": ["alfred", "baerbel", "assistant3"]
  }
}
```

> **Result:** When OpenClaw would reply in this chat, it will run all three agents.

**效果**：每当 OpenClaw 要在这个聊天里回复时，三个 agent 都会跑一遍。

---

> ### Processing strategy

### 处理策略

> Control how agents process messages:

控制多个 agent 怎么处理消息：

> [标签页: parallel (default)]
>
> All agents process simultaneously:
>
> ```json
> {
>   "broadcast": {
>     "strategy": "parallel",
>     "120363403215116621@g.us": ["alfred", "baerbel"]
>   }
> }
> ```

[标签页：parallel（默认）]

所有 agent 同时处理：

```json
{
  "broadcast": {
    "strategy": "parallel",
    "120363403215116621@g.us": ["alfred", "baerbel"]
  }
}
```

> [标签页: sequential]
>
> Agents process in order (one waits for previous to finish):
>
> ```json
> {
>   "broadcast": {
>     "strategy": "sequential",
>     "120363403215116621@g.us": ["alfred", "baerbel"]
>   }
> }
> ```

[标签页：sequential]

agent 按顺序处理（后一个等前一个跑完）：

```json
{
  "broadcast": {
    "strategy": "sequential",
    "120363403215116621@g.us": ["alfred", "baerbel"]
  }
}
```

---

> ### Complete example

### 完整示例

> ```json
> {
>   "agents": {
>     "list": [
>       {
>         "id": "code-reviewer",
>         "name": "Code Reviewer",
>         "workspace": "/path/to/code-reviewer",
>         "sandbox": { "mode": "all" }
>       },
>       {
>         "id": "security-auditor",
>         "name": "Security Auditor",
>         "workspace": "/path/to/security-auditor",
>         "sandbox": { "mode": "all" }
>       },
>       {
>         "id": "docs-generator",
>         "name": "Documentation Generator",
>         "workspace": "/path/to/docs-generator",
>         "sandbox": { "mode": "all" }
>       }
>     ]
>   },
>   "broadcast": {
>     "strategy": "parallel",
>     "120363403215116621@g.us": ["code-reviewer", "security-auditor", "docs-generator"],
>     "120363424282127706@g.us": ["support-en", "support-de"],
>     "+15555550123": ["assistant", "logger"]
>   }
> }
> ```

```json
{
  "agents": {
    "list": [
      {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "workspace": "/path/to/code-reviewer",
        "sandbox": { "mode": "all" }
      },
      {
        "id": "security-auditor",
        "name": "Security Auditor",
        "workspace": "/path/to/security-auditor",
        "sandbox": { "mode": "all" }
      },
      {
        "id": "docs-generator",
        "name": "Documentation Generator",
        "workspace": "/path/to/docs-generator",
        "sandbox": { "mode": "all" }
      }
    ]
  },
  "broadcast": {
    "strategy": "parallel",
    "120363403215116621@g.us": ["code-reviewer", "security-auditor", "docs-generator"],
    "120363424282127706@g.us": ["support-en", "support-de"],
    "+15555550123": ["assistant", "logger"]
  }
}
```

---

> ## How it works

## 工作原理

> ### Message flow

### 消息流程

> [步骤 1: Incoming message arrives] A WhatsApp group or DM message arrives.

[步骤 1：消息到达] 一条 WhatsApp 群或私聊消息送达。

> [步骤 2: Broadcast check] System checks if peer ID is in `broadcast`.

[步骤 2：广播检查] 系统检查这个 peer ID 是否在 `broadcast` 里。

> [步骤 3: If in broadcast list]
>
> * All listed agents process the message.
> * Each agent has its own session key and isolated context.
> * Agents process in parallel (default) or sequentially.

[步骤 3：在广播列表里]

- 列表里的所有 agent 都会处理这条消息。
- 每个 agent 有独立的 session key 和隔离的上下文。
- 默认并行处理；可以配成顺序处理。

> [步骤 4: If not in broadcast list]
>
> Normal routing applies (first matching binding).

[步骤 4：不在广播列表里]

走普通路由（命中的第一条 binding）。

> <Note>
>   Broadcast groups do not bypass channel allowlists or group activation rules (mentions/commands/etc). They only change *which agents run* when a message is eligible for processing.
> </Note>

> **提示**：广播组不会绕过通道白名单或群激活规则（@ 触发、命令等）。它只决定一条消息可处理时**由哪些 agent 来跑**。

---

> ### Session isolation

### 会话隔离

> Each agent in a broadcast group maintains completely separate:
>
> * **Session keys** (`agent:alfred:whatsapp:group:120363...` vs `agent:baerbel:whatsapp:group:120363...`)
> * **Conversation history** (agent doesn't see other agents' messages)
> * **Workspace** (separate sandboxes if configured)
> * **Tool access** (different allow/deny lists)
> * **Memory/context** (separate IDENTITY.md, SOUL.md, etc.)
> * **Group context buffer** (recent group messages used for context) is shared per peer, so all broadcast agents see the same context when triggered

广播组里每个 agent 各自完全独立的部分：

- **Session key**（如 `agent:alfred:whatsapp:group:120363...` 与 `agent:baerbel:whatsapp:group:120363...`）
- **对话历史**（一个 agent 看不到其他 agent 的回复）
- **工作区**（如有配置，沙盒也是分开的）
- **工具权限**（不同的 allow / deny 列表）
- **记忆 / 上下文**（IDENTITY.md、SOUL.md 等独立）
- **群上下文缓冲**（最近的群消息）按 peer 共享。被触发时所有广播 agent 看到的上下文是同一份。

> This allows each agent to have:
>
> * Different personalities
> * Different tool access (e.g., read-only vs. read-write)
> * Different models (e.g., opus vs. sonnet)
> * Different skills installed

这样每个 agent 可以有：

- 不同的人设
- 不同的工具权限（比如只读 vs 读写）
- 不同的模型（比如 opus vs sonnet）
- 各自安装的 skill

> ### Example: isolated sessions

### 示例：会话隔离

> In group `120363403215116621@g.us` with agents `["alfred", "baerbel"]`:

群 `120363403215116621@g.us` 里配了 agent `["alfred", "baerbel"]`：

> [标签页: Alfred's context]
>
> ```
> Session: agent:alfred:whatsapp:group:120363403215116621@g.us
> History: [user message, alfred's previous responses]
> Workspace: /Users/user/openclaw-alfred/
> Tools: read, write, exec
> ```

[标签页：Alfred 的上下文]

```
Session: agent:alfred:whatsapp:group:120363403215116621@g.us
History: [用户消息, alfred 之前的回复]
Workspace: /Users/user/openclaw-alfred/
Tools: read, write, exec
```

> [标签页: Bärbel's context]
>
> ```
> Session: agent:baerbel:whatsapp:group:120363403215116621@g.us
> History: [user message, baerbel's previous responses]
> Workspace: /Users/user/openclaw-baerbel/
> Tools: read only
> ```

[标签页：Bärbel 的上下文]

```
Session: agent:baerbel:whatsapp:group:120363403215116621@g.us
History: [用户消息, baerbel 之前的回复]
Workspace: /Users/user/openclaw-baerbel/
Tools: 仅 read
```

---

> ## Best practices

## 最佳实践

> [展开: 1. Keep agents focused]
>
> Design each agent with a single, clear responsibility:
>
> ```json
> {
>   "broadcast": {
>     "DEV_GROUP": ["formatter", "linter", "tester"]
>   }
> }
> ```
>
> ✅ **Good:** Each agent has one job. ❌ **Bad:** One generic "dev-helper" agent.

[展开：1. agent 要专注]

每个 agent 设计成单一、明确的职责：

```json
{
  "broadcast": {
    "DEV_GROUP": ["formatter", "linter", "tester"]
  }
}
```

✅ **好**：每个 agent 一个职责。 ❌ **不好**：一个万金油的 "dev-helper" agent。

> [展开: 2. Use descriptive names]
>
> Make it clear what each agent does:
>
> ```json
> {
>   "agents": {
>     "security-scanner": { "name": "Security Scanner" },
>     "code-formatter": { "name": "Code Formatter" },
>     "test-generator": { "name": "Test Generator" }
>   }
> }
> ```

[展开：2. 起描述性的名字]

让人一看就知道这个 agent 干嘛的：

```json
{
  "agents": {
    "security-scanner": { "name": "Security Scanner" },
    "code-formatter": { "name": "Code Formatter" },
    "test-generator": { "name": "Test Generator" }
  }
}
```

> [展开: 3. Configure different tool access]
>
> Give agents only the tools they need:
>
> ```json
> {
>   "agents": {
>     "reviewer": {
>       "tools": { "allow": ["read", "exec"] }
>     },
>     "fixer": {
>       "tools": { "allow": ["read", "write", "edit", "exec"] }
>     }
>   }
> }
> ```
>
> `reviewer` is read-only. `fixer` can read and write.

[展开：3. 给不同的工具权限]

每个 agent 只给它需要的工具：

```json
{
  "agents": {
    "reviewer": {
      "tools": { "allow": ["read", "exec"] }
    },
    "fixer": {
      "tools": { "allow": ["read", "write", "edit", "exec"] }
    }
  }
}
```

`reviewer` 只读；`fixer` 可读可写。

> [展开: 4. Monitor performance]
>
> With many agents, consider:
>
> * Using `"strategy": "parallel"` (default) for speed
> * Limiting broadcast groups to 5-10 agents
> * Using faster models for simpler agents

[展开：4. 关注性能]

agent 多的时候考虑：

- 用 `"strategy": "parallel"`（默认）提速
- 把广播组里的 agent 控制在 5-10 个
- 简单的 agent 用更快的模型

> [展开: 5. Handle failures gracefully]
>
> Agents fail independently. One agent's error doesn't block others:
>
> ```
> Message → [Agent A ✓, Agent B ✗ error, Agent C ✓]
> Result: Agent A and C respond, Agent B logs error
> ```

[展开：5. 优雅处理失败]

agent 之间互不影响。一个 agent 出错不会卡住其他的：

```
消息 → [Agent A ✓, Agent B ✗ 报错, Agent C ✓]
结果：Agent A 和 C 回复；Agent B 记错误日志
```

---

> ## Compatibility

## 兼容性

> ### Providers

### 通道支持

> Broadcast groups currently work with:
>
> * ✅ WhatsApp (implemented)
> * 🚧 Telegram (planned)
> * 🚧 Discord (planned)
> * 🚧 Slack (planned)

广播组目前支持：

- ✅ WhatsApp（已实现）
- 🚧 Telegram（计划中）
- 🚧 Discord（计划中）
- 🚧 Slack（计划中）

> ### Routing

### 路由

> Broadcast groups work alongside existing routing:

广播组和现有路由可以共存：

> ```json
> {
>   "bindings": [
>     {
>       "match": { "channel": "whatsapp", "peer": { "kind": "group", "id": "GROUP_A" } },
>       "agentId": "alfred"
>     }
>   ],
>   "broadcast": {
>     "GROUP_B": ["agent1", "agent2"]
>   }
> }
> ```

```json
{
  "bindings": [
    {
      "match": { "channel": "whatsapp", "peer": { "kind": "group", "id": "GROUP_A" } },
      "agentId": "alfred"
    }
  ],
  "broadcast": {
    "GROUP_B": ["agent1", "agent2"]
  }
}
```

> * `GROUP_A`: Only alfred responds (normal routing).
> * `GROUP_B`: agent1 AND agent2 respond (broadcast).

- `GROUP_A`：只有 alfred 回（普通路由）。
- `GROUP_B`：agent1 和 agent2 同时回（广播）。

> <Note>
>   **Precedence:** `broadcast` takes priority over `bindings`.
> </Note>

> **提示 — 优先级**：`broadcast` 比 `bindings` 优先。

---

> ## Troubleshooting

## 故障排查

> [展开: Agents not responding]
>
> **Check:**
>
> 1. Agent IDs exist in `agents.list`.
> 2. Peer ID format is correct (e.g., `120363403215116621@g.us`).
> 3. Agents are not in deny lists.
>
> **Debug:**
>
> ```bash
> tail -f ~/.openclaw/logs/gateway.log | grep broadcast
> ```

[展开：agent 没回应]

**检查**：

1. agent ID 在 `agents.list` 里存在。
2. peer ID 格式对（如 `120363403215116621@g.us`）。
3. agent 没被 deny 列表挡住。

**调试**：

```bash
tail -f ~/.openclaw/logs/gateway.log | grep broadcast
```

> [展开: Only one agent responding]
>
> **Cause:** Peer ID might be in `bindings` but not `broadcast`.
>
> **Fix:** Add to broadcast config or remove from bindings.

[展开：只有一个 agent 回了]

**原因**：peer ID 可能在 `bindings` 里、但没在 `broadcast` 里。

**修法**：要么加到 broadcast 配置里，要么从 bindings 里去掉。

> [展开: Performance issues]
>
> If slow with many agents:
>
> * Reduce number of agents per group.
> * Use lighter models (sonnet instead of opus).
> * Check sandbox startup time.

[展开：性能问题]

agent 多了变慢的话：

- 减少每个群里的 agent 数量。
- 换更轻量的模型（sonnet 替代 opus）。
- 看一下沙盒启动耗时。

---

> ## Examples

## 示例

> [展开: Example 1: Code review team]
>
> ```json
> {
>   "broadcast": {
>     "strategy": "parallel",
>     "120363403215116621@g.us": [
>       "code-formatter",
>       "security-scanner",
>       "test-coverage",
>       "docs-checker"
>     ]
>   },
>   "agents": {
>     "list": [
>       {
>         "id": "code-formatter",
>         "workspace": "~/agents/formatter",
>         "tools": { "allow": ["read", "write"] }
>       },
>       {
>         "id": "security-scanner",
>         "workspace": "~/agents/security",
>         "tools": { "allow": ["read", "exec"] }
>       },
>       {
>         "id": "test-coverage",
>         "workspace": "~/agents/testing",
>         "tools": { "allow": ["read", "exec"] }
>       },
>       { "id": "docs-checker", "workspace": "~/agents/docs", "tools": { "allow": ["read"] } }
>     ]
>   }
> }
> ```
>
> **User sends:** Code snippet.
>
> **Responses:**
>
> * code-formatter: "Fixed indentation and added type hints"
> * security-scanner: "⚠️ SQL injection vulnerability in line 12"
> * test-coverage: "Coverage is 45%, missing tests for error cases"
> * docs-checker: "Missing docstring for function `process_data`"

[展开：示例 1：代码审查团队]

```json
{
  "broadcast": {
    "strategy": "parallel",
    "120363403215116621@g.us": [
      "code-formatter",
      "security-scanner",
      "test-coverage",
      "docs-checker"
    ]
  },
  "agents": {
    "list": [
      {
        "id": "code-formatter",
        "workspace": "~/agents/formatter",
        "tools": { "allow": ["read", "write"] }
      },
      {
        "id": "security-scanner",
        "workspace": "~/agents/security",
        "tools": { "allow": ["read", "exec"] }
      },
      {
        "id": "test-coverage",
        "workspace": "~/agents/testing",
        "tools": { "allow": ["read", "exec"] }
      },
      { "id": "docs-checker", "workspace": "~/agents/docs", "tools": { "allow": ["read"] } }
    ]
  }
}
```

**用户发送**：一段代码。

**各 agent 回复**：

- code-formatter: "已修缩进、补充类型注解"
- security-scanner: "⚠️ 第 12 行有 SQL 注入漏洞"
- test-coverage: "覆盖率 45%，错误用例缺测试"
- docs-checker: "函数 `process_data` 缺 docstring"

> [展开: Example 2: Multi-language support]
>
> ```json
> {
>   "broadcast": {
>     "strategy": "sequential",
>     "+15555550123": ["detect-language", "translator-en", "translator-de"]
>   },
>   "agents": {
>     "list": [
>       { "id": "detect-language", "workspace": "~/agents/lang-detect" },
>       { "id": "translator-en", "workspace": "~/agents/translate-en" },
>       { "id": "translator-de", "workspace": "~/agents/translate-de" }
>     ]
>   }
> }
> ```

[展开：示例 2：多语言支持]

```json
{
  "broadcast": {
    "strategy": "sequential",
    "+15555550123": ["detect-language", "translator-en", "translator-de"]
  },
  "agents": {
    "list": [
      { "id": "detect-language", "workspace": "~/agents/lang-detect" },
      { "id": "translator-en", "workspace": "~/agents/translate-en" },
      { "id": "translator-de", "workspace": "~/agents/translate-de" }
    ]
  }
}
```

---

> ## API reference

## API 参考

> ### Config schema

### 配置类型

> ```typescript
> interface OpenClawConfig {
>   broadcast?: {
>     strategy?: "parallel" | "sequential";
>     [peerId: string]: string[];
>   };
> }
> ```

```typescript
interface OpenClawConfig {
  broadcast?: {
    strategy?: "parallel" | "sequential";
    [peerId: string]: string[];
  };
}
```

> ### Fields

### 字段

> <ParamField path="strategy" type="&#x22;parallel&#x22; | &#x22;sequential&#x22;" default="&#x22;parallel&#x22;">
>   How to process agents. `parallel` runs all agents simultaneously; `sequential` runs them in array order.
> </ParamField>

- `strategy`（类型 `"parallel" | "sequential"`，默认 `"parallel"`）：怎么调度 agent。`parallel` 让所有 agent 同时跑；`sequential` 按数组顺序依次跑。

> <ParamField path="[peerId]" type="string[]">
>   WhatsApp group JID, E.164 number, or other peer ID. Value is the array of agent IDs that should process messages.
> </ParamField>

- `[peerId]`（类型 `string[]`）：WhatsApp 群 JID、E.164 号码或其他 peer ID。值是该 peer 下要处理消息的 agent ID 列表。

---

> ## Limitations

## 限制

> 1. **Max agents:** No hard limit, but 10+ agents may be slow.
> 2. **Shared context:** Agents don't see each other's responses (by design).
> 3. **Message ordering:** Parallel responses may arrive in any order.
> 4. **Rate limits:** All agents count toward WhatsApp rate limits.

1. **agent 数量上限**：没有硬性上限，但超过 10 个会比较慢。
2. **共享上下文**：agent 之间互相看不到对方的回复（这是有意为之）。
3. **消息顺序**：并行模式下回复到达的顺序不固定。
4. **限速**：所有 agent 都算到 WhatsApp 限速里。

---

> ## Future enhancements

## 未来扩展

> Planned features:
>
> * [ ] Shared context mode (agents see each other's responses)
> * [ ] Agent coordination (agents can signal each other)
> * [ ] Dynamic agent selection (choose agents based on message content)
> * [ ] Agent priorities (some agents respond before others)

计划中的功能：

- [ ] 共享上下文模式（agent 之间能看到彼此的回复）
- [ ] agent 协调（agent 之间可以互发信号）
- [ ] 动态 agent 选择（按消息内容挑 agent）
- [ ] agent 优先级（部分 agent 先回）

---

> ## Related

## 相关

> * [Channel routing](/channels/channel-routing)
> * [Groups](/channels/groups)
> * [Multi-agent sandbox tools](/tools/multi-agent-sandbox-tools)
> * [Pairing](/channels/pairing)
> * [Session management](/concepts/session)

- [通道路由](/channels/channel-routing)
- [群组](/channels/groups)
- [多 agent 沙盒工具](/tools/multi-agent-sandbox-tools)
- [配对](/channels/pairing)
- [会话管理](/concepts/session)
