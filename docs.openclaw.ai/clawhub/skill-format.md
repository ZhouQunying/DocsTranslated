# Skill format / 技能格式

## 架构精读

> 跳过不影响阅读翻译正文。

### SKILL.md 作为唯一入口——为什么不是一个 manifest.json？

技能的核心是 `SKILL.md`——一个带 YAML frontmatter 的 Markdown 文件。没有单独的 `manifest.json`、`package.json` 或 `metadata.yaml`。所有元数据（名称、描述、需求、环境变量）都在 frontmatter 里。

这跟 Helm chart 的 `Chart.yaml` + `values.yaml` 分离不同，更像 Dockerfile 的"一个文件搞定一切"思路。但更极端——Dockerfile 至少还有 `COPY`、`RUN` 等指令，SKILL.md 是纯文本 + 元数据。

优势是**简单**——人类可以直接读 Markdown 理解技能做什么，机器可以解析 frontmatter 获取元数据。不需要两套工具（一套读 manifest，一套读文档）。代价是 frontmatter 可能很长（复杂技能有很多元数据），但这比维护多个文件好。

### 允许的文件类型——为什么限制为文本？

技能文件夹只允许基于文本的文件（Markdown、YAML、JSON、脚本等），不允许二进制文件（图片、编译后的代码、压缩包）。

这是因为技能在 agent 的上下文窗口内执行——agent 需要**读取**技能内容来理解和使用它。二进制文件对 agent 不可读。如果技能需要图片，应该通过 URL 引用而非嵌入。

这跟 Kubernetes ConfigMap 的限制类似——ConfigMap 只能存文本数据（YAML/JSON），二进制数据需要用 Secret 的 base64 编码。但技能更严格——连 base64 都不允许，纯文本 only。

---

## On disk / 磁盘上

A skill is a folder.

技能是一个文件夹。

**Required / 必需:**

- `SKILL.md` (or `skill.md`)

**Optional / 可选:**

- any supporting text-based files (see "Allowed files")
  
  任何支持的基于文本的文件(参见"允许的文件")

- `.clawhubignore` (ignore patterns for publish/sync, legacy `.clawdhubignore`)
  
  `.clawhubignore`(发布/同步的忽略模式,旧版 `.clawdhubignore`)

- `.gitignore` (also honored)
  
  `.gitignore`(也被遵守)

**Local install metadata (written by the CLI) / 本地安装元数据(由 CLI 写入):**

- `<skill>/.clawhub/origin.json` (legacy `.clawdhub`)

**Workdir install state (written by the CLI) / 工作目录安装状态(由 CLI 写入):**

- `<workdir>/.clawhub/lock.json` (legacy `.clawdhub`)

## SKILL.md

- Markdown with optional YAML frontmatter.
  
  带可选 YAML frontmatter 的 Markdown。

- The server extracts metadata from frontmatter during publish.
  
  服务器在发布期间从 frontmatter 提取元数据。

- `description` is used as the skill summary in the UI/search.
  
  `description` 在 UI/搜索中用作技能摘要。

## Frontmatter metadata / Frontmatter 元数据

Skill metadata is declared in the YAML frontmatter at the top of your `SKILL.md`. This tells the registry (and security analysis) what your skill needs to run.

技能元数据在 `SKILL.md` 顶部的 YAML frontmatter 中声明。这告诉注册表(和安全分析)你的技能运行需要什么。

### Basic frontmatter / 基础 frontmatter

```yaml
---
name: my-skill
description: Short summary of what this skill does.
version: 1.0.0
---
```

### Runtime metadata (metadata.openclaw) / 运行时元数据

Declare your skill's runtime requirements under `metadata.openclaw` (aliases: `metadata.clawdbot`, `metadata.clawdis`).

在 `metadata.openclaw` 下声明技能的运行时需求(别名:`metadata.clawdbot`、`metadata.clawdis`)。

```yaml
---
name: my-skill
description: Manage tasks via the Todoist API.
metadata:
  openclaw:
    requires:
      env:
        - TODOIST_API_KEY
      bins:
        - curl
    primaryEnv: TODOIST_API_KEY
---
```

