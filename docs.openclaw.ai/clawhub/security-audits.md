# Security Audits / 安全审计

## 架构精读

> 跳过不影响阅读翻译正文。

### Audit status vs Risk level——为什么是两个维度？

ClawHub 的安全审计有两个独立维度：

- **Risk level**（风险级别）：这个发布有多少权限？"如果按预期使用，它的爆炸半径有多大？"
- **Audit status**（审计状态）：我该怎么反应？"Pass 意味着令人安心，但不替代你自己的判断"

这跟 AWS IAM 的"权限范围 vs 信任策略"是一个思路。一个 IAM role 可以有高权限（AdminAccess），但信任策略限制了谁能 assume 它。权限范围和信任评估是两个不同的问题。

设计意图是**避免二元判断**。如果只有"安全/不安全"一个维度，一个高权限但合法的发布工具会被误标为"不安全"——它确实有高权限，但这是它的设计目的。Risk level 告诉你"这个工具有多强大"，Audit status 告诉你"你是否应该担心"。

举例：一个发布技能可能显示 Review + Medium risk。这不意味着它恶意——只是说它的权限范围与目的对齐，但能执行有意义的账户操作。用户需要自己判断是否接受这个权限范围。

### Findings 的证据链——为什么隐藏低置信度发现？

Findings 解释为什么显示某个审计结果。每个 finding 包含：它意味着什么、为什么被标记、相关的技能/插件内容、推荐操作。

但低置信度 finding 从公共审计汇总中隐藏。这跟 Google Lighthouse 的"opportunities vs diagnostics"是一个思路——Lighthouse 不把所有可能的优化建议都展示，只展示高置信度的、有实际影响的建议。

设计意图是**信噪比**。安全审计页面如果堆满低置信度的发现，用户会被噪音淹没，忽略真正重要的警告。隐藏低置信度发现让页面聚焦于有用证据。

代价是可能错过一些真实的低置信度问题。但这是实用主义的取舍——过度警告（false positive）会导致警告疲劳，用户开始忽略所有警告，反而更危险。

### VirusTotal 作为遥测 vs ClawHub 自身分析——为什么互补？

ClawHub 的安全审计栈结合了两个来源：

- **VirusTotal**：行业标准的恶意软件遥测，用于已知恶意制品、引擎命中、声誉信号
- **ClawScan**（ClawHub 自有系统）：agent 感知的风险分析，审查发布作为 agent 面对的制品

这跟杀毒软件的"signature-based + heuristic-based"双引擎是一个思路。VirusTotal 是 signature-based——它擅长检测已知恶意软件（"这个文件的 hash 在 62 个引擎中被 62 个标记为干净"）。ClawScan 是 heuristic-based——它分析发布的行为模式（"这个技能请求了文件系统访问，但声明的用途只是文本生成，这不一致"）。

VirusTotal 的局限是它不理解 agent 上下文。一个技能包含 `curl` 命令不会被 VirusTotal 标记（curl 是合法工具），但如果这个技能的声明用途是"markdown 格式化"，那 `curl` 命令就是可疑的。ClawScan 理解 agent 上下文——它检查"名称、摘要、元数据、请求的权限和实际内容是否与用户的合理期望一致"。

### OWASP Agentic Skills Top 10——为什么 agent 特定的风险分类？

ClawScan 使用 OWASP Agentic Skills Top 10 作为风险分析的视角：提示注入、工具滥用、凭证暴露、不安全执行、记忆/上下文投毒、过度代理等。

这跟传统 Web 应用的 OWASP Top 10 是一个思路，但针对 agent 特有的风险模式。传统 Web 应用的 SQL 注入在 agent 世界变成了"prompt injection"——攻击者通过恶意输入操纵 agent 行为。传统 Web 应用的 XSS 在 agent 世界变成了"memory poisoning"——攻击者通过污染 agent 的上下文记忆影响后续决策。

