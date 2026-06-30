# `openclaw setup`

## 架构精读

> 跳过不影响阅读翻译正文。

### 系统准备——为什么需要专门的 setup 命令？

`openclaw setup` 准备系统环境（安装依赖、创建目录、设置权限）：

- **安装依赖**：Node.js 包、系统工具（如 ffmpeg）
- **创建目录**：状态目录、日志目录、缓存目录
- **设置权限**：目录权限、文件权限

这跟 `brew install` 的 post-install 脚本是一个思路——安装完包后自动准备环境（创建目录、设置权限、初始化配置）。用户不需要手动执行这些步骤。

### 与 onboard 的区别——为什么分开？

- **`setup`**：准备系统环境（无交互）
- **`onboard`**：交互式配置引导（有交互）

这跟 `apt install` vs `dpkg-reconfigure` 是一个思路——安装（准备环境）和配置（交互式设置）是两个不同的步骤。

---

Prepares system environment: installs dependencies (Node.js packages, system tools), creates directories (state, logs, cache), and sets permissions. Non-interactive. Differs from `onboard` which is interactive configuration guidance.

准备系统环境：安装依赖（Node.js 包、系统工具）、创建目录（状态、日志、缓存）、设置权限。无交互。区别于 `onboard` 的交互式配置引导。
