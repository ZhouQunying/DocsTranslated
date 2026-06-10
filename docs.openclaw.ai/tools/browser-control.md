# Browser 控制 API

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么浏览器操控需要三套 ref 体系？

关键在于场景不同。AI snapshot 的数字 ref（`12`）用 Playwright 的 `aria-ref` 解析,适合 agent 自动化；role snapshot 的 `e12` 用 `getByRole()` 解析,适合按语义角色定位；ARIA snapshot 的 `ax12` 绑定 Chrome 后端 DOM ID,适合无障碍树检查。

三套 ref 背后是同一个设计原则：**把脆弱的 DOM 位置抽象成稳定 ID**。没有这层抽象,agent 每次页面变一点就得重新写 selector。但 ref 不跨导航——因为页面变了 DOM 树就全换了,强行维护旧 ref 只会造成幽灵点击。

Playwright 可选这个设计也很巧妙。没装 Playwright 时,CDP 直连仍能出快照、截图——降级到只读,不是完全不能用。这跟数据库"只读副本"思路一样：写操作（navigate/act）必须走主库（Playwright）,但读操作到处都能跑。

---

> For setup, configuration, and troubleshooting, see [Browser](/tools/browser).

设置、配置和故障排查见 [Browser](/tools/browser)。本页是本地控制 HTTP API、`openclaw browser` CLI 和脚本模式（快照、ref、等待、调试流程）的参考。

## 控制 API（可选）

> For local integrations only, the Gateway exposes a small loopback HTTP API:

仅用于本地集成,Gateway 暴露一个小型回环 HTTP API：

- 状态/启停：`GET /`、`POST /start`、`POST /stop`
- 标签页：`GET /tabs`、`POST /tabs/open`、`POST /tabs/focus`、`DELETE /tabs/:targetId`
- 快照/截图：`GET /snapshot`、`POST /screenshot`
- 操作：`POST /navigate`、`POST /act`
- 钩子：`POST /hooks/file-chooser`、`POST /hooks/dialog`
- 下载：`POST /download`、`POST /wait/download`
- 权限：`POST /permissions/grant`
- 调试：`GET /console`、`POST /pdf`
- 调试：`GET /errors`、`GET /requests`、`POST /trace/start`、`POST /trace/stop`、`POST /highlight`
- 网络：`POST /response/body`
- 状态：`GET /cookies`、`POST /cookies/set`、`POST /cookies/clear`
- 状态：`GET /storage/:kind`、`POST /storage/:kind/set`、`POST /storage/:kind/clear`
- 设置：`POST /set/offline`、`POST /set/headers`、`POST /set/credentials`、`POST /set/geolocation`、`POST /set/media`、`POST /set/timezone`、`POST /set/locale`、`POST /set/device`

> All endpoints accept `?profile=<name>`...

所有端点接受 `?profile=<name>`。`POST /start?headless=true` 为本地受管 profile 请求单次无头启动,不改持久化浏览器配置；attach-only、远程 CDP 和 existing-session profile 拒绝该覆盖,因为 OpenClaw 不启动那些浏览器进程。

> For tab endpoints, `targetId` is the compatibility field name...

对标签页端点,`targetId` 是兼容字段名。优先传 `GET /tabs` 或 `POST /tabs/open` 返回的 `suggestedTargetId`；标签和 `tabId` 句柄（如 `t1`）也被接受。原始 CDP target id 和唯一原始 target-id 前缀仍可用,但它们是易变的诊断句柄。

> If shared-secret gateway auth is configured...

配置了共享密钥网关认证时,浏览器 HTTP 路由也需认证：

- `Authorization: Bearer <gateway token>`
- `x-openclaw-password: <gateway password>` 或带该密码的 HTTP Basic auth

注意：

- 此独立回环浏览器 API **不**消费 trusted-proxy 或 Tailscale Serve 身份头。
- 若 `gateway.auth.mode` 为 `none` 或 `trusted-proxy`,这些回环浏览器路由不继承那些身份模式；保持仅回环。

