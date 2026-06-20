# MiniMax

## 架构精读

> 跳过不影响阅读翻译正文。

### 一个 provider 三种模态——文本、语音、视频

MiniMax 在一个 provider 中提供文本、语音和视频生成。这跟 xAI（搜索+代码+语音）类似，但 MiniMax 更专注多模态生成。对 OpenClaw agent 来说，MiniMax 的价值是**单一配置覆盖多种生成需求**——不需要为每种模态配置不同 provider。

---

MiniMax provides multimodal AI models through its API, including text, speech, and video generation.

MiniMax 通过其 API 提供多模态 AI 模型,包括文本、语音和视频生成。

## Getting started / 入门

```bash
export MINIMAX_API_KEY="..."
openclaw onboard
# Choose "MiniMax"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "minimax/minimax-text-01"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `minimax/*` models through the MiniMax API.

OpenClaw 通过 MiniMax API 路由 `minimax/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
