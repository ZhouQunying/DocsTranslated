# Google (Gemini)

Google provides access to the Gemini model family through the Gemini API and Vertex AI.

Google 通过 Gemini API 和 Vertex AI 提供 Gemini 模型系列的访问。

## Getting started / 入门

### API key / API 密钥

```bash
export GOOGLE_API_KEY="..."
openclaw onboard
# Choose "Google (Gemini)"
```

### OAuth (google-gemini-cli) / OAuth 认证

```bash
openclaw onboard --auth-choice google-gemini-cli
```

Requires a local `gemini` install (`brew install gemini-cli` or `npm install -g @google/gemini-cli`).

需要本地 `gemini` 安装(`brew install gemini-cli` 或 `npm install -g @google/gemini-cli`)。

### Vertex AI / Vertex AI

```bash
# Install the Anthropic Vertex provider plugin
openclaw plugins install @openclaw/anthropic-vertex-provider

# Configure Vertex credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "google/gemini-3-pro"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `google/*` models through the Gemini API or Vertex AI depending on credentials.

OpenClaw 根据凭证通过 Gemini API 或 Vertex AI 路由 `google/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
