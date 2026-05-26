# QA 总览

> The private QA stack is meant to exercise OpenClaw in a more realistic, channel-shaped way than a single unit test can.

这套私有 QA 框架,跑出来的场景比单元测试更贴近"真实通道"——单测看不出的问题它能看出来。

> Current pieces:
>
> * `extensions/qa-channel`: synthetic message channel with DM, channel, thread, reaction, edit, and delete surfaces.
> * `extensions/qa-lab`: debugger UI and QA bus for observing the transcript, injecting inbound messages, and exporting a Markdown report.
> * `extensions/qa-matrix`, future runner plugins: live-transport adapters that drive a real channel inside a child QA gateway.
> * `qa/`: repo-backed seed assets for the kickoff task and baseline QA scenarios.
> * [Mantis](/concepts/mantis): before and after live verification for bugs that need real transports, browser screenshots, VM state, and PR evidence.

框架里现在有这几块:

- `extensions/qa-channel`:一个合成出来的消息通道,模拟 DM、群聊、话题、表情、编辑、删除这些场景。
- `extensions/qa-lab`:调试 UI 加 QA 总线,用来看对话记录、把接收消息塞进去、导出一份 Markdown 报告。
- `extensions/qa-matrix` 加之后会出的运行器插件:在子 QA Gateway 里驱动真实通道的实时传输适配器。
- `qa/`:仓库里预置的场景文件,提供启动任务和基线 QA 场景。
- [Mantis](/concepts/mantis):有些 bug 必须看真实通道、浏览器截图、VM 状态、PR 证据才能定位,Mantis 给这类 bug 做"修前修后"的对比验证。

---

> ## Command surface

## 命令一览

> Every QA flow runs under `pnpm openclaw qa <subcommand>`. Many have `pnpm qa:*` script aliases; both forms are supported.

所有 QA 流程都走 `pnpm openclaw qa <子命令>`,大部分还有 `pnpm qa:*` 这种短别名,两种都行。

