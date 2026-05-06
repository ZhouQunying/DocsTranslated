# WeChat / 微信

## 状态

**英文原文**: OpenClaw connects to WeChat through Tencent's external `@tencent-weixin/openclaw-weixin` channel plugin. Status: external plugin. Direct chats and media are supported. Group chats are not advertised by the current plugin capability metadata.

**中文翻译**: OpenClaw 通过腾讯外部插件 `@tencent-weixin/openclaw-weixin` 连接到微信。状态：外部插件。支持私聊和媒体。当前插件能力元数据未声明支持群聊。

---

## 命名

**英文原文**: **WeChat** is the user-facing name in these docs. **Weixin** is the name used by Tencent's package and by the plugin id. `openclaw-weixin` is the OpenClaw channel id. `@tencent-weixin/openclaw-weixin` is the npm package. Use `openclaw-weixin` in CLI commands and config paths.

**中文翻译**: **WeChat** 是文档中对用户展示的名称。**Weixin** 是腾讯包名和插件 ID 中使用的名称。`openclaw-weixin` 是 OpenClaw 的频道 ID。`@tencent-weixin/openclaw-weixin` 是 npm 包名。在 CLI 命令和配置路径中使用 `openclaw-weixin`。

---

## 工作原理

**英文原文**: The WeChat code does not live in the OpenClaw core repo. OpenClaw provides the generic channel plugin contract, and the external plugin provides the WeChat-specific runtime:

1. `openclaw plugins install` installs `@tencent-weixin/openclaw-weixin`.
2. The Gateway discovers the plugin manifest and loads the plugin entrypoint.
3. The plugin registers channel id `openclaw-weixin`.
4. `openclaw channels login --channel openclaw-weixin` starts QR login.
5. The plugin stores account credentials under the OpenClaw state directory.
6. When the Gateway starts, the plugin starts its Weixin monitor for each configured account.
7. Inbound WeChat messages are normalized through the channel contract, routed to the selected OpenClaw agent, and sent back through the plugin outbound path.

That separation matters: OpenClaw core should stay channel-agnostic. WeChat login, Tencent iLink API calls, media upload/download, context tokens, and account monitoring are owned by the external plugin.

**中文翻译**: 微信代码不在 OpenClaw 核心仓库中。OpenClaw 提供通用的频道插件契约，外部插件提供微信特定的运行时：

1. `openclaw plugins install` 安装 `@tencent-weixin/openclaw-weixin`。
2. Gateway 发现插件清单并加载插件入口。
3. 插件注册频道 ID `openclaw-weixin`。
4. `openclaw channels login --channel openclaw-weixin` 启动扫码登录。
5. 插件将账号凭证存储在 OpenClaw 状态目录下。
6. Gateway 启动时，插件为每个配置的账号启动微信监控。
7. 入站微信消息通过频道契约标准化，路由到选定的 OpenClaw agent，并通过插件出站路径发回。

这种分离很重要：OpenClaw 核心应保持频道无关。微信登录、腾讯 iLink API 调用、媒体上传/下载、上下文令牌和账号监控都由外部插件负责。

---

## 安装

**英文原文**: Quick install: `npx -y @tencent-weixin/openclaw-weixin-cli install`

**中文翻译**: 快速安装：`npx -y @tencent-weixin/openclaw-weixin-cli install`

**英文原文**: Manual install:
```bash
openclaw plugins install "@tencent-weixin/openclaw-weixin"
openclaw config set plugins.entries.openclaw-weixin.enabled true
```

**中文翻译**: 手动安装：
```bash
openclaw plugins install "@tencent-weixin/openclaw-weixin"
openclaw config set plugins.entries.openclaw-weixin.enabled true
```

**英文原文**: Restart the Gateway after install: `openclaw gateway restart`

**中文翻译**: 安装后重启 Gateway：`openclaw gateway restart`

---

## 登录

**英文原文**: Run QR login on the same machine that runs the Gateway: `openclaw channels login --channel openclaw-weixin`

Scan the QR code with WeChat on your phone and confirm the login. The plugin saves the account token locally after a successful scan.

To add another WeChat account, run the same login command again. For multiple accounts, isolate direct-message sessions by account, channel, and sender: `openclaw config set session.dmScope per-account-channel-peer`

**中文翻译**: 在运行 Gateway 的同一台机器上执行扫码登录：`openclaw channels login --channel openclaw-weixin`

用手机微信扫码并确认登录。扫码成功后，插件将账号令牌保存到本地。

要添加另一个微信账号，再次运行同样的登录命令。多账号场景下，按账号、频道和发送者隔离私聊会话：`openclaw config set session.dmScope per-account-channel-peer`

