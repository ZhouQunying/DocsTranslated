# Venice AI

## 架构精读

> 跳过不影响阅读翻译正文。

### 隐私优先——无数据保留的推理

Venice AI 的核心承诺是**无数据保留**——请求不被记录、不被用于训练。这跟 DuckDuckGo 的隐私搜索是一个思路。对 OpenClaw agent 来说，Venice 适合处理敏感数据——当 agent 需要分析机密文档或用户隐私信息时，无数据保留的 provider 是必要的安全保障。

---

Venice AI 提供隐私优先的推理,无数据保留。

## Getting started / 入门

```bash
export VENICE_API_KEY="..."
openclaw onboard
# Choose "Venice AI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "venice/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `venice/*` models through the Venice AI API.

OpenClaw 通过 Venice AI API 路由 `venice/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
