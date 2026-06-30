# `openclaw docs`

## 架构精读

> 跳过不影响阅读翻译正文。

### 文档查询——为什么需要专门的命令？

`openclaw docs` 查询内置文档（命令帮助、配置参考）：

```
openclaw docs config     # → 打开配置参考页面
openclaw docs channels   # → 打开通道配置页面
```

这跟 `man` 和 `git help` 是一个思路——命令行直接查看文档，不需要打开浏览器。

### 本地 vs 在线——为什么提供本地文档？

- **本地文档**：离线可用，版本匹配（安装版本对应的文档）
- **在线文档**：实时更新，但需要网络

这跟 Rust 的 `rustup doc` 是一个思路——本地文档（离线 + 版本匹配）和在线文档（最新 + 需要网络）互补。

---

Queries built-in documentation: `openclaw docs config` (opens config reference), `openclaw docs channels` (opens channel config). Local docs are offline-available and version-matched; online docs are real-time but require network.

查询内置文档：`openclaw docs config`（打开配置参考）、`openclaw docs channels`（打开通道配置）。本地文档离线可用且版本匹配；在线文档实时更新但需要网络。
