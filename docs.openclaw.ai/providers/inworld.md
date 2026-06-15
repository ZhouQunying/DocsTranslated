# Inworld

Inworld

Inworld 为游戏和模拟提供 AI 角色和 NPC 生成。

## Getting started / 入门

```bash
export INWORLD_API_KEY="..."
openclaw onboard
# Choose "Inworld"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "inworld/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `inworld/*` models through the Inworld API.

OpenClaw 通过 Inworld API 路由 `inworld/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
