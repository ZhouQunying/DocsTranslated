# vLLM (本地模型)

## 架构精读

> 跳过不影响阅读翻译正文。

### PagedAttention——为什么 vLLM 是高吞吐首选？

vLLM 的核心创新是 PagedAttention——把 KV cache 分成固定大小的页，像操作系统的虚拟内存一样管理。这跟 OS 的分页内存管理是一个思路。传统推理引擎为每个请求预分配最大序列长度的 KV cache，导致内存碎片和浪费。vLLM 按需分页，内存利用率从 ~20% 提升到 >90%。

对 OpenClaw agent 来说，vLLM 是**自托管生产推理**的首选。当你需要在自己的 GPU 上运行开源模型（如 Llama、Mistral），vLLM 的吞吐量比 Hugging Face Transformers 高 5-24 倍。

---

vLLM 提供带 OpenAI 兼容 API 的高吞吐本地模型服务。

## Getting started / 入门

```bash
export VLLM_API_KEY="..."
openclaw onboard
# Choose "vLLM (本地模型)"
```

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "vllm/model-name"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `vllm/*` models through the vLLM (本地模型) API.

OpenClaw 通过 vLLM (本地模型) API 路由 `vllm/*` 模型。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
