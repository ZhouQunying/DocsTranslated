# Moderation and Account Safety / 审核与账户安全

## 架构精读

> 跳过不影响阅读翻译正文。

### 报告 vs 漏洞报告——为什么严格分离？

ClawHub 把"报告"和"漏洞报告"分成两个完全不同的通道：

- **ClawHub 报告**：针对市场上不安全的内容（恶意 listing、误导性元数据、冒充、滥用等）
- **漏洞报告**：针对第三方技能/插件自身源码的安全漏洞，直接报给发布者或源码仓库

这跟 GitHub 的安全模型是一个思路——GitHub Security Advisories 是给 GitHub 自身的漏洞用的，不是给 GitHub 上托管的第三方项目的漏洞用的。第三方项目的漏洞应该报给那个项目的 maintainer。

设计意图是**责任边界清晰**。ClawHub 不维护也不修补第三方技能/插件代码——它只是注册表。如果用户在 ClawHub 报告里报了一个第三方技能的 SQL 注入漏洞，ClawHub 团队既没有上下文也没有权限去修。正确的路径是直接联系发布者。

代价是用户需要理解这个区分。但混淆会更糟——如果所有报告都走同一个通道，ClawHub 团队会被不属于自己责任范围的漏洞报告淹没。

### Moderation holds——保护性隔离而非惩罚

Moderation holds 是"发布者的 listing 被置于审核保留状态"。发生时，受影响内容从公共发现中隐藏，或者未来发布默认隐藏直到问题被审查。

这跟 AWS 的"account suspension pending review"是一个思路——不是最终惩罚，而是保护性隔离。设计意图是**快速止血**。如果一个 listing 看起来高风险（恶意、误导、违反策略），先把它从公共安装界面移除。这防止更多用户受影响，同时给审核团队时间调查。

关键细节：holds 可以被解除——如果确认是误报，listing 恢复。这不是单向的惩罚机制，而是双向的保护机制。对审核团队来说，这降低了"误杀 vs 放任"的决策压力——先隔离再判断，比先判断再隔离更安全。

### 账户状态级联执行——从限权到封禁

账户违规的执行是级联的：
1. 失去发布权限
2. 严重滥用导致账户封禁
3. Token 撤销
4. 内容隐藏
5. Listing 移除

这跟 GitHub 的 enforcement escalation 是一个思路——先限制功能，再禁用账户，最后清理内容。级联设计给违规者改正机会，同时防止持续滥用。

Token 撤销是关键一步。被删除/封禁/禁用的账户不能使用 ClawHub API token——这切断了自动化滥用的路径。如果 CLI 认证在账户操作后开始失败，用户需要登录 Web UI 查看账户状态。这是**信号反馈**——认证失败不只是技术问题，可能是账户状态变化的信号。

### Org/namespace claims——为什么单独流程？

组织、品牌、包作用域、owner handle 或命名空间所有权争议使用专门的 Org and Namespace Claims 流程，而非产品内报告或账户申诉表单。

这跟 npm 的 namespace disputes 政策是一个思路。命名空间争议需要非敏感的证明材料（商标、公司注册文件等）。这些材料不适合走公共 issue（会泄露敏感信息），也不适合走产品内报告（不是安全问题）。

设计意图是**信息敏感性匹配**。命名空间争议需要提交证明材料，这些材料可能包含商业敏感信息。专门流程提供私密的审查通道，公共 issue 不适合这种场景。

---

ClawHub is open to publishing, but public discovery and install surfaces still need guardrails. Reports, moderation holds, hidden listings, and account actions help protect users when a release or account appears unsafe, misleading, or out of policy.

ClawHub 对发布开放，但公共发现和安装界面仍需要防护栏。当发布或账户看起来不安全、误导性或违反策略时，报告、审核保留、隐藏 listing 和账户操作帮助保护用户。

This page covers moderation and account standing. For audit labels such as Pass, Review, Warn, Malicious, and risk level, see Security Audits.

本页涵盖审核和账户状态。有关审计标签（如 Pass、Review、Warn、Malicious 和风险级别），参见安全审计。

See also Security and Acceptable usage. For copyright or other content rights concerns, use Content Rights Requests.

另参见安全和可接受使用。有关版权或其他内容权利问题，使用内容权利请求。

## Reports / 报告

Signed-in users can report skills, plugins, and packages.

登录用户可以报告技能、插件和包。

Use ClawHub reports only for unsafe marketplace content, such as:

仅将 ClawHub 报告用于不安全的市场内容，例如：

- malicious listings
  
  恶意 listing

- misleading metadata
  
  误导性元数据

- undeclared credentials or permission requirements
  
  未声明的凭证或权限要求

- suspicious install instructions
  
  可疑的安装说明

- impersonation
  
  冒充

- bad-faith registrations or trademark misuse
  
  恶意注册或商标滥用

- content that violates Acceptable usage
  
  违反可接受使用的内容

Use the Report skill button on a skill page, or the package reporting command/API for packages.

使用技能页面上的 Report skill 按钮，或包的包报告命令/API。

Do not use ClawHub reports for vulnerabilities in a third-party skill or plugin's own source code. Report those directly to the publisher or source repository linked from the listing. ClawHub does not maintain or patch third-party skill or plugin code.

不要将 ClawHub 报告用于第三方技能或插件自身源码中的漏洞。将这些直接报告给发布者或从 listing 链接的源仓库。ClawHub 不维护或修补第三方技能或插件代码。

