# 社区插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不直接让插件全走 npm？

核心原因：**agent 插件的风险远高于普通 npm 包**。一个恶意插件可以拦截所有消息、执行任意代码、泄露凭据。所以 OpenClaw 选了 App Store 模式——ClawHub 做中间层,新发布在审核和验证完成前对安装和下载表面不可见。

这比纯 npm 多了一道闸：npm 发出去用户就能装,ClawHub 发出去还得过审核。代价是发布周期更长,但对 agent 工具链来说是正确取舍。

---

> Community plugins are third-party packages that extend OpenClaw with channels, tools, providers, hooks, or other capabilities.

社区插件是第三方包,用频道、工具、提供商、钩子或其他能力扩展 OpenClaw。用 [ClawHub](/clawhub) 作为公共社区插件的主要发现表面。

## 查找插件

> Search ClawHub from the CLI:

从 CLI 搜索 ClawHub：

```bash
openclaw plugins search "calendar"
```

> Install a ClawHub plugin with an explicit source prefix:

用显式源前缀安装 ClawHub 插件：

```bash
openclaw plugins install clawhub:<package-name>
```

> npm remains a supported direct-install path during the launch cutover:

npm 在启动切换期间仍是受支持的直接安装路径：

```bash
openclaw plugins install npm:<package-name>
```

> Use [Manage plugins](/plugins/manage-plugins) for common install, update, inspect, and uninstall examples.

常用安装、更新、检查和卸载示例见 [Manage plugins](/plugins/manage-plugins)。完整命令参考和源选择规则见 [`openclaw plugins`](/cli/plugins)。

## 发布插件

> Publish public community plugins on ClawHub when you want OpenClaw users to discover and install them.

想让 OpenClaw 用户发现和安装你的公共社区插件时,发布到 ClawHub。ClawHub 管理实时包列表、发布历史、扫描状态和安装提示；文档不维护静态第三方插件目录。

```bash
clawhub package publish your-org/your-plugin --dry-run
clawhub package publish your-org/your-plugin
```

> Before publishing, make sure the plugin has package metadata, a plugin manifest, setup docs, and a clear maintenance owner.

发布前确保插件有包元数据、插件清单、设置文档和明确的维护负责人。ClawHub 创建发布前会验证所有者范围、包名、版本、文件限制和源元数据。新发布在审核和验证完成前对正常安装和下载表面隐藏。

发布前检查清单：

| 要求                | 原因                                         |
| ------------------- | -------------------------------------------- |
| 发布在 ClawHub      | 用户需要 `openclaw plugins install` 提示可用 |
| 公共 GitHub 仓库    | 源码审查、问题追踪、透明性                   |
| 设置和使用文档      | 用户需要知道如何配置                         |
| 活跃维护            | 近期更新或积极响应问题处理                   |

完整发布契约见以下页面：

- [ClawHub publishing](/clawhub/publishing) —— 所有者、范围、发布、审核、包验证和包转移。
- [Building plugins](/plugins/building-plugins) —— 插件包结构和首次发布工作流。
- [Plugin manifest](/plugins/manifest) —— 原生插件清单字段。

## 相关

- [Plugins](/tools/plugin) —— 安装、配置、重启和故障排查
- [Manage plugins](/plugins/manage-plugins) —— 命令示例
- [ClawHub publishing](/clawhub/publishing) —— 发布和发布规则
