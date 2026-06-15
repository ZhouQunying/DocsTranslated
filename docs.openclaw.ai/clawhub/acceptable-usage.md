# Acceptable Usage / 可接受使用

This page describes the kinds of skills and content ClawHub is okay with, and the abuse workflows it will not host.

本页描述 ClawHub 允许的技能和内容类型,以及它不会托管的滥用工作流。

These rules are intentionally practical. We care most about end-to-end abuse workflows, not just isolated keywords. If a skill is built to gain unauthorized access, abuse platforms, scam people, invade privacy, or enable non-consensual behavior, it does not belong on ClawHub.

这些规则刻意实用。我们最关心端到端滥用工作流,而非孤立关键词。如果技能被构建用于获得未授权访问、滥用平台、诈骗他人、侵犯隐私或启用非自愿行为,它不属于 ClawHub。

## Recent patterns we are explicitly okay with / 我们明确允许的近期模式

- Frontend and design-system work that uses real components, semantic tokens, accessible states, and tested user flows.
  
  使用真实组件、语义 token、可访问状态和测试用户流程的前端和设计系统工作。

- shadcn/ui composition that uses installed source components, project aliases, and documented variants instead of one-off markup.
  
  使用已安装源组件、项目别名和文档化变体而非一次性标记的 shadcn/ui 组合。

- UI5 JavaScript-to-TypeScript conversion that preserves comments, uses concrete UI5 types, and keeps generated control interfaces reviewable.
  
  保留注释、使用具体 UI5 类型并保持生成的控制接口可审查的 UI5 JavaScript 到 TypeScript 转换。

- Defensive security review, moderation tooling, and abuse-detection prompts that show evidence and keep human approval boundaries clear.
  
  显示证据并保持人工审批边界清晰的防御性安全审查、审核工具和滥用检测提示。

- Consent-based workflow automation for personal or team accounts with explicit credentials, transparent setup, and dry-run or preview modes.
  
  基于同意的工作流自动化,用于个人或团队账户,带显式凭证、透明设置和试运行或预览模式。

- Documentation, migration runbooks, developer utilities, and test fixtures scoped to the software they support.
  
  限定在其支持的软件范围内的文档、迁移运行手册、开发者工具和测试装置。

## Not okay / 不允许

**Security-bypass or unauthorized-access workflows.**

**安全绕过或未授权访问工作流。**

Examples: auth bypass, account takeover, rate-limit abuse, live call or agent takeover, reusable session theft, auto-approving pairing flows for unapproved users.

示例:认证绕过、账户接管、速率限制滥用、实时调用或 agent 接管、可复用会话窃取、为未批准用户自动批准配对流程。

**Platform abuse and ban evasion.**

**平台滥用和禁止逃避。**

Examples: stealth accounts after bans, account warming/farming, fake engagement, karma or follower cultivation, multi-account automation, mass posting, spam bots, marketplace or social automation built to avoid detection.

示例:禁止后的隐身账户、账户预热/养殖、虚假互动、业力或粉丝培养、多账户自动化、批量发帖、垃圾邮件机器人。包括为逃避检测而构建的市场或社交自动化。

**Fraud, scams, and deceptive financial workflows.**

**欺诈、诈骗和欺骗性金融工作流。**

Examples: fake certificates, fake invoices, deceptive payment flows, scam outreach, fake social proof, tools that enable spending or charging without clear human approval and transparent controls, or synthetic-identity workflows built to create accounts for fraud.

示例:假证书、假发票、欺骗性支付流程、诈骗外联、虚假社交证明。包括缺乏明确人工批准和透明控制时启用支出或收费的工具,以及为创建账户进行欺诈而构建的合成身份工作流。

**Privacy-invasive enrichment or surveillance.**

**侵犯隐私的数据丰富或监控。**

Examples: collecting contact details at scale for spam, doxxing, stalking, lead extraction paired with unsolicited outreach, covert monitoring, face search or biometric matching used without clear consent, or buying, publishing, downloading, or operationalizing leaked data or breach dumps.

