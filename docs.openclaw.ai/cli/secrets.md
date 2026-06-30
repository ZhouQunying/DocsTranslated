# `openclaw secrets`

## 架构精读

> 跳过不影响阅读翻译正文。

### 凭证管理——为什么需要专门的命令？

`openclaw secrets` 管理凭证（API 密钥、OAuth 令牌）：

- **`secrets list`**：列出已存储凭证（provider + 类型 + 状态）
- **`secrets set <provider>`**：设置凭证（交互式输入或环境变量）
- **`secrets remove <provider>`**：删除凭证
- **`secrets test <provider>`**：测试凭证有效性

这跟 `aws configure` 和 `gcloud auth` 是一个思路——管理云服务凭证（设置、删除、测试）。凭证管理让用户知道"哪些凭证已配置、是否有效"。

### 凭证存储——为什么用加密存储而非明文？

凭证存储在加密文件中（`~/.openclaw/secrets.enc`），而非明文配置文件。

这跟 macOS Keychain 和 Linux Secret Service 是一个思路——凭证加密存储（需要解锁才能访问），防止"配置文件泄露导致凭证泄露"。加密存储是"纵深防御"的一层。

---

Manages credentials (API keys, OAuth tokens): `secrets list` (stored with provider/type/status), `secrets set <provider>` (interactive or env var), `secrets remove <provider>`, `secrets test <provider>` (validity). Credentials stored encrypted (`~/.openclaw/secrets.enc`), not plaintext.

管理凭证（API 密钥、OAuth 令牌）：`secrets list`（已存储，含 provider/类型/状态）、`secrets set <provider>`（交互式或环境变量）、`secrets remove <provider>`、`secrets test <provider>`（有效性）。凭证加密存储（`~/.openclaw/secrets.enc`），非明文。
