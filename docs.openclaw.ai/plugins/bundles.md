# 插件包（Bundles）

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让 Codex/Claude/Cursor 插件"原生支持 OpenClaw"？

核心是**适配器模式**。三个生态各自有大量已发布的插件,要求作者全部重写为 OpenClaw 原生格式不现实。OpenClaw 选择了 LLVM 的思路——多前端、单后端。Codex/Claude/Cursor 是三种"前端格式",OpenClaw 的 skill/钩子/MCP 是统一的"内部表示"。包进来时自动检测格式、映射到原生特性。

信任边界的设计特别讲究。原生插件在进程内运行,可以注册任何能力——权力大但风险也大。Bundle 是内容包,不加载任意运行时模块,skill 和钩子路径必须在插件根内（边界检查）。就像浏览器插件和网页 iframe 的区别：前者能调宿主 API,后者被沙箱限制。

MCP 工具命名的确定性排序也值得注意。工具名按安全名排序后再注册,保证上游 `listTools()` 顺序变化不会打乱提示缓存的工具块。这对 prompt cache 命中率至关重要——每次工具列表顺序一变,缓存就失效。

---

> OpenClaw can install plugins from three external ecosystems: **Codex**, **Claude**, and **Cursor**.

OpenClaw 可从三个外部生态安装插件：**Codex**、**Claude** 和 **Cursor**。这些称为 **bundle** —— 内容和元数据包,OpenClaw 将其映射到 skill、钩子和 MCP 工具等原生特性。

> Bundles are **not** the same as native OpenClaw plugins...

Bundle **不**等同于原生 OpenClaw 插件。原生插件在进程内运行,可注册任何能力。Bundle 是内容包,有选择性特性映射和更窄的信任边界。

## 为什么需要 bundle

> Many useful plugins are published in Codex, Claude, or Cursor format...

很多有用的插件以 Codex、Claude 或 Cursor 格式发布。OpenClaw 不要求作者重写为原生格式,而是检测这些格式并将其支持的内容映射到原生特性集。这样你可以安装 Claude 命令包或 Codex skill 包并立即使用。

## 安装 bundle

1. **从目录、归档或 marketplace 安装：**

```bash
# 本地目录
openclaw plugins install ./my-bundle

# 归档
openclaw plugins install ./my-bundle.tgz

# Claude marketplace
openclaw plugins marketplace list <marketplace-name>
openclaw plugins install <plugin-name>@<marketplace-name>
```

2. **验证检测：**

```bash
openclaw plugins list
openclaw plugins inspect <id>
```

Bundle 显示为 `Format: bundle`,子类型为 `codex`、`claude` 或 `cursor`。

3. **重启并使用：**

```bash
openclaw gateway restart
```

映射的特性（skill、钩子、MCP 工具、LSP 默认值）在下次会话可用。

## OpenClaw 从 bundle 映射什么

不是所有 bundle 特性今天都在 OpenClaw 中运行。以下是可用和已检测但未接线的部分。

### 当前支持

| 特性        | 映射方式                                                                                  | 适用对象      |
| ----------- | ----------------------------------------------------------------------------------------- | ------------- |
| Skill 内容  | Bundle skill 根作为正常 OpenClaw skill 加载                                               | 所有格式      |
| 命令        | `commands/` 和 `.cursor/commands/` 作为 skill 根处理                                      | Claude, Cursor |
| 钩子包      | OpenClaw 式 `HOOK.md` + `handler.ts` 布局                                                 | Codex         |
| MCP 工具    | Bundle MCP 配置合并到嵌入式 OpenClaw 设置；支持 stdio 和 HTTP 服务器加载                   | 所有格式      |
| LSP 服务器  | Claude `.lsp.json` 和清单声明的 `lspServers` 合并到嵌入式 OpenClaw LSP 默认值              | Claude        |
| 设置        | Claude `settings.json` 作为嵌入式 OpenClaw 默认值导入                                      | Claude        |

#### Skill 内容

- Bundle skill 根作为正常 OpenClaw skill 根加载
- Claude `commands` 根作为额外 skill 根处理
- Cursor `.cursor/commands` 根作为额外 skill 根处理

Claude markdown 命令文件通过正常 OpenClaw skill 加载器工作。Cursor 命令 markdown 走同一路径。

