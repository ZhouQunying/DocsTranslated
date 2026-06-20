# Gateway logging

## 架构精读

> 跳过不影响阅读翻译正文。

### 两个日志 surface——CLI 日志和 Control UI 日志

OpenClaw 有两个日志"表面"(surface):

**CLI 日志**(终端输出):
- Gateway 启动时在终端输出的日志
- 适合本地开发,开发者直接看终端
- 格式是纯文本,易读

**Control UI 日志**(web 界面):
- 在 Control UI(web 界面)里查看的日志
- 适合远程查看,不需要 SSH 到服务器
- 格式是结构化 JSON,可过滤、可搜索

**为什么需要两个?** 因为使用场景不同:
- 本地开发: 开发者开着终端,直接看 CLI 日志
- 生产环境: 服务器在远程,SSH 看日志麻烦,用 Control UI 更方便
- 调试: CLI 日志实时滚动,Control UI 日志可以暂停、过滤

这跟 **Docker 的 logs 命令 vs Docker Desktop GUI** 是一个思路——CLI 用户用 `docker logs`,GUI 用户用 Docker Desktop 看日志。OpenClaw 的两个日志 surface 也是同样: 覆盖 CLI 用户和 GUI 用户。

### 启动日志——记录关键配置

Gateway 启动时,日志输出关键配置信息:

```
[INFO] Default agent model: anthropic/claude-opus-4-6
[INFO] Session mode: persistent
[INFO] Workspace: ~/.openclaw/workspace
[INFO] Listening on: 0.0.0.0:1455
```

**为什么启动时输出这些?** 因为:
- **确认配置**: 用户可以看到"Gateway 用的是哪个模型、监听哪个端口"
- **诊断问题**: 如果配置错了(如模型名拼错),启动日志立刻显示
- **审计**: 运维人员可以检查"Gateway 启动时的配置是什么"

**这跟 nginx 的启动日志**是一个思路——nginx 启动时输出"listening on port 80"、"worker processes: 4",让用户确认配置。OpenClaw 的启动日志也是同样: 输出关键配置,帮助用户确认。

### 日志级别——INFO / WARN / ERROR / DEBUG

OpenClaw 的日志有四个级别:

- **INFO**: 正常操作(如"session created"、"model switched")
- **WARN**: 警告,但不影响功能(如"API key 快过期了"、"rate limit 接近")
- **ERROR**: 错误,影响功能(如"auth failed"、"model not found")
- **DEBUG**: 调试信息,开发者用(如"request payload: {...}"、"response: {...}")

**为什么需要级别?** 因为不同场景需要不同详细程度:
- 生产环境: 只看 ERROR 和 WARN(噪音少,只看问题)
- 开发环境: 看 INFO、WARN、ERROR(了解正常操作)
- 调试: 看 DEBUG(详细到每个请求/响应)

如果所有日志都显示,生产环境会被 DEBUG 信息淹没。如果只显示 ERROR,开发时看不到 INFO 信息(不知道正常操作发生了什么)。

**这跟 log4j 的日志级别**是一个思路——log4j 有 TRACE、DEBUG、INFO、WARN、ERROR、FATAL 六个级别,可以按级别过滤。OpenClaw 的日志级别也是同样: 按级别过滤,控制详细程度。

### WS log style——WebSocket 日志格式

WebSocket 连接的日志有特殊格式,便于调试:

```
[WS] client connected: 192.168.1.100:54321
[WS] message received: {"type": "chat", "content": "hello"}
[WS] message sent: {"type": "chat", "content": "hi there"}
[WS] client disconnected: 192.168.1.100:54321
```

**为什么 WebSocket 日志需要特殊格式?** 因为 WebSocket 是长连接,一个连接会发送多条消息。如果日志只显示"连接建立"和"连接断开",看不到中间的消息交换,无法调试。WS log style 显示每条消息的发送和接收,让用户看到完整的通信过程。

**这跟 HTTP access log 是一个思路**——nginx 的 access log 记录每个 HTTP 请求(method、URL、status code、response time),不只显示"连接建立"。OpenClaw 的 WS log style 也是同样: 记录每条 WebSocket 消息,不只显示连接状态。

### 日志轮转——防止日志文件过大

OpenClaw 的日志文件会自动轮转(rotate):

- 当日志文件达到一定大小(如 10MB),自动切到新文件
- 保留最近的 N 个日志文件(如 5 个),删除更老的
- 文件名带时间戳(如 `gateway-2026-06-20.log`)

**为什么需要轮转?** 因为日志文件会越来越大:
- 不轮转: 单个文件可能达到 GB 级别,打开慢、备份慢
- 轮转: 每个文件小(如 10MB),打开快、备份快
- 保留最近 N 个: 既有历史日志(调试用),又不占太多磁盘空间

**这跟 logrotate 是一个思路**——Linux 的 logrotate 工具自动轮转日志文件(按大小或时间),保留最近 N 个,删除更老的。OpenClaw 的日志轮转也是同样: 自动轮转,防止文件过大。
