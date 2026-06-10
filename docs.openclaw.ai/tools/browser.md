# Browser

## 架构精读

> 跳过不影响阅读翻译正文。

### Agent 怎么用浏览器又不碰你的账号？

两个字：隔离。OpenClaw 给 agent 一个**完全独立的 Chrome profile**——独立 user data 目录、独立端口、独立生命周期。跟 Docker 容器化你的应用是一个思路：你不会让生产 app 跑在你的日常开发环境里。

profile 抽象层是最优雅的设计。`openclaw`（受管隔离）、`user`（接入你真实浏览器）、`remote`（远程 CDP）三种完全不同的连接模式,但 agent 只看到一个 `browser` 工具加 ref ID。跟数据库连接池一样——应用不关心连接来自主库还是从库,只管用。

安全上有两层独立检查：**控制面可达性**（CDP 端口能不能连上）和**数据面策略**（这个 URL 允不允许导航）。`start` 成功不代表 `open` 就行,这跟 Kubernetes 的就绪探针和存活探针是一回事——活着不等于能接流量。SSRF 策略默认失败即拒绝,你要显式放行才能访内网。

ref 机制让 agent 操作确定性。snapshot 返回稳定 ref ID,agent 用 ref 点击 / 输入,不用脆弱的 CSS selector。就像 React 用 key 而不是 `document.querySelector`——抽象层吸收了 DOM 变化。

---

> OpenClaw can run a dedicated Chrome/Brave/Edge/Chromium profile that the agent controls...

OpenClaw 可以运行一个 agent 控制的**专属 Chrome/Brave/Edge/Chromium profile**。它跟你的个人浏览器隔离,通过 Gateway 内的小型本地控制服务管理（仅回环）。

初学者视角:

- 把它想成一个**独立的、仅 agent 使用的浏览器**。
- `openclaw` profile **不**碰你的个人浏览器 profile。
- agent 能在安全通道中**开标签页、读页面、点击、输入**。
- 内置 `user` profile 通过 Chrome MCP 接入你真实的已登录 Chrome session。

## 你得到什么

> What you get

- 一个名为 **openclaw** 的独立浏览器 profile（默认橙色主题）。
- 确定性标签页控制（列表 / 打开 / 聚焦 / 关闭）。
- Agent 操作（点击 / 输入 / 拖拽 / 选择）、快照、截图、PDF。
- 内置 `browser-automation` 技能,在浏览器插件启用时教 agent 快照、稳定标签页、过期 ref、手动阻断恢复循环。
- 可选多 profile 支持（`openclaw`、`work`、`remote`……）。

> This browser is not your daily driver...

此浏览器**不是**你的日常工具。是 agent 自动化和验证的安全隔离表面。

## 快速开始

> Quick start

```bash
openclaw browser --browser-profile openclaw doctor
openclaw browser --browser-profile openclaw doctor --deep
openclaw browser --browser-profile openclaw status
openclaw browser --browser-profile openclaw start
openclaw browser --browser-profile openclaw open https://example.com
openclaw browser --browser-profile openclaw snapshot
```

> If you get "Browser disabled"...

出现 "Browser disabled" 时在配置中启用（见下文）并重启 Gateway。

