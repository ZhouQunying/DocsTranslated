# `openclaw skills`

## 架构精读

> 跳过不影响阅读翻译正文。

### 技能管理——为什么需要专门的命令？

`openclaw skills` 管理技能（提示词扩展）：

- **`skills search <query>`**：搜索社区技能
- **`skills install <name>`**：安装技能
- **`skills list`**：列出已安装技能
- **`skills uninstall <name>`**：卸载技能
- **`skills update`**：更新所有技能

这跟 `npm search` / `npm install` / `npm list` 是一个思路——包管理器的标准操作（搜索、安装、列表、卸载、更新）。

### 技能工坊——为什么有"草稿"概念？

技能工坊（Skill Workshop）管理待应用的技能草稿：

- **草稿**：已创建但未激活的技能
- **应用**：将草稿转为活跃技能

这跟 Git 的 staging area 是一个思路——staged 的文件还没 commit（未生效），commit 后才进入主分支（生效）。草稿让"先预览再激活"成为可能。

---

Manages skills (prompt extensions): `skills search <query>` (community registry), `skills install <name>`, `skills list` (installed), `skills uninstall <name>`, `skills update` (all). Skill Workshop manages pending drafts (created but not active until applied, like Git staging area).

管理技能（提示词扩展）：`skills search <query>`（社区注册表）、`skills install <name>`、`skills list`（已安装）、`skills uninstall <name>`、`skills update`（全部）。技能工坊管理待应用草稿（已创建但未激活，类似 Git staging area）。
