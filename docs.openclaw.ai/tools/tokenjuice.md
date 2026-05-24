# Tokenjuice

> `tokenjuice` is an optional bundled plugin that compacts noisy `exec` and `bash`
> tool results after the command has already run.

`tokenjuice` 是一个可选的内置插件,在命令已经跑完之后,把吵闹的 `exec` 和 `bash` 工具结果压紧。

> It changes the returned `tool_result`, not the command itself. Tokenjuice does
> not rewrite shell input, rerun commands, or change exit codes.

它改的是返回的 `tool_result`,不是命令本身。Tokenjuice 不改写 shell 输入,不重跑命令,也不动退出码。

> Today this applies to PI embedded runs and OpenClaw dynamic tools in the Codex
> app-server harness. Tokenjuice hooks OpenClaw's tool-result middleware and
> trims the output before it goes back into the active harness session.

目前它对 PI 嵌入式运行和 Codex app-server harness 里的 OpenClaw 动态工具生效。Tokenjuice 钩住 OpenClaw 的工具结果中间件,在输出回到当前 harness 会话之前先剪一下。

## 启用插件

> Fast path:

最快的方式:

```bash
openclaw config set plugins.entries.tokenjuice.enabled true
```

> Equivalent:

等价的:

```bash
openclaw plugins enable tokenjuice
```

> OpenClaw already ships the plugin. There is no separate `plugins install`
> or `tokenjuice install openclaw` step.

OpenClaw 自带这个插件。不需要单独跑 `plugins install` 或 `tokenjuice install openclaw`。

> If you prefer editing config directly:

如果你倾向直接改配置:

```json5
{
  plugins: {
    entries: {
      tokenjuice: {
        enabled: true,
      },
    },
  },
}
```

## tokenjuice 改什么

> - Compacts noisy `exec` and `bash` results before they are fed back into the session.
> - Keeps the original command execution untouched.
> - Preserves exact file-content reads and other commands that tokenjuice should leave raw.
> - Stays opt-in: disable the plugin if you want verbatim output everywhere.

- 在吵闹的 `exec` 和 `bash` 结果回灌进会话之前把它们压紧。
- 不动原始的命令执行。
- 对精确文件内容读取、以及其他应当保持原貌的命令,保留原样。
- 始终是可选的:想到处都拿原始输出,关掉插件就行。

## 验证它在工作

> 1. Enable the plugin.
> 2. Start a session that can call `exec`.
> 3. Run a noisy command such as `git status`.
> 4. Check that the returned tool result is shorter and more structured than the raw shell output.

1. 启用插件。
2. 开一个能调 `exec` 的会话。
3. 跑一条吵闹的命令,比如 `git status`。
4. 检查返回的工具结果比原始 shell 输出更短、结构更清楚。

## 关掉插件

```bash
openclaw config set plugins.entries.tokenjuice.enabled false
```

> Or:

或者:

```bash
openclaw plugins disable tokenjuice
```

## 相关

> - [Exec tool](/tools/exec)
> - [Thinking levels](/tools/thinking)
> - [Context engine](/concepts/context-engine)

- [Exec tool](/tools/exec)
- [思考级别](/tools/thinking)
- [上下文引擎](/concepts/context-engine)
