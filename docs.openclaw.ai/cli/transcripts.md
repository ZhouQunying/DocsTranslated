# `openclaw transcripts`

## 架构精读

> 跳过不影响阅读翻译正文。

### 会话记录查询——为什么需要专门的命令？

`openclaw transcripts` 查询已存储的会话记录：

- **`transcripts list`**：列出已存储会话（选择器 + 时间戳 + 文件位置）
- **`transcripts path <id>`**：获取会话记录文件路径
- **`transcripts list --json`**：结构化输出（自动化友好）

这跟 `kubectl logs` 是一个思路——查询已存储的日志（会话记录），支持列表、路径查询、结构化输出。

### 多会话组织——为什么按日期分目录？

同一天多个会话时，每个会话存储在独立的兄弟目录下，父目录按日期命名：

```
2024-01-15/
  session-abc/
  session-def/
```

这跟日志轮转的日期目录是一个思路——`/var/log/2024/01/15/app.log`。日期目录让"找某天的会话"变得简单，避免单目录文件过多。

### 摘要缺失——为什么需要手动重新生成？

会话摘要通常在会话结束时自动生成。如果录制仍在进行或 provider 出错，摘要可能缺失。可以手动触发重新生成。

这跟 CI 的"重试失败任务"是一个思路——自动流程失败时，提供手动重试入口。手动重新生成让"摘要缺失"不是永久问题。

---

Queries stored session records: `transcripts list` (selector + timestamp + file path), `transcripts path <id>`, `transcripts list --json` (structured output). Multiple daily sessions organized in date-grouped sibling directories. Missing summaries can be manually regenerated if auto-generation failed.

查询已存储会话记录：`transcripts list`（选择器 + 时间戳 + 文件路径）、`transcripts path <id>`、`transcripts list --json`（结构化输出）。同一天多个会话按日期分目录组织。摘要缺失时可手动重新生成（自动生成失败时）。
