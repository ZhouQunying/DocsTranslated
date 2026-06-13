# 管理插件

## 架构精读

> 跳过不影响阅读翻译正文。

### `plugins list` 和 `inspect --runtime` 为什么是两件事？

关键在于**静态清单和运行时注册是分离的**。`list` 是冷盘存——从配置、清单文件和注册表发现插件,但不证明 Gateway 进程真的加载了它。就像 Kubernetes 的 `kubectl get deployments` 只看 spec 不看 Pod 状态。要证明插件在运行时真的注册了工具、钩子、路由,得用 `inspect --runtime`,相当于 `kubectl get pods`。

源选择模型也值得注意。`clawhub:`、`npm:`、`git:`、`npm-pack:` 前缀把多个包来源统一到同一接口下,裸名在启动切换期默认走 npm。但 `update` 会记住首次安装时的源——装了 `clawhub:foo` 后 `update foo` 仍从 ClawHub 拉。这避免了"装了 A 源结果更新跳到 B 源"的惊喜。

重启策略的区分也有讲究：插件源码变更（安装/更新/卸载）触发受管 Gateway 自动重启；配置变更（enable/disable）走热重载。源码改了需要重启是因为模块已在内存里,改不了；配置改了只需重读就行。

---

> Use this page for common plugin management commands.

常用插件管理命令见本页。完整命令契约、标志、源选择规则和边界情况见 [`openclaw plugins`](/cli/plugins)。

多数安装工作流：

1. 找到包
2. 从 ClawHub、npm、git 或本地路径安装
3. 让受管 Gateway 自动重启,非受管时手动重启
4. 验证插件的运行时注册

## 列出和搜索插件

```bash
openclaw plugins list
openclaw plugins list --enabled
openclaw plugins list --verbose
openclaw plugins list --json
openclaw plugins search "calendar"
```

脚本用 `--json`：

```bash
openclaw plugins list --json \
  | jq '.plugins[] | {id, enabled, format, source, dependencyStatus}'
```

> `plugins list` is a cold inventory check...

`plugins list` 是冷盘存检查。它显示 OpenClaw 从配置、清单和注册表能发现什么；不证明已运行的 Gateway 导入了插件运行时。JSON 输出包含注册表诊断和插件的静态 `dependencyStatus`（当插件包声明了 `dependencies` 或 `optionalDependencies` 时）。

> `plugins search` queries ClawHub for installable plugin packages...

`plugins search` 查询 ClawHub 获取可安装的插件包并打印安装提示,如 `openclaw plugins install clawhub:<package>`。

## 安装插件

```bash
# 搜索 ClawHub 插件包。
openclaw plugins search "calendar"

# 从 ClawHub 安装。
openclaw plugins install clawhub:<package>
openclaw plugins install clawhub:<package>@1.2.3
openclaw plugins install clawhub:<package>@beta

# 从 npm 安装。
openclaw plugins install npm:<package>
openclaw plugins install npm:@scope/openclaw-plugin@1.2.3
openclaw plugins install npm:@openclaw/codex

# 从本地 npm pack 产物安装。
openclaw plugins install npm-pack:<path.tgz>

# 从 git 或本地开发检出安装。
openclaw plugins install git:github.com/acme/openclaw-plugin@v1.0.0
openclaw plugins install ./my-plugin
openclaw plugins install --link ./my-plugin
```

> Bare package specs install from npm during the launch cutover...

裸包名在启动切换期从 npm 安装。需要确定性源选择时用 `clawhub:`、`npm:`、`git:` 或 `npm-pack:`。裸名匹配官方插件 id 时 OpenClaw 可直接安装目录条目。

> Use `--force` only when you intentionally want to overwrite an existing install target.

`--force` 仅在故意覆盖已有安装目标时使用。已追踪的 npm、ClawHub 或钩子包安装的常规升级用 `openclaw plugins update`。

## 重启和检查

> After installing, updating, or uninstalling plugin code...

安装、更新或卸载插件代码后,启用了配置重载的受管 Gateway 自动重启。Gateway 非受管或禁用重载时,检查实时运行时表面前先自行重启：

```bash
openclaw gateway restart
openclaw plugins inspect <plugin-id> --runtime --json
```

> Use `inspect --runtime` when you need proof that the plugin registered runtime surfaces...

需要证明插件注册了运行时表面（工具、钩子、服务、Gateway 方法、HTTP 路由或插件持有的 CLI 命令）时用 `inspect --runtime`。普通 `inspect` 和 `list` 是冷清单、配置和注册表检查。

## 更新插件

```bash
openclaw plugins update <plugin-id>
openclaw plugins update <npm-package-or-spec>
openclaw plugins update --all
openclaw plugins update <plugin-id> --dry-run
```

> When you pass a plugin id, OpenClaw reuses the tracked install spec.

