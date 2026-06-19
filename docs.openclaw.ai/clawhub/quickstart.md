# Quickstart / 快速开始

## 架构精读

> 跳过不影响阅读翻译正文。

### 消费端 vs 发布端——为什么需要两条工作流？

Quickstart 页面展示了 ClawHub 的两条独立工作流：

**消费端**（用户安装技能）：`openclaw skills search` → `openclaw skills install` → `openclaw skills update`。这是只读路径——从注册表拉取元数据和文件，不需要认证。跟 `apt search` → `apt install` → `apt upgrade` 一个思路。

**发布端**（作者发布技能）：`clawhub login` → `clawhub publish` → `clawhub sync`。这是写路径——需要 GitHub OAuth 认证，推送文件到注册表。跟 `npm login` → `npm publish` 一个思路。

分离的核心原因是**认证边界**。消费端不需要知道发布者的身份；发布端需要验证作者身份。如果合一（比如所有操作都走 `openclaw`），要么每个用户都要 GitHub 认证（过度权限），要么发布操作没有认证（安全风险）。

### Skill slug 作为唯一标识

`openclaw skills install <skill-slug>` 里的 slug 是全局唯一的——类似 npm 的包名、Docker Hub 的镜像名。注册表保证同一 slug 不会有两个不同的技能。这是注册表的基本契约：名字 → 唯一实体。

跟域名系统（DNS）的约束一样：同一个域名不能指向两个不同的 IP。注册表的职责就是维护这个一对一映射，并处理版本迭代（同一 slug 的不同版本）。

---

ClawHub is a registry for OpenClaw skills and plugins.

ClawHub 是 OpenClaw 技能和插件的注册表。

Use **OpenClaw** when you are installing things into OpenClaw. Use the **`clawhub` CLI** when you are signing in, publishing, managing your own listings, or using registry-specific workflows.

安装到 OpenClaw 时使用 **OpenClaw** 命令。登录、发布、管理自己的列表或使用注册表特定工作流时使用 **`clawhub` CLI**。

## Find and install a skill / 查找和安装技能

Search from OpenClaw:

从 OpenClaw 搜索:

```bash
openclaw skills search "calendar"
```

Install a skill:

安装技能:

```bash
openclaw skills install <skill-slug>
```

Update installed skills:

更新已安装的技能:

```bash
openclaw skills update --all
```

OpenClaw records where the skill came from so later updates can continue to resolve through ClawHub.

OpenClaw 记录技能来源,后续更新可继续通过 ClawHub 解析。

## Find and install a plugin / 查找和安装插件

Search from OpenClaw:

从 OpenClaw 搜索:

```bash
openclaw plugins search "calendar"
```

Install a ClawHub-hosted plugin with an explicit ClawHub source:

使用显式 ClawHub 源安装 ClawHub 托管的插件:

```bash
openclaw plugins install clawhub:<package>
```

Update installed plugins:

更新已安装的插件:

```bash
openclaw plugins update --all
```

Use the `clawhub:` prefix when you want OpenClaw to resolve the package through ClawHub rather than npm or another source.

当你希望 OpenClaw 通过 ClawHub 而非 npm 或其他源解析包时,使用 `clawhub:` 前缀。

## Sign in for publishing / 登录以发布

Install the ClawHub CLI:

安装 ClawHub CLI:

```bash
npm i -g clawhub
# or
pnpm add -g clawhub
```

Sign in with GitHub:

使用 GitHub 登录:

```bash
clawhub login
clawhub whoami
```

Headless environments can use an API token from the ClawHub web UI:

无头环境可以使用 ClawHub Web UI 的 API token:

```bash
clawhub login --token clh_...
```

## Publish a skill / 发布技能

A skill is a folder with a required `SKILL.md` file and optional supporting files.

技能是一个包含必需的 `SKILL.md` 文件和可选支持文件的文件夹。

```bash
clawhub skill publish ./my-skill \
  --slug my-skill \
  --name "My Skill" \
  --version 1.0.0 \
  --changelog "Initial release"
```

Before publishing, check the metadata in `SKILL.md`. Declare required environment variables, tools, and permissions so users can understand what the skill needs before they install it. See [Skill format](/clawhub/skill-format).

发布前检查 `SKILL.md` 中的元数据。声明所需的环境变量、工具和权限,让用户在安装前了解技能需要什么。参见[技能格式](/clawhub/skill-format)。

## Publish a plugin / 发布插件

Publish a plugin from a local folder, a GitHub repo, a GitHub ref, or an existing archive:

从本地文件夹、GitHub 仓库、GitHub 引用或现有归档发布插件:

```bash
clawhub package publish <source> --family code-plugin --dry-run
clawhub package publish <source> --family code-plugin
```

Use `--dry-run` first to preview the resolved package metadata, compatibility fields, source attribution, and upload plan without publishing.

先使用 `--dry-run` 预览解析后的包元数据、兼容性字段、源归属和上传计划,不实际发布。

Code plugins must include OpenClaw compatibility metadata in `package.json`, including `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion`.

代码插件必须在 `package.json` 中包含 OpenClaw 兼容性元数据,包括 `openclaw.compat.pluginApi` 和 `openclaw.build.openclawVersion`。

## Sync skills you maintain / 同步你维护的技能

`sync` scans skill folders and publishes new or changed skills that are not already synchronized.

`sync` 扫描技能文件夹并发布未同步的新增或变更技能。

```bash
clawhub sync --all --dry-run
clawhub sync --all
```

For catalog repos, ClawHub also provides a reusable GitHub workflow. By default it scans `skills/`; pass `skill_path` to process one folder.

对于目录仓库,ClawHub 还提供可复用的 GitHub 工作流。默认扫描 `skills/`;传递 `skill_path` 处理单个文件夹。

```yaml
jobs:
  dry-run:
    uses: openclaw/clawhub/.github/workflows/skill-publish.yml@v1
    with:
      owner: nvidia
      dry_run: true
```

## Inspect before installing / 安装前检查

Before installing, use the ClawHub web page or CLI detail commands to inspect metadata, source links, versions, changelogs, and scan status:

安装前,使用 ClawHub 网页或 CLI 详情命令检查元数据、源链接、版本、变更日志和扫描状态:

```bash
clawhub inspect <skill-slug>
clawhub package inspect <package>
```

Public listings show the latest scan state. Releases that are held or blocked by moderation may be hidden from search and install surfaces until resolved.

公共列表显示最新扫描状态。被保留或被审核阻止的版本在解决前可能从搜索和安装界面隐藏。

## 相关 / Related

- [CLI](/clawhub/cli) — ClawHub CLI 命令参考
- [Publishing](/clawhub/publishing) — 发布流程和所有者作用域
- [Skill format](/clawhub/skill-format) — 技能文件夹格式和元数据
- [HTTP API](/clawhub/http-api) — 注册表 API 端点
