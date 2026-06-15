# Azure Speech

Azure Speech

Azure Speech 通过 Azure Cognitive Services 提供语音转文本和文本转语音。

## Getting started / 入门

```bash
export AZURE_SPEECH_KEY="..."
openclaw onboard
# Choose "Azure Speech"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "azure-speech/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `azure-speech/*` models through the Azure Speech API.

OpenClaw 通过 Azure Speech API 路由 `azure-speech/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
