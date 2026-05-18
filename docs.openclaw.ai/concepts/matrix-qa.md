# Matrix QA

> The Matrix QA lane runs the bundled `@openclaw/matrix` plugin against a disposable Tuwunel homeserver in Docker, with temporary driver, SUT, and observer accounts plus seeded rooms. It is the live transport-real coverage for Matrix.

Matrix QA lane 让内置的 `@openclaw/matrix` 插件跑在 Docker 里一台一次性 Tuwunel homeserver 上，用临时的 driver、SUT、observer 账号和预先种好的房间。它是 Matrix 的真实传输覆盖。

> This is maintainer-only tooling. Packaged OpenClaw releases intentionally omit `qa-lab`, so `openclaw qa` is only available from a source checkout. Source checkouts load the bundled runner directly - no plugin install step is needed.

这是只面向维护者的工具。打包的 OpenClaw 发版有意省略 `qa-lab`，所以 `openclaw qa` 只能从源代码 checkout 用。源代码 checkout 直接加载内置 runner，不需要插件安装步骤。

> For broader QA framework context, see [QA overview](/concepts/qa-e2e-automation).

更宽的 QA 框架背景见 [QA 总览](/concepts/qa-e2e-automation)。

---

> ## Quick start

## 快速上手

> ```bash
> pnpm openclaw qa matrix --profile fast --fail-fast
> ```

```bash
pnpm openclaw qa matrix --profile fast --fail-fast
```

> Plain `pnpm openclaw qa matrix` runs `--profile all` and does not stop on first failure. Use `--profile fast --fail-fast` for a release gate; shard the catalog with `--profile transport|media|e2ee-smoke|e2ee-deep|e2ee-cli` when running the full inventory in parallel.

裸的 `pnpm openclaw qa matrix` 跑 `--profile all`，第一次失败也不停。发版闸门用 `--profile fast --fail-fast`；并行跑完整目录时用 `--profile transport|media|e2ee-smoke|e2ee-deep|e2ee-cli` 分片。

---

> ## What the lane does

## 这条 lane 做什么

> 1. Provisions a disposable Tuwunel homeserver in Docker (default image `ghcr.io/matrix-construct/tuwunel:v1.5.1`, server name `matrix-qa.test`, port `28008`).
> 2. Registers three temporary users - `driver` (sends inbound traffic), `sut` (the OpenClaw Matrix account under test), `observer` (third-party traffic capture).
> 3. Seeds rooms required by the selected scenarios (main, threading, media, restart, secondary, allowlist, E2EE, verification DM, etc.).
> 4. Starts a child OpenClaw gateway with the real Matrix plugin scoped to the SUT account; `qa-channel` is not loaded in the child.
> 5. Runs scenarios in sequence, observing events through the driver/observer Matrix clients.
> 6. Tears down the homeserver, writes report and summary artifacts, then exits.

1. 在 Docker 里 provision 一台一次性 Tuwunel homeserver（默认镜像 `ghcr.io/matrix-construct/tuwunel:v1.5.1`，server name `matrix-qa.test`，端口 `28008`）。
2. 注册三个临时用户 ——`driver`（发送 inbound 流量）、`sut`（被测的 OpenClaw Matrix 账号）、`observer`（第三方流量捕获）。
3. 为选定场景所需的房间播种（main、threading、media、restart、secondary、allowlist、E2EE、verification DM 等）。
4. 启动一个子 OpenClaw Gateway，里面是范围限定到 SUT 账号的真实 Matrix 插件；子 Gateway 里不加载 `qa-channel`。
5. 按顺序跑场景，通过 driver / observer Matrix 客户端观察事件。
6. 拆掉 homeserver，写报告和 summary 产物，然后退出。

---

> ## CLI

## CLI

> ```text
> pnpm openclaw qa matrix [options]
> ```

```text
pnpm openclaw qa matrix [options]
```

> ### Common flags

### 常用参数

