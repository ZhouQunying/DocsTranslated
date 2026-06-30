# `openclaw reset`

## 架构精读

> 跳过不影响阅读翻译正文。

### 重置范围——为什么提供多级重置？

`openclaw reset` 提供多级重置：

- **`--sessions`**：只清除会话数据（保留配置和配对）
- **`--pairing`**：只清除配对注册（保留会话和配置）
- **`--all`**：清除所有状态（会话 + 配对 + 运行时数据）

这跟 Chrome 的"清除浏览数据"是一个思路——可以选择清除 cookie、缓存、历史记录中的特定组合，而非一刀切全清。多级重置让用户精确控制"清除什么、保留什么"。

### 确认机制——为什么需要显式确认？

重置操作需要显式确认（`--yes` 标志或交互式确认），防止误操作。

这跟 `rm -rf` 的保护机制是一个思路——破坏性操作需要显式确认。没有确认机制的话，一次手抖可能导致所有会话数据丢失。

---

Provides multi-level reset: `--sessions` (clear sessions only), `--pairing` (clear pairing registrations only), `--all` (clear everything). Requires explicit confirmation (`--yes` flag or interactive prompt) to prevent accidental data loss.

提供多级重置：`--sessions`（只清除会话）、`--pairing`（只清除配对注册）、`--all`（清除一切）。需要显式确认（`--yes` 标志或交互式提示）防止意外数据丢失。