设计意图是**威胁模型匹配**。agent 技能的威胁模型与传统软件不同。一个 npm 包的主要风险是恶意代码执行。一个 agent 技能的主要风险是"agent 被诱导执行非预期操作"——技能本身可能没有恶意代码，但指令可能被设计为操纵 agent。

---

ClawHub security audits help you decide whether a skill or plugin is safe enough to install. They show what a release does, what authority it asks for, and whether anything deserves extra attention before it can access files, accounts, credentials, code, or external services.

ClawHub 安全审计帮助你决定技能或插件是否足够安全可以安装。它们显示发布做什么、请求什么权限。在发布可以访问文件、账户、凭证、代码或外部服务之前，是否有任何内容值得额外关注。

Audits are strong safety signals, but they are not a guarantee that a release is risk-free. Always use judgment before granting sensitive access.

审计是强安全信号，但它们不保证发布无风险。在授予敏感访问前始终使用判断。

See also Security, Acceptable usage, and Moderation and Account Safety.

另参见安全、可接受使用和审核与账户安全。

## What to check before installing / 安装前检查什么

Before installing, review:

安装前，审查：

- the overall audit status
  
  整体审计状态

- the risk level
  
  风险级别

- any listed findings
  
  任何列出的发现

- required credentials, permissions, or environment variables
  
  必需的凭证、权限或环境变量

- owner, source, version, changelog, installs, stars, and other trust signals
  
  owner、源码、版本、变更日志、安装数、星标和其他信任信号

Install only content you understand and trust.

只安装你理解并信任的内容。

## Audit status / 审计状态

Audit status tells you how to react to the audit result:

审计状态告诉你如何对审计结果做出反应：

Pass is reassuring, but it does not replace your own judgment. This matters most for tools that can publish content, edit data, run commands, read files, or access production systems.

Pass 令人安心，但它不替代你自己的判断。这对于可以发布内容、编辑数据、运行命令、读取文件或访问生产系统的工具最重要。

## Risk level / 风险级别

Risk level describes blast radius: how much power the release appears to have if you use it as intended.

风险级别描述爆炸半径：如果按预期使用，发布看起来有多少权限。

Risk level and audit status answer different questions:

风险级别和审计状态回答不同的问题：

- Risk level asks: "How much power is here?"
  
  风险级别问："这里有多少权限？"

- Audit status asks: "What should I do with this result?"
  
  审计状态问："我该如何处理这个结果？"

For example, a publishing skill may show Review with Medium risk. That does not mean it is malicious. It means the skill appears purpose-aligned, but can act with meaningful account authority.

例如，一个发布技能可能显示 Review 带 Medium 风险。这不意味着它恶意。这意味着技能看起来与目的对齐，但能执行有意义的账户操作。

## Findings / 发现

Findings explain why an audit result was shown. Each finding usually includes:

发现解释为什么显示某个审计结果。每个发现通常包括：

- what it means
  
  它意味着什么

- why it was flagged
  
  为什么被标记

- the relevant skill or plugin content
  
  相关的技能或插件内容

- a recommendation
  
  推荐

Findings may be labeled Info, Low, Medium, High, or Critical. Higher severity findings contribute more strongly to risk level and audit status.

发现可能被标记为 Info、Low、Medium、High 或 Critical。更高严重性的发现对风险级别和审计状态贡献更大。

Low-confidence findings are hidden from the public audit rollup so the page stays focused on useful evidence.

低置信度发现从公共审计汇总中隐藏，以便页面聚焦于有用证据。

## What ClawHub checks / ClawHub 检查什么

ClawHub audits submitted release artifacts, including:

ClawHub 审计提交的发布制品，包括：

- skill instructions or plugin metadata
  
  技能指令或插件元数据

- declared environment variables and permissions
  
  声明的环境变量和权限

- install instructions and package metadata
  
  安装说明和包元数据

- included files and file manifests
  
  包含的文件和文件清单

- compatibility and capability metadata
  
  兼容性和能力元数据

