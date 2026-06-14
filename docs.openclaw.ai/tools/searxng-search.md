# SearXNG Search

OpenClaw 支持 [SearXNG](https://docs.searxng.org/) 作为**自托管、无需密钥**的 `web_search` 提供者。SearXNG 是开源元搜索引擎，聚合来自 Google、Bing、DuckDuckGo 和其他来源的结果。

优势：

- **免费且无限制**——无需 API 密钥或商业订阅
- **隐私/气隙**——查询不离开你的网络
- **随处可用**——无商业搜索 API 的区域限制

## 设置

1. **运行 SearXNG 实例**：

```bash
docker run -d -p 8888:8080 searxng/searxng
```

或使用你可访问的任何现有 SearXNG 部署。参见 [SearXNG 文档](https://docs.searxng.org/)了解生产设置。

2. **配置**：

```bash
openclaw configure --section web
# 选择 "searxng" 作为提供者
```

或设置环境变量让自动检测发现：

```bash
export SEARXNG_BASE_URL="http://localhost:8888"
```

## 配置

```json5
{
  tools: {
    web: {
      search: {
        provider: "searxng",
      },
    },
  },
}
```

SearXNG 实例的插件级设置：

```json5
{
  plugins: {
    entries: {
      searxng: {
        config: {
          webSearch: {
            baseUrl: "http://localhost:8888",
            categories: "general,news", // 可选
            language: "en", // 可选
          },
        },
      },
    },
  },
}
```

`baseUrl` 字段也接受 SecretRef 对象。

传输规则：

- `https://` 适用于公共或私有 SearXNG 主机
- `http://` 仅在受信任的私有网络或回环主机上被接受
- 公共 SearXNG 主机必须使用 `https://`
- 私有/内部主机使用自托管网络守卫；公共 `https://` 主机保持严格的网页搜索守卫，不能重定向到私有地址

## 环境变量

设置 `SEARXNG_BASE_URL` 作为配置的替代方案：

```bash
export SEARXNG_BASE_URL="http://localhost:8888"
```

当 `SEARXNG_BASE_URL` 已设置且未配置显式提供者时，自动检测会自动选择 SearXNG（最低优先级——任何有密钥的 API 提供者优先）。

## 插件配置参考

| 字段 | 描述 |
| --- | --- |
| `baseUrl` | SearXNG 实例的基础 URL（必填） |
| `categories` | 逗号分隔的类别，如 `general`、`news` 或 `science` |
| `language` | 结果的语言代码，如 `en`、`de` 或 `fr` |

## 注意事项

- **JSON API**——使用 SearXNG 原生的 `format=json` 端点，非 HTML 抓取
- **图片结果 URL**——当 SearXNG 返回直接图片 URL 时，图片类别结果包含 `img_src`
- **无需 API 密钥**——开箱即用，适用于任何 SearXNG 实例
- **基础 URL 验证**——`baseUrl` 必须是有效的 `http://` 或 `https://` URL；公共主机必须使用 `https://`
- **网络守卫**——私有/内部 SearXNG 端点选择加入私有网络访问；公共 `https://` SearXNG 端点保持严格 SSRF 保护
- **自动检测顺序**——SearXNG 最后检查（顺序 200）。配置了密钥的 API 提供者优先，然后是 DuckDuckGo（顺序 100），再是 Ollama Web Search（顺序 110）
- **自托管**——你控制实例、查询和上游搜索引擎
- **类别**未配置时默认为 `general`
- **类别回退**——如非 `general` 类别请求成功但返回零结果，OpenClaw 会用 `general` 重试一次后再返回空结果集

SearXNG JSON API 要正常工作，确保 SearXNG 实例的 `settings.yml` 中 `search.formats` 启用了 `json` 格式。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [DuckDuckGo Search](/tools/duckduckgo-search)——另一个无需密钥的回退
- [Brave Search](/tools/brave-search)——带免费层的结构化结果
