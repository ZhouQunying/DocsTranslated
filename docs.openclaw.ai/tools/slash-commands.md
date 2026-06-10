# 斜杠命令

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么命令要分三类而不是统一处理？

关键在于**模型是否需要看到这条消息**。Commands（`/new`、`/stop`）是管理操作,不该进上下文。Directives（`/think`、`/fast`）是参数调整,模型不需知道。Inline shortcuts（`/help`、`/status`）是即时查询,执行后剥离。

三者混在一起的坏处：模型会把 `/think high` 当用户意图去响应,浪费 token 还可能产生困惑。分离后模型只看到纯业务消息,命令在到达模型前已被网关拦截处理。

Directive 的"单独发 vs 混在消息里"区别也精妙：单独发会持久化到会话（改了后面所有轮次的行为）,混在消息里只影响当次（一次性提示）。这让用户可以精确控制"这次用高推理"还是"从现在起都用高推理"。

---

> The Gateway handles commands sent as standalone messages starting with `/`.

Gateway 处理以 `/` 开头的独立消息命令。宿主 bash 命令用 `! <cmd>`（`/bash <cmd>` 为别名）。

> When a conversation is bound to an ACP session...

对话绑定到 ACP 会话时,普通文本路由到 ACP 外部执行器。Gateway 管理命令保持本地：`/acp ...` 始终到达 OpenClaw 命令处理器,`/status` 和 `/unfocus` 在该表面启用命令处理时保持本地。

## 三种命令类型

**Commands（命令）**

以 `/...` 开头的独立消息,由 Gateway 处理。必须作为消息中唯一内容发送。

**Directives（指令）**

`/think`、`/fast`、`/verbose`、`/trace`、`/reasoning`、`/elevated`、`/exec`、`/model`、`/queue` —— 模型看到前从消息中剥离。单独发送时持久化会话设置；与其他文本一起发送时作为内联提示。

**Inline shortcuts（内联快捷方式）**

`/help`、`/commands`、`/status`、`/whoami` —— 立即执行并在模型看到剩余文本前剥离。仅授权发送者可用。

Directive 行为细节：

- Directive 在模型看到前从消息中剥离。
- **仅含 Directive 的消息**中,它们持久化到会话并回复确认。
- **含其他文本的普通聊天**消息中,它们作为内联提示,**不**持久化会话设置。
- Directive 仅对**授权发送者**生效。若设了 `commands.allowFrom` 则只用该白名单；否则授权来自频道白名单/配对加 `commands.useAccessGroups`。未授权发送者的 directive 被当纯文本。

## 配置

```json5
{
  commands: {
    native: "auto",
    nativeSkills: "auto",
    text: true,
    bash: false,
    bashForegroundMs: 2000,
    config: false,
    mcp: false,
    plugins: false,
    debug: false,
    restart: true,
    ownerAllowFrom: ["discord:123456789012345678"],
    ownerDisplay: "raw",
    ownerDisplaySecret: "${OWNER_ID_HASH_SECRET}",
    allowFrom: {
      "*": ["user1"],
      discord: ["user:123"],
    },
    useAccessGroups: true,
  },
}
```

`text`: 启用解析聊天消息中的 `/...`。无原生命令支持的表面（WhatsApp、WebChat、Signal、iMessage、Google Chat、Microsoft Teams）上即使设为 `false` 文本命令也可用。

`native`: 注册原生命令。Auto：Discord/Telegram 开；Slack 关；无原生支持的提供商忽略。用 `channels.<provider>.commands.native` 按频道覆盖。Discord 上 `false` 跳过斜杠命令注册；之前注册的命令在移除前可能仍可见。

`nativeSkills`: 支持时原生注册 skill 命令。Auto：Discord/Telegram 开；Slack 关。用 `channels.<provider>.commands.nativeSkills` 覆盖。

`bash`: 启用 `! <cmd>` 运行宿主 shell 命令（`/bash <cmd>` 别名）。需要 `tools.elevated` 白名单。

`bashForegroundMs`: bash 切到后台模式前等待多久（`0` 立即后台）。

`config`: 启用 `/config`（读写 `openclaw.json`）。仅 Owner。

