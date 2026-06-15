# xAI (Grok)

xAI provides the Grok model family through its API, including web search and code execution capabilities.

xAI 通过其 API 提供 Grok 模型系列,包括网页搜索和代码执行能力。

## Getting started / 入门

```bash
export XAI_API_KEY="xai-..."
openclaw onboard
# Choose "xAI"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "xai/grok-4-1-fast"
      }
    }
  }
}
```

## Web search / 网页搜索

xAI models support web search grounding through the `x_search` tool. See [xAI web search](/tools/grok-search) for details.

xAI 模型通过 `x_search` 工具支持网页搜索 grounding。详情参见 [xAI 网页搜索](/tools/grok-search)。

## Code execution / 代码执行

xAI models support sandboxed Python code execution through the `code_execution` tool.

xAI 模型通过 `code_execution` 工具支持沙箱化 Python 代码执行。

## Speech-to-text / 语音转文本

xAI also provides speech-to-text capabilities. See the [xAI docs](https://docs.x.ai/) for details.

xAI 还提供语音转文本能力。详情参见 [xAI 文档](https://docs.x.ai/)。

## Model routing / 模型路由

OpenClaw routes `xai/*` models through the xAI API.

OpenClaw 通过 xAI API 路由 `xai/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
- [xAI web search](/tools/grok-search) — 网页搜索工具
