# CLI Backends

## 架构精读

> 跳过不影响阅读翻译正文。

### 安全网设计——为什么 CLI 后端只是 text-only 降级通道？

CLI 后端作为 API provider 的降级方案，仅提供文本输入输出能力，不支持直接工具调用注入。这种设计是刻意为之的保守策略：当主 API 提供商宕机或触发限流时，系统自动回退到本地 CLI 继续工作，但功能有所缩减。CLI 后端就像数据库连接池中的备用节点。主节点不可用时自动接管，但只提供基础文本交互，不承载完整工具调用能力。这是安全网，不是主执行路径。

### BundleMCP 桥接——为什么需要 loopback MCP 服务器？

CLI 后端无法直接接收 OpenClaw 工具调用，但启用 `bundleMcp: true` 后可以启动 loopback HTTP MCP 服务器，将 gateway 工具暴露给 CLI 进程。这个架构类似 service mesh 中的 sidecar 代理——为每个 CLI 进程创建一个独立的 MCP 运行时，使用独立的会话级令牌认证，空闲超时后自动回收。只有启用了 `bundleMcp` 的后端才能看到 gateway 工具，其他后端只能进行纯文本交互。

### Fallback prelude——为什么回退时需要上下文注入？

当 `claude-cli` 失败后回退到非 CLI 候选时，新 provider 的会话完全没有上下文——因为 OpenClaw 自己的会话记录在 CLI 运行时是空的。如果不注入上下文，回退 provider 将从零开始。为了解决这个冷启动问题，OpenClaw 从 Claude Code 的本地 JSONL 记录文件中提取上下文摘要。优先使用最近的压缩总结，追加近期对话轮次，丢弃已被总结代表的早期轮次。

### Native compaction 所有权——为什么要声明 `ownsNativeCompaction`？

Claude Code 等后端在内部管理自己的会话记录压缩。如果 OpenClaw 的安全压缩器同时运行，两个独立的压缩机制可能产生冲突——导致数据丢失或不一致。通过声明 `ownsNativeCompaction: true`，后端告诉 OpenClaw："我自己处理压缩，你不要干预。"OpenClaw 的压缩路径返回空操作，避免了双重压缩问题。这要求后端能可靠地将记录控制在上下文窗口范围内，并支持持久化可恢复会话。

### 会话连续性——为什么依赖 CLI 的会话 id？

CLI 后端通过会话标识符维持对话连续性：每次调用时传递标识符，CLI 根据标识符在服务端找到对应的对话上下文。OpenClaw 将这些标识符持久化存储，后续交互时复用。Gateway 重启或进程空闲退出后，可以从存储的标识符恢复会话。但如果认证身份发生变化（如切换账户），旧的会话上下文可能与新身份不匹配，因此会丢弃存储的标识符。OAuth 令牌轮换不改变身份，所以不影响会话连续性。

---

CLI Backends

CLI 后端

OpenClaw 可以运行本地 AI CLI 作为纯文本降级方案。当主 API 提供商宕机或触发限流时，系统自动回退到本地 CLI 继续工作，但功能有所缩减。这是安全网，不是主执行路径。

## 配置

Configuration

`agents.defaults.cliBackends`,key 是 provider id（形成 model ref 的左半部分 `<provider>/<model>`）：

The key in `agents.defaults.cliBackends` is the provider id (forming the left half of the model ref `<provider>/<model>`):

```json5
{
  agents: {
    defaults: {
      cliBackends: {
        "claude-cli": {
          command: "/opt/homebrew/bin/claude"
        }
      }
    }
  }
}
```

Bundled Anthropic 插件注册了默认 `claude-cli` backend，零配置即可用：

The bundled Anthropic plugin registers a default `claude-cli` backend, available with zero configuration:

```bash
openclaw agent --agent main --message "hi" --model claude-cli/claude-sonnet-4-6
```

Gateway 在 launchd/systemd 下运行时 PATH 受限，需要显式指定 command 绝对路径。

