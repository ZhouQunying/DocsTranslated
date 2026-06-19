# fal

## 架构精读

> 跳过不影响阅读翻译正文。

### 无服务器媒体生成——冷启动和按需扩缩

fal 是无服务器图像/视频生成平台。这跟 AWS Lambda 是一个思路——不需要预置 GPU 服务器，按需启动推理实例。对 agent 来说，fal 的价值是**零运维的媒体生成能力**——agent 可以调用图像生成而不需要管理 GPU 基础设施。

---

fal 通过其无服务器平台提供快速图像和视频生成。

## Getting started / 入门

```bash
export FAL_KEY="..."
openclaw onboard
# Choose "fal"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "fal/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `fal/*` models through the fal API.

OpenClaw 通过 fal API 路由 `fal/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
