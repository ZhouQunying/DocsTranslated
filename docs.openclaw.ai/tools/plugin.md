# Plugin

## 架构精读

> 跳过不影响阅读翻译正文。

### 你装了一个插件,Gateway 怎么知道要加载它？

类比 VS Code 扩展：装了 `.vsix` 只是把文件放到了目录;编辑器重启后才扫描并注册命令面板项。OpenClaw 的插件也一样——`install` 只是把代码放好 + 写一条注册记录,真正生效要等 Gateway restart/reload 把代码 import 到进程里。

所以"装了但没生效"是最常见的故障模式。`plugins list` 读的是冷注册表（磁盘上的清单）,跟运行中的 Gateway 进程加载了什么是两件事。要验证"活 Gateway 确实跑着这个插件",得用 `inspect --runtime`。

来源多态也是一个设计点。ClawHub / npm / git / 本地路径四种来源,但最终都落到同一个注册表结构里。说白了跟 Docker 拉镜像一样：不管从哪个 registry 拉,本地都是同一种 layer 格式。

还有一个隐藏的优先级链：裸包名先匹配内置 → 再匹配官方外部 → 最后走 npm。这避免了社区包仿冒内置插件 ID 的供应链攻击。

---

> Plugins extend OpenClaw with channels, model providers, agent harnesses, tools,
> skills, speech, realtime transcription, voice, media understanding, generation,
> web fetch, web search, and other runtime capabilities.

插件给 OpenClaw 扩展通道、模型 provider、agent harness、工具、技能、语音、实时转录、媒体理解、生成、web 抓取、web 搜索等运行时能力。

> Use this page when you want to install a plugin, restart the Gateway, verify
> that the runtime loaded it, and route common setup failures. For command-only
> examples, see Manage plugins. For the full generated inventory of bundled,
> official external, and source-only plugins, see Plugin inventory.

装插件、重启 Gateway、验证运行时加载、以及排查常见故障时看这页。只看命令示例见 [Manage plugins](/plugins/manage-plugins)。完整的内置、官方外部、纯源码插件清单见 [Plugin 清单](/plugins/plugin-inventory)。

## 前置条件

> Before installing a plugin, make sure you have:

装插件前确保你有:

> - an OpenClaw checkout or installation with the `openclaw` CLI available
> - network access to the selected source, such as ClawHub, npm, or a git host
> - any plugin-specific credentials, config keys, or operating-system tools named by that plugin's setup docs
> - permission for the Gateway that serves your channels to reload or restart

- OpenClaw checkout 或安装,`openclaw` CLI 可用
- 到选定来源（ClawHub、npm、git 主机）的网络访问
- 插件文档要求的凭证、配置键、操作系统工具
- 为你通道服务的 Gateway 的 reload 或 restart 权限

## 快速开始

> Find the plugin

[步骤 1: 找插件]

> Search ClawHub for public plugin packages:

在 [ClawHub](/clawhub) 搜索公开插件包:

```bash
openclaw plugins search "calendar"
```

> ClawHub is the primary discovery surface for community plugins. During the launch cutover, ordinary bare package specs still install from npm unless they match an official plugin id. Raw `@openclaw/*` package specs that match bundled plugins use the bundled copy from the current OpenClaw build. Use an explicit prefix when you need one source.

ClawHub 是社区插件的主要发现入口。上线切换期间,普通裸包名仍从 npm 安装,除非匹配官方插件 id。匹配内置插件的 `@openclaw/*` 裸包名使用当前 OpenClaw 构建的内置副本。需要指定来源时用显式前缀。

> Install the plugin

[步骤 2: 安装插件]

```bash
# 从 ClawHub
openclaw plugins install clawhub:<package>

# 从 npm
openclaw plugins install npm:<package>

# 从 git
openclaw plugins install git:github.com/<owner>/<repo>@<ref>

# 从本地开发 checkout
openclaw plugins install ./my-plugin
openclaw plugins install --link ./my-plugin
```

> Treat plugin installs like running code. Prefer pinned versions when you need reproducible production installs.

把插件安装当成跑代码对待。需要可复现的生产安装时用固定版本。

