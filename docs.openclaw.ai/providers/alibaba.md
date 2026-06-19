# Alibaba Model Studio (阿里云百炼)

## 架构精读

> 跳过不影响阅读翻译正文。

### 视频生成 + 多密钥支持——百炼的多表面能力

阿里云百炼（DashScope 国际版）不仅提供文本模型（Qwen），还通过 Wan 模型提供视频生成。OpenClaw 的 `alibaba` 插件默认启用，支持多种 API key 环境变量（`MODELSTUDIO_API_KEY`、`DASHSCOPE_API_KEY`、`QWEN_API_KEY`）。

这跟 AWS 的"一个账号多种服务"是一个思路——同一个阿里云账号可以同时使用文本模型和视频生成。对 OpenClaw agent 来说，这意味着**一个 provider 覆盖文本和视频**——`qwen/*` 做文本，`alibaba/*` 做视频生成。

---

OpenClaw ships a bundled `alibaba` plugin that registers a video-generation provider for Wan models on Alibaba Model Studio (the international name for DashScope). The plugin is enabled by default; you only need to set an API key.

OpenClaw 附带一个 `alibaba` 插件,为阿里云百炼(DashScope 的国际名称)上的 Wan 模型注册视频生成提供者。插件默认启用;你只需设置 API 密钥。

## Getting started / 入门

```bash
export MODELSTUDIO_API_KEY="..."
# or
export DASHSCOPE_API_KEY="..."
# or
export QWEN_API_KEY="..."

openclaw onboard --auth-choice alibaba-model-studio-api-key --alibaba-model-studio-api-key <key>
```

## Configuration / 配置

```json5
{
  models: {
    providers: {
      alibaba: {
        apiKey: "..."
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `alibaba/*` models through the DashScope API (international endpoint: `https://dashscope-intl.aliyuncs.com`).

OpenClaw 通过 DashScope API 路由 `alibaba/*` 模型(国际端点:`https://dashscope-intl.aliyuncs.com`)。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Qwen](/providers/qwen) — 通义千问文本模型
- [Models](/providers/models) — 模型配置
