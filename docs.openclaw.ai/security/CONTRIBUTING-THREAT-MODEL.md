# Contributing to the Threat Model

## 架构精读

> 跳过不影响阅读翻译正文。

### 贡献方式——为什么接受所有技能水平的贡献？

威胁模型接受四种贡献方式：

1. **提交新风险**：发现未覆盖的攻击向量
2. **推荐防御措施**：提出新的缓解控制
3. **详述攻击序列**：描述多步利用链
4. **修正现有文本**：修复错误或过时的描述

这跟开源项目的贡献模型是一个思路——不要求贡献者熟悉整个项目，只需描述"我们没覆盖的攻击向量或风险"。维护者负责框架对齐（ATLAS mapping）和追踪码（threat ID），降低贡献门槛。

### MITRE ATLAS 框架——为什么用它做分类标准？

项目使用 MITRE ATLAS（Adversarial Threat Landscape for AI Systems）作为分类框架：

- **覆盖 ML 特有威胁**：数据投毒、模型反演、对抗样本
- **覆盖传统威胁**：prompt 注入、工具滥用、供应链攻击
- **四级严重度**：Critical / High / Medium / Low

这跟 CVE 使用 CVSS 评分是一个思路——统一分类标准让不同贡献者的报告可以互相比较、聚合。ATLAS 的标识符（如 `AML.T0001`）是全局唯一的，方便引用和追踪。

### 评审流程——为什么是四步而非一步合并？

贡献经过四步评审：

1. **初始分诊**（2 天内）：确认是否属于威胁模型范围
2. **可行性评估**：验证攻击是否真实可行
3. **格式化**：对齐 ATLAS 分类标准和标识符
4. **最终集成**：合并到规范记录和图表

这跟 Linux kernel 的补丁评审流程是一个思路。不是所有提交都直接合并，需要经过验证、格式化和集成三步。

### 认可机制——为什么用 release notes + hall of fame？

有价值的贡献者在 release notes、致谢、hall of fame（重大安全改进）中获得认可。

这跟 HackerOne 的漏洞赏金计划是一个思路——公开认可激励更多人参与安全改进。Hall of fame 专门表彰重大安全发现（如发现新的攻击面或关键漏洞）。

---

This guide explains how to contribute to the OpenClaw threat model. Contributions are welcome from all skill levels — you can submit new risks, recommend defenses, detail exploit sequences, or correct existing text.

本指南解释如何贡献到 OpenClaw 威胁模型。欢迎所有技能水平的贡献——你可以提交新风险、推荐防御措施、详述攻击序列或修正现有文本。

The project uses MITRE ATLAS for classification, with four severity tiers (Critical/High/Medium/Low) and unique identifiers for each threat. Submissions go through a four-step review: triage (within 2 days), feasibility assessment, formatting, and final integration.

项目使用 MITRE ATLAS 做分类，四级严重度（Critical/High/Medium/Low），每个威胁有唯一标识符。贡献经过四步评审：分诊（2 天内）、可行性评估、格式化、最终集成。

Contributors receive recognition in release notes, acknowledgments, and a hall of fame for major security enhancements. Active exploits should be reported via the security webpage; general inquiries go through repository issues or the chat server.

贡献者在 release notes、致谢和重大安全改进的 hall of fame 中获得认可。活跃漏洞通过安全网页报告；一般查询通过仓库 issues 或聊天服务器。
