# Hugging Face (推理)

## 架构精读

> 跳过不影响阅读翻译正文。

### 模型仓库的推理层——为什么 Hugging Face 做推理 API？

Hugging Face 本身是模型仓库（像 GitHub for ML models），但通过 Inference API 提供模型推理服务。这跟 GitHub 的 Actions 是一个思路——仓库本身是代码存储，Actions 加了一层执行能力。Hugging Face 的 Inference API 让模型从"可下载"变成"可调用"。

对 OpenClaw agent 来说，Hugging Face Inference 的价值是**长尾模型访问**。OpenAI/Anthropic 只提供几十个模型，Hugging Face 提供几十万个。当 agent 需要某个特定领域的微调模型（如医学 NER、法律文本分类），Hugging Face 是唯一选择。

---

Hugging Face 为开源模型提供推理端点。

## Getting started / 入门

```bash
export HUGGINGFACE_API_KEY="..."
openclaw onboard
# Choose "Hugging Face (推理)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "huggingface/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `huggingface/*` models through the Hugging Face (推理) API.

OpenClaw 通过 Hugging Face (推理) API 路由 `huggingface/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
