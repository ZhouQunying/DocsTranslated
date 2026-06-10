# Skills

## 架构精读

> 跳过不影响阅读翻译正文。

### 技能不是"提示词模板"——它是运行时才组装的指令注入

很多人把 skill 理解成"存个 prompt 模板,用的时候贴进去"。但 OpenClaw 的 skill 系统复杂得多。

关键在于加载时机：skill 不是启动时一次性全加载的。每个 session 开始时做一次快照,之后只在文件变更或新远程节点连接时刷新。说白了跟 Spring Boot 的 `@Configuration` 刷新作用域一样——不是随时热更新的。

第二个设计点是多层优先级。工作区 > 项目 agent > 个人 agent > 受管 > 内置 > 额外目录。跟 CSS 的 specificity 一个道理：同名 skill 在多层出现时,最具体的那层赢。这让你能"用工作区 skill 覆盖内置 skill"而不用改内置代码。

第三个是 gating 机制。skill 可以声明"我需要 `uv` 在 PATH 上"、"我需要 `GEMINI_API_KEY`"——不满足就自动过滤掉,agent 根本看不到。这避免了"模型生成了用某工具的回复,但工具压根不可用"的尴尬。

最后是 token 开销的确定性：每个 skill 往 system prompt 加多少字符是可精确计算的公式。这让运维能做容量规划而不是猜。

---

> Skills are markdown instruction files that teach the agent how and when to use
> tools. Each skill lives in a directory containing a `SKILL.md` file with YAML
> frontmatter and a markdown body. OpenClaw loads bundled skills plus any local
> overrides, and filters them at load time based on environment, config, and
> binary presence.

Skill 是教 agent 怎么用工具、什么时候用的 markdown 指令文件。每个 skill 住在一个含 `SKILL.md` 的目录里,有 YAML frontmatter 和 markdown 正文。OpenClaw 加载内置 skill 加本地覆盖,并在加载时根据环境、配置、二进制存在性过滤。

> CardGroup: Creating skills, Skill Workshop, Skills config, ClawHub

- [创建 skill](/tools/creating-skills) —— 从零构建和测试自定义 skill。
- [Skill Workshop](/tools/skill-workshop) —— 审查和批准 agent 起草的 skill 提案。
- [Skills 配置](/tools/skills-config) —— 完整 `skills.*` 配置 schema 和 agent 白名单。
- [ClawHub](/clawhub) —— 浏览和安装社区 skill。

## 加载顺序

> OpenClaw loads from these sources, highest precedence first. When the same skill name appears in multiple places, the highest source wins.

OpenClaw 从以下来源加载,**最高优先级在前**。同名 skill 出现在多处时,最高层赢。

| 优先级      | 来源                 | 路径                                    |
| ----------- | -------------------- | --------------------------------------- |
| 1 — 最高    | 工作区 skill         | `<workspace>/skills`                    |
| 2           | 项目 agent skill     | `<workspace>/.agents/skills`            |
| 3           | 个人 agent skill     | `~/.agents/skills`                      |
| 4           | 受管 / 本地 skill    | `~/.openclaw/skills`                    |
| 5           | 内置 skill           | 随安装附带                              |
| 6 — 最低    | 额外目录             | `skills.load.extraDirs` + 插件 skill    |

> Skill roots support grouped layouts...

Skill 根支持分组布局。`SKILL.md` 出现在配置根下任何位置时 OpenClaw 都能发现:

```text
<workspace>/skills/research/SKILL.md          ✓ 发现为 "research"
<workspace>/skills/personal/research/SKILL.md ✓ 也发现为 "research"
```

> The folder path is for organization only...

文件夹路径只用于组织。skill 的名称、斜杠命令、白名单 key 都来自 `name` frontmatter 字段（缺失时用目录名）。

> Codex CLI's native `$CODEX_HOME/skills` directory is not an OpenClaw skill root...

[展开: 注意] Codex CLI 的原生 `$CODEX_HOME/skills` 目录**不是** OpenClaw skill 根。用 `openclaw migrate plan codex` 盘点那些 skill,再用 `openclaw migrate codex` 复制到 OpenClaw 工作区。

## 每 agent vs 共享 skill

> In multi-agent setups, each agent has its own workspace...

多 agent 设置中,每个 agent 有自己的工作区。用匹配你期望可见性的路径:

