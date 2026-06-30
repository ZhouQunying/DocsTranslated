# Incident Response

## 架构精读

> 跳过不影响阅读翻译正文。

### 响应流程——为什么是四步而非一步修复？

安全事件响应是四步流程：

1. **分诊**（24 小时内）：确认事件真实性和影响范围
2. **评估**：评估严重度（Critical/High/Medium/Low）
3. **修复**：在私有分支开发修复补丁
4. **发布**：合并到主分支 + 发布安全公告

这跟 GitHub Security Advisory 的漏洞披露流程是一个思路——先私下确认和修复（private fork），再公开披露（security advisory）。直接公开未修复的漏洞会给攻击者提供利用窗口。

### 严重度分级——为什么用四级而非十级？

四级严重度（Critical/High/Medium/Low），每级有明确定义：

| 级别 | 定义 | 示例 |
|------|------|------|
| Critical | 远程代码执行或数据泄露 | 未认证远程执行 |
| High | 权限提升或沙箱逃逸 | 沙箱逃逸 |
| Medium | 信息泄露或拒绝服务 | 配置信息泄露 |
| Low | 低影响问题 | 误导性错误消息 |

这跟 CVSS 评分的四级分类是一个思路——Critical（9.0-10.0）、High（7.0-8.9）、Medium（4.0-6.9）、Low（0.1-3.9）。四级足够区分响应优先级，十级过于细粒度（运维人员难以快速判断）。

### 私有修复——为什么不在主分支修？

修复在私有分支（private fork）进行，而非直接在主分支提交。修复完成后再合并到主分支并打标签。

这跟 Linux kernel 的安全修复流程是一个思路——security fix 先在 private mailing list 讨论和开发补丁，补丁准备好后一次性发布。如果直接在主分支提交，攻击者可以通过 commit diff 分析漏洞细节，在补丁发布前利用漏洞。

### 安全公告——为什么包含 PoC 而非只说"已修复"？

安全公告包含 PoC（Proof of Concept）和修复细节：

- **PoC**：证明漏洞真实存在，帮助受影响用户确认风险
- **修复细节**：帮助受影响用户评估是否需要紧急升级
- **缓解措施**：提供临时解决方案（如禁用特定功能）

这跟 CVE 公告的标准格式是一个思路——每个 CVE 包含漏洞描述、影响范围、修复版本和临时缓解措施。只说"已修复"不够透明，用户无法判断自己是否受影响。

### 报告渠道——为什么区分活跃漏洞和一般查询？

两种报告渠道：

- **活跃漏洞**（active exploit）：通过安全网页紧急报告（24 小时响应）
- **一般查询**：通过仓库 issues 或聊天服务器（标准响应时间）

这跟 911 vs 311 的区分是一个思路——紧急情况走快速通道（24 小时响应），非紧急走标准通道。活跃漏洞需要快速响应（可能正在被利用），一般查询可以按正常节奏处理。

---

OpenClaw follows a structured incident response process: triage (within 24 hours), severity assessment (Critical/High/Medium/Low), private fix (in private fork, not on main branch), and public disclosure (security advisory with PoC, fix details, and mitigation steps).

OpenClaw 遵循结构化的事件响应流程。分诊（24 小时内）、严重度评估（四级）、私有修复（私有分支）、公开披露（安全公告）。

Critical severity covers remote code execution or data exfiltration. High covers privilege escalation or sandbox escape. Medium covers information disclosure or denial of service. Low covers low-impact issues.

Critical 级别覆盖远程代码执行或数据泄露。High 覆盖权限提升或沙箱逃逸。Medium 覆盖信息泄露或拒绝服务。Low 覆盖低影响问题。

Active exploits should be reported via the security webpage (24-hour response). General inquiries go through repository issues or the chat server. Security advisories include PoC, fix details, and temporary mitigation steps to help affected users assess their risk.

活跃漏洞通过安全网页报告（24 小时响应）。一般查询通过仓库 issues 或聊天服务器。安全公告包含 PoC、修复细节和临时缓解步骤，帮助受影响用户评估风险。
