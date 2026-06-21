# Formal Verification

**总结：** OpenClaw 最高风险路径的机器校验安全模型——使用 TLA+ 和 TLC。

> **类比：K8s 的 conformance test + TLA+ 模型校验。** K8s conformance test 验证实现符合规范，TLA+ 用数学模型验证并发系统的正确性。OpenClaw formal verification 类似——用 TLA+ 建模安全关键路径（gateway exposure、node exec、pairing、ingress gating、routing isolation），TLC 状态空间搜索验证不变量，每个 assertion 配套 negative model 证明攻击场景可被检测。
>
> **架构要点：** 代码在 [vignesh07/openclaw-formal-models](https://github.com/vignesh07/openclaw-formal-models)；TLC 有界状态空间搜索，通过测试只保证界限内的安全；模型与代码可能 drift；每个 assertion 配套 passing + negative（攻击）模型；核心模型：gateway exposure（non-loopback 无 auth 的风险）、node exec pipeline（allowlist + declared commands + tokenized approvals 防重放）、pairing store（TTL + cap + 并发幂等）、ingress gating（mention 要求不可绕过）、routing/session-key isolation（不同 peer DM 隔离）、ingress trace correlation（fan-out 保持 trace identity）。
