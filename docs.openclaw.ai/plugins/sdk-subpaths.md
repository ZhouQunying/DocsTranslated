# Plugin SDK 子路径

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 SDK 导出数量需要 CI 审计？

一般 SDK 作者加新导出时不会删除旧导出，怕破坏已有用户。结果 SDK 表面积只增不减，几年后变成一锅粥。OpenClaw 用 `pnpm plugin-sdk:surface` 审计公开导出数量，用 `pnpm plugins:boundary-report:summary` 审计保留 helper 子路径。未使用的保留 helper 导出让 CI 报告失败，而不是作为休眠兼容债务留在公开 SDK 中。这就像 TypeScript 的 `noUnusedLocals`——编译器强制清理，不靠人记得删。好处是 SDK 表面积可控，坏处是维护者需要定期运行审计命令。

第二个关键设计：子路径按能力分组，不按文件位置。`plugin-sdk/channel-inbound` 包含所有入站 channel helper，`plugin-sdk/channel-outbound` 包含所有出站 helper。同一个文件可能导出到多个子路径——逻辑分组优先于物理布局。就像 Kubernetes API 的 core/v1、apps/v1——用户按能力找 API，不关心源码在哪个目录。

第三个边界：公开、私有、已弃用三层严格分离。公开子路径是第三方插件可导入的契约。私有子路径（`scripts/lib/plugin-sdk-private-local-only-subpaths.json` 列出）仅仓库内测试可用。已弃用子路径保持导出但 CI 拒绝捆绑插件的新的生产导入。就像 Java 9 模块系统的 exports/opens/provides——每个导出都有明确的可见性级别。

---

插件 SDK 以 `openclaw/plugin-sdk/` 下的一组窄公开子路径暴露。本页按用途分组列出常用子路径。生成的编译器入口点清单在 `scripts/lib/plugin-sdk-entrypoints.json`；包导出是公开子集，减去 `scripts/lib/plugin-sdk-private-local-only-subpaths.json` 中列出的仓库本地测试/内部子路径。维护者可用 `pnpm plugin-sdk:surface` 审计公开导出数量，用 `pnpm plugins:boundary-report:summary` 审计活跃保留 helper 子路径；未使用的保留 helper 导出让 CI 报告失败，而不是作为休眠兼容债务留在公开 SDK 中。

插件编写指南见 [Plugin SDK overview](/plugins/sdk-overview)。

## 插件入口