| 范围           | 路径                         | 可见于                      |
| -------------- | ---------------------------- | --------------------------- |
| 单 agent       | `<workspace>/skills`         | 只该 agent                  |
| 项目 agent     | `<workspace>/.agents/skills` | 只该工作区的 agent          |
| 个人 agent     | `~/.agents/skills`           | 本机所有 agent              |
| 共享受管       | `~/.openclaw/skills`         | 本机所有 agent              |
| 额外目录       | `skills.load.extraDirs`      | 本机所有 agent              |

## Agent 白名单

> Skill location (precedence) and skill visibility (which agent can use it) are separate controls...

Skill **位置**（优先级）和 skill **可见性**（哪个 agent 能用）是分开的控制。用白名单限制 agent 看到哪些 skill,不管它们从哪加载。

```json5
{
  agents: {
    defaults: {
      skills: ["github", "weather"], // 共享基线
    },
    list: [
      { id: "writer" }, // 继承 github, weather
      { id: "docs", skills: ["docs-search"] }, // 完全替换 defaults
      { id: "locked-down", skills: [] }, // 无 skill
    ],
  },
}
```

> Allowlist rules:

白名单规则:

- 省略 `agents.defaults.skills` 则默认不限制所有 skill。
- 省略 `agents.list[].skills` 则继承 `agents.defaults.skills`。
- 设 `agents.list[].skills: []` 则该 agent 无 skill。
- 非空 `agents.list[].skills` 列表是**最终**集合——不跟 defaults 合并。
- 生效白名单跨 prompt 构建、斜杠命令发现、沙箱同步、skill 快照应用。

## 插件和 skill

> Plugins can ship their own skills by listing `skills` directories in `openclaw.plugin.json`...

插件可以在 `openclaw.plugin.json` 列 `skills` 目录来附带自己的 skill（相对插件根的路径）。插件启用时其 skill 加载——比如浏览器插件附带 `browser-automation` skill 做多步浏览器控制。

> Plugin skill directories merge at the same low-precedence level as `skills.load.extraDirs`...

插件 skill 目录在跟 `skills.load.extraDirs` 同低优先级合并,所以同名的内置、受管、agent、工作区 skill 会覆盖它们。通过插件配置条目上的 `metadata.openclaw.requires.config` 来门控。

见 [Plugins](/tools/plugin) 和 [Tools](/tools)。

## Skill Workshop

> Skill Workshop is a proposal queue between the agent and your active skill files...

[Skill Workshop](/tools/skill-workshop) 是 agent 和你活跃 skill 文件之间的提案队列。agent 发现可复用的工作时,起草提案而不是直接写 `SKILL.md`。你审查批准后才变更。

```bash
openclaw skills workshop list
openclaw skills workshop inspect <proposal-id>
openclaw skills workshop apply <proposal-id>
```

完整生命周期、CLI 参考、配置见 [Skill Workshop](/tools/skill-workshop)。

## 从 ClawHub 安装

> ClawHub is the public skills registry...

