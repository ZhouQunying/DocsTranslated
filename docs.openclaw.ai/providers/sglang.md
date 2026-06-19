# SGLang (本地模型)

## 架构精读

> 跳过不影响阅读翻译正文。

### 结构化生成——为什么 agent 需要 JSON 约束？

SGLang 的核心能力是结构化生成——通过约束解码保证输出符合预定义的 schema（如 JSON Schema）。这跟 TypeScript 的类型系统是一个思路——编译时保证类型安全，SGLang 在解码时保证格式安全。

对 OpenClaw agent 来说，结构化生成解决了**工具调用可靠性**问题。agent 的工具调用必须是合法 JSON，但普通 LLM 经常生成格式错误的 JSON。SGLang 的约束解码保证每次输出都是合法 JSON，减少了解析失败和重试。

---

SGLang 提供带结构化生成的快速本地模型服务。

## Getting started / 入门

```bash
export N/A="..."
openclaw onboard
# Choose "SGLang (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "sglang/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `sglang/*` models through the SGLang (本地模型) API.

OpenClaw 通过 SGLang (本地模型) API 路由 `sglang/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
