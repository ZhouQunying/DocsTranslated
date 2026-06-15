# NVIDIA

NVIDIA

NVIDIA 通过其 NIM 微服务和 API 目录提供推理。

## Getting started / 入门

```bash
export NVIDIA_API_KEY="..."
openclaw onboard
# Choose "NVIDIA"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "nvidia/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `nvidia/*` models through the NVIDIA API.

OpenClaw 通过 NVIDIA API 路由 `nvidia/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
