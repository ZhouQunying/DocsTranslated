# How ClawHub Works / ClawHub 工作原理

## 架构精读

> 跳过不影响阅读翻译正文。

### 注册表记录——每个列表是一个不可变版本链

ClawHub 的每个公共列表是一个**注册表记录**（registry record），包含所有者、slug、一个或多个已发布版本、元数据、文件、源归属、变更日志、安全扫描状态。

这跟 Git 的 commit 链是一个思路：每次发布创建一个**不可变版本记录**。v1.0.0 发布后就不能再改——你想改就发 v1.0.1。这保证了安装的可重复性：`openclaw skills install foo@1.0.0` 永远拿到相同的内容。

不可变版本是包注册表的核心契约。npm 的 `unpublish` 政策（发布 72 小时后不可撤回）、Docker Hub 的 tag 不变性、PyPI 的版本锁定——都是同一个设计：消费者依赖的包不能偷偷被换。

### Skills vs Plugins——两种包类型的本质区别

**Skills** 是以 `SKILL.md` 为中心的**版本化文本包**——可以包含支持文件、示例、模板、脚本。但核心是 Markdown 文件。ClawHub 读 `SKILL.md` 的 frontmatter 了解技能名称、描述、需求、环境变量、元数据。

**Plugins** 是**打包的 OpenClaw 扩展**——包含包元数据、兼容性信息、源链接、artifacts、版本记录。安装时 OpenClaw 检查声明的兼容性元数据（API 兼容性、最低 gateway 版本、宿主目标、环境需求）。

区别在于执行方式：Skills 是**被动文本**（agent 读取并遵循指令），Plugins 是**主动代码**（注册工具、钩子、提供者）。Skills 的安全风险是提示注入（恶意 Markdown 操纵 agent 行为）；Plugins 的安全风险是代码执行（恶意 JavaScript 访问系统资源）。

### 安全扫描——开放发布 + 上传门禁

ClawHub 对发布开放（任何人都能发），但发布仍受**上传门禁**（upload gates）、自动检查、用户报告、管理员操作约束。被扣留、隐藏或阻止的内容从公共搜索和安装流中消失，但对所有者仍可见（用于诊断）。

这跟 GitHub 的模型一样：任何人都能创建仓库，但恶意仓库会被标记、限制或删除。开放发布鼓励生态增长；安全扫描防止恶意包传播。两者必须并存——只有开放发布没有扫描是危险的（npm 的 typosquatting 问题）；只有扫描没有开放发布是封闭的（Apple App Store 的审核瓶颈）。

---

ClawHub is the registry layer for OpenClaw skills and plugins. It gives users a place to discover packages, gives publishers a place to release versions, and gives OpenClaw enough metadata to install and update those packages safely.

ClawHub 是 OpenClaw 技能和插件的注册表层。它为用户提供发现包的场所，为发布者提供发布版本的场所，为 OpenClaw 提供安全安装和更新这些包所需的元数据。

## 注册表记录

Each public listing is a registry record with:

每个公共列表是一个注册表记录，包含：

- an owner and slug or package name
  
  所有者和 slug 或包名

- one or more published versions
  
  一个或多个已发布版本

- metadata, summary, files, and source attribution
  
  元数据、摘要、文件和源归属

- changelog and tag information such as `latest`
  
  变更日志和标签信息（如 `latest`）

- download, install, and star signals
  
  下载、安装和星标信号

- security scan and moderation status
  
  安全扫描和管理状态

The listing page is the canonical place for users to inspect what a skill or plugin claims to do before installing it.

列表页面是用户在安装前检查技能或插件声称做什么的权威场所。

## Skills / 技能

A skill is a versioned text bundle centered on `SKILL.md`. It can include supporting files, examples, templates, and scripts.

技能是以 `SKILL.md` 为中心的版本化文本包。它可以包含支持文件、示例、模板和脚本。

ClawHub reads the `SKILL.md` frontmatter to understand the skill name, description, requirements, environment variables, and metadata. Accurate metadata matters because it helps users decide whether to install the skill and helps automated scans detect mismatches between declared and observed behavior.

