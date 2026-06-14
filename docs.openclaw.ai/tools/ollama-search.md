# Ollama Web Search

OpenClaw 支持 **Ollama Web Search** 作为捆绑的 `web_search` 提供者。它使用 Ollama 的网页搜索 API，返回带标题、URL 和摘要的结构化结果。

对于本地或自托管 Ollama，此设置默认不需要 API 密钥。但需要：

- OpenClaw 可达的 Ollama 主机
- `ollama signin`

对于直接托管搜索，将 Ollama 提供者基础 URL 设为 `https://ollama.com` 并提供真实的 `OLLAMA_API_KEY`。

## 设置

1. **启动 Ollama**：确保 Ollama 已安装并运行
2. **登录**：运行 `ollama signin`
3. **选择 Ollama Web Search**：

```bash
openclaw configure --section web
# 选择 "Ollama Web Search" 作为提供者
```

如已使用 Ollama 进行模型推理，Ollama Web Search 复用相同配置的主机。

## 配置

```json5
{
  tools: {
    web: {
      search: {
        provider: "ollama",
      },
    },
  },
}
```

可选的 Ollama 主机覆盖：

```json5
{
  plugins: {
    entries: {
      ollama: {
        config: {
          webSearch: {
            baseUrl: "http://ollama-host:11434",
          },
        },
      },
    },
  },
}
```

如已将 Ollama 配置为模型提供者，网页搜索提供者可复用该主机：

```json5
{
  models: {
    providers: {
      ollama: {
        baseUrl: "http://ollama-host:11434",
      },
    },
  },
}
```

Ollama 模型提供者使用 `baseUrl` 作为规范键。网页搜索提供者也兼容 `models.providers.ollama` 上的 `baseURL`，以适配 OpenAI SDK 风格的配置示例。

如未设置显式 Ollama 基础 URL，OpenClaw 使用 `http://127.0.0.1:11434`。

如 Ollama 主机需要 bearer 认证，OpenClaw 复用 `models.providers.ollama.apiKey`（或匹配的环境变量提供者认证）对该配置主机的请求。

直接托管 Ollama Web Search：

```json5
{
  models: {
    providers: {
      ollama: {
        baseUrl: "https://ollama.com",
        apiKey: "OLLAMA_API_KEY",
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "ollama",
      },
    },
  },
}
```

## 注意事项

- 此提供者不需要网页搜索特定的 API 密钥字段
- 如 Ollama 主机受认证保护，OpenClaw 在存在时复用普通 Ollama 提供者 API 密钥
- 如 `baseUrl` 为 `https://ollama.com`，OpenClaw 直接调用 `https://ollama.com/api/web_search` 并将配置的 Ollama API 密钥作为 bearer 认证发送
- 如配置的主机不暴露网页搜索且设置了 `OLLAMA_API_KEY`，OpenClaw 可回退到 `https://ollama.com/api/web_search` 而不将该环境密钥发送到本地主机
- 如 Ollama 不可达或未登录，OpenClaw 在设置期间警告但不阻止选择
- 运行时自动检测可在没有更高优先级凭据提供者时回退到 Ollama Web Search
- 本地 Ollama 守护进程主机使用本地代理端点 `/api/experimental/web_search`，签名并转发到 Ollama Cloud
- `https://ollama.com` 主机直接使用公共托管端点 `/api/web_search` 和 bearer API 密钥认证

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [Ollama](/providers/ollama)——Ollama 模型设置和云/本地模式
