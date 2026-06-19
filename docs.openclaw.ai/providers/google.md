# Google (Gemini)

## 架构精读

> 跳过不影响阅读翻译正文。

### Gemini API vs Vertex AI——凭证驱动的路由选择

Google 提供两条访问 Gemini 模型的路径：Gemini API（API key 或 OAuth）和 Vertex AI（GCP 服务账户）。OpenClaw 根据可用凭证自动选择路由。

这跟 AWS SDK 的"默认凭证链"是一个思路。AWS SDK 按顺序检查：环境变量 → 共享凭证文件 → EC2 实例角色 → ECS 任务角色。第一个找到的凭证被使用。OpenClaw 对 Google 也类似：如果有 GOOGLE_API_KEY 就走 Gemini API，如果有 GOOGLE_APPLICATION_CREDENTIALS 就走 Vertex AI。

设计意图是**同一 model ID 跨环境工作**。开发者在本地用 API key 测试，在生产环境用 Vertex AI 的服务账户。代码和配置不变，只是凭证不同。

代价是路由行为隐式——用户可能不清楚自己的请求走了哪条路径。但文档明确了优先级，且 Vertex AI 需要安装额外插件（`@openclaw/anthropic-vertex-provider`），所以不会意外走错路径。

---

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
