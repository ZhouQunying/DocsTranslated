# Claude Max API proxy

Claude Max API proxy

Claude Max API proxy 通过 Claude Max 订阅路由请求。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "Claude Max API proxy"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "claude-max-api-proxy/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `claude-max-api-proxy/*` models through the Claude Max API proxy API.

OpenClaw 通过 Claude Max API proxy API 路由 `claude-max-api-proxy/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