`mcp`: 启用 `/mcp`（读写 `mcp.servers` 下 OpenClaw 管理的 MCP 配置）。仅 Owner。

`plugins`: 启用 `/plugins`（插件发现/状态加安装 + 启用/禁用）。写操作仅 Owner。

`debug`: 启用 `/debug`（仅运行时配置覆盖）。仅 Owner。

`restart`: 启用 `/restart` 和 gateway 重启工具操作。

`ownerAllowFrom`: 仅 Owner 命令表面的显式 owner 白名单。与 `commands.allowFrom` 和 DM 配对访问分开。

`<channel>.commands.enforceOwnerForCommands`: 按频道：要求 owner 身份才能用 owner-only 命令。为 `true` 时发送者须匹配 `commands.ownerAllowFrom` 或持有内部 `operator.admin` 权限范围。通配 `allowFrom` 条目**不**足够。

`ownerDisplay`: 控制系统提示中 owner id 的显示方式。

`ownerDisplaySecret`: `commands.ownerDisplay: "hash"` 时使用的 HMAC 密钥。

`allowFrom`: 按提供商的命令授权白名单。配置后它是命令和 directive 的**唯一**授权源。`"*"` 作全局默认；提供商特定键覆盖它。

`useAccessGroups`: `commands.allowFrom` 未设时对命令强制白名单/策略。

## 命令列表

> Commands come from three sources:

命令来自三个源：

- **核心内置：** `src/auto-reply/commands-registry.shared.ts`
- **生成的 dock 命令：** `src/auto-reply/commands-registry.data.ts`
- **插件命令：** 插件 `registerCommand()` 调用

可用性取决于配置标志、频道表面和已安装/启用的插件。

### 核心命令

**会话和运行**

| 命令 | 说明 |
| --- | --- |
| `/new [model]` | 归档当前会话并开始新会话 |
| `/reset [soft [message]]` | 原地重置当前会话。`soft` 保留记录,丢弃复用的 CLI 后端会话 id,重跑启动 |
| `/compact [instructions]` | 压缩会话上下文。见 [Compaction](/concepts/compaction) |
| `/stop` | 中止当前运行 |
| `/session idle <duration\|off>` | 管理线程绑定空闲过期 |
| `/session max-age <duration\|off>` | 管理线程绑定最大存活期 |
| `/export-session [path]` | 导出当前会话为 HTML。别名：`/export` |
| `/export-trajectory [path]` | 导出当前会话的 JSONL 轨迹包。别名：`/trajectory` |

注意：Control UI 拦截输入的 `/new` 以创建并切换到新仪表板会话,除非配了 `session.dmScope: "main"` 且当前父级是 agent 的主会话——此时 `/new` 原地重置主会话。输入的 `/reset` 仍运行 Gateway 的原地重置。

**模型和运行控制**

| 命令 | 说明 |
| --- | --- |
| `/think <level\|default>` | 设思考级别或清除会话覆盖。别名：`/thinking`、`/t` |
| `/verbose on\|off\|full` | 切换详细输出。别名：`/v` |
| `/trace on\|off` | 切换当前会话的插件 trace 输出 |
| `/fast [status\|on\|off\|default]` | 显示、设置或清除快速模式 |
| `/reasoning [on\|off\|stream]` | 切换推理可见性。别名：`/reason` |
| `/elevated [on\|off\|ask\|full]` | 切换提权模式。别名：`/elev` |
| `/exec host=<auto\|sandbox\|gateway\|node> security=<deny\|allowlist\|full> ask=<off\|on-miss\|always> node=<id>` | 显示或设置执行默认值 |
| `/model [name\|#\|status]` | 显示或设置模型 |
| `/models [provider] [page] [limit=<n>\|all]` | 列出已配置/认证可用的提供商或模型 |
| `/queue <mode>` | 管理活跃运行队列行为。见 [Queue](/concepts/queue) 和 [Queue steering](/concepts/queue-steering) |
| `/steer <message>` | 向活跃运行注入引导。别名：`/tell`。见 [Steer](/tools/steer) |

verbose / trace / fast / reasoning 安全说明：

