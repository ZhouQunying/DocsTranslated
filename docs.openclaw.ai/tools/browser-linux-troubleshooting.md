# Browser 故障排查（Linux）

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么 Linux 上浏览器启动这么容易出问题？

核心矛盾是 **Snap 的 AppArmor 沙箱和 OpenClaw 的进程管理模式冲突**。OpenClaw 需要派生 Chrome 子进程、监控 PID、读 CDP 端口——这些全被 Snap 隔离策略拦截。而 `apt install chromium` 在 Ubuntu 上装的是 Snap 套壳,不是真浏览器。

两种解法的选择逻辑：装 Google Chrome deb 包（绕过 Snap）,或者 attach-only（放弃管理生命周期,自己起 Chrome,OpenClaw 只连上去）。前者简单,后者适合已有 Snap 生态不想动的环境。

无头回退也值得注意：Linux 无桌面时 OpenClaw 现在默认自动切无头,除非你手动强制了 headed 模式。这是防御性设计——服务器环境不该因为"忘记配 headless"就起不来。

---

## 问题："Failed to start Chrome CDP on port 18800"

> OpenClaw's browser control server fails to launch Chrome/Brave/Edge/Chromium with the error:

OpenClaw 的浏览器控制服务器启动 Chrome/Brave/Edge/Chromium 失败,报错：

```
{"error":"Error: Failed to start Chrome CDP on port 18800 for profile \"openclaw\"."}
```

### 根因

> On Ubuntu (and many Linux distros), the default Chromium installation is a **snap package**...

Ubuntu（和很多 Linux 发行版）上默认 Chromium 安装是 **Snap 包**。Snap 的 AppArmor 限制干扰 OpenClaw 产生和监控浏览器进程的方式。

`apt install chromium` 装的是跳转到 Snap 的桩包：

```
Note, selecting 'chromium-browser' instead of 'chromium'
chromium-browser is already the newest version (2:1snap1-0ubuntu2).
```

这不是真浏览器——只是个包装器。

其他常见 Linux 启动失败：

- `The profile appears to be in use by another Chromium process` 表示 Chrome 在受管 profile 目录发现了过期的 `Singleton*` 锁文件。锁指向已死或不同主机进程时 OpenClaw 移除锁并重试一次。
- `Missing X server or $DISPLAY` 表示在无桌面会话的主机上显式请求了可视浏览器。默认情况下,`DISPLAY` 和 `WAYLAND_DISPLAY` 都未设置时,本地受管 profile 在 Linux 回退到无头模式。如果设了 `OPENCLAW_BROWSER_HEADLESS=0`、`browser.headless: false` 或 `browser.profiles.<name>.headless: false`,移除该 headed 覆盖、设 `OPENCLAW_BROWSER_HEADLESS=1`、启动 `Xvfb`、运行 `openclaw browser start --headless` 做单次受管启动,或在真实桌面会话中运行 OpenClaw。

### 方案 1：安装 Google Chrome（推荐）

> Install the official Google Chrome `.deb` package...

安装不受 Snap 沙箱限制的官方 Google Chrome `.deb` 包：

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y  # 依赖错误时
```

然后更新 OpenClaw 配置（`~/.openclaw/openclaw.json`）：

```json
{
  "browser": {
    "enabled": true,
    "executablePath": "/usr/bin/google-chrome-stable",
    "headless": true,
    "noSandbox": true
  }
}
```

### 方案 2：Snap Chromium + Attach-Only 模式

> If you must use snap Chromium, configure OpenClaw to attach to a manually-started browser:

必须用 Snap Chromium 时,配置 OpenClaw 附加到手动启动的浏览器：

1. 更新配置：

```json
{
  "browser": {
    "enabled": true,
    "attachOnly": true,
    "headless": true,
    "noSandbox": true
  }
}
```

2. 手动启动 Chromium：

```bash
chromium-browser --headless --no-sandbox --disable-gpu \
  --remote-debugging-port=18800 \
  --user-data-dir=$HOME/.openclaw/browser/openclaw/user-data \
  about:blank &
