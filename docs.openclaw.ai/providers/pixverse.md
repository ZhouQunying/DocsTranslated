# PixVerse

## 架构精读

> 跳过不影响阅读翻译正文。

### 视频生成竞争——Runway 之外的选择

PixVerse 提供 AI 视频生成，是 Runway 的竞争者。对 OpenClaw agent 来说，多一个视频生成 provider 意味着**故障转移和成本优化**——当 Runway API 不可用或价格不合适时，可以切换到 PixVerse。

---

PixVerse 提供 AI 视频生成。

## Getting started / 入门

```bash
export PIXVERSE_API_KEY="..."
openclaw onboard
# Choose "PixVerse"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "pixverse/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `pixverse/*` models through the PixVerse API.

OpenClaw 通过 PixVerse API 路由 `pixverse/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