| 子路径                         | 关键导出                                                                                                                                                               |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plugin-sdk/plugin-entry`      | `definePluginEntry`                                                                                                                                                    |
| `plugin-sdk/core`              | `defineChannelPluginEntry`、`createChatChannelPlugin`、`createChannelPluginBase`、`defineSetupPluginEntry`、`buildChannelConfigSchema`、`buildJsonChannelConfigSchema` |
| `plugin-sdk/config-schema`     | `OpenClawSchema`                                                                                                                                                       |
| `plugin-sdk/provider-entry`    | `defineSingleProviderPluginEntry`                                                                                                                                      |
| `plugin-sdk/migration`         | 迁移 provider 条目 helper，如 `createMigrationItem`、原因常量、条目状态标记、脱敏 helper 和 `summarizeMigrationItems`                                                  |
| `plugin-sdk/migration-runtime` | 运行时迁移 helper，如 `copyMigrationFileItem`、`withCachedMigrationConfigRuntime` 和 `writeMigrationReport`                                                           |
| `plugin-sdk/health`            | Doctor 健康检查注册、检测、修复、选择、严重性和发现类型，用于捆绑健康消费者                                                                                            |

### 已弃用兼容和测试 helper

已弃用子路径保持导出以兼容旧插件，但新代码应用下面的聚焦 SDK 子路径。维护的列表是 `scripts/lib/plugin-sdk-deprecated-public-subpaths.json`；CI 拒绝捆绑插件的生产导入。广泛 barrel 如 `compat`、`config-types`、`infra-runtime`、`text-runtime` 和 `zod` 仅用于兼容。直接从 `zod` 导入 `zod`。

OpenClaw 的 Vitest 支持的测试 helper 子路径仅仓库本地使用，不再是包导出：`agent-runtime-test-contracts`、`channel-contract-testing`、`channel-target-testing`、`channel-test-helpers`、`plugin-test-api`、`plugin-test-contracts`、`plugin-test-runtime`、`provider-http-test-mocks`、`provider-test-contracts`、`test-env`、`test-fixtures`、`test-node-mocks` 和 `testing`。

### 保留的捆绑插件 helper 子路径

这些子路径是其持有的捆绑插件的兼容表面，不是通用 SDK API：`plugin-sdk/codex-mcp-projection` 和 `plugin-sdk/codex-native-task-runtime`。跨 owner 扩展导入被包契约守卫阻断。

**Channel 子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/channel-core` | `defineChannelPluginEntry`、`defineSetupPluginEntry`、`createChatChannelPlugin`、`createChannelPluginBase` |
| `plugin-sdk/config-schema` | 根 `openclaw.json` Zod schema 导出（`OpenClawSchema`） |
| `plugin-sdk/json-schema-runtime` | 插件持有 schema 的缓存 JSON Schema 验证 helper |
| `plugin-sdk/channel-setup` | `createOptionalChannelSetupSurface`、`createOptionalChannelSetupAdapter`、`createOptionalChannelSetupWizard`，加 `DEFAULT_ACCOUNT_ID`、`createTopLevelChannelDmPolicy`、`setSetupChannelEnabled`、`splitSetupEntries` |
| `plugin-sdk/setup` | 共享设置向导 helper、设置翻译器、允许列表提示、设置状态构建器 |
| `plugin-sdk/setup-runtime` | `createSetupTranslator`、`createPatchedAccountSetupAdapter`、`createEnvPatchedAccountSetupAdapter`、`createSetupInputPresenceValidator`、`noteChannelLookupFailure`、`noteChannelLookupSummary`、`promptResolvedAllowFrom`、`splitSetupEntries`、`createAllowlistSetupWizardProxy`、`createDelegatedSetupWizardProxy` |
| `plugin-sdk/setup-adapter-runtime` | 已弃用兼容别名；用 `plugin-sdk/setup-runtime` |
| `plugin-sdk/setup-tools` | `formatCliCommand`、`detectBinary`、`extractArchive`、`resolveBrewExecutable`、`formatDocsLink`、`CONFIG_DIR` |
| `plugin-sdk/account-core` | 多账户配置/动作门控 helper、默认账户回退 helper |
| `plugin-sdk/account-id` | `DEFAULT_ACCOUNT_ID`、账户 id 规范化 helper |
| `plugin-sdk/account-resolution` | 账户查找 + 默认回退 helper |
| `plugin-sdk/account-helpers` | 窄账户列表/账户动作 helper |
| `plugin-sdk/access-groups` | 访问组允许列表解析和脱敏组诊断 helper |
| `plugin-sdk/channel-pairing` | `createChannelPairingController` |
| `plugin-sdk/channel-reply-pipeline` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/channel-config-helpers` | `createHybridChannelConfigAdapter`、`resolveChannelDmAccess`、`resolveChannelDmAllowFrom`、`resolveChannelDmPolicy`、`normalizeChannelDmPolicy`、`normalizeLegacyDmAliases` |
| `plugin-sdk/channel-config-schema` | 共享 channel 配置 schema 原语加 Zod 和直接 JSON/TypeBox 构建器 |
| `plugin-sdk/bundled-channel-config-schema` | 仅维护的捆绑插件的捆绑 OpenClaw channel 配置 schema |
| `plugin-sdk/chat-channel-ids` | `BUNDLED_CHAT_CHANNEL_IDS`、`BUNDLED_CHAT_CHANNEL_ENVELOPE_PREFIXES`、`ChatChannelId`。规范捆绑/官方聊天 channel id 加格式化标签/别名 |
| `plugin-sdk/channel-config-schema-legacy` | 捆绑 channel 配置 schema 的已弃用兼容别名 |
| `plugin-sdk/telegram-command-config` | Telegram 自定义命令规范化/验证 helper，带捆绑契约回退 |
| `plugin-sdk/command-gating` | 窄命令授权门控 helper |
| `plugin-sdk/channel-policy` | `resolveChannelGroupRequireMention` |
| `plugin-sdk/channel-ingress` | 已弃用底层 channel 入站兼容门面。新接收路径应用 `plugin-sdk/channel-ingress-runtime` |
| `plugin-sdk/channel-ingress-runtime` | 实验性高级 channel 入站运行时解析器和路由事实构建器，用于迁移的 channel 接收路径 |
| `plugin-sdk/channel-lifecycle` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/channel-outbound` | 消息生命周期契约加回复管道选项、回执、实时预览/流式、生命周期 helper、出站身份、负载规划、持久发送和消息发送上下文 helper |
| `plugin-sdk/channel-message` | `plugin-sdk/channel-outbound` 的已弃用兼容别名加遗留回复分发门面 |
| `plugin-sdk/channel-message-runtime` | `plugin-sdk/channel-outbound` 的已弃用兼容别名加遗留回复分发门面 |
| `plugin-sdk/inbound-envelope` | 共享入站路由 + 信封构建 helper |
| `plugin-sdk/inbound-reply-dispatch` | 已弃用兼容门面。入站运行器和分发谓词用 `plugin-sdk/channel-inbound`，消息投递 helper 用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/messaging-targets` | 已弃用目标解析别名；用 `plugin-sdk/channel-targets` |
| `plugin-sdk/outbound-media` | 共享出站媒体加载和托管媒体状态 helper |
| `plugin-sdk/outbound-send-deps` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/outbound-runtime` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/poll-runtime` | 窄投票规范化 helper |
| `plugin-sdk/thread-bindings-runtime` | 线程绑定生命周期和适配器 helper |
| `plugin-sdk/agent-media-payload` | 遗留 agent 媒体负载构建器 |
| `plugin-sdk/conversation-runtime` | 对话/线程绑定、配对和配置绑定 helper |
| `plugin-sdk/runtime-config-snapshot` | 运行时配置快照 helper |
| `plugin-sdk/runtime-group-policy` | 运行时组策略解析 helper |
| `plugin-sdk/channel-status` | 共享 channel 状态快照/摘要 helper |
| `plugin-sdk/channel-config-primitives` | 窄 channel 配置 schema 原语 |
| `plugin-sdk/channel-config-writes` | Channel 配置写入授权 helper |
| `plugin-sdk/channel-plugin-common` | 共享 channel 插件序曲导出 |
| `plugin-sdk/allowlist-config-edit` | 允许列表配置编辑/读取 helper |
| `plugin-sdk/group-access` | 共享组访问决策 helper |
| `plugin-sdk/direct-dm`、`plugin-sdk/direct-dm-access` | 已弃用兼容门面。用 `plugin-sdk/channel-inbound` |
| `plugin-sdk/direct-dm-guard-policy` | 窄直接 DM 预加密守卫策略 helper |
| `plugin-sdk/discord` | Discord 已弃用兼容门面，用于已发布的 `@openclaw/discord@2026.3.13` 和有追踪 owner 的兼容 |
| `plugin-sdk/telegram-account` | Telegram 账户解析已弃用兼容门面，用于有追踪 owner 的兼容 |
| `plugin-sdk/zalouser` | Zalo Personal 已弃用兼容门面，用于已发布的 Lark/Zalo 包 |
| `plugin-sdk/interactive-runtime` | 语义消息展示、投递和遗留交互回复 helper |
| `plugin-sdk/channel-inbound` | 共享入站 helper：事件分类、上下文构建、格式化、根、防抖、提及匹配、提及策略和入站日志 |
| `plugin-sdk/channel-inbound-debounce` | 窄入站防抖 helper |
| `plugin-sdk/channel-mention-gating` | 窄提及策略、提及标记和提及文本 helper，不含更广的入站运行时表面 |
| `plugin-sdk/channel-envelope`、`plugin-sdk/channel-inbound-roots`、`plugin-sdk/channel-location`、`plugin-sdk/channel-logging` | 已弃用兼容门面。用 `plugin-sdk/channel-inbound` 或 `plugin-sdk/channel-outbound` |
| `plugin-sdk/channel-pairing-paths` | 已弃用兼容门面。用 `plugin-sdk/channel-pairing` |
| `plugin-sdk/channel-reply-options-runtime` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/channel-streaming` | 已弃用兼容门面。用 `plugin-sdk/channel-outbound` |
| `plugin-sdk/channel-send-result` | 回复结果类型 |
| `plugin-sdk/channel-actions` | Channel 消息动作 helper，加为插件兼容保留的已弃用原生 schema helper |
| `plugin-sdk/channel-route` | 共享路由规范化、解析器驱动目标解析、线程 id 字符串化、去重/压缩路由键、解析目标类型和路由/目标比较 helper |
| `plugin-sdk/channel-targets` | 目标解析 helper；路由比较调用者应用 `plugin-sdk/channel-route` |
| `plugin-sdk/channel-contract` | Channel 契约类型 |
| `plugin-sdk/channel-feedback` | 反馈/反应接线 |
| `plugin-sdk/channel-secret-runtime` | 窄秘密契约 helper，如 `collectSimpleChannelFieldAssignments`、`getChannelSurface`、`pushAssignment` 和秘密目标类型 |

