# Voice overlay

## 架构精读

> 跳过不影响阅读翻译正文。

### Stream logs 调试卡住的 overlay——多组件问题的定位

Voice overlay(语音输入时显示的浮动窗口)卡住时(应该消失但没消失),文档建议 **stream logs**(实时查看日志输出,而不是事后看日志文件)复现问题。

**为什么需要 stream logs?** 因为 voice overlay 涉及多个组件:
- SwiftUI overlay(macOS app 的 UI 层)
- Gateway voice API(Gateway 提供的语音服务接口)
- STT 服务(Speech-to-Text,语音转文字,可能是第三方如 Whisper)

当 overlay 卡住时,问题可能出在任何一层: UI 没收到关闭事件、Gateway 没发关闭命令、STT 没返回结果。Stream logs 可以看到每个组件的状态变化(如"Gateway 发了 close 事件,但 UI 没收到"),定位卡在哪一层。

这跟分布式系统的 distributed tracing(分布式追踪,用 trace ID 串联多个服务的日志)是一个思路——当请求在多个服务间跳转时,用 trace ID 串联日志,定位卡在哪一跳。OpenClaw 的 voice overlay 也是多层组件协作,stream logs 是定位问题的关键。

### 确保只有一个 active session token——防止过期回调干扰

文档强调**验证只有一个 active session token**(会话令牌,标识当前的语音输入会话),stale callbacks(过期回调,如上一个会话的回调延迟到达)应该被丢弃。

**为什么这样设计?** 因为用户可能快速连续操作:
1. 按住快捷键开始录音(session token = A)
2. 松开快捷键结束录音(Gateway 停止录音,token A 过期)
3. 立刻又按住快捷键开始录音(session token = B)
4. 这时 token A 的回调才到达(网络延迟)

如果 app 不检查 token,就会处理 token A 的回调(属于上一个会话),导致状态混乱(如"录音已结束"事件覆盖了当前录音状态)。验证 active token = 只处理当前会话的回调,丢弃过期回调。

**这跟事件排序的防乱序处理是一个思路**——网络请求可能乱序到达,处理时必须检查"这个事件是不是当前会话的",不是就丢弃。Voice overlay 的 token 验证就是防乱序: 只接受当前 token 的事件,过期 token 的事件忽略。

### Push-to-talk 释放必须调 endCapture——显式通知停止录音

Push-to-talk(按住快捷键录音)释放时**总是**调 `endCapture`(通知 Gateway 停止录音)并传入 active token。

**为什么必须显式通知?** 因为 Gateway 不知道用户什么时候松开按键——只有 app 知道。如果 app 不调 `endCapture`,Gateway 会继续录音(以为用户还在说话),浪费资源、占用 STT 配额、还有隐私风险(用户以为录音结束了,其实还在录)。

**这跟 WebSocket 的 close handshake 是一个思路**——WebSocket 不是直接断开 TCP,而是发 close frame(通知对方"我要断开了"),对方回 close frame(确认),然后才断 TCP。Voice overlay 的 endCapture 也是 close handshake——通知 Gateway "我停止录音了",Gateway 停止 STT 处理,双方状态一致。

**不调 endCapture 的后果**: Gateway 继续录音,直到超时(如果有的话)或用户手动干预。这段时间内,用户的说话会被录下来(隐私风险),STT 配额被消耗(资源浪费),还可能产生额外的费用(STT 服务按时间计费)。
