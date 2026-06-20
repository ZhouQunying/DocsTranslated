# iOS app / iOS 应用

## 架构精读

> 跳过不影响阅读翻译正文。

### Relay-backed Push——APNs token 不暴露给 Gateway

iOS 官方构建用外部 push relay，不把原始 APNs token 直接给 Gateway。流程是：
1. iOS app 用 App Attest + StoreKit JWS 向 relay 注册
2. Relay 返回不透明的 relay handle + registration-scoped send grant
3. iOS app 把 relay handle 转发给 paired Gateway
4. Gateway 用 relay handle 发 push，relay 转发给 APNs

这跟 Stripe 的 token 化支付是一个思路。Stripe 不让商户直接接触信用卡号——商户拿到的是 token，用 token 调 Stripe API 扣款。OpenClaw 的 push relay 也是这样：Gateway 拿到的是 relay handle，用 handle 调 relay API 发 push，Gateway 永远不接触 APNs key。

安全收益是**最小权限**。Gateway 被入侵后，攻击者只能给这一台 iOS 设备发 push，不能用 APNs key 给所有用户发 push。这是 blast radius 控制——限制单次入侵的影响范围。

### App Attest + StoreKit——设备真实性验证

iOS app 用 **App Attest**（Apple 的设备真实性验证）和 **StoreKit app transaction JWS**（Apple 签名的交易凭证）向 relay 证明"我是真实的 OpenClaw app，运行在真实的 iOS 设备上"。

这跟 Google 的 Play Integrity API 是一个思路。Play Integrity 让服务端验证"这个请求来自真实的 Android 设备上的真实 app"，防止模拟器和修改版 app。OpenClaw 的 iOS push relay 用同样的机制防止伪造 push 注册。

### Background Alive Beacons——后台保活

iOS app 用 **background alive beacons** 定期向 Gateway 报告存活状态。这是 iOS 后台限制下的生存策略——iOS 不像 Android 允许 foreground service 无限后台运行，iOS 只给有限的后台执行时间。

Beacon 的设计是**低功耗 + 高信息量**。不是持续连接，而是定期 ping 一下，告诉 Gateway "我还活着"。Gateway 收到 beacon 就知道 iOS node 在线，可以转发命令。这跟 IoT 设备的 heartbeat 是一个思路——低功耗设备定期 wakeup 上报状态，其余时间 sleep。

### Node 能力声明——和 Android 对称但不同

iOS 暴露的 node 能力和 Android 类似（Canvas、Screen snapshot、Camera、Location、Talk mode、Voice wake），但实现细节不同。iOS 用 Apple 的 API（如 AVFoundation 做 camera，CoreLocation 做 location），Android 用 Android SDK。

这跟 Flutter 的平台通道是一个思路。Flutter 用统一 API 调平台能力，但底层 iOS 用 Swift/Objective-C，Android 用 Kotlin/Java。OpenClaw 的 node protocol 是统一 API，底层各平台用自己的 SDK 实现。