The main question is coherence: do the name, summary, metadata, requested authority, and actual content line up with what users would reasonably expect?

主要问题是一致性：名称、摘要、元数据、请求的权限和实际内容是否与用户的合理期望一致？

Powerful behavior is not automatically bad. Many useful tools need credentials, local commands, provider APIs, or package installs. The audit checks whether that power is expected, disclosed, and proportionate.

强大行为不自动是坏的。许多有用工具需要凭证、本地命令、提供者 API 或包安装。审计检查该权限是否是预期的、已披露的且成比例的。

Artifact pages link to the full audit at:

制品页面链接到完整审计：

```
/<owner>/<slug>/security-audit
```

The audit page combines:

审计页面结合：

- SkillSpector
- VirusTotal
- Risk analysis

## VirusTotal / VirusTotal

ClawHub uses VirusTotal as malware telemetry in the audit stack. VirusTotal is a trusted industry standard for file reputation and malware scanning, and our partnership lets ClawHub add broader security intelligence to skill and plugin review.

ClawHub 在审计栈中使用 VirusTotal 作为恶意软件遥测。VirusTotal 是文件声誉和恶意软件扫描的受信任行业标准，我们的合作伙伴关系让 ClawHub 为技能和插件审查添加更广泛的安全智能。

VirusTotal is especially useful for known malicious artifacts, engine hits, and reputation signals that complement ClawHub's agent-aware review. When vendor engine counts are available, the audit summarizes them in plain language, such as:

VirusTotal 对于已知恶意制品、引擎命中和补充 ClawHub agent 感知审查的声誉信号特别有用。当供应商引擎计数可用时，审计用纯语言总结它们，例如：

```
62/62 vendors flagged this skill as clean.
```

or:

或：

```
2/64 vendors flagged this skill as malicious, 1/64 flagged it as suspicious, and 61/64 flagged it as clean.
```

When ClawHub has no vendor-count telemetry to summarize, the audit says:

当 ClawHub 没有供应商计数遥测可总结时，审计说：

```
No VirusTotal findings
```

VirusTotal remains telemetry. It does not replace ClawHub's own artifact-aware risk analysis.

VirusTotal 仍然是遥测。它不替代 ClawHub 自己的制品感知风险分析。

## Risk analysis / 风险分析

Risk analysis is powered internally by ClawScan, ClawHub's own security audit system. It reviews each release as an agent-facing artifact: instructions, metadata, declared permissions, files, capability signals, static scan signals, SkillSpector findings, VirusTotal telemetry, and publisher-provided context. Static scan signals are internal context for this review; they are not a standalone public audit section or install-blocking verdict.

风险分析由 ClawScan（ClawHub 自己的安全审计系统）内部驱动。它将每个发布作为 agent 面对的制品审查。审查内容包括：指令、元数据、声明的权限、文件、能力信号、静态扫描信号、SkillSpector 发现、VirusTotal 遥测和发布者提供的上下文。静态扫描信号是此审查的内部上下文；它们不是独立的公共审计部分或安装阻止判决。

Risk analysis uses the OWASP Agentic Skills Top 10 as a lens for risks such as prompt injection, tool misuse, credential exposure, unsafe execution, memory or context poisoning, and excessive agency.

风险分析使用 OWASP Agentic Skills Top 10 作为视角，针对提示注入、工具滥用、凭证暴露、不安全执行、记忆或上下文投毒和过度代理等风险。

ClawScan does not treat a scary-looking capability as automatically malicious. It asks whether the capability is disclosed, purpose-aligned, and supported by the release's stated use case.

ClawScan 不将看起来可怕的能力视为自动恶意。它询问该能力是否被披露、与目的对齐，并由发布的声明用例支持。

## 相关 / Related

- [Security](/clawhub/security) — 安全
- [Acceptable Usage](/clawhub/acceptable-usage) — 可接受使用
- [Moderation and Account Safety](/clawhub/moderation) — 审核与账户安全
