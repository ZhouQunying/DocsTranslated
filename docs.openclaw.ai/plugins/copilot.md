# Copilot

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么把 Copilot 做成独立外部插件而不是内置？

`@github/copilot-sdk` 加上平台特定的 `@github/copilot-<platform>-<arch>` CLI 二进制一共约 260 MB。内置进核心 `openclaw` 包意味着每个用户都要下载这 260 MB，哪怕从来不用 Copilot。拆成外部插件后，只有真正选择这个运行时的 agent 才安装。就像 VS Code 不把每个语言服务器打包进安装器——C++ 扩展、Python 扩展各自独立安装，按需下载。好处是核心包保持精简，坏处是第一次使用时多一步安装。

第二个关键设计：双写会话记录（dual-write transcripts）。Copilot SDK 接管 agent 循环后，OpenClaw 仍然需要一个审计追踪——channel 可见历史、搜索索引、`/new` 和 `/reset` 都依赖它。所以每个回合的消息同时写入 SDK 会话和 OpenClaw 审计记录，就像 CQRS 的事件溯源——命令端（SDK）执行逻辑，查询端（OpenClaw）维护读模型。两层失败隔离确保写入审计记录失败不会导致回合失败：尽力而为包装器加尝试级别的 `.catch(...)`。

第三个边界：认证优先级链。五种认证源按优先级排列——显式登录用户、显式 token、契约解析的认证配置、环境变量后备、默认登录用户。就像 HTTP 认证中间件依次尝试每种方法。关键是每个 agent 持有独立的 `copilotHome` 目录，这样 Copilot CLI 的 token、会话和配置不会在同一台机器上不同 agent 之间泄漏。

---

外部 `@openclaw/copilot` 插件让 OpenClaw 通过 GitHub Copilot CLI（`@github/copilot-sdk`）运行嵌入式订阅 Copilot agent 回合，而非内置 PI harness。

