# Alibaba Model Studio (阿里云百炼)

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
