# Session management

> OpenClaw organizes conversations into **sessions**. Each message is routed to a session based on where it came from -- DMs, group chats, cron jobs, etc.

OpenClaw 把对话组织成**会话**。每条消息按来源路由到一个会话 —— 私聊、群聊、cron 任务等等。

---

> ## How messages are routed

## 消息怎么路由

> | Source          | Behavior                  |
> | --------------- | ------------------------- |
> | Direct messages | Shared session by default |
> | Group chats     | Isolated per group        |
> | Rooms/channels  | Isolated per room         |
> | Cron jobs       | Fresh session per run     |
> | Webhooks        | Isolated per hook         |

| 来源              | 行为                              |
| ----------------- | --------------------------------- |
| 私聊              | 默认共用一个会话                  |
| 群聊              | 按群隔离                          |
| 房间 / 频道       | 按房间隔离                        |
| cron 任务         | 每次运行一个新会话                |
| webhook           | 按钩子隔离                      |

---

> ## DM isolation

## 私聊隔离

> By default, all DMs share one session for continuity. This is fine for single-user setups.

默认所有私聊共用一个会话以保持连贯。单用户部署没问题。

> <Warning>
>   If multiple people can message your agent, enable DM isolation. Without it, all users share the same conversation context -- Alice's private messages would be visible to Bob.
> </Warning>

> **警告**：多人都能给你的 agent 发消息时，启用私聊隔离。不开的话所有用户共享同一份对话上下文 ——Alice 的私聊会被 Bob 看到。

> **The fix:**
>
> ```json5
> {
>   session: {
>     dmScope: "per-channel-peer", // isolate by channel + sender
>   },
> }
> ```

**修法**：

```json5
{
  session: {
    dmScope: "per-channel-peer", // 按通道 + 发件人隔离
  },
}
```

> Other options:
>
> * `main` (default) -- all DMs share one session.
> * `per-peer` -- isolate by sender (across channels).
> * `per-channel-peer` -- isolate by channel + sender (recommended).
> * `per-account-channel-peer` -- isolate by account + channel + sender.

其他选项：

- `main`（默认）：所有私聊共用一个会话。
- `per-peer`：按发件人隔离（跨通道）。
- `per-channel-peer`：按通道 + 发件人隔离（推荐）。
- `per-account-channel-peer`：按账号 + 通道 + 发件人隔离。

> <Tip>
>   If the same person contacts you from multiple channels, use `session.identityLinks` to link their identities so they share one session.
> </Tip>

> **小贴士**：同一个人从多个通道联系你时，用 `session.identityLinks` 把他的身份链起来，让它们共享一个会话。

> ### Dock linked channels

### 切换链接的通道（dock）

> Dock commands let a user move the current direct-chat session's reply route to another linked channel without starting a new session. See [Channel docking](/concepts/channel-docking) for examples, config, and troubleshooting.

dock 命令让用户把当前私聊会话的回复路由切到另一个链接的通道上，不开新会话。例子、配置和排查见 [通道 dock](/concepts/channel-docking)。

> Verify your setup with `openclaw security audit`.

用 `openclaw security audit` 验证配置。

---

> ## Session lifecycle

## 会话生命周期

> Sessions are reused until they expire:
>
> * **Daily reset** (default) -- new session at 4:00 AM local time on the gateway host. Daily freshness is based on when the current `sessionId` started, not on later metadata writes.
> * **Idle reset** (optional) -- new session after a period of inactivity. Set `session.reset.idleMinutes`. Idle freshness is based on the last real user/channel interaction, so heartbeat, cron, and exec system events do not keep the session alive.
> * **Manual reset** -- type `/new` or `/reset` in chat. `/new <model>` also switches the model.

会话会被复用，直到过期：

- **每日重置**（默认）：Gateway 宿主机本地时间凌晨 4:00 开新会话。每日新鲜度基于当前 `sessionId` 开始的时间，不基于之后的元数据写入。
- **空闲重置**（可选）：一段时间没活动就开新会话。设 `session.reset.idleMinutes`。空闲新鲜度基于最后一次真实的用户 / 通道交互 —— 心跳、cron、exec 这些系统事件**不**会让会话保持活跃。
- **手动重置**：在聊天里发 `/new` 或 `/reset`。`/new <model>` 还会切模型。

> When both daily and idle resets are configured, whichever expires first wins. Heartbeat, cron, exec, and other system-event turns may write session metadata, but those writes do not extend daily or idle reset freshness. When a reset rolls the session, queued system-event notices for the old session are discarded so stale background updates are not prepended to the first prompt in the new session.

每日和空闲重置同时配置时，先到期的胜出。心跳、cron、exec 等系统事件轮次可能写会话元数据，但这些写不延长每日或空闲重置的新鲜度。重置滚动会话时，旧会话排队的系统事件提示会被丢弃，避免过期的后台更新被前置到新会话的第一条 prompt 里。

> Sessions with an active provider-owned CLI session are not cut by the implicit daily default. Use `/reset` or configure `session.reset` explicitly when those sessions should expire on a timer.

带活跃 provider 持有 CLI 会话的会话不会被隐式的每日默认切掉。需要这些会话按定时过期时，用 `/reset` 或显式配 `session.reset`。

---

> ## Where state lives

## 状态在哪

> All session state is owned by the **gateway**. UI clients query the gateway for session data.

所有会话状态由 **Gateway** 持有。UI 客户端从 Gateway 查会话数据。

> * **Store:** `~/.openclaw/agents/<agentId>/sessions/sessions.json`
> * **Transcripts:** `~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`

- **存储**：`~/.openclaw/agents/<agentId>/sessions/sessions.json`
- **对话记录**：`~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`