`openclaw browser` 命令整个不存在,或 agent 说浏览器工具不可用时,跳到 [Missing browser command or tool](/tools/browser#missing-browser-command-or-tool)。

## 插件控制

> Plugin control

默认 `browser` 工具是内置插件。禁用它以换成注册相同 `browser` 工具名的另一插件:

```json5
{
  plugins: {
    entries: {
      browser: {
        enabled: false,
      },
    },
  },
}
```

> Defaults need both `plugins.entries.browser.enabled` and `browser.enabled=true`...

默认需要 `plugins.entries.browser.enabled` **和** `browser.enabled=true` 都满足。只禁用插件会整体移除 `openclaw browser` CLI、`browser.request` gateway 方法、agent 工具和控制服务;`browser.*` 配置保留给替代品。

浏览器配置变更需要 Gateway 重启让插件重新注册服务。

## Agent 引导

> Agent guidance

工具 profile 注意：`tools.profile: "coding"` 含 `web_search` 和 `web_fetch`,但不含完整 `browser` 工具。agent 或子 agent 要用浏览器自动化时,在 profile 阶段加:

```json5
{
  tools: {
    profile: "coding",
    alsoAllow: ["browser"],
  },
}
```

> For a single agent...

单 agent 用 `agents.list[].tools.alsoAllow: ["browser"]`。`tools.subagents.tools.allow: ["browser"]` 单独不够,因为 sub-agent 策略在 profile 过滤后才应用。

浏览器插件附带两层 agent 引导:

- `browser` 工具描述带紧凑的始终在线契约：选对 profile、ref 保持同一标签页、用 `tabId`/label 定位标签页、多步工作加载浏览器技能。
- 内置 `browser-automation` 技能带更长的操作循环：先查状态 / 标签页、标记任务标签页、操作前快照、UI 变更后重新快照、过期 ref 恢复一次、登录/2FA/验证码或摄像头/麦克风阻断报为手动操作而非猜测。

> Plugin-bundled skills are listed in the agent's available skills...

插件启用时插件附带的技能出现在 agent 的可用技能列表中。完整技能指令按需加载,日常轮次不付全量 token 开销。

## 缺失浏览器命令或工具

> Missing browser command or tool

升级后 `openclaw browser` 未知、`browser.request` 缺失、或 agent 报浏览器工具不可用时,通常是 `plugins.allow` 列表遗漏 `browser` 且无根 `browser` 配置块。加上:

```json5
{
  plugins: {
    allow: ["telegram", "browser"],
  },
}
```

> An explicit root `browser` block...

显式的根 `browser` 块（如 `browser.enabled=true` 或 `browser.profiles.<name>`）即使在限制性 `plugins.allow` 下也激活内置浏览器插件,跟通道配置行为一致。`plugins.entries.browser.enabled=true` 和 `tools.alsoAllow: ["browser"]` 本身不能代替白名单成员资格。完全移除 `plugins.allow` 也恢复默认。

## Profile：`openclaw` vs `user`

> Profiles: openclaw vs user

- `openclaw`：受管隔离浏览器（无需扩展）。
- `user`：内置 Chrome MCP 接入 profile,连你**真实已登录的 Chrome** session。

agent 浏览器工具调用:

- 默认：用隔离的 `openclaw` 浏览器。
- 需要已有登录 session 且用户在电脑前能点击 / 批准接入提示时,优选 `profile="user"`。
- `profile` 是想要特定浏览器模式时的显式覆盖。

想默认受管模式设 `browser.defaultProfile: "openclaw"`。

## 配置

> Configuration

浏览器设置在 `~/.openclaw/openclaw.json`。

```json5
{
  browser: {
    enabled: true, // 默认: true
    ssrfPolicy: {
      // dangerouslyAllowPrivateNetwork: true, // 仅受信私网访问时 opt in
      // hostnameAllowlist: ["*.example.com", "example.com"],
      // allowedHostnames: ["localhost"],
    },
    remoteCdpTimeoutMs: 1500, // 远程 CDP HTTP 超时 (ms)
    remoteCdpHandshakeTimeoutMs: 3000, // 远程 CDP WebSocket 握手超时 (ms)
    localLaunchTimeoutMs: 15000, // 本地受管 Chrome 发现超时 (ms)
    localCdpReadyTimeoutMs: 8000, // 本地受管启动后 CDP 就绪超时 (ms)
    actionTimeoutMs: 60000, // 默认浏览器 act 超时 (ms)
    tabCleanup: {
      enabled: true, // 默认: true
      idleMinutes: 120, // 设 0 禁用空闲清理
      maxTabsPerSession: 8, // 设 0 禁用逐 session 上限
      sweepMinutes: 5,
    },
    defaultProfile: "openclaw",
    color: "#FF4500",
    headless: false,
    noSandbox: false,
    attachOnly: false,
    executablePath: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    profiles: {
      openclaw: { cdpPort: 18800, color: "#FF4500" },
      work: {
        cdpPort: 18801,
        color: "#0066CC",
        headless: true,
        executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      },
      user: {
        driver: "existing-session",
        attachOnly: true,
        color: "#00AA00",
      },
      brave: {
        driver: "existing-session",
        attachOnly: true,
        userDataDir: "~/Library/Application Support/BraveSoftware/Brave-Browser",
        color: "#FB542B",
      },
      remote: { cdpUrl: "http://10.0.0.42:9222", color: "#00AA00" },
    },
  },
}
```

### 截图视觉（纯文本模型支持）

> Screenshot vision (text-only model support)

主模型是纯文本（无视觉 / 多模态支持）时,浏览器截图返回模型无法读取的图片块。浏览器截图复用已有的图像理解配置,配了媒体理解的图像模型能把截图描述为文本,无需浏览器专属模型设置。

```json5
{
  tools: {
    media: {
      image: {
        models: [
          { provider: "bytedance", model: "doubao-seed-2.0-pro" },
          { provider: "openai", model: "gpt-4o" },
        ],
      },
    },
  },
}
```

**工作方式:**

1. Agent 调 `browser screenshot` → 图片照常捕获到磁盘。
2. 浏览器工具问已有图像理解运行时能否用配置的媒体图像模型描述截图。
3. 视觉模型返回文本描述,用 `wrapExternalContent`（prompt 注入防护）包装后作为文本块返回给 agent。
4. 图像理解不可用、跳过、或失败时,回退返回原始图片块。

> Use the existing `tools.media.image` / `tools.media.models` fields...

用已有 `tools.media.image` / `tools.media.models` 字段做模型回退、超时、字节限制、profile、provider 请求设置。

活跃主模型已支持视觉且没配显式图像理解模型时,OpenClaw 保留正常图片结果让主模型直接读截图。

### 端口和可达性

> Ports and reachability

- 控制服务在从 `gateway.port` 导出的端口上绑定回环（默认 `18791` = gateway + 2）。覆盖 `gateway.port` 或 `OPENCLAW_GATEWAY_PORT` 同族移动导出端口。
- 本地 `openclaw` profile 自动分配 `cdpPort`/`cdpUrl`;只为远程 CDP 设它们。未设时 `cdpUrl` 默认到受管本地 CDP 端口。
- `remoteCdpTimeoutMs` 应用于远程和 `attachOnly` CDP HTTP 可达性检查和标签页打开 HTTP 请求;`remoteCdpHandshakeTimeoutMs` 应用于其 CDP WebSocket 握手。
- `localLaunchTimeoutMs` 是本地启动的受管 Chrome 进程暴露 CDP HTTP 端点的预算。`localCdpReadyTimeoutMs` 是进程发现后 CDP websocket 就绪的后续预算。树莓派、低配 VPS、或旧硬件上 Chromium 启动慢时提高这些值。值须为正整数,上限 `120000` ms;无效值被拒绝。
- 重复的受管 Chrome 启动 / 就绪失败按 profile 做断路。连续多次失败后 OpenClaw 短暂暂停新启动尝试而非每次浏览器工具调用都启动 Chromium。修启动问题、不需要时禁用浏览器、或修复后重启 Gateway。
- `actionTimeoutMs` 是调用者不传 `timeoutMs` 时浏览器 `act` 请求的默认预算。客户端传输加一小段松弛窗口让长等待能完成而非在 HTTP 边界超时。
- `tabCleanup` 是主 agent 浏览器 session 打开的标签页的尽力清理。Sub-agent、cron、ACP 生命周期清理仍在 session 结束时关闭显式跟踪的标签页;主 session 保持活跃标签页可复用,后台关闭空闲或超额的已跟踪标签页。

### SSRF 策略

> SSRF policy

- 浏览器导航和 open-tab 在导航前做 SSRF 防护,最终 `http(s)` URL 之后尽力复查。
- 严格 SSRF 模式下远程 CDP 端点发现和 `/json/version` 探测（`cdpUrl`）也被检查。
- Gateway/provider 的 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`NO_PROXY` 环境变量不自动代理 OpenClaw 受管浏览器。受管 Chrome 默认直连启动,provider 代理设置不削弱浏览器 SSRF 检查。
- OpenClaw 受管本地 CDP 就绪探测和 DevTools WebSocket 连接对精确启动的回环端点绕过受管网络代理,所以运营者代理阻止回环出口时 `openclaw browser start` 仍工作。
- 要代理受管浏览器本身,通过 `browser.extraArgs` 传显式 Chrome 代理标志如 `--proxy-server=...` 或 `--proxy-pac-url=...`。严格 SSRF 模式阻止显式浏览器代理路由,除非有意启用了私网浏览器访问。
- `browser.ssrfPolicy.dangerouslyAllowPrivateNetwork` 默认关;仅在有意受信且已审查私网浏览器访问的环境启用。
- `browser.ssrfPolicy.allowPrivateNetwork` 作为旧别名仍支持。

### Profile 行为

> Profile behavior

- `attachOnly: true` 意味从不启动本地浏览器;仅在已有运行时接入。
- `headless` 可全局设或逐本地受管 profile 设。逐 profile 值覆盖 `browser.headless`,一个本地启动的 profile 可 headless 另一个保持可见。
- `POST /start?headless=true` 和 `openclaw browser start --headless` 对本地受管 profile 请求一次性 headless 启动而不改写 `browser.headless` 或 profile 配置。existing-session、attach-only、远程 CDP profile 拒绝覆盖因为 OpenClaw 不启动那些浏览器进程。
- Linux 宿主无 `DISPLAY` 或 `WAYLAND_DISPLAY` 时,环境或 profile/全局配置都没显式选 headed 模式的本地受管 profile 默认自动 headless。`openclaw browser status --json` 报告 `headlessSource`。
- `OPENCLAW_BROWSER_HEADLESS=1` 强制当前进程本地受管启动 headless。`=0` 强制 headed 模式。
- `executablePath` 可全局或逐本地受管 profile 设。逐 profile 值覆盖 `browser.executablePath`,不同受管 profile 可启动不同 Chromium 系浏览器。两种形式接受 `~` 表示 OS 主目录。
- `color`（顶层和逐 profile）给浏览器 UI 着色,看得出哪个 profile 活跃。
- 默认 profile 是 `openclaw`（受管独立）。用 `defaultProfile: "user"` opt-in 到已登录用户浏览器。
- 自动检测顺序：系统默认浏览器（如果基于 Chromium）;否则 Chrome → Brave → Edge → Chromium → Chrome Canary。
- `driver: "existing-session"` 用 Chrome DevTools MCP 而非原始 CDP。该 driver 不设 `cdpUrl`。
- `browser.profiles.<name>.userDataDir` 在 existing-session profile 应接入非默认 Chromium 用户 profile（Brave、Edge 等）时设。路径也接受 `~`。

## 用 Brave 或其他 Chromium 系浏览器

> Use Brave or another Chromium-based browser

**系统默认**浏览器是 Chromium 系时 OpenClaw 自动使用。设 `browser.executablePath` 覆盖自动检测。顶层和逐 profile 的 `executablePath` 接受 `~`:

```bash
openclaw config set browser.executablePath "/usr/bin/google-chrome"
openclaw config set browser.profiles.work.executablePath "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

或在配置中按平台设:

macOS:
```json5
{ browser: { executablePath: "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" } }
```

Windows:
```json5
{ browser: { executablePath: "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" } }
```

Linux:
```json5
{ browser: { executablePath: "/usr/bin/brave-browser" } }
```

> Per-profile `executablePath` only affects local managed profiles...

逐 profile `executablePath` 只影响 OpenClaw 启动的本地受管 profile。`existing-session` profile 接入已运行浏览器,远程 CDP profile 用 `cdpUrl` 后的浏览器。

## 本地 vs 远程控制

> Local vs remote control

- **本地控制（默认）:** Gateway 启动回环控制服务并可启动本地浏览器。
- **远程控制（节点宿主）:** 在有浏览器的机器上跑节点宿主;Gateway 把浏览器操作代理给它。
- **远程 CDP:** 设 `browser.profiles.<name>.cdpUrl`（或 `browser.cdpUrl`）接入远程 Chromium 系浏览器。此时 OpenClaw 不启动本地浏览器。
- 回环上外部管理的 CDP 服务（如 Docker 发布到 `127.0.0.1` 的 Browserless）也设 `attachOnly: true`。无 `attachOnly` 的回环 CDP 被视为本地 OpenClaw 受管浏览器 profile。
- `headless` 只影响 OpenClaw 启动的本地受管 profile。不重启或改变 existing-session 或远程 CDP 浏览器。
- `executablePath` 遵循同样的本地受管 profile 规则。运行中的本地受管 profile 上改它会标记该 profile 待重启 / 协调,下次启动用新二进制。

停止行为按 profile 模式不同:

- 本地受管 profile：`openclaw browser stop` 停止 OpenClaw 启动的浏览器进程
- attach-only 和远程 CDP profile：`openclaw browser stop` 关闭活跃控制 session 并释放 Playwright/CDP 仿真覆盖（viewport、配色方案、locale、时区、离线模式等状态）,即使 OpenClaw 没启动浏览器进程

> Remote CDP URLs can include auth...

远程 CDP URL 可含认证:

- 查询 token（如 `https://provider.example?token=<token>`）
- HTTP Basic auth（如 `https://user:pass@provider.example`）

OpenClaw 在调 `/json/*` 端点和连 CDP WebSocket 时保留认证。token 优选环境变量或密钥管理器而非提交到配置文件。

## 节点浏览器代理（零配置默认）

> Node browser proxy (zero-config default)

在有浏览器的机器上跑**节点宿主**时,OpenClaw 可以无需额外浏览器配置就自动路由浏览器工具调用到该节点。这是远程 gateway 的默认路径。

注意:

- 节点宿主通过**代理命令**暴露本地浏览器控制服务器。
- Profile 来自节点自己的 `browser.profiles` 配置（跟本地一样）。
- `nodeHost.browserProxy.allowProfiles` 可选。留空为旧 / 默认行为：所有配置的 profile 通过代理可达,含 profile 创建 / 删除路由。
- 设了 `allowProfiles` 时 OpenClaw 视其为最小权限边界：只有白名单 profile 可被访问,持久 profile 创建 / 删除路由在代理面被阻止。
- 不需要时禁用:
  - 节点上：`nodeHost.browserProxy.enabled=false`
  - Gateway 上：`gateway.nodes.browser.mode="off"`

## Browserless（托管远程 CDP）

> Browserless (hosted remote CDP)

[Browserless](https://browserless.io) 是通过 HTTPS 和 WebSocket 暴露 CDP 连接 URL 的托管 Chromium 服务。OpenClaw 两种形式都接受,但远程浏览器 profile 最简选项是 Browserless 连接文档中的直接 WebSocket URL。

示例:

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "browserless",
    remoteCdpTimeoutMs: 2000,
    remoteCdpHandshakeTimeoutMs: 4000,
    profiles: {
      browserless: {
        cdpUrl: "wss://production-sfo.browserless.io?token=BROWSERLESS_API_KEY",
        color: "#00AA00",
      },
    },
  },
}
```

注意:

- 把 `BROWSERLESS_API_KEY` 换成你真实的 Browserless token。
- 选匹配你 Browserless 账户的地区端点。
- Browserless 给的是 HTTPS 基础 URL 时,可以转成 `wss://` 做直接 CDP 连接,或保留 HTTPS URL 让 OpenClaw 发现 `/json/version`。

