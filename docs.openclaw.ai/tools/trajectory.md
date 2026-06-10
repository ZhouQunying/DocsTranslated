# Trajectory bundles

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 出了问题——怎么事后查它到底做了什么？

Agent 自主跑了 20 步工具调用，最后给了一个错误结果。对话历史只有最终输出。你想知道："第 7 步调的什么？为什么第 12 步突然换了方向？"

这就是飞行记录仪（flight recorder）。飞机无论出不出事都在录黑匣子——出事了才去查。OpenClaw 的 trajectory 一样：每个会话的每一步都在记录，但平时不看它。出问题时 `/export-trajectory` 打个包给你。

### 结构化时间线 vs 原始日志

不是简单地 dump 所有 stdout。每个事件有类型（工具调用、模型响应、系统事件）、时间戳、因果链（哪个工具调用触发了哪个结果）。

跟分布式链路追踪（Jaeger/Zipkin）一个思路：不是看日志里 grep 关键字，而是能按请求维度看完整的调用链。

### 脱敏和打包

导出时自动脱敏：API key、用户敏感信息被替换。这样你能把 trajectory 发给别人帮你 debug，不用担心泄露凭证。

打包格式是自包含的：不依赖运行环境，别人拿到包就能完整回放时间线。跟 Firefox crash report 的设计意图一样——用户一键导出，开发者拿到就能复现。

---

> Trajectory capture is OpenClaw's per-session flight recorder. It records a
> structured timeline for each agent run, then `/export-trajectory` packages the
> current session into a redacted support bundle.

trajectory 捕获是 OpenClaw 按会话的"飞行记录仪"。它给每次 agent 运行记一份结构化时间线,然后 `/export-trajectory` 把当前会话打包成一份脱敏的排障 bundle。

> Use it when you need to answer questions like:
>
> - What prompt, system prompt, and tools were sent to the model?
> - Which transcript messages and tool calls led to this answer?
> - Did the run time out, abort, compact, or hit a provider error?
> - Which model, plugins, skills, and runtime settings were active?
> - What usage and prompt-cache metadata did the provider return?

需要回答这种问题时用它:

- 发给模型的 prompt、system prompt 和工具是哪些?
- 哪些对话记录消息和工具调用导致了这个答案?
- 这次运行有没有超时、中止、压缩,或撞上 provider 错误?
- 当时活跃的模型、插件、技能、运行时设置是什么?
- provider 返回了哪些用量和 prompt 缓存元数据?

