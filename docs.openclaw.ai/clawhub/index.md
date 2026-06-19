# ClawHub

## 架构精读

> 跳过不影响阅读翻译正文。

### 技能和插件注册表——跟 npm / PyPI 有什么区别？

ClawHub 是 OpenClaw 技能和插件的公共注册表，角色跟 npm（Node.js）、PyPI（Python）、Docker Hub（容器）一样。但 AI agent 的"包"跟传统软件的包有一个本质区别：**技能和插件在 agent 的上下文窗口内执行**，能访问对话历史、工具调用链、用户数据。npm 包装在你的 Node.js 进程里，PyPI 包装在你的 Python 进程里——它们能访问的是文件系统和网络。ClawHub 的包装在 agent 的推理链里，能访问的是对话内容和 agent 能力。

这让信任模型完全不同。传统包管理器的安全边界是操作系统——恶意包能做的最坏的事是读你的文件或发网络请求。ClawHub 的安全边界是 agent 的工具权限——恶意技能能做的最坏的事是操纵 agent 行为（提示注入）、泄露对话数据、或滥用工具调用。

### 两个 CLI 的分离——为什么不是合一？

OpenClaw 把 CLI 拆成两个：`openclaw`（消费端：搜索、安装、更新）和 `clawhub`（发布端：认证、发布、同步、删除）。

这跟 Terraform 的分离是一个思路：`terraform` CLI 做 `plan`/`apply`（消费模块），Registry API 做发布和版本管理。消费者不需要知道发布者的认证机制；发布者不需要知道消费者的运行时环境。

合一的代价是**权限膨胀**——一个既消费又发布的 CLI 需要同时持有两种身份凭证。分离后，普通用户只需要 `openclaw`（无需 GitHub 认证），发布者额外安装 `clawhub`（需要 GitHub OAuth）。最小权限原则。

### 发现、安装、更新的闭环

`openclaw skills search` → `openclaw skills install` → `openclaw skills update --all` 是一个完整的生命周期闭环。跟 `apt search` → `apt install` → `apt upgrade` 是同一个模式。

但 agent 技能没有传统意义上的"依赖解析"——npm 需要解 `package.json` 的依赖树，ClawHub 不需要。因为技能是自包含的（一个 SKILL.md 文件 + 可能的附件），不依赖其他技能。这大幅简化了注册表的设计——不需要版本冲突解决、不需要依赖锁定、不需要 `node_modules` 地狱。

---

ClawHub is the public registry for OpenClaw skills and plugins.

ClawHub 是 OpenClaw 技能和插件的公共注册表。

- Use native `openclaw` commands to search, install, and update skills and to install plugins from ClawHub.
  
  使用原生 `openclaw` 命令搜索、安装和更新技能以及从 ClawHub 安装插件。

- Use the separate `clawhub` CLI for registry auth, publishing, sync, and delete/undelete workflows.
  
  使用独立的 `clawhub` CLI 进行注册表认证、发布、同步和删除/恢复工作流。