> Configure and enable it

[步骤 3: 配置并启用]

> Configure plugin-specific settings under `plugins.entries.<id>.config`. Enable the plugin when it is not already enabled:

在 `plugins.entries.<id>.config` 下配插件特定设置。插件未启用时启用它:

```bash
openclaw plugins enable <plugin-id>
```

> If your config uses a restrictive `plugins.allow` list, the installed plugin id must be present there before the plugin can load. `openclaw plugins install` adds the installed id to an existing `plugins.allow` list and removes the same id from `plugins.deny` so the explicit install can load after restart.

配置用了限制性 `plugins.allow` 列表时,安装的插件 id 必须在里面才能加载。`openclaw plugins install` 会把安装的 id 加到已有 `plugins.allow` 列表并从 `plugins.deny` 移除,让显式安装在重启后能加载。

> Let the Gateway reload

[步骤 4: 让 Gateway 重新加载]

> Installing, updating, or uninstalling plugin code requires a Gateway restart. When a managed Gateway is already running with config reload enabled, OpenClaw detects the changed plugin install record and restarts the Gateway automatically. If the Gateway is not managed or reload is disabled, restart it yourself:

安装、更新、卸载插件代码需要 Gateway 重启。受管 Gateway 已在跑且启用了配置 reload 时,OpenClaw 检测到插件安装记录变化会自动重启。非受管或 reload 关闭时,自己重启:

```bash
openclaw gateway restart
```

> Enable and disable operations update config and refresh the cold registry. A runtime inspect is still the clearest verification path for live runtime surfaces.

enable/disable 操作更新配置并刷新冷注册表。运行时 inspect 仍是验证活运行时面的最清晰路径。

> Verify runtime registration

[步骤 5: 验证运行时注册]

```bash
openclaw plugins inspect <plugin-id> --runtime --json
```

> Use `--runtime` when you need to prove registered tools, hooks, services, Gateway methods, or plugin-owned CLI commands. Plain `inspect` is a cold manifest and registry check.

需要证明已注册的工具、钩子、服务、Gateway 方法、或插件持有的 CLI 命令时用 `--runtime`。不加的 `inspect` 是冷清单和注册表检查。

## 配置

### 选择安装来源

| 来源        | 场景                                                    | 示例                                                           |
| ----------- | ------------------------------------------------------- | -------------------------------------------------------------- |
| ClawHub     | 想要 OpenClaw 原生发现、扫描、版本元数据、安装提示      | `openclaw plugins install clawhub:<package>`                   |
| npm         | 需要直接 npm registry 或 dist-tag 工作流                | `openclaw plugins install npm:<package>`                       |
| git         | 需要仓库的分支、tag、或 commit                          | `openclaw plugins install git:github.com/<owner>/<repo>@<ref>` |
| 本地路径    | 在同一台机器上开发或测试插件                            | `openclaw plugins install --link ./my-plugin`                  |
| marketplace | 安装 Claude 兼容的 marketplace 插件                     | `openclaw plugins install <plugin> --marketplace <source>`     |

> Bare package specs have special compatibility behavior...