When the Gateway runs under launchd/systemd, the PATH is restricted, so you must explicitly specify the absolute path for the command.

## 备用方案配置

Fallback Configuration

加入备用列表，primary 失败时自动尝试：

Add to the fallback list to automatically try when the primary fails:

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-6",
        fallbacks: ["claude-cli/claude-sonnet-4-6"]
      },
      models: {
        "anthropic/claude-opus-4-6": { alias: "Opus" },
        "claude-cli/claude-sonnet-4-6": {}
      }
    }
  }
}
```

使用 `agents.defaults.models` 作为 allowlist 时，CLI backend models 也必须包含在内。

When using `agents.defaults.models` as an allowlist, CLI backend models must also be included.

## 执行流程

Execution Flow

1. 基于 provider prefix 选择 backend
2. 构建 system prompt（OpenClaw prompt + workspace context）
3. CLI 执行，带 session id（如果支持）
4. 输出解析（JSON/JSONL/text）
5. Session id 持久化，后续复用

1. Select backend based on provider prefix
2. Build system prompt (OpenClaw prompt + workspace context)
3. Execute CLI with session id (if supported)
4. Parse output (JSON/JSONL/text)
5. Persist session id for reuse in follow-up calls

## 内置 backend

Bundled Backends

### claude-cli (Anthropic)

默认：`command: "claude"`, `output: "jsonl"`, `input: "stdin"`, `sessionMode: "always"`, `liveSession: "claude-stdio"`。

Defaults: `command: "claude"`, `output: "jsonl"`, `input: "stdin"`, `sessionMode: "always"`, `liveSession: "claude-stdio"`.

前置条件：Claude Code 必须在同一主机登录（`claude auth login`）。

Prerequisite: Claude Code must be logged in on the same host (`claude auth login`).

**Skill 解析**：优先用 Claude Code 的 native skill resolver。当 skills snapshot 包含至少一个 materialized path 的 skill 时，通过 `--plugin-dir` 传递临时 plugin，从 system prompt 省略重复 skills catalog。

**Skill resolution**: Prefers Claude Code's native skill resolver. When the skills snapshot contains at least one skill with a materialized path, a temporary plugin is passed via `--plugin-dir`, and the duplicate skills catalog is omitted from the system prompt.

**权限映射**：OpenClaw exec policy 映射到 Claude permission mode。YOLO mode（`tools.exec.security: "full"` + `tools.exec.ask: "off"`）→ `--permission-mode bypassPermissions`。Restrictive policy → `--permission-mode default`。

**Permission mapping**: OpenClaw exec policy maps to Claude permission mode. YOLO mode (`tools.exec.security: "full"` + `tools.exec.ask: "off"`) → `--permission-mode bypassPermissions`. Restrictive policy → `--permission-mode default`.

**Effort 映射**：`/think` levels 映射到 Claude `--effort`：minimal/low → low, adaptive/medium → medium, high/xhigh/max → direct。

**Effort mapping**: `/think` levels map to Claude `--effort`: minimal/low → low, adaptive/medium → medium, high/xhigh/max → direct.

**Native compaction**：Claude Code 内部压缩自己的 transcript，声明 `ownsNativeCompaction: true`。OpenClaw 从 compaction path 返回 no-op。旧的 `contextTokens: 1_000_000` workaround 不再需要。

**Native compaction**: Claude Code internally compacts its own transcript, declaring `ownsNativeCompaction: true`. OpenClaw returns a no-op from the compaction path. The old `contextTokens: 1_000_000` workaround is no longer needed.

**活跃会话**：每个 OpenClaw session 保持一个 Claude stdio process。Gateway 重启或 idle process 退出时，从存储 session id 恢复。Stored session ids 在恢复前验证可读 project transcripts，不可读的条目以 `reason=transcript-missing` 清除。Bounded JSONL output guards 默认 8 MiB 和 20,000 lines per turn，可通过 `reliability.outputLimits` 提高（上限 64 MiB / 100,000 lines）。

**Live sessions**: Each OpenClaw session maintains one Claude stdio process. When the Gateway restarts or an idle process exits, it recovers from the stored session id. Stored session ids are validated for readable project transcripts before recovery; unreadable entries are cleared with `reason=transcript-missing`. Bounded JSONL output guards default to 8 MiB and 20,000 lines per turn, configurable via `reliability.outputLimits` (clamped to 64 MiB / 100,000 lines).

### google-gemini-cli (Google)

默认：`command: "gemini"`, `output: "jsonl"`, `jsonlDialect: "gemini-stream-json"`, `imageArg: "@"`, `imagePathScope: "workspace"`, `sessionMode: "existing"`。

Defaults: `command: "gemini"`, `output: "jsonl"`, `jsonlDialect: "gemini-stream-json"`, `imageArg: "@"`, `imagePathScope: "workspace"`, `sessionMode: "existing"`.

前置条件：`brew install gemini-cli` 或 `npm install -g @google/gemini-cli`。

Prerequisite: `brew install gemini-cli` or `npm install -g @google/gemini-cli`.

`stream-json` parser 读取 assistant message events、tool events、final result usage、fatal error events。Usage fallback 到 `stats`，`stats.cached` 归一化为 `cacheRead`，input tokens 从 `stats.input_tokens - stats.cached` 派生。

The `stream-json` parser reads assistant message events, tool events, final result usage, and fatal error events. Usage falls back to `stats`, `stats.cached` is normalized to `cacheRead`, and input tokens are derived from `stats.input_tokens - stats.cached`.

## 会话管理

Session Management

三种 session modes：

Three session modes:

| Mode | Behavior |
|---|---|
| `always` | 每次调用发送 session id（无则生成 UUID） / Sends session id on every call (generates UUID if none) |
| `existing` | 仅在有存储 session id 时发送 / Only sends when a stored session id exists |
| `none` | 不发送 session id / Does not send session id |

会话连续性规则：

Session continuity rules:

- Stored CLI sessions 是 provider-owned，隐式日重置不切断；`/reset` 和 `session.reset` 仍然清除
- Auth identity 变更（profile id、static key、token、OAuth account identity）时丢弃 stored session
- OAuth token rotation **不**切断 stored session
- `serialize: true` 保持同通道运行有序

- Stored CLI sessions are provider-owned; implicit daily resets do not sever them; `/reset` and `session.reset` still clear them
- Auth identity changes (profile id, static key, token, OAuth account identity) discard stored sessions
- OAuth token rotation does **not** sever stored sessions
- `serialize: true` keeps same-channel runs ordered

### Reseed 行为

Reseed Behavior

新 CLI session 从 OpenClaw compaction summary + post-compaction tail reseed。`reseedFromRawTranscriptWhenUncompacted: true` 可恢复安全 invalidations（missing transcripts、system prompt 变更、session-expired retries）。Auth profile 或 credential-epoch 变更永不触发 raw transcript reseed。

New CLI sessions reseed from the OpenClaw compaction summary + post-compaction tail. `reseedFromRawTranscriptWhenUncompacted: true` enables recovery from safe invalidations (missing transcripts, system prompt changes, session-expired retries). Auth profile or credential-epoch changes never trigger raw transcript reseed.

Reseed history cap 默认 12,288 字符（~3,000 tokens）。Claude CLI 用更大的 cap（基于 resolved context tier）。

Reseed history cap defaults to 12,288 characters (~3,000 tokens). Claude CLI uses a larger cap (based on resolved context tier).

## Fallback prelude

`claude-cli` 失败后 fallback 到非 CLI 候选时，OpenClaw 从 Claude Code 的本地 JSONL transcript（`~/.claude/projects/`）提取 context prelude：

When `claude-cli` fails and falls back to a non-CLI candidate, OpenClaw extracts a context prelude from Claude Code's local JSONL transcript (`~/.claude/projects/`):

- 优先使用 latest `/compact` summary 或 `compact_boundary` marker
- Append 最近的 post-boundary turns（character budget 内）
- Pre-boundary turns 丢弃（summary 已代表）
- Tool blocks 合并为 compact hints：`(tool call: name)` / `(tool result: …)`
- Same-provider `claude-cli` → `claude-cli` fallback 用 Claude 的 `--resume`，跳过 prelude

- Prefers the latest `/compact` summary or `compact_boundary` marker
- Appends recent post-boundary turns (within character budget)
- Pre-boundary turns are discarded (already represented by summary)
- Tool blocks are merged into compact hints: `(tool call: name)` / `(tool result: …)`
- Same-provider `claude-cli` → `claude-cli` fallback uses Claude's `--resume`, skipping the prelude

没有这个上下文 prelude，fallback provider 会 cold start，因为 OpenClaw 自己的 session transcript 对 `claude-cli` runs 是空的。

Without this context prelude, the fallback provider would cold start because OpenClaw's own session transcript is empty for `claude-cli` runs.

## BundleMCP overlays

CLI backend 不直接接收 OpenClaw tool calls。`bundleMcp: true` 启用 MCP config overlay：

CLI backends do not directly receive OpenClaw tool calls. `bundleMcp: true` enables an MCP config overlay:

1. 启动 loopback HTTP MCP server，暴露 gateway tools 给 CLI process
2. Per-session token 认证（`OPENCLAW_MCP_TOKEN`）
3. Tool access 限定到当前 session、account、channel context
4. 加载 enabled bundle-MCP servers
5. 合并已有 backend MCP config
6. 用 backend-owned integration mode 重写 launch config

1. Starts a loopback HTTP MCP server, exposing gateway tools to the CLI process
2. Per-session token authentication (`OPENCLAW_MCP_TOKEN`)
3. Tool access scoped to the current session, account, and channel context
4. Loads enabled bundle-MCP servers
5. Merges existing backend MCP config
6. Rewrites launch config with backend-owned integration mode

`claude-cli` 生成 strict MCP config file，`google-gemini-cli` 生成 Gemini system settings file。

`claude-cli` generates a strict MCP config file; `google-gemini-cli` generates a Gemini system settings file.

Session-scoped MCP runtimes 缓存复用，`mcp.sessionIdleTtlMs`（默认 10 分钟）后回收。One-shot runs（auth probes、slug generation、active-memory recall）在 run 结束时请求清理。

Session-scoped MCP runtimes are cached for reuse and reclaimed after `mcp.sessionIdleTtlMs` (default 10 minutes). One-shot runs (auth probes, slug generation, active-memory recall) request cleanup at the end of the run.

## Native compaction 所有权

Native Compaction Ownership

声明 `ownsNativeCompaction: true` 的 backend 防止 OpenClaw safeguard summarizer 与其自己的 compaction 冲突。要求：可靠 bound transcript near context window，持久化可恢复 session（`--resume` / `--session-id`）。Matching `agentHarnessId` sessions 仍路由到 harness endpoint。

Backends declaring `ownsNativeCompaction: true` prevent conflicts between OpenClaw's safeguard summarizer and their own compaction mechanism. Requirements: reliably bound transcript near the context window, persistent recoverable sessions (`--resume` / `--session-id`). Matching `agentHarnessId` sessions are still routed to the harness endpoint.

## 限制

Limitations

- **没有直接 tool calls**：只有 `bundleMcp: true` backends 看到 gateway tools
- **Streaming 变化**：有些 stream JSONL，有些 buffer 到退出
- **Structured outputs** 完全依赖 CLI 的 JSON 格式

- **No direct tool calls**: Only `bundleMcp: true` backends see gateway tools
- **Streaming varies**: Some stream JSONL, others buffer until exit
- **Structured outputs** rely entirely on the CLI's JSON format
