# `openclaw completion`

## 架构精读

> 跳过不影响阅读翻译正文。

### Shell 补全——为什么需要专门的命令？

`openclaw completion` 生成命令行补全脚本（bash/zsh/fish）：

```
openclaw completion bash > ~/.openclaw-completion.bash
source ~/.openclaw-completion.bash
```

这跟 `kubectl completion bash` 是一个思路——生成补全脚本，输入 `openclaw <TAB>` 时自动提示子命令和选项。

### 多命令行环境支持——为什么覆盖 bash/zsh/fish？

不同用户用不同的命令行环境（bash 是默认，zsh 是 macOS 默认，fish 是现代化选择）。生成器覆盖三种主流命令行环境，用户选择自己用的。

这跟 Docker 的补全脚本是一个思路——覆盖 bash/zsh/fish，不强制用户切换命令行环境。

---

Generates shell completion scripts (bash/zsh/fish): `openclaw completion bash > ~/.openclaw-completion.bash`. Enables TAB auto-completion for subcommands and options. Covers three mainstream shells (bash, zsh, fish).

生成命令行补全脚本（bash/zsh/fish）：`openclaw completion bash > ~/.openclaw-completion.bash`。启用 TAB 自动补全子命令和选项。覆盖三种主流命令行环境（bash、zsh、fish）。
