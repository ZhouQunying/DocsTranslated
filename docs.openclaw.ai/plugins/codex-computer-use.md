# Codex Computer Use

## 架构精读

> 跳过不影响阅读翻译正文。

### OpenClaw 为什么不自己控制桌面？

职责分离。OpenClaw 只做编排,不做执行。它负责准备环境（安装/启用插件、检查 MCP 服务器就绪）然后退到幕后——Codex app-server 在线程期间持有实际的桌面控制。就像舞台监督只管道具和灯光,演出时绝不登台。

"失败即拒绝"的设计也值得注意。`computerUse.enabled: true` 但 MCP 服务器不可用时,Codex 模式轮次在线程启动前就失败。这防止了 agent 缺少预期工具仍默默跑下去——配置说"我要桌面控制",那就必须有,没有就停。

三条路径的品牌混淆也需要澄清：OpenClaw.app/Peekaboo（macOS 权限宿主）、iOS app（节点命令）、Codex Computer Use（Codex 原生 MCP 插件）——三个完全独立的系统,名字像但不是同一个东西。

---

Computer Use 是本地桌面控制的 Codex 原生 MCP 插件。OpenClaw 不打包桌面 app、不自己执行桌面操作、也不绕过 Codex 权限。内置 `codex` 插件只准备 Codex app-server：启用 Codex 插件支持、查找或安装配置的 Codex Computer Use 插件、检查 `computer-use` MCP 服务器是否可用,然后让 Codex 在 Codex 模式轮次中持有原生 MCP 工具调用。

OpenClaw 已在使用原生 Codex harness 时再用本页。运行时设置本身见 [Codex harness](/plugins/codex-harness)。

## OpenClaw.app 和 Peekaboo

OpenClaw.app 的 Peekaboo 集成独立于 Codex Computer Use。macOS app 可承载 PeekabooBridge socket 让 `peekaboo` CLI 复用该 app 的本地 Accessibility 和 Screen Recording 授权来驱动 Peekaboo 自己的自动化工具。该 bridge 不安装也不代理 Codex Computer Use,Codex Computer Use 也不走 PeekabooBridge socket 调用。

需要 OpenClaw.app 作为 Peekaboo CLI 自动化的权限感知宿主时用 [Peekaboo bridge](/platforms/mac/peekaboo)。需要 Codex 模式 OpenClaw agent 在轮次开始前就有 Codex 原生 `computer-use` MCP 插件可用时用本页。

## iOS app

iOS app 独立于 Codex Computer Use。不安装也不代理 Codex `computer-use` MCP 服务器,不是桌面控制后端。iOS app 作为 OpenClaw 节点连接并通过 `canvas.*`、`camera.*`、`screen.*`、`location.*` 和 `talk.*` 等节点命令暴露移动端能力。

需要 agent 通过 gateway 驱动 iPhone 节点时用 [iOS](/platforms/ios)。需要 Codex 模式 agent 通过 Codex 原生 Computer Use 插件控制本地 macOS 桌面时用本页。

## 直接走 cua-driver MCP

Codex Computer Use 不是暴露桌面控制的唯一路径。想让 OpenClaw 管理的运行时直接调用 TryCua 的 driver,走上游 `cua-driver mcp` 服务器通过 OpenClaw MCP 注册表注册,而非 Codex 专属 marketplace 流程。

安装 `cua-driver` 后,可以让它自己输出 OpenClaw 命令：

```bash
cua-driver mcp-config --client openclaw
```

或者自己注册 stdio 服务器：

```bash
openclaw mcp set cua-driver '{"command":"cua-driver","args":["mcp"]}'
```

这条路径保持上游 MCP 工具表面完整,包括 driver schema 和结构化 MCP 响应。想把 CUA driver 当普通 OpenClaw MCP 服务器用时走这条路。需要 Codex app-server 持有插件安装、MCP 重载和 Codex 模式轮次内的原生工具调用时用本页的 Codex Computer Use 设置。

CUA 的 driver 是 macOS 专属的,仍需其 app 提示的本地 macOS 权限,如 Accessibility 和 Screen Recording。OpenClaw 不安装 `cua-driver`、不授予这些权限、也不绕开上游 driver 的安全模型。

## 快速设置

