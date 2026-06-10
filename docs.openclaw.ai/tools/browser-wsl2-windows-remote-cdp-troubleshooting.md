# WSL2 + Windows + 远程 Chrome CDP 故障排查

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 WSL2 浏览器控制这么难调？

因为**三层独立故障面叠加**：CDP 传输（Chrome 端口能不能从 WSL2 访问）、Control UI 安全源策略（HTTP 页面开在哪个地址）、令牌/配对认证。三者各自独立失败但错误信息看起来相似,所以修一层后还有下一层的错误冒出来,让人以为没修好。

分层验证是唯一正确方法：从 Windows 本机验证 Chrome CDP → 从 WSL2 验证跨界可达 → 配置 OpenClaw profile → 单独验证 Control UI → 端到端测试。每层不通则不该跳到下一层。

---

> In the common split-host setup, OpenClaw Gateway runs inside WSL2, Chrome runs on Windows...

常见的分主机设置中,OpenClaw Gateway 在 WSL2 内运行,Chrome 在 Windows 运行,浏览器控制必须跨 WSL2 和 Windows 边界。来自 [issue #39369](https://github.com/openclaw/openclaw/issues/39369) 的分层故障模式意味着多个独立问题可同时出现,导致错误层先看起来像是坏的那个。

## 先选对浏览器模式

两种有效模式：

### 选项 1：从 WSL2 到 Windows 的原始远程 CDP

用远程浏览器 profile 从 WSL2 指向 Windows Chrome CDP 端点。

适用场景：

- Gateway 留在 WSL2 内
- Chrome 在 Windows 运行
- 需要浏览器控制跨 WSL2/Windows 边界

### 选项 2：宿主本地 Chrome MCP

仅当 Gateway 本身和 Chrome 在同一台主机时用 `existing-session` / `user`。

适用场景：

- OpenClaw 和 Chrome 在同一台机器
- 需要本地已登录浏览器状态
- 不需要跨主机浏览器传输
- 不需要高级受管/原始 CDP 专属路由如 `responsebody`、PDF 导出、下载拦截或批量操作

WSL2 Gateway + Windows Chrome 优先用原始远程 CDP。Chrome MCP 是宿主本地的,不是 WSL2 到 Windows 的桥。

## 工作架构

参考形态：

- WSL2 在 `127.0.0.1:18789` 运行 Gateway
- Windows 在普通浏览器中打开 Control UI `http://127.0.0.1:18789/`
- Windows Chrome 在端口 `9222` 暴露 CDP 端点
- WSL2 能访问该 Windows CDP 端点
- OpenClaw 把浏览器 profile 指向从 WSL2 可达的地址

## 为什么这个设置容易混淆

多个故障可重叠：

- WSL2 不能访问 Windows CDP 端点
- Control UI 从非安全源打开
- `gateway.controlUi.allowedOrigins` 不匹配页面源
- 令牌或配对缺失
- 浏览器 profile 指向错误地址

因此修一层仍可能留下不同层的错误可见。

## Control UI 关键规则

> When the UI is opened from Windows, use Windows localhost...

从 Windows 打开 UI 时,除非有故意的 HTTPS 设置,用 Windows localhost。

使用：`http://127.0.0.1:18789/`

Control UI 不要默认用局域网 IP。局域网或 tailnet 地址上的 HTTP 明文可触发与 CDP 无关的不安全源/设备认证行为。见 [Control UI](/web/control-ui)。

## 分层验证

从上到下,不要跳步。

### 第 1 层：验证 Chrome 在 Windows 提供 CDP

在 Windows 启动带远程调试的 Chrome：

```powershell
chrome.exe --remote-debugging-port=9222
```

先从 Windows 验证 Chrome 本身：

```powershell
curl http://127.0.0.1:9222/json/version
curl http://127.0.0.1:9222/json/list
```

此处失败则问题还不在 OpenClaw。

### 第 2 层：验证 WSL2 能访问该 Windows 端点

从 WSL2 测试你计划在 `cdpUrl` 中用的确切地址：

```bash
curl http://WINDOWS_HOST_OR_IP:9222/json/version
curl http://WINDOWS_HOST_OR_IP:9222/json/list
```

正常结果：

- `/json/version` 返回含 Browser / Protocol-Version 元数据的 JSON
- `/json/list` 返回 JSON（无页面打开时空数组正常）

失败原因：

- Windows 尚未向 WSL2 暴露端口
- 地址对 WSL2 侧不对
- 防火墙/端口转发/本地代理仍缺

修复后再碰 OpenClaw 配置。

### 第 3 层：配置正确的浏览器 profile

原始远程 CDP,将 OpenClaw 指向从 WSL2 可达的地址：

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "remote",
    profiles: {
      remote: {
        cdpUrl: "http://WINDOWS_HOST_OR_IP:9222",
        attachOnly: true,
        color: "#00AA00",
      },
    },
  },
}
```

注意：

- 用 WSL2 可达地址,不是只在 Windows 本地通的
- 外部管理的浏览器保持 `attachOnly: true`
- `cdpUrl` 可以是 `http://`、`https://`、`ws://` 或 `wss://`
- 要 OpenClaw 发现 `/json/version` 时用 HTTP(S)
- 浏览器提供商给直接 DevTools socket URL 时才用 WS(S)
- 期望 OpenClaw 成功前先用 `curl` 测同一 URL