### `/act` 错误契约

> `POST /act` uses a structured error response...

`POST /act` 对路由级验证和策略失败使用结构化错误响应：

```json
{ "error": "<message>", "code": "ACT_*" }
```

当前 `code` 值：

- `ACT_KIND_REQUIRED`（HTTP 400）：`kind` 缺失或不识别。
- `ACT_INVALID_REQUEST`（HTTP 400）：操作载荷规范化或验证失败。
- `ACT_SELECTOR_UNSUPPORTED`（HTTP 400）：`selector` 用于不支持的操作类型。
- `ACT_EVALUATE_DISABLED`（HTTP 403）：`evaluate`（或 `wait --fn`）被配置禁用。
- `ACT_TARGET_ID_MISMATCH`（HTTP 403）：顶层或批量 `targetId` 与请求目标冲突。
- `ACT_EXISTING_SESSION_UNSUPPORTED`（HTTP 501）：操作不支持 existing-session profile。

其他运行时失败可能仍返回无 `code` 字段的 `{ "error": "<message>" }`。

### Playwright 要求

> Some features (navigate/act/AI snapshot/role snapshot, element screenshots, PDF) require Playwright...

部分功能（navigate/act/AI snapshot/role snapshot、元素截图、PDF）需要 Playwright。未安装 Playwright 时这些端点返回明确的 501 错误。

无 Playwright 仍可用的：

- ARIA 快照
- 有 per-tab CDP WebSocket 时的角色式无障碍快照（`--interactive`、`--compact`、`--depth`、`--efficient`）。这是检查和 ref 发现的回退；Playwright 仍是主要操作引擎。
- 有 per-tab CDP WebSocket 时受管 `openclaw` 浏览器的页面截图
- `existing-session` / Chrome MCP profile 的页面截图
- `existing-session` 基于 ref 的截图（`--ref`）来自快照输出

仍需 Playwright 的：

- `navigate`
- `act`
- 依赖 Playwright 原生 AI 快照格式的 AI 快照
- CSS 选择器元素截图（`--element`）
- 完整浏览器 PDF 导出

元素截图还拒绝 `--full-page`；路由返回 `fullPage is not supported for element screenshots`。

> If you see `Playwright is not available in this gateway build`...

看到 `Playwright is not available in this gateway build` 说明打包的 Gateway 缺核心浏览器运行时依赖。重新安装或更新 OpenClaw 后重启 gateway。Docker 环境还需安装 Chromium 浏览器二进制。

#### Docker Playwright 安装

> If your Gateway runs in Docker, avoid `npx playwright`...

Gateway 在 Docker 中运行时避免 `npx playwright`（npm 覆盖冲突）。自定义镜像中将 Chromium 烘焙进镜像：

```bash
OPENCLAW_INSTALL_BROWSER=1 ./scripts/docker/setup.sh
```

已有镜像通过内置 CLI 安装：

```bash
docker compose run --rm openclaw-cli \
  node /app/node_modules/playwright-core/cli.js install chromium
```

持久化浏览器下载,设 `PLAYWRIGHT_BROWSERS_PATH`（例如 `/home/node/.cache/ms-playwright`）并确保 `/home/node` 通过 `OPENCLAW_HOME_VOLUME` 或 bind mount 持久化。OpenClaw 在 Linux 自动检测持久化的 Chromium。见 [Docker](/install/docker)。

## 工作原理（内部）

> A small loopback control server accepts HTTP requests and connects to Chromium-based browsers via CDP...

小型回环控制服务器接受 HTTP 请求,经 CDP 连接 Chromium 系浏览器。高级操作（click/type/snapshot/PDF）走 CDP 上层的 Playwright；缺 Playwright 时只有非 Playwright 操作可用。Agent 看到一个稳定接口,底层本地/远程浏览器和 profile 自由切换。

## CLI 快速参考

所有命令接受 `--browser-profile <name>` 指定 profile,`--json` 获取机器可读输出。

