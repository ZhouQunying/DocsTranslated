# Peekaboo bridge

## 架构精读

> 跳过不影响阅读翻译正文。

### 三条桌面控制路径——关注点分离

OpenClaw 有三条桌面控制路径：
1. **原生 macOS app 能力**（AppleScript、Accessibility）
2. **PeekabooBridge**（UI automation broker）
3. **Browser automation**（Playwright/Puppeteer via CLI node）

三条路径**故意保持分离**。它们分别对应三种控制层级：操作系统 UI（原生能力）、应用 UI（Peekaboo）、Web UI（browser automation）。Agent 要操作什么就选什么路径——操作 Finder 用 AppleScript，点击 macOS app 按钮用 Peekaboo，填 web 表单用 browser automation。

这跟 Kubernetes 的多层控制是一个思路。kubectl 操作集群资源，Helm 操作 release，GitOps 操作 Git 仓库。三个工具各自在不同抽象层工作，不重叠。OpenClaw 的三条路径也是这样：各自在不同 UI 层级工作，agent 根据目标选择路径。

分离的好处是**权限最小化**。Browser automation 不需要 Accessibility 权限，Peekaboo 不需要 browser 控制。每条路径只申请自己需要的权限，符合 least privilege 原则。

### Peekaboo 作为 permission-aware broker——capability-based security

PeekabooBridge 是 **permission-aware** 的 UI automation broker。它检查 agent 的权限，决定允许哪些 UI 操作。这跟 capability-based security 是一个思路——不是 ACL（谁可以访问什么），而是 capability（持有什么 token 可以做什么）。Peekaboo 的 agent 持有特定 capability（如"可以点击按钮"），但不能"读取屏幕内容"（需要另一个 capability）。

这跟 iOS 的 entitlements 也是一个思路。iOS app 的 entitlements 文件声明了 app 的能力（如 push notification、iCloud），系统根据 entitlements 决定允许哪些 API 调用。Peekaboo 也是这样：agent 的 capability 决定允许哪些 UI 操作。

### Unix socket server 的懒加载——按需启动

Peekaboo 启用时才启动 Unix socket server，禁用时不启动。这跟 lazy initialization 是一个思路——资源在第一次使用时初始化，不是 app 启动时全部加载。OpenClaw 的 Peekaboo 也是这样：用户不需要 UI automation 时，不启动 socket server（不占资源、不暴露攻击面）。需要时启动，禁用时停止。
