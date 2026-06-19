# LM Studio (本地模型)

## 架构精读

> 跳过不影响阅读翻译正文。

### 桌面优先——为什么不是所有本地推理都需要命令行？

LM Studio 是桌面应用，提供 GUI 下载和运行本地模型。这跟 Docker Desktop 是一个思路——不是所有用户都 comfortable 用 `docker run` 命令行，GUI 降低了门槛。

对 OpenClaw 来说，LM Studio 的价值是**零配置本地推理**。开发者安装 LM Studio，点击下载模型，LM Studio 自动启动 OpenAI 兼容 API 服务器。OpenClaw 连接 `localhost:1234` 就能用。不需要配置 Python 环境、不需要安装 CUDA、不需要理解模型格式。

---

LM Studio 通过 OpenAI 兼容 API 提供本地模型推理。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "LM Studio (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "lmstudio/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `lmstudio/*` models through the LM Studio (本地模型) API.

OpenClaw 通过 LM Studio (本地模型) API 路由 `lmstudio/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
