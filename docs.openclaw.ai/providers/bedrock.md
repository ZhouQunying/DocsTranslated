# Amazon Bedrock

## 架构精读

> 跳过不影响阅读翻译正文。

### AWS 凭证链 vs API 密钥——为什么不用 API key？

Bedrock 认证使用 AWS SDK 默认凭证链（环境变量 → AWS 配置文件 → IAM 角色），而非 API 密钥。这跟 Anthropic/OpenAI 的 `export API_KEY="sk-..."` 模式完全不同。

这跟 AWS 的安全哲学是一个思路。AWS 不鼓励把长期凭证（access key）硬编码在环境变量中。生产环境推荐 IAM 角色（EC2 实例角色、EKS 服务账户）——临时凭证，自动轮换，最小权限。Bedrock 作为 AWS 服务，继承了这个安全模型。

对 OpenClaw 来说，这意味着三种认证场景：
- **开发环境**：access key（快速但不安全）
- **CI/CD**：AWS profile（持久化但需要管理）
- **生产环境**：IAM role（零配置、自动轮换、最小权限）

代价是入门复杂度比 API key 高。你需要配置 AWS CLI 或设置 IAM 角色。但这是 AWS 生态的标准成本——任何 AWS 服务都有这个门槛。

### Converse API——为什么不用 Bedrock 原生 API？

OpenClaw 通过 Bedrock Converse API 路由模型调用，而非 Bedrock 的原生 InvokeModel API。Converse API 是 AWS 2024 年推出的统一 API，把不同模型提供商（Anthropic、Meta、Mistral）的差异抽象掉了。

这跟 OpenClaw 自身的多提供者抽象是一个思路。Converse API 是 AWS 层面的多模型抽象——你写一次 Converse 调用代码，可以切换到 Claude、Llama、Mistral 而不改代码。OpenClaw 选择 Converse API 是因为它跟 OpenClaw 的抽象层对齐——两层抽象叠加，简化了集成。

---

OpenClaw can use Amazon Bedrock models via its Bedrock Converse streaming provider. Bedrock auth uses the AWS SDK default credential chain, not an API key.

OpenClaw 可以通过其 Bedrock Converse 流式提供者使用 Amazon Bedrock 模型。Bedrock 认证使用 AWS SDK 默认凭证链,而非 API 密钥。

## Getting started / 入门

### Access keys / env vars / 访问密钥 / 环境变量

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
openclaw onboard
# Choose "Amazon Bedrock"
```

### AWS profile / AWS 配置文件

```bash
# Configure AWS CLI
aws configure --profile myprofile

# Use the profile
export AWS_PROFILE="myprofile"
openclaw onboard
# Choose "Amazon Bedrock"
```

### IAM role (EC2/EKS) / IAM 角色

When running on EC2 or EKS with an instance profile or service account, Bedrock auth uses the attached role automatically.

在具有实例配置文件或服务账户的 EC2 或 EKS 上运行时,Bedrock 认证自动使用附加的角色。

## Configuration / 配置

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "amazon-bedrock/anthropic.claude-opus-4-6-v1:0"
      }
    }
  }
}
```

## Model routing / 模型路由

OpenClaw routes `amazon-bedrock/*` models through the Bedrock Converse API. Model IDs follow AWS Bedrock model ARN patterns.

OpenClaw 通过 Bedrock Converse API 路由 `amazon-bedrock/*` 模型。模型 ID 遵循 AWS Bedrock 模型 ARN 模式。

## Related / 相关

- [Provider directory](/providers) — 所有提供者列表
- [Models](/providers/models) — 模型配置
