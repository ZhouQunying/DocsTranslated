# Volcengine (Doubao)

Volcengine (Doubao)

火山引擎提供字节跳动豆包模型系列的访问。

## Getting started / 入门

```bash
export VOLCENGINE_API_KEY="..."
openclaw onboard
# Choose "Volcengine (Doubao)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "volcengine/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `volcengine/*` models through the Volcengine (Doubao) API.

OpenClaw 通过 Volcengine (Doubao) API 路由 `volcengine/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