Codex 模式轮次必须在线程启动前有 Computer Use 可用时,设置 `plugins.entries.codex.config.computerUse`。`autoInstall: true` 启用 Computer Use 并让 OpenClaw 在轮次前安装或重新启用：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          computerUse: {
            autoInstall: true,
          },
        },
      },
    },
  },
  agents: {
    defaults: {
      model: "openai/gpt-5.5",
    },
  },
}
```

此配置下 OpenClaw 在每个 Codex 模式轮次前检查 Codex app-server。Computer Use 缺失但 Codex app-server 已发现可安装的 marketplace 时,OpenClaw 让 Codex app-server 安装或重新启用插件并重载 MCP 服务器。macOS 上无匹配 marketplace 已注册且标准 Codex app bundle 存在时,OpenClaw 还会在失败前尝试从 `/Applications/Codex.app/Contents/Resources/plugins/openai-bundled` 注册内置 Codex marketplace。如果设置仍无法使 MCP 服务器可用,轮次在线程启动前失败。

Computer Use 配置变更后,如已有 Codex 线程启动,测试前在受影响聊天中用 `/new` 或 `/reset`。

## 命令

`codex` 插件命令表面可用的任何聊天界面均可使用 `/codex computer-use` 命令。这些是 OpenClaw 聊天/运行时命令,不是 `openclaw codex ...` CLI 子命令：

```text
/codex computer-use status
/codex computer-use install
/codex computer-use install --source <marketplace-source>
/codex computer-use install --marketplace-path <path>
/codex computer-use install --marketplace <name>
```

`status` 只读。不添加 marketplace 源、不安装插件、不启用 Codex 插件支持。如果没有配置启用 Computer Use,`status` 即使执行过一次安装命令也可能报告禁用。

`install` 启用 Codex app-server 插件支持,可选添加配置的 marketplace 源,通过 Codex app-server 安装或重新启用配置的插件,重载 MCP 服务器并验证 MCP 服务器暴露工具。

## Marketplace 选择

OpenClaw 使用和 Codex 自身暴露的相同 app-server API。marketplace 字段选择 Codex 去哪里找 `computer-use`。

| 字段                 | 适用场景                                            | 安装支持                                    |
| -------------------- | --------------------------------------------------- | ------------------------------------------- |
| 无 marketplace 字段  | 让 Codex app-server 用它已知的 marketplace。        | app-server 返回本地 marketplace 时支持。    |
| `marketplaceSource`  | 有 Codex app-server 可添加的 marketplace 源。       | 显式 `/codex computer-use install` 时支持。 |
| `marketplacePath`    | 已知宿主机上本地 marketplace 文件路径。             | 显式安装和轮次启动自动安装均支持。          |
| `marketplaceName`    | 想按名称选择已注册的 marketplace。                  | 仅当选中的 marketplace 有本地路径时支持。   |

全新 Codex home 可能需要短暂时间播种其官方 marketplace。安装期间 OpenClaw 最多轮询 `plugin/list` `marketplaceDiscoveryTimeoutMs` 毫秒。默认 60 秒。

多个已知 marketplace 包含 Computer Use 时,OpenClaw 优先选 `openai-bundled`,其次 `openai-curated`,再次 `local`。未知歧义匹配失败即拒绝并要求设置 `marketplaceName` 或 `marketplacePath`。

## 内置 macOS marketplace

近期 Codex 桌面版内置 Computer Use 位置：

```text
/Applications/Codex.app/Contents/Resources/plugins/openai-bundled/plugins/computer-use
```

`computerUse.autoInstall` 为 true 且无包含 `computer-use` 的 marketplace 已注册时,OpenClaw 自动尝试添加标准内置 marketplace 根：

```text
/Applications/Codex.app/Contents/Resources/plugins/openai-bundled
```

也可用 shell 显式注册：

```bash
codex plugin marketplace add /Applications/Codex.app/Contents/Resources/plugins/openai-bundled
```

使用非标准 Codex app 路径时,运行一次 `/codex computer-use install --source <marketplace-root>` 或将 `computerUse.marketplacePath` 设为本地 marketplace 文件路径。`--marketplace-path` 仅在持有 marketplace JSON 文件路径时使用,不是内置 marketplace 根。

## 远程目录限制

Codex app-server 可列出和读取仅远程的目录条目,但当前不支持远程 `plugin/install`。这意味着 `marketplaceName` 可选择仅远程 marketplace 做状态检查,但安装和重新启用仍需通过 `marketplaceSource` 或 `marketplacePath` 提供本地 marketplace。

status 报告插件在远程 Codex marketplace 可用但远程安装不支持时,用本地源或路径运行安装：

```text
/codex computer-use install --source <marketplace-source>
/codex computer-use install --marketplace-path <path>
```

## 配置参考

| 字段                            | 默认值         | 含义                                                         |
| ------------------------------- | -------------- | ------------------------------------------------------------ |
| `enabled`                       | 推断           | 是否要求 Computer Use。设置了其他 Computer Use 字段时默认 true。 |
| `autoInstall`                   | false          | 轮次启动时从已发现的 marketplace 安装或重新启用。            |
| `marketplaceDiscoveryTimeoutMs` | 60000          | 安装等待 Codex app-server marketplace 发现的时长。           |
| `marketplaceSource`             | 未设置         | 传给 Codex app-server `marketplace/add` 的源字符串。         |
| `marketplacePath`               | 未设置         | 包含该插件的本地 Codex marketplace 文件路径。                |
| `marketplaceName`               | 未设置         | 要选择的已注册 Codex marketplace 名称。                      |
| `pluginName`                    | `computer-use` | Codex marketplace 插件名。                                   |
| `mcpServerName`                 | `computer-use` | 已安装插件暴露的 MCP 服务器名。                              |

轮次启动自动安装有意拒绝已配置的 `marketplaceSource` 值。添加新源是显式设置操作,所以先用 `/codex computer-use install --source <marketplace-source>` 执行一次,然后让 `autoInstall` 处理从已发现的本地 marketplace 的后续重新启用。轮次启动自动安装可使用已配置的 `marketplacePath`,因为这已是宿主机上的本地路径。

## OpenClaw 检查什么

OpenClaw 内部报告稳定的设置原因并格式化面向用户的状态输出：

| 原因                         | 含义                                           | 下一步                                     |
| ---------------------------- | ---------------------------------------------- | ------------------------------------------ |
| `disabled`                   | `computerUse.enabled` 解析为 false。           | 设置 `enabled` 或其他 Computer Use 字段。  |
| `marketplace_missing`        | 无匹配的 marketplace 可用。                    | 配置源、路径或 marketplace 名称。          |
| `plugin_not_installed`       | Marketplace 存在但插件未安装。                 | 运行安装或启用 `autoInstall`。             |
| `plugin_disabled`            | 插件已安装但在 Codex 配置中被禁用。            | 运行安装以重新启用。                       |
| `remote_install_unsupported` | 选中的 marketplace 仅远程。                    | 用 `marketplaceSource` 或 `marketplacePath`。 |
| `mcp_missing`                | 插件已启用但 MCP 服务器不可用。                | 检查 Codex Computer Use 和 OS 权限。       |
| `ready`                      | 插件和 MCP 工具可用。                          | 开始 Codex 模式轮次。                      |
| `check_failed`               | 状态检查期间 Codex app-server 请求失败。       | 检查 app-server 连通性和日志。             |
| `auto_install_blocked`       | 轮次启动设置需要添加新源。                     | 先运行显式安装。                           |

聊天输出包含插件状态、MCP 服务器状态、marketplace、可用时的工具列表和失败设置步骤的具体消息。

## macOS 权限

Computer Use 是 macOS 专属的。Codex 持有的 MCP 服务器在检查或控制 app 前可能需要本地 OS 权限。OpenClaw 报告 Computer Use 已安装但 MCP 服务器不可用时,先验证 Codex 侧 Computer Use 设置：

- Codex app-server 在应发生桌面控制的同一宿主机上运行。
- Computer Use 插件在 Codex 配置中已启用。
- `computer-use` MCP 服务器出现在 Codex app-server MCP 状态中。
- macOS 已授予桌面控制 app 所需权限。
- 当前宿主机会话可访问被控制的桌面。

OpenClaw 在 `computerUse.enabled` 为 true 时有意失败即拒绝。Codex 模式轮次不应在缺少配置要求的原生桌面工具时默默继续。

## 故障排查

**Status 报告未安装。** 运行 `/codex computer-use install`。marketplace 未发现时传 `--source` 或 `--marketplace-path`。

**Status 报告已安装但禁用。** 再次运行 `/codex computer-use install`。Codex app-server 安装将插件配置写回启用。

**Status 报告远程安装不支持。** 用本地 marketplace 源或路径。仅远程目录条目可通过当前 app-server API 查看但不能安装。

**Status 报告 MCP 服务器不可用。** 重跑一次安装让 MCP 服务器重载。仍不可用则修复 Codex Computer Use app、Codex app-server MCP 状态或 macOS 权限。

**Status 或探测在 `computer-use.list_apps` 超时。** 插件和 MCP 服务器都在,但本地 Computer Use bridge 无响应。退出或重启 Codex Computer Use,必要时重启 Codex Desktop,然后在全新 OpenClaw 会话中重试。

**Computer Use 工具报 `Native hook relay unavailable`。** Codex 原生工具钩子无法通过本地 bridge 或 Gateway 回退到达活跃的 OpenClaw 中继。用 `/new` 或 `/reset` 开始全新 OpenClaw 会话。如果成功一次后下次工具调用又失败,`/new` 仅清除当前尝试；重启 Codex app-server 或 OpenClaw Gateway 让旧线程和钩子注册被丢弃,然后在全新会话中重试。

**轮次启动自动安装拒绝源。** 这是有意设计。先用显式 `/codex computer-use install --source <marketplace-source>` 添加源,后续轮次启动自动安装可使用已发现的本地 marketplace。

## 相关

- [Codex harness](/plugins/codex-harness)
- [Peekaboo bridge](/platforms/mac/peekaboo)
- [iOS app](/platforms/ios)
