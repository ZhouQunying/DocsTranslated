# ACP Agents 设置

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 agent 编排需要标准化通信协议而非直接 API 调用？

OpenClaw 的 ACP（Agent Communication Protocol）让 Gateway 能生成和管理外部编码 agent（Codex、Claude Code、Gemini CLI 等），就像 Kubernetes 管理容器一样。acpx 是底层运行时——它启动 agent 进程、管理 stdio 通信、处理权限模型、提供健康探测。这就像 Docker 运行时与 OCI 标准的关系——任何符合 OCI 的容器都能运行，任何符合 ACP 的 agent 都能被 OpenClaw 编排。好处是添加新 agent 只需一个适配器配置，无需重写编排逻辑。

第二个设计：非交互式权限模型。ACP 会话没有 TTY——无法弹出"允许写入文件吗？"的提示。acpx 提供三级权限模式：`approve-all`（自动批准所有操作）、`approve-reads`（仅自动批准读取）、`deny-all`（拒绝所有）。当权限提示出现但没有交互式 TTY 时，`nonInteractivePermissions` 决定是失败退出还是静默拒绝并继续。这就像 Linux 的 SELinux 策略——在非交互式环境中，每个操作要么被预批准，要么被拒绝，没有"询问用户"的选项。好处是 agent 不会因等待人类输入而挂起。

第三个边界：MCP 桥接的信任域。ACP agent 默认无法访问 OpenClaw 插件工具。两个显式开关分别控制：`pluginToolsMcpBridge` 将 OpenClaw 插件工具通过 MCP 暴露给 ACP agent；`openClawToolsMcpBridge` 将内置工具（如 `cron`）暴露出去。这就像微服务的 API Gateway——内部服务不直接暴露给外部，必须通过显式路由。好处是信任边界是显式的、可审计的；坏处是需要额外配置才能跨域使用工具。

---

如需概览、操作者运行手册和概念，参见 [ACP agents](/tools/acp-agents)。

以下部分涵盖 acpx 运行时配置、MCP 桥接的插件设置和权限配置。

仅在使用 ACP/acpx 路由时才参考本页。对于原生 Codex 应用服务器运行时配置，使用 [Codex 运行时](/plugins/codex-harness)。对于 OpenAI API 密钥或 Codex OAuth 模型提供者配置，使用 [OpenAI](/providers/openai)。

Codex 有两条 OpenClaw 路由：

| 路由 | 配置/命令 | 设置页面 |
| --- | --- | --- |
| 原生 Codex 应用服务器 | `/codex ...`、`openai/gpt-*` agent 引用 | [Codex 运行时](/plugins/codex-harness) |
| 显式 Codex ACP 适配器 | `/acp spawn codex`、`runtime: "acp", agentId: "codex"` | 本页 |

除非明确需要 ACP/acpx 行为，否则优先使用原生路由。

## acpx 运行时支持（当前）

当前 acpx 内置运行时别名：

- `claude`、`codex`、`copilot`、`cursor`（Cursor CLI：`cursor-agent acp`）
- `droid`、`gemini`、`iflow`、`kilocode`、`kimi`、`kiro`
- `openclaw`、`opencode`、`qwen`

当 OpenClaw 使用 acpx 后端时，优先将这些值用于 `agentId`，除非你的 acpx 配置定义了自定义 agent 别名。

模型控制取决于适配器能力。Codex ACP 模型引用由 OpenClaw 在启动前规范化。其他运行时需要 ACP `models` 加 `session/set_model` 支持；如果运行时既不暴露该 ACP 能力也不提供自身的启动模型标志，OpenClaw/acpx 无法强制模型选择。

## 必需配置

核心 ACP 基线：

```json5
{
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "codex",
    allowedAgents: [
      "claude", "codex", "copilot", "cursor", "droid", "gemini",
      "iflow", "kilocode", "kimi", "kiro", "openclaw", "opencode", "qwen",
    ],
    maxConcurrentSessions: 8,
    stream: {
      coalesceIdleMs: 300,
      maxChunkChars: 1200,
    },
    runtime: {
      ttlMinutes: 120,
    },
  },
}
```

线程绑定配置因 channel 适配器而异。Discord 示例：

```json5
{
  session: {
    threadBindings: {
      enabled: true,
      idleHours: 24,
      maxAgeHours: 0,
    },
  },
  channels: {
    discord: {
      threadBindings: {
        enabled: true,
        spawnSessions: true,
      },
    },
  },
}
```

如线程绑定的 ACP 生成不工作，先验证适配器特性标志：`channels.discord.threadBindings.spawnSessions=true`。

当前会话绑定不需要子线程创建。它们需要活跃的会话上下文和暴露 ACP 会话绑定的 channel 适配器。

## acpx 后端的插件设置

打包安装使用官方 `@openclaw/acpx` 运行时插件进行 ACP。使用前安装并启用它：

```bash
openclaw plugins install @openclaw/acpx
openclaw config set plugins.entries.acpx.enabled true
```

源码检出也可在 `pnpm install` 后使用本地工作区插件。

从以下命令开始验证后端健康：

```text
/acp doctor
```

