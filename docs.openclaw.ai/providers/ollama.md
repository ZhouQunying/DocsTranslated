# Ollama

## 架构精读

> 跳过不影响阅读翻译正文。

### 三种模式——为什么同一个 provider ID 覆盖本地和云端？

Ollama 在 OpenClaw 中有三种使用模式：Cloud + Local、Cloud only、Local only。但更关键的是 `ollama-cloud` 被注册为**一等托管 provider ID**。

这跟 Docker 的"本地 daemon vs Docker Hub"是一个思路。Docker CLI 用同一个 `docker` 命令操作本地容器和远程 registry。本地和云端共享接口，但路由不同。OpenClaw 的 `ollama/*` 走本地主机，`ollama-cloud/*` 走云端——同一生态，不同路由。

设计意图是**渐进式迁移**。开发者在本地用 Ollama 开发和测试（零成本），然后在生产环境切换到 Ollama Cloud（托管、高可用）。切换只需要改 model ID 前缀，不需要改代码或配置。

代价是 `ollama` 和 `ollama-cloud` 共享模型名称但走不同路径，可能造成混淆。所以文档建议"当你想要仅云端路由而不共享本地 ollama provider id 时"显式使用 `ollama-cloud/*`。

---

OpenClaw integrates with Ollama's native API (`/api/chat`) for hosted cloud models and local/self-hosted Ollama servers. You can use Ollama in three modes:

OpenClaw 集成 Ollama 的原生 API(``/api/chat``)用于托管云端模型和本地/自托管 Ollama 服务器。你可以在三种模式下使用 Ollama:

- **Cloud + Local** — through a reachable Ollama host
  
  **云端 + 本地** — 通过可达的 Ollama 主机

- **Cloud only** — against `https://ollama.com`
  
  **仅云端** — 针对 `https://ollama.com`

- **Local only** — against a reachable Ollama host
  
  **仅本地** — 针对可达的 Ollama 主机

OpenClaw also registers `ollama-cloud` as a first-class hosted provider id for direct Ollama Cloud use. Use refs like `ollama-cloud/kimi-k2.5:cloud` when you want cloud-only routing without sharing the local `ollama` provider id.

OpenClaw 还将 `ollama-cloud` 注册为一等托管提供者 id 用于直接 Ollama Cloud 使用。当你想要仅云端路由而不共享本地 `ollama` 提供者 id 时,使用如 `ollama-cloud/kimi-k2.5:cloud` 的引用。

For the dedicated cloud-only setup page, see [Ollama Cloud](/providers/ollama-cloud).

专用仅云端设置页面,参见 [Ollama Cloud](/providers/ollama-cloud)。

## Getting started / 入门

### Cloud + Local / 云端 + 本地

```bash
openclaw onboard
# Choose "Ollama" - auto-detects local host and cloud
```

### Local only / 仅本地

```bash
export OLLAMA_HOST="http://localhost:11434"
openclaw onboard
# Choose "Ollama"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ollama/llama3.3"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `ollama/*` models through the Ollama provider. Local models use the reachable host; cloud models route through `ollama-cloud`.

OpenClaw 通过 Ollama 提供者路由 `ollama/*` 模型。本地模型使用可达主机;云端模型通过 `ollama-cloud` 路由。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Ollama Cloud](/providers/ollama-cloud) — 仅云端设置
- [Models](/providers/models) — 模型配置
