# Memory Wiki 插件

## 架构精读

> 跳过不影响阅读翻译正文。

### 记忆插件已经够了，为什么还要加一层 Wiki？

`memory-core` 或 QMD 这类活跃记忆插件管的是"召回"——对话中快速找到相关片段。但它们输出的是一堆 Markdown 笔记，没有结构，没有置信度，也没有"这两条记忆矛盾了"的告警。时间一长，笔记越积越多，越找越乱。

`memory-wiki` 不替代记忆插件。它坐在记忆旁边，把零散笔记编译成有结构的 Wiki 页面。每个页面有类型（实体/概念/综合/来源），每个事实有置信度和证据链，系统自动检测矛盾和过期内容。就像把散乱的工作笔记整理成维护良好的内部文档站。

第二个关键设计：结构化断言。页面不只是 prose，还能挂 `claims` frontmatter——每条断言有 `status`、`confidence`、`evidence[]` 指向源页面。这让 Wiki 从"被动笔记堆"变成"信念层"。你可以查询"关于 X 系统我们知道什么、有多确定、证据在哪"。科学论文的每个结论都附引用，Wiki 的每条断言也附证据。

第三个边界：编译管道。Wiki 页面编译成 `agent-digest.json` 和 `claims.jsonl`，供 agent 直接消费结构化数据，而不是让 agent 去解析 Markdown。这就像前端构建——源码是 Markdown，产物是 JSON，运行时只读产物。

---

`memory-wiki` 是捆绑插件，把持久记忆编译成结构化知识库。

它**不**替代活跃记忆插件。活跃记忆插件仍负责召回、晋升、索引和做梦。`memory-wiki` 坐在旁边，把持久知识编译成可导航的 Wiki，具备确定性页面、结构化断言、溯源、仪表盘和机器可读摘要。

想让记忆更像维护良好的知识层而非一堆 Markdown 文件时使用。

## 新增能力

- 专用 Wiki 库，确定性页面布局
- 结构化断言和证据元数据，不只是 prose
- 页面级溯源、置信度、矛盾和待解决问题
- 供 agent/运行时消费的编译摘要
- Wiki 原生 search/get/apply/lint 工具
- 可选 bridge 模式，从活跃记忆插件导入公共产物
- 可选 Obsidian 友好渲染和 CLI 集成

## 与记忆的分工

| 层                                              | 职责                                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| 活跃记忆插件（`memory-core`、QMD、Honcho 等）   | 召回、语义搜索、晋升、做梦、记忆运行时                       |
| `memory-wiki`                                   | 编译 Wiki 页面、溯源丰富的综合、仪表盘、Wiki 专用 search/get/apply |

若活跃记忆插件暴露共享召回产物，OpenClaw 可用 `memory_search corpus=all` 一次搜索两层。

需要 Wiki 专用排序、溯源或直接页面访问时，改用 Wiki 原生工具。

## 推荐的混合模式

本地优先架构的强默认配置：

- QMD 做活跃记忆后端，负责召回和广域语义搜索
- `memory-wiki` 用 `bridge` 模式，负责持久综合知识页面

这个分工有效是因为每层保持专注：

- QMD 保留原始笔记、会话导出和额外集合的可搜索性
- `memory-wiki` 编译稳定实体、断言、仪表盘和来源页面

实用原则：

- 想做一次广域召回时用 `memory_search`
- 关心溯源时用 `wiki_search` 和 `wiki_get`
- 想让共享搜索覆盖两层时用 `memory_search corpus=all`

若 bridge 模式报告零导出产物，说明活跃记忆插件尚未暴露公共 bridge 输入。先跑 `openclaw wiki doctor`，再确认活跃记忆插件是否支持公共产物。

Bridge 模式启用且 `bridge.readMemoryArtifacts` 开启时，`openclaw wiki status`、`openclaw wiki doctor` 和 `openclaw wiki bridge import` 通过运行中的 Gateway 读取。这保证 CLI bridge 检查与运行时记忆插件上下文一致。Bridge 禁用或产物读取关闭时，这些命令保持本地/离线行为。

## Vault 模式

`memory-wiki` 支持三种 vault 模式：

