# ds4 (本地 DeepSeek V4)

## 架构精读

> 跳过不影响阅读翻译正文。

### MLX on Apple Silicon——为什么不用 CUDA？

ds4 通过 Apple 的 MLX 框架在 Apple Silicon 上本地运行 DeepSeek V4。这跟 CUDA 的 GPU 推理是一个思路，但针对 Apple 的统一内存架构优化。MLX 利用 M 系列芯片的统一内存（CPU 和 GPU 共享同一块内存），避免了 CUDA 的"CPU 到 GPU 内存拷贝"瓶颈。

对 OpenClaw 来说，ds4 的价值是**Mac 用户的零成本推理**。开发者不需要 GPU 服务器或 API 费用——MacBook Pro 就能运行 DeepSeek V4。代价是只支持 Apple Silicon，且模型选择有限。

---

ds4 通过 MLX 在 Apple Silicon 上本地运行 DeepSeek V4。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "ds4 (本地 DeepSeek V4)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ds4/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `ds4/*` models through the ds4 (本地 DeepSeek V4) API.

OpenClaw 通过 ds4 (本地 DeepSeek V4) API 路由 `ds4/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
