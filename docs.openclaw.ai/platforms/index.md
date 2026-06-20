# Platforms / 平台

## 架构精读

> 跳过不影响阅读翻译正文。

### Gateway 作为跨平台核心——同一进程，不同外壳

OpenClaw 的核心是一个 TypeScript 编写的 Gateway 进程。不管你是 macOS、Windows、Linux、Android 还是 iOS，运行的都是同一个 Gateway。平台差异不在 Gateway 内部，而在**进程外部**——谁来启动它、谁来管理它的生命周期、谁来提供系统集成。

这跟 Kubernetes 是一个思路。Kubernetes 的 kube-apiserver 在所有平台上都是同一个二进制，但启动方式不同：Linux 上用 systemd，macOS 开发环境用 minikube，云托管用 EKS/GKE。OpenClaw 也是这样：Gateway 是统一的控制平面，平台只是不同的"部署目标"。

macOS 有 menu bar companion app，Windows 有 Hub，Android/iOS 是 companion node app。Linux 最纯粹——直接跑 Gateway，没有额外外壳。这反映了每个平台的用户预期：macOS/Windows 用户期望桌面集成，移动用户期望手机 app，Linux 用户期望 CLI。

### 进程管理抽象——launchd / systemd / Scheduled Task

OpenClaw 的 `openclaw gateway install` 命令把 Gateway 安装为系统服务，但底层用的是每个 OS 原生的服务管理器：

- **macOS**：LaunchAgent（`ai.openclaw.gateway`）
- **Linux/WSL2**：systemd user service（`openclaw-gateway.service`）
- **Windows**：Scheduled Task（per-user Startup folder 作为后备）

这跟 Docker 的 daemon 启动方式是一个思路。Docker 在 Linux 上用 systemd，在 macOS 上用 launchd，在 Windows 上用服务。OpenClaw 也是——用 `openclaw gateway install` 一个命令抽象掉三个 OS 的服务管理差异。

`openclaw doctor` 的设计也很巧妙——它不仅诊断问题，还**主动提供服务安装/修复选项**。这跟 `brew doctor` 是一个思路：不是只告诉你哪里错了，而是帮你修。doctor 成了安装和修复的统一入口。

### Node 架构——hub-spoke 模式

每个平台把自己注册为 Gateway 的 **node**。macOS app 暴露 Canvas/Camera/Screen，Windows Hub 暴露 canvas/screen/camera/notifications，Android/iOS 暴露 Canvas/Screen/Camera/Location/Talk mode。Gateway 是中心 hub，nodes 是 spoke。

这跟 Kubernetes 的 node 注册是一个思路。kubelet 向 control plane 注册自己的能力和状态，control plane 就可以调度 pod 到它。OpenClaw 的 node 也是这样：向 Gateway 注册自己声明的能力（Canvas、Camera、Screen 等），Gateway 就可以转发对应命令到它。

关键设计是**能力声明 + 策略控制**。Node 声明"我能做什么"，Gateway 的策略决定"允许你做什么"。隐私敏感命令如 `screen.record`、`camera.snap` 需要显式 `gateway.nodes.allowCommands` opt-in。这跟 Kubernetes 的 RBAC 是一个思路——能力存在是一回事，权限授予是另一回事。

### 设备配对信任模型——zero-trust

设备连接 Gateway 前必须经过 **pairing**（配对）和 **approve**（审批）。这是 zero-trust 网络模型——不假设任何设备可信，每个设备必须显式批准。

这跟 Tailscale 的 ACL 是一个思路。Tailscale 不假设同一 tailnet 内的设备互相信任，每台设备的访问权限由 ACL 策略控制。OpenClaw 的设备配对也是这样：即使是同一 LAN 内的设备，也必须经过 Gateway 主机的审批才能连接。

Android/iOS 的远程连接要求更严格：tailnet/公共主机的配对**不**使用原始 tailnet IP 的 `ws://` 端点，必须用 Tailscale Serve 或其他 `wss://` URL。这防止了中间人攻击——加密传输是远程配对的前提。