### `isolated`

独立 vault，独立来源，不依赖 `memory-core`。

想让 Wiki 作为独立策划的知识库时使用。

### `bridge`

通过公共插件 SDK 接缝读取活跃记忆插件的公共记忆产物和记忆事件。

想让 Wiki 编译和组织记忆插件导出的产物，而不深入插件私有内部时使用。

Bridge 模式可索引：

- 导出的记忆产物
- 做梦报告
- 每日笔记
- 记忆根目录文件
- 记忆事件日志

### `unsafe-local`

显式的本机逃逸，用于本地私有路径。

此模式故意保持实验性和非可移植性。仅在理解信任边界且 bridge 模式无法满足时使用。

## Vault 布局

插件初始化 vault 如下：

```text
<vault>/
  AGENTS.md
  WIKI.md
  index.md
  inbox.md
  entities/
  concepts/
  syntheses/
  sources/
  reports/
  _attachments/
  _views/
  .openclaw-wiki/
```

托管内容在生成块内。人类笔记块被保留。

主要页面组：

- `sources/` 存放导入的原始材料和 bridge 支持的页面
- `entities/` 存放持久事物、人、系统、项目和对象
- `concepts/` 存放想法、抽象、模式和策略
- `syntheses/` 存放编译摘要和维护的汇总
- `reports/` 存放生成的仪表盘

## 结构化断言和证据

页面可携带结构化 `claims` frontmatter，不只是自由文本。

每条断言可包含：

- `id`
- `text`
- `status`
- `confidence`
- `evidence[]`
- `updatedAt`

evidence 条目可包含：

- `kind`
- `sourceId`
- `path`
- `lines`
- `weight`
- `confidence`
- `privacyTier`
- `note`
- `updatedAt`

这让 Wiki 更像信念层而非被动笔记堆。断言可被追踪、打分、争议，并回溯到来源。

## Agent 面向的实体元数据

实体页面还可携带路由元数据供 agent 使用。这是通用 frontmatter，适用于人、团队、系统、项目或任何实体类型。

常见字段：

- `entityType`：如 `person`、`team`、`system`、`project`
- `canonicalId`：跨别名和导入的稳定身份键
- `aliases`：应解析到同一页面的名称、句柄或标签
- `privacyTier`：`public`、`local-private`、`sensitive`、`confirm-before-use`
- `bestUsedFor` / `notEnoughFor`：紧凑路由提示
- `lastRefreshedAt`：来源刷新时间戳，区别于页面编辑时间
- `personCard`：可选的人员路由卡，含句柄、社交、邮箱、时区、方向、可问/避免问、置信度和隐私
- `relationships`：与相关页面的类型化边，含目标、类型、权重、置信度、证据类型、隐私层和备注

人员 Wiki 的 agent 通常先读 `reports/person-agent-directory.md`，再用 `wiki_get` 打开人员页面，然后使用联系方式或推断事实。

示例：

```yaml
pageType: entity
entityType: person
id: entity.brad-groux
canonicalId: maintainer.brad-groux
aliases:
  - Brad
  - bgroux
privacyTier: local-private
bestUsedFor:
  - Microsoft Teams 和 Azure 路由
notEnoughFor:
  - 法律审批
lastRefreshedAt: "2026-04-29T00:00:00.000Z"
personCard:
  handles:
    - "@bgroux"
  socials:
    - "https://x.example/bgroux"
  emails:
    - brad@example.com
  timezone: America/Chicago
  lane: Microsoft 生态
  askFor:
    - Teams 上线问题
  avoidAskingFor:
    - 无关的账单决策
  confidence: 0.8
  privacyTier: confirm-before-use
relationships:
  - targetId: entity.alice
    targetTitle: Alice
    kind: collaborates-with
    confidence: 0.7
    evidenceKind: discrawl-stat
claims:
  - id: claim.brad.teams
    text: Brad 适用于 Microsoft Teams 路由。
    status: supported
    confidence: 0.9
    evidence:
      - kind: maintainer-whois
        sourceId: source.maintainers
        privacyTier: local-private
```

## 编译管道

编译步骤读取 Wiki 页面，规范化摘要，并在以下路径生成稳定的机器产物：