### 第 4 层：单独验证 Control UI 层

从 Windows 打开 UI：`http://127.0.0.1:18789/`

然后验证：

- 页面源匹配 `gateway.controlUi.allowedOrigins` 期望
- 令牌认证或配对正确配置
- 没有把 Control UI 认证问题当浏览器问题调

参考：[Control UI](/web/control-ui)

### 第 5 层：验证端到端浏览器控制

从 WSL2：

```bash
openclaw browser open https://example.com --browser-profile remote
openclaw browser tabs --browser-profile remote
```

正常结果：

- 标签页在 Windows Chrome 中打开
- `openclaw browser tabs` 返回目标
- 后续操作（`snapshot`、`screenshot`、`navigate`）在同一 profile 可用

## 常见误导性错误

将每条消息视为特定层的线索：

- `control-ui-insecure-auth` — UI 源/安全上下文问题,不是 CDP 传输问题
- `token_missing` — 认证配置问题
- `pairing required` — 设备审批问题
- `Remote CDP for profile "remote" is not reachable` — WSL2 不能访问配置的 `cdpUrl`
- `Browser attachOnly is enabled and CDP websocket for profile "remote" is not reachable` — HTTP 端点应答了,但 DevTools WebSocket 仍打不开
- 远程会话后过期的视口/暗色模式/区域/离线覆盖 — 运行 `openclaw browser stop --browser-profile remote`（关闭活跃控制会话并释放 Playwright/CDP 模拟状态,不重启 gateway 或外部浏览器）
- `gateway timeout after 1500ms` — 通常仍是 CDP 可达性或慢/不可达远程端点
- `No Chrome tabs found for profile="user"` — 选了本地 Chrome MCP profile 但无宿主本地标签页可用

## 快速排查清单

1. Windows：`curl http://127.0.0.1:9222/json/version` 通吗？
2. WSL2：`curl http://WINDOWS_HOST_OR_IP:9222/json/version` 通吗？
3. OpenClaw 配置：`browser.profiles.<name>.cdpUrl` 用的是那个 WSL2 可达地址吗？
4. Control UI：打开的是 `http://127.0.0.1:18789/` 而非局域网 IP 吗？
5. 是不是用了 `existing-session` 跨 WSL2 和 Windows 而非原始远程 CDP？

## 实际要点

> The setup is usually viable...

这个设置通常可行。难点在于浏览器传输、Control UI 源安全和令牌/配对各自可以独立失败,但从用户侧看起来相似。

拿不准时：

- 先在 Windows 本地验证 Chrome 端点
- 再从 WSL2 验证同一端点
- 然后才调 OpenClaw 配置或 Control UI 认证

## 相关

- [Browser](/tools/browser)
- [Browser login](/tools/browser-login)
- [Browser Linux 故障排查](/tools/browser-linux-troubleshooting)