当你想让 Copilot CLI 会话持有底层 agent 循环时使用 Copilot SDK harness：原生工具执行、原生压缩（`infiniteSessions`）和 `copilotHome` 下 CLI 管理的线程状态。OpenClaw 仍持有聊天 channel、会话文件、模型选择、动态工具桥接、审批、媒体交付和可见会话记录镜像。`/btw` 侧问由内置 PI 后备处理（参见[侧问 (`/btw`)](#侧问-btw)），`openclaw doctor` 照常工作。

关于更广泛的模型/provider/运行时划分，从 [Agent runtimes](/concepts/agent-runtimes) 开始。

## 要求

- 安装了 `@openclaw/copilot` 插件的 OpenClaw。
- 如果配置使用 `plugins.allow`，包含 `copilot`（插件声明的 manifest id）。使用 npm 风格 `@openclaw/copilot` 包名的限制允许列表会让插件被阻止，即使配置了 `agentRuntime.id: "copilot"` 运行时也不会加载。
- 能驱动 Copilot CLI 的 GitHub Copilot 订阅（或用于无头/cron 运行的 `gitHubToken` 环境变量/认证配置条目）。
- 可写的 `copilotHome` 目录。harness 默认使用 `~/.openclaw/agents/<agentId>/copilot` 实现完全按 agent 隔离。平台默认（Windows 上 `%APPDATA%\copilot`，其他系统上 `$XDG_CONFIG_HOME/copilot` 或 `~/.config/copilot`）在未设置显式 home 时用作 doctor 探测后备。

`openclaw doctor` 运行扩展的插件 [doctor 契约](#doctor-和探测)；那里的失败是在让 agent 加入前确认环境就绪的标准方式。

## 插件安装

Copilot 运行时是外部插件，核心 `openclaw` 包不附带 `@github/copilot-sdk` 依赖或其平台特定的 `@github/copilot-<platform>-<arch>` CLI 二进制。两者合计约 260 MB，只为选择此运行时的 agent 安装：

```bash
openclaw plugins install @openclaw/copilot
```

当你第一次选择 `github-copilot/*` 模型**且**配置通过 `agentRuntime: { id: "copilot" }` 让该模型（或其 provider）加入 Copilot agent 运行时，向导会安装插件。没有加入的话，openclaw 使用内置 GitHub Copilot provider，永远不安装运行时插件。

运行时按此顺序解析 SDK：

1. 从已安装的 `@openclaw/copilot` 包 `import("@github/copilot-sdk")`。
2. 已知后备目录 `~/.openclaw/npm-runtime/copilot/`（遗留的按需安装目标）。

缺少 SDK 时抛出单一错误，代码 `COPILOT_SDK_MISSING`，附带上述插件重装命令。

## 快速入门

将一个模型（或一个 provider）固定到 harness：

```json5
{
  agents: {
    defaults: {
      model: "github-copilot/gpt-5.5",
      models: {
        "github-copilot/gpt-5.5": {
          agentRuntime: { id: "copilot" },
        },
      },
    },
  },
}
```

两种方式等价。仅该模型应路由到 harness 时在单个模型条目上使用 `agentRuntime.id`；provider 下每个模型都应使用它时在 provider 上设置 `agentRuntime.id`。

## 支持的 provider

harness 声明支持标准 `github-copilot` provider（与 `extensions/github-copilot` 持有的相同 id）：

- `github-copilot`

该集合之外的任何东西都通过 `selection.ts` 的 `auto_pi` 分支回退到 PI。

## 认证

按 agent 优先级排列，在 `runCopilotAttempt` 期间应用：

1. **显式 `useLoggedInUser: true`** 在尝试输入上。使用 agent 的 `copilotHome` 下解析的 Copilot CLI 登录用户。
2. **显式 `gitHubToken`** 在尝试输入上（附带 `profileId` + `profileVersion`）。适用于调用者想绕过认证配置解析的直接 CLI 调用和测试。
3. **契约解析的 `resolvedApiKey` + `authProfileId`** 来自 `EmbeddedRunAttemptParams` 形态。这是**生产主路径**：核心在调用 harness 前解析 agent 配置的 `github-copilot` 认证配置（通过 `src/infra/provider-usage.auth.ts:resolveProviderAuths`），harness 直接消费两个字段。这让 `github-copilot:<profile>` 认证配置在无头/cron/多配置设置中端到端工作，无需环境变量。
4. **环境变量后备** 用于没有配置认证配置的直接 CLI/dogfood 运行。运行时按优先级顺序检查以下变量，镜像已发布的 `github-copilot` provider（`extensions/github-copilot/auth.ts`）和文档化的 Copilot SDK 设置：
   1. `OPENCLAW_GITHUB_TOKEN`——harness 特定覆盖；设置它以固定 OpenClaw harness 的 token，不影响系统级 `gh`/Copilot CLI 配置。
   2. `COPILOT_GITHUB_TOKEN`——标准 Copilot SDK/CLI 环境变量。
   3. `GH_TOKEN`——标准 `gh` CLI 环境变量（匹配现有 `github-copilot` provider 优先级）。
   4. `GITHUB_TOKEN`——通用 GitHub token 后备。

   第一个非空值生效；空字符串视为不存在。合成的池配置 id 是 `env:NAME`，profileVersion 是 token 的不可逆 sha256 指纹，所以轮换环境变量值会干净地使客户端池失效。

5. **默认 `useLoggedInUser`** 当没有 token 信号可用时。

每个 agent 获得专用 `copilotHome`，这样 Copilot CLI token、会话和配置不会在同一台机器上不同 agent 之间泄漏。默认是当宿主给 harness 传递 agent 目录时的 `<agentDir>/copilot`（将 SDK 状态与同目录下的 OpenClaw `models.json`/`auth-profiles.json` 隔离），否则是 `~/.openclaw/agents/<agentId>/copilot`。需要自定义位置时用 `copilotHome: <path>` 覆盖（例如迁移的共享挂载）。

`probeCopilotAuthShape`（参见 [Doctor 和探测](#doctor-和探测)）是纯形态检查，验证上述哪种模式会被使用。它不执行实际 SDK 握手。

## 配置表面

harness 从每次尝试输入（`runCopilotAttempt({...})`）加上 `extensions/copilot/src/` 中的少量环境变量默认值读取配置：

- `copilotHome`——按 agent 的 CLI 状态目录（默认值见上述文档）。
- `model`——字符串或 `{ provider, id, api? }`。省略时 OpenClaw 使用 agent 的正常模型选择，harness 验证解析出的 provider 在支持集合中。
- `reasoningEffort`——`"low" | "medium" | "high" | "xhigh"`。从 `auto-reply/thinking.ts` 中的 OpenClaw `ThinkLevel`/`ReasoningLevel` 解析映射。
- `infiniteSessionConfig`——SDK `infiniteSessions` 块的可选覆盖，由 `harness.compact` 驱动。默认值保持不变是安全的。
- `hooksConfig`——可选桥接配置，将 OpenClaw 消息写入前后钩子暴露给 SDK 循环。
- `permissionPolicy`——SDK `onPermissionRequest` 处理器的可选覆盖，用于内置 SDK 工具类型（`shell`、`write`、`read`、`url`、`mcp`、`memory`、`hook`）。默认 `rejectAllPolicy` 作为安全网；实际上 SDK 从不调用这些类型，因为每个桥接的 OpenClaw 工具都以 `overridesBuiltInTool: true` 和 `skipPermission: true` 注册，100% 的工具调用通过 OpenClaw 包装的 `execute()` 流转。参见[权限和 ask_user](#权限和-ask_user)。
- `enableSessionTelemetry`——通过 `telemetry-bridge.ts` 的 opt-in OpenTelemetry 路由。

OpenClaw 其余部分无需知道这些字段。其他插件、channel 和核心代码只看到标准 `AgentHarnessAttemptParams`/`AgentHarnessAttemptResult` 形态。

## 压缩

当 `harness.compact` 运行时，Copilot SDK harness：

1. 恢复追踪的 SDK 会话，不继续待处理工作。
2. 调用 SDK 会话级历史压缩 RPC。
3. 返回 SDK 压缩结果，不在工作区下写入兼容标记文件。

OpenClaw 端的会话记录镜像（见下文）继续接收压缩后消息，用户可见的聊天历史保持一致。

## 会话记录镜像

`runCopilotAttempt` 通过 `extensions/copilot/src/dual-write-transcripts.ts` 将每个回合的可镜像消息双写到 OpenClaw 审计记录。镜像按会话作用域（`copilot:${sessionId}`），使用按消息身份（`${role}:${sha256_16(role,content)}`），这样前回合条目的重新发出与磁盘上现有键碰撞，不会重复。

镜像包裹在两层失败隔离中，确保记录写入失败不会导致尝试失败：内部尽力而为包装器和尝试级别的纵深防御 `.catch(...)`。失败被记录但不浮出。

## 侧问 (`/btw`)

`/btw` 在此 harness 上**不是**原生的。`createCopilotAgentHarness()` 故意不定义 `harness.runSideQuestion`，OpenClaw 的 `/btw` 调度器（`src/agents/btw.ts`）回退到每个非 Codex 运行时使用的内置 PI 后备路径。配置的模型 provider 被直接调用，附带简短侧问提示，通过 `streamSimple` 流式返回（无 CLI 会话，无额外池槽）。

这保持 Copilot CLI 会话专用于 agent 的主回合循环，保持 `/btw` 行为与其他 PI 支持的运行时一致。契约在 `extensions/copilot/harness.test.ts` 的 `describe("runSideQuestion")` 下断言。

## Doctor 和探测

`extensions/copilot/doctor-contract-api.ts` 被 `src/plugins/doctor-contract-registry.ts` 自动加载。它贡献：

- 空的 `legacyConfigRules`（MVP 阶段无退役字段）。
- 空操作 `normalizeCompatibilityConfig`（保留以便未来字段退役有稳定的内置归属）。
- 一条 `sessionRouteStateOwners` 条目，声明 provider `github-copilot`；运行时 `copilot`；CLI 会话键 `copilot`；认证配置前缀 `github-copilot:`。

`extensions/copilot/src/doctor-probes.ts` 导出三个命令式探测，宿主（包括 `openclaw doctor`）可调用它们验证环境：

| 探测 | 检查内容 | 可能失败原因 |
| --- | --- | --- |
| `probeCopilotCliVersion` | `copilot --version` 退出 0 且版本字符串非空 | `non-zero-exit`、`empty-version`、`spawn-failed`、`spawn-error`、`probe-timeout` |
| `probeCopilotHomeWritable` | `mkdir -p copilotHome` + 写入 + 删除标记文件 | `copilothome-not-writable`（底层 fs 错误在 `details.rawError` 中） |
| `probeCopilotAuthShape` | `useLoggedInUser`、`gitHubToken` 或 `profileId`+`profileVersion` 至少一个 | `no-auth-source` |

每个探测接受 DI 接缝（`spawnFn`、`fsApi`），测试不会生成真实 Copilot CLI 或触及宿主文件系统。

## 限制

- harness 在 MVP 阶段只声明标准 `github-copilot` provider。额外 provider（BYOK 或其他）应在后续 PR 中附带适配器一起落地。
- harness 不提供 TUI；PI 的 TUI 不受影响，仍是没有对等表面的运行时的后备。
- agent 切换到 `copilot` 时不迁移 PI 会话状态。选择按尝试进行；现有 PI 会话保持有效。
- **交互式 `ask_user` 尚未接线。** SDK 的 `onUserInputRequest` 处理器故意未注册，按 SDK 契约这完全对模型隐藏 `ask_user` 工具。在此 harness 下运行的 agent 从初始提示做最佳判断，而非在回合中途询问澄清问题。后续工作会将 `extensions/codex/src/app-server/user-input-bridge.ts` 的 codex 模式移植过来，将 SDK `UserInputRequest` 路由到 OpenClaw channel/TUI 提示路径；`extensions/copilot/src/user-input-bridge.ts` 中的休眠脚手架就是后续工作要接线的表面。

## 权限和 ask_user

桥接 OpenClaw 工具的权限执行发生在**工具包装器内部**，而非通过 SDK 的 `onPermissionRequest` 回调。PI 使用的同一个 `wrapToolWithBeforeToolCallHook`（`src/agents/pi-tools.before-tool-call.ts`）被 `createOpenClawCodingTools` 应用到每个编码工具。循环检测、可信插件策略、工具调用前钩子和通过 gateway 的两阶段插件审批（`plugin.approval.request`）都以与原生 PI 尝试完全相同的代码路径运行。

为了让该包装器持有决策权，`convertOpenClawToolToSdkTool` 返回的 SDK Tool 标记为：

- `overridesBuiltInTool: true`——替换同名 Copilot CLI 内置工具（edit、read、write、bash 等），这样每个工具调用路由回 OpenClaw。
- `skipPermission: true`——告诉 SDK 在调用工具前不触发 `onPermissionRequest({kind: "custom-tool"})`。包装的 `execute()` 内部执行更丰富的 OpenClaw 策略检查；SDK 级提示要么短路 OpenClaw 的执行（如果全部允许），要么阻止每个工具调用（如果全部拒绝）——都不匹配 PI 对等。

内置 codex harness 使用相同划分。桥接的 OpenClaw 工具被包装（`extensions/codex/src/app-server/dynamic-tools.ts`），codex-app-server 自己的原生审批类型通过 `plugin.approval.request` 路由（`extensions/codex/src/app-server/approval-bridge.ts`）。Copilot SDK 等价物是对任何到达 `onPermissionRequest` 的非 `custom-tool` 类型的默认拒绝 `rejectAllPolicy`——相同的安全网，实际上不触发，因为 `overridesBuiltInTool: true` 替换了每个内置。

为了让包装工具层做出与 PI 等价的策略决策，harness 将完整 PI 尝试工具上下文转发给 `createOpenClawCodingTools`。转发身份字段如 `senderIsOwner`、`memberRoleIds`、`ownerOnlyToolAllowlist`。转发 channel/路由字段如 `groupId`、`currentChannelId`、`replyToMode`、消息工具开关。转发认证（`authProfileStore`）、运行身份（`sessionKey`/`runSessionKey` 派生自 `sandboxSessionKey`、`runId`）、模型上下文（`modelApi`、`modelContextWindowTokens` 等）和运行钩子（`onToolOutcome`、`onYield`）。没有这些字段，仅限 owner 的允许列表默认表现为拒绝，插件信任策略无法解析到正确作用域，`session_status: "current"` 解析到过期的沙箱键。桥构建器在 `extensions/copilot/src/tool-bridge.ts`，镜像 `src/agents/pi-embedded-runner/run/attempt.ts:1029-1117` 的 PI 权威调用。两个 PI 字段在 MVP 阶段故意**不**转发并作为后续追踪：`sandbox`（harness 尚未通过 `resolveSandboxContext` 路由）和 PI 工具搜索/代码模式机制，后者在 SDK 边界没有对应物。

### 会话级 GitHub token

Copilot SDK 契约区分**客户端级** GitHub token（`CopilotClientOptions.gitHubToken`，用于认证 CLI 进程本身）和**会话级** token（`SessionConfig.gitHubToken`，决定该会话的内容排除、模型路由和配额，在 `createSession` 和 `resumeSession` 上都生效）。harness 通过 `resolveCopilotAuth` 解析认证一次，当认证模式是 `gitHubToken`（显式 `auth.gitHubToken` 或从配置的 `github-copilot` 认证配置契约解析的 `resolvedApiKey`）时设置两个字段。当解析模式是 `useLoggedInUser` 时，省略会话级字段，SDK 继续从登录身份派生身份。

`ask_user` 故意隐藏——参见上述限制。

## 相关

- [Agent runtimes](/concepts/agent-runtimes)
- [Codex harness](/plugins/codex-harness)
- [Agent harness plugins (SDK reference)](/plugins/sdk-agent-harness)
