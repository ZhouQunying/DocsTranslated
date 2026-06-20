# macOS permissions

## 架构精读

> 跳过不影响阅读翻译正文。

### TCC 权限绑定代码身份——为什么 ad-hoc 签名这么坑

macOS 的 TCC（Transparency, Consent, and Control）把权限授予**绑定到代码身份**，而不是进程名或路径。Ad-hoc 签名每次构建都生成新身份，所以 macOS 会**忘记**之前的权限授予。

这跟 Stripe API key 绑定 account 是一个思路。API key 换了，之前 key 的权限就失效了。TCC 也是这样：代码身份换了（ad-hoc 重新签名），之前的 Accessibility/Screen Recording 权限就没了。这就是为什么文档建议**授予权限给签名过的 app**（OpenClaw.app 或 Peekaboo.app），而不是 ad-hoc build。

### Ad-hoc 签名的身份不稳定——dev 模式的代价

Ad-hoc 签名（`codesign -s -`）不依赖 Apple Developer 证书，但每次构建都生成不同的代码身份。这意味着：
- 每次 `pnpm build` 后，TCC 权限丢失
- 用户需要重新授权 Accessibility、Screen Recording 等
- Dev 体验很差，但 production build 没问题（Developer ID 签名稳定）

这跟 JWT token rotation 是一个思路。Token 每次 rotation 都生成新 token，旧 token 失效。Ad-hoc 签名也是这样：每次构建都是"新身份"，旧权限失效。Dev 模式接受这个代价，production 用稳定签名避免。

### System Settings 的 node entry——权限的聚合视图

文档建议把 System Settings 里的 node entry 看作**该 node runtime 的广泛权限**。这意味着一个 node（如 Peekaboo.app）的 TCC 权限覆盖了它的所有子进程。这跟 Kubernetes RBAC 的 namespace-scoped 权限是一个思路——权限绑定到 namespace（或 node），不是绑定到单个 pod（或进程）。