基础：状态、标签页、打开/聚焦/关闭

```bash
openclaw browser status
openclaw browser start
openclaw browser start --headless # 单次本地受管无头启动
openclaw browser stop            # attach-only/远程 CDP 也清除模拟
openclaw browser tabs
openclaw browser tab             # 当前标签页快捷方式
openclaw browser tab new
openclaw browser tab select 2
openclaw browser tab close 2
openclaw browser open https://example.com
openclaw browser focus abcd1234
openclaw browser close abcd1234
```

检查：截图、快照、控制台、错误、请求

```bash
openclaw browser screenshot
openclaw browser screenshot --full-page
openclaw browser screenshot --ref 12        # 或 --ref e12
openclaw browser screenshot --labels
openclaw browser snapshot
openclaw browser snapshot --format aria --limit 200
openclaw browser snapshot --interactive --compact --depth 6
openclaw browser snapshot --efficient
openclaw browser snapshot --labels
openclaw browser snapshot --urls
openclaw browser snapshot --selector "#main" --interactive
openclaw browser snapshot --frame "iframe#main" --interactive
openclaw browser console --level error
openclaw browser errors --clear
openclaw browser requests --filter api --clear
openclaw browser pdf
openclaw browser responsebody "**/api" --max-chars 5000
```

操作：导航、点击、输入、拖拽、等待、执行

```bash
openclaw browser navigate https://example.com
openclaw browser resize 1280 720
openclaw browser click 12 --double           # role ref 用 e12
openclaw browser click-coords 120 340        # 视口坐标
openclaw browser type 23 "hello" --submit
openclaw browser press Enter
openclaw browser hover 44
openclaw browser scrollintoview e12
openclaw browser drag 10 11
openclaw browser select 9 OptionA OptionB
openclaw browser download e12 report.pdf
openclaw browser waitfordownload report.pdf
openclaw browser upload /tmp/openclaw/uploads/file.pdf
openclaw browser upload media://inbound/file.pdf
openclaw browser fill --fields '[{"ref":"1","type":"text","value":"Ada"}]'
openclaw browser dialog --accept
openclaw browser dialog --dismiss --dialog-id d1
openclaw browser wait --text "Done"
openclaw browser wait "#main" --url "**/dash" --load networkidle --fn "window.ready===true"
openclaw browser evaluate --fn '(el) => el.textContent' --ref 7
openclaw browser evaluate --timeout-ms 30000 --fn 'async () => { await window.ready; return true; }'
openclaw browser highlight e12
openclaw browser trace start
openclaw browser trace stop
```

状态：cookie、存储、离线、头、地理位置、设备

```bash
openclaw browser cookies
openclaw browser cookies set session abc123 --url "https://example.com"
openclaw browser cookies clear
openclaw browser storage local get
openclaw browser storage local set theme dark
openclaw browser storage session clear
openclaw browser set offline on
openclaw browser set headers --headers-json '{"X-Debug":"1"}'
openclaw browser set credentials user pass            # --clear 移除
openclaw browser set geo 37.7749 -122.4194 --origin "https://example.com"
openclaw browser set media dark
openclaw browser set timezone America/New_York
openclaw browser set locale en-US
openclaw browser set device "iPhone 14"
```

注意：

- `upload` 和 `dialog` 是**预备**调用；在触发选择器/对话框的 click/press 之前运行。操作打开模态框时,操作响应含 `blockedByDialog` 和 `browserState.dialogs.pending`；传该 `dialogId` 直接响应。OpenClaw 外处理的对话框出现在 `browserState.dialogs.recent`。
- `click`/`type` 等需要 `snapshot` 返回的 `ref`（数字 `12`、role ref `e12` 或可操作 ARIA ref `ax12`）。操作有意不支持 CSS 选择器。可见视口位置是唯一可靠目标时用 `click-coords`。
- 下载和 trace 路径限制在 OpenClaw 临时根：`/tmp/openclaw{,/downloads}`（回退：`${os.tmpdir()}/openclaw/...`）。
- `upload` 接受来自 OpenClaw 临时上传根和 OpenClaw 受管入站媒体的文件。受管入站媒体可引用为 `media://inbound/<id>`、沙箱相对路径 `media/inbound/<id>` 或受管入站媒体目录内的解析路径。嵌套媒体引用、遍历、符号链接、硬链接和任意本地路径仍被拒绝。
- `upload` 还可通过 `--input-ref` 或 `--element` 直接设置文件输入。

