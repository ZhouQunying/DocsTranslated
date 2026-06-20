# Voice wake (macOS)

## 架构精读

> 跳过不影响阅读翻译正文。

### macOS 26+ 硬要求——平台 API 的依赖

Voice Wake("Hey OpenClaw"语音唤醒,用户说这句话就能启动语音输入)和 push-to-talk(按住快捷键启动语音输入)要求 macOS 26 或更新。老版本 macOS 不支持这些特性。

**为什么不能支持老版本?** 这不是"建议 macOS 26",而是**硬依赖**——Voice Wake 依赖 macOS 26 新引入的语音识别 API 和低延迟音频 API,老版本系统没有这些 API。开发者想支持老版本也没办法——API 不存在,代码编译都过不了。

**这跟 browser API 兼容性是一个思路**。WebRTC(浏览器实时音视频通信 API)要求现代浏览器(Chrome/Firefox/Safari 最新版),IE 不支持不是因为"IE 太旧",而是 IE 根本没有 WebRTC API。OpenClaw 的 Voice Wake 也是这样: macOS 26 之前没有对应的语音 API,不是 fallback 到旧 API,而是根本没有。

### Stuck overlay recovery——状态一致性恢复

Overlay(语音输入时显示的浮动窗口,提示用户"正在听"或"录音中")如果卡住可见(应该消失但没消失),用户手动关闭后,Voice Wake 应该能恢复正常工作。

**之前的问题是什么?** 手动关闭 overlay 后,Voice Wake 不再工作——因为状态机认为 overlay 还在(状态不一致)。用户说"Hey OpenClaw",状态机检查"overlay 可见,不需要再开",但 overlay 实际上已经关了。

**修复方式**: 确保状态转换有**唯一路径**——overlay 的开启和关闭都必须经过状态机,不能从外部绕过。手动关闭 overlay 时,必须通知状态机"overlay 已关闭",状态机更新状态为"overlay 不可见",Voice Wake 才能重新触发 overlay。

**这跟数据库的事务一致性是一个思路**——数据库的状态(如"账户余额")必须跟实际操作一致。如果用户转账 100 元,数据库必须记录"扣 100 + 加 100",不能只扣不加(状态不一致)。Voice Wake 的状态机也是同样: overlay 的实际状态(可见/不可见)必须跟状态机记录的状态一致。

### 状态机 bug 的教训——手动关闭破坏了状态

之前手动关闭 overlay 会破坏 Voice Wake,因为状态机认为 overlay 还在(状态不一致)。这跟 React 的 stale closure(闭包捕获了旧状态,组件更新后闭包里的状态还是旧的)是一个思路——Voice Wake 的状态机也是这样: overlay 手动关闭了,但状态机没收到关闭事件,状态还是"overlay 可见"。

**修复方式**: 确保状态转换有唯一路径,不能从外部绕过。所有改变 overlay 可见性的操作(自动关闭、手动关闭、超时关闭)都必须经过状态机,状态机更新后才能生效。
