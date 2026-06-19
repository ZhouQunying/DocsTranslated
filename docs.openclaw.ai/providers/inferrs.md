# inferrs (本地模型)

## 架构精读

> 跳过不影响阅读翻译正文。

### 自定义推理服务器——为什么需要另一个本地推理引擎？

inferrs 是另一个本地模型推理服务器，提供 OpenAI 兼容 API。跟 vLLM（高吞吐生产服务）、SGLang（结构化生成）、LM Studio（桌面 GUI）相比，inferrs 的定位是**轻量灵活的自托管推理**。当现有引擎不满足特定需求（如自定义模型格式、特殊硬件适配），inferrs 提供更灵活的配置。

---

inferrs 通过 OpenAI 兼容 API 提供本地模型服务。

## Getting started / 入门

```bash
export INFERRS_API_KEY="..."
openclaw onboard
# Choose "inferrs (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "inferrs/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `inferrs/*` models through the inferrs (本地模型) API.

OpenClaw 通过 inferrs (本地模型) API 路由 `inferrs/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