### acpx 命令和版本配置

默认情况下，`acpx` 插件在 Gateway 启动期间注册嵌入式 ACP 后端，并等待嵌入式运行时启动探测就绪后才发出 Gateway `ready` 信号。仅在需要故意禁用启动探测的脚本或环境中才设置 `OPENCLAW_ACPX_RUNTIME_STARTUP_PROBE=0`。

在插件配置中覆盖命令或版本：

```json
{
  "plugins": {
    "entries": {
      "acpx": {
        "enabled": true,
        "config": {
          "command": "../acpx/dist/cli.js",
          "expectedVersion": "any"
        }
      }
    }
  }
}
```

- `command` 接受绝对路径、相对路径（从 OpenClaw 工作区解析）或命令名
- `expectedVersion: "any"` 禁用严格版本匹配
- 自定义 `command` 路径会禁用插件本地自动安装

当路径或标志值应保持为单个 argv token 时，使用结构化参数覆盖单个 ACP agent 命令：

```json
{
  "plugins": {
    "entries": {
      "acpx": {
        "enabled": true,
        "config": {
          "agents": {
            "claude": {
              "command": "node",
              "args": ["/path/to/custom-adapter.mjs", "--verbose"]
            }
          }
        }
      }
    }
  }
}
```

### 自动依赖安装

使用 `npm install -g openclaw` 全局安装 OpenClaw 时，acpx 运行时依赖（平台特定的二进制文件）通过 postinstall 钩子自动安装。如自动安装失败，Gateway 仍正常启动并通过 `openclaw acp doctor` 报告缺少的依赖。

### 插件工具 MCP 桥接

默认情况下，ACPX 会话**不**将 OpenClaw 插件注册的工具暴露给 ACP 运行时。

如需让 Codex 或 Claude Code 等 ACP agent 调用已安装的 OpenClaw 插件工具（如记忆存储/召回），启用专用桥接：

```bash
openclaw config set plugins.entries.acpx.config.pluginToolsMcpBridge true
```

其作用：

- 在 ACPX 会话引导中注入名为 `openclaw-plugin-tools` 的内置 MCP 服务器
- 暴露已由已安装且启用的 OpenClaw 插件注册的工具
- 保持该功能为显式且默认关闭

安全和信任注意事项：这会扩展 ACP 运行时的工具表面。ACP agent 仅能访问 Gateway 中已活跃的插件工具。将此视为与让这些插件在 OpenClaw 本身中执行相同的信任边界。启用前请审查已安装的插件。

### OpenClaw 工具 MCP 桥接

默认情况下，ACPX 会话也**不**通过 MCP 暴露内置 OpenClaw 工具。当 ACP agent 需要选定的内置工具（如 `cron`）时，启用单独的核心工具桥接：

```bash
openclaw config set plugins.entries.acpx.config.openClawToolsMcpBridge true
```

### 运行时操作超时配置

`acpx` 插件默认给嵌入式运行时启动和控制操作 120 秒。这为 Gemini CLI 等较慢的运行时提供足够时间完成 ACP 启动和初始化。如需不同的操作限制可覆盖：

```bash
openclaw config set plugins.entries.acpx.config.timeoutSeconds 180
```

## 权限配置

ACP 会话以非交互方式运行——没有 TTY 来批准或拒绝文件写入和 shell 执行权限提示。acpx 插件提供两个配置键控制权限处理方式。

这些 ACPX 运行时权限与 OpenClaw exec 审批以及 CLI 后端厂商绕过标志（如 Claude CLI `--permission-mode bypassPermissions`）是分开的。ACPX `approve-all` 是 ACP 会话的运行时级应急开关。

### `permissionMode`

控制运行时 agent 无需提示即可执行的操作。

| 值 | 行为 |
| --- | --- |
| `approve-all` | 自动批准所有文件写入和 shell 命令 |
| `approve-reads` | 仅自动批准读取；写入和执行需要提示 |
| `deny-all` | 拒绝所有权限提示 |

### `nonInteractivePermissions`

控制当权限提示本应显示但没有交互式 TTY 可用时的行为（ACP 会话始终如此）。

| 值 | 行为 |
| --- | --- |
| `fail` | 以 `AcpRuntimeError` 中止会话。**（默认）** |
| `deny` | 静默拒绝权限并继续（优雅降级） |

### 配置

通过插件配置设置：

```bash
openclaw config set plugins.entries.acpx.config.permissionMode approve-all
openclaw config set plugins.entries.acpx.config.nonInteractivePermissions fail
```

更改这些值后重启 Gateway。

OpenClaw 默认使用 `permissionMode=approve-reads` 和 `nonInteractivePermissions=fail`。在非交互式 ACP 会话中，任何触发权限提示的写入或执行可能以 `AcpRuntimeError: Permission prompt unavailable in non-interactive mode` 失败。

如需限制权限，将 `nonInteractivePermissions` 设为 `deny`，使会话优雅降级而非崩溃。

## 相关

- [ACP agents](/tools/acp-agents)——概览、操作者运行手册、概念
- [子 agent](/tools/subagents)
- [多 agent 路由](/concepts/multi-agent)
