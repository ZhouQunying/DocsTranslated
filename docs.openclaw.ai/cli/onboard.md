# `openclaw onboard`

## 架构精读

> 跳过不影响阅读翻译正文。

### 交互式引导——为什么需要专门的入门命令？

`openclaw onboard` 提供交互式引导流程：

1. 选择 AI provider（Anthropic/OpenAI/本地）
2. 输入 API 密钥或 OAuth 认证
3. 选择通道（WhatsApp/Telegram/Discord）
4. 配置通道凭证
5. 验证配置并启动

这跟 `rails new` 和 `create-react-app` 是一个思路——新用户不需要读完整文档就能在 5 分钟内跑起来。交互式引导降低入门摩擦，避免"配置太复杂放弃"。

### 幂等性——为什么可以重复运行？

`onboard` 是幂等的——重复运行不会覆盖已有配置，只补充缺失部分。

这跟 `apt install` 的幂等性是一个思路——已安装的包不会重新安装，只安装缺失的。用户可以中断后继续，不需要从头开始。

---

Interactive onboarding wizard: select AI provider → input credentials → select channel → configure channel credentials → validate and start. Idempotent — re-running does not overwrite existing config, only fills missing parts.

交互式入门向导：选择 AI provider → 输入凭证 → 选择通道 → 配置通道凭证 → 验证并启动。幂等——重复运行不覆盖已有配置，只补充缺失部分。