示例:大规模收集联系方式用于垃圾邮件、人肉搜索、跟踪、与未经请求的外联配对的潜在客户提取、秘密监控。包括缺乏明确同意时使用的人脸搜索或生物特征匹配,以及购买、发布、下载或操作化泄露数据或违规转储。

**Non-consensual impersonation or deceptive identity manipulation.**

**非自愿冒充或欺骗性身份操纵。**

Examples: face swap, digital twins, fake personas, cloned influencers, or other identity-manipulation tooling used to impersonate or mislead.

示例:换脸、数字孪生、虚假人物、克隆网红,或其他用于冒充或误导的身份操纵工具。

**Explicit sexual content and safety-disabled adult generation.**

**显式性内容和安全禁用的成人生成。**

Examples: NSFW image/video/content generation, adult-content wrappers around third-party APIs, or skills whose primary purpose is explicit sexual content.

示例:NSFW 图像/视频/内容生成、第三方 API 的成人内容包装器,或主要目的是显式性内容的技能。

**Hidden, unsafe, or misleading execution requirements.**

**隐藏、不安全或误导的执行要求。**

Examples: obfuscated install commands, `curl | sh`, undeclared secret requirements, undeclared private-key use, remote `npx @latest` execution without clear reviewability, misleading metadata that hides what the skill really needs to run.

示例:混淆的安装命令、`curl | sh`、未声明的密钥要求、未声明的私钥使用。包括缺乏明确可审查性的远程 `npx @latest` 执行,以及隐藏技能真正运行所需内容的误导性元数据。

## Recent patterns we are explicitly not okay with / 我们明确不允许的近期模式

- "Create stealth seller accounts after marketplace bans."
  
  "市场禁止后创建隐身卖家账户。"

- "Modify Telegram pairing so unapproved users automatically receive pairing codes."
  
  "修改 Telegram 配对使未批准用户自动接收配对代码。"

- "Cultivate Reddit/Twitter accounts with undetectable automation."
  
  "使用不可检测的自动化培养 Reddit/Twitter 账户。"

- "Generate professional certificates or invoices for arbitrary use."
  
  "生成用于任意用途的专业证书或发票。"

- "Generate NSFW content with safety checks disabled."
  
  "禁用安全检查以生成 NSFW 内容。"

- "Harvest leads, enrich contacts, and launch cold outreach at scale."
  
  "收获潜在客户、丰富联系人并大规模启动冷外联。"

- "Buy, publish, or download leaked data or breach dumps."
  
  "购买、发布或下载泄露数据或违规转储。"

- "Bulk-create email or social accounts with synthetic identities."
  
  "使用合成身份批量创建电子邮件或社交账户。"

## Notes for reviewers / 审核者注意事项

- Context matters. The same topic can be legitimate in a narrow defensive or consent-based setting and unacceptable when packaged as an abuse workflow.
  
  上下文很重要。同一主题在狭窄的防御性或基于同意的环境中可能是合法的,但打包为滥用工作流时不可接受。

- We should bias toward action when a skill is clearly optimized for unauthorized access, platform abuse, deception, or non-consensual use.
  
  当技能明显为未授权访问、平台滥用、欺骗或非自愿使用优化时,我们应倾向于采取行动。

- Repeated uploads in these categories are grounds for hiding content and banning the account.
  
  在这些类别中重复上传是隐藏内容和禁止账户的理由。

## Enforcement / 执行

- We may hide, remove, or hard-delete violating skills.
  
  我们可能隐藏、移除或硬删除违规技能。

- We may revoke tokens, soft-delete associated content, and ban repeat or severe offenders.
  
  我们可能撤销 token、软删除关联内容,并禁止重复或严重违规者。

- We do not guarantee warning-first enforcement for obvious abuse.
  
  对于明显的滥用,我们不保证先警告后执行。

## 相关 / Related

- [Publishing](/clawhub/publishing) — 发布流程
- [Skill format](/clawhub/skill-format) — 技能格式要求
- [HTTP API](/clawhub/http-api) — API 端点
