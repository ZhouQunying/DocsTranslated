# ComfyUI

## 架构精读

> 跳过不影响阅读翻译正文。

### 节点工作流——可视化编程的图像生成

ComfyUI 用基于节点的工作流系统生成图像和视频。这跟 Unreal Engine 的蓝图系统是一个思路——用可视化节点连接替代代码编写。对 OpenClaw agent 来说，ComfyUI 的价值是**可组合的图像生成管线**——agent 可以动态组装不同的工作流节点，实现复杂的图像编辑任务。

---

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
