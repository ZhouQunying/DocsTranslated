# Memory LanceDB 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么要在内置记忆之外再加一层向量数据库？

内置 `memory-core` 用 Markdown 文件存记忆，检索靠关键词和语义打分。对于"我上次说过什么"这类回忆够用，但一旦记忆量上千条，关键词匹配就开始漏——你搜"项目偏好"，可能错过写着"代码风格"的那条。

LanceDB 把每条记忆转成向量。向量搜索算余弦距离而非关键词命中，所以"项目偏好"也能召回写着"代码风格指南"的记忆。这是语义检索和关键词检索的根本差别。

第二个关键设计：嵌入模型通过 provider 适配器接入，不用在插件配置里硬编码 API key。你已经配好了 OpenAI 或 Copilot 的认证，LanceDB 直接复用。就像 Docker volume 挂载——存储引擎和认证凭据分开管理，各走各的生命周期。

第三个边界值得注意：`recallMaxChars` 和 `captureMaxChars` 是两个独立限制。前者管"发给嵌入模型的文本有多长"，后者管"多长的回复才有资格被自动捕获"。调错第一个会报错，调错第二个会漏存。两者互不影响。

---

`memory-lancedb` 是官方外部记忆插件，用 LanceDB 存储长期记忆并用嵌入模型做语义召回。它能在模型响应前自动召回相关记忆，在响应后捕获重要事实。

需要本地向量数据库做记忆、需要 OpenAI 兼容的嵌入端点、或想把记忆数据库放在默认内置记忆存储之外时使用。

## 安装

设置 `plugins.slots.memory = "memory-lancedb"` 前先安装：

```bash
openclaw plugins install @openclaw/memory-lancedb
```

插件发布到 npm，不内置在 OpenClaw 运行时镜像中。安装器写入插件条目并在没有其他插件占用时切换 memory slot。

> **注意**：`memory-lancedb` 是活跃记忆插件。通过 `plugins.slots.memory = "memory-lancedb"` 启用。`memory-wiki` 等伴侣插件可并行运行，但活跃 memory slot 只能归一个插件。

## 快速开始

```json5
{
  plugins: {
    slots: {
      memory: "memory-lancedb",
    },
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          embedding: {
            provider: "openai",
            model: "text-embedding-3-small",
          },
          autoRecall: true,
          autoCapture: false,
        },
      },
    },
  },
}
```

改完插件配置后重启 Gateway：

```bash
openclaw gateway restart
```

然后验证插件已加载：

```bash
openclaw plugins list
```

## Provider 适配器嵌入

`memory-lancedb` 可复用 `memory-core` 的嵌入 provider 适配器。设置 `embedding.provider` 并省略 `embedding.apiKey`，即可使用 provider 已配置的认证档案、环境变量或 `models.providers.<provider>.apiKey`。

```json5
{
  plugins: {
    slots: {
      memory: "memory-lancedb",
    },
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          embedding: {
            provider: "openai",
            model: "text-embedding-3-small",
          },
          autoRecall: true,
        },
      },
    },
  },
}
```

此路径支持暴露嵌入凭证的 provider 认证档案。例如 GitHub Copilot 在订阅计划支持嵌入时可直接使用：

```json5
{
  plugins: {
    slots: {
      memory: "memory-lancedb",
    },
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          embedding: {
            provider: "github-copilot",
            model: "text-embedding-3-small",
          },
        },
      },
    },
  },
}
```

OpenAI Codex / ChatGPT OAuth 凭证不等同于 OpenAI Platform 嵌入凭证。要用 OpenAI 嵌入，需使用 OpenAI API key 认证档案、`OPENAI_API_KEY` 环境变量或 `models.providers.openai.apiKey`。仅有 OAuth 的用户可改用 Copilot 或 Ollama 等其他支持嵌入的 provider。

## Ollama 嵌入

Ollama 嵌入优先用内置 Ollama 嵌入 provider。它使用原生 Ollama `/api/embed` 端点，遵循 [Ollama](/providers/ollama) 文档中相同的认证和 baseUrl 规则。

```json5
{
  plugins: {
    slots: {
      memory: "memory-lancedb",
    },
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          embedding: {
            provider: "ollama",
            baseUrl: "http://127.0.0.1:11434",
            model: "mxbai-embed-large",
            dimensions: 1024,
          },
          recallMaxChars: 400,
          autoRecall: true,
          autoCapture: false,
        },
      },
    },
  },
}
```

非标准嵌入模型需设置 `dimensions`。OpenClaw 内置了 `text-embedding-3-small` 和 `text-embedding-3-large` 的维度；自定义模型需在配置里写明维度值，LanceDB 才能创建向量列。

本地小嵌入模型若出现上下文长度错误，可降低 `recallMaxChars`。

## OpenAI 兼容 provider

部分 OpenAI 兼容嵌入 provider 会拒绝 `encoding_format` 参数，另一些则忽略它并始终返回 `number[]` 向量。`memory-lancedb` 在嵌入请求中省略 `encoding_format`，同时接受浮点数组响应和 base64 编码的 float32 响应。

原始 OpenAI 兼容端点若没有内置 provider 适配器，可省略 `embedding.provider`（或保持 `openai`），直接设置 `embedding.apiKey` 和 `embedding.baseUrl`。这保留了直连 OpenAI 兼容客户端的路径。

维度非内置的 provider 需设置 `embedding.dimensions`。例如智谱 `embedding-3` 用 `2048` 维度：

