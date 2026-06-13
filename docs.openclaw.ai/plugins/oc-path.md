# OC Path 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不把文件寻址直接放进核心？

`oc-path` 是 opt-in 的,不是默认开启。关键取舍：解析器依赖（`jsonc-parser`、`markdown-it`、`yaml`）是插件本地的,不进核心运行时。从不使用 `openclaw path` 的安装不付任何成本。就像按需加载的 polyfill——不是每个用户都需要,需要的用户希望它精确可靠。

`oc://` 地址指向工作区文件的单个叶节点。四种文件格式（markdown/jsonc/jsonl/yaml）用统一接口寻址,但各自的解析和发射保持字节忠实度——注释、行尾、格式不被破坏。这和 `jq`/`yq` 的区别在于：`jq` 会重新格式化 JSON,`oc-path` 只改目标叶节点,其余原封不动。

脱敏哨兵也值得注意。携带 `__OPENCLAW_REDACTED__` 的叶节点在写入时被拒绝,CLI 输出中该标记被替换为 `[REDACTED]`。防止终端捕获和管道意外泄露脱敏标记。

---

内置 `oc-path` 插件为 `oc://` 工作区文件寻址方案添加 [`openclaw path`](/cli/path) CLI。它在 OpenClaw 仓库的 `extensions/oc-path/` 下发布,但是 opt-in——安装/构建后处于休眠状态直到启用。

`oc://` 地址指向工作区文件内的单个叶节点（或通配符叶节点集合）。插件当前理解四种文件：

- **markdown**（`.md`、`.mdx`）：frontmatter、节、条目、字段
- **jsonc**（`.jsonc`、`.json5`、`.json`）：注释和格式保留
- **jsonl**（`.jsonl`、`.ndjson`）：面向行的记录
- **yaml**（`.yaml`、`.yml`、`.lobster`）：通过 YAML 文档 API 的 map/sequence/scalar 节点

自托管者和编辑器扩展用 CLI 读写单个叶节点而无需直接对 SDK 编程。Agent 和钩子将其视为确定性基底,字节忠实度往返和脱敏哨兵保护在各种文件类型间统一适用。

## 为什么启用

脚本、钩子或本地 agent 工具需要指向工作区状态的精确片段而不想为每种文件格式发明解析器时启用 `oc-path`。单个 `oc://` 地址可命名 markdown frontmatter 键、节条目、JSONC 配置叶节点、JSONL 事件字段或 YAML 工作流步骤。

这对维护者工作流很重要——变更应小、可审计、可重复。检查一个值、找到匹配记录、干跑写入,然后仅应用该叶节点,留下注释、行尾和周围格式不动。作为 opt-in 插件保留让高级用户获得寻址基底,而不将解析器依赖或 CLI 表面放入从不使用它的安装的核心。

常见启用原因：

- **本地自动化**：shell 脚本可用 `openclaw path … --json` 解析或更新一个工作区值,而无需携带独立的 markdown、JSONC、JSONL 和 YAML 解析代码。
- **Agent 可见编辑**：agent 可在写入前为一个寻址叶节点显示干跑 diff,比自由格式文件重写更易审查。
- **编辑器集成**：编辑器可将 `oc://AGENTS.md/tools/gh` 映射到精确 markdown 节点和行号,无需从标题文本猜测。
- **诊断**：`emit` 将文件往返通过解析器和发射器,可在依赖自动化编辑前检查文件格式是否字节稳定。

具体示例：

```bash
# 此配置中 GitHub 插件是否启用？
openclaw path resolve 'oc://config.jsonc/plugins/github/enabled' --json

# 此会话日志中出现哪些工具调用名？
openclaw path find 'oc://session.jsonl/[event=tool_call]/name' --json

# 这个小编辑会写入什么字节？
openclaw path set 'oc://config.jsonc/plugins/github/enabled' 'true' --dry-run
```