传插件 id 时 OpenClaw 复用追踪的安装规格。存储的 dist-tag（如 `@beta`）和精确固定版本在后续 `update <plugin-id>` 运行中继续使用。

> For npm installs, you can pass an explicit package spec to switch the tracked record:

npm 安装可传显式包规格切换追踪记录：

```bash
openclaw plugins update @scope/openclaw-plugin@beta
openclaw plugins update @scope/openclaw-plugin
```

第二条命令将之前固定到精确版本或标签的插件移回注册表的默认发布线。

> When `openclaw update` runs on the beta channel...

`openclaw update` 在 beta 通道运行时,插件记录可优先匹配 `@beta` 发布。精确回退和固定规则见 [`openclaw plugins`](/cli/plugins#update)。

## 卸载插件

```bash
openclaw plugins uninstall <plugin-id> --dry-run
openclaw plugins uninstall <plugin-id>
openclaw plugins uninstall <plugin-id> --keep-files
```

> Uninstall removes the plugin's config entry, persisted plugin index record, allow/deny list entries, and linked load paths when applicable.

卸载移除插件的配置条目、持久化插件索引记录、允许/拒绝列表条目和关联的加载路径。传 `--keep-files` 则保留受管安装目录。卸载变更插件源码时受管 Gateway 自动重启。

> In Nix mode (`OPENCLAW_NIX_MODE=1`), plugin install, update, uninstall, enable, and disable commands are disabled.

Nix 模式（`OPENCLAW_NIX_MODE=1`）下插件的安装、更新、卸载、启用和禁用命令被禁用。改为在 Nix 源码中管理这些选择。

## 选择源

| 源          | 适用场景                                                   | 示例                                                           |
| ----------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| ClawHub     | 需要 OpenClaw 原生发现、扫描摘要、版本和提示               | `openclaw plugins install clawhub:<package>`                   |
| npmjs.com   | 已有 JavaScript 包发布流程或需要 npm dist-tag/私有注册表   | `openclaw plugins install npm:@acme/openclaw-plugin`           |
| git         | 需要仓库的分支、标签或提交                                 | `openclaw plugins install git:github.com/<owner>/<repo>@<ref>` |
| 本地路径    | 在同一台机器上开发或测试插件                               | `openclaw plugins install --link ./my-plugin`                  |
| npm pack    | 通过 npm 安装语义验证本地包产物                            | `openclaw plugins install npm-pack:<path.tgz>`                 |
| marketplace | 安装 Claude 兼容的 marketplace 插件                        | `openclaw plugins install <plugin> --marketplace <source>`     |

> Managed local path installs must be plugin directories or archives.

受管本地路径安装必须是插件目录或归档。独立插件文件放 `plugins.load.paths` 而非用 `plugins install` 安装。

## 发布插件

> ClawHub is the primary public discovery surface for OpenClaw plugins.

ClawHub 是 OpenClaw 插件的主要公共发现表面。想让用户在安装前看到插件元数据、版本历史、注册表扫描结果和安装提示时发布到这里。

```bash
npm i -g clawhub
clawhub login
clawhub package publish your-org/your-plugin --dry-run
clawhub package publish your-org/your-plugin
clawhub package publish your-org/your-plugin@v1.0.0
```

> Native npm plugins must include a plugin manifest and package metadata before publishing:

原生 npm 插件发布前必须包含插件清单和包元数据：

```json package.json
{
  "name": "@acme/openclaw-plugin",
  "version": "1.0.0",
  "type": "module",
  "openclaw": {
    "extensions": ["./dist/index.js"]
  }
}
```

```bash
npm publish --access public
openclaw plugins install npm:@acme/openclaw-plugin
openclaw plugins install npm:@acme/openclaw-plugin@beta
openclaw plugins install npm:@acme/openclaw-plugin@1.0.0
```

完整发布契约见以下页面而非本页作为发布参考：

- [ClawHub publishing](/clawhub/publishing) —— 所有者、范围、发布、审核、包验证和包转移。
- [Building plugins](/plugins/building-plugins) —— 插件包结构和首次发布工作流。
- [Plugin manifest](/plugins/manifest) —— 原生插件清单字段。

> If the same package is available on both ClawHub and npm...

同一包同时在 ClawHub 和 npm 上时,需要强制指定源时用显式 `clawhub:` 或 `npm:` 前缀。

## 相关

- [Plugins](/tools/plugin) —— 安装、配置、重启和故障排查
- [`openclaw plugins`](/cli/plugins) —— 完整 CLI 参考
- [Community plugins](/plugins/community) —— 公共发现和 ClawHub 发布
- [ClawHub](/clawhub/cli) —— 注册表 CLI 操作
- [Building plugins](/plugins/building-plugins) —— 创建插件包
- [Plugin manifest](/plugins/manifest) —— 清单和包元数据