- `.openclaw-wiki/cache/agent-digest.json`
- `.openclaw-wiki/cache/claims.jsonl`

这些摘要让 agent 和运行时代码不必解析 Markdown 页面。

编译产物还支持：

- Wiki 索引的搜索/get 流第一轮
- 断言 id 回溯到所属页面
- 紧凑 prompt 补充
- 报告/仪表盘生成

## 仪表盘和健康报告

`render.createDashboards` 启用时，编译在 `reports/` 下维护仪表盘。

内置报告包括：

- `reports/open-questions.md`
- `reports/contradictions.md`
- `reports/low-confidence.md`
- `reports/claim-health.md`
- `reports/stale-pages.md`
- `reports/person-agent-directory.md`
- `reports/relationship-graph.md`
- `reports/provenance-coverage.md`
- `reports/privacy-review.md`

这些报告追踪：

- 矛盾笔记簇
- 竞争断言簇
- 缺少结构化证据的断言
- 低置信度页面和断言
- 过期或未知的刷新状态
- 有未解决问题的页面
- 人员/实体路由卡
- 结构化关系边
- 证据类别覆盖率
- 使用前需审查的非公开隐私层

## 搜索和检索

`memory-wiki` 支持两种搜索后端：

- `shared`：可用时使用共享记忆搜索流
- `local`：本地搜索 Wiki

还支持三种语料库：

- `wiki`
- `memory`
- `all`

重要行为：

- `wiki_search` 和 `wiki_get` 优先用编译摘要做第一轮
- 断言 id 可回溯到所属页面
- 争议/过期/新鲜断言影响排序
- 溯源标签可传递到结果
- 搜索模式可偏向人员查找、问题路由、来源证据或原始断言

实用原则：

- 一次广域召回用 `memory_search corpus=all`
- 关心 Wiki 专用排序、溯源或页面级信念结构时用 `wiki_search` + `wiki_get`

搜索模式：

- `auto`：均衡默认
- `find-person`：偏向类人实体、别名、句柄、社交和 canonical ID
- `route-question`：偏向 agent 卡、ask-for 提示、best-used-for 提示和关系上下文
- `source-evidence`：偏向来源页面和结构化证据元数据
- `raw-claim`：偏向匹配的结构化断言，在结果中返回断言/证据元数据

当结果匹配结构化断言时，`wiki_search` 可在详情负载中返回 `matchedClaimId`、`matchedClaimStatus`、`matchedClaimConfidence`、`evidenceKinds` 和 `evidenceSourceIds`。文本输出在可用时也包含紧凑的 `Claim:` 和 `Evidence:` 行。

## Agent 工具

插件注册以下工具：

- `wiki_status`
- `wiki_search`
- `wiki_get`
- `wiki_apply`
- `wiki_lint`

功能：

- `wiki_status`：当前 vault 模式、健康状态、Obsidian CLI 可用性
- `wiki_search`：搜索 Wiki 页面，配置后也可搜索共享记忆语料；接受 `mode` 参数用于人员查找、问题路由、来源证据或原始断言下钻
- `wiki_get`：按 id/路径读取 Wiki 页面，或回退到共享记忆语料
- `wiki_apply`：窄范围综合/元数据变更，不做自由格式页面手术
- `wiki_lint`：结构检查、溯源缺口、矛盾、待解决问题

插件还注册非排他记忆语料补充，共享 `memory_search` 和 `memory_get` 在活跃记忆插件支持语料选择时可访问 Wiki。

## Prompt 和上下文行为

`context.includeCompiledDigestPrompt` 启用时，记忆 prompt 段追加来自 `agent-digest.json` 的紧凑编译快照。

该快照刻意保持小而高信号：

- 仅顶级页面
- 仅顶级断言
- 矛盾计数
- 问题计数
- 置信度/新鲜度限定符

这是 opt-in 的，因为它改变 prompt 形状，主要用于明确消费记忆补充的上下文引擎或遗留 prompt 装配。

## 配置

配置放在 `plugins.entries.memory-wiki.config` 下：

