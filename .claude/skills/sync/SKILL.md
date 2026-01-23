# Sync Skill

将项目改动同步到 Claude Code 生产环境 (~/.claude/)。

**⚠️ 作用域说明**: 这是 `claude-code-auto-decision` 项目的专用 skill，仅在该项目中使用。

## 触发条件

**仅在 claude-code-auto-decision 项目中**，当用户说以下内容时自动触发：
- "同步 Claude Code"、"同步 hooks 到生产"
- "部署 Claude hooks"、"更新 Claude 配置"
- "检查 Claude Code 更新"、"检查 auto-decision 更新"
- "sync claude code"、"deploy claude hooks"

**不再使用的通用触发词**（避免在其他项目误触发）：
- ❌ "同步"、"部署"、"更新"（太通用）
- ❌ "sync"、"deploy"、"check updates"（容易误触发）

## 执行前安全检查

触发后会先检查：
1. 当前目录是否包含 `check-updates.sh` 和 `sync.sh`
2. 如果不在正确项目中，提示用户并退出
3. 用户在正确项目中，才继续执行

## 执行步骤

### 方式 1: 自动检查更新（推荐）

```bash
# 检查是否在正确的项目中
if [ ! -f "./check-updates.sh" ] || [ ! -f "./sync.sh" ]; then
    echo "❌ 错误: 当前不在 claude-code-auto-decision 项目中"
    echo "当前目录: $(pwd)"
    echo "预期目录: /Users/michael/projects/claude-code-auto-decision"
    echo ""
    echo "请先切换到正确的项目目录，或使用完整路径："
    echo "  cd /Users/michael/projects/claude-code-auto-decision && ./check-updates.sh"
    exit 1
fi

# 在正确的项目中，执行检查
./check-updates.sh
```

这会自动：
1. 检查 Git 远程更新
2. 检查 hooks/skills/rules/config 差异
3. 运行测试验证
4. 输出彩色状态报告和具体建议

### 方式 2: 直接同步

如果用户明确要求立即同步：

```bash
# 同样先检查项目路径
if [ ! -f "./sync.sh" ]; then
    echo "❌ 错误: 当前不在 claude-code-auto-decision 项目中"
    exit 1
fi

# 执行同步
./sync.sh --diff  # 先显示差异
# 用户确认后
./sync.sh         # 执行同步
```

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

**在项目目录内**:
```bash
./check-updates.sh              # 完整更新检查（推荐）
./check-updates.sh --auto-sync  # 自动同步代码（不包括规则）
./sync.sh --diff                # 查看差异
./sync.sh --dry-run             # 预览同步（不实际执行）
./sync.sh                       # 执行同步
```

**从其他目录**:
```bash
cd /Users/michael/projects/claude-code-auto-decision && ./check-updates.sh
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
