---
name: rule-editor
description: 帮助用户编辑自动决策规则。当用户提到"规则"、"自动允许"、"自动拒绝"、"添加规则"、"修改决策"、"待确认规则"、"全局规则"、"同意全局"、"仅本项目"、"忽略"时自动使用。
allowed-tools: Read, Write, Edit, Glob, Bash
---

# 规则编辑器

你正在帮助用户编辑 Claude Code 的自动决策规则。

## 处理用户对全局规则的回复

当用户回复关于全局规则的决定时，根据回复内容执行相应操作：

### 用户说「同意全局」或类似表达（如"全局"、"保存全局"、"yes"、"好"）

1. 先读取待确认规则文件找到最新的规则
2. 调用确认函数保存到全局

```python
# 在 Python 中执行
import sys, json
sys.path.insert(0, '/Users/michael/.claude/hooks')
from lib.patterns import confirm_pending_global_rule, get_pending_global_rules

pending = get_pending_global_rules()
if pending:
    latest = pending[-1]  # 最新的一条
    result = confirm_pending_global_rule(latest['id'], True)
    print(f"✅ 已保存为全局规则: {result}")
```

### 用户说「仅本项目」或类似表达（如"项目"、"本项目"、"不要全局"）

1. 读取待确认规则
2. 拒绝全局，但手动保存到项目级

```python
import sys, json
sys.path.insert(0, '/Users/michael/.claude/hooks')
from lib.patterns import confirm_pending_global_rule, get_pending_global_rules, save_learned_rule

pending = get_pending_global_rules()
if pending:
    latest = pending[-1]
    confirm_pending_global_rule(latest['id'], False)  # 从队列移除
    rule_id = save_learned_rule(latest['rule'], scope="project")  # 保存到项目
    print(f"✅ 已保存为项目规则: {rule_id}")
```

### 用户说「忽略」或类似表达（如"不要"、"跳过"、"算了"）

1. 直接从队列移除，不保存

```python
import sys
sys.path.insert(0, '/Users/michael/.claude/hooks')
from lib.patterns import confirm_pending_global_rule, get_pending_global_rules

pending = get_pending_global_rules()
if pending:
    latest = pending[-1]
    confirm_pending_global_rule(latest['id'], False)
    print("✅ 已忽略该规则")
```

### 查看所有待确认规则

```python
import sys, json
sys.path.insert(0, '/Users/michael/.claude/hooks')
from lib.patterns import get_pending_global_rules

pending = get_pending_global_rules()
for p in pending:
    print(f"- {p['id']}: {p['rule'].get('tool')} → {p['rule'].get('action')}")
    print(f"  理由: {p['reason']}")
```

## 规则文件位置

| 文件 | 作用 | 优先级 |
|------|------|--------|
| `.claude/memory-bank/learned-rules.md` | 项目学习规则 | 最高 |
| `.claude/memory-bank/rules.md` | 项目基础规则 | 高 |
| `~/.claude/memory-bank/learned-rules.md` | 全局学习规则 | 中 |
| `~/.claude/memory-bank/rules.md` | 全局基础规则 | 最低 |

## 规则格式

每条规则写成这样：

```markdown
### rule-name
- tool: Bash
  action: allow
  pattern: ^npm test
  reason: 说明文字
```

### 字段说明

| 字段 | 必需 | 说明 |
|------|------|------|
| tool | 是 | 工具名，支持正则如 `Write\|Edit` |
| action | 是 | `allow`（自动批准）、`deny`（自动拒绝）、`ask`（弹框确认） |
| pattern | 否 | 匹配命令内容的正则表达式 |
| path | 否 | 匹配文件路径的 glob 模式 |
| reason | 是 | 规则说明（会显示给用户） |

### 常用工具名

- `Read` - 读取文件
- `Write` - 创建文件
- `Edit` - 编辑文件
- `Bash` - 执行命令
- `Glob` - 搜索文件名
- `Grep` - 搜索内容
- `WebSearch` - 网络搜索
- `WebFetch` - 获取网页

## 操作指南

1. 先用 Read 读取现有规则文件
2. 根据用户需求添加/修改规则
3. 确保格式正确（YAML-like 语法）
4. 告知用户变更内容

## 示例规则

### 允许所有测试命令
```markdown
### allow-test-commands
- tool: Bash
  action: allow
  pattern: ^(npm test|pytest|go test|cargo test)
  reason: 测试命令是安全的
```

### 保护配置文件
```markdown
### protect-config
- tool: Write|Edit
  action: ask
  path: **/*.config.js
  reason: 配置文件修改需要确认
```

### 拒绝危险删除
```markdown
### deny-dangerous-rm
- tool: Bash
  action: deny
  pattern: rm\s+-rf\s+[/~]
  reason: 危险：可能删除重要目录
```
