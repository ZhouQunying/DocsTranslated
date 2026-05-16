# WeChat / 微信

> OpenClaw connects to WeChat through Tencent's external `@tencent-weixin/openclaw-weixin` channel plugin.

OpenClaw 通过腾讯提供的外部通道插件 `@tencent-weixin/openclaw-weixin` 接入微信。

> Status: external plugin. Direct chats and media are supported. Group chats are not advertised by the current plugin capability metadata.

状态：外部插件。支持私聊和媒体收发。当前插件能力清单里没有声明支持群聊。

---

> ## Naming

## 命名

> - **WeChat** is the user-facing name in these docs.
> - **Weixin** is the name used by Tencent's package and by the plugin id.
> - `openclaw-weixin` is the OpenClaw channel id.
> - `@tencent-weixin/openclaw-weixin` is the npm package.

- **WeChat**：文档里对外用的名字。
- **Weixin**：腾讯包名和插件 ID 用的名字。
- `openclaw-weixin`：OpenClaw 里的通道 ID。
- `@tencent-weixin/openclaw-weixin`：npm 包名。

> Use `openclaw-weixin` in CLI commands and config paths.

写 CLI 命令和配置路径时统一用 `openclaw-weixin`。

---

> ## How it works

## 工作原理

> The WeChat-specific code lives outside the OpenClaw core repo. Core provides the generic channel plugin contract; the external package supplies the runtime for WeChat.

微信相关的代码不在 OpenClaw 核心仓库里。核心只定义通用的通道插件接口，微信运行时由外部包来实现。

> 1. `openclaw plugins install` installs `@tencent-weixin/openclaw-weixin`.
> 2. The Gateway discovers the plugin manifest and loads the plugin entrypoint.
> 3. The plugin registers channel id `openclaw-weixin`.
> 4. `openclaw channels login --channel openclaw-weixin` starts QR login.
> 5. The plugin stores account credentials under the OpenClaw state directory.
> 6. When the Gateway starts, the plugin starts its Weixin monitor for each configured account.
> 7. Inbound WeChat messages are normalized through the channel contract, routed to the selected agent, and sent back via the plugin outbound path.

1. `openclaw plugins install` 安装 `@tencent-weixin/openclaw-weixin`。
2. Gateway 读取插件清单，加载插件入口。
3. 插件注册通道 ID `openclaw-weixin`。
4. `openclaw channels login --channel openclaw-weixin` 启动扫码登录。
5. 插件把账号凭证存到 OpenClaw 的状态目录下。
6. Gateway 启动时，插件给每个配置好的账号起一个微信监听器。
7. 收到的微信消息走通道接口做标准化，路由到选定的 agent，回包再经插件的发送链路发出去。

> The split keeps core channel-agnostic. Authentication, Tencent iLink API calls, media transfer, context tokens, and account monitoring are all owned by the external plugin.

这种拆分让核心和具体通道解耦：登录、腾讯 iLink API 调用、媒体收发、上下文 token、账号监听这些事，都归外部插件管。

---

> ## Install

## 安装

> Quick install:

一键安装：

> ```bash
> npx -y @tencent-weixin/openclaw-weixin-cli install
> ```

```bash
npx -y @tencent-weixin/openclaw-weixin-cli install
```

> Manual install:

手动安装：

> ```bash
> openclaw plugins install "@tencent-weixin/openclaw-weixin"
> openclaw config set plugins.entries.openclaw-weixin.enabled true
> ```

```bash
openclaw plugins install "@tencent-weixin/openclaw-weixin"
openclaw config set plugins.entries.openclaw-weixin.enabled true
```

> Restart the Gateway after install:

装完之后重启 Gateway：

> ```bash
> openclaw gateway restart
> ```

```bash
openclaw gateway restart
```

---

> ## Login

## 登录

> Run QR login on the same machine that runs the Gateway:

在跑 Gateway 的那台机器上扫码登录：

> ```bash
> openclaw channels login --channel openclaw-weixin
> ```

```bash
openclaw channels login --channel openclaw-weixin
```

> Scan the QR code with WeChat on your phone and confirm. The plugin persists the account token locally after a successful scan.

用手机微信扫码并确认。扫码成功后，插件会把账号 token 存到本地。

> To add another WeChat account, run the same login command again. For multiple accounts, isolate direct-message sessions by account, channel, and sender:

要再加一个微信号，把登录命令再跑一遍。多账号的场景，按账号、通道、发件人三个维度隔离私聊会话：

> ```bash
> openclaw config set session.dmScope per-account-channel-peer
> ```

```bash
openclaw config set session.dmScope per-account-channel-peer
```

---

> ## Access control

## 访问控制

> Direct messages use the standard OpenClaw pairing and allowlist model for channel plugins.

私聊沿用 OpenClaw 通道插件标准的配对 + 白名单机制。

> Approve new senders:

放行新的发件人：

> ```bash
> openclaw pairing list openclaw-weixin
> openclaw pairing approve openclaw-weixin <CODE>
> ```

```bash
openclaw pairing list openclaw-weixin
openclaw pairing approve openclaw-weixin <CODE>
```

> For the full access-control model, see [Pairing](/channels/pairing).

