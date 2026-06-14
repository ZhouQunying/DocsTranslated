# MiniMax Search

OpenClaw 支持 MiniMax 作为 `web_search` 提供者，通过 MiniMax Token Plan 搜索 API。返回带标题、URL、摘要和相关查询的结构化搜索结果。

## 获取 Token Plan 凭据

1. 从 [MiniMax Platform](https://platform.minimax.io/user-center/basic-information/interface-key) 创建或复制 MiniMax Token Plan 密钥。OAuth 设置可复用 `MINIMAX_OAUTH_TOKEN`
2. 在 Gateway 环境中设置 `MINIMAX_CODE_PLAN_KEY`，或通过以下方式配置：

```bash
openclaw configure --section web
```

OpenClaw 也接受 `MINIMAX_CODING_API_KEY`、`MINIMAX_OAUTH_TOKEN` 和 `MINIMAX_API_KEY` 作为环境变量别名。`MINIMAX_API_KEY` 应指向启用了搜索的 Token Plan 凭据；普通 MiniMax 模型 API 密钥可能不被 Token Plan 搜索端点接受。

## 配置

```json5
{
  plugins: {
    entries: {
      minimax: {
        config: {
          webSearch: {
            apiKey: "sk-cp-...", // 如设置了 MiniMax Token Plan 环境变量则可省略
            region: "global", // 或 "cn"
          },
        },
      },
    },
  },
  tools: {
    web: {
      search: {
        provider: "minimax",
      },
    },
  },
}
```

**环境替代方案：** 在 Gateway 环境中设置 `MINIMAX_CODE_PLAN_KEY`、`MINIMAX_CODING_API_KEY`、`MINIMAX_OAUTH_TOKEN` 或 `MINIMAX_API_KEY`。对于网关安装，放在 `~/.openclaw/.env` 中。

## 区域选择

MiniMax 搜索使用以下端点：

- 全球：`https://api.minimax.io/v1/coding_plan/search`
- 中国：`https://api.minimaxi.com/v1/coding_plan/search`

如 `plugins.entries.minimax.config.webSearch.region` 未设置，OpenClaw 按此顺序解析区域：

1. `tools.web.search.minimax.region` / 插件自有的 `webSearch.region`
2. `MINIMAX_API_HOST`
3. `models.providers.minimax.baseUrl`
4. `models.providers.minimax-portal.baseUrl`

这意味着中国引导或 `MINIMAX_API_HOST=https://api.minimaxi.com/...` 会自动将 MiniMax 搜索也保持在中国主机上。

即使通过 OAuth `minimax-portal` 路径认证了 MiniMax，网页搜索仍注册为提供者 id `minimax`；OAuth 提供者基础 URL 用作中国/全球主机选择的区域提示，`MINIMAX_OAUTH_TOKEN` 可满足 MiniMax 搜索的 bearer 凭据。

## 支持的参数

| 参数 | 类型 | 约束 | 描述 |
| --- | --- | --- | --- |
| `query` | string | 必填 | 搜索查询字符串 |
| `count` | integer | 1-10 | 返回结果数。OpenClaw 将返回列表裁剪到此大小 |

目前不支持提供者特定的过滤器。

## 相关

- [网页搜索概览](/tools/web)——所有提供者和自动检测
- [MiniMax](/providers/minimax)——模型、图像、语音和认证设置
