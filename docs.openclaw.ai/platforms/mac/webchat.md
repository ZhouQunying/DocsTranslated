# WebChat (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### SwiftUI 嵌入 Web UI——hybrid native/web 架构

macOS menu bar app(菜单栏 app,图标在屏幕顶部菜单栏,不占 dock)用 **SwiftUI**(Apple 的 UI 框架,用 Swift 语言写)嵌入 WebChat UI。具体来说,用 **WKWebView**(Apple 提供的 web 渲染组件,类似 browser 的渲染引擎,但不带地址栏和书签)显示 WebChat 的 HTML/CSS/JS。

**为什么选择 hybrid(native + web)而不是纯 native?** 原因是**成本**: WebChat 已有完整的 chat UI 实现(消息渲染、markdown、code block 高亮),重写 native 版本成本高、还要维护两套代码(bug fix 要改两次)。Hybrid 架构让 native shell 提供系统集成(menu bar、notification、hotkey),web content 提供业务逻辑(chat UI),各取所长。

**好处是一套 UI 多端复用**: WebChat 在 browser 和 macOS app 里是同一套代码,bug fix 一次生效。**缺点是 web view 不如 native view 流畅**,但对 chat UI 来说性能要求不高——用户不期望 chat 有 60fps 动画,流畅度要求远低于游戏或视频编辑。

### Lobster menu 集成——plugin 式 UI 扩展

WebChat 通过 **Lobster menu**(OpenClaw 的 plugin menu,类似 app 的"扩展功能"菜单)打开。用户点击 menu 里的"Open Chat"或类似选项,WebChat 窗口就显示出来。

**为什么这样设计?** 因为 WebChat 不是 macOS app 的核心功能(核心功能是 Gateway 管理和 node 控制),而是可选的扩展功能。把可选功能放在 menu 里,而不是主界面,避免 UI 拥挤。用户想用 chat 就点开,不想用就忽略。

这跟 VS Code 的 command palette(Ctrl/Cmd+Shift+P 打开的命令面板,可以执行各种命令)是一个思路——核心功能通过 command 触发,不需要在 UI 上占按钮。OpenClaw 的 Lobster menu 也是同样: WebChat 注册一个 command,menu 显示入口,用户点击打开 chat。

### 自定义 subsystem 日志——按组件和功能过滤

文档提到用 `./scripts/clawlog.sh`(OpenClaw 提供的日志查看脚本)过滤 `ai.openclaw` subsystem 和 `WebChatSwiftUI` category。

**什么是 subsystem 和 category?** macOS unified logging 的两层过滤:
- **Subsystem**(子系统): 按组件过滤,如 `com.openclaw.gateway`、`com.openclaw.app`、`com.openclaw.webchat`
- **Category**(类别): 按功能过滤,如 `WebChatSwiftUI`(WebChat 的 SwiftUI 层)、`WebChatNetwork`(WebChat 的网络请求)

**为什么需要两层?** 因为 OpenClaw 有多个组件(Gateway、app、WebChat),每个组件有多个功能(UI、网络、存储)。调试时可能需要"只看 WebChat 的所有日志"(subsystem 过滤),或者"只看 WebChat 的网络请求日志"(subsystem + category 过滤)。两层过滤让调试更精准。

这跟 Docker 的 `--filter` 是一个思路——`docker logs --filter "container=web"` 只看 web 容器的日志,`docker logs --filter "container=web" --filter "level=error"` 进一步只看错误。OpenClaw 的 subsystem/category 也是同样的设计理念: 按组件和功能过滤,精准调试。
