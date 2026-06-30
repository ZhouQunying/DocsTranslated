# `openclaw migrate`

## 架构精读

> 跳过不影响阅读翻译正文。

### 数据迁移——为什么需要专门的迁移命令？

`openclaw migrate` 执行结构化数据迁移（会话索引、配对注册、状态目录、配置模式）：

- **会话索引迁移**：旧格式会话数据迁移到新格式
- **配对注册迁移**：设备配对数据格式升级
- **状态目录迁移**：运行时状态目录结构调整
- **配置模式迁移**：配置文件字段变更

这跟 Rails 的 `db:migrate` 是一个思路——数据库 schema 变更需要显式迁移脚本（`ALTER TABLE`），而非直接覆盖。迁移命令确保数据完整性（原子操作、回滚支持）。

### Dry-run vs 应用——为什么先预览？

默认 dry-run（只显示将要执行的变更），不实际修改。确认后加 `--apply` 执行。

这跟 Terraform 的 `plan` → `apply` 是一个思路——先预览变更（plan），确认无问题后执行（apply）。dry-run 防止误操作（如意外删除会话数据）。

---

Runs structural data migrations (session indexes, pairing registrations, state directories, config schemas). Default is dry-run (shows planned changes without modifying). Use `--apply` to execute migrations.

执行结构化数据迁移（会话索引、配对注册、状态目录、配置模式）。默认 dry-run（显示计划变更但不修改）。用 `--apply` 执行迁移。
