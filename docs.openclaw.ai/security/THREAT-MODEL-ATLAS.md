# Threat Model (MITRE ATLAS)

## 架构精读

> 跳过不影响阅读翻译正文。

### MITRE ATLAS 框架——为什么用 ML 系统威胁模型而非传统 OWASP？

OpenClaw 选择 MITRE ATLAS（Adversarial Threat Landscape for AI Systems）作为威胁分类框架，而非传统 OWASP Top 10：

- **ATLAS 覆盖 ML 特定攻击**：数据投毒、模型反演、对抗样本
- **ATLAS 覆盖传统网络攻击**：prompt 注入、工具滥用、供应链攻击
- **OWASP 只覆盖 Web 层**：XSS/CSRF/SQLi，不覆盖 AI 智能体特有攻击

这跟云安全用 CSA STAR 而非传统 ISO 27001 是一个思路——通用安全框架不覆盖特定领域的威胁（AI 智能体的 prompt 注入、工具滥用、数据投毒）。ATLAS 是"AI 系统的威胁清单"，确保没有遗漏 智能体特有的攻击面。

关键设计是**领域特定威胁模型**。OpenClaw 作为 AI 智能体网关，攻击面包括传统网络（API 暴露、凭证泄露）和 AI 特有（prompt 注入、工具策略绕过、会话隔离失效）。ATLAS 框架覆盖两者。

### 威胁分类——哪些是 智能体特有攻击？

ATLAS 框架覆盖的 OpenClaw 相关威胁：

| 威胁类别 | 示例 |
|---------|------|
| **初始访问** | 暴露的 WebSocket、凭证泄露、pairing 绕过 |
| **执行** | prompt 注入、工具滥用、沙箱逃逸 |
| **持久化** | 后门 skill、恶意 plugin、定时任务滥用 |
| **权限提升** | 工具策略绕过、operator scope 伪造 |
| **防御规避** | 日志篡改、遥测禁用、审计绕过 |
| **凭证访问** | 明文 secret 泄露、SecretRef 绕过 |
| **发现** | session 枚举、智能体列表泄露 |
| **横向移动** | 跨 session 访问、跨智能体通信 |
| **影响** | 数据泄露、资源耗尽、配置破坏 |

这跟 STRIDE 威胁模型是一个思路——按攻击阶段分类（侦察→初始访问→执行→持久化→横向移动→影响），每个阶段有对应的缓解措施。ATLAS 在 STRIDE 基础上增加了 ML 特有攻击（数据投毒、模型反演）。

### 缓解映射——每个威胁对应哪些控制？

每个威胁条目映射到具体的缓解控制：

- **暴露的 WebSocket** → loopback 绑定 + Tailscale Serve + 可信代理认证
- **prompt 注入** → 工具策略（允许/拒绝）+ 沙箱隔离 + approval 门控
- **后门 skill** → ClawHub 审计 + 签名验证 + skill 沙箱
- **凭证泄露** → SecretRef（env/file/exec）+ 禁止明文 + 自动脱敏

这跟 NIST CSF 的"识别→保护→检测→响应→恢复"是一个思路——每个威胁有对应的保护控制（preventive）、检测控制（detective）、响应控制（responsive）。缓解映射让运维人员知道"这个威胁用什么配置防御"。

### 持续演进——为什么威胁模型不是一次性文档？

威胁模型随版本迭代持续更新。每个新版本发布时，安全团队评审新增功能（如新工具、新协议）引入的新攻击面，补充到威胁模型中。

这跟 CVE 数据库的持续更新是一个思路——威胁不是一次性评估，而是随系统演进持续识别新风险。

---

OpenClaw's threat model is aligned with the MITRE ATLAS framework, which covers both ML-specific threats (data poisoning, model inversion, adversarial examples) and traditional threats (prompt injection, tool abuse, supply chain attacks).

OpenClaw 的威胁模型对齐 MITRE ATLAS 框架——覆盖 ML 特有威胁（数据投毒、模型反演、对抗样本）和传统威胁（prompt 注入、工具滥用、供应链攻击）。

Threat categories span initial access (exposed WebSocket, credential leak), execution (prompt injection, tool abuse), persistence (backdoor skill, malicious plugin), privilege escalation (tool policy bypass), defense evasion (log tampering), credential access (plaintext secret leak), discovery (session enumeration), lateral movement (cross-session access), and impact (data exfiltration, resource exhaustion).

威胁类别覆盖初始访问（暴露的 WebSocket、凭证泄露）、执行（prompt 注入、工具滥用）、持久化（后门 skill、恶意 plugin）、权限提升（工具策略绕过）、防御规避（日志篡改）、凭证访问（明文 secret 泄露）、发现（session 枚举）、横向移动（跨 session 访问）、影响（数据泄露、资源耗尽）。

Each threat maps to specific mitigating controls (loopback binding, Tailscale Serve, tool policy, sandbox isolation, approval gating, SecretRef, ClawHub audit). The model evolves with each release — new features are assessed for new attack surfaces.

每个威胁映射到具体的缓解控制（loopback 绑定、Tailscale Serve、工具策略、沙箱隔离、approval 门控、SecretRef、ClawHub 审计）。模型随版本演进——新功能评估新攻击面。