### 同宿主 Docker 中的 Browserless

> Browserless Docker on the same host

Browserless 在 Docker 自托管且 OpenClaw 跑在宿主上时,把 Browserless 当外部管理的 CDP 服务:

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "browserless",
    profiles: {
      browserless: {
        cdpUrl: "ws://127.0.0.1:3000",
        attachOnly: true,
        color: "#00AA00",
      },
    },
  },
}
```

> The address in `browser.profiles.browserless.cdpUrl` must be reachable...

`cdpUrl` 中的地址必须从 OpenClaw 进程可达。Browserless 也须广告匹配的可达端点;设 Browserless `EXTERNAL` 为同一个对 OpenClaw 公开的 WebSocket 基址。`/json/version` 返回 OpenClaw 不可达的 `webSocketDebuggerUrl` 时,CDP HTTP 看着健康但 WebSocket 接入仍失败。

回环 Browserless profile 不要漏设 `attachOnly`。无 `attachOnly` 时 OpenClaw 把回环端口当本地受管浏览器 profile,可能报端口被占用但不归 OpenClaw。

## 直接 WebSocket CDP 提供商

> Direct WebSocket CDP providers

有些托管浏览器服务暴露**直接 WebSocket** 端点而非标准基于 HTTP 的 CDP 发现（`/json/version`）。OpenClaw 接受三种 CDP URL 形状并自动选对的连接策略:

- **HTTP(S) 发现** —— `http://host[:port]` 或 `https://host[:port]`。OpenClaw 调 `/json/version` 发现 WebSocket debugger URL 然后连。无 WebSocket 回退。
- **直接 WebSocket 端点** —— `ws://host[:port]/devtools/<kind>/<id>` 或 `wss://...` 带 `/devtools/browser|page|worker|.../<id>` 路径。OpenClaw 直接 WebSocket 握手,完全跳过 `/json/version`。
- **裸 WebSocket 根** —— `ws://host[:port]` 或 `wss://host[:port]` 无 `/devtools/...` 路径（如 Browserless、Browserbase）。OpenClaw 先试 HTTP `/json/version` 发现;发现返回 `webSocketDebuggerUrl` 时用它,否则回退到裸根直接 WebSocket 握手。