#### 钩子包

- Bundle 钩子根**仅**在使用正常 OpenClaw 钩子包布局时工作。今天主要是 Codex 兼容场景：
  - `HOOK.md`
  - `handler.ts` 或 `handler.js`

#### 嵌入式 OpenClaw 的 MCP

- 启用的 bundle 可贡献 MCP 服务器配置
- OpenClaw 将 bundle MCP 配置合并到有效嵌入式 OpenClaw 设置中的 `mcpServers`
- OpenClaw 在嵌入式 agent 轮次中通过启动 stdio 服务器或连接 HTTP 服务器暴露支持的 bundle MCP 工具
- `coding` 和 `messaging` 工具 profile 默认包含 bundle MCP 工具；用 `tools.deny: ["bundle-mcp"]` 为 agent 或 gateway 退出
- bundle 默认值后仍应用项目本地嵌入式 agent 设置,所以工作区设置可在需要时覆盖 bundle MCP 条目
- bundle MCP 工具目录在注册前确定性排序,所以上游 `listTools()` 顺序变化不会打乱提示缓存工具块

##### 传输

MCP 服务器可用 stdio 或 HTTP 传输：

**Stdio** 启动子进程：

```json
{
  "mcp": {
    "servers": {
      "my-server": {
        "command": "node",
        "args": ["server.js"],
        "env": { "PORT": "3000" }
      }
    }
  }
}
```

**HTTP** 默认通过 `sse` 连接运行中的 MCP 服务器,请求时用 `streamable-http`：

```json
{
  "mcp": {
    "servers": {
      "my-server": {
        "url": "http://localhost:3100/mcp",
        "transport": "streamable-http",
        "headers": {
          "Authorization": "Bearer ${MY_SECRET_TOKEN}"
        },
        "connectionTimeoutMs": 30000
      }
    }
  }
}
```

- `transport` 可设为 `"streamable-http"` 或 `"sse"`；省略时 OpenClaw 用 `sse`
- `type: "http"` 是 CLI 原生下游形态；OpenClaw 配置中用 `transport: "streamable-http"`。`openclaw mcp set` 和 `openclaw doctor --fix` 规范化常见别名
- 仅允许 `http:` 和 `https:` URL scheme
- `headers` 值支持 `${ENV_VAR}` 插值
- 同时有 `command` 和 `url` 的服务器条目被拒绝
- URL 凭据（userinfo 和 query params）在工具描述和日志中脱敏
- `connectionTimeoutMs` 覆盖 stdio 和 HTTP 传输的默认 30 秒连接超时

##### 工具命名

> OpenClaw registers bundle MCP tools with provider-safe names...

OpenClaw 用提供商安全名称注册 bundle MCP 工具,格式 `serverName__toolName`。例如键为 `"vigil-harbor"` 的服务器暴露的 `memory_search` 工具注册为 `vigil-harbor__memory_search`。

- `A-Za-z0-9_-` 外的字符替换为 `-`
- 非字母开头的片段加字母前缀,所以 `12306` 等数字服务器键变为提供商安全的工具前缀
- 服务器前缀上限 30 字符
- 完整工具名上限 64 字符
- 空服务器名回退到 `mcp`
- 冲突的净化名用数字后缀消歧
- 最终暴露工具顺序按安全名确定性排列,保持重复嵌入式 agent 轮次缓存稳定
- profile 过滤将同一 bundle MCP 服务器的所有工具视为 `bundle-mcp` 插件持有,所以 profile 允许和拒绝列表可包含单独暴露工具名或 `bundle-mcp` 插件键

#### 嵌入式 OpenClaw 设置

- 启用时 Claude `settings.json` 作为默认嵌入式 OpenClaw 设置导入
- OpenClaw 在应用前净化 shell 覆盖键

净化的键：`shellPath`、`shellCommandPrefix`。

#### 嵌入式 OpenClaw LSP

- 启用的 Claude bundle 可贡献 LSP 服务器配置
- OpenClaw 加载 `.lsp.json` 加清单声明的 `lspServers` 路径
- Bundle LSP 配置合并到有效嵌入式 OpenClaw LSP 默认值
- 今天仅支持 stdio 后端 LSP 服务器可运行；不支持的传输仍出现在 `openclaw plugins inspect <id>` 中

