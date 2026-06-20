# macOS signing

## 架构精读

> 跳过不影响阅读翻译正文。

### Ad-hoc vs Developer ID——签名策略的两极

macOS app 的签名有两种：
- **Ad-hoc**（`SIGN_IDENTITY="-"`）：不需要 Apple Developer 证书，但每次构建生成新代码身份
- **Developer ID**：需要 Apple Developer Program 会员，代码身份稳定

这跟 self-signed cert vs CA-signed cert 是一个思路。Self-signed 免费但浏览器不信任，CA-signed 付费但浏览器信任。Ad-hoc 签名也是免费但 TCC 不信任（每次重建权限丢失），Developer ID 付费但 TCC 信任（权限持久）。Dev 用 ad-hoc 够用，production 必须用 Developer ID。

### package-mac-app.sh 的 build metadata——版本可追溯

构建脚本自动 stamp bundle 的 Info.plist：
- Version（语义版本号）
- Build date（构建时间）
- Git commit（代码版本）
- Signed/unsigned（签名状态）

这跟 Docker image labels 是一个思路。Docker image 可以打 `org.opencontainers.image.source`、`org.opencontainers.image.revision` 等 label，记录来源和版本。OpenClaw 的 bundle 也是这样：About tab 读取 Info.plist，用户可以看版本、提交、构建时间。**可追溯性是 production 的基本要求**。

### TCC 权限绑定 bundle ID + signature——双重身份验证

TCC 权限不仅绑定 bundle ID，还绑定代码签名。这意味着：
- 同一个 bundle ID，不同签名 → 不同权限
- 同一个签名，不同 bundle ID → 不同权限

这跟 OAuth 2.0 的 client_id + client_secret 是一个思路。Client ID 标识客户端，client secret 证明身份。TCC 也是这样：bundle ID 标识 app，代码签名证明身份。双重验证防止"伪造 app 骗取权限"。
