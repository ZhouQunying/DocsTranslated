# WebChat (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### SwiftUI 嵌入 Web UI——hybrid native/web 架构

macOS menu bar app 用 **SwiftUI view** 嵌入 WebChat UI（WKWebView）。这跟 Slack/Electron 的 hybrid 架构是一个思路——native shell 提供系统集成（menu bar、notification、hotkey），web content 提供业务逻辑（chat UI、markdown 渲染）。OpenClaw 选择 hybrid 而不是纯 native，是因为 WebChat 已有完整实现，重写 native 成本高、维护负担重。

Hybrid 的好处是**一套 UI 多端复用**。WebChat 在 browser 和 macOS app 里是同一套代码，bug fix 一次生效。缺点是 web view 不如 native view 流畅，但对 chat UI 来说性能要求不高。

### Lobster menu 集成——plugin 式 UI 扩展

WebChat 通过 **Lobster menu**（可能是 OpenClaw 的 plugin menu）打开。这跟 VS Code 的 command palette 是一个思路——核心功能通过 command 触发，不需要在 UI 上占按钮。OpenClaw 的 Lobster menu 是 plugin 式扩展点：WebChat 注册一个 command，menu 显示入口，用户点击打开 chat。

### 自定义 subsystem 日志——可观测性的粒度

文档提到用 `./scripts/clawlog.sh` 过滤 `ai.openclaw` subsystem 和 `WebChatSwiftUI` category。这跟 Kubernetes 的 component logging 是一个思路——kube-apiserver、kube-scheduler、kube-controller-manager 各有独立日志，可以按 component 过滤。OpenClaw 也是这样：WebChat 用独立 subsystem/category，调试时只看 WebChat 日志，不被 Gateway 或其他组件的日志淹没。
