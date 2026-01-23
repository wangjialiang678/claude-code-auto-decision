# Sync Skill

将项目改动同步到 Claude Code 生产环境 (~/.claude/)。

## 触发条件

当用户说以下内容时自动触发：
- "同步"、"同步到生产"、"部署"
- "帮我更新"、"更新到生产环境"
- "让修改生效"
- "sync"、"deploy"
- "检查更新"、"check updates"

## 执行步骤

### 方式 1: 自动检查更新（推荐）

```bash
cd /Users/michael/projects/claude-code-auto-decision && ./check-updates.sh
```

这会自动：
1. 检查 Git 远程更新
2. 检查 hooks/skills/rules/config 差异
3. 运行测试验证
4. 输出彩色状态报告和具体建议

### 方式 2: 直接同步

如果用户明确要求立即同步：

1. 先运行 `./sync.sh --diff` 显示差异
2. 如果有差异，询问用户是否继续
3. 用户确认后运行 `./sync.sh` 执行同步

## 重要提示

**规则文件更新策略**：

如果 `rules.md` 有差异，需要提醒用户：

```
⚠️ 规则文件有更新，但 sync.sh 会保留你的现有规则。

如果你没有自定义规则，建议：
  1. 备份: cp ~/.claude/memory-bank/rules.md ~/.claude/memory-bank/rules.md.backup
  2. 更新: cp rules/global-rules.md ~/.claude/memory-bank/rules.md
  3. 同步: ./sync.sh

如果有自定义规则，建议手动合并：
  diff -u ~/.claude/memory-bank/rules.md rules/global-rules.md
```

详细说明见: `docs/update-strategy.md`

## 命令参考

```bash
# 完整更新检查（推荐）
cd /Users/michael/projects/claude-code-auto-decision && ./check-updates.sh

# 自动同步代码（不包括规则）
cd /Users/michael/projects/claude-code-auto-decision && ./check-updates.sh --auto-sync

# 查看差异
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh --diff

# 预览同步（不实际执行）
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh --dry-run

# 执行同步
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh
```

## 同步策略

| 文件类型 | sync.sh 行为 | 说明 |
|---------|-------------|------|
| hooks/ | 完全覆盖 | 核心代码，总是更新 |
| skills/ | 完全覆盖 | 辅助功能，总是更新 |
| config.json | 仅首次创建 | 保留用户配置 |
| rules.md | 仅首次创建 | 保留用户规则，需手动更新 |

## 相关文件

- [sync.sh](../../../sync.sh) - 同步脚本
- [check-updates.sh](../../../check-updates.sh) - 更新检查工具
- [docs/update-strategy.md](../../../docs/update-strategy.md) - 更新策略文档