- `/verbose` 用于调试——正常使用保持**关闭**。
- `/trace` 只显示插件持有的 trace/debug 行；正常详细输出保持关闭。
- `/fast on|off` 持久化会话覆盖；用会话 UI 的 `inherit` 选项清除。
- `/fast` 是提供商特定的：OpenAI/Codex 映射到 `service_tier=priority`；直接 Anthropic 请求映射到 `service_tier=auto` 或 `standard_only`。
- `/reasoning`、`/verbose` 和 `/trace` 在群组中有风险——可能暴露内部推理或插件诊断。群聊中保持关闭。

模型切换细节：

- `/model` 立即将新模型持久化到会话。
- Agent 空闲时下次运行立即使用。
- 运行活跃时切换标记为 pending,在下个干净重试点应用。

**发现和状态**

| 命令 | 说明 |
| --- | --- |
| `/help` | 显示简短帮助摘要 |
| `/commands` | 显示生成的命令目录 |
| `/tools [compact\|verbose]` | 显示当前 agent 现在能用什么 |
| `/status` | 显示执行/运行时状态、Gateway 和系统运行时间,加提供商用量/配额 |
| `/goal [status\|start\|pause\|resume\|complete\|block\|clear] ...` | 管理当前会话的持久 [goal](/tools/goal) |
| `/diagnostics [note]` | 仅 Owner 的支持报告流。每次都要求执行审批 |
| `/crestodian <request>` | 从 owner DM 运行 Crestodian 设置和修复助手 |
| `/tasks` | 列出当前会话的活跃/最近后台任务 |
| `/context [list\|detail\|map\|json]` | 解释上下文如何组装 |
| `/whoami` | 显示你的发送者 id。别名：`/id` |
| `/usage off\|tokens\|full\|cost` | 控制每响应用量页脚或打印本地成本摘要 |

**Skills、白名单、审批**

| 命令 | 说明 |
| --- | --- |
| `/skill <name> [input]` | 按名称运行 skill |
| `/allowlist [list\|add\|remove] ...` | 管理白名单条目。仅文本 |
| `/approve <id> <decision>` | 解决执行或插件审批提示 |
| `/btw <question>` | 不改会话上下文的旁问。别名：`/side`。见 [BTW](/tools/btw) |

**子 agent 和 ACP**

| 命令 | 说明 |
| --- | --- |
| `/subagents list\|log\|info` | 检查当前会话的子 agent 运行 |
| `/acp spawn\|cancel\|steer\|close\|sessions\|status\|set-mode\|set\|cwd\|permissions\|timeout\|model\|reset-options\|doctor\|install\|help` | 管理 ACP 会话和运行时选项 |
| `/focus <target>` | 将当前 Discord 帖子或 Telegram 话题绑定到会话目标 |
| `/unfocus` | 移除当前帖子绑定 |
| `/agents` | 列出当前会话的帖子绑定 agent |

**仅 Owner 写入和管理**

| 命令 | 需要 | 说明 |
| --- | --- | --- |
| `/config show\|get\|set\|unset` | `commands.config: true` | 读写 `openclaw.json`。仅 Owner |
| `/mcp show\|get\|set\|unset` | `commands.mcp: true` | 读写 OpenClaw 管理的 MCP 服务器配置。仅 Owner |
| `/plugins list\|inspect\|show\|get\|install\|enable\|disable` | `commands.plugins: true` | 检查或变更插件状态。写操作仅 Owner。别名：`/plugin` |
| `/debug show\|set\|unset\|reset` | `commands.debug: true` | 仅运行时配置覆盖。仅 Owner |
| `/restart` | `commands.restart: true`（默认） | 重启 OpenClaw |
| `/send on\|off\|inherit` | owner | 设置发送策略 |

**语音、TTS、频道控制**

| 命令 | 说明 |
| --- | --- |
| `/tts on\|off\|status\|chat\|latest\|provider\|limit\|summary\|audio\|help` | 控制 TTS。见 [TTS](/tools/tts) |
| `/activation mention\|always` | 设置群组激活模式 |
| `/bash <command>` | 运行宿主 shell 命令。别名：`! <command>`。需 `commands.bash: true` |
| `!poll [sessionId]` | 检查后台 bash 任务 |
| `!stop [sessionId]` | 停止后台 bash 任务 |

### Dock 命令

> Dock commands switch the active session's reply route to another linked channel.

