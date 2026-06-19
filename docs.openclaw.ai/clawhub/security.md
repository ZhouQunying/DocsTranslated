# Security / 安全

## 架构精读

> 跳过不影响阅读翻译正文。

### ClawHub 自身漏洞 vs 第三方技能漏洞——为什么报告通道不同？

ClawHub 把漏洞报告分成两个完全不同的通道：

- **ClawHub 自身漏洞**：通过 GitHub Security Advisories for openclaw/clawhub 报告。包括网站、API、CLI、注册表发布/下载/安装、认证/授权、扫描/审核等
- **第三方技能/插件漏洞**：直接报告给发布者或源码仓库

这跟 Docker Hub 的安全模型是一个思路。Docker Hub 自身的安全漏洞（网站、API、registry 协议）报给 Docker 团队。但 Docker Hub 上托管的第三方镜像（如某个 nginx 镜像）的漏洞报给那个镜像的 maintainer。Docker 不负责修补第三方镜像。

设计意图是**责任边界清晰**。ClawHub 是注册表平台，不是技能/插件的 maintainer。它不维护、不审查、不修补第三方代码的运行时行为。如果用户发现一个技能有 SQL 注入漏洞（技能自身的代码问题），正确的路径是联系技能发布者。ClawHub 团队既没有上下文也没有权限去修第三方代码。

但如果漏洞在 ClawHub 自身的下载机制（如 tarball 完整性验证被绕过），那是 ClawHub 的责任——它破坏了所有技能的安装信任链。

### 托管服务漏洞默认不公开披露——为什么？

ClawHub 是托管云应用，其服务漏洞默认不公开披露。只在以下情况公开：
- 有真实用户影响的证据（确认的利用、用户数据/秘密泄露）
- 用户需要采取行动（轮换凭证、更新本地软件）

这跟 AWS、Google Cloud、Azure 等云服务商的安全披露策略是一个思路。云服务漏洞默认不公开——因为公开一个未修补的云服务漏洞等于给攻击者一张攻击地图。只有在漏洞已被利用、或用户需要采取行动时，才公开披露。

代价是透明度降低。用户不知道 ClawHub 曾经有过哪些漏洞、什么时候修补的。但这是托管服务的现实——用户无法自己修补服务漏洞，公开未修补漏洞只会增加风险，不会帮助用户。

对比：开源软件（如 Linux 内核）的漏洞通常公开披露——因为用户自己可以打补丁。但托管服务的用户没有这个选项。

### 用户安装软件的漏洞公开披露——为什么不同？

用户安装的软件（ClawHub CLI 包、二进制文件、库等）的漏洞公开披露。这跟托管服务漏洞的处理完全不同。

这跟 npm CLI vs npm registry 的安全披露差异是一个思路。npm registry（托管服务）的漏洞默认不公开。但 npm CLI（用户本地安装的软件）的漏洞公开披露——因为用户可以更新本地版本。

设计意图是**用户可行动性**。如果漏洞在用户本地安装的软件中，用户可以采取行动（更新到新版本）。公开披露让用户知道需要更新。如果漏洞在托管服务中，用户无法采取行动（不能修补 ClawHub 的服务器），公开披露只会给攻击者信息优势。

这是安全披露策略的核心原则：**公开披露的前提是用户可以采取行动保护自己**。

---

ClawHub security issues can be reported through GitHub Security Advisories for openclaw/clawhub.

ClawHub 安全问题可以通过 openclaw/clawhub 的 GitHub Security Advisories 报告。

Use GitHub Security Advisories for vulnerabilities in ClawHub itself. Good ClawHub advisory reports include bugs in:

将 GitHub Security Advisories 用于 ClawHub 自身的漏洞。好的 ClawHub advisory 报告包括以下方面的错误：

- the ClawHub website, API, or CLI
  
  ClawHub 网站、API 或 CLI

- registry publishing, downloads, installs, or artifact integrity
  
  注册表发布、下载、安装或制品完整性

- authentication, authorization, or API tokens
  
  认证、授权或 API token

- scanning, moderation, or report handling
  
  扫描、审核或报告处理

Do not use ClawHub advisories for vulnerabilities in a third-party skill or plugin's own source code. Report those directly to the publisher or source repository linked from the ClawHub listing.

不要将 ClawHub advisories 用于第三方技能或插件自身源码中的漏洞。将这些直接报告给发布者或从 ClawHub listing 链接的源仓库。

## Vulnerability disclosure / 漏洞披露

Because ClawHub is a hosted cloud application, ClawHub service vulnerabilities are not publicly disclosed by default. They are publicly disclosed when there is evidence of real user impact or when users need to take action.

因为 ClawHub 是托管云应用，ClawHub 服务漏洞默认不公开披露。当有真实用户影响的证据或用户需要采取行动时，它们被公开披露。

Examples of real user impact include confirmed exploitation, exposure of user data or secrets, malicious content reaching users because of a platform failure, or any issue that requires users to rotate credentials, update local software, or take other protective action.

真实用户影响的示例包括确认的利用、用户数据或秘密的泄露、因平台故障导致恶意内容到达用户。或任何要求用户轮换凭证、更新本地软件或采取其他保护行动的问题。

Vulnerabilities in user-installed software are publicly disclosed, such as ClawHub CLI packages, binaries, libraries, or other release artifacts that users need to update locally.

用户安装软件中的漏洞被公开披露，例如用户需要在本地更新的 ClawHub CLI 包、二进制文件、库或其他发布制品。

## Related pages / 相关页面

For install-time audit labels, risk levels, findings, and interpretation, see Security Audits.

有关安装时审计标签、风险级别、发现和解释，参见安全审计。

For marketplace reports, moderation holds, hidden listings, bans, and account standing, see Moderation and Account Safety.

有关市场报告、审核保留、隐藏 listing、封禁和账户状态，参见审核与账户安全。

## 相关 / Related

- [Security Audits](/clawhub/security-audits) — 安全审计标签和风险分析
- [Moderation and Account Safety](/clawhub/moderation) — 审核与账户安全
- [Acceptable Usage](/clawhub/acceptable-usage) — 可接受使用策略
