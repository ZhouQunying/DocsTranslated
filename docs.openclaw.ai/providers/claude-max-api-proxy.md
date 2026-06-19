# Claude Max API proxy

## 架构精读

> 跳过不影响阅读翻译正文。

### 订阅计划当 API——绕过按量计费

Claude Max API proxy 通过 Claude Max 订阅计划路由请求，而非 Anthropic 的按量计费 API。这跟 github-copilot 的认证复用是一个思路——利用已有的订阅基础设施。

设计意图是**成本可预测性**。API 按量计费意味着账单不可预测——agent 的高频调用可能产生意外的高额账单。Claude Max 订阅是固定月费，无论调用多少次。对于高频 agent 使用，订阅计划比按量计费便宜得多。

代价是订阅计划有速率限制和使用政策。如果 agent 的调用模式违反了订阅条款（如自动化过度使用），可能被限制或封禁。

---

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
