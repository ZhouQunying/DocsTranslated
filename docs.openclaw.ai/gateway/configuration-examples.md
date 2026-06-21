# Configuration Examples

## 架构精读

> 跳过不影响阅读翻译正文。

### 渐进式复杂度——为什么从最小配置开始？

配置示例按复杂度递进：

1. **最小配置**：只有工作区 + WhatsApp 白名单（5 分钟上手）
2. **推荐入门配置**：加模型/工具配置文件/私信策略/提及门槛（生产就绪）
3. **扩展示例**：完整 JSON5 覆盖所有主要选项（按需学习）

这跟 React 学习曲线是一个思路——先写 `Hello`，再状态，再钩子，再上下文。先用最小配置跑起来，需要时加功能。

关键设计是**降低入门摩擦**。用户看到 100 行配置会被吓到，看到 5 行配置会觉得“这很简单”。

### 符号链接的同级技能仓库——为什么技能要符号链接到 Git 仓库？

技能目录可以符号链接到同级 Git 仓库：

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

这跟单体仓库的包共享是一个思路——技能放在 Git 仓库 = 代码审查 + 版本管理 + 多人协作 + 变更可追溯。`allowSymlinkTargets` 显式信任符号链接目标（防路径逃逸攻击）。

代价是配置稍复杂。但这让技能管理从“手动复制文件”升级到“Git 工作流”。

### 可信节点自动审批——为什么只在可信网络用？

```json5
{
  gateway: {
    pairing: {
      autoApproveNetworks: ["192.168.1.0/24"]
    }
  }
}
```

这跟 WiFi WPS 是一个思路——同一网络内设备自动配对，减少管理员负担。但必须配合网络白名单（CIDR 范围），只在可信网络（公司内网/实验室/Tailnet）使用。

代价是公共网络开启则任何人都能配对（安全风险）。

### 仅本地模型——为什么需要完全本地推理？

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

这跟气隙环境是一个思路——完全本地推理（LM Studio/Ollama），零成本、零网络依赖、零数据泄露风险。适合敏感数据/离线环境/成本敏感场景。

代价是模型能力受限（本地硬件跑不动 GPT-4 级别的模型）。

---

Configuration examples aligned with the current config schema. See Configuration reference for exhaustive per-field documentation.

与当前 config schema 对齐的配置示例。完整字段级文档见 Configuration reference。