已弃用 channel helper 族仅在已发布插件兼容期间保持可用。移除计划：在外部插件迁移窗口期间保留，保持仓库/捆绑插件使用 `channel-inbound` 和 `channel-outbound`，然后在下一次大版本 SDK 清理中移除兼容子路径。这适用于旧的 channel message/runtime、channel streaming、direct-DM access、inbound helper splinter、reply-options 和 pairing-path 族。

**Provider 子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/provider-entry` | `defineSingleProviderPluginEntry` |
| `plugin-sdk/lmstudio` | 受支持的 LM Studio provider 门面，用于设置、目录发现和运行时模型准备 |
| `plugin-sdk/lmstudio-runtime` | 受支持的 LM Studio 运行时门面，用于本地服务器默认值、模型发现、请求头和已加载模型 helper |
| `plugin-sdk/provider-setup` | 精选本地/自托管 provider 设置 helper |
| `plugin-sdk/self-hosted-provider-setup` | 聚焦 OpenAI 兼容自托管 provider 设置 helper |
| `plugin-sdk/cli-backend` | CLI 后端默认值 + watchdog 常量 |
| `plugin-sdk/provider-auth-runtime` | provider 插件的运行时 API 密钥解析 helper |
| `plugin-sdk/provider-oauth-runtime` | 通用 provider OAuth 回调类型、回调页渲染、PKCE/state helper、授权输入解析、token 过期 helper 和中止 helper |
| `plugin-sdk/provider-auth-api-key` | API 密钥入门/档案写入 helper，如 `upsertApiKeyProfile` |
| `plugin-sdk/provider-auth-result` | 标准 OAuth auth 结果构建器 |
| `plugin-sdk/provider-env-vars` | Provider auth 环境变量查找 helper |
| `plugin-sdk/provider-auth` | `createProviderApiKeyAuthMethod`、`ensureApiKeyFromOptionEnvOrPrompt`、`upsertAuthProfile`、`upsertApiKeyProfile`、`writeOAuthCredentials`、OpenAI Codex auth 导入 helper |
| `plugin-sdk/provider-model-shared` | `ProviderReplayFamily`、`buildProviderReplayFamilyHooks`、`normalizeModelCompat`、共享重放策略构建器、provider 端点 helper 和共享模型 id 规范化 helper |
| `plugin-sdk/provider-catalog-runtime` | Provider 目录增强运行时钩子和插件 provider 注册表接缝，用于契约测试 |
| `plugin-sdk/provider-catalog-shared` | `findCatalogTemplate`、`buildSingleProviderApiKeyCatalog`、`buildManifestModelProviderConfig`、`supportsNativeStreamingUsageCompat`、`applyProviderNativeStreamingUsageCompat` |
| `plugin-sdk/provider-http` | 通用 provider HTTP/端点能力 helper、provider HTTP 错误和音频转录 multipart 表单 helper |
| `plugin-sdk/provider-web-fetch-contract` | 窄网页抓取配置/选择契约 helper，如 `enablePluginInConfig` 和 `WebFetchProviderPlugin` |
| `plugin-sdk/provider-web-fetch` | 网页抓取 provider 注册/缓存 helper |
| `plugin-sdk/provider-web-search-config-contract` | 窄网页搜索配置/凭证 helper，用于不需要插件启用接线的 provider |
| `plugin-sdk/provider-web-search-contract` | 窄网页搜索配置/凭证契约 helper，如 `createWebSearchProviderContractFields`、`enablePluginInConfig`、`resolveProviderWebSearchPluginConfig` 和有作用域凭证设置器/获取器 |
| `plugin-sdk/provider-web-search` | 网页搜索 provider 注册/缓存/运行时 helper |
| `plugin-sdk/embedding-providers` | 通用嵌入 provider 类型和读取 helper，包括 `EmbeddingProviderAdapter`、`getEmbeddingProvider(...)` 和 `listEmbeddingProviders(...)` |
| `plugin-sdk/provider-tools` | `ProviderToolCompatFamily`、`buildProviderToolCompatFamilyHooks` 和 DeepSeek/Gemini/OpenAI schema 清理 + 诊断 |
| `plugin-sdk/provider-usage` | Provider 用量快照类型、共享用量 fetch helper 和 provider 获取器如 `fetchClaudeUsage` |
| `plugin-sdk/provider-stream` | `ProviderStreamFamily`、`buildProviderStreamFamilyHooks`、`composeProviderStreamWrappers`、流包装器类型、纯文本工具调用兼容和共享 Anthropic/Bedrock/DeepSeek V4/Google/Kilocode/Moonshot/OpenAI/OpenRouter/Z.A.I/MiniMax/Copilot 包装器 helper |
| `plugin-sdk/provider-stream-shared` | 公开共享 provider 流包装器 helper，包括 `composeProviderStreamWrappers`、`createPlainTextToolCallCompatWrapper`、`createPayloadPatchStreamWrapper`、`createToolStreamWrapper` 和 Anthropic/DeepSeek/OpenAI 兼容流工具 |
| `plugin-sdk/provider-transport-runtime` | 原生 provider 传输 helper，如守卫 fetch、传输消息变换和可写传输事件流 |
| `plugin-sdk/provider-onboard` | 入门配置补丁 helper |
| `plugin-sdk/global-singleton` | 进程本地单例/映射/缓存 helper |
| `plugin-sdk/group-activation` | 窄组激活模式和命令解析 helper |

Provider 用量快照通常报告一个或多个配额 `windows`，每个有标签、已使用百分比和可选重置时间。暴露余额或账户状态文本而非可重置配额窗口的 provider 应返回带空 `windows` 数组的 `summary`，而不是捏造百分比。OpenClaw 在状态输出中显示该摘要文本；仅在用量端点失败或未返回可用用量数据时用 `error`。

**Auth 和安全子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/command-auth` | `resolveControlCommandGate`、命令注册表 helper（包括动态参数菜单格式化）、发送者授权 helper |
| `plugin-sdk/command-status` | 命令/帮助消息构建器，如 `buildCommandsMessagePaginated` 和 `buildHelpMessage` |
| `plugin-sdk/approval-runtime` | Exec/插件审批负载 helper、原生审批路由/运行时 helper 和结构化审批展示 helper |
| `plugin-sdk/security-runtime` | 共享信任、DM 门控、根有界文件/路径 helper，包括仅创建写入、同步/异步原子文件替换、同级临时写入、跨设备移动回退、私有文件存储 helper、符号链接父守卫、外部内容、敏感文本脱敏、常量时间秘密比较和秘密收集 helper |
| `plugin-sdk/ssrf-policy` | Host 允许列表和私有网络 SSRF 策略 helper |
| `plugin-sdk/ssrf-dispatcher` | 窄固定分发器 helper，不含广泛基础设施运行时表面 |
| `plugin-sdk/ssrf-runtime` | 固定分发器、SSRF 守卫 fetch、SSRF 错误和 SSRF 策略 helper |
| `plugin-sdk/webhook-ingress` | Webhook 请求/目标 helper 和原始 websocket/body 强制 |
| `plugin-sdk/webhook-request-guards` | 请求体大小/超时 helper |

