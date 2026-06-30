# `openclaw configure`

## 架构精读

> 跳过不影响阅读翻译正文。

### 交互式配置——为什么需要专门的命令？

`openclaw configure` 提供交互式配置向导：

1. 选择 AI provider（Anthropic/OpenAI/本地）
2. 输入 API 密钥
3. 选择通道（WhatsApp/Telegram/Discord）
4. 配置通道凭证
5. 验证并保存

这跟 `aws configure` 是一个思路——交互式引导用户输入关键配置（provider、密钥、通道），不需要手动编辑 JSON5 文件。

### 与 onboard 的区别——为什么有两个类似命令？

- **`onboard`**：完整入门流程（配置 + 首次启动）
- **`configure`**：只配置（不启动），适合"重新配置"场景

这跟 `create-react-app` vs `npm run eject` 是一个思路——`create-react-app` 是完整初始化（创建项目 + 配置），`eject` 是只修改配置（不重新创建项目）。

---

Interactive configuration wizard: select AI provider → input API key → select channel → configure channel credentials → validate and save. Differs from `onboard` which includes first startup; `configure` only modifies config without restarting.

交互式配置向导：选择 AI provider → 输入 API 密钥 → 选择通道 → 配置通道凭证 → 验证并保存。区别于 `onboard`（包含首次启动）；`configure` 只修改配置不重启。
