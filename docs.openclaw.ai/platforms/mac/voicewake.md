# Voice wake (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### macOS 26+ 硬要求——平台 API 的依赖

Voice Wake（"Hey OpenClaw"）和 push-to-talk 要求 macOS 26 或更新。老版本 macOS 不支持这些特性。这跟 iOS 的 API availability 是一个思路——iOS 16 引入了 Lock Screen widgets，iOS 15 用不了。OpenClaw 的 Voice Wake 依赖 macOS 26 的新 API（可能是语音识别或低延迟音频），老版本只能 fallback 到手动触发。

### Stuck overlay recovery——circuit breaker 模式

文档提到一个 hardening：如果 overlay 卡住可见，手动关闭后，Voice Wake 不再工作。修复后应该能恢复。这跟 circuit breaker 是一个思路。Circuit breaker 在失败次数过多时断开（防止雪崩），但**必须能自动恢复**（half-open 状态探测）。Voice Wake 的 stuck overlay 也是：卡住了手动关闭（断开），但修复后应该能重新唤醒（恢复）。

### 状态机 bug 的教训——手动关闭破坏了状态

之前手动关闭 overlay 会破坏 Voice Wake，因为状态机认为 overlay 还在（状态不一致）。这跟 React 的 stale closure 是一个思路——闭包捕获了旧状态，更新后闭包里的状态还是旧的。Voice Wake 的状态机也是这样：overlay 手动关闭了，但状态机没收到关闭事件，状态还是"overlay 可见"。修复方式是**确保状态转换有唯一路径**，不能从外部绕过。