> | Command                                             | Purpose                                                                                                                                                                                                                                                                 |
> | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | `qa run`                                            | Bundled QA self-check; writes a Markdown report.                                                                                                                                                                                                                        |
> | `qa suite`                                          | Run repo-backed scenarios against the QA gateway lane. Aliases: `pnpm openclaw qa suite --runner multipass` for a disposable Linux VM.                                                                                                                                  |
> | `qa coverage`                                       | Print the markdown scenario-coverage inventory (`--json` for machine output).                                                                                                                                                                                           |
> | `qa parity-report`                                  | Compare two `qa-suite-summary.json` files and write the agentic parity report.                                                                                                                                                                                          |
> | `qa character-eval`                                 | Run the character QA scenario across multiple live models with a judged report. See [Reporting](#reporting).                                                                                                                                                            |
> | `qa manual`                                         | Run a one-off prompt against the selected provider/model lane.                                                                                                                                                                                                          |
> | `qa ui`                                             | Start the QA debugger UI and local QA bus (alias: `pnpm qa:lab:ui`).                                                                                                                                                                                                    |
> | `qa docker-build-image`                             | Build the prebaked QA Docker image.                                                                                                                                                                                                                                     |
> | `qa docker-scaffold`                                | Write a docker-compose scaffold for the QA dashboard + gateway lane.                                                                                                                                                                                                    |
> | `qa up`                                             | Build the QA site, start the Docker-backed stack, print the URL (alias: `pnpm qa:lab:up`; `:fast` variant adds `--use-prebuilt-image --bind-ui-dist --skip-ui-build`).                                                                                                  |
> | `qa aimock`                                         | Start only the AIMock provider server.                                                                                                                                                                                                                                  |
> | `qa mock-openai`                                    | Start only the scenario-aware `mock-openai` provider server.                                                                                                                                                                                                            |
> | `qa credentials doctor` / `add` / `list` / `remove` | Manage the shared Convex credential pool.                                                                                                                                                                                                                               |
> | `qa matrix`                                         | Live transport lane against a disposable Tuwunel homeserver. See [Matrix QA](/concepts/qa-matrix).                                                                                                                                                                      |
> | `qa telegram`                                       | Live transport lane against a real private Telegram group.                                                                                                                                                                                                              |
> | `qa discord`                                        | Live transport lane against a real private Discord guild channel.                                                                                                                                                                                                       |
> | `qa slack`                                          | Live transport lane against a real private Slack channel.                                                                                                                                                                                                               |
> | `qa mantis`                                         | Before and after verification runner for live transport bugs, with Discord status-reactions evidence, Crabbox desktop/browser smoke, and Slack-in-VNC smoke. See [Mantis](/concepts/mantis) and [Mantis Slack Desktop Runbook](/concepts/mantis-slack-desktop-runbook). |

| 命令 | 干什么 |
|---|---|
| `qa run` | 内置自检,跑完出一份 Markdown 报告。 |
| `qa suite` | 拿仓库里预置的场景跑 QA Gateway。别名 `pnpm openclaw qa suite --runner multipass` 可以丢进一次性 Linux VM 里跑。 |
| `qa coverage` | 列出场景覆盖清单(加 `--json` 输出机器可读)。 |
| `qa parity-report` | 对比两份 `qa-suite-summary.json`,写一份 agent 行为一致性的报告。 |
| `qa character-eval` | 同一份人格 QA 场景在多个在线模型上跑一遍,出一份带评审的报告。见下文 [Reporting](#reporting)。 |
| `qa manual` | 给选定的 provider / 模型发一条 prompt 跑一次。 |
| `qa ui` | 启动 QA 调试 UI 和本地 QA 总线(别名 `pnpm qa:lab:ui`)。 |
| `qa docker-build-image` | 构建预先烤好的 QA Docker 镜像。 |
| `qa docker-scaffold` | 生成一份 docker-compose 脚手架,跑 QA dashboard 加 Gateway。 |
| `qa up` | 构建 QA 站点、用 Docker 起一整套栈、打印 URL(别名 `pnpm qa:lab:up`;`:fast` 变体加 `--use-prebuilt-image --bind-ui-dist --skip-ui-build`)。 |
| `qa aimock` | 只启 AIMock provider 服务。 |
| `qa mock-openai` | 只启场景感知的 `mock-openai` provider 服务。 |
| `qa credentials doctor` / `add` / `list` / `remove` | 管共享的 Convex 凭证池。 |
| `qa matrix` | 实时传输测试,后面是一台一次性的 Tuwunel homeserver。见 [Matrix QA](/concepts/qa-matrix)。 |
| `qa telegram` | 实时传输测试,后面是一个真实的私有 Telegram 群。 |
| `qa discord` | 实时传输测试,后面是一个真实的私有 Discord guild 频道。 |
| `qa slack` | 实时传输测试,后面是一个真实的私有 Slack 频道。 |
| `qa mantis` | 给实时传输的 bug 做修前修后对比,带 Discord 状态反应证据、Crabbox 桌面 / 浏览器冒烟、Slack-in-VNC 冒烟。见 [Mantis](/concepts/mantis) 和 [Mantis Slack Desktop 运行手册](/concepts/mantis-slack-desktop-runbook)。 |

---

> ## Operator flow

## 操作员流程

> The current QA operator flow is a two-pane QA site:
>
> * Left: Gateway dashboard (Control UI) with the agent.
> * Right: QA Lab, showing the Slack-ish transcript and scenario plan.

现在的 QA 操作员流程长这样:一个左右两栏的站点。

- 左侧:Gateway dashboard(Control UI),agent 在里头。
- 右侧:QA Lab,显示 Slack 那种风格的对话记录和场景计划。

> Run it with:
>
> ```bash
> pnpm qa:lab:up
> ```

跑这条命令:

```bash
pnpm qa:lab:up
```

> That builds the QA site, starts the Docker-backed gateway lane, and exposes the QA Lab page where an operator or automation loop can give the agent a QA mission, observe real channel behavior, and record what worked, failed, or stayed blocked.

这条命令会构建 QA 站点、用 Docker 起一条 Gateway 通路、把 QA Lab 页面挂出来。操作员(或者一个自动化循环)就在这个页面给 agent 派 QA 任务,看真实通道里发生了什么,记下哪些过了、哪些挂了、哪些卡住。

> For faster QA Lab UI iteration without rebuilding the Docker image each time, start the stack with a bind-mounted QA Lab bundle:
>
> ```bash
> pnpm openclaw qa docker-build-image
> pnpm qa:lab:build
> pnpm qa:lab:up:fast
> pnpm qa:lab:watch
> ```

不想每次都重新构建 Docker 镜像、想更快迭代 QA Lab UI,启动时挂载一份 QA Lab 资源包就行:

```bash
pnpm openclaw qa docker-build-image
pnpm qa:lab:build
pnpm qa:lab:up:fast
pnpm qa:lab:watch
```

> `qa:lab:up:fast` keeps the Docker services on a prebuilt image and bind-mounts `extensions/qa-lab/web/dist` into the `qa-lab` container. `qa:lab:watch` rebuilds that bundle on change, and the browser auto-reloads when the QA Lab asset hash changes.

`qa:lab:up:fast` 会让 Docker 服务用一份已经构建好的镜像,把 `extensions/qa-lab/web/dist` 挂进 `qa-lab` 容器里。`qa:lab:watch` 会在你改东西时重新构建那份资源包,QA Lab 资源 hash 变化时浏览器自动刷新。

> For a local OpenTelemetry trace smoke, run:
>
> ```bash
> pnpm qa:otel:smoke
> ```

本地跑一次 OpenTelemetry trace 冒烟测试:

```bash
pnpm qa:otel:smoke
```

> That script starts a local OTLP/HTTP trace receiver, runs the `otel-trace-smoke` QA scenario with the `diagnostics-otel` plugin enabled, then decodes the exported protobuf spans and asserts the release-critical shape: `openclaw.run`, `openclaw.harness.run`, `openclaw.model.call`, `openclaw.context.assembled`, and `openclaw.message.delivery` must be present; model calls must not export `StreamAbandoned` on successful turns; raw diagnostic IDs and `openclaw.content.*` attributes must stay out of the trace. It writes `otel-smoke-summary.json` next to the QA suite artifacts.

这个脚本干这几件事:本地起一个 OTLP/HTTP trace 接收器、开 `diagnostics-otel` 插件跑 `otel-trace-smoke` 这个场景、把导出的 protobuf span 解码出来,然后断言发版必须看到的几样东西:`openclaw.run`、`openclaw.harness.run`、`openclaw.model.call`、`openclaw.context.assembled`、`openclaw.message.delivery` 都得在;成功轮次里模型调用不能发 `StreamAbandoned`;原始诊断 ID 和 `openclaw.content.*` 属性不能跑进 trace。最后把 `otel-smoke-summary.json` 写在 QA suite 产物旁边。

> Observability QA stays source-checkout only. The npm tarball intentionally omits QA Lab, so package Docker release lanes do not run `qa` commands. Use `pnpm qa:otel:smoke` from a built source checkout when changing diagnostics instrumentation.

可观测性 QA 只能在 checkout 出的源码里跑。npm tarball 故意把 QA Lab 删掉了,所以 npm 包的 Docker 发版流程不会跑 `qa` 命令。你改诊断埋点时,在构建好的源码 checkout 里跑 `pnpm qa:otel:smoke` 就行。

> For a transport-real Matrix smoke lane, run:
>
> ```bash
> pnpm openclaw qa matrix --profile fast --fail-fast
> ```

跑一次真实传输的 Matrix 冒烟:

```bash
pnpm openclaw qa matrix --profile fast --fail-fast
```

> The full CLI reference, profile/scenario catalog, env vars, and artifact layout for this lane live in [Matrix QA](/concepts/qa-matrix). At a glance: it provisions a disposable Tuwunel homeserver in Docker, registers temporary driver/SUT/observer users, runs the real Matrix plugin inside a child QA gateway scoped to that transport (no `qa-channel`), then writes a Markdown report, JSON summary, observed-events artifact, and combined output log under `.artifacts/qa-e2e/matrix-<timestamp>/`.

完整 CLI 参考、profile / 场景目录、环境变量、产物布局都在 [Matrix QA](/concepts/qa-matrix)。一句话概括它做什么:Docker 里起一台用完即扔的 Tuwunel homeserver、注册临时的 driver / SUT / observer 用户、在子 QA Gateway 里只跑真实的 Matrix 插件(不带 `qa-channel`),跑完在 `.artifacts/qa-e2e/matrix-<timestamp>/` 下写一份 Markdown 报告、一份 JSON 摘要、一份事件观察产物,加一份合并的输出日志。

> The scenarios cover transport behavior that unit tests cannot prove end to end: mention gating, allow-bot policies, allowlists, top-level and threaded replies, DM routing, reaction handling, inbound edit suppression, restart replay dedupe, homeserver interruption recovery, approval metadata delivery, media handling, and Matrix E2EE bootstrap/recovery/verification flows. The E2EE CLI profile also drives `openclaw matrix encryption setup` and verification commands through the same disposable homeserver before checking gateway replies.

这些场景覆盖的是单测做不了的端到端传输行为:@ 提及触发、bot 放行策略、白名单、顶层回复和话题回复、DM 路由、表情反应处理、接收侧消息编辑的抑制、重启重放去重、homeserver 中断恢复、审批元数据投递、媒体处理,以及 Matrix E2EE 的引导 / 恢复 / 验证流程。E2EE CLI profile 还会用同一台一次性 homeserver 跑 `openclaw matrix encryption setup` 和验证命令,再去看 Gateway 的回复。

> Discord also has Mantis-only opt-in scenarios for bug reproduction. Use `--scenario discord-status-reactions-tool-only` for the explicit status reaction timeline, or `--scenario discord-thread-reply-filepath-attachment` to create a real Discord thread and verify that `message.thread-reply` preserves a `filePath` attachment. These scenarios stay out of the default live Discord lane because they are before/after repro probes rather than broad smoke coverage. The thread-attachment Mantis workflow can also add a logged-in Discord Web witness video when `MANTIS_DISCORD_VIEWER_CHROME_PROFILE_DIR` or `MANTIS_DISCORD_VIEWER_CHROME_PROFILE_TGZ_B64` is configured in the QA environment. That viewer profile is only for visual capture; the pass/fail decision still comes from the Discord REST oracle.

Discord 还有几个只在 Mantis 里跑、专门复现 bug 的场景。`--scenario discord-status-reactions-tool-only` 出一份明确的状态反应时间线;`--scenario discord-thread-reply-filepath-attachment` 真的去建一个 Discord 话题,验证 `message.thread-reply` 把 `filePath` 附件带过去了。它们不进默认的实时 Discord 测试 —— 这些是定向复现 bug 的探针,不是为了广覆盖。话题附件这个 Mantis 流程,如果 QA 环境里配了 `MANTIS_DISCORD_VIEWER_CHROME_PROFILE_DIR` 或 `MANTIS_DISCORD_VIEWER_CHROME_PROFILE_TGZ_B64`,还会附一段已登录的 Discord Web 旁观录像。这份旁观 profile 只是给视觉证据用的;最终通过 / 失败靠 Discord REST oracle 判。

> CI uses the same command surface in `.github/workflows/qa-live-transports-convex.yml`. Scheduled and default manual runs execute the fast Matrix profile with live frontier credentials, `--fast`, and `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS=3000`. Manual `matrix_profile=all` fans out into the five profile shards so the exhaustive catalog can run in parallel while keeping one artifact directory per shard.

CI 在 `.github/workflows/qa-live-transports-convex.yml` 里用同一套命令。定时跑和默认手动跑都用线上模型的凭证执行 fast 这套 Matrix profile,带上 `--fast` 和 `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS=3000`。手动选 `matrix_profile=all` 时,会扇出成 5 个 profile 分片并行跑完整套目录,每个分片各留一个产物目录。

> For transport-real Telegram, Discord, and Slack smoke lanes:
>
> ```bash
> pnpm openclaw qa telegram
> pnpm openclaw qa discord
> pnpm openclaw qa slack
> ```

跑真实传输的 Telegram / Discord / Slack 冒烟:

```bash
pnpm openclaw qa telegram
pnpm openclaw qa discord
pnpm openclaw qa slack
```

> They target a pre-existing real channel with two bots (driver + SUT). Required env vars, scenario lists, output artifacts, and the Convex credential pool are documented in [Telegram, Discord, and Slack QA reference](#telegram-discord-and-slack-qa-reference) below.

这些跑的是已经存在的真实通道,通道里有两个机器人(driver + SUT)。需要哪些环境变量、有哪些场景、输出什么产物、Convex 凭证池怎么用,都在下文 [Telegram / Discord / Slack QA 参考](#telegram-discord-and-slack-qa-reference)。

> For a full Slack desktop VM run with VNC rescue, run:
>
> ```bash
> pnpm openclaw qa mantis slack-desktop-smoke \
>   --gateway-setup \
>   --scenario slack-canary \
>   --keep-lease
> ```

在 Slack 桌面 VM 里跑完整一遍,带 VNC 救援:

```bash
pnpm openclaw qa mantis slack-desktop-smoke \
  --gateway-setup \
  --scenario slack-canary \
  --keep-lease
```

> That command leases a Crabbox desktop/browser machine, runs the Slack live lane inside the VM, opens Slack Web in the VNC browser, captures the desktop, and copies `slack-qa/`, `slack-desktop-smoke.png`, and `slack-desktop-smoke.mp4` when video capture is available back to the Mantis artifact directory. Crabbox desktop/browser leases provide the capture tools and browser/native-build helper packages up front, so the scenario should only install fallbacks on older leases. Mantis reports total and per-phase timings in `mantis-slack-desktop-smoke-report.md` so slow runs show whether time went into lease warmup, credential acquisition, remote setup, or artifact copy. Reuse `--lease-id <cbx_...>` after logging in to Slack Web manually through VNC; reused leases also keep Crabbox's pnpm store cache warm. The default `--hydrate-mode source` verifies from a source checkout and runs install/build inside the VM. Use `--hydrate-mode prehydrated` only when the reused remote workspace already has `node_modules` and a built `dist/`; that mode skips the expensive install/build step and fails closed when the workspace is not ready. With `--gateway-setup`, Mantis leaves a persistent OpenClaw Slack gateway running inside the VM on port `38973`; without it, the command runs the normal bot-to-bot Slack QA lane and exits after artifact capture.

这条命令的流程是:租一台 Crabbox 桌面 / 浏览器机器、在 VM 里跑实时的 Slack 测试、在 VNC 浏览器里打开 Slack Web、把桌面截下来,能录视频时把 `slack-qa/`、`slack-desktop-smoke.png`、`slack-desktop-smoke.mp4` 拷回 Mantis 产物目录。新版 Crabbox 桌面 / 浏览器租约出来就自带录制工具和浏览器 / 原生构建辅助包,所以场景只在老租约上才需要装一遍兜底。Mantis 在 `mantis-slack-desktop-smoke-report.md` 里报告总时长和每个阶段的时长,跑慢了能看出时间花在哪 —— 租约预热、拿凭证、远程 setup,还是产物拷贝。如果你已经手动通过 VNC 登过 Slack Web,加 `--lease-id <cbx_...>` 复用这份租约;复用的租约还能省掉 Crabbox 的 pnpm store 缓存重建。默认 `--hydrate-mode source`,从源码 checkout 验证,VM 里跑一遍 install / build。只有当复用的远程工作区已经有 `node_modules` 和构建好的 `dist/` 时,才能用 `--hydrate-mode prehydrated` —— 这个模式跳过费时的 install / build,工作区没准备好时直接拒绝。带 `--gateway-setup` 时,Mantis 会让一个常驻的 OpenClaw Slack gateway 在 VM 的 `38973` 端口上跑着;不带时,命令跑普通的 bot-to-bot Slack QA,把产物拷下来就退出。

> The operator checklist, GitHub workflow dispatch command, evidence-comment contract, hydrate-mode decision table, timing interpretation, and failure handling steps live in [Mantis Slack Desktop Runbook](/concepts/mantis-slack-desktop-runbook).

操作员清单、GitHub workflow 触发命令、证据评论的约定、hydrate-mode 怎么选、时长怎么解读、失败怎么处理 —— 这些都在 [Mantis Slack Desktop 运行手册](/concepts/mantis-slack-desktop-runbook) 里。

> For an agent/CV style desktop task, run:
>
> ```bash
> pnpm openclaw qa mantis visual-task \
>   --browser-url https://example.net \
>   --expect-text "Example Domain" \
>   --vision-model openai/gpt-5.4
> ```

跑一个 agent / CV 风格的桌面任务:

```bash
pnpm openclaw qa mantis visual-task \
  --browser-url https://example.net \
  --expect-text "Example Domain" \
  --vision-model openai/gpt-5.4
```

> `visual-task` leases or reuses a Crabbox desktop/browser machine, starts `crabbox record --while`, drives the visible browser through a nested `visual-driver`, captures `visual-task.png`, runs `openclaw infer image describe` against the screenshot when `--vision-mode image-describe` is selected, and writes `visual-task.mp4`, `mantis-visual-task-summary.json`, `mantis-visual-task-driver-result.json`, and `mantis-visual-task-report.md`. When `--expect-text` is set, the vision prompt asks for a structured JSON verdict and only passes when the model reports positive visible evidence; a negative response that merely quotes the target text fails the assertion. Use `--vision-mode metadata` for a no-model smoke that proves the desktop, browser, screenshot, and video plumbing without calling an image-understanding provider. Recording is a required artifact for `visual-task`; if Crabbox records no non-empty `visual-task.mp4`, the task fails even when the visual driver passed. On failure, Mantis keeps the lease for VNC unless the task had already passed and `--keep-lease` was not set.

`visual-task` 的流程是这样:租(或复用)一台 Crabbox 桌面 / 浏览器机器,启动 `crabbox record --while`,通过嵌套的 `visual-driver` 驱动那个可见浏览器,把界面截下来存成 `visual-task.png`;选了 `--vision-mode image-describe` 时,会对截图跑一次 `openclaw infer image describe`,最后写出 `visual-task.mp4`、`mantis-visual-task-summary.json`、`mantis-visual-task-driver-result.json`、`mantis-visual-task-report.md`。设了 `--expect-text` 时,视觉 prompt 要求模型给一个结构化 JSON 判定,只有模型明确说"看到了"才算通过;模型如果只是把目标文字引一下、却给了否定回答,断言会失败。`--vision-mode metadata` 是不调模型的冒烟模式,用来证明桌面、浏览器、截图、视频这套管道是通的,完全不调图片理解 provider。录像是 `visual-task` 必需的产物;Crabbox 没录出非空的 `visual-task.mp4`,哪怕视觉 driver 自己通过了,任务也算失败。失败时 Mantis 会保留租约给 VNC 用 —— 除非任务在那之前已经通过、又没加 `--keep-lease`。

> Before using pooled live credentials, run:
>
> ```bash
> pnpm openclaw qa credentials doctor
> ```

用共享池里的在线凭证之前,先跑:

```bash
pnpm openclaw qa credentials doctor
```

> The doctor checks Convex broker env, validates endpoint settings, and verifies admin/list reachability when the maintainer secret is present. It reports only set/missing status for secrets.

doctor 会检查 Convex broker 的环境、校验端点配置;有维护者密钥时再去验证 admin / list 接口能不能通。对密钥本身只报告"已设置 / 没设置",不会打印密钥内容。

---

> ## Live transport coverage

## 实时传输覆盖

> Live transport lanes share one contract instead of each inventing their own scenario list shape. `qa-channel` is the broad synthetic product-behavior suite and is not part of the live transport coverage matrix.

各条实时传输通路共用一份契约,而不是各自定义自己的场景列表。`qa-channel` 是宽泛的合成产品行为套件,不算在这张实时传输覆盖矩阵里。

> | Lane     | Canary | Mention gating | Bot-to-bot | Allowlist block | Top-level reply | Restart resume | Thread follow-up | Thread isolation | Reaction observation | Help command | Native command registration |
> | -------- | ------ | -------------- | ---------- | --------------- | --------------- | -------------- | ---------------- | ---------------- | -------------------- | ------------ | --------------------------- |
> | Matrix   | x      | x              | x          | x               | x               | x              | x                | x                | x                    |              |                             |
> | Telegram | x      | x              | x          |                 |                 |                |                  |                  |                      | x            |                             |
> | Discord  | x      | x              | x          |                 |                 |                |                  |                  |                      |              | x                           |
> | Slack    | x      | x              | x          | x               | x               | x              | x                | x                |                      |              |                             |

| Lane     | Canary | Mention 触发 | Bot-to-bot | 白名单拦截 | 顶层回复 | 重启续跑 | Thread 跟进 | Thread 隔离 | 反应观察 | Help 命令 | 原生命令注册 |
| -------- | ------ | ------------ | ---------- | ---------- | -------- | -------- | ----------- | ----------- | -------- | --------- | ------------ |
| Matrix   | x      | x            | x          | x          | x        | x        | x           | x           | x        |           |              |
| Telegram | x      | x            | x          |            |          |          |             |             |          | x         |              |
| Discord  | x      | x            | x          |            |          |          |             |             |          |           | x            |
| Slack    | x      | x            | x          | x          | x        | x        | x           | x           |          |           |              |

> This keeps `qa-channel` as the broad product-behavior suite while Matrix, Telegram, and future live transports share one explicit transport-contract checklist.

这样分工:`qa-channel` 继续做宽泛的产品行为套件,Matrix、Telegram 和将来的实时传输共用同一份明确的传输契约清单。

> For a disposable Linux VM lane without bringing Docker into the QA path, run:
>
> ```bash
> pnpm openclaw qa suite --runner multipass --scenario channel-chat-baseline
> ```

想要一次性 Linux VM、又不想把 Docker 拉进 QA 链路:

```bash
pnpm openclaw qa suite --runner multipass --scenario channel-chat-baseline
```

> This boots a fresh Multipass guest, installs dependencies, builds OpenClaw inside the guest, runs `qa suite`, then copies the normal QA report and summary back into `.artifacts/qa-e2e/...` on the host. It reuses the same scenario-selection behavior as `qa suite` on the host. Host and Multipass suite runs execute multiple selected scenarios in parallel with isolated gateway workers by default. `qa-channel` defaults to concurrency 4, capped by the selected scenario count. Use `--concurrency <count>` to tune the worker count, or `--concurrency 1` for serial execution. The command exits non-zero when any scenario fails. Use `--allow-failures` when you want artifacts without a failing exit code. Live runs forward the supported QA auth inputs that are practical for the guest: env-based provider keys, the QA live provider config path, and `CODEX_HOME` when present. Keep `--output-dir` under the repo root so the guest can write back through the mounted workspace.

这条命令会:启一台干净的 Multipass 来宾机、装依赖、在来宾里把 OpenClaw 构建好、跑 `qa suite`,然后把常规 QA 报告和摘要拷回宿主机的 `.artifacts/qa-e2e/...`。场景选择的逻辑跟宿主上直接跑 `qa suite` 一样。宿主上和 Multipass 里默认都用相互隔离的 Gateway worker 并行跑多个选中的场景。`qa-channel` 的默认并发是 4,但不会超过选中的场景数。`--concurrency <数>` 自己调 worker 数;`--concurrency 1` 串行跑。任一场景失败,命令退出码就非零;想保留产物又不想要失败退出码,加 `--allow-failures`。实时运行会把来宾里能用的几样 QA 认证输入透传过去:环境里的 provider key、QA 实时 provider 配置路径,以及(如果有)`CODEX_HOME`。`--output-dir` 要放在 repo root 之内,这样来宾才能通过挂载的工作区把产物写回来。

---

> ## Telegram, Discord, and Slack QA reference

## Telegram、Discord、Slack QA 参考

> Matrix has a [dedicated page](/concepts/qa-matrix) because of its scenario count and Docker-backed homeserver provisioning. Telegram, Discord, and Slack are smaller - a handful of scenarios each, no profile system, against pre-existing real channels - so their reference lives here.

Matrix 的场景多、还要 Docker 起一台 homeserver,所以单独有 [一页文档](/concepts/qa-matrix)。Telegram / Discord / Slack 小得多 —— 各自只有几个场景、没有 profile 系统、跑在已经存在的真实通道上 —— 所以参考统一放在本页。

> ### Shared CLI flags

### 共享的 CLI 参数

> These lanes register through `extensions/qa-lab/src/live-transports/shared/live-transport-cli.ts` and accept the same flags:

这几条通路都在 `extensions/qa-lab/src/live-transports/shared/live-transport-cli.ts` 里注册,接受同一套参数:

> | Flag                                  | Default                                                         | Description                                                                                                           |
> | ------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
> | `--scenario <id>`                     | -                                                               | Run only this scenario. Repeatable.                                                                                   |
> | `--output-dir <path>`                 | `<repo>/.artifacts/qa-e2e/{telegram,discord,slack}-<timestamp>` | Where reports/summary/observed messages and the output log are written. Relative paths resolve against `--repo-root`. |
> | `--repo-root <path>`                  | `process.cwd()`                                                 | Repository root when invoking from a neutral cwd.                                                                     |
> | `--sut-account <id>`                  | `sut`                                                           | Temporary account id inside the QA gateway config.                                                                    |
> | `--provider-mode <mode>`              | `live-frontier`                                                 | `mock-openai` or `live-frontier` (legacy `live-openai` still works).                                                  |
> | `--model <ref>` / `--alt-model <ref>` | provider default                                                | Primary/alternate model refs.                                                                                         |
> | `--fast`                              | off                                                             | Provider fast mode where supported.                                                                                   |
> | `--credential-source <env\|convex>`   | `env`                                                           | See [Convex credential pool](#convex-credential-pool).                                                                |
> | `--credential-role <maintainer\|ci>`  | `ci` in CI, `maintainer` otherwise                              | Role used when `--credential-source convex`.                                                                          |

| 参数                                  | 默认值                                                          | 说明                                                                                                                  |
| ------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `--scenario <id>` | - | 只跑这一个场景。可以重复指定。 |
| `--output-dir <path>` | `<repo>/.artifacts/qa-e2e/{telegram,discord,slack}-<时间戳>` | 报告 / 摘要 / 观察到的消息 / 输出日志往哪写。相对路径会按 `--repo-root` 解析。 |
| `--repo-root <path>` | `process.cwd()` | 从一个中立目录调用时,指定仓库根。 |
| `--sut-account <id>` | `sut` | QA Gateway 配置里临时账号的 id。 |
| `--provider-mode <mode>` | `live-frontier` | `mock-openai` 或 `live-frontier`(旧名 `live-openai` 仍兼容)。 |
| `--model <ref>` / `--alt-model <ref>` | provider 自带默认 | 主模型 / 备用模型的 ref。 |
| `--fast` | 关 | provider 支持时启用 fast 模式。 |
| `--credential-source <env\|convex>` | `env` | 见下文 [Convex 凭证池](#convex-credential-pool)。 |
| `--credential-role <maintainer\|ci>` | CI 里默认 `ci`,其他场合 `maintainer` | `--credential-source convex` 时按什么角色去取。 |

> Each lane exits non-zero on any failed scenario. `--allow-failures` writes artifacts without setting a failing exit code.

每条通路只要有一个场景失败,退出码就非零。想要拿产物又不想要失败退出码,加 `--allow-failures`。

> ### Telegram QA

### Telegram QA

> ```bash
> pnpm openclaw qa telegram
> ```

```bash
pnpm openclaw qa telegram
```

> Targets one real private Telegram group with two distinct bots (driver + SUT). The SUT bot must have a Telegram username; bot-to-bot observation works best when both bots have **Bot-to-Bot Communication Mode** enabled in `@BotFather`.

跑在一个真实的私有 Telegram 群里,群里有两个不同的机器人(driver + SUT)。SUT 这只机器人必须有 Telegram username;两只机器人在 `@BotFather` 里都开 **Bot-to-Bot Communication Mode** 时,bot 互看的效果最好。

> Required env when `--credential-source env`:
>
> * `OPENCLAW_QA_TELEGRAM_GROUP_ID` - numeric chat id (string).
> * `OPENCLAW_QA_TELEGRAM_DRIVER_BOT_TOKEN`
> * `OPENCLAW_QA_TELEGRAM_SUT_BOT_TOKEN`

用 `--credential-source env` 时,这几个环境变量必填:

- `OPENCLAW_QA_TELEGRAM_GROUP_ID`:数字 chat id(字符串形式)。
- `OPENCLAW_QA_TELEGRAM_DRIVER_BOT_TOKEN`
- `OPENCLAW_QA_TELEGRAM_SUT_BOT_TOKEN`

> Optional:
>
> * `OPENCLAW_QA_TELEGRAM_CAPTURE_CONTENT=1` keeps message bodies in observed-message artifacts (default redacts).

可选:

- `OPENCLAW_QA_TELEGRAM_CAPTURE_CONTENT=1`:让"观察到的消息"产物里保留消息正文(默认会脱敏)。

> Scenarios (`extensions/qa-lab/src/live-transports/telegram/telegram-live.runtime.ts`):
>
> * `telegram-canary`
> * `telegram-mention-gating`
> * `telegram-mentioned-message-reply`
> * `telegram-help-command`
> * `telegram-commands-command`
> * `telegram-tools-compact-command`
> * `telegram-whoami-command`
> * `telegram-status-command`
> * `telegram-repeated-command-authorization`
> * `telegram-other-bot-command-gating`
> * `telegram-context-command`
> * `telegram-current-session-status-tool`
> * `telegram-reply-chain-exact-marker`
> * `telegram-stream-final-single-message`
> * `telegram-long-final-reuses-preview`
> * `telegram-long-final-three-chunks`

场景（`extensions/qa-lab/src/live-transports/telegram/telegram-live.runtime.ts`）：

- `telegram-canary`
- `telegram-mention-gating`
- `telegram-mentioned-message-reply`
- `telegram-help-command`
- `telegram-commands-command`
- `telegram-tools-compact-command`
- `telegram-whoami-command`
- `telegram-status-command`
- `telegram-repeated-command-authorization`
- `telegram-other-bot-command-gating`
- `telegram-context-command`
- `telegram-current-session-status-tool`
- `telegram-reply-chain-exact-marker`
- `telegram-stream-final-single-message`
- `telegram-long-final-reuses-preview`
- `telegram-long-final-three-chunks`

> The implicit default set always covers canary, mention gating, native command replies, command addressing, and bot-to-bot group replies. `mock-openai` defaults also include deterministic reply-chain and final-message streaming checks. `telegram-current-session-status-tool` remains opt-in because it is only stable when threaded directly after canary, not after arbitrary native command replies. Use `pnpm openclaw qa telegram --list-scenarios --provider-mode mock-openai` to print the current default/optional split with regression refs.

不显式指定时,默认场景集一定包含:canary、@ 提及触发、原生命令回复、命令寻址、bot 间群回复。走 `mock-openai` 时还会额外加上确定性的回复链检查和最终消息流式检查。`telegram-current-session-status-tool` 没进默认集 —— 它只有紧接 canary 那条话题跑才稳定,跟在任意一条原生命令回复之后会飘。想看当前默认集和可选集怎么分的、对应哪个回归用例,跑 `pnpm openclaw qa telegram --list-scenarios --provider-mode mock-openai`。

> Output artifacts:
>
> * `telegram-qa-report.md`
> * `telegram-qa-summary.json` - includes per-reply RTT (driver send → observed SUT reply) starting with the canary.
> * `telegram-qa-observed-messages.json` - bodies redacted unless `OPENCLAW_QA_TELEGRAM_CAPTURE_CONTENT=1`.

输出产物:

- `telegram-qa-report.md`
- `telegram-qa-summary.json`:从 canary 开始,每条回复都记一份 RTT(driver 发出 → 观察到 SUT 回应所花的时间)。
- `telegram-qa-observed-messages.json`:正文默认脱敏,除非设了 `OPENCLAW_QA_TELEGRAM_CAPTURE_CONTENT=1`。

> ### Discord QA

### Discord QA

> ```bash
> pnpm openclaw qa discord
> ```

```bash
pnpm openclaw qa discord
```

> Targets one real private Discord guild channel with two bots: a driver bot controlled by the harness and a SUT bot started by the child OpenClaw gateway through the bundled Discord plugin. Verifies channel mention handling, that the SUT bot has registered the native `/help` command with Discord, and opt-in Mantis evidence scenarios.

跑在一个真实的私有 Discord guild 频道里,频道里有两个机器人:driver 由 harness 控制,SUT 由子 OpenClaw Gateway 通过内置 Discord 插件起。验证三件事:频道里的 @ 提及怎么处理、SUT 有没有在 Discord 上注册原生 `/help` 命令、以及可选的 Mantis 证据场景。

> Required env when `--credential-source env`:
>
> * `OPENCLAW_QA_DISCORD_GUILD_ID`
> * `OPENCLAW_QA_DISCORD_CHANNEL_ID`
> * `OPENCLAW_QA_DISCORD_DRIVER_BOT_TOKEN`
> * `OPENCLAW_QA_DISCORD_SUT_BOT_TOKEN`
> * `OPENCLAW_QA_DISCORD_SUT_APPLICATION_ID` - must match the SUT bot user id returned by Discord (the lane fails fast otherwise).

用 `--credential-source env` 时,这几个必填:

- `OPENCLAW_QA_DISCORD_GUILD_ID`
- `OPENCLAW_QA_DISCORD_CHANNEL_ID`
- `OPENCLAW_QA_DISCORD_DRIVER_BOT_TOKEN`
- `OPENCLAW_QA_DISCORD_SUT_BOT_TOKEN`
- `OPENCLAW_QA_DISCORD_SUT_APPLICATION_ID`:必须跟 Discord 返回的 SUT 机器人 user id 一致 —— 对不上时整条通路直接失败。

> Optional:
>
> * `OPENCLAW_QA_DISCORD_CAPTURE_CONTENT=1` keeps message bodies in observed-message artifacts.
> * `OPENCLAW_QA_DISCORD_VOICE_CHANNEL_ID` selects the voice/stage channel for `discord-voice-autojoin`; without it, the scenario picks the first visible voice/stage channel for the SUT bot.

可选:

- `OPENCLAW_QA_DISCORD_CAPTURE_CONTENT=1`:观察到的消息产物里保留消息正文。
- `OPENCLAW_QA_DISCORD_VOICE_CHANNEL_ID`:给 `discord-voice-autojoin` 指定 voice / stage 频道;不设的话,场景会挑 SUT 机器人能看到的第一个 voice / stage 频道。

> Scenarios (`extensions/qa-lab/src/live-transports/discord/discord-live.runtime.ts:36`):
>
> * `discord-canary`
> * `discord-mention-gating`
> * `discord-native-help-command-registration`
> * `discord-voice-autojoin` - opt-in voice scenario. Runs by itself, enables `channels.discord.voice.autoJoin`, and verifies the SUT bot's current Discord voice state is the target voice/stage channel. Convex Discord credentials may include optional `voiceChannelId`; otherwise the runner discovers the first visible voice/stage channel in the guild.
> * `discord-status-reactions-tool-only` - opt-in Mantis scenario. Runs by itself because it switches the SUT to always-on, tool-only guild replies with `messages.statusReactions.enabled=true`, then captures a REST reaction timeline plus HTML/PNG visual artifacts. Mantis before/after reports also preserve scenario-provided MP4 artifacts as `baseline.mp4` and `candidate.mp4`.

场景（`extensions/qa-lab/src/live-transports/discord/discord-live.runtime.ts:36`）：

- `discord-canary`
- `discord-mention-gating`
- `discord-native-help-command-registration`
- `discord-voice-autojoin`:可选的语音场景。要单独跑;它开 `channels.discord.voice.autoJoin`,然后看 SUT 机器人当前的 Discord 语音状态是不是停在目标 voice / stage 频道上。Convex Discord 凭证里可以带一个 `voiceChannelId`;不带的话,运行器自己去 guild 里找第一个能看到的 voice / stage 频道。
- `discord-status-reactions-tool-only`:可选的 Mantis 场景。也要单独跑 —— 因为它会把 SUT 切到"always-on、只用 tool 回复 guild"的模式,并把 `messages.statusReactions.enabled` 设成 `true`,然后录一条 REST 反应时间线,加 HTML / PNG 可视产物。Mantis 的"修前修后"报告还会把场景产生的 MP4 保留成 `baseline.mp4` 和 `candidate.mp4`。

> Run the Discord voice auto-join scenario explicitly:
>
> ```bash
> pnpm openclaw qa discord \
>   --scenario discord-voice-autojoin \
>   --provider-mode mock-openai
> ```

显式跑 Discord 语音自动加入这个场景:

```bash
pnpm openclaw qa discord \
  --scenario discord-voice-autojoin \
  --provider-mode mock-openai
```

> Run the Mantis status-reaction scenario explicitly:
>
> ```bash
> pnpm openclaw qa discord \
>   --scenario discord-status-reactions-tool-only \
>   --provider-mode live-frontier \
>   --model openai/gpt-5.4 \
>   --alt-model openai/gpt-5.4 \
>   --fast
> ```

显式跑 Mantis 的状态反应场景:

```bash
pnpm openclaw qa discord \
  --scenario discord-status-reactions-tool-only \
  --provider-mode live-frontier \
  --model openai/gpt-5.4 \
  --alt-model openai/gpt-5.4 \
  --fast
```

> Output artifacts:
>
> * `discord-qa-report.md`
> * `discord-qa-summary.json`
> * `discord-qa-observed-messages.json` - bodies redacted unless `OPENCLAW_QA_DISCORD_CAPTURE_CONTENT=1`.
> * `discord-qa-reaction-timelines.json` and `discord-status-reactions-tool-only-timeline.png` when the status-reaction scenario runs.

输出产物:

- `discord-qa-report.md`
- `discord-qa-summary.json`
- `discord-qa-observed-messages.json`:正文默认脱敏,除非设了 `OPENCLAW_QA_DISCORD_CAPTURE_CONTENT=1`。
- 跑了状态反应场景时,还会多出 `discord-qa-reaction-timelines.json` 和 `discord-status-reactions-tool-only-timeline.png`。

> ### Slack QA

### Slack QA

> ```bash
> pnpm openclaw qa slack
> ```

```bash
pnpm openclaw qa slack
```

> Targets one real private Slack channel with two distinct bots: a driver bot controlled by the harness and a SUT bot started by the child OpenClaw gateway through the bundled Slack plugin.

跑在一个真实的私有 Slack 频道里,频道里有两个互不相同的机器人:driver 由 harness 控制,SUT 由子 OpenClaw Gateway 通过内置 Slack 插件起。

> Required env when `--credential-source env`:
>
> * `OPENCLAW_QA_SLACK_CHANNEL_ID`
> * `OPENCLAW_QA_SLACK_DRIVER_BOT_TOKEN`
> * `OPENCLAW_QA_SLACK_SUT_BOT_TOKEN`
> * `OPENCLAW_QA_SLACK_SUT_APP_TOKEN`

用 `--credential-source env` 时,这几个必填:

- `OPENCLAW_QA_SLACK_CHANNEL_ID`
- `OPENCLAW_QA_SLACK_DRIVER_BOT_TOKEN`
- `OPENCLAW_QA_SLACK_SUT_BOT_TOKEN`
- `OPENCLAW_QA_SLACK_SUT_APP_TOKEN`

> Optional:
>
> * `OPENCLAW_QA_SLACK_CAPTURE_CONTENT=1` keeps message bodies in observed-message artifacts.

可选:

- `OPENCLAW_QA_SLACK_CAPTURE_CONTENT=1`:观察到的消息产物里保留消息正文。

> Scenarios (`extensions/qa-lab/src/live-transports/slack/slack-live.runtime.ts:39`):
>
> * `slack-canary`
> * `slack-mention-gating`
> * `slack-allowlist-block`
> * `slack-top-level-reply-shape`
> * `slack-restart-resume`
> * `slack-thread-follow-up`
> * `slack-thread-isolation`

场景（`extensions/qa-lab/src/live-transports/slack/slack-live.runtime.ts:39`）：

- `slack-canary`
- `slack-mention-gating`
- `slack-allowlist-block`
- `slack-top-level-reply-shape`
- `slack-restart-resume`
- `slack-thread-follow-up`
- `slack-thread-isolation`

> Output artifacts:
>
> * `slack-qa-report.md`
> * `slack-qa-summary.json`
> * `slack-qa-observed-messages.json` - bodies redacted unless `OPENCLAW_QA_SLACK_CAPTURE_CONTENT=1`.

输出产物:

- `slack-qa-report.md`
- `slack-qa-summary.json`
- `slack-qa-observed-messages.json`:正文默认脱敏,除非设了 `OPENCLAW_QA_SLACK_CAPTURE_CONTENT=1`。

> #### Setting up the Slack workspace

#### 配置 Slack 工作区

> The lane needs two distinct Slack apps in one workspace, plus a channel both bots are members of:
>
> * `channelId` - the `Cxxxxxxxxxx` id of a channel both bots have been invited to. Use a dedicated channel; the lane posts on every run.
> * `driverBotToken` - bot token (`xoxb-...`) of the **Driver** app.
> * `sutBotToken` - bot token (`xoxb-...`) of the **SUT** app, which must be a separate Slack app from the driver so its bot user id is distinct.
> * `sutAppToken` - app-level token (`xapp-...`) of the SUT app with `connections:write`, used by Socket Mode so the SUT app can receive events.

这条通路要在同一个工作区里建两个不同的 Slack app,再加一个两个机器人都在的频道:

- `channelId`:两个机器人都被邀请进去的那个频道的 `Cxxxxxxxxxx` id。最好用一个专门频道,因为这条通路每跑一次都会在里面发消息。
- `driverBotToken`:**Driver** app 的机器人 token(`xoxb-...`)。
- `sutBotToken`:**SUT** app 的机器人 token(`xoxb-...`)。SUT 必须是另一个独立的 Slack app,这样它的机器人 user id 才跟 driver 不同。
- `sutAppToken`:SUT app 的 app 级 token(`xapp-...`),带 `connections:write` 权限,Socket Mode 靠它让 SUT app 收事件。

> Prefer a Slack workspace dedicated to QA over reusing a production workspace.

建议单开一个 QA 专用的 Slack 工作区,不要拿生产工作区凑合。

> The SUT manifest below intentionally narrows the bundled Slack plugin's production install (`extensions/slack/src/setup-shared.ts:10`) to the permissions and events covered by the live Slack QA suite. For the production-channel setup as users see it, see [Slack channel quick setup](/channels/slack#quick-setup); the QA Driver/SUT pair is intentionally separate because the lane needs two distinct bot user ids in one workspace.

下面这份 SUT manifest 是有意把内置 Slack 插件的生产版安装(`extensions/slack/src/setup-shared.ts:10`)收窄,只留实时 Slack QA 套件用到的那些权限和事件。普通用户看到的生产通道怎么搭,见 [Slack 通道快速配置](/channels/slack#quick-setup);QA 这边 Driver 和 SUT 故意分开,因为这条通路必须在同一个工作区里有两个不同的机器人 user id。

> **1. Create the Driver app**

**1. 创建 Driver app**

> Go to [api.slack.com/apps](https://api.slack.com/apps) → *Create New App* → *From a manifest* → pick the QA workspace, paste the following manifest, then *Install to Workspace*:

去 [api.slack.com/apps](https://api.slack.com/apps) → *Create New App* → *From a manifest*,选 QA 工作区,把下面这份 manifest 粘进去,然后点 *Install to Workspace*:

> ```json
> {
>   "display_information": {
>     "name": "OpenClaw QA Driver",
>     "description": "Test driver bot for OpenClaw QA Slack live lane"
>   },
>   "features": {
>     "bot_user": {
>       "display_name": "OpenClaw QA Driver",
>       "always_online": true
>     }
>   },
>   "oauth_config": {
>     "scopes": {
>       "bot": ["chat:write", "channels:history", "groups:history", "users:read"]
>     }
>   },
>   "settings": {
>     "socket_mode_enabled": false
>   }
> }
> ```

```json
{
  "display_information": {
    "name": "OpenClaw QA Driver",
    "description": "Test driver bot for OpenClaw QA Slack live lane"
  },
  "features": {
    "bot_user": {
      "display_name": "OpenClaw QA Driver",
      "always_online": true
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": ["chat:write", "channels:history", "groups:history", "users:read"]
    }
  },
  "settings": {
    "socket_mode_enabled": false
  }
}
```

> Copy the *Bot User OAuth Token* (`xoxb-...`) - that becomes `driverBotToken`. The driver only needs to post messages and identify itself; no events, no Socket Mode.

把 *Bot User OAuth Token*(`xoxb-...`)复制出来,这就是 `driverBotToken`。driver 只要能发消息、能报自己身份就行,不接事件、也不开 Socket Mode。

> **2. Create the SUT app**

**2. 创建 SUT app**

> Repeat *Create New App → From a manifest* in the same workspace. This QA app intentionally uses a narrower version of the bundled Slack plugin's production manifest (`extensions/slack/src/setup-shared.ts:10`): reaction scopes and events are omitted because the live Slack QA suite does not cover reaction handling yet.

在同一个工作区里再来一次 *Create New App → From a manifest*。下面这份 QA app 的 manifest 比内置 Slack 插件的生产版(`extensions/slack/src/setup-shared.ts:10`)窄一截 —— 反应相关的权限和事件都省了,因为实时 Slack QA 套件暂时不覆盖反应处理。

> ```json
> {
>   "display_information": {
>     "name": "OpenClaw QA SUT",
>     "description": "OpenClaw QA SUT connector for OpenClaw"
>   },
>   "features": {
>     "bot_user": {
>       "display_name": "OpenClaw QA SUT",
>       "always_online": true
>     },
>     "app_home": {
>       "home_tab_enabled": true,
>       "messages_tab_enabled": true,
>       "messages_tab_read_only_enabled": false
>     }
>   },
>   "oauth_config": {
>     "scopes": {
>       "bot": [
>         "app_mentions:read",
>         "assistant:write",
>         "channels:history",
>         "channels:read",
>         "chat:write",
>         "commands",
>         "emoji:read",
>         "files:read",
>         "files:write",
>         "groups:history",
>         "groups:read",
>         "im:history",
>         "im:read",
>         "im:write",
>         "mpim:history",
>         "mpim:read",
>         "mpim:write",
>         "pins:read",
>         "pins:write",
>         "usergroups:read",
>         "users:read"
>       ]
>     }
>   },
>   "settings": {
>     "socket_mode_enabled": true,
>     "event_subscriptions": {
>       "bot_events": [
>         "app_home_opened",
>         "app_mention",
>         "channel_rename",
>         "member_joined_channel",
>         "member_left_channel",
>         "message.channels",
>         "message.groups",
>         "message.im",
>         "message.mpim",
>         "pin_added",
>         "pin_removed"
>       ]
>     }
>   }
> }
> ```

```json
{
  "display_information": {
    "name": "OpenClaw QA SUT",
    "description": "OpenClaw QA SUT connector for OpenClaw"
  },
  "features": {
    "bot_user": {
      "display_name": "OpenClaw QA SUT",
      "always_online": true
    },
    "app_home": {
      "home_tab_enabled": true,
      "messages_tab_enabled": true,
      "messages_tab_read_only_enabled": false
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": [
        "app_mentions:read",
        "assistant:write",
        "channels:history",
        "channels:read",
        "chat:write",
        "commands",
        "emoji:read",
        "files:read",
        "files:write",
        "groups:history",
        "groups:read",
        "im:history",
        "im:read",
        "im:write",
        "mpim:history",
        "mpim:read",
        "mpim:write",
        "pins:read",
        "pins:write",
        "usergroups:read",
        "users:read"
      ]
    }
  },
  "settings": {
    "socket_mode_enabled": true,
    "event_subscriptions": {
      "bot_events": [
        "app_home_opened",
        "app_mention",
        "channel_rename",
        "member_joined_channel",
        "member_left_channel",
        "message.channels",
        "message.groups",
        "message.im",
        "message.mpim",
        "pin_added",
        "pin_removed"
      ]
    }
  }
}
```

> After Slack creates the app, do two things on its settings page:
>
> * *Install to Workspace* → copy the *Bot User OAuth Token* → that becomes `sutBotToken`.
> * *Basic Information → App-Level Tokens → Generate Token and Scopes* → add scope `connections:write` → save → copy the `xapp-...` value → that becomes `sutAppToken`.

Slack 把这个 app 建好之后,在它的设置页做两件事:

- *Install to Workspace*,复制 *Bot User OAuth Token*,这就是 `sutBotToken`。
- *Basic Information → App-Level Tokens → Generate Token and Scopes*,加一个 `connections:write` 权限,保存,把 `xapp-...` 那串复制出来,这就是 `sutAppToken`。

> Verify the two bots have distinct user ids by calling `auth.test` on each token. The runtime distinguishes driver and SUT by user id; reusing one app for both will fail mention-gating immediately.

拿两个 token 各调一次 `auth.test`,确认两个机器人的 user id 真的不一样。运行时是靠 user id 来区分 driver 和 SUT 的;一个 app 兼任两个角色,@ 提及触发立刻就会失败。

> **3. Create the channel**

**3. 创建频道**

> In the QA workspace, create a channel (e.g. `#openclaw-qa`) and invite both bots from inside the channel:
>
> ```
> /invite @OpenClaw QA Driver
> /invite @OpenClaw QA SUT
> ```

在 QA 工作区里建一个频道(比如 `#openclaw-qa`),进频道之后把两个机器人都邀请进来:

```
/invite @OpenClaw QA Driver
/invite @OpenClaw QA SUT
```

> Copy the `Cxxxxxxxxxx` id from *channel info → About → Channel ID* - that becomes `channelId`. A public channel works; if you use a private channel both apps already have `groups:history` so the harness's history reads will still succeed.

从 *channel info → About → Channel ID* 把 `Cxxxxxxxxxx` 复制出来 —— 这就是 `channelId`。公开频道可以;用私有频道也行,两个 app 都申请了 `groups:history`,harness 读历史仍然能读到。

> **4. Register the credentials**

**4. 注册凭证**

> Two options. Use env vars for single-machine debugging (set the four `OPENCLAW_QA_SLACK_*` variables and pass `--credential-source env`), or seed the shared Convex pool so CI and other maintainers can lease them.

有两种选择。单机调试就用环境变量(把那四个 `OPENCLAW_QA_SLACK_*` 设好,跑命令时加 `--credential-source env`);要让 CI 和其他维护者也能拿到,就预置到共享的 Convex 池里租用。

> For the Convex pool, write the four fields to a JSON file:
>
> ```json
> {
>   "channelId": "Cxxxxxxxxxx",
>   "driverBotToken": "xoxb-...",
>   "sutBotToken": "xoxb-...",
>   "sutAppToken": "xapp-..."
> }
> ```

走 Convex 池的话,把这四个字段写进一个 JSON 文件:

```json
{
  "channelId": "Cxxxxxxxxxx",
  "driverBotToken": "xoxb-...",
  "sutBotToken": "xoxb-...",
  "sutAppToken": "xapp-..."
}
```

> With `OPENCLAW_QA_CONVEX_SITE_URL` and `OPENCLAW_QA_CONVEX_SECRET_MAINTAINER` exported in your shell, register and verify:
>
> ```bash
> pnpm openclaw qa credentials add \
>   --kind slack \
>   --payload-file slack-creds.json \
>   --note "QA Slack pool seed"
>
> pnpm openclaw qa credentials list --kind slack --status all --json
> ```

在 shell 里 export 好 `OPENCLAW_QA_CONVEX_SITE_URL` 和 `OPENCLAW_QA_CONVEX_SECRET_MAINTAINER`,然后注册并验证:

```bash
pnpm openclaw qa credentials add \
  --kind slack \
  --payload-file slack-creds.json \
  --note "QA Slack pool seed"

pnpm openclaw qa credentials list --kind slack --status all --json
```

> Expect `count: 1`, `status: "active"`, no `lease` field.

应该看到 `count: 1`、`status: "active"`、没有 `lease` 字段。

> **5. Verify end to end**

**5. 端到端验证**

> Run the lane locally to confirm both bots can talk to each other through the broker:
>
> ```bash
> pnpm openclaw qa slack \
>   --credential-source convex \
>   --credential-role maintainer \
>   --output-dir .artifacts/qa-e2e/slack-local
> ```

本地跑一次这条通路,看看两个机器人能不能通过 broker 互相说话:

```bash
pnpm openclaw qa slack \
  --credential-source convex \
  --credential-role maintainer \
  --output-dir .artifacts/qa-e2e/slack-local
```

> A green run completes in well under 30 seconds and `slack-qa-report.md` shows both `slack-canary` and `slack-mention-gating` at status `pass`. If the lane hangs for \~90 seconds and exits with `Convex credential pool exhausted for kind "slack"`, either the pool is empty or every row is leased - `qa credentials list --kind slack --status all --json` will tell you which.

一次跑通常 30 秒内就好,`slack-qa-report.md` 里 `slack-canary` 和 `slack-mention-gating` 应该都是 `pass`。如果卡了大约 90 秒、然后报 `Convex credential pool exhausted for kind "slack"` 退出,要么池子是空的、要么每条凭证都被租走了 —— `qa credentials list --kind slack --status all --json` 能告诉你具体是哪种。

> ### Convex credential pool

### Convex 凭证池

> Telegram, Discord, Slack, and WhatsApp lanes can lease credentials from a shared Convex pool instead of reading the env vars above. Pass `--credential-source convex` (or set `OPENCLAW_QA_CREDENTIAL_SOURCE=convex`); QA Lab acquires an exclusive lease, heartbeats it for the duration of the run, and releases it on shutdown. Pool kinds are `"telegram"`, `"discord"`, `"slack"`, and `"whatsapp"`.

Telegram / Discord / Slack / WhatsApp 这几条通路可以不读上面那些环境变量,改从共享的 Convex 池里租凭证。加 `--credential-source convex`(或设 `OPENCLAW_QA_CREDENTIAL_SOURCE=convex`);QA Lab 会拿一份独占的租约,运行期间每隔一段心跳一次,跑完关停时释放。池子的 kind 有 `"telegram"`、`"discord"`、`"slack"`、`"whatsapp"`。

> Payload shapes the broker validates on `admin/add`:
>
> * Telegram (`kind: "telegram"`): `{ groupId: string, driverToken: string, sutToken: string }` - `groupId` must be a numeric chat-id string.
> * Telegram real user (`kind: "telegram-user"`): `{ groupId: string, sutToken: string, testerUserId: string, testerUsername: string, telegramApiId: string, telegramApiHash: string, tdlibDatabaseEncryptionKey: string, tdlibArchiveBase64: string, tdlibArchiveSha256: string, desktopTdataArchiveBase64: string, desktopTdataArchiveSha256: string }` - one exclusive burner-account lease used by both the TDLib CLI driver and Telegram Desktop visual witness.
> * Discord (`kind: "discord"`): `{ guildId: string, channelId: string, driverBotToken: string, sutBotToken: string, sutApplicationId: string }`.
> * WhatsApp (`kind: "whatsapp"`): `{ driverPhoneE164: string, sutPhoneE164: string, driverAuthArchiveBase64: string, sutAuthArchiveBase64: string, groupJid?: string }` - phone numbers must be distinct E.164 strings.

broker 在 `admin/add` 时会校验的载荷形态:

- Telegram(`kind: "telegram"`):`{ groupId: string, driverToken: string, sutToken: string }` —— `groupId` 必须是数字 chat-id 的字符串形式。
- Telegram 真实用户(`kind: "telegram-user"`):`{ groupId: string, sutToken: string, testerUserId: string, testerUsername: string, telegramApiId: string, telegramApiHash: string, tdlibDatabaseEncryptionKey: string, tdlibArchiveBase64: string, tdlibArchiveSha256: string, desktopTdataArchiveBase64: string, desktopTdataArchiveSha256: string }` —— 一份独占的 burner 账号租约,TDLib CLI driver 和 Telegram Desktop 可视旁观人共用一份。
- Discord(`kind: "discord"`):`{ guildId: string, channelId: string, driverBotToken: string, sutBotToken: string, sutApplicationId: string }`。
- WhatsApp(`kind: "whatsapp"`):`{ driverPhoneE164: string, sutPhoneE164: string, driverAuthArchiveBase64: string, sutAuthArchiveBase64: string, groupJid?: string }` —— 两个电话号码必须是不同的 E.164 字符串。

> For visual real-user Telegram proof, prefer a held Crabbox session:
>
> ```bash
> pnpm qa:telegram-user:crabbox -- start --tdlib-url http://artifacts.openclaw.ai/tdlib-v1.8.0-linux-x64.tgz --output-dir .artifacts/qa-e2e/telegram-user-crabbox/pr-review
> pnpm qa:telegram-user:crabbox -- send --session .artifacts/qa-e2e/telegram-user-crabbox/pr-review/session.json --text /status
> pnpm qa:telegram-user:crabbox -- finish --session .artifacts/qa-e2e/telegram-user-crabbox/pr-review/session.json
> ```

想给真实用户的 Telegram 留可视证据,优先用一份持续保持的 Crabbox session:

```bash
pnpm qa:telegram-user:crabbox -- start --tdlib-url http://artifacts.openclaw.ai/tdlib-v1.8.0-linux-x64.tgz --output-dir .artifacts/qa-e2e/telegram-user-crabbox/pr-review
pnpm qa:telegram-user:crabbox -- send --session .artifacts/qa-e2e/telegram-user-crabbox/pr-review/session.json --text /status
pnpm qa:telegram-user:crabbox -- finish --session .artifacts/qa-e2e/telegram-user-crabbox/pr-review/session.json
```

> `start` holds one exclusive Convex `telegram-user` lease for both the TDLib CLI driver and Telegram Desktop witness, starts desktop recording, and leaves the Crabbox alive for arbitrary agent-driven repro steps. Agents can use `send`, `run`, `screenshot`, and `status` until they are satisfied, then `finish` collects the screenshot, video, motion-trimmed video/GIF, TDLib probe outputs, and logs before releasing the credential. `publish --session <file> --pr <number>` comments only the motion GIF by default; `--full-artifacts` is the explicit opt-in for logs and JSON output. The default `probe` command remains a one-command shorthand for quick `/status` smoke checks.

`start` 会拿一份独占的 Convex `telegram-user` 租约,TDLib CLI driver 和 Telegram Desktop 旁观人共用这份,然后开桌面录制,让 Crabbox 一直活着给 agent 跑各种复现步骤。中间 agent 可以反复用 `send`、`run`、`screenshot`、`status`,直到觉得够了;最后 `finish` 把截图、视频、按动作裁过的视频 / GIF、TDLib probe 输出、日志都收齐,再释放凭证。`publish --session <file> --pr <number>` 默认只把那段动作 GIF 评论上去;想把日志和 JSON 一起带上,加 `--full-artifacts`。`probe` 还是那条用来快速 `/status` 冒烟的一行简写命令。

> Use `--mock-response-file <path>` when a PR needs a deterministic visual diff: the same mock model reply can be run on `main` and on the PR head while the Telegram formatter or delivery layer changes. Capture defaults are tuned for PR comments: standard Crabbox class, 24fps desktop recording, 24fps motion GIF, and 1920px preview width. Before/after comments should publish a clean bundle that contains only the intended GIFs.

PR 想要确定性的可视 diff 时用 `--mock-response-file <path>`:同一份 mock 模型回复,在 `main` 和 PR head 上各跑一遍,这样 Telegram 格式化或投递层有改动时,差异一眼能看出来。录制的默认值就是按 PR 评论的需要调好的:标准 Crabbox class、24fps 桌面录制、24fps 动作 GIF、预览宽度 1920px。修前修后对比评论要发的是一份干净的资源包,里面只有预期的几个 GIF。

> Slack lanes can also use the pool. Slack payload shape checks currently live in the Slack QA runner rather than the broker; use `{ channelId: string, driverBotToken: string, sutBotToken: string, sutAppToken: string }`, with a Slack channel id like `Cxxxxxxxxxx`. See [Setting up the Slack workspace](#setting-up-the-slack-workspace) for app and scope provisioning.

Slack 通路也能用这个池。Slack 的载荷形态目前是 Slack QA 运行器自己在校验,不在 broker 上;格式是 `{ channelId: string, driverBotToken: string, sutBotToken: string, sutAppToken: string }`,Slack channel id 长这种样:`Cxxxxxxxxxx`。app 和权限怎么配,见 [配置 Slack 工作区](#setting-up-the-slack-workspace)。

> Operational env vars and the Convex broker endpoint contract live in [Testing → Shared Telegram credentials via Convex](/help/testing#shared-telegram-credentials-via-convex-v1) (the section name predates the multi-channel pool; the lease semantics are shared across kinds).

运维要用的环境变量、以及 Convex broker 端点的契约,都在 [Testing → Shared Telegram credentials via Convex](/help/testing#shared-telegram-credentials-via-convex-v1)(这个章节名比"多通道池"早出现,所以名字带 Telegram;租约语义其实是所有 kind 通用的)。

---

> ## Repo-backed seeds

## 仓库内的种子

> Seed assets live in `qa/`:
>
> * `qa/scenarios/index.md`
> * `qa/scenarios/<theme>/*.md`

种子资产放在 `qa/`：

- `qa/scenarios/index.md`
- `qa/scenarios/<主题>/*.md`

> These are intentionally in git so the QA plan is visible to both humans and the agent.

它们刻意放在 git 里，让 QA 计划对人和 agent 都可见。

> `qa-lab` should stay a generic markdown runner. Each scenario markdown file is the source of truth for one test run and should define:
>
> * scenario metadata
> * optional category, capability, lane, and risk metadata
> * docs and code refs
> * optional plugin requirements
> * optional gateway config patch
> * the executable `qa-flow`

`qa-lab` 应该保持通用的 markdown runner。每个场景 markdown 文件是一次测试运行的权威源，应当定义：

- 场景元数据
- 可选的分类、能力、队列、风险元数据
- 文档和代码引用
- 可选的插件需求
- 可选的 Gateway 配置 patch
- 可执行的 `qa-flow`

> The reusable runtime surface that backs `qa-flow` is allowed to stay generic and cross-cutting. For example, markdown scenarios can combine transport-side helpers with browser-side helpers that drive the embedded Control UI through the Gateway `browser.request` seam without adding a special-case runner.

支撑 `qa-flow` 的可复用运行时面允许保持通用、跨切面。比如 markdown 场景可以把传输侧辅助函数和浏览器侧辅助函数组合起来，通过 Gateway 的 `browser.request` 接缝驱动内嵌 Control UI，不必加特例运行器。

> Scenario files should be grouped by product capability rather than source tree folder. Keep scenario IDs stable when files move; use `docsRefs` and `codeRefs` for implementation traceability.

场景文件应按产品能力分组，不按源代码树文件夹。文件移动时保持场景 ID 稳定；用 `docsRefs` 和 `codeRefs` 做实现可追溯。

> The baseline list should stay broad enough to cover:
>
> * DM and channel chat
> * thread behavior
> * message action lifecycle
> * cron callbacks
> * memory recall
> * model switching
> * subagent handoff
> * repo-reading and docs-reading
> * one small build task such as Lobster Invaders

基线列表应当宽到能覆盖：

- DM 和频道聊天
- thread 行为
- 消息动作生命周期
- cron 回调
- 记忆召回
- 模型切换
- sub-agent 接力
- 读仓库和读文档
- 一项小型构建任务（比如 Lobster Invaders）

---

> ## Provider mock lanes

## Provider mock 通路

> `qa suite` has two local provider mock lanes:
>
> * `mock-openai` is the scenario-aware OpenClaw mock. It remains the default deterministic mock lane for repo-backed QA and parity gates.
> * `aimock` starts an AIMock-backed provider server for experimental protocol, fixture, record/replay, and chaos coverage. It is additive and does not replace the `mock-openai` scenario dispatcher.

`qa suite` 有两条本地 provider mock 通路：

- `mock-openai` 是 OpenClaw 自己的、场景感知的 mock。仍然是仓库内 QA 和 parity 闸门的默认确定性 mock 队列。
- `aimock` 启动 AIMock 支持的 provider server，用于实验性协议、fixture、record/replay 和混沌覆盖。它是增量的，不替代 `mock-openai` 的场景分发器。

> Provider-lane implementation lives under `extensions/qa-lab/src/providers/`. Each provider owns its defaults, local server startup, gateway model config, auth-profile staging needs, and live/mock capability flags. Shared suite and gateway code should route through the provider registry instead of branching on provider names.

Provider 通路的实现在 `extensions/qa-lab/src/providers/` 下。每个 provider 拥有自己的默认值、本地 server 启动、Gateway 模型配置、认证 profile 暂存需求、实时 / mock 能力标志。共享的 suite 和 Gateway 代码应通过 provider 注册表路由，不要按 provider 名分支。

---

> ## Transport adapters

## 传输适配器

> `qa-lab` owns a generic transport seam for markdown QA scenarios. `qa-channel` is the first adapter on that seam, but the design target is wider: future real or synthetic channels should plug into the same suite runner instead of adding a transport-specific QA runner.

`qa-lab` 拥有 markdown QA 场景的通用传输接缝。`qa-channel` 是这道接缝上的第一个适配器，但设计目标更宽：未来的真实或合成通道应该接到同一个 suite runner，而不是加一个针对传输的 QA 运行器。

> At the architecture level, the split is:
>
> * `qa-lab` owns generic scenario execution, worker concurrency, artifact writing, and reporting.
> * The transport adapter owns gateway config, readiness, inbound and outbound observation, transport actions, and normalized transport state.
> * Markdown scenario files under `qa/scenarios/` define the test run; `qa-lab` provides the reusable runtime surface that executes them.

架构上的切分：

- `qa-lab` 拥有通用场景执行、worker 并发、产物写入、报告。
- 传输适配器拥有 Gateway 配置、就绪、接收和发送观察、传输动作、归一化传输状态。
- `qa/scenarios/` 下的 markdown 场景文件定义测试运行；`qa-lab` 提供执行它们的可复用运行时面。

> ### Adding a channel

### 加一个通道

> Adding a channel to the markdown QA system requires exactly two things:
>
> 1. A transport adapter for the channel.
> 2. A scenario pack that exercises the channel contract.

往 markdown QA 系统里加一个通道，正好需要两样东西：

1. 该通道的传输适配器。
2. 一组练这个通道契约的场景。

> Do not add a new top-level QA command root when the shared `qa-lab` host can own the flow.

共享 `qa-lab` 主机能承载这个流程时，不要加新的顶层 QA 命令根。

> `qa-lab` owns the shared host mechanics:
>
> * the `openclaw qa` command root
> * suite startup and teardown
> * worker concurrency
> * artifact writing
> * report generation
> * scenario execution
> * compatibility aliases for older `qa-channel` scenarios

`qa-lab` 拥有共享主机机制：

- `openclaw qa` 命令根
- suite 启动和拆除
- worker 并发
- 产物写入
- 报告生成
- 场景执行
- 老 `qa-channel` 场景的兼容别名

> Runner plugins own the transport contract:
>
> * how `openclaw qa <runner>` is mounted beneath the shared `qa` root
> * how the gateway is configured for that transport
> * how readiness is checked
> * how inbound events are injected
> * how outbound messages are observed
> * how transcripts and normalized transport state are exposed
> * how transport-backed actions are executed
> * how transport-specific reset or cleanup is handled

Runner 插件拥有传输契约：

- `openclaw qa <runner>` 怎么挂在共享 `qa` 根下
- 该传输的 Gateway 怎么配置
- 怎么检查就绪
- 怎么注入接收事件
- 怎么观察发送消息
- 怎么暴露 transcript 和归一化传输状态
- 怎么执行传输背书的动作
- 怎么处理传输专属的重置或清理

> The minimum adoption bar for a new channel:
>
> 1. Keep `qa-lab` as the owner of the shared `qa` root.
> 2. Implement the transport runner on the shared `qa-lab` host seam.
> 3. Keep transport-specific mechanics inside the runner plugin or channel harness.
> 4. Mount the runner as `openclaw qa <runner>` instead of registering a competing root command. Runner plugins should declare `qaRunners` in `openclaw.plugin.json` and export a matching `qaRunnerCliRegistrations` array from `runtime-api.ts`. Keep `runtime-api.ts` light; lazy CLI and runner execution should stay behind separate entrypoints.
> 5. Author or adapt markdown scenarios under the themed `qa/scenarios/` directories.
> 6. Use the generic scenario helpers for new scenarios.
> 7. Keep existing compatibility aliases working unless the repo is doing an intentional migration.

新通道接入的最低门槛：

1. 让 `qa-lab` 继续做共享 `qa` 根的拥有者。
2. 在共享的 `qa-lab` 主机接缝上实现传输 runner。
3. 把传输专属机制放在运行器插件或通道 harness 里。
4. 把 runner 作为 `openclaw qa <runner>` 挂载，不要注册竞争根命令。Runner 插件应当在 `openclaw.plugin.json` 里声明 `qaRunners`，并从 `runtime-api.ts` 导出对应的 `qaRunnerCliRegistrations` 数组。`runtime-api.ts` 保持轻量；懒加载的 CLI 和 runner 执行放在独立入口后面。
5. 在主题化的 `qa/scenarios/` 目录下写或改 markdown 场景。
6. 新场景用通用场景辅助函数。
7. 除非仓库在做有意识的迁移，否则保留现有兼容别名。

> The decision rule is strict:
>
> * If behavior can be expressed once in `qa-lab`, put it in `qa-lab`.
> * If behavior depends on one channel transport, keep it in that runner plugin or plugin harness.
> * If a scenario needs a new capability that more than one channel can use, add a generic helper instead of a channel-specific branch in `suite.ts`.
> * If a behavior is only meaningful for one transport, keep the scenario transport-specific and make that explicit in the scenario contract.

决策规则严格：

- 行为能在 `qa-lab` 里写一次的，就放 `qa-lab`。
- 行为依赖某个具体通道传输的，留在那个运行器插件或插件 harness 里。
- 场景需要的新能力多于一个通道能用时，加一个通用辅助函数，不要在 `suite.ts` 里加按通道分支。
- 某行为只对一个传输有意义时，让场景保持按传输专属，并在场景契约里说清楚。

> ### Scenario helper names

### 场景辅助函数命名

> Preferred generic helpers for new scenarios:
>
> * `waitForTransportReady`
> * `waitForChannelReady`
> * `injectInboundMessage`
> * `injectOutboundMessage`
> * `waitForTransportOutboundMessage`
> * `waitForChannelOutboundMessage`
> * `waitForNoTransportOutbound`
> * `getTransportSnapshot`
> * `readTransportMessage`
> * `readTransportTranscript`
> * `formatTransportTranscript`
> * `resetTransport`

新场景优先用的通用辅助函数：

- `waitForTransportReady`
- `waitForChannelReady`
- `injectInboundMessage`
- `injectOutboundMessage`
- `waitForTransportOutboundMessage`
- `waitForChannelOutboundMessage`
- `waitForNoTransportOutbound`
- `getTransportSnapshot`
- `readTransportMessage`
- `readTransportTranscript`
- `formatTransportTranscript`
- `resetTransport`

> Compatibility aliases remain available for existing scenarios - `waitForQaChannelReady`, `waitForOutboundMessage`, `waitForNoOutbound`, `formatConversationTranscript`, `resetBus` - but new scenario authoring should use the generic names. The aliases exist to avoid a flag-day migration, not as the model going forward.

兼容别名仍然为已有场景可用 ——`waitForQaChannelReady`、`waitForOutboundMessage`、`waitForNoOutbound`、`formatConversationTranscript`、`resetBus` —— 但新场景应当用通用名。别名存在是为了避免一刀切迁移，不是未来的模型。

---

> ## Reporting

## 报告

> `qa-lab` exports a Markdown protocol report from the observed bus timeline. The report should answer:
>
> * What worked
> * What failed
> * What stayed blocked
> * What follow-up scenarios are worth adding

`qa-lab` 从观察到的总线时间线里导出一份 Markdown 协议报告。报告要回答：

- 哪些通过了
- 哪些失败了
- 哪些一直卡着
- 还值得加哪些跟进场景

> For the inventory of available scenarios - useful when sizing follow-up work or wiring a new transport - run `pnpm openclaw qa coverage` (add `--json` for machine-readable output).

要看可用场景清单 —— 评估跟进工作或接入新传输时有用 —— 跑 `pnpm openclaw qa coverage`（加 `--json` 输出机器可读格式）。

> For character and style checks, run the same scenario across multiple live model refs and write a judged Markdown report:
>
> ```bash
> pnpm openclaw qa character-eval \
>   --model openai/gpt-5.5,thinking=medium,fast \
>   --model openai/gpt-5.2,thinking=xhigh \
>   --model openai/gpt-5,thinking=xhigh \
>   --model anthropic/claude-opus-4-6,thinking=high \
>   --model anthropic/claude-sonnet-4-6,thinking=high \
>   --model zai/glm-5.1,thinking=high \
>   --model moonshot/kimi-k2.5,thinking=high \
>   --model google/gemini-3.1-pro-preview,thinking=high \
>   --judge-model openai/gpt-5.5,thinking=xhigh,fast \
>   --judge-model anthropic/claude-opus-4-6,thinking=high \
>   --blind-judge-models \
>   --concurrency 16 \
>   --judge-concurrency 16
> ```

人格和风格检查时，把同一个场景跨多个在线模型 ref 跑，写一份带评审的 Markdown 报告：

```bash
pnpm openclaw qa character-eval \
  --model openai/gpt-5.5,thinking=medium,fast \
  --model openai/gpt-5.2,thinking=xhigh \
  --model openai/gpt-5,thinking=xhigh \
  --model anthropic/claude-opus-4-6,thinking=high \
  --model anthropic/claude-sonnet-4-6,thinking=high \
  --model zai/glm-5.1,thinking=high \
  --model moonshot/kimi-k2.5,thinking=high \
  --model google/gemini-3.1-pro-preview,thinking=high \
  --judge-model openai/gpt-5.5,thinking=xhigh,fast \
  --judge-model anthropic/claude-opus-4-6,thinking=high \
  --blind-judge-models \
  --concurrency 16 \
  --judge-concurrency 16
```

> The command runs local QA gateway child processes, not Docker. Character eval scenarios should set the persona through `SOUL.md`, then run ordinary user turns such as chat, workspace help, and small file tasks. The candidate model should not be told that it is being evaluated. The command preserves each full transcript, records basic run stats, then asks the judge models in fast mode with `xhigh` reasoning where supported to rank the runs by naturalness, vibe, and humor. Use `--blind-judge-models` when comparing providers: the judge prompt still gets every transcript and run status, but candidate refs are replaced with neutral labels such as `candidate-01`; the report maps rankings back to real refs after parsing. Candidate runs default to `high` thinking, with `medium` for GPT-5.5 and `xhigh` for older OpenAI eval refs that support it. Override a specific candidate inline with `--model provider/model,thinking=<level>`. `--thinking <level>` still sets a global fallback, and the older `--model-thinking <provider/model=level>` form is kept for compatibility. OpenAI candidate refs default to fast mode so priority processing is used where the provider supports it. Add `,fast`, `,no-fast`, or `,fast=false` inline when a single candidate or judge needs an override. Pass `--fast` only when you want to force fast mode on for every candidate model. Candidate and judge durations are recorded in the report for benchmark analysis, but judge prompts explicitly say not to rank by speed. Candidate and judge model runs both default to concurrency 16. Lower `--concurrency` or `--judge-concurrency` when provider limits or local gateway pressure make a run too noisy. When no candidate `--model` is passed, the character eval defaults to `openai/gpt-5.5`, `openai/gpt-5.2`, `openai/gpt-5`, `anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-6`, `zai/glm-5.1`, `moonshot/kimi-k2.5`, and `google/gemini-3.1-pro-preview` when no `--model` is passed. When no `--judge-model` is passed, the judges default to `openai/gpt-5.5,thinking=xhigh,fast` and `anthropic/claude-opus-4-6,thinking=high`.

这条命令跑本地 QA Gateway 子进程，不走 Docker。人格 eval 场景应当通过 `SOUL.md` 设定 persona，然后跑常规用户轮次：聊天、工作区求助、小文件任务。候选模型不要被告知它正在被评测。命令保留每份完整 transcript、记录基本运行统计，然后让评审模型在 fast 模式（支持的地方加 `xhigh` reasoning）按自然度、氛围、幽默对各次运行排名。比较 provider 时用 `--blind-judge-models`：评审 prompt 仍然拿到每份 transcript 和运行状态，但候选 ref 被换成 `candidate-01` 这种中性标签；报告解析后把排名映射回真实 ref。候选运行默认 `high` thinking；GPT-5.5 用 `medium`；支持的旧 OpenAI eval ref 用 `xhigh`。要覆盖具体候选用 `--model provider/model,thinking=<level>`。`--thinking <level>` 仍然设全局回退；旧形式 `--model-thinking <provider/model=level>` 保留兼容。OpenAI 候选 ref 默认 fast 模式，让 provider 支持的地方使用优先处理。某个候选或评审需要单独覆盖时加 `,fast`、`,no-fast`、`,fast=false`。`--fast` 只在你想让所有候选都强制 fast 时用。候选和评审时长会记录在报告里做基准分析，但评审 prompt 明确说不要按速度排名。候选和评审模型运行默认并发 16。provider 限速或本地 Gateway 压力让运行太嘈杂时调低 `--concurrency` 或 `--judge-concurrency`。没传候选 `--model` 时，character eval 默认是 `openai/gpt-5.5`、`openai/gpt-5.2`、`openai/gpt-5`、`anthropic/claude-opus-4-6`、`anthropic/claude-sonnet-4-6`、`zai/glm-5.1`、`moonshot/kimi-k2.5`、`google/gemini-3.1-pro-preview`。没传 `--judge-model` 时，评审默认 `openai/gpt-5.5,thinking=xhigh,fast` 和 `anthropic/claude-opus-4-6,thinking=high`。

---

> ## Related docs

## 相关文档

> * [Matrix QA](/concepts/qa-matrix)
> * [QA Channel](/channels/qa-channel)
> * [Testing](/help/testing)
> * [Dashboard](/web/dashboard)

- [Matrix QA](/concepts/qa-matrix)
- [QA Channel](/channels/qa-channel)
- [Testing](/help/testing)
- [Dashboard](/web/dashboard)
