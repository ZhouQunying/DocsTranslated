# 原生 Codex 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 三个独立状态为什么要分开？

原生插件有三个独立状态：**已安装**（Codex app-server 运行时里有 bundle）、**已启用**（OpenClaw 配置允许该插件）、**可访问**（Codex app-server 确认该插件的 app 对当前账号可用）。三者缺一不可但互相独立。

这和 Docker 部署三阶段一个道理：镜像拉下来了（Installed）、Deployment 副本数设成 1 了（Enabled）、就绪探针通过了（Accessible）。任何一个阶段失败,插件就不工作,但失败原因完全不同。Migration 管前两关,运行时检查第三关。

线程 app 配置也值得注意。OpenClaw 给 Codex 线程注入的是**限制性** `config.apps`：`_default` 被禁用,只有已启用且已迁移的插件名下的 app 才被打开。就像最小权限原则——不是"默认全部开放然后逐个关",而是"默认全关然后逐个开"。

---

原生 Codex 插件支持让 Codex 模式下的 OpenClaw agent 在同一 Codex 线程内使用 Codex app-server 自身的 app 和插件能力,该线程同时处理 OpenClaw 轮次。

OpenClaw 不把 Codex 插件翻译成合成的 `codex_plugin_*` OpenClaw 动态工具。插件调用留在原生 Codex 转录中,Codex app-server 负责 app 支持的 MCP 执行。

在基础 [Codex harness](/plugins/codex-harness) 跑通后再使用本页。

## 前提条件

- 选定的 OpenClaw agent 运行时必须是原生 Codex harness。
- `plugins.entries.codex.enabled` 必须为 true。
- `plugins.entries.codex.config.codexPlugins.enabled` 必须为 true。
- V1 仅支持迁移时观察到已源码安装在源 Codex home 的 `openai-curated` 插件。
- 目标 Codex app-server 必须能看到预期的 marketplace、插件和 app 清单。

`codexPlugins` 对 OpenClaw 运行、普通 OpenAI 提供商运行、ACP 会话绑定或其他 harness 无效,因为这些路径不创建带原生 `apps` 配置的 Codex app-server 线程。

OpenAI 侧 Codex 访问权、app 可用性和工作区 app/插件控制来自已登录的 Codex 账号。OpenAI 账号和管理模型见 [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)。

## 快速开始

从源 Codex home 预览迁移：

```bash
openclaw migrate codex --dry-run
```

需要在规划原生插件激活前检查源 app 可访问性时,使用严格源 app 验证：

```bash
openclaw migrate codex --dry-run --verify-plugin-apps
```

计划确认无误后应用迁移：

```bash
openclaw migrate apply codex --yes
```