完整的访问控制模型见 [Pairing](/channels/pairing)。

---

> ## Compatibility

## 兼容性

> The plugin checks the host OpenClaw version at startup.

插件启动时会检查宿主 OpenClaw 的版本。

> | Plugin line | OpenClaw version        | npm tag  |
> | ----------- | ----------------------- | -------- |
> | `2.x`       | `>=2026.3.22`           | `latest` |
> | `1.x`       | `>=2026.1.0 <2026.3.22` | `legacy` |

| 插件主版本 | OpenClaw 版本           | npm tag  |
| ---------- | ----------------------- | -------- |
| `2.x`      | `>=2026.3.22`           | `latest` |
| `1.x`      | `>=2026.1.0 <2026.3.22` | `legacy` |

> If the plugin reports that your OpenClaw version is too old, either upgrade OpenClaw or install the legacy line:

如果插件提示你的 OpenClaw 版本过旧，升级 OpenClaw，或者装老版本插件分支：

> ```bash
> openclaw plugins install @tencent-weixin/openclaw-weixin@legacy
> ```

```bash
openclaw plugins install @tencent-weixin/openclaw-weixin@legacy
```

---

> ## Sidecar process

## 边车进程（Sidecar）

> The WeChat plugin can run helper work alongside the Gateway while it monitors the Tencent iLink API. In issue #68451, that helper path exposed a bug in OpenClaw's generic stale-Gateway cleanup: a child process could try to clean up its parent Gateway, triggering restart loops under process managers like systemd.

微信插件在监听腾讯 iLink API 时，会在 Gateway 旁边跑一些辅助逻辑。issue #68451 里，这条辅助流程暴露出 OpenClaw 通用"清理失效 Gateway"逻辑的一个 bug：子进程可能反过来去清理自己的父 Gateway，在 systemd 这类进程管理器下造成反复重启。

> Current startup cleanup now excludes the current process and its ancestors, so a channel helper cannot kill the Gateway that launched it. The fix is generic and not WeChat-specific in core.

现在的启动清理逻辑会跳开当前进程和它的祖先进程，通道辅助进程没法再把启动自己的 Gateway 干掉。这是核心层面的通用修复，跟微信本身无关。

---

> ## Troubleshooting

## 故障排查

> Check install and status:

检查安装情况和运行状态：

> ```bash
> openclaw plugins list
> openclaw channels status --probe
> openclaw --version
> ```

```bash
openclaw plugins list
openclaw channels status --probe
openclaw --version
```

> If the channel shows as installed but does not connect, confirm the plugin is enabled and restart:

如果通道显示已安装但连不上，确认插件已启用，然后重启：

> ```bash
> openclaw config set plugins.entries.openclaw-weixin.enabled true
> openclaw gateway restart
> ```

```bash
openclaw config set plugins.entries.openclaw-weixin.enabled true
openclaw gateway restart
```

> If the Gateway restarts repeatedly after enabling WeChat, update both OpenClaw and the plugin:

启用微信之后 Gateway 反复重启，把 OpenClaw 和插件一起更新到最新版本：

> ```bash
> npm view @tencent-weixin/openclaw-weixin version
> openclaw plugins install "@tencent-weixin/openclaw-weixin" --force
> openclaw gateway restart
> ```

```bash
npm view @tencent-weixin/openclaw-weixin version
openclaw plugins install "@tencent-weixin/openclaw-weixin" --force
openclaw gateway restart
```

> If startup reports that the installed package `"requires compiled runtime output for TypeScript entry"`, the npm release was published without the compiled JavaScript runtime files OpenClaw needs. Reinstall once the publisher ships a fixed package, or temporarily disable/uninstall the plugin.

如果启动时报错说插件包 `"requires compiled runtime output for TypeScript entry"`，意思是发布到 npm 的版本里少了 OpenClaw 需要的编译后 JS 文件。等插件作者重新发布修好的版本再装，或者先临时禁用、卸载这个插件。

> Temporary disable:

临时禁用：

> ```bash
> openclaw config set plugins.entries.openclaw-weixin.enabled false
> openclaw gateway restart
> ```

```bash
openclaw config set plugins.entries.openclaw-weixin.enabled false
openclaw gateway restart
```

---

> ## Related docs

## 相关文档

> - Channel overview: [Chat Channels](/channels)
> - Pairing: [Pairing](/channels/pairing)
> - Channel routing: [Channel Routing](/channels/channel-routing)
> - Plugin architecture: [Plugin Architecture](/plugins/architecture)
> - Channel plugin SDK: [Channel Plugin SDK](/plugins/sdk-channel-plugins)
> - External package: [@tencent-weixin/openclaw-weixin](https://www.npmjs.com/package/@tencent-weixin/openclaw-weixin)

- 通道总览：[Chat Channels](/channels)
- 配对：[Pairing](/channels/pairing)
- 通道路由：[Channel Routing](/channels/channel-routing)
- 插件架构：[Plugin Architecture](/plugins/architecture)
- 通道插件 SDK：[Channel Plugin SDK](/plugins/sdk-channel-plugins)
- 外部包：[@tencent-weixin/openclaw-weixin](https：//www.npmjs.com/package/@tencent-weixin/openclaw-weixin)