> `openclaw browser doctor` uses the same discovery-first, WebSocket-fallback logic...

`openclaw browser doctor` 用跟运行时接入同样的发现优先、WebSocket 回退逻辑,裸根 URL 连接成功时诊断不报不可达。

### Browserbase

> Browserbase

[Browserbase](https://www.browserbase.com) 是带内置验证码解决、隐身模式、住宅代理的云平台。

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "browserbase",
    remoteCdpTimeoutMs: 3000,
    remoteCdpHandshakeTimeoutMs: 5000,
    profiles: {
      browserbase: {
        cdpUrl: "wss://connect.browserbase.com?apiKey=BROWSERBASE_API_KEY",
        color: "#F97316",
      },
    },
  },
}
```

### Notte

> Notte

[Notte](https://www.notte.cc) 是带内置隐身、住宅代理和 CDP 原生 WebSocket 网关的云平台。

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "notte",
    remoteCdpTimeoutMs: 3000,
    remoteCdpHandshakeTimeoutMs: 5000,
    profiles: {
      notte: {
        cdpUrl: "wss://us-prod.notte.cc/sessions/connect?token=NOTTE_API_KEY",
        color: "#7C3AED",
      },
    },
  },
}
```

## 安全

> Security

关键点:

- 浏览器控制仅回环;访问经 Gateway 认证或节点配对。
- 独立回环浏览器 HTTP API 仅用**共享密钥认证**：gateway token bearer auth、`x-openclaw-password`、或用配置的 gateway 密码的 HTTP Basic auth。
- Tailscale Serve 身份头和 `gateway.auth.mode: "trusted-proxy"` **不**认证此独立回环浏览器 API。
- 浏览器控制启用且无共享密钥认证配置时,OpenClaw 为该次启动生成仅运行时 gateway token。需跨重启稳定密钥时显式配 `gateway.auth.token`、`gateway.auth.password`、`OPENCLAW_GATEWAY_TOKEN`、或 `OPENCLAW_GATEWAY_PASSWORD`。
- `gateway.auth.mode` 已是 `password`、`none`、或 `trusted-proxy` 时 OpenClaw **不**自动生成该 token。
- Gateway 和节点宿主放在私网（Tailscale）上;避免公网暴露。
- 远程 CDP URL/token 当密钥对待;优选环境变量或密钥管理器。