裸包名有特殊兼容行为。匹配内置插件 id 时用内置来源。匹配官方外部插件 id 时用官方包目录。其他普通裸包名在上线切换期间走 npm 安装。匹配内置插件的 `@openclaw/*` 裸包名也先解析到内置副本再 npm 回退。故意要外部 npm 包而非镜像内置时用 `npm:@openclaw/<plugin>@<version>`。需要确定性来源选择时用 `clawhub:`、`npm:`、`git:`、或 `npm-pack:`。完整命令契约见 [`openclaw plugins`](/cli/plugins#install)。

> For npm installs, unpinned package specs and `@latest` choose the newest stable package that advertises compatibility with this OpenClaw build...

npm 安装中,未固定包名和 `@latest` 选声明与当前 OpenClaw 构建兼容的最新稳定包。如果 npm 的当前 latest 声明了更新的 `openclaw.compat.pluginApi` 或 `openclaw.install.minHostVersion`,OpenClaw 扫描旧稳定版,安装兼容的最新版。精确版本和显式通道 tag（如 `@beta`）钉死到选中包,不兼容时失败。

### 运营者安装策略

> Configure `security.installPolicy` to run a trusted local policy command before plugin install or update proceeds...

配置 `security.installPolicy` 在插件安装或更新前跑受信本地策略命令。策略收到元数据加暂存源路径,可以允许或阻止安装。它在插件 `before_install` 钩子之前跑。已废弃的 `--dangerously-force-unsafe-install` 标志为兼容仍接受,但不绕过安装策略、钩子、或 OpenClaw 的内置插件依赖拒绝名单。

共享的 `security.installPolicy` exec schema 见 [Skills config](/tools/skills-config#operator-install-policy-securityinstallpolicy)。

### 配置插件策略

> The common plugin config shape is:

通用插件配置结构:

```json5
{
  plugins: {
    enabled: true,
    allow: ["voice-call"],
    deny: ["untrusted-plugin"],
    load: { paths: ["~/Projects/oss/voice-call-plugin"] },
    slots: { memory: "memory-core" },
    entries: {
      "voice-call": { enabled: true, config: { provider: "twilio" } },
    },
  },
}
```

> Key policy rules:

关键策略规则:

> - `plugins.enabled: false` disables all plugins...

- `plugins.enabled: false` 禁用所有插件,跳过插件发现 / 加载。此时失效的插件引用是惰性的;想让 doctor 清理失效 id 时先重新启用插件。
- `plugins.deny` 优先于 allow 和单插件启用。
- `plugins.allow` 是排他白名单。白名单外的插件工具不可用,即使 `tools.allow` 包含 `"*"`。
- `plugins.entries.<id>.enabled: false` 禁用单个插件但保留配置。
- `plugins.load.paths` 添加显式本地插件文件或目录。受管 `plugins install` 的本地路径必须是插件目录或归档;独立插件文件用 `plugins.load.paths`。
- 工作区来源的插件默认禁用;使用本地工作区代码前先显式启用或加白名单。
- 内置插件遵循内置的默认开 / 默认关元数据,除非配置显式覆盖。
- `plugins.slots.<slot>` 为独占类别（如 memory 和 context 引擎）选一个插件。Slot 选择强制启用选中插件;但 `plugins.deny` 和 `plugins.entries.<id>.enabled: false` 仍能阻止。
- 内置 opt-in 插件在配置命名了其管理的某个面（provider/model ref、通道配置、CLI 后端、agent harness 运行时）时可自动激活。
- OpenAI 系 Codex 路由保持 provider 和运行时插件边界分离:旧 Codex model ref 是旧配置由 doctor 修复;内置 `codex` 插件负责规范 `openai/*` agent ref、显式 `agentRuntime.id: "codex"`、以及旧 `codex/*` ref 的 Codex app-server 运行时。

> Run `openclaw doctor` or `openclaw doctor --fix` when config validation reports stale plugin ids, allowlist/tool mismatches, or legacy bundled plugin paths.

配置验证报告失效插件 id、白名单 / 工具不匹配、或旧内置插件路径时跑 `openclaw doctor` 或 `openclaw doctor --fix`。

## 理解插件格式

> OpenClaw recognizes two plugin formats:

OpenClaw 认两种插件格式:

| 格式               | 加载方式                                                  | 场景                                            |
| ------------------ | --------------------------------------------------------- | ----------------------------------------------- |
| Native OpenClaw 插件 | `openclaw.plugin.json` + 进程内加载的运行时模块          | 安装或构建 OpenClaw 专属运行时能力              |
| Compatible bundle  | Codex、Claude、Cursor 插件布局映射到 OpenClaw 插件清单    | 复用兼容的技能、命令、钩子、或 bundle 元数据    |

> Both formats appear in `openclaw plugins list`...

两种格式都出现在 `openclaw plugins list`、`inspect`、`enable`、`disable`。Bundle 兼容边界见 [Plugin bundles](/plugins/bundles);原生插件编写见 [Building plugins](/plugins/building-plugins)。

## 插件钩子

> Plugins can register hooks at runtime, but there are two different APIs with different jobs.

插件可以在运行时注册钩子,但有两套不同用途的 API。

> - Use typed hooks via `api.on(...)` for runtime lifecycle hooks...
> - Use `api.registerHook(...)` only when you want to participate in the internal hook system...

- 运行时生命周期钩子用 `api.on(...)` 的类型化钩子。这是中间件、策略、消息改写、prompt 整形、工具控制的首选面。
- 只有想参与 [Hooks](/automation/hooks) 描述的内部钩子系统时才用 `api.registerHook(...)`。主要用于粗粒度命令 / 生命周期副作用和旧钩子风格自动化兼容。

> Quick rule:

速记:

> - If the handler needs priority, merge semantics, or block/cancel behavior, use typed plugin hooks.
> - If the handler just reacts to `command:new`, `command:reset`, `message:sent`, or similar coarse events, `api.registerHook(...)` is fine.

- handler 需要优先级、合并语义、或阻断 / 取消行为 → 类型化插件钩子。
- handler 只对 `command:new`、`command:reset`、`message:sent` 等粗事件做反应 → `api.registerHook(...)` 就行。

> Plugin-managed internal hooks show up in `openclaw hooks list` with `plugin:<id>`. You cannot enable or disable them through `openclaw hooks`; enable or disable the plugin instead.

插件管理的内部钩子在 `openclaw hooks list` 显示为 `plugin:<id>`。不能通过 `openclaw hooks` 启禁;启禁插件本体。

## 验证活 Gateway

> `openclaw plugins list` and plain `openclaw plugins inspect` read cold config, manifest, and registry state. They do not prove that an already-running Gateway has imported the same plugin code.

`openclaw plugins list` 和不带参数的 `inspect` 读的是冷配置、清单、注册表。它们不能证明已经在跑的 Gateway import 了同样的插件代码。

> When a plugin appears installed but live chat traffic does not use it:

插件显示已安装但实时聊天流量没用它时:

```bash
openclaw gateway status --deep --require-rpc
openclaw plugins inspect <plugin-id> --runtime --json
openclaw gateway restart
```

> Managed Gateways restart automatically after plugin install, update, and uninstall changes...

受管 Gateway 在插件安装、更新、卸载改变插件源后自动重启。VPS 或容器安装上,确保手动重启的是实际服务通道的 `openclaw gateway run` 子进程,不只是包装器或 supervisor。

## 故障排查

| 症状                                         | 检查                                                                                  | 修复                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 插件在 `plugins list` 但运行时钩子不跑       | `inspect <id> --runtime --json` + `gateway status --deep --require-rpc`               | 安装 / 更新 / 配置 / 源变更后重启活 Gateway                        |
| 出现重复通道或工具归属诊断                   | `plugins list --enabled --verbose`,inspect 比较通道 / 工具归属                        | 禁用一方,移除失效安装,或用 manifest `preferOver` 做有意替换       |
| 配置说插件缺失                               | 查 [Plugin 清单](/plugins/plugin-inventory) 确认是内置、官方外部、还是纯源码           | 安装外部包、启用内置插件、或移除失效配置                            |
| 安装时配置无效                               | 读验证消息 + `openclaw doctor --fix`                                                  | doctor 可隔离无效插件配置                                           |
| 插件路径因可疑归属或权限被阻止               | 看诊断消息                                                                            | 修文件系统归属 / 权限,再 `plugins registry --refresh`              |
| `OPENCLAW_NIX_MODE=1` 阻止生命周期命令       | 确认安装由 Nix 管理                                                                   | 在 Nix 源改插件选择,不用插件 mutator 命令                          |
| 运行时依赖导入失败                           | 检查插件是走 npm/git/ClawHub 安装还是从本地路径加载                                   | `plugins update <id>`,重装源,或自己安装本地插件依赖               |

> When stale plugin config still names a no-longer-discoverable channel plugin...

失效插件配置仍命名了不可发现的通道插件时,Gateway 启动跳过该插件支持的通道而不阻塞其他通道。跑 `openclaw doctor --fix` 移除失效插件和通道条目。没有失效插件证据的未知通道 key 仍验证失败,拼写错误保持可见。

> For intentional channel replacement...

有意做通道替换时,首选插件应在 manifest 声明 `channelConfigs.<channel-id>.preferOver` 加旧 / 低优先级插件 id。两个插件都显式启用时,OpenClaw 保留该请求并报告重复诊断,而不是静默选一方。

> If an installed package reports that it `requires compiled runtime output for TypeScript entry ...`...

安装的包报告 `requires compiled runtime output for TypeScript entry ...` 时,说明包发布时没带 OpenClaw 运行时需要的 JavaScript 文件。等发布者打包了 JS 后更新或重装,或在此之前禁用 / 卸载。

### 被阻止的插件路径归属

> If plugin diagnostics say `blocked plugin candidate: suspicious ownership...`

插件诊断说 `blocked plugin candidate: suspicious ownership (... uid=1000, expected uid=0 or root)` 且配置验证跟着报 `plugin present but blocked` 时,OpenClaw 发现插件文件归属于跟加载进程不同的 Unix 用户。保留插件配置;修文件系统归属或以持有 state 目录的同一用户跑 OpenClaw。

> For Docker installs...

Docker 安装中,官方镜像以 `node`（uid `1000`）运行,所以宿主 bind-mount 的 OpenClaw 配置和工作区目录通常应归 uid `1000`:

```bash
sudo chown -R 1000:1000 /path/to/openclaw-config /path/to/openclaw-workspace
```

> If you intentionally run OpenClaw as root...

故意以 root 跑时,把受管插件根改为 root 归属:

```bash
sudo chown -R root:root /path/to/openclaw-config/npm
```

修归属后跑 `openclaw doctor --fix` 或 `openclaw plugins registry --refresh` 让持久化插件注册表匹配修复后的文件。

### 慢插件工具初始化

> If agent turns appear to stall while preparing tools...

agent 轮次在准备工具时卡住,启用 trace 日志检查插件工具工厂耗时:

```bash
openclaw config set logging.level trace
openclaw logs --follow
```

> Look for:

找:

```text
[trace:plugin-tools] factory timings ...
```

> The summary lists total factory time and the slowest plugin tool factories...

摘要列出总工厂耗时和最慢的插件工具工厂,含插件 id、声明的工具名、结果形状、是否可选。单工厂 ≥1s 或总工厂耗时 ≥5s 时慢行提升为警告。

> OpenClaw caches successful plugin tool factory results...

OpenClaw 缓存成功的插件工具工厂结果。缓存 key 含运行时配置、工作区、agent/session id、沙箱策略、浏览器设置等上下文,上下文变了工厂重跑。耗时持续高说明插件在返回工具定义前做了昂贵工作。

> If one plugin dominates the timing...

一个插件占主导时,inspect 其运行时注册:

```bash
openclaw plugins inspect <plugin-id> --runtime --json
```

然后更新、重装、或禁用。插件作者应把昂贵依赖加载移到工具执行路径后面,而不是在工具工厂里做。

依赖根、包元数据验证、注册表记录、启动 reload 行为、旧清理见 [Plugin dependency resolution](/plugins/dependency-resolution)。

## 相关

> - Manage plugins, openclaw plugins, Plugin inventory, Plugin reference, Community plugins, Plugin dependency resolution, Building plugins, Plugin SDK overview, Plugin manifest

- [Manage plugins](/plugins/manage-plugins) —— list、install、update、uninstall、publish 的命令示例。
- [`openclaw plugins`](/cli/plugins) —— 完整 CLI 参考。
- [Plugin 清单](/plugins/plugin-inventory) —— 生成的内置和外部插件列表。
- [Plugin reference](/plugins/reference) —— 生成的逐插件参考页。
- [Community plugins](/plugins/community) —— ClawHub 发现和文档 PR 策略。
- [Plugin dependency resolution](/plugins/dependency-resolution) —— 安装根、注册表记录、运行时边界。
- [Building plugins](/plugins/building-plugins) —— 原生插件编写指南。
- [Plugin SDK overview](/plugins/sdk-overview) —— 运行时注册、钩子、API 字段。
- [Plugin manifest](/plugins/manifest) —— manifest 和包元数据。
