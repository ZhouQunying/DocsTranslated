# Qwen (通义千问)

## 架构精读

> 跳过不影响阅读翻译正文。

### DashScope API——阿里云模型服务的统一入口

Qwen Cloud 通过 DashScope API 访问阿里巴巴的 Qwen 模型。DashScope 是阿里云的统一模型服务平台，类似 AWS Bedrock 在 AWS 生态中的角色。对 OpenClaw agent 来说，Qwen 的价值是**中文场景优化**——Qwen 模型在中文理解和生成上表现优异，适合面向中文用户的 agent 工作流。

---

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
