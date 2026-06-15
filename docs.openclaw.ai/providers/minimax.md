# MiniMax

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
