# Vydra

## 架构精读

> 跳过不影响阅读翻译正文。

### 优化路由——跟 Kilocode 类似的定位

Vydra 提供带优化路由的托管推理，定位类似 Kilocode。在 OpenClaw 的 provider 列表中，多个同类 provider 的存在说明了一个架构原则：**冗余和选择**。agent 系统需要多个后端以保证可用性，provider 之间的竞争也推动了价格和服务质量的改善。

---

Vydra 提供带优化路由的托管推理。

## Getting started / 入门

```bash
export VYDRA_API_KEY="..."
openclaw onboard
# Choose "Vydra"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "vydra/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `vydra/*` models through the Vydra API.

OpenClaw 通过 Vydra API 路由 `vydra/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
