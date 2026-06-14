# Zalo 个人账户

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 zalouser 和 zalo 是两个不同的插件？

Zalo 没有官方的 Bot API（截至本文档编写时）。`zalouser` 通过 `zca-js` 自动化一个普通 Zalo 用户账户——本质上是模拟浏览器登录。这与未来可能的官方 Zalo API 集成是完全不同的契约：一个是非官方自动化（有封号风险），一个是官方 API。用不同的 channel id 区分是防止用户混淆——看到 `zalouser` 就知道这是个人账户自动化，不是官方集成。就像 Instagram 的官方 Graph API 和第三方 scraper 库的区别——功能可能相似，但法律和技术风险完全不同。

---

Zalo 个人账户通过插件支持 OpenClaw，使用原生 `zca-js` 自动化普通 Zalo 用户账户。

> **警告**
>
> 非官方自动化可能导致账户暂停或封禁。使用风险自负。

## 命名

Channel id 是 `zalouser`，明确表示这是自动化**个人 Zalo 用户账户**（非官方）。我们保留 `zalo` 给未来可能的官方 Zalo API 集成。

## 运行位置

此插件在 **Gateway 进程内部**运行。

如果使用远程 Gateway，在**运行 Gateway 的机器**上安装/配置，然后重启 Gateway。

不需要外部 `zca`/`openzca` CLI 二进制。

## 安装

### 选项 A：从 npm 安装

```bash
openclaw plugins install @openclaw/zalouser
```

使用裸包跟踪当前官方发布标签。仅在需要可复现安装时固定精确版本。

之后重启 Gateway。

### 选项 B：从本地文件夹安装（开发）

```bash
PLUGIN_SRC=./path/to/local/zalouser-plugin
openclaw plugins install "$PLUGIN_SRC"
cd "$PLUGIN_SRC" && pnpm install
```

之后重启 Gateway。

## 配置

Channel 配置在 `channels.zalouser` 下（不是 `plugins.entries.*`）：

```json5
{
  channels: {
    zalouser: {
      enabled: true,
      dmPolicy: "pairing",
    },
  },
}
```

## CLI

```bash
openclaw channels login --channel zalouser
openclaw channels logout --channel zalouser
openclaw channels status --probe
openclaw message send --channel zalouser --target <threadId> --message "Hello from OpenClaw"
openclaw directory peers list --channel zalouser --query "name"
```

## Agent 工具

工具名：`zalouser`

操作：`send`、`image`、`link`、`friends`、`groups`、`me`、`status`

Channel 消息操作还支持 `react` 做消息反应。

## 相关

- [Building plugins](/plugins/building-plugins)
- [ClawHub](/clawhub)
