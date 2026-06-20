# Peekaboo bridge

## 架构精读

> 跳过不影响阅读翻译正文。

### 三条桌面控制路径——按控制层级分离

OpenClaw 有三条桌面控制路径:
1. **原生 macOS app 能力**: AppleScript(macOS 的脚本语言,可以控制 Finder、Mail 等系统 app)、Accessibility(辅助功能 API,可以读取和操作其他 app 的 UI 元素)
2. **PeekabooBridge**: UI automation broker(独立的 UI 自动化进程,作为 agent 和 macOS UI 之间的桥梁)
3. **Browser automation**: Playwright/Puppeteer(浏览器自动化框架,通过 CLI node 执行)控制 Chromium

三条路径**故意保持分离**,因为它们分别对应三种控制层级:
- **操作系统 UI**(原生能力): 操作 Finder、Mail 等系统 app
- **应用 UI**(Peekaboo): 操作任意 macOS app 的按钮、文本框、菜单
- **Web UI**(browser automation): 操作浏览器里的网页(填表单、点击按钮)

Agent 要操作什么就选什么路径——操作 Finder 用 AppleScript,点击 macOS app 按钮用 Peekaboo,填 web 表单用 browser automation。

这跟 Kubernetes 的多层控制是一个思路——kubectl 操作集群资源(Pod、Service),Helm 操作 release(一组资源的集合),GitOps 操作 Git 仓库(通过 Git 变更触发部署)。三个工具各自在不同抽象层工作,不重叠。OpenClaw 的三条路径也是同样: 各自在不同 UI 层级工作,agent 根据目标选择路径。

分离的好处是**权限最小化**: Browser automation 不需要 Accessibility 权限(它只控制浏览器,不需要控制其他 app),Peekaboo 不需要 browser 控制(它控制 macOS UI,不需要控制浏览器)。每条路径只申请自己需要的权限,符合 least privilege 原则(最小权限原则,只给必要的权限)。

### Peekaboo 作为权限感知的 broker——基于能力的安全模型

PeekabooBridge 是 **permission-aware**(权限感知)的 UI automation broker。它检查 agent 的权限,决定允许哪些 UI 操作。

这跟 **capability-based security**(基于能力的安全模型)是一个思路——不是 ACL(谁可以访问什么资源),而是 capability(持有什么 token 可以做什么操作)。Peekaboo 的 agent 持有特定 capability(如"可以点击按钮"),但不能"读取屏幕内容"(需要另一个 capability)。

**为什么用 capability 而不是 ACL?** ACL 是"agent A 可以访问资源 X",粒度粗。Capability 是"agent A 持有 token 可以做 action Y",粒度细。UI automation 需要细粒度控制——"可以点击按钮"和"可以读取屏幕"是两种不同的能力,应该分开授权。

这跟 iOS 的 entitlements(能力声明文件,声明 app 需要哪些系统能力)是一个思路——iOS app 的 entitlements 文件声明了 app 的能力(如 push notification、iCloud),系统根据 entitlements 决定允许哪些 API 调用。Peekaboo 也是同样: agent 的 capability 决定允许哪些 UI 操作。

### Unix socket server 的懒加载——按需启动

Peekaboo 启用时才启动 Unix socket server,禁用时不启动。这跟 **lazy initialization**(懒加载,资源在第一次使用时初始化)是一个思路——不是 app 启动时全部加载,而是需要时才启动。

**为什么这样设计?** 用户不需要 UI automation 时,不启动 socket server 有两个好处:
- 不占资源(socket server 需要内存和 CPU)
- 不暴露攻击面(socket server 是潜在的入口点,少一个就少一个风险)

需要 UI automation 时启动,禁用时停止。这跟数据库连接池的懒加载是一个思路——连接在第一次查询时创建,不是启动时全部创建。