```json5
{
  plugins: {
    entries: {
      "memory-wiki": {
        enabled: true,
        config: {
          vaultMode: "isolated",
          vault: {
            path: "~/.openclaw/wiki/main",
            renderMode: "obsidian",
          },
          obsidian: {
            enabled: true,
            useOfficialCli: true,
            vaultName: "OpenClaw Wiki",
            openAfterWrites: false,
          },
          bridge: {
            enabled: false,
            readMemoryArtifacts: true,
            indexDreamReports: true,
            indexDailyNotes: true,
            indexMemoryRoot: true,
            followMemoryEvents: true,
          },
          ingest: {
            autoCompile: true,
            maxConcurrentJobs: 1,
            allowUrlIngest: true,
          },
          search: {
            backend: "shared",
            corpus: "wiki",
          },
          context: {
            includeCompiledDigestPrompt: false,
          },
          render: {
            preserveHumanBlocks: true,
            createBacklinks: true,
            createDashboards: true,
          },
        },
      },
    },
  },
}
```

关键开关：

- `vaultMode`：`isolated`、`bridge`、`unsafe-local`
- `vault.renderMode`：`native` 或 `obsidian`
- `bridge.readMemoryArtifacts`：导入活跃记忆插件公共产物
- `bridge.followMemoryEvents`：bridge 模式中包含事件日志
- `search.backend`：`shared` 或 `local`
- `search.corpus`：`wiki`、`memory`、`all`
- `context.includeCompiledDigestPrompt`：向记忆 prompt 段追加紧凑摘要快照
- `render.createBacklinks`：生成确定性相关块
- `render.createDashboards`：生成仪表盘页面

### 示例：QMD + bridge 模式

QMD 负责召回、`memory-wiki` 负责维护知识层时使用：

```json5
{
  memory: {
    backend: "qmd",
  },
  plugins: {
    entries: {
      "memory-wiki": {
        enabled: true,
        config: {
          vaultMode: "bridge",
          bridge: {
            enabled: true,
            readMemoryArtifacts: true,
            indexDreamReports: true,
            indexDailyNotes: true,
            indexMemoryRoot: true,
            followMemoryEvents: true,
          },
          search: {
            backend: "shared",
            corpus: "all",
          },
          context: {
            includeCompiledDigestPrompt: false,
          },
        },
      },
    },
  },
}
```

这保持了：

- QMD 掌管活跃记忆召回
- `memory-wiki` 专注编译页面和仪表盘
- 除非故意启用编译摘要 prompt，否则 prompt 形状不变

## CLI

`memory-wiki` 还暴露顶层 CLI 界面：

```bash
openclaw wiki status
openclaw wiki doctor
openclaw wiki init
openclaw wiki ingest ./notes/alpha.md
openclaw wiki compile
openclaw wiki lint
openclaw wiki search "alpha"
openclaw wiki get entity.alpha
openclaw wiki apply synthesis "Alpha Summary" --body "..." --source-id source.alpha
openclaw wiki bridge import
openclaw wiki obsidian status
```

完整命令参考见 [CLI: wiki](/cli/wiki)。

## Obsidian 支持

`vault.renderMode` 为 `obsidian` 时，插件写 Obsidian 友好的 Markdown，并可选使用官方 `obsidian` CLI。

支持的工作流包括：

- 状态探测
- Vault 搜索
- 打开页面
- 调用 Obsidian 命令
- 跳转到每日笔记

这是可选的。Wiki 在 native 模式下不依赖 Obsidian 也能工作。

## 推荐工作流

1. 保留活跃记忆插件负责召回/晋升/做梦。
2. 启用 `memory-wiki`。
3. 除非明确需要 bridge 模式，否则从 `isolated` 开始。
4. 关心溯源时用 `wiki_search` / `wiki_get`。
5. 做窄范围综合或元数据更新时用 `wiki_apply`。
6. 有意义的变更后跑 `wiki_lint`。
7. 想要过期/矛盾可见性时开启仪表盘。

## 相关文档

- [Memory 概述](/concepts/memory)
- [CLI: memory](/cli/memory)
- [CLI: wiki](/cli/wiki)
- [Plugin SDK 概述](/plugins/sdk-overview)