### 已检测但未执行

这些被识别并显示在诊断中,但 OpenClaw 不运行它们：

- Claude `agents`、`hooks.json` 自动化、`outputStyles`
- Cursor `.cursor/agents`、`.cursor/hooks.json`、`.cursor/rules`
- Codex 能力报告之外的内联/应用元数据

## Bundle 格式

**Codex bundle：**

标记：`.codex-plugin/plugin.json`

可选内容：`skills/`、`hooks/`、`.mcp.json`、`.app.json`

Codex bundle 在使用 skill 根和 OpenClaw 式钩子包目录（`HOOK.md` + `handler.ts`）时最适合 OpenClaw。

**Claude bundle：**

两种检测模式：
- **清单式：** `.claude-plugin/plugin.json`
- **无清单：** 默认 Claude 布局（`skills/`、`commands/`、`agents/`、`hooks/`、`.mcp.json`、`.lsp.json`、`settings.json`）

Claude 特有行为：
- `commands/` 作为 skill 内容处理
- `settings.json` 导入到嵌入式 OpenClaw 设置（shell 覆盖键被净化）
- `.mcp.json` 向嵌入式 OpenClaw 暴露支持的 stdio 工具
- `.lsp.json` 加清单声明的 `lspServers` 路径加载到嵌入式 OpenClaw LSP 默认值
- `hooks/hooks.json` 仅检测不执行
- 清单中自定义组件路径是附加的（扩展默认值,不替换）

**Cursor bundle：**

标记：`.cursor-plugin/plugin.json`

可选内容：`skills/`、`.cursor/commands/`、`.cursor/agents/`、`.cursor/rules/`、`.cursor/hooks.json`、`.mcp.json`

- `.cursor/commands/` 作为 skill 内容处理
- `.cursor/rules/`、`.cursor/agents/` 和 `.cursor/hooks.json` 仅检测

## 检测优先级

> OpenClaw checks for native plugin format first:

OpenClaw 先检查原生插件格式：

1. `openclaw.plugin.json` 或含 `openclaw.extensions` 的有效 `package.json` —— 作为**原生插件**处理
2. Bundle 标记（`.codex-plugin/`、`.claude-plugin/` 或默认 Claude/Cursor 布局）—— 作为 **bundle** 处理

> If a directory contains both, OpenClaw uses the native path.

目录同时包含两者时 OpenClaw 走原生路径。防止双格式包被部分安装为 bundle。

## 运行时依赖和清理

- 第三方兼容 bundle 不获得启动时 `npm install` 修复。应通过 `openclaw plugins install` 安装并在安装插件目录中自带所有需要的内容。
- OpenClaw 持有的内置插件要么轻量发布在核心中,要么通过插件安装器下载。Gateway 启动从不为它们跑包管理器。
- `openclaw doctor --fix` 移除旧的分阶段依赖目录,可在配置引用时恢复本地插件索引中缺失的可下载插件。

## 安全

> Bundles have a narrower trust boundary than native plugins:

Bundle 的信任边界比原生插件更窄：

- OpenClaw **不**在进程内加载任意 bundle 运行时模块
- Skill 和钩子包路径必须在插件根内（边界检查）
- 设置文件读取采用相同的边界检查
- 支持的 stdio MCP 服务器可作为子进程启动

这使 bundle 默认更安全,但仍应将第三方 bundle 视为对其暴露特性的受信内容。

## 故障排查

**Bundle 被检测但能力不运行：**
运行 `openclaw plugins inspect <id>`。能力被列出但标记为未接线,那是产品限制——不是安装损坏。

**Claude 命令文件不出现：**
确保 bundle 已启用且 markdown 文件在检测到的 `commands/` 或 `skills/` 根内。

**Claude 设置不生效：**
仅支持 `settings.json` 中的嵌入式 OpenClaw 设置。OpenClaw 不将 bundle 设置视为原始配置补丁。

**Claude 钩子不执行：**
`hooks/hooks.json` 仅检测。需要可运行钩子时用 OpenClaw 钩子包布局或发布原生插件。

## 相关

- [Install and Configure Plugins](/tools/plugin)
- [Building Plugins](/plugins/building-plugins) —— 创建原生插件
- [Plugin Manifest](/plugins/manifest) —— 原生清单 schema
