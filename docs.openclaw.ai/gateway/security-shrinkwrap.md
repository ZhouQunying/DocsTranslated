# Shrinkwrap——依赖版本锁定

## 架构精读

> 跳过不影响阅读翻译正文。

### 双锁定文件策略——为什么开发和发布用不同格式？

OpenClaw 开发时用 `pnpm-lock.yaml`（pnpm 友好、快、monorepo 支持），发布时转换成 `npm-shrinkwrap.json`（npm 能识别）。这跟 TypeScript 开发 + JavaScript 发布是一个思路——开发时用高级语言，发布时编译成用户工具链能识别的格式。

`package-lock.json` 不会被发布到 npm（被 `.npmignore` 忽略），`npm-shrinkwrap.json` 即使被 `.npmignore` 忽略也会发布。这保证了用户安装时能读取锁定的版本。

### 供应链安全——为什么锁定版本能防攻击？

依赖升级可能引入缺陷或恶意代码。锁定文件锁定确切版本，任何时候安装都相同，不自动升级。这跟 Docker image digest 是一个思路——`node@sha256:abc123` 总是相同的 image，不会因为 `node:latest` 更新而改变。

审计人员可以追踪间接模块变化，自动化检查可以阻止未授权的文件修改，QA 团队可以验证跟用户收到的一模一样的结构。

### 什么时候更新 shrinkwrap？

锁定文件手动更新：依赖升级时、安全补丁时、发布新版本时。手动更新 + 测试 = 更可控，不自动升级。这跟 Kubernetes image 策略是一个思路——`IfNotPresent`（本地没有才拉取）比 `Always`（总是拉取）更安全。

---

### 概述 / Overview

Developers working directly with the repository rely on pnpm lockfiles. However, distributed builds utilize a different mechanism to ensure consumers receive the exact vetted dependency tree approved by maintainers.

直接开发仓库的开发者依赖 pnpm lockfile。但发布构建使用不同机制，确保用户收到维护者审核过的精确依赖树。

### 简化说明 / Simplified Explanation

Think of this file as a detailed manifest accompanying distributed modules. It instructs the package manager to fetch precise sub-dependency iterations.

把这个文件当成发布模块的清单，指示包管理器获取精确的子依赖版本。

For distributed releases, this implies:

- Prevents the package manager from dynamically generating new trees during setup.
- Simplifies code reviews by capturing modifications in a dedicated tracking file.
- Enables quality assurance to evaluate the identical structure end-users receive.
- Helps identify unexpected binary or storage expansions prior to distribution.

对发布版本的意义：

- 防止包管理器在安装时动态生成新的依赖树。
- 简化代码审查——修改记录在专用追踪文件中。
- QA 团队可以评估跟终端用户收到的一模一样的结构。
- 发布前发现意外的二进制或存储膨胀。

This mechanism lacks sandboxing capabilities. It cannot independently guarantee safety, nor does it substitute for environment separation, the `openclaw security audit` tool, origin verification, or preliminary execution checks.

这不是沙箱机制，不能独立保证安全，也不能替代环境隔离、`openclaw security audit`、来源验证或预执行检查。

The core concept:

| Document | Primary Context | Purpose |
|---|---|---|
| `pnpm-lock.yaml` | Repository cloning | Tracks the core team's module structure |
| `npm-shrinkwrap.json` | Distributed modules | Dictates the consumer installation layout |
| `package-lock.json` | Personal projects | Irrelevant to official distribution agreements |

核心概念：

| 文件 | 主要场景 | 用途 |
|---|---|---|
| `pnpm-lock.yaml` | 仓库克隆 | 追踪核心团队的模块结构 |
| `npm-shrinkwrap.json` | 发布模块 | 指定用户安装时的依赖布局 |
| `package-lock.json` | 个人项目 | 与官方发布无关 |

### 采用理由 / Rationale for Adoption

Because the platform functions as a multifaceted runtime and routing hub, standard setups significantly influence boot speeds, storage consumption, binary fetching, and third-party risks.

作为多功能运行时和路由中心，标准配置显著影响启动速度、存储消耗、二进制获取和第三方风险。

Locking versions provides a firm perimeter for evaluating updates:

- Auditors can track indirect module shifts.
- Automated checks can block unauthorized file alterations.
- Quality teams can verify the exact layout destined for production.
- Extensions can encapsulate their own locked requirements rather than depending on the core application.

锁定版本为评估更新提供明确边界：

- 审计人员可以追踪间接模块变化。
- 自动化检查可以阻止未授权的文件修改。
- QA 团队可以验证跟生产环境一模一样的布局。
- 扩展可以封装自己的锁定依赖，不依赖核心应用。

The objective is not creating "more lockfiles" but achieving consistent deployments with defined accountability.

目标不是"更多 lockfile"，而是实现一致的部署和明确的责任归属。

### 实现细节 / Implementation Specifics

Core distributions and official extensions embed the specialized JSON file during deployment. Certain extensions also utilize explicit bundling configurations, embedding runtime modules directly inside the archive to bypass dynamic resolution.

核心发行版和官方扩展在发布时嵌入专用 JSON 文件。部分扩展还使用显式打包配置，直接把运行时模块嵌入归档中跳过动态解析。

Maintain this separation via:

通过以下命令维护分离：

```bash
pnpm deps:shrinkwrap:generate
pnpm deps:shrinkwrap:check
```

The creation script outputs the correct format while blocking any iterations absent from the primary pnpm tracker. This preserves existing rules regarding module age, custom overrides, and modification reviews.

创建脚本输出正确格式，同时阻止主 pnpm tracker 中不存在的版本。保留现有的模块版本、自定义覆盖和修改审查规则。

Execute core-specific scripts exclusively when updating the main application independently of extensions:

独立更新主应用（不含扩展）时使用专用脚本：

```bash
pnpm deps:shrinkwrap:root:generate
pnpm deps:shrinkwrap:root:check
```

Treat the following artifacts as critical security components:

以下制品视为关键安全组件：

- The primary pnpm tracker
- The distributed JSON manifest
- Bundled extension payloads
- Any modifications to standard package locks

- 主 pnpm tracker
- 发布的 JSON manifest
- 打包的扩展内容
- 对标准 package lock 的任何修改

Validation tools mandate the specialized manifest for fresh core archives. Extension deployment pipelines verify local manifests, set up bundled modules, and finalize distribution. Standard lockfiles are strictly prohibited in official releases.

验证工具要求新核心归档必须包含专用 manifest。扩展发布管线验证本地 manifest、设置打包模块、完成发布。官方发布严格禁止标准 lockfile。

Examine a distributed core archive using these commands:

检查发布的核心归档：

```bash
npm pack openclaw@<version> --json --pack-destination /tmp/openclaw-pack
tar -tf /tmp/openclaw-pack/openclaw-<version>.tgz | grep '^package/npm-shrinkwrap.json$'
```

Examine an official extension archive with these instructions:

检查官方扩展归档：

```bash
npm pack @openclaw/discord@<version> --json --pack-destination /tmp/openclaw-plugin-pack
tar -tf /tmp/openclaw-plugin-pack/openclaw-discord-<version>.tgz | grep '^package/npm-shrinkwrap.json$'
tar -tf /tmp/openclaw-plugin-pack/openclaw-discord-<version>.tgz | grep '^package/node_modules/'
```

For further context, consult the official documentation regarding this specific JSON configuration.

更多信息参考官方关于此 JSON 配置的文档。
