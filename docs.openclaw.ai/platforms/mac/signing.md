# macOS signing

## 架构精读

> 跳过不影响阅读翻译正文。

### Ad-hoc vs Developer ID——签名策略的两极

macOS app 的签名有两种：
- **Ad-hoc**（`SIGN_IDENTITY="-"`）：不需要 Apple Developer 证书，但每次构建生成新代码身份
- **Developer ID**：需要 Apple Developer Program 会员，代码身份稳定

这跟 self-signed cert vs CA-signed cert 是一个思路。Self-signed 免费但浏览器不信任，CA-signed 付费但浏览器信任。Ad-hoc 签名也是免费但 TCC 不信任（每次重建权限丢失），Developer ID 付费但 TCC 信任（权限持久）。Dev 用 ad-hoc 够用，production 必须用 Developer ID。

### Build metadata——每个构建可独立追溯

macOS 的每个 app 都是一个"bundle"(捆绑包,就是一个文件夹,但系统把它当成一个整体),里面有一个 `Info.plist` 文件,记录了 app 的基本信息。这个文件就像 app 的"身份证"——丢了它,app 就不知道自己是谁。

OpenClaw 的构建脚本会自动把以下信息写进 Info.plist:
- Version(语义版本号,如 1.2.3)
- Build date(构建时间,如 2026-06-20 14:30)
- Git commit(代码版本,如 abc1234)
- Signed/unsigned(签名状态,是否经过 Apple 认证)

用户在 app 里点开**关于面板**(macOS 里叫 "About xxx",通常在菜单栏 app name 下的第一个选项,点开后显示 app 版本信息)就能看到这些。

**这不是装饰,是 debugging 的基础设施**。用户报 bug 时说"我用的最新版",但"最新"是相对的——他们可能用的是三天前构建的旧版,或者未签名的 dev build,或者他们机器上的"最新"和开发者理解的"最新"不是同一个 commit。Info.plist 里的 metadata 让每个构建有独立身份,开发者看到"Git commit: abc1234"就知道这是哪个版本。

**没有 build metadata 的 app 是黑盒**——出了问题不知道是哪个版本,只能猜。有 metadata 的 app 每个构建都可追溯,debugging 有据可查。

### TCC 双重身份绑定——两个维度防两种攻击

TCC 权限不仅绑定 bundle ID,还绑定代码签名。这意味着:
- 同一个 bundle ID,不同签名 → 不同权限
- 同一个签名,不同 bundle ID → 不同权限

两个维度各自防不同类型的攻击:
- **Bundle ID 防"恶意 fork"**: 攻击者可以 fork 你的代码、复用 bundle ID,但没有你的 Developer ID 签名,TCC 不会授予相同的权限
- **代码签名防"bundle ID 伪造"**: 攻击者可以创建一个 bundle ID 相同的 app,但没有对应的 Developer ID,TCC 识别出签名不匹配,拒绝授权

**单一维度绑定的风险**: 如果只绑定 bundle ID,攻击者创建同名 bundle ID 的恶意 app 就能窃取权限(比如伪装成银行 app 读通讯录)。如果只绑定签名,攻击者可以在自己签名的 app 里用同样的签名逻辑滥用权限。双重绑定 = 双保险。

这跟 OAuth 2.0 的 **client_id + client_secret** 是两个不同的机制,不要混淆。OAuth 是"客户端声明身份 + 证明身份",TCC 是"操作系统验证身份 + 绑定权限"。
