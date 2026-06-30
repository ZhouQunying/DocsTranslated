# `openclaw infer`

## 架构精读

> 跳过不影响阅读翻译正文。

### 直接推理——为什么绕过智能体？

`openclaw infer` 直接调用 AI 模型进行单次推理，绕过智能体的工具、记忆和会话管理：

```
openclaw infer "What is the capital of France?"
```

这跟 `curl` 直接调用 API 是一个思路——不需要经过应用层（智能体），直接调用底层（模型）。适合快速测试、脚本集成、调试模型行为。

### 模型覆盖——为什么支持 `--model`？

`--model gpt-4` 指定模型，覆盖配置文件中的默认模型。

这跟 `docker run --image` 是一个思路——临时覆盖默认配置，不需要修改配置文件。适合"用不同模型测试同一个 prompt"。

---

Direct single-turn inference bypassing agent (tools, memory, session management). Supports `--model` override for testing different models with the same prompt. Like `curl` to the AI API directly.

直接单次推理，绕过智能体（工具、记忆、会话管理）。支持 `--model` 覆盖，用不同模型测试同一个 prompt。类似直接 `curl` AI API。