插件有意不做高层语义的所有者。记忆插件仍持有记忆写入,config 命令仍持有完整配置管理,LKG 逻辑仍持有恢复/提升。`oc-path` 是窄寻址和字节保持文件操作层,高层工具可围绕它构建。

## 运行位置

插件在调用命令的宿主机上**在 `openclaw` CLI 进程内**运行。不需要运行中的 Gateway 也不打开任何网络套接字——每个动词是对指向文件的纯变换。

插件元数据在 `extensions/oc-path/openclaw.plugin.json`：

```json
{
  "id": "oc-path",
  "name": "OC Path",
  "activation": {
    "onStartup": false,
    "onCommands": ["path"]
  },
  "commandAliases": [{ "name": "path", "kind": "cli" }]
}
```

`onStartup: false` 让插件不进入 Gateway 热路径。`onCommands: ["path"]` 告诉 CLI 在首次运行 `openclaw path …` 时懒加载插件,从不使用该动词的安装不付成本。

## 启用

```bash
openclaw plugins enable oc-path
```

重启 Gateway（如运行的话）让清单快照拾取新状态。裸 `openclaw path` 调用在同一宿主机上立即可用——CLI 按需加载插件。

禁用：

```bash
openclaw plugins disable oc-path
```

## 依赖

所有解析器依赖是插件本地的——启用 `oc-path` 不将新包拉入核心运行时：

| 依赖           | 用途                                                         |
| -------------- | ------------------------------------------------------------ |
| `commander`    | `resolve`、`find`、`set`、`validate`、`emit` 的子命令接线。 |
| `jsonc-parser` | JSONC 解析 + 叶节点编辑,保留注释和尾逗号。                   |
| `markdown-it`  | 节/条目/字段模型的 Markdown 标记化。                         |
| `yaml`         | YAML `Document` 解析/发射/编辑,保留注释和流式风格。          |

JSONL 保持手写——面向行解析比任何依赖都简单,每行 JSONC 解析已走 `jsonc-parser`。

## 提供什么

| 表面                         | 提供者                                                  |
| ---------------------------- | ------------------------------------------------------- |
| `openclaw path` CLI          | `extensions/oc-path/cli-registration.ts`                |
| `oc://` 解析器/格式化器      | `extensions/oc-path/src/oc-path/oc-path.ts`             |
| 每种类型解析/发射/编辑       | `extensions/oc-path/src/oc-path/{md,jsonc,jsonl,yaml}`  |
| 通用 resolve/find/set        | `extensions/oc-path/src/oc-path/{resolve,find,edit}.ts` |
| 脱敏哨兵保护                 | `extensions/oc-path/src/oc-path/sentinel.ts`            |

CLI 是当前唯一的公共表面。基底动词对插件私有；消费者使用 CLI（或基于 SDK 构建自己的插件）。

## 与其他插件的关系

- **`memory-*`**：记忆写入通过记忆插件,不通过 `oc-path`。`oc-path` 是通用文件基底；记忆插件在其上层叠自己的语义。
- **LKG**：`path` 不知道 Last-Known-Good 配置恢复。文件被 LKG 追踪时,下次 `observe` 调用决定提升还是恢复；通过 LKG promote/recover 生命周期的原子多设置的 `set --batch` 计划与 LKG 恢复基底同步。

## 安全

`set` 通过基底发射路径写入原始字节,自动应用脱敏哨兵保护。携带 `__OPENCLAW_REDACTED__`（字面或子串）的叶节点在写入时被 `OC_EMIT_SENTINEL` 拒绝。CLI 还从打印的任何人类或 JSON 输出中清除字面哨兵,替换为 `[REDACTED]`,终端捕获和管道永不泄露标记。

## 相关

- [`openclaw path` CLI reference](/cli/path)
- [Manage plugins](/plugins/manage-plugins)
- [Building plugins](/plugins/building-plugins)
