# Configuration

## 架构精读

> 跳过不影响阅读翻译正文。

### JSON5 格式——为什么不用纯 JSON 或 YAML？

OpenClaw 选择 JSON5 作为配置文件格式，这是 JSON 的超集，支持注释和末尾逗号：

```json5
{
  // 这是注释
  model: "gpt-4",  // 无引号键
  tools: ["shell", "web",],  // 末尾逗号
}
```

这跟 TypeScript 与 JavaScript 是一个思路——TS 是 JS 超集，加了类型但保持兼容。JSON5 = JSON 的简单 + YAML 的人性化，但没有 YAML 的缩进陷阱和隐式类型转换。

关键设计是**配置文件的可维护性**。纯 JSON 不支持注释，运维者无法解释“为什么这个值是这样”。YAML 语法灵活但容易出错（缩进错误、`yes`/`no` 被解析为布尔值）。JSON5 在两者之间找到平衡。

### 四种配置方式——为什么需要这么多入口？

OpenClaw 提供四种配置入口：

1. **交互式向导** (`openclaw configure`)：新手友好
2. **CLI 单行命令** (`openclaw models set gpt-4`)：脚本自动化
3. **控制界面**（网页界面）：不喜欢命令行
4. **直接编辑文件**：高级用户

这跟 AWS 控制台、CLI、SDK、CloudFormation 是一个思路——不同用户群体偏好不同，不强迫任何人用不习惯的方式。

代价是需要维护四种配置入口。但这降低了入门摩擦——每个人用自己最舒服的方式。

### 热更新与重启——哪些配置能即时生效？

配置修改后分两类：

- **热更新**（热应用）：策略类配置（模型选择、工具开关、私信策略），改了立刻生效
- **需要重启**：基础设施类配置（端口、TLS、数据库连接），启动时固定

这跟 nginx 重新加载与重启是一个思路——`proxy_pass` 可以重新加载生效，`listen` 端口改了必须重启。

设计原因是**运行时状态**。策略类配置每次请求时读取，可以热更新。基础设施类配置在启动时初始化（绑定端口、加载证书、建立连接），必须重启。

### 符号链接不被支持——为什么？

配置文件路径必须是**真实文件**（普通文件），不能是符号链接。

这跟 inotify 的文件监控行为有关。文件监控工具对符号链接的行为不一致——有些监控符号链接本身，有些监控目标文件。如果 OpenClaw 监控符号链接，可能出现“改了配置但网关没检测到”的问题。

替代方案：用 `rsync` 或 `scp` 复制文件，不用符号链接。

---

OpenClaw reads an optional JSON5 config from `~/.openclaw/openclaw.json`. The active config path must be a regular file. Symlinked `openclaw.json` layouts are unsupported for OpenClaw-owned writes; an atomic write may replace the path instead of preserving the symlink. If you keep config outside the default state directory, point `OPENCLAW_CONFIG_PATH` directly at the real file.

If the file is missing, OpenClaw uses safe defaults. Common reasons to add a config:

- Connect channels and control who can message the bot
- Set models, tools, sandboxing, or automation (cron, hooks)
- Tune sessions, media, networking, or UI

See the full reference for every available field.

Agents and automation should use `config.schema.lookup` for exact field-level docs before editing config. Use this page for task-oriented guidance and Configuration reference for the broader field map and defaults.

> **Tip**: New to configuration? Start with `openclaw onboard` for interactive setup, or check out the Configuration Examples guide for complete copy-paste configs.

OpenClaw 从 `~/.openclaw/openclaw.json` 读取可选的 JSON5 配置。活动配置路径必须是真实文件。Symlink 的 `openclaw.json` 布局不支持 OpenClaw 的写入操作；原子写入可能会替换路径而不是保留 symlink。如果你把配置放在默认状态目录之外，把 `OPENCLAW_CONFIG_PATH` 直接指向真实文件。

如果文件缺失，OpenClaw 使用安全默认值。添加配置的常见原因：

- 连接 channel 并控制谁能给 bot 发消息
- 设置模型、工具、沙箱或自动化（cron、hooks）
- 调整 session、media、网络或 UI

完整字段见完整参考文档。

Agent 和自动化在编辑配置前应该用 `config.schema.lookup` 查询精确的字段级文档。本页用于任务导向的指导，Configuration reference 用于更广泛的字段映射和默认值。

> **提示**：刚接触配置？用 `openclaw onboard` 做交互式设置，或查看 Configuration Examples 指南获取完整的可复制粘贴配置。
