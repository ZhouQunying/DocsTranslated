# CLI Backends

> **类比:数据库连接池的 fallback 节点。** 主数据库(API provider)宕机或限流时,自动切换到备用数据库(本地 CLI)。但备用节点功能有限——没有完整 tool 支持,只有 text-only fallback。这是一个保守的安全网设计,不是主执行路径。
>
> **类比:MCP bridge 作为 sidecar proxy。** CLI backend 不能直接接收 OpenClaw tool calls,但 `bundleMcp: true` 的 backend 可以通过 loopback MCP bridge 访问 gateway tools——就像 service mesh 里 sidecar proxy 把外部服务接入 mesh。每个 session 有独立的 MCP runtime,per-session token 认证,idle 后自动回收。
>
> **架构要点:** text-only fallback,不是主执行路径;OpenClaw 工具不直接注入,只有 `bundleMcp: true` 的 backend 通过 MCP bridge 看到 gateway tools;session 连续性通过 CLI 的 session id 维持;fallback prelude 从 Claude Code 的本地 JSONL transcript 提取 context 避免 cold start;`ownsNativeCompaction` 防止 OpenClaw safeguard summarizer 与 backend 自己的 compaction 冲突。

## 配置

`agents.defaults.cliBackends`,key 是 provider id(形成 model ref 的左半部分 `<provider>/<model>`):

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

Bundled Anthropic plugin 注册了默认 `claude-cli` backend,零配置即可用:
```bash
openclaw agent --agent main --message "hi" --model claude-cli/claude-sonnet-4-6
```

Gateway 在 launchd/systemd 下运行时 PATH 受限,需要显式指定 command 绝对路径。

## Fallback 配置

加入 fallback 列表,primary 失败时自动尝试:

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

使用 `agents.defaults.models` 作为 allowlist 时,CLI backend models 也必须包含在内。

## 执行流程

1. 基于 provider prefix 选择 backend
2. 构建 system prompt(OpenClaw prompt + workspace context)
3. CLI 执行,带 session id(如果支持)
4. 输出解析(JSON/JSONL/text)
5. Session id 持久化,follow-up 复用

## Bundled backends

### claude-cli (Anthropic)

默认: `command: "claude"`, `output: "jsonl"`, `input: "stdin"`, `sessionMode: "always"`, `liveSession: "claude-stdio"`。

前置条件: Claude Code 必须在同一主机登录(`claude auth login`)。

**Skill resolution**: 优先用 Claude Code 的 native skill resolver。当 skills snapshot 包含至少一个 materialized path 的 skill 时,通过 `--plugin-dir` 传递临时 plugin,从 system prompt 省略重复 skills catalog。

**Permission mapping**: OpenClaw exec policy 映射到 Claude permission mode。YOLO mode (`tools.exec.security: "full"` + `tools.exec.ask: "off"`) → `--permission-mode bypassPermissions`。Restrictive policy → `--permission-mode default`。

**Effort mapping**: `/think` levels 映射到 Claude `--effort`: minimal/low → low, adaptive/medium → medium, high/xhigh/max → direct。

**Native compaction**: Claude Code 内部 compact 自己的 transcript,声明 `ownsNativeCompaction: true`。OpenClaw 从 compaction path 返回 no-op。旧的 `contextTokens: 1_000_000` workaround 不再需要。

**活跃会话**: 每个 OpenClaw session 保持一个 Claude stdio process。Gateway 重启或 idle process 退出时,从存储 session id 恢复。Stored session ids 在恢复前验证可读 project transcripts,phantom bindings 以 `reason=transcript-missing` 清除。Bounded JSONL output guards 默认 8 MiB 和 20,000 lines per turn,可通过 `reliability.outputLimits` 提高(clamped 到 64 MiB / 100,000 lines)。

### google-gemini-cli (Google)

默认: `command: "gemini"`, `output: "jsonl"`, `jsonlDialect: "gemini-stream-json"`, `imageArg: "@"`, `imagePathScope: "workspace"`, `sessionMode: "existing"`。

前置条件: `brew install gemini-cli` 或 `npm install -g @google/gemini-cli`。

`stream-json` parser 读取 assistant message events、tool events、final result usage、fatal error events。Usage fallback 到 `stats`,`stats.cached` 归一化为 `cacheRead`,input tokens 从 `stats.input_tokens - stats.cached` 派生。

## Session management

三种 session modes:

| Mode | Behavior |
|---|---|
| `always` | 每次调用发送 session id(无则生成 UUID) |
| `existing` | 仅在有存储 session id 时发送 |
| `none` | 不发送 session id |

Session 连续性规则:
- Stored CLI sessions 是 provider-owned,隐式日重置不切断;`/reset` 和 `session.reset` 仍然清除
- Auth identity 变更(profile id、static key、token、OAuth account identity)时丢弃 stored session
- OAuth token rotation **不**切断 stored session
- `serialize: true` 保持同通道运行有序

### Reseed behavior

新 CLI session 从 OpenClaw compaction summary + post-compaction tail reseed。`reseedFromRawTranscriptWhenUncompacted: true` 可恢复安全 invalidations(missing transcripts、system prompt 变更、session-expired retries)。Auth profile 或 credential-epoch 变更永不触发 raw transcript reseed。

Reseed history cap 默认 12,288 字符(~3,000 tokens)。Claude CLI 用更大的 cap(基于 resolved context tier)。

## Fallback prelude

`claude-cli` 失败后 fallback 到非 CLI 候选时,OpenClaw 从 Claude Code 的本地 JSONL transcript (`~/.claude/projects/`) 提取 context prelude:

- 优先使用 latest `/compact` summary 或 `compact_boundary` marker
- Append 最近的 post-boundary turns(character budget 内)
- Pre-boundary turns 丢弃(summary 已代表)
- Tool blocks 合并为 compact hints: `(tool call: name)` / `(tool result: …)`
- Same-provider `claude-cli` → `claude-cli` fallback 用 Claude 的 `--resume`,跳过 prelude

没有这个上下文种子,fallback provider 会 cold start,因为 OpenClaw 自己的 session transcript 对 `claude-cli` runs 是空的。

## BundleMCP overlays

CLI backend 不直接接收 OpenClaw tool calls。`bundleMcp: true` 启用 MCP config overlay:

1. 启动 loopback HTTP MCP server,暴露 gateway tools 给 CLI process
2. Per-session token 认证 (`OPENCLAW_MCP_TOKEN`)
3. Tool access scoped 到当前 session、account、channel context
4. 加载 enabled bundle-MCP servers
5. 合并已有 backend MCP config
6. 用 backend-owned integration mode 重写 launch config

`claude-cli` 生成 strict MCP config file,`google-gemini-cli` 生成 Gemini system settings file。

Session-scoped MCP runtimes 缓存复用,`mcp.sessionIdleTtlMs` (默认 10 分钟) 后回收。One-shot runs(auth probes、slug generation、active-memory recall)在 run 结束时请求清理。

## Native compaction ownership

声明 `ownsNativeCompaction: true` 的 backend 防止 OpenClaw safeguard summarizer 与其自己的 compaction 冲突。要求: 可靠 bound transcript near context window,持久化可恢复 session(`--resume` / `--session-id`)。Matching `agentHarnessId` sessions 仍路由到 harness endpoint。

## 限制

- **没有直接 tool calls**: 只有 `bundleMcp: true` backends 看到 gateway tools
- **Streaming 变化**: 有些 stream JSONL,有些 buffer 到退出
- **Structured outputs** 完全依赖 CLI 的 JSON 格式
