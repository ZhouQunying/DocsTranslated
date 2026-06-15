# Tencent Cloud (TokenHub)

Tencent Cloud (TokenHub)

腾讯云 TokenHub 提供混元和其他模型的访问。

## Getting started / 入门

```bash
export TENCENT_API_KEY="..."
openclaw onboard
# Choose "Tencent Cloud (TokenHub)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "tencent/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `tencent/*` models through the Tencent Cloud (TokenHub) API.

OpenClaw 通过 Tencent Cloud (TokenHub) API 路由 `tencent/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
