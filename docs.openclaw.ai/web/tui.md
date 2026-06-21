# TUI

Terminal UI (TUI): 连接到 Gateway 或在 embedded mode 本地运行。

> **类比:tmux + Slack CLI。** tmux 是 terminal multiplexer,让你在终端管理多个 sessions;Slack CLI (`slackcli`) 让你在终端发送 Slack 消息。TUI 类似: terminal 里与 Gateway 交互 (chat、agents、sessions、tools),类似 Slack CLI 但更强大 (支持 tool cards、model picker、agent picker、session picker)。区别: tmux 是 session multiplexer,TUI 是 agent/session multiplexer。
>
> **架构要点:** Gateway mode (`openclaw tui`) 连接 Gateway WebSocket,local mode (`openclaw chat` 或 `openclaw tui --local`) 直连 embedded agent runtime;agents 是唯一 slugs (如 `main`、`research`),sessions 属于当前 agent,session keys 存储为 `agent:<agentId>:<sessionKey>`;session scope: `per-sender` (默认,每个 agent 多个 sessions) 或 `global` (TUI 始终用 `global` session);footer 显示: agent + session + model + goal state + think/fast/verbose/trace/reasoning + token counts + deliver;消息发送到 Gateway,delivery 到 providers 默认关闭 (TUI 是 internal source surface 如 WebChat,不是通用 outbound channel);`!` 前缀运行本地 shell 命令 (每 session 提示一次允许);keyboard shortcuts: Enter 发送、Esc abort、Ctrl+C 清输入 (两次退出)、Ctrl+D 退出、Ctrl+L model picker、Ctrl+G agent picker、Ctrl+P session picker;local mode 用于 config repair (embedded agent 检查 config、对比 docs、建议修复);tool calls 显示为 cards (args + results),Ctrl+O toggle collapse/expand;history 默认加载 200 messages,streaming responses 原地更新;TUI 注册为 `mode: "tui"`,reconnects 显示 system message;`--url` 时不复用 config 或环境凭证,必须显式 `--token` 或 `--password`。

## Quick Start

### Gateway Mode

```bash
openclaw gateway  # 启动 Gateway
openclaw tui      # 打开 TUI
```

Remote Gateway:
```bash
openclaw tui --url ws://<host>:<port> --token <gateway-token>
```

### Local Mode

```bash
openclaw chat  # 或 openclaw tui --local
```

## Mental Model: Agents + Sessions

- Agents 是唯一 slugs (如 `main`、`research`)
- Sessions 属于当前 agent
- Session keys 存储为 `agent:<agentId>:<sessionKey>`
- `/session main` 展开为 `agent:<currentAgent>:main`
- Session 作用域: `per-sender` (默认) 或 `global`

## Sending + Delivery

- 消息发送到 Gateway;delivery 到 providers 默认关闭
- Turn delivery on: `/deliver on` 或 Settings panel 或 `openclaw tui --deliver`

## Keyboard Shortcuts

- Enter: 发送消息
- Esc: abort 活跃 run
- Ctrl+C: 清输入 (两次退出)
- Ctrl+D: 退出
- Ctrl+L: model picker
- Ctrl+G: agent picker
- Ctrl+P: session picker
- Ctrl+O: toggle tool output 展开
- Ctrl+T: toggle thinking 可见性 (重载 history)

## Slash Commands

核心: `/help`、`/status`、`/agent <id>`、`/session <key>`、`/model <provider/model>`

Session controls: `/think`、`/fast`、`/verbose`、`/trace`、`/reasoning`、`/usage`、`/goal`、`/elevated`、`/activation`、`/deliver`

Session lifecycle: `/new`、`/reset`、`/abort`、`/settings`、`/exit`

Local mode only: `/auth [provider]`

## Local Shell Commands

`!` 前缀在 TUI host 运行本地 shell 命令。每 session 提示一次允许。

## Repair Configs from Local TUI

Local mode 用于 config repair (embedded agent 检查 config、对比 docs、建议修复):

```bash
openclaw chat
# 然后问 agent:
# Compare my gateway auth config with the docs and suggest the smallest fix.
# 用本地 shell 命令:
# !openclaw config file
# !openclaw docs gateway auth token secretref
# !openclaw config validate
# !openclaw doctor
```

## Options

- `--local`: 对本地 embedded agent runtime 运行
- `--url <url>`: Gateway WebSocket URL
- `--token <token>`: Gateway token
- `--password <password>`: Gateway password
- `--session <key>`: Session key
- `--deliver`: Delivery assistant replies 到 provider
- `--thinking <level>`: Override thinking level
- `--message <text>`: 连接后发送初始消息
- `--timeout-ms <ms>`: Agent timeout
- `--history-limit <n>`: History 条目加载数 (默认 200)
