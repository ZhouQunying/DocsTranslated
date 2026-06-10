# Browser 登录

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么不让 agent 自己登录？

两个原因：反机器人防御和凭据安全。自动化登录触发 CAPTCHA、设备验证、甚至封号——特别是 X/Twitter 这类严格站点。而把密码给模型意味着凭据进入上下文窗口,可能被提示注入泄露。

正确模式是**人登录、agent 复用会话**。`openclaw` profile 的 cookie 持久化,登一次后续都能用。沙箱环境更容易被检测为机器人,所以严格站点优先走宿主浏览器而非沙箱内浏览器。

---

## 手动登录（推荐）

> When a site requires login, **sign in manually** in the **host** browser profile (the openclaw browser).

站点需要登录时,在**宿主**浏览器 profile（openclaw 浏览器）中**手动登录**。

**不要**把凭据给模型。自动化登录常触发反机器人防御,可能锁定账号。

返回主浏览器文档：[Browser](/tools/browser)。

## 用的是哪个 Chrome profile？

> OpenClaw controls a **dedicated Chrome profile** (named `openclaw`, orange-tinted UI)...

OpenClaw 控制一个**专用 Chrome profile**（名为 `openclaw`,橙色调 UI）。与你日常浏览器 profile 隔离。

Agent 浏览器工具调用：

- 默认选择：agent 应使用隔离的 `openclaw` 浏览器。
- 仅当已有登录会话重要且用户在电脑前能点击/批准附加提示时用 `profile="user"`。
- 有多个 user-browser profile 时显式指定 profile 而非猜测。

两种便捷访问方式：

1. **让 agent 打开浏览器**然后自己登录。
2. **CLI 打开：**

```bash
openclaw browser start
openclaw browser open https://x.com
```

有多个 profile 时传 `--browser-profile <name>`（默认 `openclaw`）。

## X/Twitter：推荐流程

- **读/搜/帖子：** 用**宿主**浏览器（手动登录）。
- **发推：** 用**宿主**浏览器（手动登录）。

## 沙箱 + 宿主浏览器访问

> Sandboxed browser sessions are **more likely** to trigger bot detection...

沙箱浏览器会话**更可能**触发机器人检测。X/Twitter（及其他严格站点）优先用**宿主**浏览器。

Agent 在沙箱中时浏览器工具默认用沙箱。允许宿主控制：

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",
        browser: {
          allowHostControl: true,
        },
      },
    },
  },
}
```

然后自己打开宿主浏览器（CLI 调用始终针对宿主浏览器运行）：

```bash
openclaw browser open https://x.com --browser-profile openclaw
```

设了 `sandbox.browser.allowHostControl: true` 后 agent 的 `browser` 工具调用可定向宿主。或者对发推的 agent 禁用沙箱。

## 相关

- [Browser](/tools/browser)
- [Browser Linux 故障排查](/tools/browser-linux-troubleshooting)
- [Browser WSL2 故障排查](/tools/browser-wsl2-windows-remote-cdp-troubleshooting)