**运行时和存储子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/runtime` | 广泛运行时/日志/备份/插件安装 helper |
| `plugin-sdk/runtime-env` | 窄运行时环境、logger、超时、重试和退避 helper |
| `plugin-sdk/runtime-store` | `createPluginRuntimeStore` |
| `plugin-sdk/config-contracts` | 聚焦仅类型配置表面，用于插件配置形状如 `OpenClawConfig` 和 channel/provider 配置类型 |
| `plugin-sdk/plugin-config-runtime` | 运行时插件配置查找 helper，如 `requireRuntimeConfig`、`resolvePluginConfigObject` 和 `resolveLivePluginConfigObject` |
| `plugin-sdk/config-mutation` | 事务配置变更 helper，如 `mutateConfigFile`、`replaceConfigFile` 和 `logConfigUpdated` |
| `plugin-sdk/runtime-config-snapshot` | 当前进程配置快照 helper，如 `getRuntimeConfig`、`getRuntimeConfigSnapshot` 和测试快照设置器 |
| `plugin-sdk/session-store-runtime` | 会话工作流 helper（`getSessionEntry`、`listSessionEntries`、`patchSessionEntry`、`upsertSessionEntry`）、遗留会话存储路径/会话键 helper |
| `plugin-sdk/routing` | 路由/会话键/账户绑定 helper，如 `resolveAgentRoute`、`buildAgentSessionKey` 和 `resolveDefaultAgentBoundAccountId` |
| `plugin-sdk/tool-plugin` | 定义简单类型化 agent 工具插件并暴露静态元数据用于 manifest 生成 |
| `plugin-sdk/gateway-runtime` | Gateway 客户端、事件循环就绪客户端启动 helper、gateway CLI RPC、gateway 协议错误和 channel 状态补丁 helper |
| `plugin-sdk/agent-harness` | 实验性受信插件表面，用于底层 agent harness：harness 类型、活跃运行引导/中止 helper、工具桥 helper、运行时计划工具策略 helper、终端 outcome 分类 |

**能力和测试子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/media-runtime` | 共享媒体获取/变换/存储 helper，包括 `saveRemoteMedia`、`saveResponseMedia`、`readRemoteMediaBuffer` |
| `plugin-sdk/media-mime` | 窄 MIME 规范化、文件扩展名映射、MIME 检测和媒体种类 helper |
| `plugin-sdk/speech` | 语音 provider 类型加 provider 指令、注册表、验证、OpenAI 兼容 TTS 构建器和语音 helper 导出 |
| `plugin-sdk/image-generation` | 图片生成 provider 类型加图片资产/数据 URL helper 和 OpenAI 兼容图片 provider 构建器 |
| `plugin-sdk/video-generation` | 视频生成 provider/请求/结果类型 |
| `plugin-sdk/music-generation` | 音乐生成 provider/请求/结果类型 |