远程 CDP 建议:

- 尽量用加密端点（HTTPS 或 WSS）和短生命期 token。
- 避免在配置文件中直接嵌入长期 token。

## Profile（多浏览器）

> Profiles (multi-browser)

OpenClaw 支持多个命名 profile（路由配置）。Profile 可以是:

- **openclaw 受管**: 有自己 user data 目录 + CDP 端口的专属 Chromium 系浏览器实例
- **远程**: 显式 CDP URL（跑在别处的 Chromium 系浏览器）
- **existing session**: 通过 Chrome DevTools MCP 自动连接的你已有 Chrome profile

默认:

- 缺失时自动创建 `openclaw` profile。
- `user` profile 内置用于 Chrome MCP existing-session 接入。
- `user` 之外的 existing-session profile 是 opt-in;用 `--driver existing-session` 创建。
- 本地 CDP 端口默认从 **18800-18899** 分配。
- 删除 profile 把其本地数据目录移到废纸篓。

所有控制端点接受 `?profile=<name>`;CLI 用 `--browser-profile`。

## 通过 Chrome DevTools MCP 的 existing session

> Existing session via Chrome DevTools MCP

OpenClaw 也能通过官方 Chrome DevTools MCP 服务器接入运行中的 Chromium 系浏览器 profile。这复用该浏览器 profile 中已打开的标签页和登录状态。

