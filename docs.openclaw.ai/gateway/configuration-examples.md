# Configuration Examples

**总结：** 与当前 config schema 对齐的配置示例集合——从 quick start 最小配置到完整生产配置，覆盖常见 pattern。

> **类比：Helm Chart 的 values.yaml 示例 + Terraform module examples。** Helm 提供 minimal/production/custom 多种 values.yaml 模板，Terraform module 有 examples/ 目录展示不同场景用法。OpenClaw 配置示例类似——渐进式复杂度（最小配置 5 分钟上手 → 推荐起步加常用功能 → 完整配置覆盖高级选项），common pattern 覆盖共享 skill baseline、多平台 channel、可信网络自动审批、安全 DM 模式、API key fallback、受限工作 bot、本地模型等场景。
>
> **架构要点：** Quick start：最小配置（仅 workspace + channel allowlist）+ 推荐起步（加 tool profile + DM policy）；Expanded example：完整 JSON5 覆盖 env var、auth profile、logging、message format、tooling、session、channel、agent、model、cron、webhook、gateway、skill；Symlinked sibling skill repo：skill 目录 symlink 到 Git 仓库（code review + 版本管理 + 多人协作）；Common patterns：shared skill baseline（基线 + per-agent override）、multi-platform（Slack + Discord + WhatsApp 同时配置）、trusted node auto-approval（`autoApproveNetworks` 可信网络自动配对，须配合网络白名单）、secure DM mode、API key fallback、restricted work bot、local-only model；Tips：DM policy 格式、provider ID 格式、可选 section 按需添加。
