# 依赖解析

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 Gateway 启动时不自动修复依赖？

启动时发现缺依赖就 `npm install` 听起来方便，但会让启动时间不可预测，可能在生产中触发网络请求，还可能引入未经测试的依赖版本。OpenClaw 把依赖工作放在安装/更新时做：安装时解决所有依赖，运行时只加载。缺依赖就报错并给出修复命令。就像容器镜像——构建时解决所有依赖，运行时不再安装。好处是启动快速可预测，坏处是更新后需要显式重新安装。

---

OpenClaw 将插件依赖工作保持在安装/更新时。运行时加载不运行包管理器、不修复依赖树、不变更 OpenClaw 包目录。

## 职责划分

插件包持有其依赖图：

- 运行时依赖在插件包 `dependencies` 或 `optionalDependencies` 中
- SDK/核心导入是 peer 或提供的 OpenClaw 导入
- 本地开发插件自带已安装的依赖
- npm 和 git 插件安装到 OpenClaw 持有的包根

OpenClaw 仅持有插件生命周期：

- 发现插件源
- 显式请求时安装或更新包
- 记录安装元数据
- 加载插件入口点
- 依赖缺失时给出可操作的错误

## 安装根

OpenClaw 使用稳定的每源根：

- npm 包安装到 `~/.openclaw/npm/projects/<encoded-package>` 下的每插件项目
- git 包克隆到 `~/.openclaw/git` 下
- 本地/路径/归档安装被复制或引用，不做依赖修复

npm 安装在该每插件项目根中运行：

```bash
cd ~/.openclaw/npm/projects/<encoded-package>
npm install --omit=dev --omit=peer --legacy-peer-deps --ignore-scripts --no-audit --no-fund
```

`openclaw plugins install npm-pack:<path.tgz>` 对本地 npm 打包 tarball 使用相同的每插件 npm 项目根。OpenClaw 读取 tarball 的 npm 元数据，将其作为复制的 `file:` 依赖添加到托管项目，运行正常 npm 安装，然后在信任插件前验证已安装的 lockfile 元数据。这用于包接受和发布候选验证，本地打包产物应表现得像它模拟的注册表产物。

npm 可能将传递依赖提升到每插件项目的 `node_modules`（在插件包旁边）。OpenClaw 在信任安装前扫描托管项目根，卸载时移除该项目，所以提升的运行时依赖保持在该插件的清理边界内。

已发布的 npm 插件包可附带 `npm-shrinkwrap.json`。npm 在安装期间使用该可发布的 lockfile，OpenClaw 的托管 npm 项目根通过正常 npm 安装路径支持它。OpenClaw 持有的可发布插件包必须包含从该插件包已发布的依赖图生成的包本地 shrinkwrap：

```bash
pnpm deps:shrinkwrap:generate
pnpm deps:shrinkwrap:check
```

生成器剥离插件 `devDependencies`，应用工作区覆盖策略，为每个 `publishToNpm` 插件写入 `extensions/<id>/npm-shrinkwrap.json`。第三方插件包也可附带 shrinkwrap；OpenClaw 不要求社区包这样做，但 npm 在存在时会遵守它。

OpenClaw 持有的 npm 插件包也可用显式 `bundledDependencies` 发布。npm 发布路径覆盖运行时依赖名列表，从已发布的包 manifest 移除仅开发的元数据。然后为包本地运行时依赖运行无脚本 npm 安装，将这些依赖文件打包或发布到插件 tarball 中。原生重量级包（包括 Codex 和 ACP 运行时）用 `openclaw.release.bundleRuntimeDependencies: false` 选择退出。这些包仍附带 shrinkwrap，但 npm 在安装期间解析运行时依赖，而不是将每个平台二进制嵌入插件 tarball。根 `openclaw` 包不捆绑其完整依赖树。

导入 `openclaw/plugin-sdk/*` 的插件声明 `openclaw` 为 peer 依赖。OpenClaw 不让 npm 将主包的单独注册表副本安装到托管项目中，因为过期的主包可能影响该插件内的 npm peer 解析。托管 npm 安装跳过 npm peer 解析/物化，OpenClaw 在安装或更新后为声明主包 peer 的已安装包重新断言插件本地 `node_modules/openclaw` 链接。

git 安装克隆或刷新仓库，然后运行：

```bash
npm install --omit=dev --ignore-scripts --no-audit --no-fund
```

已安装的插件然后从该包目录加载，所以包本地和父 `node_modules` 解析的工作方式与正常 Node 包相同。

## 本地插件

本地插件被视为开发者控制的目录。OpenClaw 不为它们运行 `npm install`、`pnpm install` 或依赖修复。如果本地插件有依赖，在加载前在该插件中安装它们。

第三方 TypeScript 本地插件可使用紧急 Jiti 路径。打包的 JavaScript 插件和捆绑内部插件通过原生 import/require 加载，而不是 Jiti。

## 启动和重载

Gateway 启动和配置重载永不安装插件依赖。它们读取插件安装记录，计算入口点并加载。

如果运行时依赖缺失，插件加载失败，错误应指向 operator 给出显式修复：

```bash
openclaw plugins update <id>
openclaw plugins install <source>
openclaw doctor --fix
```

`doctor --fix` 可清理遗留的 OpenClaw 生成的依赖状态，恢复配置引用但本地安装记录中缺失的可下载插件。Doctor 不为已安装的本地插件修复依赖。

## 捆绑插件

轻量级和核心关键捆绑插件作为 OpenClaw 的一部分发布。它们应没有重型运行时依赖树，或移到 ClawHub/npm 上的可下载包。

当前在核心包中发布、外部安装或仅保持源码的插件生成列表见[插件清单](/plugins/plugin-inventory)。

捆绑插件 manifest 不得请求依赖暂存。大型或可选插件功能应打包为正常插件，通过与第三方插件相同的 npm/git/ClawHub 路径安装。

源码检出中，OpenClaw 将仓库视为 pnpm monorepo。`pnpm install` 后，捆绑插件从 `extensions/<id>` 加载，所以包本地工作区依赖可用，编辑直接被拾取。源码检出开发仅限 pnpm；仓库根的普通 `npm install` 不是准备捆绑插件依赖的支持方式。

| 安装形态                         | 捆绑插件位置                   | 依赖 owner                                                           |
| -------------------------------- | ------------------------------ | -------------------------------------------------------------------- |
| `npm install -g openclaw`        | 包内的已构建运行时树           | OpenClaw 包和显式插件安装/更新/doctor 流程                           |
| Git 检出加 `pnpm install`        | `extensions/<id>` 工作区包     | pnpm 工作区，包括每个插件包自己的依赖                                |
| `openclaw plugins install ...`   | 托管 npm 项目/git/ClawHub 根   | 插件安装/更新流程                                                    |

## 遗留清理

旧版 OpenClaw 在启动或 doctor 修复期间生成捆绑插件依赖根。当前 doctor 清理在使用 `--fix` 时移除那些过期目录和符号链接。包括旧的 `plugin-runtime-deps` 根、指向已修剪目标的全局包符号链接、`.openclaw-runtime-deps*` manifest、生成的插件 `node_modules`、安装阶段目录和包本地 pnpm 存储。打包的 postinstall 也在修剪遗留目标根前移除那些全局符号链接。这样升级不会留下悬挂的 ESM 包导入。

旧版 npm 安装也使用共享的 `~/.openclaw/npm/node_modules` 根。当前安装、更新、卸载和 doctor 流程仅在恢复和清理时识别该遗留扁平根。新 npm 安装应创建每插件项目根。
