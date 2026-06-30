# `openclaw clawbot`

## 架构精读

> 跳过不影响阅读翻译正文。

### ClawBot 管理——为什么需要专门的命令？

`openclaw clawbot` 管理 ClawBot 实例（预配置的智能体模板）：

- **`clawbot list`**：列出可用 ClawBot 模板
- **`clawbot create <template>`**：从模板创建新智能体
- **`clawbot delete <name>`**：删除智能体

这跟 `cookiecutter` 和 `rails new` 是一个思路——从模板创建新项目（预配置的工具、提示词、模型）。ClawBot 模板让"快速创建特定用途的智能体"变得简单。

### 模板 vs 手动配置——为什么用模板？

- **模板**：预配置（工具 + 提示词 + 模型已选好）
- **手动**：从零开始（需要自己选每个配置）

这跟 Terraform module vs 手写 HCL 是一个思路——module 是预配置的基础设施（VPC + 子网 + 安全组），手写需要自己配置每个资源。模板降低"创建特定用途智能体"的门槛。

---

Manages ClawBot instances (pre-configured agent templates): `clawbot list` (available templates), `clawbot create <template>` (create from template), `clawbot delete <name>`. Templates provide pre-configured tools, prompts, and models; manual setup requires configuring each option from scratch.

管理 ClawBot 实例（预配置的智能体模板）：`clawbot list`（可用模板）、`clawbot create <template>`（从模板创建）、`clawbot delete <name>`。模板提供预配置的工具、提示词和模型；手动配置需要从零开始选每个选项。
