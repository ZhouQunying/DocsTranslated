# Qianfan (千帆)

## 架构精读

> 跳过不影响阅读翻译正文。

### 百度的模型服务——ERNIE 系列的 API 入口

百度千帆提供 ERNIE 和其他模型的访问。这跟阿里 DashScope（Qwen）和腾讯 TokenHub（混元）是中国三大云厂商的模型服务平台。对 OpenClaw agent 来说，千帆的价值是**ERNIE 模型的访问**——ERNIE 在中文搜索和知识问答场景表现突出。

---

百度千帆提供 ERNIE 和其他模型的访问。

## Getting started / 入门

```bash
export QIANFAN_API_KEY="..."
openclaw onboard
# Choose "Qianfan (千帆)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "qianfan/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `qianfan/*` models through the Qianfan (千帆) API.

OpenClaw 通过 Qianfan (千帆) API 路由 `qianfan/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
