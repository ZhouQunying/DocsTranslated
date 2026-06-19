# Runway

## 架构精读

> 跳过不影响阅读翻译正文。

### 视频生成作为 agent 能力——从文本到视频的管线

Runway 是视频生成领域的领先提供商（Gen-2/Gen-3）。对 OpenClaw agent 来说，Runway 把 agent 的输出能力从文本扩展到了视频。这实现了**文本到视频**的完整工作流——agent 生成脚本，Runway 把脚本转为视频。

---

Runway 提供 AI 视频和图像生成。

## Getting started / 入门

```bash
export RUNWAY_API_KEY="..."
openclaw onboard
# Choose "Runway"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "runway/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `runway/*` models through the Runway API.

OpenClaw 通过 Runway API 路由 `runway/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