OpenClaw 能证明替换标签页时（如相同 URL 或表单提交后单旧标签变单新标签）,稳定标签 id 和标签名在 Chromium 原始 target 替换后仍存在。原始 target id 仍易变；脚本中优先用 `tabs` 返回的 `suggestedTargetId`。

快照标志一览：

- `--format ai`（有 Playwright 时默认）：带数字 ref 的 AI 快照（`aria-ref="<n>"`）。
- `--format aria`：带 `axN` ref 的无障碍树。有 Playwright 时 OpenClaw 用后端 DOM id 将 ref 绑定到活页面,后续操作可用；否则视为仅检查输出。
- `--efficient`（或 `--mode efficient`）：紧凑 role 快照预设。设 `browser.snapshotDefaults.mode: "efficient"` 使其成为默认（见 [Gateway 配置](/gateway/configuration-reference#browser)）。
- `--interactive`、`--compact`、`--depth`、`--selector` 强制 role 快照,ref 为 `e12`。`--frame "<iframe>"` 将 role 快照限定到 iframe。
- `--labels` 添加带覆盖 ref 标签的视口截图并打印保存路径。
- `--urls` 向 AI 快照追加发现的链接目标。

## 快照和 ref

> OpenClaw supports two "snapshot" styles:

OpenClaw 支持两种"快照"风格：

- **AI 快照（数字 ref）**：`openclaw browser snapshot`（默认；`--format ai`）
  - 输出：含数字 ref 的文本快照。
  - 操作：`openclaw browser click 12`、`openclaw browser type 23 "hello"`。
  - 内部通过 Playwright 的 `aria-ref` 解析 ref。

- **Role 快照（role ref 如 `e12`）**：`openclaw browser snapshot --interactive`（或 `--compact`、`--depth`、`--selector`、`--frame`）
  - 输出：带 `[ref=e12]`（可选 `[nth=1]`）的角色列表/树。
  - 操作：`openclaw browser click e12`、`openclaw browser highlight e12`。
  - 内部通过 `getByRole(...)`（重复时加 `nth()`）解析 ref。
  - 加 `--labels` 包含带覆盖 `e12` 标签的视口截图。
  - 链接文本模糊且 agent 需要具体导航目标时加 `--urls`。

- **ARIA 快照（ARIA ref 如 `ax12`）**：`openclaw browser snapshot --format aria`
  - 输出：结构化节点的无障碍树。
  - 操作：快照路径能通过 Playwright 和 Chrome 后端 DOM id 绑定 ref 时 `openclaw browser click ax12` 可用。
- 无 Playwright 时 ARIA 快照仍可用于检查,但 ref 可能不可操作。需要操作 ref 时用 `--format ai` 或 `--interactive` 重新快照。
- 原始 CDP 回退路径的 Docker 验证：`pnpm test:docker:browser-cdp-snapshot` 启动带 CDP 的 Chromium,运行 `browser doctor --deep`,验证 role 快照含链接 URL、光标提升的可点击元素和 iframe 元数据。

Ref 行为：

- Ref **不跨导航稳定**；失败时重跑 `snapshot` 用新 ref。
- 能证明替换标签页时 `/act` 在操作触发替换后返回当前原始 `targetId`。后续命令继续用稳定标签 id/标签名。
- role 快照用 `--frame` 拍摄时,role ref 限定到该 iframe 直到下次 role 快照。
- 未知或过期的 `axN` ref 快速失败而非回退到 Playwright 的 `aria-ref` 选择器。发生时在同一标签页跑新快照。

## Wait 增强

> You can wait on more than just time/text:

不只能等时间/文本：

- 等 URL（Playwright 支持 glob）：
  - `openclaw browser wait --url "**/dash"`
- 等加载状态：
  - `openclaw browser wait --load networkidle`
- 等 JS 谓词：
  - `openclaw browser wait --fn "window.ready===true"`
- 等选择器可见：
  - `openclaw browser wait "#main"`

可组合使用：

```bash
openclaw browser wait "#main" \
  --url "**/dash" \
  --load networkidle \
  --fn "window.ready===true" \
  --timeout-ms 15000
```

## 调试工作流

> When an action fails...

操作失败时（如"not visible"、"strict mode violation"、"covered"）：

1. `openclaw browser snapshot --interactive`
2. 用 `click <ref>` / `type <ref>`（interactive 模式优先 role ref）
3. 仍失败：`openclaw browser highlight <ref>` 看 Playwright 定位了什么
4. 页面行为异常：
   - `openclaw browser errors --clear`
   - `openclaw browser requests --filter api --clear`
5. 深度调试：录制 trace：
   - `openclaw browser trace start`
   - 复现问题
   - `openclaw browser trace stop`（打印 `TRACE:<path>`）

## JSON 输出

> `--json` is for scripting and structured tooling.

`--json` 用于脚本和结构化工具。

```bash
openclaw browser status --json
openclaw browser snapshot --interactive --json
openclaw browser requests --filter api --json
openclaw browser cookies --json
```

Role 快照 JSON 含 `refs` 加小型 `stats` 块（lines/chars/refs/interactive）,方便工具判断载荷大小和密度。

## 状态和环境旋钮

> These are useful for "make the site behave like X" workflows:

用于"让站点表现得像 X"工作流：

- Cookie：`cookies`、`cookies set`、`cookies clear`
- 存储：`storage local|session get|set|clear`
- 离线：`set offline on|off`
- 头：`set headers --headers-json '{"X-Debug":"1"}'`（旧版 `set headers --json '{"X-Debug":"1"}'` 仍支持）
- HTTP basic auth：`set credentials user pass`（或 `--clear`）
- 地理位置：`set geo <lat> <lon> --origin "https://example.com"`（或 `--clear`）
- 媒体：`set media dark|light|no-preference|none`
- 时区/区域：`set timezone ...`、`set locale ...`
- 设备/视口：
  - `set device "iPhone 14"`（Playwright 设备预设）
  - `set viewport 1280 720`

## 安全和隐私

- openclaw 浏览器 profile 可能含已登录会话；视为敏感。
- `browser act kind=evaluate` / `openclaw browser evaluate` 和 `wait --fn` 在页面上下文中执行任意 JavaScript。提示注入可操控此功能。不需要时用 `browser.evaluateEnabled=false` 禁用。
- 页面端函数可能需要比默认超时更长时用 `openclaw browser evaluate --timeout-ms <ms>`。
- 登录和反机器人说明（X/Twitter 等）见 [Browser login + X/Twitter posting](/tools/browser-login)。
- 保持 Gateway/node 主机私密（仅回环或 tailnet）。
- 远程 CDP 端点权力大；通过隧道保护它们。

严格模式示例（默认阻止私有/内部目标）：

```json5
{
  browser: {
    ssrfPolicy: {
      dangerouslyAllowPrivateNetwork: false,
      hostnameAllowlist: ["*.example.com", "example.com"],
      allowedHostnames: ["localhost"], // 可选精确放行
    },
  },
}
```

## 相关

- [Browser](/tools/browser) —— 概述、配置、profile、安全
- [Browser login](/tools/browser-login) —— 站点登录
- [Browser Linux 故障排查](/tools/browser-linux-troubleshooting)
- [Browser WSL2 故障排查](/tools/browser-wsl2-windows-remote-cdp-troubleshooting)
