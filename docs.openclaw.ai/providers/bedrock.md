# Amazon Bedrock

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
