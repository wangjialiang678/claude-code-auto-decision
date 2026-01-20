---
name: experience-learner
description: 帮助用户分析决策习惯和学习记录。当用户提到"分析习惯"、"查看学习"、"决策记录"、"反馈日志"时自动使用。
allowed-tools: Read, Glob, Grep
---

# 经验学习分析器

你正在帮助用户分析他们的 Claude Code 使用习惯和自动学习的规则。

## 数据文件位置

| 文件 | 内容 |
|------|------|
| `.claude/memory-bank/feedback/*.jsonl` | 每日反馈日志 |
| `.claude/memory-bank/sessions/*.md` | 会话总结 |
| `.claude/memory-bank/learned-rules.md` | 项目学习规则 |
| `~/.claude/memory-bank/learned-rules.md` | 全局学习规则 |
| `~/.claude/memory-bank/profile.md` | 用户画像 |

## 反馈日志格式

每行是一个 JSON 对象：

```json
{
  "id": "tool_use_id",
  "ts": "2024-01-19T10:00:00",
  "session_id": "abc123",
  "tool": "Bash",
  "input": {"command": "npm test"},
  "auto_decision": "ask",
  "executed": true
}
```

### 字段含义

| 字段 | 说明 |
|------|------|
| auto_decision | 系统决策：`allow`/`deny`/`ask` |
| executed | `true`=用户批准, `false`=用户拒绝, `null`=待确认 |

## 分析任务

### 1. 统计决策分布

```bash
# 统计各类决策数量
grep -o '"auto_decision":"[^"]*"' feedback/*.jsonl | sort | uniq -c
```

### 2. 找出用户总是批准的操作

查找 `auto_decision=ask` 且 `executed=true` 的记录，统计重复模式。

### 3. 找出用户总是拒绝的操作

查找 `auto_decision=ask` 且 `executed=false` 的记录。

### 4. 审核学习规则

检查 `learned-rules.md` 中的规则是否合理：
- confidence 是否足够高（>0.8）
- 样本数是否足够（>3）
- 规则是否过于宽泛

## 建议格式

当发现可优化的地方，用这个格式给出建议：

```markdown
## 发现

[描述发现的模式]

## 建议

- **操作**: [建议的操作]
- **理由**: [为什么这样做]
- **影响**: [这会带来什么变化]
```
