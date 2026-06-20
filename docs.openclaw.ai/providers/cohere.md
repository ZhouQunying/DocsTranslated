# Cohere

## 架构精读

> 跳过不影响阅读翻译正文。

### 外部化过渡——bundled plugin 到 external plugin 的迁移模式

Cohere 在 OpenClaw 中有一个独特的状态：**在外部化过渡期间 bundled**。这意味着 Cohere provider 目前内置在 OpenClaw 中，但同时也发布为官方外部插件（`@openclaw/cohere-provider`）。

这跟 Kubernetes 的 in-tree vs out-of-tree 插件迁移是一个思路。Kubernetes 把 CSI 驱动、CNI 插件从内核中逐步外部化——先保持 in-tree 可用性，同时发布 out-of-tree 版本，让用户平滑迁移。OpenClaw 对 Cohere 的处理也是这样：bundled 版本保证现有用户不受影响，external plugin 版本是未来方向。

设计意图是**渐进式架构演进**。如果把 Cohere provider 直接从 bundled 移除，现有用户的配置立刻失效。如果永远不外部化，核心包越来越大，每个新 provider 都膨胀主包。外部化过渡让用户有时间迁移，同时核心包保持精简。

### OpenAI-compatible API——为什么 Command A 走 OpenAI 协议？

Cohere 的 Compatibility API 使用 OpenAI 兼容协议（`openai-completions`），base URL 是 `https://api.cohere.ai/compatibility/v1`。这跟 Mistral、Together AI 等越来越多 provider 采用 OpenAI 兼容协议是一个趋势。

设计意图是**降低集成成本**。如果每个 provider 都用自己的协议，OpenClaw 需要为每个 provider 写适配器。OpenAI 兼容协议成了事实标准——provider 端做协议适配，OpenClaw 端用统一的 OpenAI 客户端调用。这跟 HTTP 统一了 Web 协议是一个思路。

---

Cohere provides OpenAI-compatible inference through its Compatibility API. OpenClaw ships the Cohere provider during its externalization transition and also publishes it as an official external plugin with the Command A model catalog.

Cohere 通过其 Compatibility API 提供 OpenAI 兼容推理。OpenClaw 在外部化过渡期间附带 Cohere provider，并将其作为官方外部插件发布，包含 Command A 模型目录。

| Property | Value |
|----------|-------|
| Provider id | `cohere` |
| Plugin | bundled during transition; official external package |
| Auth env var | `COHERE_API_KEY` |
| Onboarding flag | `--auth-choice cohere-api-key` |
| Direct CLI flag | `--cohere-api-key <key>` |
| API | OpenAI-compatible (`openai-completions`) |
| Base URL | `https://api.cohere.ai/compatibility/v1` |
| Default model | `cohere/command-a-03-2025` |

## Get started / 入门

Cohere is included in current OpenClaw packages. If it is unavailable, install the external package and restart the Gateway:

Cohere 包含在当前 OpenClaw 包中。如果不可用，安装外部包并重启 Gateway：

```bash
openclaw plugins install @openclaw/cohere-provider
openclaw gateway restart
```

Create a Cohere API key. Run onboarding:

创建 Cohere API 密钥。运行入门：

```bash
openclaw onboard --non-interactive \
  --auth-choice cohere-api-key \
  --cohere-api-key "$COHERE_API_KEY"
```

Confirm the catalog is available:

确认可用：

```bash
openclaw models list --provider cohere
```

The default model is set only when no primary model is already configured.

默认模型仅在没有主模型已配置时设置。

## Environment-only setup / 仅环境变量设置

Make `COHERE_API_KEY` available to the Gateway process, then select the Cohere model:

使 `COHERE_API_KEY` 对 Gateway 进程可用，然后选择 Cohere 模型：

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "cohere/command-a-03-2025"
      }
    }
  }
}
```

If the Gateway runs as a daemon or in Docker, configure `COHERE_API_KEY` for that service. Exporting it only in an interactive shell does not make it available to an already-running Gateway.

如果 Gateway 作为守护进程或在 Docker 中运行，为该服务配置 `COHERE_API_KEY`。仅在交互式 shell 中导出它不会使其对已运行的 Gateway 可用。

## 相关 / Related

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