**记忆子路径**

| 子路径 | 关键导出 |
| --- | --- |
| `plugin-sdk/memory-core` | 捆绑记忆核心 helper 表面，用于管理器/配置/文件/CLI helper |
| `plugin-sdk/memory-host-core` | 记忆中性的记忆 host 核心运行时 helper 别名 |
| `plugin-sdk/memory-host-search` | 活跃记忆运行时门面，用于搜索管理器访问 |
| `plugin-sdk/memory-core-host-embedding-registry` | 轻量级记忆嵌入 provider 注册表 helper |
| `plugin-sdk/memory-core-host-engine-embeddings` | 记忆 host 嵌入契约、注册表访问、本地 provider 和通用批量/远程 helper |

**保留的捆绑 helper 子路径**

保留的捆绑 helper SDK 子路径是捆绑插件代码的窄 owner 专用表面。它们在 SDK 清单中追踪，让包构建和别名保持确定性，但不是通用插件编写 API。新的可复用 host 应用通用 SDK 子路径如 `plugin-sdk/gateway-runtime`、`plugin-sdk/security-runtime` 和 `plugin-sdk/plugin-config-runtime`。

| 子路径 | Owner 和用途 |
| --- | --- |
| `plugin-sdk/codex-mcp-projection` | 捆绑 Codex 插件 helper，用于将用户 MCP 服务器配置投影到 Codex app-server 线程配置 |
| `plugin-sdk/codex-native-task-runtime` | 捆绑 Codex 插件 helper，用于将 Codex app-server 原生子 agent 镜像到 OpenClaw 任务状态 |

## 相关

- [Plugin SDK overview](/plugins/sdk-overview)
- [Plugin SDK setup](/plugins/sdk-setup)
- [Building plugins](/plugins/building-plugins)
