# `openclaw models`

## 架构精读

> 跳过不影响阅读翻译正文。

### 模型管理——为什么需要专门的命令？

`openclaw models` 管理 AI 模型配置：

- **`models list`**：列出可用模型（provider + 模型名 + 上下文窗口）
- **`models set <model>`**：设置默认模型
- **`models test <model>`**：测试模型连通性

这跟 `kubectl get storageclass` 是一个思路——列出可用资源（存储类/模型），选择默认，验证连通性。

### 模型测试——为什么需要连通性测试？

`models test` 发送一个简单 prompt 验证模型可用：

```
openclaw models test gpt-4
```

这跟 `ping` 是一个思路——发送最小请求验证连通性，不需要实际使用。快速发现"API 密钥过期"或"模型下线"等问题。

---

Manages AI model configuration: `models list` (available models with provider, context window), `models set <model>` (set default), `models test <model>` (verify connectivity with simple prompt).

管理 AI 模型配置：`models list`（可用模型，含 provider、上下文窗口）、`models set <model>`（设置默认）、`models test <model>`（用简单 prompt 验证连通性）。
