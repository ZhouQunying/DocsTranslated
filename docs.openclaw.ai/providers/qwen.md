# Qwen (通义千问)

Qwen Cloud provides access to Alibaba's Qwen model family through the DashScope API.

Qwen Cloud 通过 DashScope API 提供阿里巴巴 Qwen 模型系列的访问。

## Getting started / 入门

```bash
export DASHSCOPE_API_KEY="sk-..."
openclaw onboard
# Choose "Qwen"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "qwen/qwen-max"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `qwen/*` models through the DashScope API.

OpenClaw 通过 DashScope API 路由 `qwen/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Qwen OAuth](/providers/qwen-oauth) — OAuth 认证
- [Models](/providers/models) — 模型配置