ClawHub 读取 `SKILL.md` frontmatter 以了解技能名称、描述、需求、环境变量和元数据。准确的元数据很重要，因为它帮助用户决定是否安装该技能，并帮助自动扫描检测声明行为与实际行为之间的不匹配。

See [Skill format](/clawhub/skill-format).

参见[技能格式](/clawhub/skill-format)。

## Plugins / 插件

Plugins are packaged OpenClaw extensions. ClawHub stores package metadata, compatibility information, source links, artifacts, and version records.

插件是打包的 OpenClaw 扩展。ClawHub 存储包元数据、兼容性信息、源链接、artifacts 和版本记录。

When OpenClaw installs a plugin from ClawHub, it checks advertised compatibility metadata before installing. Package records can include API compatibility, minimum gateway version, host targets, environment requirements, and artifact digests.

当 OpenClaw 从 ClawHub 安装插件时，它在安装前检查声明的兼容性元数据。包记录可以包括 API 兼容性、最低 gateway 版本、宿主目标、环境需求和 artifact 摘要。

Use an explicit ClawHub install source when you want the registry to be the source of truth:

当你希望注册表成为唯一真相来源时，使用显式 ClawHub 安装源：

```bash
openclaw plugins install clawhub:<package>
```

## Publishing / 发布

Publishing creates a new immutable version record. Publishers use the `clawhub` CLI for authenticated registry workflows:

发布创建新的不可变版本记录。发布者使用 `clawhub` CLI 进行认证注册表工作流：

```bash
clawhub skill publish ./my-skill
clawhub package publish <source> --family code-plugin --dry-run
clawhub package publish <source> --family code-plugin
```

Use dry runs to preview the resolved payload before upload. Public pages then surface the published metadata, files, source attribution, and scan status.

使用 dry run 在上传前预览解析后的载荷。公共页面随后展示已发布的元数据、文件、源归属和扫描状态。

## Installs and updates / 安装和更新

OpenClaw install commands use ClawHub as a package source:

OpenClaw 安装命令使用 ClawHub 作为包源：

```bash
openclaw skills install @openclaw/demo
openclaw plugins install clawhub:<package>
```

OpenClaw records install source metadata so updates can resolve the same registry package later. The ClawHub CLI also supports direct skill install and update workflows for users who want registry-managed skill folders outside a full OpenClaw workspace.

OpenClaw 记录安装源元数据，以便更新可以在以后解析同一注册表包。ClawHub CLI 还支持直接技能安装和更新工作流，适用于希望在完整 OpenClaw 工作区之外使用注册表管理的技能文件夹的用户。

## Security state / 安全状态

ClawHub is open to publishing, but releases are still subject to upload gates, automated checks, user reports, and moderator action.

ClawHub 对发布开放，但发布仍受上传门禁、自动检查、用户报告和管理员操作约束。

Public pages show scan summaries when available. Content that is held, hidden, or blocked may disappear from public search and install flows while remaining visible to the owner for diagnostics.

公共页面在可用时显示扫描摘要。被扣留、隐藏或阻止的内容可能从公共搜索和安装流中消失，同时对所有者仍可见以供诊断。

See [Security](/clawhub/security), [Security Audits](/clawhub/security-audits), [Moderation and Account Safety](/clawhub/moderation), and [Acceptable usage](/clawhub/acceptable-usage).

参见[安全](/clawhub/security)、[安全审计](/clawhub/security-audits)、[管理和账户安全](/clawhub/moderation)和[可接受使用](/clawhub/acceptable-usage)。

## API access / API 访问

ClawHub exposes public read APIs for discovery, search, package details, and downloads. Third-party catalogs may use these APIs when they link back to the canonical ClawHub listing, respect rate limits, and avoid implying endorsement.

ClawHub 为发现、搜索、包详情和下载暴露公共只读 API。第三方目录在链接回权威 ClawHub 列表、尊重速率限制且避免暗示认可时可以使用这些 API。

See [Public API](/clawhub/api) and [HTTP API](/clawhub/http-api).

参见[公共 API](/clawhub/api)和 [HTTP API](/clawhub/http-api)。