Use `requires.env` for environment variables that must be present before the skill can run. Use `envVars` when you need per-variable metadata, including optional variables with `required: false`.

使用 `requires.env` 声明技能运行前必须存在的环境变量。当需要每个变量的元数据时使用 `envVars`,包括带 `required: false` 的可选变量。

### Full field reference / 完整字段参考

- `requires.env` - `string[]` - required environment variables
  
  必需的环境变量

- `requires.bins` - `string[]` - required binaries
  
  必需的二进制文件

- `requires.anyBins` - `string[]` - at least one of these binaries must exist
  
  这些二进制文件中至少一个必须存在

- `requires.config` - `string[]` - required config keys
  
  必需的配置键

- `primaryEnv` - `string` - the main environment variable for this skill
  
  此技能的主要环境变量

- `envVars` - `array` - detailed variable metadata
  
  详细的变量元数据

- `name` - `string` (required) - skill name
  
  技能名称

- `description` - `string` (required) - skill description
  
  技能描述

- `required: false` - mark variable as optional
  
  标记变量为可选

- `always` - `boolean` - if `true`, always load this skill
  
  如果为 `true`,始终加载此技能

- `skillKey` - `string` - unique skill identifier
  
  唯一技能标识符

- `emoji` - `string` - skill emoji
  
  技能 emoji

- `homepage` - `string` - skill homepage URL
  
  技能主页 URL

- `os` - `string[]` - supported operating systems, e.g. `["macos"]`, `["linux"]`
  
  支持的操作系统

- `install` - `array` - dependency install specs
  
  依赖安装规格

- `nix` - `object` - Nix package specs
  
  Nix 包规格

- `config` - `object` - skill-specific config
  
  技能特定配置

### Install specs / 安装规格

If your skill needs dependencies installed, declare them in the `install` array:

如果你的技能需要安装依赖,在 `install` 数组中声明:

```yaml
metadata:
  openclaw:
    install:
      - kind: brew
        formula: jq
        bins: [jq]
      - kind: node
        package: typescript
        bins: [tsc]
```

Supported install kinds: `brew`, `node`, `go`, `uv`.

支持的安装类型:`brew`、`node`、`go`、`uv`。

### Optional environment variables / 可选环境变量

Declare optional environment variables under `metadata.openclaw.envVars` and set `required: false`. Do not add optional entries to `requires.env`, because `requires.env` means the skill cannot run without them.

在 `metadata.openclaw.envVars` 下声明可选环境变量并设置 `required: false`。不要将可选项添加到 `requires.env`,因为 `requires.env` 表示技能没有它们无法运行。

```yaml
metadata:
  openclaw:
    primaryEnv: TODOIST_API_KEY
    envVars:
      - name: TODOIST_API_KEY
        required: true
        description: Todoist API token used for authenticated requests.
      - name: TODOIST_PROJECT_ID
        required: false
        description: Optional default project ID when the user does not specify one.
```

### Why this matters / 为什么重要

ClawHub's security analysis checks that what your skill declares matches what it actually does. If your code references `TODOIST_API_KEY` but your frontmatter doesn't declare it under `requires.env`, `primaryEnv`, or `envVars`, the analysis will flag a metadata mismatch. Keeping declarations accurate helps your skill pass review and helps users understand what they're installing.

ClawHub 的安全分析检查你的技能声明的内容是否与实际行为匹配。如果你的代码引用 `TODOIST_API_KEY` 但 frontmatter 没有在 `requires.env`、`primaryEnv` 或 `envVars` 下声明它,分析会标记元数据不匹配。保持声明准确有助于你的技能通过审核并帮助用户理解他们安装的是什么。

### Example: complete frontmatter / 示例:完整 frontmatter

```yaml
---
name: todoist-cli
description: Manage Todoist tasks, projects, and labels from the command line.
version: 1.2.0
metadata:
  openclaw:
    requires:
      env:
        - TODOIST_API_KEY
      bins:
        - curl
    primaryEnv: TODOIST_API_KEY
    envVars:
      - name: TODOIST_API_KEY
        required: true
        description: Todoist API token.
      - name: TODOIST_PROJECT_ID
        required: false
        description: Optional default project ID.
    emoji: "✅"
    homepage: https://github.com/example/todoist-cli
---
```