> If you are filing a broad support report for a live Gateway issue, start with
> [`/diagnostics`](/gateway/diagnostics#chat-command). Diagnostics collects the
> sanitized Gateway bundle and, for OpenAI Codex harness sessions, can also send
> Codex feedback to OpenAI servers after approval. Use `/export-trajectory` when
> you specifically need the detailed per-session prompt, tool, and transcript
> timeline.

要给一个正在跑的 Gateway 问题提交宽泛的排障报告,先用 [`/diagnostics`](/gateway/diagnostics#chat-command)。diagnostics 收集脱敏后的 Gateway bundle;对 OpenAI Codex harness 会话,审批后还能把 Codex 反馈发给 OpenAI 服务器。当你**明确**需要按会话的详细 prompt、工具、对话记录时间线时,才用 `/export-trajectory`。

## 快速开始

> Send this in the active session:

在当前会话里发:

```text
/export-trajectory
```

> Alias:

别名:

```text
/trajectory
```

> OpenClaw writes the bundle under the workspace:

OpenClaw 把 bundle 写到工作区下面:

```text
.openclaw/trajectory-exports/openclaw-trajectory-<session>-<timestamp>/
```

> You can choose a relative output directory name:

可以指定一个相对的输出目录名:

```text
/export-trajectory bug-1234
```

> The custom path is resolved inside `.openclaw/trajectory-exports/`. Absolute
> paths and `~` paths are rejected.

自定义路径在 `.openclaw/trajectory-exports/` 里解析。绝对路径和 `~` 路径会被拒。

> Trajectory bundles can contain prompts, model messages, tool schemas, tool
> results, runtime events, and local paths. The chat slash command therefore runs
> through exec approval every time. Approve the export once when you intend to
> create the bundle; do not use allow-all. In group chats, OpenClaw sends the
> approval prompt and export result to the owner privately instead of posting the
> trajectory details back to the shared room.

trajectory bundle 可能包含 prompt、模型消息、工具 schema、工具结果、运行时事件、本地路径。所以聊天里的 slash 命令每次都走 exec 审批。打算导一份就批一次;不要用 allow-all。群聊里,OpenClaw 把审批提示和导出结果**私聊**给所有者,不会把 trajectory 细节贴回共享房间。

> For local inspection or support workflows, you can also run the approved command
> path directly:

本地查看或支持工作流里,也可以直接走审批好的命令路径:

```bash
openclaw sessions export-trajectory --session-key "agent:main:telegram:direct:123" --workspace .
```

## 访问权限

> Trajectory export is an owner command. The sender must pass the normal command
> authorization checks and owner checks for the channel.

trajectory 导出是所有者命令。发送者必须通过通道的普通命令授权检查和所有者检查。

## 记录什么

> Trajectory capture is on by default for OpenClaw agent runs.

trajectory 捕获对 OpenClaw agent 运行**默认开**。

> Runtime events include:

运行时事件包括:

> - `session.started`
> - `trace.metadata`
> - `context.compiled`
> - `prompt.submitted`
> - `model.fallback_step`, including the source model, next model, failure reason/detail, chain position, and whether fallback advanced, succeeded, or exhausted the chain
> - `model.completed`
> - `trace.artifacts`
> - `session.ended`

- `session.started`
- `trace.metadata`
- `context.compiled`
- `prompt.submitted`
- `model.fallback_step`,含源模型、下一个模型、失败原因 / 细节、在回退链里的位置,以及"回退是否前进、成功或耗尽链路"
- `model.completed`
- `trace.artifacts`
- `session.ended`

> Transcript events are also reconstructed from the active session branch:
>
> - user messages
> - assistant messages
> - tool calls
> - tool results
> - compactions
> - model changes
> - labels and custom session entries

对话记录事件也会从当前会话分支重建:

- 用户消息
- assistant 消息
- 工具调用
- 工具结果
- 压缩
- 模型切换
- 标签和自定义会话条目

> Events are written as JSON Lines with this schema marker:

事件以 JSON Lines 写出,带这个 schema 标记:

```json
{
  "traceSchema": "openclaw-trajectory",
  "schemaVersion": 1
}
```

## bundle 文件

> An exported bundle can contain:

一份导出的 bundle 可能包含:

> | File                  | Contents                                                                                       |

| 文件                  | 内容                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------ |
| `manifest.json`       | Bundle schema、源文件、事件计数、生成文件清单                                              |
| `events.jsonl`        | 排好序的运行时和对话记录时间线                                                             |
| `session-branch.json` | 脱敏后的当前对话记录分支和会话头                                                           |
| `metadata.json`       | OpenClaw 版本、操作系统 / 运行时、模型、配置快照、插件、技能、prompt 元数据                |
| `artifacts.json`      | 最终状态、错误、用量、prompt 缓存、压缩计数、assistant 文本、工具元数据                    |
| `prompts.json`        | 提交的 prompt 和选中的 prompt 构建细节                                                     |
| `system-prompt.txt`   | 最新编译出的 system prompt(捕获到的话)                                                   |
| `tools.json`          | 发给模型的工具定义(捕获到的话)                                                           |

> `manifest.json` lists the files present in that bundle. Some files are omitted
> when the session did not capture the corresponding runtime data.

`manifest.json` 列出 bundle 里实际存在的文件。会话没捕获到对应运行时数据时,有些文件会省略。

## 捕获位置

> By default, runtime trajectory events are written beside the session file:

默认情况下,运行时 trajectory 事件写在会话文件旁边:

```text
<session>.trajectory.jsonl
```

> OpenClaw also writes a best-effort pointer file beside the session:

OpenClaw 也尽力在会话旁边写一份指针文件:

```text
<session>.trajectory-path.json
```

> Set `OPENCLAW_TRAJECTORY_DIR` to store runtime trajectory sidecars in a
> dedicated directory:

把运行时 trajectory sidecar 存到专门目录,设 `OPENCLAW_TRAJECTORY_DIR`:

```bash
export OPENCLAW_TRAJECTORY_DIR=/var/lib/openclaw/trajectories
```

> When this variable is set, OpenClaw writes one JSONL file per session id in that
> directory.

设了这个变量,OpenClaw 在那个目录下按 session id 一份一份地写 JSONL 文件。

> Session maintenance removes trajectory sidecars when their owning session entry
> is pruned, capped, or evicted by the sessions disk budget. Runtime files outside
> the sessions directory are removed only when the pointer target still proves it
> belongs to that session.

会话维护会在对应会话条目被裁剪、超上限、或因 sessions 磁盘预算被驱逐时,删掉 trajectory sidecar。sessions 目录之外的运行时文件,只有在指针目标仍能证明它属于这个会话时才会删。

## 关掉捕获

> Set `OPENCLAW_TRAJECTORY=0` before starting OpenClaw:

启动 OpenClaw 之前设 `OPENCLAW_TRAJECTORY=0`:

```bash
export OPENCLAW_TRAJECTORY=0
```

> This disables runtime trajectory capture. `/export-trajectory` can still export
> the transcript branch, but runtime-only files such as compiled context,
> provider artifacts, and prompt metadata may be missing.

这关掉运行时 trajectory 捕获。`/export-trajectory` 仍然能导出对话记录分支,但只在运行时才有的文件(如编译出的上下文、provider artifact、prompt 元数据)可能缺失。

## 调 flush 超时

> OpenClaw flushes runtime trajectory sidecars during agent cleanup. The default
> cleanup timeout is 10,000 ms. On slow disks or large stores, set
> `OPENCLAW_TRAJECTORY_FLUSH_TIMEOUT_MS` before starting OpenClaw:

OpenClaw 在 agent 清理期间把运行时 trajectory sidecar 推出来。默认清理超时 10,000 毫秒。慢盘或大存储上,启动 OpenClaw 之前设 `OPENCLAW_TRAJECTORY_FLUSH_TIMEOUT_MS`:

```bash
export OPENCLAW_TRAJECTORY_FLUSH_TIMEOUT_MS=30000
```

> This controls when OpenClaw logs a `pi-trajectory-flush` timeout and continues.
> It does not change the trajectory size caps. To tune all agent cleanup steps
> that do not pass an explicit timeout, set `OPENCLAW_AGENT_CLEANUP_TIMEOUT_MS`.

这控制 OpenClaw 多久会记下一条 `pi-trajectory-flush` 超时然后继续。它不改 trajectory 大小上限。要调所有不带显式超时的 agent 清理步骤,设 `OPENCLAW_AGENT_CLEANUP_TIMEOUT_MS`。

## 隐私和大小限制

> Trajectory bundles are designed for support and debugging, not public posting.
> OpenClaw redacts sensitive values before writing export files:

trajectory bundle 是为支持和排障设计的,不是公开张贴用的。OpenClaw 在写导出文件之前会把敏感值抹掉:

> - credentials and known secret-like payload fields
> - image data
> - local state paths
> - workspace paths, replaced with `$WORKSPACE_DIR`
> - home directory paths, where detected

- 凭证,以及已知的疑似密钥载荷字段
- 图片数据
- 本地状态路径
- 工作区路径,换成 `$WORKSPACE_DIR`
- 检测到的家目录路径

> The exporter also bounds input size:

导出器还限制输入大小:

> - runtime sidecar files: live capture stops at 10 MiB and records a truncation event when space remains; export accepts existing runtime sidecars up to 50 MiB
> - session files: 50 MiB
> - runtime events: 200,000
> - total exported events: 250,000
> - individual runtime event lines are truncated above 256 KiB

- 运行时 sidecar 文件:实时捕获到 10 MiB 停止,有空间时记一次截断事件;导出时接受最多 50 MiB 的已有运行时 sidecar
- 会话文件:50 MiB
- 运行时事件:200,000 条
- 导出的总事件:250,000 条
- 单条运行时事件行超过 256 KiB 会被截断

> Review bundles before sharing them outside your team. Redaction is best-effort
> and cannot know every application-specific secret.

把 bundle 分享出团队之前先复审一遍。脱敏是尽力而为的,无法识别每一个应用级密钥。

## 排障

> If the export has no runtime events:
>
> - confirm OpenClaw was started without `OPENCLAW_TRAJECTORY=0`
> - check whether `OPENCLAW_TRAJECTORY_DIR` points to a writable directory
> - run another message in the session, then export again
> - inspect `manifest.json` for `runtimeEventCount`

导出来的没有运行时事件:

- 确认 OpenClaw 启动时没有 `OPENCLAW_TRAJECTORY=0`
- 看 `OPENCLAW_TRAJECTORY_DIR` 是不是指向一个可写目录
- 在会话里再发一条消息,然后再导一次
- 看 `manifest.json` 里的 `runtimeEventCount`

> If the command rejects the output path:
>
> - use a relative name like `bug-1234`
> - do not pass `/tmp/...` or `~/...`
> - keep the export inside `.openclaw/trajectory-exports/`

命令拒绝输出路径时:

- 用 `bug-1234` 这种相对名
- 别传 `/tmp/...` 或 `~/...`
- 让导出留在 `.openclaw/trajectory-exports/` 里

> If the export fails with a size error, the session or sidecar exceeded the
> export safety limits. Start a new session or export a smaller reproduction.

导出报大小错误时,说明会话或 sidecar 超过了导出安全上限。开一个新会话,或者导一份更小的复现。

## 相关

> - [Diffs](/tools/diffs)
> - [Session management](/concepts/session)
> - [Exec tool](/tools/exec)

- [Diffs](/tools/diffs)
- [会话管理](/concepts/session)
- [Exec tool](/tools/exec)
