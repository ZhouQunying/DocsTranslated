# Canvas

## 架构精读

> 跳过不影响阅读翻译正文。

### WKWebView 嵌入 agent UI——嵌入式浏览器的安全考量

macOS app 用 **WKWebView**(Apple 提供的 web 渲染组件,类似 browser 的渲染引擎,可以嵌入到 native app 中)渲染 agent 控制的 Canvas panel(画布面板,agent 可以在上面绘制 UI、显示图表、渲染交互式内容)。

**为什么用 WKWebView 而不是纯 native view?** 因为 Canvas 需要渲染 agent 生成的 HTML/JS/CSS(如 A2UI commands,agent 通过特定命令生成 UI,如"画一个图表"、"显示一个表格")。Web 技术(HTML/JS/CSS)更灵活,agent 可以生成任意 UI,native view 需要为每种 UI 写专门的组件。

**但 WKWebView 有安全风险**: agent 生成的 JS 可以执行任意代码。如果 agent 被恶意 prompt 注入,JS 可能读取本地文件、发起网络请求、甚至控制 app。OpenClaw 的应对是:
- **Custom URL scheme**(自定义 URL 协议,如 `openclaw-canvas://`): 限制资源加载,只允许加载本地文件
- **Sandbox**(沙盒,限制 JS 的能力): 禁止访问文件系统、网络、其他 app

这跟 **CSP**(Content Security Policy,内容安全策略,浏览器用来限制网页能加载哪些资源)是一个思路: 不允许 inline script、只加载 trusted source。Canvas 的 WKWebView 也是同样: 只加载本地文件,不允许外部请求。

### Custom URL scheme——隐藏文件系统路径

Canvas 用 **custom URL scheme**(自定义 URL 协议,如 `openclaw-canvas://`)加载本地文件,而不是直接暴露文件系统路径(如 `file:///Users/xxx/Library/Application Support/OpenClaw/canvas/index.html`)。

**为什么这样设计?** 因为暴露路径有安全风险:
- Agent 知道文件在哪,可能尝试读取其他文件(如 `file:///Users/xxx/.ssh/id_rsa`)
- 用户看到路径,可能手动修改文件(破坏 Canvas 状态)

Custom scheme 隐藏了真实路径: agent 看到 `openclaw-canvas://index.html`,不知道实际路径是 `~/Library/Application Support/OpenClaw/canvas/`。App 在内部做映射(`openclaw-canvas://` → `~/Library/...`),agent 无法绕过。

这跟 Chrome Extension 的 `chrome-extension://` scheme 是一个思路——extension 资源通过 custom scheme 加载,不暴露文件系统路径。OpenClaw 的 Canvas 也是同样: agent 用 `openclaw-canvas://` 访问资源,不知道真实路径。

**额外好处**: 实际路径可以变(如从 `~/Library/` 移到 `~/.openclaw/`),但 scheme URL 不变,app 内部改映射就行。这跟 REST API 的 URL 设计是一个思路: URL 是资源标识,不是文件路径。

### Built-in scaffold——首次体验的引导

如果 Canvas 根目录没有 `index.html`,app 显示 built-in scaffold page(内置的引导页面)。

**为什么需要这个?** 因为用户第一次打开 Canvas 时,agent 还没创建任何 UI,Canvas 是空的。如果显示空白,用户会困惑("这是啥?是不是坏了?")。Scaffold 页面告诉用户:"Canvas 是 agent 用来显示交互式内容的,你可以让 agent 画图表、显示数据、创建工具"。

这跟 SPA 的 loading state(单页应用启动时显示的加载状态,如 skeleton screen 或 loading spinner)是一个思路——应用启动时显示引导内容,不是白屏。OpenClaw 的 scaffold 也是同样的 UX 原则: agent 还没创建 Canvas UI 时,用户看到引导页,而不是空白或错误。首次体验(first-run experience)是产品设计的关键。
