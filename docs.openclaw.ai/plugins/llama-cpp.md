# llama.cpp Provider

## 架构精读

> 跳过不影响阅读翻译正文。

### 为什么把 node-llama-cpp 拆成独立插件？

如果把 node-llama-cpp 执行环境放在主包中，npm 升级时会覆盖自定义编译。OpenClaw 把 GGUF 嵌入支持拆成独立的 `llama-cpp` 插件，管理原生依赖。这就像 Linux 内核模块与用户空间工具分离——内核模块需要针对特定硬件编译，用户空间工具可以独立升级。好处是常规包管理器升级不会影响自定义设置，坏处是需要额外安装步骤。

配置指向 `memorySearch.provider: "local"` 时使用此插件。系统自动选择 embeddinggemma 变体，也可指向本地任何 GGUF 资产。Node 24 提供最无缝的设置体验。如果使用 pnpm 从源码工作，需要批准并重新编译底层组件。

---

本指南介绍如何添加授权的 GGUF 向量扩展到你的系统。当你需要设备端搜索向量、将配置设置为本地选项或获取管理底层执行环境的特定附加组件时阅读此页面。

## 核心细节

`llama-cpp` 扩展作为授权的第三方附加组件，在你的机器上启用 GGUF 嵌入。它管理将搜索设置配置为本地时所需的 `node-llama-cpp` 执行环境。

使用设备端记忆向量前必须设置此附加组件：

```bash
openclaw plugins install @openclaw/llama-cpp-provider
```

因为主 npm 分发省略了执行环境，将此原生需求放在独立附加组件中可防止常规包管理器升级擦除自定义设置。

## 设置说明

调整向量搜索设置以使用设备端选项：

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "local",
        local: {
          modelPath: "hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf",
        },
      },
    },
  },
}
```

系统自动选择特定的 embeddinggemma 变体，开发者也可将配置路径指向机器上存储的任何 GGUF 资产。

## 执行环境

Node 24 版本提供最无缝的设置体验。如果通过 pnpm 直接从源码工作，可能需要批准并重新编译底层组件：

```bash
pnpm approve-builds
pnpm rebuild node-llama-cpp
```

如果偏好文档所称的"更低摩擦的本地嵌入"，考虑使用 LM Studio 或 Ollama 等替代平台。

## 相关

- [Memory LanceDB](/plugins/memory-lancedb)
- [Ollama provider](/providers/ollama)