内置 profile：`user`

可选：想要不同名字、颜色、或浏览器数据目录时创建自定义 existing-session profile。

默认行为：内置 `user` profile 用 Chrome MCP 自动连接,目标是默认本地 Google Chrome profile。

Brave、Edge、Chromium、或非默认 Chrome profile 用 `userDataDir`。`~` 展开为 OS 主目录:

```json5
{
  browser: {
    profiles: {
      brave: {
        driver: "existing-session",
        attachOnly: true,
        userDataDir: "~/Library/Application Support/BraveSoftware/Brave-Browser",
        color: "#FB542B",
      },
    },
  },
}
```

然后在匹配的浏览器中:

1. 打开该浏览器的远程调试 inspect 页面。
2. 启用远程调试。
3. 保持浏览器运行,OpenClaw 接入时批准连接提示。

常见 inspect 页面:

- Chrome: `chrome://inspect/#remote-debugging`
- Brave: `brave://inspect/#remote-debugging`
- Edge: `edge://inspect/#remote-debugging`

实时接入冒烟测试:

```bash
openclaw browser --browser-profile user start
openclaw browser --browser-profile user status
openclaw browser --browser-profile user tabs
openclaw browser --browser-profile user snapshot --format ai
```

成功的样子:

- `status` 显示 `driver: existing-session`
- `status` 显示 `transport: chrome-mcp`
- `status` 显示 `running: true`
- `tabs` 列出你已打开的浏览器标签页
- `snapshot` 返回选中活标签页的 ref

接入不工作时检查:

- 目标 Chromium 系浏览器版本 `144+`
- 该浏览器 inspect 页面中启用了远程调试
- 浏览器显示了且你接受了接入同意提示
- `openclaw doctor` 迁移旧的扩展式浏览器配置并检查默认自动连接 profile 的 Chrome 本地安装,但不能替你启用浏览器侧远程调试

