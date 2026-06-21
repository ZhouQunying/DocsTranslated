# WebChat

Native chat interface 用于 gateway,无 embedded browser 或本地 static server。macOS/iOS SwiftUI chat UI 直接与 Gateway WebSocket 通信。

> **类比:iMessage + 多 provider 后端。** iMessage 是 Apple 的原生 chat UI,消息经 Apple servers 路由到 recipient。WebChat 类似: native UI (SwiftUI) 直接与 Gateway WebSocket 通信,消息经 Gateway 路由到 model provider (OpenAI、Anthropic 等)。区别: iMessage 是 P2P (Apple servers relay),WebChat 是 client-server (Gateway 是 server,拥有 sessions、state)。
>
> **架构要点:** Native SwiftUI UI (macOS/iOS) 直连 Gateway WebSocket,无 embedded browser;共享 sessions 和 routing rules 与其他 channels;确定性 routing: 回复返回 WebChat;经 `chat.history`、`chat.send`、`chat.inject` commands;history 有 bounds (stability),Gateway 可能 truncate 长字段或 omit 重 metadata,oversized 条目显示 `[chat.history omitted: message too large]`,Control UI 可经 `chat.message.get` 获取完整条目;history 跟随活跃 transcript branch (abandoned rewrites 不显示);compaction entries 用显式 dividers 渲染并链接到 checkpoint controls;Control UI 跟踪 `sessionId` 用于 session continuity 跨 reconnect;重复 in-flight submits 在生成新 run IDs 前合并;bootstrap files 经 system prompt Project Context 提供,不是 user messages;display normalization 剥离 runtime context、delivery tags、tool-call XML、control tokens;只含 `NO_REPLY`/`no_reply` 的消息被 omit;reasoning-flagged payloads 从可见内容排除;`chat.inject` 追加 assistant notes 无 agent runs;aborted runs 可能保持 partial output 可见;history 从 gateway 获取 (无本地 file watching);gateway 不可达 = read-only mode。

## Quick Start

1. 启动 gateway
2. 打开 WebChat UI (macOS/iOS app) 或 Control UI chat tab
3. 配置有效 gateway auth (shared-secret 默认,即使在 loopback)

## Transcript 和 Delivery Model

两条数据路径:
1. **Session JSONL file** — 持久 model/runtime transcript,由 embedded OpenClaw runtime 写入
2. **Gateway ReplyPayload events** — 实时 delivery projection,带 normalization 用于显示

## Control UI Agents Tools Panel

两个视图:
- **Available Right Now** — 用 `tools.effective(sessionKey=...)` 获取当前 session 清单
- **Tool Configuration** — 用 `tools.catalog` 获取 profiles 和 overrides

Runtime 可用性是 session-scoped,切换 sessions 时可能变化。

## Remote Use

Remote mode 经 SSH/Tailscale tunnel gateway WebSocket。无需独立 WebChat server。

## Configuration Reference

WebChat 无持久化 config section。Legacy `channels.webchat` 和 `gateway.webchat` config 已废弃;用 `openclaw doctor --fix` 移除。

**相关全局选项**:
- `gateway.port`、`gateway.bind` — WebSocket host/port
- `gateway.auth.mode`、`gateway.auth.token`、`gateway.auth.password` — auth settings
- `gateway.auth.allowTailscale` — Tailscale Serve identity headers
- `gateway.auth.mode: "trusted-proxy"` — reverse-proxy auth
- `gateway.remote.url`、`gateway.remote.token`、`gateway.remote.password` — remote target
- `session.*` — session storage 默认值
