# Configuration

**总结：** OpenClaw 使用可选的 JSON5 配置文件 `~/.openclaw/openclaw.json` 控制 bot 行为——缺省时使用安全默认值。配置覆盖 channels、models、tools、sandbox、automation、sessions、media、networking 和 UI。

> **类比：K8s ConfigMap + Helm values + nginx reload。** ConfigMap 提供分层配置（default → namespace → pod），Helm values 用 YAML 覆盖模板参数，nginx reload 热更新不重启。OpenClaw 配置类似——JSON5 格式（支持注释和末尾逗号），四种编辑入口（交互向导 `openclaw configure`、CLI 单行命令、Control UI web 界面、直接编辑文件），严格 schema 校验（未知 key 或无效值阻止启动），文件监控热重载（策略类即时生效、基础设施类需重启），RPC 编程式更新（schema lookup → get → patch → apply，hash 冲突检测），环境变量支持（`.env` 文件、`${VAR_NAME}` 替换、secret reference）。
>
> **架构要点：** 配置格式：JSON5（JSON 超集，支持注释 `//`、末尾逗号、无引号键）；加载位置：`~/.openclaw/openclaw.json`（不支持 symlink，必须真实文件）；四种编辑方式：`openclaw configure`（向导）、`openclaw <sub> set`（CLI）、Control UI（web）、直接编辑；严格校验：启动时 schema 全量检查，未知 key 或类型错误阻止启动，给出具体修复建议，诊断命令可用于排查；热重载：文件监控自动 reload，四种模式（hybrid 默认/hot/restart/off），策略类（model/tool/agent/channel）即时生效，基础设施类（port/TLS/database）需重启；RPC：`config.schema.lookup`/`config.get`/`config.patch`/`config.apply`，hash 冲突检测，rate limit；环境变量：`.env` 文件加载、shell 环境导入、`${VAR_NAME}` 替换、secret reference（env/file/exec 三种 source）；`$include` 拆分配置（多文件合并，数组 deep-merge，最多嵌套 10 层）。
