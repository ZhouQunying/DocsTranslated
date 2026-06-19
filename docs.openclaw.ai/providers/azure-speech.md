# Azure Speech

## 架构精读

> 跳过不影响阅读翻译正文。

### 企业级语音服务——Azure 生态的集成优势

Azure Speech 通过 Azure Cognitive Services 提供语音服务。跟 Deepgram（专注精度）和 ElevenLabs（专注质量）不同，Azure Speech 的价值是**Azure 生态集成**——如果你的基础设施已经在 Azure 上，用 Azure Speech 避免了跨云网络延迟和额外供应商管理。

---

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