GitHub Security Advisories for openclaw/clawhub are for vulnerabilities in ClawHub itself. Examples include bugs in the website, API, CLI, registry, auth, scanning, moderation, or download/install trust boundaries. Do not use ClawHub advisories for vulnerabilities in third-party skills or plugins.

openclaw/clawhub 的 GitHub Security Advisories 用于 ClawHub 自身的漏洞。示例包括网站、API、CLI、注册表、认证、扫描、审核或下载/安装信任边界中的错误。不要将 ClawHub advisories 用于第三方技能或插件的漏洞。

Good reports are specific and actionable. Abuse of reporting can itself lead to account action.

好的报告是具体且可操作的。滥用报告本身可能导致账户操作。

## Org and namespace claims / 组织和命名空间声明

Org, brand, package-scope, owner-handle, or namespace ownership disputes should use the Org and Namespace Claims process, not the in-product report flow or the account appeal form.

组织、品牌、包作用域、owner handle 或命名空间所有权争议应使用组织和命名空间声明流程，而非产品内报告流程或账户申诉表单。

Use that process when you need ClawHub staff to review non-sensitive proof that a namespace should be reserved, transferred, renamed, hidden, quarantined, aliased, or otherwise reviewed. Do not include secrets, private documents, private legal files, personal identity documents, API tokens, or DNS challenge tokens in a public issue.

当你需要 ClawHub 员工审查命名空间应被保留、转移、重命名、隐藏、隔离、别名化或以其他方式审查的非敏感证明时，使用该流程。不要在公共 issue 中包含秘密、私密文档、私密法律文件、个人身份文件、API token 或 DNS 挑战 token。

## Moderation holds / 审核保留

Some severe findings or policy issues can place a publisher or listing under a moderation hold. When this happens, affected content may be hidden from public discovery or future publishes may start hidden until the issue is reviewed.

一些严重发现或策略问题可能将发布者或 listing 置于审核保留状态。发生这种情况时，受影响内容可能从公共发现中隐藏，或未来发布可能默认隐藏直到问题被审查。

Moderation holds are meant to protect users while ClawHub resolves high-risk cases. They can also be lifted when a false positive is confirmed.

审核保留旨在在 ClawHub 解决高风险案例时保护用户。当确认误报时，它们也可以被解除。

## Hidden or blocked listings / 隐藏或被阻止的 listing

A listing may be held, hidden, quarantined, revoked, or otherwise unavailable on public install surfaces.

listing 可能在公共安装界面上被保留、隐藏、隔离、撤销或以其他方式不可用。

If you see one of these states, do not install the release unless the owner resolves the issue or moderation restores it.

如果你看到这些状态之一，除非 owner 解决问题或审核恢复它，否则不要安装该版本。

Owners may still see diagnostics for their own held or hidden listings. These diagnostics help explain what happened and what needs to change before the listing can return to public surfaces.

owner 仍可能看到其自己保留或隐藏 listing 的诊断。这些诊断帮助解释发生了什么以及 listing 返回公共界面前需要更改什么。

## Bans and account standing / 封禁和账户状态

Accounts that violate ClawHub policy may lose publishing access. Severe abuse can result in account bans, token revocation, hidden content, or removed listings.

违反 ClawHub 策略的账户可能失去发布访问权限。严重滥用可能导致账户封禁、token 撤销、内容隐藏或 listing 移除。

Deleted, banned, or disabled accounts cannot use ClawHub API tokens. If CLI auth starts failing after account action, sign in to the web UI to review account state. If sign-in or normal CLI access is blocked by a ban or disabled account, use the ClawHub appeal form for recovery review.

已删除、封禁或禁用的账户不能使用 ClawHub API token。如果账户操作后 CLI 认证开始失败，登录 Web UI 查看账户状态。如果登录或正常 CLI 访问被封禁或禁用账户阻止，使用 ClawHub 申诉表单进行恢复审查。

If a scanner-triggered email names a skill or plugin version as malicious, download the stored scan results for the blocked submitted version: `clawhub scan download <slug> --version <version>`. For plugins, add `--kind plugin`. Review the scan output, fix the listing, increment the version number, and upload the fixed version.

如果扫描器触发的电子邮件将技能或插件版本命名为恶意，下载被阻止提交版本的存储扫描结果：`clawhub scan download <slug> --version <version>`。对于插件，添加 `--kind plugin`。审查扫描输出，修复 listing，递增版本号，并上传修复版本。

## Publisher guidance / 发布者指南

To reduce false positives and improve user trust:

为减少误报并改善用户信任：

- keep names, summaries, tags, and changelogs accurate
  
  保持名称、摘要、标签和变更日志准确

- declare required environment variables and permissions
  
  声明必需的环境变量和权限

- avoid obfuscated install commands
  
  避免混淆的安装命令

- link to source when possible
  
  尽可能链接到源码

- use dry runs before publishing plugins
  
  发布插件前使用 dry run

- respond clearly if users or moderators ask about release behavior
  
  如果用户或审核者询问发布行为，清晰回应

## 相关 / Related

- [Acceptable Usage](/clawhub/acceptable-usage) — 可接受使用策略
- [Security Audits](/clawhub/security-audits) — 安全审计标签
- [Security](/clawhub/security) — 安全
