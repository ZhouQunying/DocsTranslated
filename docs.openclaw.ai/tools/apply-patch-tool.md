# apply_patch tool

> Apply file changes using a structured patch format. This is ideal for multi-file
> or multi-hunk edits where a single `edit` call would be brittle.

用结构化的 patch 格式改文件。适合跨多文件、多 hunk 的修改 —— 这种场景下单次 `edit` 调用容易出错。

> The tool accepts a single `input` string that wraps one or more file operations:

工具接受单个 `input` 字符串,里面包一份或多份文件操作:

```
*** Begin Patch
*** Add File: path/to/file.txt
+line 1
+line 2
*** Update File: src/app.ts
@@
-old line
+new line
*** Delete File: obsolete.txt
*** End Patch
```

## 参数

> - `input` (required): Full patch contents including `*** Begin Patch` and `*** End Patch`.

- `input`(必填):完整的 patch 内容,含 `*** Begin Patch` 和 `*** End Patch`。

## 说明

> - Patch paths support relative paths (from the workspace directory) and absolute paths.
> - `tools.exec.applyPatch.workspaceOnly` defaults to `true` (workspace-contained). Set it to `false` only if you intentionally want `apply_patch` to write/delete outside the workspace directory.
> - Use `*** Move to:` within an `*** Update File:` hunk to rename files.
> - `*** End of File` marks an EOF-only insert when needed.
> - Available by default for OpenAI and OpenAI Codex models. Set
>   `tools.exec.applyPatch.enabled: false` to disable it.
> - Optionally gate by model via
>   `tools.exec.applyPatch.allowModels`.
> - Config is only under `tools.exec`.

- patch 路径支持相对路径(相对工作区目录)和绝对路径。
- `tools.exec.applyPatch.workspaceOnly` 默认 `true`(限定在工作区内)。只有当你确实想让 `apply_patch` 写或删工作区外的文件时,才设成 `false`。
- 在 `*** Update File:` hunk 里用 `*** Move to:` 重命名文件。
- 需要"仅在文件末尾插入"时用 `*** End of File`。
- OpenAI 和 OpenAI Codex 模型默认开启。设 `tools.exec.applyPatch.enabled: false` 关掉。
- 可选按模型放行:`tools.exec.applyPatch.allowModels`。
- 配置只放在 `tools.exec` 下。

## 例子

```json
{
  "tool": "apply_patch",
  "input": "*** Begin Patch\n*** Update File: src/index.ts\n@@\n-const foo = 1\n+const foo = 2\n*** End Patch"
}
```

## 相关

> - Diffs — Read-only diff viewer for change presentation.
> - Exec tool — Shell command execution from the agent.
> - Code execution — Sandboxed remote Python analysis with xAI.

- [Diffs](/tools/diffs) —— 只读的 diff 查看器,用来展示改动。
- [Exec tool](/tools/exec) —— agent 跑 shell 命令。
- [Code execution](/tools/code-execution) —— xAI 的沙箱化远程 Python 分析。
