# `openclaw path`

## 架构精读

> 跳过不影响阅读翻译正文。

### 路径查询——为什么需要专门的命令？

`openclaw path` 查询关键路径（配置目录、状态目录、日志目录）：

```
openclaw path config   # → ~/.openclaw/openclaw.json5
openclaw path state    # → ~/.openclaw/state/
openclaw path logs     # → ~/.openclaw/logs/
```

这跟 `npm root` / `npm prefix` 是一个思路——查询包管理器使用的关键路径，不需要记住默认值。

### 为什么需要路径查询而非文档？

路径可能因环境不同而变化（如 `$OPENCLAW_HOME` 覆盖默认路径）。`openclaw path` 返回**实际使用的路径**，而非文档中的默认值。

这跟 `python -c "import sys; print(sys.prefix)"` 是一个思路——返回运行时实际路径，而非文档中的默认安装路径。

---

Queries key paths: `openclaw path config` (config file), `openclaw path state` (state directory), `openclaw path logs` (log directory). Returns actual runtime paths (which may differ from defaults due to environment variables like `$OPENCLAW_HOME`).

查询关键路径：`openclaw path config`（配置文件）、`openclaw path state`（状态目录）、`openclaw path logs`（日志目录）。返回运行时实际路径（可能因环境变量如 `$OPENCLAW_HOME` 而不同于默认值）。