> | Flag                  | Default                                       | Description                                                                                                            |
> | --------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
> | `--profile <profile>` | `all`                                         | Scenario profile. See [Profiles](#profiles).                                                                           |
> | `--fail-fast`         | off                                           | Stop after the first failed check or scenario.                                                                         |
> | `--scenario <id>`     | -                                             | Run only this scenario. Repeatable. See [Scenarios](#scenarios).                                                       |
> | `--output-dir <path>` | `<repo>/.artifacts/qa-e2e/matrix-<timestamp>` | Where reports, summary, observed events, and the output log are written. Relative paths resolve against `--repo-root`. |
> | `--repo-root <path>`  | `process.cwd()`                               | Repository root when invoking from a neutral working directory.                                                        |
> | `--sut-account <id>`  | `sut`                                         | Matrix account id inside the QA gateway config.                                                                        |

| 参数                  | 默认值                                          | 说明                                                                                                          |
| --------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `--profile <profile>` | `all`                                           | 场景 profile。见 [Profile](#profiles)。                                                                       |
| `--fail-fast`         | 关                                              | 第一次检查或场景失败后停。                                                                                    |
| `--scenario <id>`     | -                                               | 只跑这个场景。可重复。见 [场景](#scenarios)。                                                                 |
| `--output-dir <path>` | `<repo>/.artifacts/qa-e2e/matrix-<时间戳>`      | 报告、summary、观察事件和输出日志的写入目录。相对路径相对 `--repo-root` 解析。                                |
| `--repo-root <path>`  | `process.cwd()`                                 | 从中立工作目录调用时的仓库根。                                                                                |
| `--sut-account <id>`  | `sut`                                           | QA Gateway 配置里的 Matrix 账号 id。                                                                          |

> ### Provider flags

### Provider 参数

> The lane uses a real Matrix transport but the model provider is configurable:

这条 lane 用真实的 Matrix 传输，但模型 provider 可配：

> | Flag                     | Default          | Description                                                                                                                               |
> | ------------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
> | `--provider-mode <mode>` | `live-frontier`  | `mock-openai` for deterministic mock dispatch or `live-frontier` for live frontier providers. The legacy alias `live-openai` still works. |
> | `--model <ref>`          | provider default | Primary `provider/model` ref.                                                                                                             |
> | `--alt-model <ref>`      | provider default | Alternate `provider/model` ref where scenarios switch mid-run.                                                                            |
> | `--fast`                 | off              | Enable provider fast mode where supported.                                                                                                |

| 参数                     | 默认值           | 说明                                                                                                              |
| ------------------------ | ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| `--provider-mode <mode>` | `live-frontier`  | `mock-openai` 走确定性 mock 分发；`live-frontier` 走实时前沿 provider。旧别名 `live-openai` 仍可用。               |
| `--model <ref>`          | provider 默认    | 主 `provider/model` ref。                                                                                         |
| `--alt-model <ref>`      | provider 默认    | 场景中途切换时用的备 `provider/model` ref。                                                                       |
| `--fast`                 | 关               | 在支持的地方开 provider fast 模式。                                                                               |

> Matrix QA does not accept `--credential-source` or `--credential-role`. The lane provisions disposable users locally; there is no shared credential pool to lease against.

Matrix QA 不接受 `--credential-source` 或 `--credential-role`。这条 lane 在本地 provision 一次性用户；没有共享凭证池可租。

---

> ## Profiles

## Profile

> The selected profile decides which scenarios run.

选定的 profile 决定跑哪些场景。

> | Profile         | Use it for                                                                                                                                                                                                                           |
> | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
> | `all` (default) | Full catalog. Slow but exhaustive.                                                                                                                                                                                                   |
> | `fast`          | Release-gate subset that exercises the live transport contract: canary, mention gating, allowlist block, reply shape, restart resume, thread follow-up, thread isolation, reaction observation, and exec approval metadata delivery. |
> | `transport`     | Transport-level threading, DM, room, autojoin, mention/allowlist, approval, and reaction scenarios.                                                                                                                                  |
> | `media`         | Image, audio, video, PDF, EPUB attachment coverage.                                                                                                                                                                                  |
> | `e2ee-smoke`    | Minimum E2EE coverage - basic encrypted reply, thread follow-up, bootstrap success.                                                                                                                                                  |
> | `e2ee-deep`     | Exhaustive E2EE state-loss, backup, key, and recovery scenarios.                                                                                                                                                                     |
> | `e2ee-cli`      | `openclaw matrix encryption setup` and `verify *` CLI scenarios driven through the QA harness.                                                                                                                                       |

| Profile         | 用法                                                                                                                                                                                              |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `all`（默认）   | 完整目录。慢但全。                                                                                                                                                                                |
| `fast`          | 发版闸门子集，覆盖实时传输契约：canary、mention 触发、白名单拦截、回复形状、重启续跑、thread 跟进、thread 隔离、反应观察、执行批准元数据投递。                                                    |
| `transport`     | 传输级别的 threading、DM、房间、autojoin、mention / 白名单、批准、反应场景。                                                                                                                      |
| `media`         | 图片、音频、视频、PDF、EPUB 附件覆盖。                                                                                                                                                            |
| `e2ee-smoke`    | 最小 E2EE 覆盖 —— 基础加密回复、thread 跟进、引导成功。                                                                                                                                           |
| `e2ee-deep`     | 完整的 E2EE 状态丢失、备份、密钥、恢复场景。                                                                                                                                                      |
| `e2ee-cli`      | 通过 QA harness 驱动的 `openclaw matrix encryption setup` 和 `verify *` CLI 场景。                                                                                                                |

> The exact mapping lives in `extensions/qa-matrix/src/runners/contract/scenario-catalog.ts`.

精确映射在 `extensions/qa-matrix/src/runners/contract/scenario-catalog.ts`。

---

> ## Scenarios

## 场景

> The full scenario id list is the `MatrixQaScenarioId` union in `extensions/qa-matrix/src/runners/contract/scenario-catalog.ts:15`. Categories include:

完整场景 id 列表是 `extensions/qa-matrix/src/runners/contract/scenario-catalog.ts:15` 里的 `MatrixQaScenarioId` 联合类型。分类：

> * threading - `matrix-thread-*`, `matrix-subagent-thread-spawn`
> * top-level / DM / room - `matrix-top-level-reply-shape`, `matrix-room-*`, `matrix-dm-*`
> * streaming and tool progress - `matrix-room-partial-streaming-preview`, `matrix-room-quiet-streaming-preview`, `matrix-room-tool-progress-*`, `matrix-room-block-streaming`
> * media - `matrix-media-type-coverage`, `matrix-room-image-understanding-attachment`, `matrix-attachment-only-ignored`, `matrix-unsupported-media-safe`
> * routing - `matrix-room-autojoin-invite`, `matrix-secondary-room-*`
> * reactions - `matrix-reaction-*`
> * approvals - `matrix-approval-*` (exec/plugin metadata, chunked fallback, deny reactions, threads, and `target: "both"` routing)
> * restart and replay - `matrix-restart-*`, `matrix-stale-sync-replay-dedupe`, `matrix-room-membership-loss`, `matrix-homeserver-restart-resume`, `matrix-initial-catchup-then-incremental`
> * mention gating, bot-to-bot, and allowlists - `matrix-mention-*`, `matrix-allowbots-*`, `matrix-allowlist-*`, `matrix-multi-actor-ordering`, `matrix-inbound-edit-*`, `matrix-mxid-prefixed-command-block`, `matrix-observer-allowlist-override`
> * E2EE - `matrix-e2ee-*` (basic reply, thread follow-up, bootstrap, recovery key lifecycle, state-loss variants, server backup behavior, device hygiene, SAS / QR / DM verification, restart, artifact redaction)
> * E2EE CLI - `matrix-e2ee-cli-*` (encryption setup, idempotent setup, bootstrap failure, recovery-key lifecycle, multi-account, gateway-reply round-trip, self-verification)

- threading：`matrix-thread-*`、`matrix-subagent-thread-spawn`
- top-level / DM / room：`matrix-top-level-reply-shape`、`matrix-room-*`、`matrix-dm-*`
- 流式和工具进度：`matrix-room-partial-streaming-preview`、`matrix-room-quiet-streaming-preview`、`matrix-room-tool-progress-*`、`matrix-room-block-streaming`
- 媒体：`matrix-media-type-coverage`、`matrix-room-image-understanding-attachment`、`matrix-attachment-only-ignored`、`matrix-unsupported-media-safe`
- 路由：`matrix-room-autojoin-invite`、`matrix-secondary-room-*`
- 反应：`matrix-reaction-*`
- 批准：`matrix-approval-*`（exec / 插件元数据、分片回退、拒绝反应、threads、`target: "both"` 路由）
- 重启与重放：`matrix-restart-*`、`matrix-stale-sync-replay-dedupe`、`matrix-room-membership-loss`、`matrix-homeserver-restart-resume`、`matrix-initial-catchup-then-incremental`
- mention 触发、bot-to-bot、白名单：`matrix-mention-*`、`matrix-allowbots-*`、`matrix-allowlist-*`、`matrix-multi-actor-ordering`、`matrix-inbound-edit-*`、`matrix-mxid-prefixed-command-block`、`matrix-observer-allowlist-override`
- E2EE：`matrix-e2ee-*`（基础回复、thread 跟进、引导、恢复 key 生命周期、状态丢失变体、服务端备份行为、设备卫生、SAS / QR / DM 验证、重启、产物脱敏）
- E2EE CLI：`matrix-e2ee-cli-*`（加密 setup、幂等 setup、bootstrap 失败、恢复 key 生命周期、多账号、Gateway 回复往返、自验证）

> Pass `--scenario <id>` (repeatable) to run a hand-picked set; combine with `--profile all` to ignore profile gating.

传 `--scenario <id>`（可重复）跑手挑的一组；和 `--profile all` 组合忽略 profile 门禁。

---

> ## Environment variables

## 环境变量

> | Variable                                | Default                                   | Effect                                                                                                                                                                                         |
> | --------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | `OPENCLAW_QA_MATRIX_TIMEOUT_MS`         | `1800000` (30 min)                        | Hard upper bound on the entire run.                                                                                                                                                            |
> | `OPENCLAW_QA_MATRIX_CANARY_TIMEOUT_MS`  | `45000`                                   | Bound for the initial canary reply. Release CI raises this on shared runners so a slow first gateway turn does not fail before scenario coverage starts.                                       |
> | `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS` | `8000`                                    | Quiet window for negative no-reply assertions. Clamped to `≤` the run timeout.                                                                                                                 |
> | `OPENCLAW_QA_MATRIX_CLEANUP_TIMEOUT_MS` | `90000`                                   | Bound for Docker teardown. Failure surfaces include the recovery `docker compose ... down --remove-orphans` command.                                                                           |
> | `OPENCLAW_QA_MATRIX_TUWUNEL_IMAGE`      | `ghcr.io/matrix-construct/tuwunel:v1.5.1` | Override the homeserver image when validating against a different Tuwunel version.                                                                                                             |
> | `OPENCLAW_QA_MATRIX_PROGRESS`           | on                                        | `0` silences `[matrix-qa] ...` progress lines on stderr. `1` forces them on.                                                                                                                   |
> | `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT`    | redacted                                  | `1` keeps message body and `formatted_body` in `matrix-qa-observed-events.json`. Default redacts to keep CI artifacts safe.                                                                    |
> | `OPENCLAW_QA_MATRIX_DISABLE_FORCE_EXIT` | off                                       | `1` skips the deterministic `process.exit` after artifact write. The default forces exit because matrix-js-sdk's native crypto handles can keep the event loop alive past artifact completion. |
> | `OPENCLAW_RUN_NODE_OUTPUT_LOG`          | unset                                     | When set by an outer launcher (e.g. `scripts/run-node.mjs`), Matrix QA reuses that log path instead of starting its own tee.                                                                   |

| 变量                                    | 默认值                                    | 影响                                                                                                                                                                                                       |
| --------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OPENCLAW_QA_MATRIX_TIMEOUT_MS`         | `1800000`（30 分钟）                      | 整次运行的硬上限。                                                                                                                                                                                         |
| `OPENCLAW_QA_MATRIX_CANARY_TIMEOUT_MS`  | `45000`                                   | 初始 canary 回复的上限。发版 CI 在共享 runner 上调高它，避免第一次 Gateway 慢导致场景覆盖还没开始就失败。                                                                                                  |
| `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS` | `8000`                                    | 负向"无回复"断言的安静窗口。被钳制到 `≤` 运行超时。                                                                                                                                                        |
| `OPENCLAW_QA_MATRIX_CLEANUP_TIMEOUT_MS` | `90000`                                   | Docker 拆除的上限。失败时输出里会带恢复用的 `docker compose ... down --remove-orphans` 命令。                                                                                                              |
| `OPENCLAW_QA_MATRIX_TUWUNEL_IMAGE`      | `ghcr.io/matrix-construct/tuwunel:v1.5.1` | 验证不同 Tuwunel 版本时覆盖 homeserver 镜像。                                                                                                                                                              |
| `OPENCLAW_QA_MATRIX_PROGRESS`           | 开                                        | `0` 静默 stderr 上的 `[matrix-qa] ...` 进度行；`1` 强制开启。                                                                                                                                              |
| `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT`    | 脱敏                                      | `1` 让 `matrix-qa-observed-events.json` 保留消息正文和 `formatted_body`。默认脱敏，保护 CI 产物安全。                                                                                                      |
| `OPENCLAW_QA_MATRIX_DISABLE_FORCE_EXIT` | 关                                        | `1` 跳过产物写入后的确定性 `process.exit`。默认强制退出 —— matrix-js-sdk 的原生 crypto 句柄可能让事件循环在产物写完之后还活着。                                                                            |
| `OPENCLAW_RUN_NODE_OUTPUT_LOG`          | 未设                                      | 外层 launcher（如 `scripts/run-node.mjs`）设了这个时，Matrix QA 复用那条日志路径，不再起自己的 tee。                                                                                                       |

---

> ## Output artifacts

## 输出产物

> Written to `--output-dir`:
>
> * `matrix-qa-report.md` - Markdown protocol report (what passed, failed, was skipped, and why).
> * `matrix-qa-summary.json` - Structured summary suitable for CI parsing and dashboards.
> * `matrix-qa-observed-events.json` - Observed Matrix events from the driver and observer clients. Bodies are redacted unless `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT=1`; approval metadata is summarized with selected safe fields and truncated command preview.
> * `matrix-qa-output.log` - Combined stdout/stderr from the run. If `OPENCLAW_RUN_NODE_OUTPUT_LOG` is set, the outer launcher's log is reused instead.

写到 `--output-dir`：

- `matrix-qa-report.md`：Markdown 协议报告（通过、失败、跳过及原因）。
- `matrix-qa-summary.json`：结构化 summary，适合 CI 解析和仪表板。
- `matrix-qa-observed-events.json`：driver 和 observer 客户端观察到的 Matrix 事件。除非 `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT=1`，否则正文脱敏；批准元数据用选定的安全字段做总结、命令预览截断。
- `matrix-qa-output.log`：本次运行合并的 stdout / stderr。设了 `OPENCLAW_RUN_NODE_OUTPUT_LOG` 时，复用外层 launcher 的日志。

> The default output dir is `<repo>/.artifacts/qa-e2e/matrix-<timestamp>` so successive runs do not overwrite each other.

默认输出目录是 `<repo>/.artifacts/qa-e2e/matrix-<时间戳>`，连续多次运行不会互相覆盖。

---

> ## Triage tips

## 排查小贴士

> * **Run hangs near the end:** `matrix-js-sdk` native crypto handles can outlive the harness. The default forces a clean `process.exit` after artifact write; if you have unset `OPENCLAW_QA_MATRIX_DISABLE_FORCE_EXIT=1`, expect the process to linger.
> * **Cleanup error:** look for the printed recovery command (a `docker compose ... down --remove-orphans` invocation) and run it manually to release the homeserver port.
> * **Flaky negative-assertion windows in CI:** lower `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS` (default 8 s) when CI is fast; raise it on slow shared runners.
> * **Need redacted bodies for a bug report:** rerun with `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT=1` and attach `matrix-qa-observed-events.json`. Treat the resulting artifact as sensitive.
> * **Different Tuwunel version:** point `OPENCLAW_QA_MATRIX_TUWUNEL_IMAGE` at the version under test. The lane checks in only the pinned default image.

- **快结束时挂住**：`matrix-js-sdk` 原生 crypto 句柄可能比 harness 活得久。默认在产物写完后强制干净 `process.exit`；如果你设了 `OPENCLAW_QA_MATRIX_DISABLE_FORCE_EXIT=1` 把它关掉，那进程会拖一会儿。
- **清理出错**：看打印出来的恢复命令（一条 `docker compose ... down --remove-orphans`），手动跑一下释放 homeserver 端口。
- **CI 里负向断言窗口抖**：CI 快时调低 `OPENCLAW_QA_MATRIX_NO_REPLY_WINDOW_MS`（默认 8 秒）；慢的共享 runner 上调高。
- **写 bug 报告需要脱敏正文**：用 `OPENCLAW_QA_MATRIX_CAPTURE_CONTENT=1` 重跑，附 `matrix-qa-observed-events.json`。把出来的产物当作敏感数据对待。
- **换 Tuwunel 版本**：把 `OPENCLAW_QA_MATRIX_TUWUNEL_IMAGE` 指向被测版本。lane 默认只 check in 一个钉死的镜像。

---

> ## Live transport contract

## 实时传输契约

> Matrix is one of three live transport lanes (Matrix, Telegram, Discord) that share a single contract checklist defined in [QA overview → Live transport coverage](/concepts/qa-e2e-automation#live-transport-coverage). `qa-channel` remains the broad synthetic suite and is intentionally not part of that matrix.

Matrix 是三条共享同一份契约清单的实时传输 lane（Matrix、Telegram、Discord）之一，清单定义在 [QA 总览 → 实时传输覆盖](/concepts/qa-e2e-automation#live-transport-coverage)。`qa-channel` 仍然是宽泛的合成套件，刻意不进这个矩阵。

---

> ## Related

## 相关

> * [QA overview](/concepts/qa-e2e-automation) - overall QA stack and live transport contract
> * [QA Channel](/channels/qa-channel) - synthetic channel adapter for repo-backed scenarios
> * [Testing](/help/testing) - running tests and adding QA coverage
> * [Matrix](/channels/matrix) - the channel plugin under test

- [QA 总览](/concepts/qa-e2e-automation)：整体 QA 栈和实时传输契约
- [QA Channel](/channels/qa-channel)：仓库内场景用的合成通道适配器
- [Testing](/help/testing)：跑测试和加 QA 覆盖
- [Matrix](/channels/matrix)：被测的通道插件
