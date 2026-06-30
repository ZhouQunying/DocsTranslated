# `openclaw wiki`

## 架构精读

> 跳过不影响阅读翻译正文。

### 知识库管理——为什么需要专门的命令？

`openclaw wiki` 管理本地知识库（编译后的知识文档）：

- **`wiki init`**：初始化知识库目录结构
- **`wiki ingest <path>`**：导入外部内容（保留原始 frontmatter）
- **`wiki compile`**：编译知识库（生成索引和摘要）
- **`wiki search <query>`**：搜索知识库
- **`wiki lint`**：检查知识库结构问题

这跟 Jekyll 的 `jekyll build` / `jekyll serve` 是一个思路——静态站点生成器（Markdown → 编译后的 HTML + 索引）。知识库是"编译后的文档"，支持快速搜索。

### 矛盾检测——为什么需要 `wiki lint`？

`wiki lint` 检测知识库中的矛盾（如两个文档对同一问题给出不同答案）和过期信息。

这跟 TypeScript 的类型检查是一个思路——编译时检测错误（类型不匹配/矛盾），而非运行时才发现。矛盾检测让知识库保持内部一致性。

---

Manages local knowledge base (compiled documents): `wiki init` (directory structure), `wiki ingest <path>` (import with frontmatter), `wiki compile` (generate indexes/digests), `wiki search <query>`, `wiki lint` (detect contradictions/stale info). Like Jekyll static site generator (Markdown → compiled HTML + indexes).

管理本地知识库（编译后的文档）：`wiki init`（目录结构）、`wiki ingest <path>`（导入保留 frontmatter）、`wiki compile`（生成索引/摘要）、`wiki search <query>`、`wiki lint`（检测矛盾/过期信息）。类似 Jekyll 静态站点生成器（Markdown → 编译后的 HTML + 索引）。
