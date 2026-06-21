# Configuration Examples

## 架构精读

> 跳过不影响阅读翻译正文。

### 渐进式复杂度——为什么从最小配置开始？

Configuration examples 按复杂度递进：

1. **Absolute minimum**：只有 workspace + WhatsApp allowlist（5 分钟上手）
2. **Recommended starter**：加 model/tool profile/DM policy/mention gating（生产就绪）
3. **Expanded example**：完整 JSON5 覆盖所有主要选项（按需学习）

这跟 React 学习曲线是一个思路——先写 `Hello`，再 state，再 hooks，再 context。先用最小配置跑起来，需要时加功能。

关键设计是**降低入门摩擦**。用户看到 100 行配置会被吓到，看到 5 行配置会觉得"这很简单"。

### Symlinked sibling skill repo——为什么 skill 要 symlink 到 Git 仓库？

Skill 目录可以 symlink 到 sibling Git 仓库：

```json5
{
  agents: {
    defaults: {
      skills: {
        extraDirs: ["../skills-repo/skills"],
        allowSymlinkTargets: ["../skills-repo"]
      }
    }
  }
}
```

这跟 monorepo 的 package 共享是一个思路——skill 放在 Git 仓库 = code review + 版本管理 + 多人协作 + 变更可追溯。`allowSymlinkTargets` 显式信任 symlink target（防 path escape 攻击）。

代价是配置稍复杂。但这让 skill 管理从"手动复制文件"升级到"Git workflow"。

### Trusted node auto-approval——为什么只在可信网络用？

```json5
{
  gateway: {
    pairing: {
      autoApproveNetworks: ["192.168.1.0/24"]
    }
  }
}
```

这跟 WiFi WPS 是一个思路——同一网络内设备自动配对，减少管理员负担。但必须配合网络白名单（CIDR range），只在可信网络（公司内网/lab/tailnet）使用。

代价是公共网络开启则任何人都能配对（安全风险）。

### Local models only——为什么需要完全本地推理？

```json5
{
  providers: {
    custom: {
      baseUrl: "http://localhost:1234/v1",
      adapter: "openai-completions",
      models: [{ id: "local-model", contextWindow: 8192, costPer1kInputTokens: 0, costPer1kOutputTokens: 0 }]
    }
  }
}
```

这跟 air-gapped 环境是一个思路——完全本地推理（LM Studio/Ollama），零成本、零网络依赖、零数据泄露风险。适合敏感数据/离线环境/成本敏感场景。

代价是模型能力受限（本地硬件跑不动 GPT-4 级别的模型）。

---

Configuration examples aligned with the current config schema. See Configuration reference for exhaustive per-field documentation.

与当前 config schema 对齐的配置示例。完整字段级文档见 Configuration reference。