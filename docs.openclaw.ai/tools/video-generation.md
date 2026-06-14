# 视频生成

OpenClaw agent 可从文本提示、参考图像或现有视频生成视频。支持十六个提供者后端，每个有不同的模型选项、输入模式和功能集。agent 根据配置和可用的 API 密钥自动选择正确的提供者。

`video_generate` 工具仅在至少一个视频生成提供者可用时才出现。如在 agent 工具中看不到它，设置提供者 API 密钥或配置 `agents.defaults.videoGenerationModel`。

OpenClaw 将视频生成视为三种运行时模式：

- `generate`——无参考媒体的文本到视频请求
- `imageToVideo`——请求包含一个或多个参考图像
- `videoToVideo`——请求包含一个或多个参考视频

提供者可支持这些模式的任意子集。工具在提交前验证活跃模式，并在 `action=list` 中报告支持的模式。

## 快速开始

1. **配置认证**：设置任何支持提供者的 API 密钥：

```bash
export GEMINI_API_KEY="your-key"
```

2. **选择默认模型（可选）**：

```bash
openclaw config set agents.defaults.videoGenerationModel.primary "google/veo-3.1-fast-generate-preview"
```

3. **请求 agent**：

> Generate a 5-second cinematic video of a friendly lobster surfing at sunset.

agent 自动调用 `video_generate`。无需工具白名单。

## 异步生成的工作原理

视频生成是异步的。当 agent 在会话中调用 `video_generate` 时：

1. OpenClaw 将请求提交给提供者并立即返回任务 id
2. 提供者在后台处理作业（通常 30 秒到几分钟，取决于提供者和分辨率）
3. 视频就绪后，OpenClaw 用内部完成事件唤醒同一会话
4. agent 通过会话的正常可见回复模式告知用户

当作业在进行中时，同一会话中的重复 `video_generate` 调用返回当前任务状态而非启动新生成。使用 `openclaw tasks list` 或 `openclaw tasks show <taskId>` 从 CLI 检查进度。

在会话支持的 agent 运行之外（如直接工具调用），工具回退到内联生成并在同一轮次返回最终媒体路径。

### 任务生命周期

| 状态 | 含义 |
| --- | --- |
| `queued` | 任务已创建，等待提供者接受 |
| `running` | 提供者正在处理（通常 30 秒到几分钟） |
| `succeeded` | 视频就绪；agent 唤醒并发布到对话 |
| `failed` | 提供者错误或超时；agent 携带错误详情唤醒 |

从 CLI 检查状态：

```bash
openclaw tasks list
openclaw tasks show <taskId>
openclaw tasks cancel <taskId>
```

## 支持的提供者

| 提供者 | 默认模型 | 文本 | 图像参考 | 视频参考 | 认证 |
| --- | --- | :---: | --- | --- | --- |
| Alibaba | `wan2.6-t2v` | ✓ | 是（远程 URL） | 是（远程 URL） | `MODELSTUDIO_API_KEY` |
| BytePlus (1.0) | `seedance-1-0-pro-250528` | ✓ | 最多 2 张（仅 I2V 模型） | - | `BYTEPLUS_API_KEY` |
| BytePlus Seedance 2.0 | `dreamica-seedance-2-0-260128` | ✓ | 最多 9 张参考图 | 最多 3 个视频 | `BYTEPLUS_API_KEY` |
| ComfyUI | `workflow` | ✓ | 1 张 | - | `COMFY_API_KEY` 或 `COMFY_CLOUD_API_KEY` |
| DeepInfra | `Pixverse/Pixverse-T2V` | ✓ | - | - | `DEEPINFRA_API_KEY` |
| fal | `fal-ai/minimax/video-01-live` | ✓ | 1 张 | 最多 3 个视频 | `FAL_KEY` |
| Google | `veo-3.1-fast-generate-preview` | ✓ | 1 张 | 1 个视频 | `GEMINI_API_KEY` |
| MiniMax | `MiniMax-Hailuo-2.3` | ✓ | 1 张 | - | `MINIMAX_API_KEY` |
| OpenAI | `sora-2` | ✓ | 1 张 | 1 个视频 | `OPENAI_API_KEY` |
| OpenRouter | `google/veo-3.1-fast` | ✓ | 最多 4 张 | - | `OPENROUTER_API_KEY` |
| Qwen | `wan2.6-t2v` | ✓ | 是（远程 URL） | 是（远程 URL） | `QWEN_API_KEY` |
| Runway | `gen4.5` | ✓ | 1 张 | 1 个视频 | `RUNWAYML_API_SECRET` |
| Together | `Wan-AI/Wan2.2-T2V-A14B` | ✓ | 仅限 I2V 模型 | - | `TOGETHER_API_KEY` |
| Vydra | `veo3` | ✓ | 1 张（`kling`） | - | `VYDRA_API_KEY` |
| xAI | `grok-imagine-video` | ✓ | 1 张首帧或最多 7 张参考图 | 1 个视频 | `XAI_API_KEY` |

运行 `video_generate action=list` 可在运行时检查可用的提供者、模型和模式。

## 相关

- [配置参考](/gateway/configuration-reference)——完整视频生成配置
- [各提供者文档](/providers)——各提供者的详细设置