```json5
{
  plugins: {
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          embedding: {
            apiKey: "${ZHIPU_API_KEY}",
            baseUrl: "https://open.bigmodel.cn/api/paas/v4",
            model: "embedding-3",
            dimensions: 2048,
          },
        },
      },
    },
  },
}
```

## Recall 和 capture 限制

`memory-lancedb` 有两个独立的文本限制：

| 设置             | 默认值 | 范围       | 作用对象                          |
| ---------------- | ------ | ---------- | --------------------------------- |
| `recallMaxChars` | `1000` | 100-10000  | 发给嵌入 API 做 recall 的文本     |
| `captureMaxChars`| `500`  | 100-10000  | 有资格被自动捕获的消息长度        |
| `customTriggers` | `[]`   | 0-50       | 触发自动捕获的自定义短语          |

`recallMaxChars` 控制自动召回、`memory_recall` 工具、`memory_forget` 查询路径和 `openclaw ltm search`。自动召回优先取 turn 中最新的用户消息，仅在无用户消息时才回退到完整 prompt。这避免了频道元数据和大量 prompt 块被塞进嵌入请求。

`captureMaxChars` 控制响应是否有资格被自动捕获，不影响 recall 查询的嵌入长度。

`customTriggers` 允许添加字面自动捕获短语，无需写正则表达式。内置触发词覆盖英语、捷克语、中文、日语和韩语常见记忆短语。

## 命令

`memory-lancedb` 为活跃记忆插件时，注册 `ltm` CLI 命名空间：

```bash
openclaw ltm list
openclaw ltm search "项目偏好"
openclaw ltm stats
```

`query` 子命令对 LanceDB 表做非向量查询：

```bash
openclaw ltm query --cols id,text,createdAt --limit 20
openclaw ltm query --filter "category = 'preference'" --order-by createdAt:desc
```

- `--cols <列>`：逗号分隔的列白名单，默认 `id`、`text`、`importance`、`category`、`createdAt`
- `--filter <条件>`：SQL 风格 WHERE 子句，上限 200 字符，仅允许字母数字、比较运算符、引号、括号和少量安全标点
- `--limit <n>`：正整数，默认 `10`
- `--order-by <列>:<asc|desc>`：过滤后的内存排序，排序列自动包含在投影中

Agent 还能从活跃记忆插件获得 LanceDB 记忆工具：

- `memory_recall` 做 LanceDB 召回
- `memory_store` 保存重要事实、偏好、决策和实体
- `memory_forget` 删除匹配记忆

## 存储

LanceDB 数据默认存在 `~/.openclaw/memory/lancedb`。可用 `dbPath` 覆盖：

```json5
{
  plugins: {
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          dbPath: "~/.openclaw/memory/lancedb",
          embedding: {
            apiKey: "${OPENAI_API_KEY}",
            model: "text-embedding-3-small",
          },
        },
      },
    },
  },
}
```

`storageOptions` 接受字符串键值对，用于 LanceDB 存储后端，支持 `${ENV_VAR}` 展开：

```json5
{
  plugins: {
    entries: {
      "memory-lancedb": {
        enabled: true,
        config: {
          dbPath: "s3://memory-bucket/openclaw",
          storageOptions: {
            access_key: "${AWS_ACCESS_KEY_ID}",
            secret_key: "${AWS_SECRET_ACCESS_KEY}",
            endpoint: "${AWS_ENDPOINT_URL}",
          },
          embedding: {
            apiKey: "${OPENAI_API_KEY}",
            model: "text-embedding-3-small",
          },
        },
      },
    },
  },
}
```

## 运行时依赖

`memory-lancedb` 依赖原生 `@lancedb/lancedb` 包。打包的 OpenClaw 将该包视为插件包的一部分。Gateway 启动不修复插件依赖；若依赖缺失，重装或更新插件包后重启 Gateway。

旧版安装若日志报缺少 `dist/package.json` 或 `@lancedb/lancedb`，升级 OpenClaw 后重启 Gateway。

若插件日志显示 LanceDB 在 `darwin-x64` 上不可用，在该机器上用默认记忆后端、将 Gateway 迁到支持的平台、或禁用 `memory-lancedb`。

## 故障排查

### 输入长度超出上下文

通常是嵌入模型拒绝了 recall 查询：

```text
memory-lancedb: recall failed: Error: 400 the input length exceeds the context length
```

降低 `recallMaxChars` 后重启 Gateway：

```json5
{
  plugins: {
    entries: {
      "memory-lancedb": {
        config: {
          recallMaxChars: 400,
        },
      },
    },
  },
}
```

Ollama 还需确认嵌入服务从 Gateway 宿主机可达：

```bash
curl http://127.0.0.1:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"mxbai-embed-large","input":"hello"}'
```

### 不支持的嵌入模型

未设置 `dimensions` 时，仅内置 OpenAI 嵌入维度已知。本地或自定义嵌入模型需设置 `embedding.dimensions` 为该模型报告的向量大小。

### 插件加载但无记忆

确认 `plugins.slots.memory` 指向 `memory-lancedb`，然后运行：

```bash
openclaw ltm stats
openclaw ltm search "最近的偏好"
```

若 `autoCapture` 被禁用，插件会召回已有记忆但不自动存储新记忆。用 `memory_store` 工具或启用 `autoCapture` 实现自动捕获。

## 相关

- [Memory 概述](/concepts/memory)
- [Active memory](/concepts/active-memory)
- [Memory search](/concepts/memory-search)
- [Memory Wiki](/plugins/memory-wiki)
- [Ollama](/providers/ollama)