Dock 命令将活跃会话的回复路由切到另一个链接频道。见 [Channel docking](/concepts/channel-docking)。

从有原生命令支持的频道插件生成：

- `/dock-discord`（别名：`/dock_discord`）
- `/dock-mattermost`（别名：`/dock_mattermost`）
- `/dock-slack`（别名：`/dock_slack`）
- `/dock-telegram`（别名：`/dock_telegram`）

Dock 命令需要 `session.identityLinks`。源发送者和目标对端须在同一身份组中。

### 内置插件命令

| 命令 | 说明 |
| --- | --- |
| `/dreaming [on\|off\|status\|help]` | 切换记忆做梦。见 [Dreaming](/concepts/dreaming) |
| `/pair [qr\|status\|pending\|approve\|cleanup\|notify]` | 管理设备配对。见 [Pairing](/channels/pairing) |
| `/phone status\|arm ...\|disarm` | 临时启用高风险电话节点命令 |
| `/voice status\|list\|set <voiceId>` | 管理 Talk 语音配置。Discord 原生名：`/talkvoice` |
| `/card ...` | 发送 LINE rich card 预设。见 [LINE](/channels/line) |
| `/codex status\|models\|threads\|resume\|compact\|review\|diagnostics\|account\|mcp\|skills` | 控制 Codex app-server 外部执行器。见 [Codex harness](/plugins/codex-harness) |

QQBot 专用：`/bot-ping`、`/bot-version`、`/bot-help`、`/bot-upgrade`、`/bot-logs`

### Skill 命令

> User-invocable skills are exposed as slash commands:

用户可调用的 skill 作为斜杠命令暴露：

- `/skill <name> [input]` 始终作为通用入口可用。
- Skill 可注册为直接命令（如 OpenProse 的 `/prose`）。
- 原生 skill 命令注册由 `commands.nativeSkills` 和 `channels.<provider>.commands.nativeSkills` 控制。
- 名称净化为 `a-z0-9_`（最大 32 字符）；冲突加数字后缀。

Skill 命令分发：默认 skill 命令路由到模型作为正常请求。Skill 可声明 `command-dispatch: tool` 直接路由到工具（确定性,无模型介入）。例：`/prose`（OpenProse 插件）。

原生命令参数：Discord 对动态选项用自动完成,必需参数省略时用按钮菜单。Telegram 和 Slack 对有选择的命令显示按钮菜单。动态选择根据目标会话模型解析,所以 `/think` 级别等模型特定选项跟随会话的 `/model` 覆盖。

## `/tools` —— agent 现在能用什么

> `/tools` answers a runtime question...

`/tools` 回答运行时问题：**这个 agent 在这个对话中现在能用什么** —— 不是静态配置目录。

```text
/tools         # 紧凑视图
/tools verbose # 带简短说明
```

结果是会话范围的。改 agent、频道、帖子、发送者授权或模型可能改变输出。Profile 和覆盖编辑用 Control UI Tools 面板或配置表面。

## `/model` —— 模型选择

```text
/model             # 显示模型选择器
/model list        # 同上
/model 3           # 按选择器中的编号选
/model openai/gpt-5.4
/model opus@anthropic:default
/model status      # 含端点和 API 模式的详细视图
```

Discord 上 `/model` 和 `/models` 打开带提供商和模型下拉的交互选择器。选择器尊重 `agents.defaults.models`,含 `provider/*` 条目。

## `/config` —— 磁盘配置写入

注意：仅 Owner。默认禁用——用 `commands.config: true` 启用。

```text
/config show
/config show messages.responsePrefix
/config get messages.responsePrefix
/config set messages.responsePrefix="[openclaw]"
/config unset messages.responsePrefix
```

写前验证配置。无效变更被拒绝。`/config` 更新跨重启持久化。

## `/mcp` —— MCP 服务器配置

注意：仅 Owner。默认禁用——用 `commands.mcp: true` 启用。

```text
/mcp show
/mcp show context7
/mcp set context7={"command":"uvx","args":["context7-mcp"]}
/mcp unset context7
```

`/mcp` 在 OpenClaw 配置中存储配置,不在嵌入式 agent 项目设置中。

## `/debug` —— 仅运行时覆盖

