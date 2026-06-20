# Voice overlay

## 架构精读

> 跳过不影响阅读翻译正文。

### Stream logs 调试 sticky overlay——分布式追踪的思路

Voice overlay 卡住时，文档建议 stream logs 复现问题。这跟 distributed tracing 是一个思路——当请求在多个服务间跳转时，用 trace ID 串联日志，定位卡在哪一跳。OpenClaw 的 voice overlay 也涉及多个组件（SwiftUI overlay、Gateway voice API、STT 服务），stream logs 可以看到每个组件的状态变化。

### Single active session token——幂等性保证

文档强调**验证只有一个 active session token**，stale callbacks 应该被丢弃。这跟分布式系统的幂等性是一个思路。HTTP 请求可能重复（网络超时重试），幂等 API 保证重复请求不产生副作用。Voice overlay 也是这样：push-to-talk 释放时调 `endCapture`，如果 token 已过期（stale），就忽略而不是报错。

### Push-to-talk 释放必须调 endCapture——graceful shutdown

Push-to-talk 释放时**总是**调 `endCapture` 和 active token。这跟 graceful shutdown 是一个思路——进程退出前清理资源（关连接、flush buffer、release lock）。Voice overlay 也是这样：用户松开按键时，必须通知 Gateway 停止录音，否则 Gateway 会继续录音（浪费资源、隐私风险）。

这跟 WebSocket 的 close handshake 是一个思路。WebSocket 不是直接断开 TCP，而是发 close frame，对方回 close frame，然后才断 TCP。Voice overlay 的 endCapture 也是 close handshake——通知 Gateway "我停止录音了"，Gateway 停止 STT 处理。
