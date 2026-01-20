# Sync Skill

将项目改动同步到 Claude Code 生产环境 (~/.claude/)。

## 触发条件

当用户说以下内容时自动触发：
- "同步"、"同步到生产"
- "帮我更新"、"更新到生产环境"
- "让修改生效"
- "sync"、"deploy"

## 执行步骤

1. 先运行 `./sync.sh --diff` 显示差异
2. 如果有差异，询问用户是否继续
3. 用户确认后运行 `./sync.sh` 执行同步

## 命令

```bash
# 查看差异
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh --diff

# 预览同步（不实际执行）
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh --dry-run

# 执行同步
cd /Users/michael/projects/claude-code-auto-decision && ./sync.sh
```

## 同步策略

| 文件类型 | 策略 |
|---------|------|
| hooks/ | 完全覆盖（核心代码） |
| skills/ | 完全覆盖（辅助功能） |
| config.json | 仅首次创建，保留用户配置 |
| rules.md | 仅首次创建，保留用户规则 |