注意：仅 Owner。默认禁用——用 `commands.debug: true` 启用。覆盖对新配置读取立即生效但**不**写磁盘。

```text
/debug show
/debug set messages.responsePrefix="[openclaw]"
/debug set channels.whatsapp.allowFrom=["+1555","+4477"]
/debug unset messages.responsePrefix
/debug reset
```

## `/plugins` —— 插件管理

注意：写操作仅 Owner。默认禁用——用 `commands.plugins: true` 启用。

```text
/plugins
/plugins list
/plugin show context7
/plugins enable context7
/plugins disable context7
/plugins install ./path/to/plugin
```

`/plugins enable|disable` 更新插件配置并热重载 Gateway 插件运行时用于新 agent 轮次。`/plugins install` 因插件源模块变更自动重启受管 Gateway。

## `/trace` —— 插件 trace 输出

```text
/trace          # 显示当前 trace 状态
/trace on
/trace off
```

`/trace` 显示会话范围的插件 trace/debug 行,无需完整 verbose 模式。不替代 `/debug`（运行时覆盖）或 `/verbose`（正常工具输出）。

## `/btw` —— 旁问

> `/btw` is a quick side question about the current session context.

`/btw` 是关于当前会话上下文的快速旁问。别名：`/side`。

```text
/btw what are we doing right now?
/side what changed while the main run continued?
```

与普通消息不同：

- 用当前会话作为背景上下文。
- Codex harness 会话中作为临时 Codex 侧线程运行。
- **不**改变未来会话上下文。
- 不写入记录历史。

完整行为见 [BTW side questions](/tools/btw)。

## 表面说明

会话范围按表面：

- **文本命令：** 在正常聊天会话中运行（DM 共享 `main`,群组有自己的会话）。
- **原生 Discord 命令：** `agent:<agentId>:discord:slash:<userId>`
- **原生 Slack 命令：** `agent:<agentId>:slack:slash:<userId>`（前缀可通过 `channels.slack.slashCommand.sessionPrefix` 配置）
- **原生 Telegram 命令：** `telegram:slash:<userId>`（通过 `CommandTargetSessionKey` 定向聊天会话）
- **`/stop`** 定向活跃聊天会话以中止当前运行。

Slack 特有：`channels.slack.slashCommand` 支持单个 `/openclaw` 式命令。`commands.native: true` 时每个内置命令创建一个 Slack 斜杠命令。注册 `/agentstatus`（非 `/status`）因 Slack 保留了 `/status`。Slack 消息中文本 `/status` 仍可用。

快速路径和内联快捷方式：

- 白名单发送者的纯命令消息立即处理（绕过队列 + 模型）。
- 内联快捷方式（`/help`、`/commands`、`/status`、`/whoami`）也在普通消息中嵌入工作,模型看到剩余文本前被剥离。
- 未授权的纯命令消息被静默忽略；内联 `/...` token 被当纯文本。

参数说明：

- 命令接受命令和参数间的可选 `:`（`/think: high`、`/send: on`）。
- `/new <model>` 接受模型别名、`provider/model` 或提供商名（模糊匹配）；无匹配时文本被当消息正文。
- `/allowlist add|remove` 需要 `commands.config: true` 并尊重频道 `configWrites`。

## 提供商用量和状态

- **提供商用量/配额**（如"Claude 80% left"）在启用用量追踪时显示在 `/status` 中。
- `/status` 中的**令牌/缓存行**在活会话快照稀疏时可回退到最新记录用量条目。
- **执行 vs 运行时：** `/status` 报告 `Execution` 为有效沙箱路径,`Runtime` 为谁在跑会话：`OpenClaw Default`、`OpenAI Codex`、CLI 后端或 ACP 后端。
- **每响应令牌/成本：** 由 `/usage off|tokens|full` 控制。
- `/model status` 是关于模型/认证/端点,不是用量。

## 相关

- [Skills](/tools/skills) —— Skill 斜杠命令如何注册和门控。
- [Creating skills](/tools/creating-skills) —— 构建注册自己斜杠命令的 skill。
- [BTW](/tools/btw) —— 不改会话上下文的旁问。
- [Steer](/tools/steer) —— 用 `/steer` 引导运行中的 agent。