Agent 使用:

- 需要用户已登录浏览器状态时用 `profile="user"`。
- 用自定义 existing-session profile 时传该显式 profile 名。
- 仅用户在电脑前能批准接入提示时选此模式。
- Gateway 或节点宿主可启动 `npx chrome-devtools-mcp@latest --autoConnect`

注意:

- 此路径比隔离的 `openclaw` profile 风险更高,因为能在你已登录的浏览器 session 内操作。
- OpenClaw 不为此 driver 启动浏览器;仅接入。
- OpenClaw 此处用官方 Chrome DevTools MCP `--autoConnect` 流。设了 `userDataDir` 时传递给它以定位该 user data 目录。
- Existing-session 可在选中宿主或通过已连浏览器节点接入。Chrome 在别处且无浏览器节点连接时,用远程 CDP 或节点宿主。

### 自定义 Chrome MCP 启动

> Custom Chrome MCP launch

默认 `npx chrome-devtools-mcp@latest` 流不合适时（离线宿主、固定版本、打包二进制）逐 profile 覆盖启动的 Chrome DevTools MCP 服务器:

| 字段         | 作用                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------- |
| `mcpCommand` | 代替 `npx` 启动的可执行文件。按原样解析;绝对路径被尊重。                                |
| `mcpArgs`    | 传给 `mcpCommand` 的参数数组。替换默认 `chrome-devtools-mcp@latest --autoConnect` 参数。 |

existing-session profile 设了 `cdpUrl` 时,OpenClaw 跳过 `--autoConnect` 并自动把端点转发给 Chrome MCP:

- `http(s)://...` → `--browserUrl <url>`（DevTools HTTP 发现端点）。
- `ws(s)://...` → `--wsEndpoint <url>`（直接 CDP WebSocket）。

端点标志和 `userDataDir` 不能组合：设了 `cdpUrl` 时 Chrome MCP 启动忽略 `userDataDir`,因为 Chrome MCP 接入端点后的运行浏览器而非打开 profile 目录。

### Existing-session 功能限制

> Existing-session feature limitations

跟受管 `openclaw` profile 相比,existing-session driver 更受限:

- **截图** —— 页面捕获和 `--ref` 元素捕获工作;CSS `--element` selector 不支持。`--full-page` 不能跟 `--ref` 或 `--element` 组合。
- **操作** —— `click`、`type`、`hover`、`scrollIntoView`、`drag`、`select` 需要快照 ref（无 CSS selector）。`click-coords` 点击可见视口坐标不需 snapshot ref。`click` 仅左键。`type` 不支持 `slowly=true`;用 `fill` 或 `press`。`press` 不支持 `delayMs`。部分操作不支持逐调超时。`select` 接受单值。
- **等待 / 上传 / 对话框** —— `wait --url` 支持精确、子串、glob 模式;不支持 `wait --load networkidle`。上传钩子需 `ref` 或 `inputRef`,一次一个文件。对话框钩子不支持超时覆盖或 `dialogId`。
- **对话框可见性** —— 受管浏览器操作响应在操作打开模态对话框时含 `blockedByDialog` 和 `browserState.dialogs.pending`;快照也含待处理对话框状态。对话框待处理时用 `browser dialog --accept/--dismiss --dialog-id <id>` 响应。
- **仅受管功能** —— 批量操作、PDF 导出、下载拦截、`responsebody` 仍需受管浏览器路径。

## 隔离保证

> Isolation guarantees

- **专属 user data 目录**: 永不碰你的个人浏览器 profile。
- **专属端口**: 避免 `9222` 防跟开发工作流冲突。
- **确定性标签页控制**: `tabs` 先返回 `suggestedTargetId`,再稳定 `tabId` 句柄如 `t1`、可选 label、原始 `targetId`。Agent 应复用 `suggestedTargetId`;原始 id 留做调试和兼容。

## 浏览器选择

> Browser selection

本地启动时 OpenClaw 选第一个可用的:

1. Chrome
2. Brave
3. Edge
4. Chromium
5. Chrome Canary

可用 `browser.executablePath` 覆盖。

平台:

- macOS: 检查 `/Applications` 和 `~/Applications`。
- Linux: 检查 `/usr/bin`、`/snap/bin`、`/opt/google`、`/opt/brave.com`、`/usr/lib/chromium`、`/usr/lib/chromium-browser` 下常见位置,加 `PLAYWRIGHT_BROWSERS_PATH` 或 `~/.cache/ms-playwright` 下 Playwright 管理的 Chromium。
- Windows: 检查常见安装位置。