## Allowed files / 允许的文件

Only "text-based" files are accepted by publish.

发布只接受"基于文本"的文件。

- Extension allowlist is in `packages/schema/src/textFiles.ts` (`TEXT_FILE_EXTENSIONS`).
  
  扩展名白名单在 `packages/schema/src/textFiles.ts`(`TEXT_FILE_EXTENSIONS`)。

- Script files are still scanned after upload; PowerShell `.ps1`, `.psm1`, and `.psd1` files are accepted as text.
  
  脚本文件上传后仍会被扫描;PowerShell `.ps1`、`.psm1`、`.psd1` 文件作为文本接受。

- Content types starting with `text/` are treated as text; plus a small allowlist (JSON/YAML/TOML/JS/TS/Markdown/SVG).
  
  以 `text/` 开头的内容类型被视为文本;加上小白名单(JSON/YAML/TOML/JS/TS/Markdown/SVG)。

**Limits (server-side) / 限制(服务器端):**

- Total bundle size: 50MB.
  
  总包大小:50MB。

- Embedding text includes `SKILL.md` + up to ~40 non-`.md` files (best-effort cap).
  
  嵌入文本包括 `SKILL.md` + 最多约 40 个非 `.md` 文件(尽力而为的上限)。

## Slugs / 短名称

- Derived from folder name by default.
  
  默认从文件夹名派生。

- Package scopes must match the ClawHub publisher handle exactly. Publisher handles can use lowercase letters, numbers, hyphens, dots, and underscores; they must start and end with a lowercase letter or number.
  
  包作用域必须完全匹配 ClawHub 发布者句柄。发布者句柄可以使用小写字母、数字、连字符、点和下划线;它们必须以小写字母或数字开头和结尾。

- Package slugs must be lowercase and npm-safe, for example `@example.tools/demo-plugin` or `demo-plugin`.
  
  包短名称必须是小写且 npm 安全的,例如 `@example.tools/demo-plugin` 或 `demo-plugin`。

## Versioning + tags / 版本控制 + 标签

- Each publish creates a new version (semver).
  
  每次发布创建一个新版本(semver)。

- Tags are string pointers to a version; `latest` is commonly used.
  
  标签是指向版本的字符串指针;`latest` 常用。

## License / 许可证

- All skills published on ClawHub are licensed under `MIT-0`.
  
  所有在 ClawHub 上发布的技能都在 `MIT-0` 许可下。

- Anyone may use, modify, and redistribute published skills, including commercially.
  
  任何人都可以使用、修改和重新分发已发布的技能,包括商业用途。

- Attribution is not required.
  
  不需要署名。

- Do not add conflicting license terms in `SKILL.md`; ClawHub does not support per-skill license overrides.
  
  不要在 `SKILL.md` 中添加冲突的许可条款;ClawHub 不支持每个技能的许可覆盖。

## Paid skills / 付费技能

- ClawHub does not support paid skills, per-skill pricing, paywalls, or revenue sharing.
  
  ClawHub 不支持付费技能、按技能定价、付费墙或收入分成。

- Do not add pricing metadata to `SKILL.md`; it is not part of the skill format and will not make a published skill paid.
  
  不要在 `SKILL.md` 中添加定价元数据;它不是技能格式的一部分,不会使已发布的技能变为付费。

- If your skill integrates with a paid third-party service, document the external cost and required account clearly in the skill instructions and env declarations (`requires.env` for required variables, or `envVars` with `required: false` for optional variables).
  
  如果你的技能集成付费第三方服务,在技能说明和环境声明中清楚记录外部成本和所需账户(必需变量用 `requires.env`,可选变量用带 `required: false` 的 `envVars`)。

## 相关 / Related

- [Quickstart](/clawhub/quickstart) — 快速开始发布
- [Publishing](/clawhub/publishing) — 发布流程
- [CLI](/clawhub/cli) — ClawHub CLI 命令
