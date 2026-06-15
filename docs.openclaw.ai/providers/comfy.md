# ComfyUI

ComfyUI

ComfyUI 通过其基于节点的工作流系统提供图像和视频生成。

## Getting started / 入门

```bash
export COMFY_API_KEY="..."
openclaw onboard
# Choose "ComfyUI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "comfy/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `comfy/*` models through the ComfyUI API.

OpenClaw 通过 ComfyUI API 路由 `comfy/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