[ClawHub](https://clawhub.ai) 是公开 skill 注册中心。用 `openclaw skills` 命令安装和更新,或 `clawhub` CLI 做发布和同步。

| 操作                              | 命令                                                   |
| --------------------------------- | ------------------------------------------------------ |
| 安装 skill 到工作区               | `openclaw skills install <slug>`                       |
| 从 Git 仓库安装                   | `openclaw skills install git:owner/repo@ref`           |
| 安装本地 skill 目录               | `openclaw skills install ./path/to/skill --as my-tool` |
| 为所有本地 agent 安装             | `openclaw skills install <slug> --global`              |
| 更新工作区所有 skill              | `openclaw skills update --all`                         |
| 更新共享受管 skill                | `openclaw skills update <slug> --global`               |
| 更新所有共享受管 skill            | `openclaw skills update --all --global`                |
| 验证 skill 信任信封               | `openclaw skills verify <slug>`                        |
| 打印生成的 Skill Card             | `openclaw skills verify <slug> --card`                 |
| 通过 ClawHub CLI 发布 / 同步      | `clawhub sync --all`                                   |

> Install details:

安装详情:

`openclaw skills install` 默认装到活跃工作区 `skills/` 目录。加 `--global` 装到共享 `~/.openclaw/skills` 目录,对所有本地 agent 可见（除非 agent 白名单收窄）。

Git 和本地安装期望源根有 `SKILL.md`。slug 来自 `SKILL.md` frontmatter `name`（有效时）,否则回退到目录或仓库名。用 `--as <slug>` 覆盖。`openclaw skills update` 只跟踪 ClawHub 安装——Git 或本地来源要刷新需重装。

> Verification and security scanning:

验证和安全扫描:

`openclaw skills verify <slug>` 向 ClawHub 请求 skill 的 `clawhub.skill.verify.v1` 信任信封。已安装的 ClawHub skill 对照 `.clawhub/origin.json` 中记录的版本和注册中心验证。

ClawHub skill 页在安装前展示最新安全扫描状态,有 VirusTotal、ClawScan、静态分析的详情页。ClawHub 标记验证失败时命令以非零退出。发布者通过 ClawHub 仪表盘或 `clawhub skill rescan <slug>` 恢复误报。

> Private archive installs:

私有归档安装:

需要非 ClawHub 投递的 Gateway 客户端可以用 `skills.upload.begin`、`skills.upload.chunk`、`skills.upload.commit` 暂存 zip skill 归档,再用 `skills.install({ source: "upload", ... })` 安装。此路径默认关闭,需要 `openclaw.json` 中 `skills.install.allowUploadedArchives: true`。正常 ClawHub 安装不需要该设置。

## 安全

> Treat third-party skills as untrusted code. Read them before enabling...

[展开: 警告] 把第三方 skill 当**不可信代码**。启用前先读。不可信输入和高风险工具优先用沙箱运行。见 [Sandboxing](/gateway/sandboxing)。

> Path containment:

路径围栏:

工作区、项目 agent、额外目录的 skill 发现只接受解析后真实路径在配置根内的 skill 根,除非 `skills.load.allowSymlinkTargets` 显式信任了目标根。受管 `~/.openclaw/skills` 和个人 `~/.agents/skills` 可以含符号链接的 skill 文件夹,但每个 `SKILL.md` 真实路径必须仍在其解析后的 skill 目录内。

> Operator install policy:

运营者安装策略:

配置 `security.installPolicy` 在 skill 安装前跑受信本地策略命令。策略收到元数据和暂存源路径,适用于 ClawHub、上传、Git、本地、更新、依赖安装器路径,命令不能返回有效决定时默认拒绝。

> Secret injection scope:

密钥注入范围:

`skills.entries.*.env` 和 `skills.entries.*.apiKey` 把密钥注入到那个 agent 轮次的**宿主**进程——不是沙箱。让密钥远离 prompt 和日志。

更广的威胁模型和安全清单见 [Security](/gateway/security)。

## SKILL.md 格式

> Every skill needs at minimum a `name` and `description` in the frontmatter:

每个 skill 最少需要 frontmatter 中的 `name` 和 `description`:

```markdown
---
name: image-lab
description: Generate or edit images via a provider-backed image workflow
---

When the user asks to generate an image, use the `image_generate` tool...
```

> OpenClaw follows the AgentSkills spec...

[展开: 注意] OpenClaw 遵循 [AgentSkills](https://agentskills.io) 规范。frontmatter 解析器只支持**单行 key**——`metadata` 必须是单行 JSON 对象。正文中用 `{baseDir}` 引用 skill 文件夹路径。

### 可选 frontmatter 字段

- `homepage` —— 在 macOS Skills UI 显示为"Website"的 URL。也支持 `metadata.openclaw.homepage`。
- `user-invocable` —— `true` 时 skill 暴露为用户可调的斜杠命令。
- `agent-only` —— `true` 时 OpenClaw 把 skill 指令排除在 agent 正常 prompt 外。skill 在 `user-invocable` 也为 `true` 时仍可作为斜杠命令使用。
- `command-dispatch` —— 设为 `tool` 时斜杠命令绕过模型直接分发到已注册工具。
- `command-dispatch-tool` —— `command-dispatch: tool` 时要调的工具名。
- `command-dispatch-raw-args` —— 工具分发时,把原始 args 字符串不做核心解析转发给工具。

## Gating

> OpenClaw filters skills at load time using `metadata.openclaw`...

OpenClaw 在加载时用 `metadata.openclaw`（frontmatter 中的单行 JSON）过滤 skill。没 `metadata.openclaw` 块的 skill 除非显式禁用否则总是合格。

```markdown
---
name: image-lab
description: Generate or edit images via a provider-backed image workflow
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["uv"], "env": ["GEMINI_API_KEY"], "config": ["browser.enabled"] },
        "primaryEnv": "GEMINI_API_KEY",
      },
  }
---
```

> Gating fields:

Gating 字段:

- `alwaysInclude` —— `true` 时总包含 skill,跳过所有其他门控。
- `emoji` —— 可选,macOS Skills UI 显示的 emoji。
- `homepage` —— 可选 URL。
- `requires.os` —— 平台过滤。只在列出的 OS 上合格。
- `requires.bins` —— 每个二进制必须在 `PATH` 上。
- `requires.anyBins` —— 至少一个二进制在 `PATH` 上。
- `requires.env` —— 每个环境变量必须存在于进程或通过配置提供。
- `requires.config` —— 每个 `openclaw.json` 路径必须为 truthy。
- `primaryEnv` —— 跟 `skills.entries.<name>.apiKey` 关联的环境变量名。
- `install` —— 可选安装器 spec（brew / node / go / uv / download）。

> Legacy `metadata.clawdbot` blocks are still accepted...

[展开: 注意] 旧 `metadata.clawdbot` 块在 `metadata.openclaw` 缺失时仍接受,让已安装的旧 skill 保留依赖门控和安装器提示。新 skill 应用 `metadata.openclaw`。

### 安装器 spec

> Installer specs tell the macOS Skills UI how to install a dependency:

安装器 spec 告诉 macOS Skills UI 怎么安装依赖。

> Installer selection rules:

安装器选择规则:

- 列了多个安装器时,gateway 选一个首选（brew 可用时选 brew,否则 node）。
- 所有安装器都是 `download` 时,OpenClaw 列出每条。
- Spec 可含 `os: ["darwin"|"linux"|"win32"]` 按平台过滤。
- Node 安装遵循 `openclaw.json` 中的 `skills.install.nodeManager`（默认 npm;选项 npm / pnpm / yarn / bun）。只影响 skill 安装;Gateway 运行时仍应是 Node。
- Gateway 安装器偏好:Homebrew → uv → 配置的 node 管理器 → go → download。

> Per-installer details:

各安装器细节:

- **Homebrew:** OpenClaw 不自动装 Homebrew 也不把 brew formula 翻译成系统包命令。没 `brew` 的 Linux 容器中 brew-only 安装器被隐藏;用自定义镜像或手动装依赖。
- **Go:** `go` 缺失且 `brew` 可用时,gateway 先通过 Homebrew 装 Go 并设 `GOBIN` 到 Homebrew 的 `bin`。
- **Download:** `url`（必填）、`archive`（`tar.gz` | `tar.bz2` | `zip`）、`extract`（默认自动检测）、`stripComponents`、`targetDir`（默认 `~/.openclaw/tools/<skillKey>`）。

> Sandboxing notes:

沙箱注意:

`requires.bins` 在 skill 加载时在**宿主**上检查。agent 跑在沙箱里时,二进制也必须在**容器内**存在。通过 `agents.defaults.sandbox.docker.setupCommand` 或自定义镜像安装。`setupCommand` 在容器创建后跑一次,需要网络出口、可写根 FS、容器内 root 用户。

## 配置覆盖

> Toggle and configure bundled or managed skills under `skills.entries`:

在 `~/.openclaw/openclaw.json` 的 `skills.entries` 下切换和配置内置或受管 skill:

```json5
{
  skills: {
    entries: {
      "image-lab": {
        enabled: true,
        apiKey: { source: "env", provider: "default", id: "GEMINI_API_KEY" },
        env: { GEMINI_API_KEY: "GEMINI_KEY_HERE" },
        config: {
          endpoint: "https://example.invalid",
          model: "nano-pro",
        },
      },
      peekaboo: { enabled: true },
      sag: { enabled: false },
    },
  },
}
```

- `enabled` —— `false` 禁用 skill。`coding-agent` 内置 skill 是 opt-in——设 `skills.entries.coding-agent.enabled: true` 并确保支持的 CLI 已安装认证。
- `apiKey` —— 给声明了 `metadata.openclaw.primaryEnv` 的 skill 用的便捷字段。支持明文字符串或 SecretRef 对象。
- `env` —— agent 运行时注入的环境变量。已在进程中设了的不注入。
- `config` —— 可选的自定义逐 skill 配置字段包。
- `skills.bundledAllow` —— 可选白名单,只对**内置** skill 生效。设了时只有列表中的内置 skill 合格。受管和工作区 skill 不受影响。

[展开: 注意] 配置 key 默认匹配 **skill 名称**。skill 定义了 `metadata.openclaw.skillKey` 时,用该 key 在 `skills.entries` 下配。连字符名用引号。

## 环境注入

> When an agent run starts, OpenClaw:

agent 运行开始时,OpenClaw:

1. **读 skill 元数据** —— 解析该 agent 的生效 skill 列表,应用 gating 规则、白名单、配置覆盖。
2. **注入 env 和 API key** —— `skills.entries.<key>.env` 和 `apiKey` 在运行期间应用到 `process.env`。
3. **构建 system prompt** —— 合格 skill 编译成紧凑 XML 块注入 system prompt。
4. **恢复环境** —— 运行结束后恢复原始环境。

[展开: 警告] env 注入范围是**宿主** agent 运行,不是沙箱。沙箱内 `env` 和 `apiKey` 无效。怎么把密钥传进沙箱运行见 [Skills config](/tools/skills-config#sandboxed-skills-and-env-vars)。

> For the bundled `claude-cli` backend...

内置 `claude-cli` 后端中,OpenClaw 还把同样的合格 skill 快照物化为临时 Claude Code 插件并通过 `--plugin-dir` 传递。其他 CLI 后端只用 prompt 目录。

## 快照和刷新

> OpenClaw snapshots eligible skills when a session starts...

OpenClaw 在 **session 开始时**快照合格 skill,后续该 session 所有轮次复用该列表。skill 或配置变更在下一个新 session 生效。

两种情况下 session 中途刷新:

- skill 观察器检测到 `SKILL.md` 变更。
- 新的合格远程节点连接。

刷新后的列表在下一个 agent 轮次被采用。生效 agent 白名单变了时,OpenClaw 刷新快照以保持可见 skill 对齐。

> Skills watcher config:

skill 观察器配置:

```json5
{
  skills: {
    load: {
      extraDirs: ["~/Projects/agent-scripts/skills"],
      allowSymlinkTargets: ["~/Projects/manager/skills"],
      watch: true,
      watchDebounceMs: 250,
    },
  },
}
```

`allowSymlinkTargets` 用于有意的符号链接布局,即 skill 根符号链接指向配置根外的地方。

> Remote macOS nodes (Linux gateway):

远程 macOS 节点（Linux gateway）:

Gateway 跑在 Linux 但 macOS 节点连了且 `system.run` 允许时,OpenClaw 可以在所需二进制在该节点上存在时把 macOS-only skill 视为合格。agent 应通过 `exec` 工具加 `host=node` 跑那些 skill。

离线节点**不**让仅远程的 skill 可见。节点停止响应 bin 探测时,OpenClaw 清除其缓存的 bin 匹配。

## Token 开销

> When skills are eligible, OpenClaw injects a compact XML block into the system prompt...

skill 合格时,OpenClaw 往 system prompt 注入紧凑 XML 块。开销是确定性的:

```text
total = 195 + Σ (97 + len(name) + len(description) + len(filepath))
```

- **基础开销**（≥1 个 skill 时）:约 195 字符
- **每 skill:** 约 97 字符 + 你的 `name`、`description`、`location` 字段长度
- XML 转义把 `& < > " '` 展开为实体,每个多几个字符
- 按约 4 字符/token,97 字符 ≈ 24 token/skill（不含字段长度）

保持 description 短且有描述性以最小化 prompt 开销。

## 相关

- [创建 skill](/tools/creating-skills) —— 编写自定义 skill 的逐步指南。
- [Skill Workshop](/tools/skill-workshop) —— agent 起草 skill 的提案队列。
- [Skills 配置](/tools/skills-config) —— 完整 `skills.*` 配置 schema 和 agent 白名单。
- [Slash 命令](/tools/slash-commands) —— skill 斜杠命令怎么注册和路由。
- [ClawHub](/clawhub) —— 在公开注册中心浏览和发布 skill。
- [Plugins](/tools/plugin) —— 插件可以随工具附带 skill。