迁移为符合条件的插件写入显式 `codexPlugins` 条目并对选定插件调用 Codex app-server `plugin/install`。典型迁移后配置如下：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          codexPlugins: {
            enabled: true,
            allow_destructive_actions: true,
            plugins: {
              "google-calendar": {
                enabled: true,
                marketplaceName: "openai-curated",
                pluginName: "google-calendar",
              },
            },
          },
        },
      },
    },
  },
}
```

`codexPlugins` 变更后,新 Codex 会话自动拾取更新的 app 集合。用 `/new` 或 `/reset` 刷新当前会话。插件启用或禁用变更不需要 gateway 重启。

## 从聊天管理插件

需要在操作 Codex harness 的同一聊天中检查或修改已配置的原生 Codex 插件时,使用 `/codex plugins`：

```text
/codex plugins
/codex plugins list
/codex plugins disable google-calendar
/codex plugins enable google-calendar
```

`/codex plugins` 是 `/codex plugins list` 的别名。列表输出显示 `plugins.entries.codex.config.codexPlugins.plugins` 中已配置的插件键、开关状态、Codex 插件名和 marketplace。

`enable` 和 `disable` 仅写入 `~/.openclaw/openclaw.json` 中的 OpenClaw 配置；不编辑 `~/.codex/config.toml` 也不安装新 Codex 插件。仅所有者或持有 `operator.admin` 权限范围的 gateway 客户端可变更插件状态。

启用已配置的插件同时开启全局 `codexPlugins.enabled` 开关。如果插件因迁移返回 `auth_required` 而被写入为禁用状态,先在 Codex 中重新授权该 app,再在 OpenClaw 中启用。

## 原生插件设置的工作原理

集成有三个独立状态：

- 已安装：Codex 在目标 app-server 运行时中持有本地插件 bundle。
- 已启用：OpenClaw 配置愿意将该插件提供给 Codex harness 轮次。
- 可访问：Codex app-server 确认该插件的 app 条目对活跃账号可用且可映射到已迁移的插件身份。

迁移是持久化的安装/资格审查步骤。规划阶段 OpenClaw 读取源 Codex `plugin/read` 详情并检查源 Codex app-server 账号响应是否为 ChatGPT 订阅账号。非 ChatGPT 或缺失账号响应跳过 app 支持的插件,标记 `codex_subscription_required`。默认情况下迁移不调用源 `app/list`；通过账号关卡的 app 支持源插件不做源 app 可访问性验证直接被规划,账号查找传输失败以 `codex_account_unavailable` 跳过。使用 `--verify-plugin-apps` 时,迁移获取源 `app/list` 新快照并要求每个名下 app 在规划原生激活前存在、启用且可访问。该模式下账号查找传输失败回落到源 app 清单关卡。运行时 app 清单是迁移后的目标会话可访问性检查。Codex harness 会话设置随后为已启用且可访问的插件 app 计算限制性线程 app 配置。

线程 app 配置在 OpenClaw 建立 Codex harness 会话或替换陈旧 Codex 线程绑定时计算。不在每轮重新计算,所以 `/codex plugins enable` 和 `/codex plugins disable` 影响新 Codex 会话。当前会话需要拾取更新的 app 集合时用 `/new` 或 `/reset`。

## V1 支持边界

V1 有意收窄：

- 仅已安装在源 Codex app-server 清单中的 `openai-curated` 插件有迁移资格。
- App 支持的源插件必须通过迁移时订阅关卡。`--verify-plugin-apps` 增加源 app 清单关卡。订阅关卡账号加上验证模式下不可访问、禁用、缺失的源 app 或源 app 清单刷新失败被报告为跳过的手动条目而非启用的配置条目。不可读的插件详情在源 app 清单关卡前跳过。
- 迁移写入带 `marketplaceName` 和 `pluginName` 的显式插件身份；不写入本地 `marketplacePath` 缓存路径。
- `codexPlugins.enabled` 是全局启用开关。
- 没有 `plugins["*"]` 通配符也没有授予任意安装权限的配置键。
- 不支持的 marketplace、缓存的插件 bundle、钩子和 Codex 配置文件在迁移报告中保留供手动审查。

## App 清单和所有权

OpenClaw 通过 app-server `app/list` 读取 Codex app 清单,缓存一小时并在陈旧或缺失时异步刷新。缓存仅在内存中；重启 CLI 或 gateway 会丢弃缓存,OpenClaw 从下次 `app/list` 读取重建。

迁移和运行时使用不同缓存键：

- 源迁移验证使用源 Codex home 和源 app-server 启动选项。仅在设置了 `--verify-plugin-apps` 时运行,并强制该规划运行的源 `app/list` 全新遍历。
- 目标运行时设置在构建 Codex 线程 app 配置时使用目标 agent 的 Codex app-server 身份。插件激活使该目标缓存键失效并在 `plugin/install` 后强制刷新。

插件 app 仅在 OpenClaw 能通过稳定所有权将其映射回已迁移插件时暴露：

- 插件详情中的精确 app id
- 已知 MCP 服务器名
- 唯一稳定元数据

仅显示名称或模糊所有权被排除,直到下次清单刷新证明所有权。

## 线程 app 配置

OpenClaw 为 Codex 线程注入限制性 `config.apps` 补丁：`_default` 被禁用,仅已启用的已迁移插件名下的 app 被启用。

OpenClaw 从有效的全局或每插件 `allow_destructive_actions` 策略设置 app 级 `destructive_enabled`,并让 Codex 从其原生 app 工具注解执行破坏性工具元数据。`_default` app 配置以 `open_world_enabled: false` 禁用。已启用的插件 app 以 `open_world_enabled: true` 发出；OpenClaw 不暴露单独的插件开放世界策略旋钮,也不维护每插件破坏性工具名拒绝列表。

插件 app 的工具审批模式默认自动,非破坏性读工具无线程内审批 UI 直接运行。破坏性工具仍受各 app 的 `destructive_enabled` 策略控制。

## 破坏性操作策略

已迁移的 Codex 插件默认允许破坏性插件操作,但不安全 schema 和模糊所有权仍然失败即拒绝：

- 全局 `allow_destructive_actions` 默认 `true`。
- 每插件 `allow_destructive_actions` 覆盖该插件的全局策略。
- 策略为 `false` 时 OpenClaw 返回确定性拒绝。
- 策略为 `true` 时 OpenClaw 仅自动接受可映射到审批响应的安全 schema,如布尔批准字段。
- 缺失插件身份、模糊所有权、缺失 turn id、错误 turn id 或不安全操作 schema 拒绝而非提示。

## 故障排查

**`auth_required`：** 迁移已安装插件但其某个 app 仍需认证。显式插件条目写入为禁用状态直到重新授权并启用。

**`app_inaccessible`、`app_disabled` 或 `app_missing`：** 迁移未安装该插件,因为设置了 `--verify-plugin-apps` 时源 Codex app 清单未显示所有名下 app 为存在、启用且可访问。在 Codex 中重新授权或启用该 app,然后用 `--verify-plugin-apps` 重跑迁移。

**`app_inventory_unavailable`：** 迁移未安装该插件,因为请求了严格源 app 验证且源 Codex app 清单刷新失败。修复源 Codex app-server 访问,或接受更快的账号关卡规划时不带 `--verify-plugin-apps` 重试。

**`codex_subscription_required`：** 迁移未安装该 app 支持插件,因为源 Codex app-server 账号未以 ChatGPT 订阅账号登录。用订阅认证登录 Codex app 后重跑迁移。

**`codex_account_unavailable`：** 迁移未安装该 app 支持插件,因为源 Codex app-server 账号不可读。修复源 Codex app-server 认证,或账号查找失败时想用源 app 清单决定资格则带 `--verify-plugin-apps` 重跑。

**`marketplace_missing` 或 `plugin_missing`：** 目标 Codex app-server 看不到预期的 `openai-curated` marketplace 或插件。对目标运行时重跑迁移或检查 Codex app-server 插件状态。

**`app_inventory_missing` 或 `app_inventory_stale`：** app 就绪状态来自空或陈旧缓存。OpenClaw 调度异步刷新并在所有权和就绪状态已知前排除插件 app。

**`app_ownership_ambiguous`：** app 清单仅按显示名称匹配,该 app 不暴露给 Codex 线程。

**配置已变更但 agent 看不到插件：** 用 `/codex plugins list` 确认配置状态,然后用 `/new` 或 `/reset`。现有 Codex 线程绑定保持其启动时的 app 配置,直到 OpenClaw 建立新 harness 会话或替换陈旧绑定。

**破坏性操作被拒绝：** 检查全局和每插件 `allow_destructive_actions` 值。即使策略为 true,不安全操作 schema 和模糊插件身份仍然失败即拒绝。

## 相关

- [Codex harness](/plugins/codex-harness)
- [Codex harness reference](/plugins/codex-harness-reference)
- [Codex harness runtime](/plugins/codex-harness-runtime)
- [Configuration reference](/gateway/configuration-reference#codex-harness-plugin-config)
- [Migrate CLI](/cli/migrate)