> `sessions.json` keeps separate lifecycle timestamps:
>
> * `sessionStartedAt`: when the current `sessionId` began; daily reset uses this.
> * `lastInteractionAt`: last user/channel interaction that extends idle lifetime.
> * `updatedAt`: last store-row mutation; useful for listing and pruning, but not authoritative for daily/idle reset freshness.

`sessions.json` 维护几个不同的生命周期时间戳：

- `sessionStartedAt`：当前 `sessionId` 开始的时间；每日重置看这个。
- `lastInteractionAt`：最后一次延长空闲生命周期的用户 / 通道交互。
- `updatedAt`：存储行最后一次改动；用于列表和裁剪，但对每日 / 空闲重置新鲜度不是权威。

> Older rows without `sessionStartedAt` are resolved from the transcript JSONL session header when available. If an older row also lacks `lastInteractionAt`, idle freshness falls back to that session start time, not to later bookkeeping writes.

没 `sessionStartedAt` 的旧行可用时从对话记录 JSONL 的会话头解出。旧行也没 `lastInteractionAt` 时，空闲新鲜度回退到会话开始时间，不回退到后来的记账写入。

---

> ## Session maintenance

## 会话维护

> OpenClaw automatically bounds session storage over time. By default, it runs in `warn` mode (reports what would be cleaned). Set `session.maintenance.mode` to `"enforce"` for automatic cleanup:

OpenClaw 会随时间限制会话存储大小。默认跑在 `warn` 模式（报告会清掉哪些）。要自动清理就把 `session.maintenance.mode` 设成 `"enforce"`：

> ```json5
> {
>   session: {
>     maintenance: {
>       mode: "enforce",
>       pruneAfter: "30d",
>       maxEntries: 500,
>     },
>   },
> }
> ```

```json5
{
  session: {
    maintenance: {
      mode: "enforce",
      pruneAfter: "30d",
      maxEntries: 500,
    },
  },
}
```

> For production-sized `maxEntries` limits, Gateway runtime writes use a small high-water buffer and clean back down to the configured cap in batches. Session store reads do not prune or cap entries during Gateway startup. This avoids running full store cleanup on every startup or isolated cron session. `openclaw sessions cleanup --enforce` applies the cap immediately.

生产规模的 `maxEntries` 上限下，Gateway 运行时写入用一个小的高水位缓冲，分批清回到配置的上限。会话存储读取在 Gateway 启动时不裁剪或封顶条目。这样避免每次启动或隔离的 cron 会话都跑完整存储清理。`openclaw sessions cleanup --enforce` 立刻应用上限。

> Maintenance preserves durable external conversation pointers, including group sessions and thread-scoped chat sessions, while still allowing synthetic cron, hook, heartbeat, ACP, and sub-agent entries to age out.

维护会保留长期的外部对话指针 —— 包括群会话和按 thread 作用域的聊天会话 —— 同时让 cron、钩子、心跳、ACP、sub-agent 这些合成条目随时间淘汰。

> If you previously used direct-message isolation and later returned `session.dmScope` to `main`, preview stale peer-keyed DM rows with `openclaw sessions cleanup --dry-run --fix-dm-scope`. Applying the same flag retires those old direct-DM rows and keeps their transcripts as deleted archives.

如果之前用过私聊隔离，后来又把 `session.dmScope` 改回 `main`，用 `openclaw sessions cleanup --dry-run --fix-dm-scope` 预览过期的、按发件人 key 的私聊行。带同样的开关执行会让这些旧私聊行退役，把它们的对话记录留作已删除归档。

> Preview with `openclaw sessions cleanup --dry-run`.

用 `openclaw sessions cleanup --dry-run` 预览。

---

> ## Inspecting sessions

## 查看会话

> * `openclaw status` -- session store path and recent activity.
> * `openclaw sessions --json` -- all sessions (filter with `--active <minutes>`).
> * `/status` in chat -- context usage, model, and toggles.
> * `/context list` -- what is in the system prompt.

- `openclaw status`：会话存储路径和近期活动。
- `openclaw sessions --json`：所有会话（用 `--active <分钟>` 过滤）。
- 在聊天里发 `/status`：上下文用量、模型、开关。
- `/context list`：系统提示词里有什么。

---

> ## Further reading

## 进一步阅读

> * [Session Pruning](/concepts/session-pruning) -- trimming tool results
> * [Compaction](/concepts/compaction) -- summarizing long conversations
> * [Session Tools](/concepts/session-tool) -- agent tools for cross-session work
> * [Session Management Deep Dive](/reference/session-management-compaction) -- store schema, transcripts, send policy, origin metadata, and advanced config
> * [Multi-Agent](/concepts/multi-agent) — routing and session isolation across agents
> * [Background Tasks](/automation/tasks) — how detached work creates task records with session references
> * [Channel Routing](/channels/channel-routing) — how inbound messages are routed to sessions

- [会话裁剪](/concepts/session-pruning)：裁掉工具结果。
- [压缩](/concepts/compaction)：概括长对话。
- [会话工具](/concepts/session-tool)：跨会话工作的 agent 工具。
- [会话管理深入](/reference/session-management-compaction)：存储 schema、对话记录、发送策略、来源元数据、进阶配置。
- [多 Agent](/concepts/multi-agent)：跨 agent 的路由和会话隔离。
- [后台任务](/automation/tasks)：脱离主 agent 的工作怎么建带会话引用的任务记录。
- [通道路由](/channels/channel-routing)：接收消息怎么路由到会话。

---

> ## Related

## 相关

> * [Session pruning](/concepts/session-pruning)
> * [Session tools](/concepts/session-tool)
> * [Command queue](/concepts/queue)

- [会话裁剪](/concepts/session-pruning)
- [会话工具](/concepts/session-tool)
- [命令队列](/concepts/queue)
