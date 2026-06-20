# macOS dev setup

## 架构精读

> 跳过不影响阅读翻译正文。

### Xcode 26.2+ 和 Node 24——为什么版本要求这么高

OpenClaw macOS app 要求 Xcode 26.2+ 和 Node 24，这不是随意选的。Xcode 26.2 引入了新的 Swift concurrency 特性和 macOS SDK，app 代码依赖这些新 API。Node 24 是 LTS，提供了稳定的 native addon ABI。

这跟 React Native 的版本要求是一个思路。React Native 要求特定版本的 Xcode 和 Android Studio，因为 native module 编译依赖特定 SDK。OpenClaw 也是这样：Swift 代码依赖新 Xcode，Node 部分依赖 LTS。版本要求不是"建议"，而是"必须"——低了编译不过。

### pnpm workspace——monorepo 的标准选择

项目用 pnpm workspace 管理 monorepo，app 和 CLI 共享依赖。这跟 Turborepo/Nx 的 monorepo 是一个思路——多个 package 共享 node_modules，pnpm 的 symlink 策略避免了依赖重复和版本冲突。

OpenClaw 的 workspace 结构是 app（Swift + Node bridge）和 CLI（纯 Node）共享 common package。pnpm 的 workspace 让 `pnpm install` 一次装好所有依赖，`pnpm --filter` 可以单独构建某个 package。

### Install CLI from source——dev 模式的逃生口

文档提供了 `pnpm build && pnpm install:cli` 从源码安装 CLI 的方式。这跟 Homebrew 的 `--HEAD` 是一个思路——production 用稳定版本，dev 用最新源码。OpenClaw 的 dev setup 也是这样：production 用户 `npm install -g openclaw`，开发者从源码安装以调试最新特性。

### Troubleshooting 的常见坑——codesign 和 launchagent

文档列出了两个常见坑：
1. **Codesign 失败**——unsigned build 不能加载 LaunchAgent
2. **LaunchAgent 冲突**——`~/.openclaw/disable-launchagent` 标记阻止 launchd 启动

这跟 Docker Desktop 的 troubleshooting 是一个思路。Docker Desktop 常见问题也是 VM 启动失败、权限不足、端口冲突。OpenClaw 的 troubleshooting 聚焦在 macOS 特有的两个坑：签名和 launchd。理解了这两个，大部分 dev 问题都能定位。