Site: [clawhub.ai](https://clawhub.ai)

## Quick start / 快速开始

Search and install skills with OpenClaw:

使用 OpenClaw 搜索和安装技能:

```bash
openclaw skills search "calendar"
openclaw skills install <skill-slug>
openclaw skills update --all
```

Search and install plugins with OpenClaw:

使用 OpenClaw 搜索和安装插件:

```bash
openclaw plugins search "calendar"
openclaw plugins install clawhub:<package>
openclaw plugins update --all
```

Install the ClawHub CLI when you want registry-authenticated workflows such as publish, sync, or delete/undelete:

当你需要注册表认证的工作流如发布、同步或删除/恢复时安装 ClawHub CLI:

```bash
npm i -g clawhub
# or
pnpm add -g clawhub
```

## What ClawHub hosts / ClawHub 托管什么

ClawHub hosts skills (folders with `SKILL.md`) and plugins (npm-style packages). Install with `openclaw skills install <slug>` or `openclaw plugins install clawhub:<package>`. Publish with `clawhub package publish <source>`.

ClawHub 托管技能(带 `SKILL.md` 的文件夹)和插件(npm 风格包)。使用 `openclaw skills install <slug>` 或 `openclaw plugins install clawhub:<package>` 安装。使用 `clawhub package publish <source>` 发布。

ClawHub tracks semver versions, tags such as `latest`, changelogs, files, downloads, stars, and security scan summaries. Public pages show current registry state so users can inspect a skill or plugin before installing it.

ClawHub 跟踪 semver 版本、如 `latest` 的标签、变更日志、文件、下载、星标和安全扫描摘要。公共页面显示当前注册表状态,以便用户在安装前检查技能或插件。

## Native OpenClaw flows / 原生 OpenClaw 流程

Native OpenClaw commands install into the active OpenClaw workspace and persist source metadata so later update commands can stay on ClawHub.

原生 OpenClaw 命令安装到活跃的 OpenClaw 工作区并持久化源元数据,以便后续更新命令可以保持在 ClawHub 上。

Use `clawhub:<package>` when a plugin install should resolve through ClawHub. Bare npm-safe plugin specs may resolve through npm during launch cutovers, and `npm:<package>` stays npm-only when a source must be explicit.

当插件安装应通过 ClawHub 解析时使用 `clawhub:<package>`。裸 npm 安全插件规格在启动切换期间可能通过 npm 解析,而 `npm:<package>` 在源必须显式时保持仅 npm。

Plugin installs validate advertised `pluginApi` and `minGatewayVersion` compatibility before archive install runs. When a package version publishes a ClawPack artifact, OpenClaw prefers the exact uploaded npm-pack `.tgz`, verifies the ClawHub digest header and downloaded bytes, and records artifact metadata for later updates.

插件安装在归档安装运行前验证宣传的 `pluginApi` 和 `minGatewayVersion` 兼容性。当包版本发布 ClawPack 构建产物时,OpenClaw 优先使用精确上传的 npm-pack `.tgz`,验证 ClawHub 摘要头和下载字节,并记录构建产物元数据供后续更新使用。

## ClawHub CLI / ClawHub CLI

The ClawHub CLI is for registry-authenticated work:

ClawHub CLI 用于注册表认证的工作:

```bash
clawhub login
clawhub whoami
clawhub search "postgres backups"
clawhub skill publish ./my-skill --slug my-skill --name "My Skill" --version 1.0.0
clawhub package explore --family code-plugin
clawhub package inspect episodic-claw
clawhub package publish your-org/your-plugin --dry-run
clawhub package publish your-org/your-plugin
clawhub sync --all
```

The CLI also has skill install/update commands for direct registry workflows:

CLI 还有用于直接注册表工作流的技能安装/更新命令:

```bash
clawhub install <slug>
clawhub update <slug>
clawhub update --all
clawhub list
```

Those commands install skills into `./skills` under the current working directory and record installed versions in `.clawhub/lock.json`.

这些命令将技能安装到当前工作目录下的 `./skills` 并在 `.clawhub/lock.json` 中记录已安装版本。

## Publishing / 发布

Publish skills from a local folder containing `SKILL.md`:

从包含 `SKILL.md` 的本地文件夹发布技能:

```bash
clawhub skill publish <path>
```

Common publish options:

常用发布选项:

- `--slug <slug>`: skill slug.
  
  技能短名称。

- `--name <name>`: display name.
  
  显示名称。

- `--version <version>`: semver version.
  
  semver 版本。

- `--changelog <text>`: changelog text.
  
  变更日志文本。

- `--tags <tags>`: comma-separated tags, defaulting to `latest`.
  
  逗号分隔的标签,默认为 `latest`。

Publish plugins from a local folder, `owner/repo`, `owner/repo@ref`, or a GitHub URL:

从本地文件夹、`owner/repo`、`owner/repo@ref` 或 GitHub URL 发布插件:

```bash
clawhub package publish <source>
```

Use `--dry-run` to build the exact publish plan without uploading, and `--json` for CI-friendly output.

使用 `--dry-run` 构建精确的发布计划而不上传,使用 `--json` 获取 CI 友好的输出。

Code plugins must include the required OpenClaw compatibility metadata in `package.json`, including `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion`. See [CLI](/clawhub/cli) for the full command reference and [Skill format](/clawhub/skill-format) for skill metadata.

代码插件必须在 `package.json` 中包含必需的 OpenClaw 兼容性元数据,包括 `openclaw.compat.pluginApi` 和 `openclaw.build.openclawVersion`。参见 [CLI](/clawhub/cli) 了解完整命令参考和 [技能格式](/clawhub/skill-format) 了解技能元数据。

## Security and moderation / 安全和审核

ClawHub is open by default: anyone can upload, but publishing requires a GitHub account old enough to pass the upload gate. Public detail pages summarize the latest scan state before install or download.

ClawHub 默认开放:任何人都可以上传,但发布需要足够老以通过上传门控的 GitHub 账户。公共详情页在安装或下载前总结最新扫描状态。

ClawHub runs automated checks on published skills and plugin releases. Scan-held or blocked releases may disappear from public catalog and install surfaces while remaining visible to their owner in `/dashboard`.

ClawHub 对已发布的技能和插件版本运行自动化检查。扫描保留或阻止的版本可能从公共目录和安装界面消失,同时对其 owner 在 `/dashboard` 中保持可见。

Signed-in users can report skills and packages. Moderators can review reports, hide or restore content, and ban abusive accounts. See [Security](/security), [Security Audits](/security/audits), [Moderation and Account Safety](/security/moderation), and [Acceptable usage](/clawhub/acceptable-usage) for policy and enforcement details.

已登录用户可以报告技能和包。审核者可以审查报告、隐藏或恢复内容,并禁止滥用账户。参见[安全](/security)、[安全审计](/security/audits)、[审核和账户安全](/security/moderation)和[可接受使用](/clawhub/acceptable-usage)了解政策和执行详情。

## Telemetry and environment / 遥测和环境

When you run `clawhub install` while logged in, the CLI may send a best-effort install event so ClawHub can compute aggregate install counts. Disable this with:

当你在登录状态下运行 `clawhub install` 时,CLI 可能发送尽力而为的安装事件,以便 ClawHub 计算聚合安装计数。禁用方式:

```bash
export CLAWHUB_DISABLE_TELEMETRY=1
```

Useful environment overrides:

有用的环境覆盖:

- `CLAWHUB_SITE`
- `CLAWHUB_REGISTRY`
- `CLAWHUB_CONFIG_PATH`
- `CLAWHUB_WORKDIR`
- `CLAWHUB_DISABLE_TELEMETRY=1`

See [Telemetry](/clawhub/telemetry), [HTTP API](/clawhub/http-api), and [Troubleshooting](/clawhub/troubleshooting) for deeper reference material.

参见[遥测](/clawhub/telemetry)、[HTTP API](/clawhub/http-api)和[故障排除](/clawhub/troubleshooting)了解更深的参考材料。

## 相关 / Related

- [Quickstart](/clawhub/quickstart) — 快速开始
- [CLI](/clawhub/cli) — CLI 命令参考
- [Publishing](/clawhub/publishing) — 发布流程
- [Skill format](/clawhub/skill-format) — 技能格式
- [Auth](/clawhub/auth) — 认证
- [HTTP API](/clawhub/http-api) — API 端点