---

## 访问控制

**英文原文**: Direct messages use the normal OpenClaw pairing and allowlist model for channel plugins.

Approve new senders:
```bash
openclaw pairing list openclaw-weixin
openclaw pairing approve openclaw-weixin <CODE>
```

For the full access-control model, see [Pairing](/channels/pairing).

**中文翻译**: 私聊使用 OpenClaw 正常的配对和白名单模型。

批准新发送者：
```bash
openclaw pairing list openclaw-weixin
openclaw pairing approve openclaw-weixin <CODE>
```

完整的访问控制模型，参见[配对文档](/channels/pairing)。

---

## 兼容性

**英文原文**: The plugin checks the host OpenClaw version at startup.

| Plugin line | OpenClaw version | npm tag |
|---|---|---|
| `2.x` | `>=2026.3.22` | `latest` |
| `1.x` | `>=2026.1.0 <2026.3.22` | `legacy` |

If the plugin reports that your OpenClaw version is too old, either update OpenClaw or install the legacy plugin line: `openclaw plugins install @tencent-weixin/openclaw-weixin@legacy`

**中文翻译**: 插件在启动时检查主机 OpenClaw 版本。

| 插件版本线 | OpenClaw 版本 | npm 标签 |
|---|---|---|
| `2.x` | `>=2026.3.22` | `latest` |
| `1.x` | `>=2026.1.0 <2026.3.22` | `legacy` |

如果插件报告你的 OpenClaw 版本过旧，更新 OpenClaw 或安装旧版插件：`openclaw plugins install @tencent-weixin/openclaw-weixin@legacy`

---

## [展开] Sidecar process / 伴随进程

**英文原文**: The WeChat plugin can run helper work beside the Gateway while it monitors the Tencent iLink API. In issue #68451, that helper path exposed a bug in OpenClaw's generic stale-Gateway cleanup: a child process could try to clean up the parent Gateway process, causing restart loops under process managers such as systemd.

Current OpenClaw startup cleanup excludes the current process and its ancestors, so a channel helper must not kill the Gateway that launched it. This fix is generic; it is not a WeChat-specific path in core.

**中文翻译**: 微信插件可以在 Gateway 旁边运行辅助工作，同时监控腾讯 iLink API。在 issue #68451 中，该辅助路径暴露了 OpenClaw 通用过期 Gateway 清理的一个 bug：子进程可能尝试清理父 Gateway 进程，导致在 systemd 等进程管理器下出现重启循环。

当前 OpenClaw 启动清理排除了当前进程及其祖先，因此频道助手不得杀死启动它的 Gateway。这个修复是通用的，不是核心中微信特定的路径。

---

## 故障排除

**英文原文**: Check install and status:
```bash
openclaw plugins list
openclaw channels status --probe
openclaw --version
```

If the channel shows as installed but does not connect, confirm that the plugin is enabled and restart:
```bash
openclaw config set plugins.entries.openclaw-weixin.enabled true
openclaw gateway restart
```

If the Gateway restarts repeatedly after enabling WeChat, update both OpenClaw and the plugin:
```bash
npm view @tencent-weixin/openclaw-weixin version
openclaw plugins install "@tencent-weixin/openclaw-weixin" --force
openclaw gateway restart
```

If startup reports that the installed plugin package `requires compiled runtime output for TypeScript entry`, the npm package was published without the compiled JavaScript runtime files OpenClaw needs. Update/reinstall after the plugin publisher ships a fixed package, or temporarily disable/uninstall the plugin.

Temporary disable:
```bash
openclaw config set plugins.entries.openclaw-weixin.enabled false
openclaw gateway restart
```

**中文翻译**: 检查安装和状态：
```bash
openclaw plugins list
openclaw channels status --probe
openclaw --version
```

如果频道显示已安装但无法连接，确认插件已启用并重启：
```bash
openclaw config set plugins.entries.openclaw-weixin.enabled true
openclaw gateway restart
```

如果启用微信后 Gateway 反复重启，同时更新 OpenClaw 和插件：
```bash
npm view @tencent-weixin/openclaw-weixin version
openclaw plugins install "@tencent-weixin/openclaw-weixin" --force
openclaw gateway restart
```

如果启动时报告已安装的插件包"requires compiled runtime output for TypeScript entry"，说明 npm 包发布时缺少 OpenClaw 需要的编译后 JavaScript 运行时文件。等待插件发布者修复后更新/重新安装，或临时禁用/卸载该插件。

临时禁用：
```bash
openclaw config set plugins.entries.openclaw-weixin.enabled false
openclaw gateway restart
```