## 控制 API（可选）

> Control API (optional)

用于脚本和调试,Gateway 暴露小型**仅回环 HTTP 控制 API** 加匹配的 `openclaw browser` CLI（快照、ref、等待增强、JSON 输出、调试工作流）。见 [Browser control API](/tools/browser-control) 获取完整参考。

## 故障排查

> Troubleshooting

Linux 特有问题（尤其 snap Chromium）见 [Browser troubleshooting](/tools/browser-linux-troubleshooting)。

WSL2 Gateway + Windows Chrome 分宿主设置见 [WSL2 + Windows + remote Chrome CDP troubleshooting](/tools/browser-wsl2-windows-remote-cdp-troubleshooting)。

### CDP 启动失败 vs 导航 SSRF 阻止

> CDP startup failure vs navigation SSRF block

这是不同的失败类别,指向不同代码路径。

- **CDP 启动或就绪失败** 意味 OpenClaw 无法确认浏览器控制面健康。
- **导航 SSRF 阻止** 意味浏览器控制面健康,但页面导航目标被策略拒绝。

常见示例:

- CDP 启动或就绪失败:
  - `Chrome CDP websocket for profile "openclaw" is not reachable after start`
  - `Remote CDP for profile "<name>" is not reachable at <cdpUrl>`
  - `Port <port> is in use for profile "<name>" but not by openclaw`（回环外部 CDP 服务没设 `attachOnly: true` 时）
- 导航 SSRF 阻止:
  - `open`、`navigate`、snapshot 或标签页打开流失败返回浏览器 / 网络策略错误而 `start` 和 `tabs` 仍工作

用此最小序列分离两者:

```bash
openclaw browser --browser-profile openclaw start
openclaw browser --browser-profile openclaw tabs
openclaw browser --browser-profile openclaw open https://example.com
```

怎么读结果:

- `start` 以 `not reachable after start` 失败 → 先排查 CDP 可达性。
- `start` 成功但 `tabs` 失败 → 控制面仍不健康。视为 CDP 可达性问题,非页面导航问题。
- `start` 和 `tabs` 成功但 `open` 或 `navigate` 失败 → 浏览器控制面正常,失败在导航策略或目标页面。
- `start`、`tabs`、`open` 全成功 → 基本受管浏览器控制路径健康。

重要行为细节:

- 浏览器配置默认失败即拒绝的 SSRF 策略对象,即使你没配 `browser.ssrfPolicy`。
- 本地回环 `openclaw` 受管 profile 的 CDP 健康检查有意跳过浏览器 SSRF 可达性强制——针对 OpenClaw 自己的本地控制面。
- 导航保护是分开的。`start` 或 `tabs` 成功不代表之后的 `open` 或 `navigate` 目标被允许。

安全指引:

- 默认**不要**放松浏览器 SSRF 策略。
- 优选窄主机例外如 `hostnameAllowlist` 或 `allowedHostnames`,不要用宽泛私网访问。
- `dangerouslyAllowPrivateNetwork: true` 仅在有意受信且已审查私网浏览器访问的环境使用。

## Agent 工具 + 控制方式

> Agent tools + how control works

Agent 得到**一个工具**做浏览器自动化:

- `browser` —— doctor/status/start/stop/tabs/open/focus/close/snapshot/screenshot/navigate/act

怎么映射:

- `browser snapshot` 返回稳定 UI 树（AI 或 ARIA）。
- `browser act` 用快照 `ref` ID 做点击 / 输入 / 拖拽 / 选择。
- `browser screenshot` 捕获像素（全页、元素、或标记的 ref）。
- `browser doctor` 检查 Gateway、插件、profile、浏览器、标签页就绪性。
- `browser` 接受:
  - `profile` 选命名浏览器 profile（openclaw、chrome、或远程 CDP）。
  - `target`（`sandbox` | `host` | `node`）选浏览器在哪里。
  - 沙箱 session 中 `target: "host"` 需要 `agents.defaults.sandbox.browser.allowHostControl=true`。
  - 省略 `target` 时：沙箱 session 默认 `sandbox`,非沙箱 session 默认 `host`。
  - 浏览器能力节点连接时,工具可能自动路由到它,除非你钉住 `target="host"` 或 `target="node"`。

这让 agent 确定性,避免脆弱 selector。

## 相关

> Related

- [Tools Overview](/tools) —— 所有可用 agent 工具
- [Sandboxing](/gateway/sandboxing) —— 沙箱环境中的浏览器控制
- [Security](/gateway/security) —— 浏览器控制风险和加固