```

3. 可选创建 systemd 用户服务自动启动 Chrome：

```ini
# ~/.config/systemd/user/openclaw-browser.service
[Unit]
Description=OpenClaw Browser (Chrome CDP)
After=network.target

[Service]
ExecStart=/snap/bin/chromium --headless --no-sandbox --disable-gpu --remote-debugging-port=18800 --user-data-dir=%h/.openclaw/browser/openclaw/user-data about:blank
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

启用：`systemctl --user enable --now openclaw-browser.service`

### 验证浏览器工作正常

检查状态：

```bash
curl -s http://127.0.0.1:18791/ | jq '{running, pid, chosenBrowser}'
```

测试浏览：

```bash
curl -s -X POST http://127.0.0.1:18791/start
curl -s http://127.0.0.1:18791/tabs
```

### 配置参考

| 选项                             | 说明                                                    | 默认                                                        |
| -------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------- |
| `browser.enabled`                | 启用浏览器控制                                          | `true`                                                      |
| `browser.executablePath`         | Chromium 系浏览器二进制路径（Chrome/Brave/Edge/Chromium）| 自动检测（Chromium 系时优先默认浏览器）                      |
| `browser.headless`               | 无 GUI 运行                                             | `false`                                                     |
| `OPENCLAW_BROWSER_HEADLESS`      | 本地受管浏览器无头模式的进程级覆盖                      | 未设置                                                      |
| `browser.noSandbox`              | 添加 `--no-sandbox` 标志（部分 Linux 设置需要）         | `false`                                                     |
| `browser.attachOnly`             | 不启动浏览器,只附加已有                                 | `false`                                                     |
| `browser.cdpPort`                | Chrome DevTools Protocol 端口                           | `18800`                                                     |
| `browser.localLaunchTimeoutMs`   | 本地受管 Chrome 发现超时                                | `15000`                                                     |
| `browser.localCdpReadyTimeoutMs` | 本地受管启动后 CDP 就绪超时                             | `8000`                                                      |

树莓派、旧 VPS 或慢存储上,Chrome 需更多时间暴露 CDP HTTP 端点时提高 `browser.localLaunchTimeoutMs`。启动成功但 `openclaw browser start` 仍报 `not reachable after start` 时提高 `browser.localCdpReadyTimeoutMs`。值须为不超过 `120000` ms 的正整数；无效配置值被拒绝。

### 问题："No Chrome tabs found for profile=\"user\""

> You're using an `existing-session` / Chrome MCP profile...

你在用 `existing-session` / Chrome MCP profile。OpenClaw 能看到本地 Chrome,但没有可附加的打开标签页。

修复选项：

1. **用受管浏览器：** `openclaw browser start --browser-profile openclaw`（或设 `browser.defaultProfile: "openclaw"`）。
2. **用 Chrome MCP：** 确保本地 Chrome 运行且至少有一个打开标签页,然后用 `--browser-profile user` 重试。

注意：

- `user` 仅限宿主。Linux 服务器、容器或远程主机优先用 CDP profile。
- `user` / 其他 `existing-session` profile 保持当前 Chrome MCP 限制：ref 驱动操作、单文件上传钩子、无对话框超时覆盖、无 `wait --load networkidle`、无 `responsebody`、PDF 导出、下载拦截或批量操作。
- 本地 `openclaw` profile 自动分配 `cdpPort`/`cdpUrl`；只对远程 CDP 设置它们。
- 远程 CDP profile 接受 `http://`、`https://`、`ws://` 和 `wss://`。HTTP(S) 用于 `/json/version` 发现,WS(S) 用于浏览器服务给你直接 DevTools socket URL 时。

## 相关

- [Browser](/tools/browser)
- [Browser login](/tools/browser-login)
- [Browser WSL2 故障排查](/tools/browser-wsl2-windows-remote-cdp-troubleshooting)
