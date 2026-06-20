# Inworld

## 架构精读

> 跳过不影响阅读翻译正文。

### 虚拟角色引擎——agent 在游戏中的化身

Inworld 专门为游戏和模拟场景提供 AI 角色和 NPC（非玩家角色）生成。这跟 OpenAI/Anthropic（通用对话）的定位完全不同——Inworld 的模型优化了**角色扮演一致性**、情绪状态追踪和行为树集成。

对 OpenClaw agent 来说，Inworld 打开了一个独特的应用场景：**游戏 AI agent**。agent 可以控制 NPC 的行为逻辑——根据玩家动作动态调整 NPC 的对话和行为。这是 agent 从"工具使用"扩展到"角色扮演"的边界。

---

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
