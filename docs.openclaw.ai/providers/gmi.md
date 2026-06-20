# GMI Cloud

## 架构精读

> 跳过不影响阅读翻译正文。

### GPU 加速推理——专注硬件性能

GMI Cloud 为开源模型提供 GPU 加速推理。在多个开源推理 provider 中，GMI 的差异化是硬件配置和性能优化。对 OpenClaw agent 来说，选择 GMI 还是其他 provider 取决于**具体的性能需求和价格比较**。

---

GMI Cloud 为开源模型提供 GPU 加速推理。

## Getting started / 入门

```bash
export GMI_API_KEY="..."
openclaw onboard
# Choose "GMI Cloud"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "gmi/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `gmi/*` models through the GMI Cloud API.

OpenClaw 通过 GMI Cloud API 路由 `gmi/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
