# Canvas

## 架构精读

> 跳过不影响阅读翻译正文。

### WKWebView 嵌入 agent UI——嵌入式浏览器的安全考量

macOS app 用 **WKWebView** 嵌入 agent 控制的 Canvas panel。这跟 Electron 的 BrowserWindow 是一个思路——用 web 技术渲染 UI，但 native shell 控制生命周期和权限。OpenClaw 选择 WKWebView 而不是纯 native view，是因为 Canvas 需要渲染 agent 生成的 HTML/JS（如 A2UI commands），web 技术更灵活。

但 WKWebView 有安全风险——agent 生成的 JS 可以执行任意代码。OpenClaw 的应对是**custom URL scheme**（限制资源加载）和 **sandbox**（限制 JS 能力）。这跟 CSP（Content Security Policy）是一个思路：不允许 inline script、只加载 trusted source。Canvas 的 WKWebView 也是这样：只加载本地文件，不允许外部请求。

### Custom URL scheme 本地文件服务——内容安全

Canvas 用 custom URL scheme（如 `openclaw-canvas://`）服务本地文件。这跟 Chrome Extension 的 `chrome-extension://` scheme 是一个思路——extension 资源通过 custom scheme 加载，不暴露文件系统路径。OpenClaw 的 Canvas 也是这样：agent 看到 `openclaw-canvas://index.html`，不知道实际路径是 `~/Library/Application Support/OpenClaw/canvas/`。

Custom scheme 的好处是**抽象层**。实际路径可以变（如从 `~/Library/` 移到 `~/.openclaw/`），但 scheme URL 不变。这跟 REST API 的 URL 设计是一个思路：URL 是资源标识，不是文件路径。

### Built-in scaffold——graceful degradation

如果 Canvas 根目录没有 `index.html`，app 显示 built-in scaffold page。这跟 Nginx 的 default page 是一个思路——没有配置 server block 时，Nginx 显示 welcome page，不是 404。OpenClaw 的 scaffold 也是 graceful degradation：agent 还没创建 Canvas UI 时，用户看到引导页（"Canvas 是什么、怎么用"），而不是空白或错误。
