# 全局修改强制审查协议

## 📌 问题背景

当 AI 修改全局配置（如 `~/.claude/CLAUDE.md`、`~/.claude/skills/`、`~/.claude/memory-bank/rules.md`）时，容易忽略跨项目影响，导致：
- 作用域污染（全局 skill 误触发）
- 配置冲突（不同项目需求不同）
- 意外副作用（影响其他正在进行的项目）

**核心解决思路**：在任何全局修改前，**强制**触发作用域审查流程。

---

## 🚨 强制审查触发条件

### 触发条件清单

当 AI 计划执行以下任一操作时，**必须先**进入审查流程：

#### 1. 全局配置文件修改

| 文件路径 | 风险等级 | 说明 |
|---------|---------|------|
| `~/.claude/CLAUDE.md` | 🔴 极高 | 影响所有项目和会话 |
| `~/.claude/memory-bank/rules.md` | 🔴 极高 | 影响所有自动决策 |
| `~/.claude/config.json` | 🟠 高 | 全局配置 |
| `~/.claude/hooks/**` | 🟠 高 | 核心执行逻辑 |

#### 2. 全局 Skills 操作

| 操作 | 风险等级 | 示例 |
|------|---------|------|
| 创建全局 skill | 🔴 极高 | `mkdir ~/.claude/skills/new-skill` |
| 修改全局 skill | 🟠 高 | `edit ~/.claude/skills/sync/SKILL.md` |
| 删除全局 skill | 🟡 中 | `rm -rf ~/.claude/skills/old-skill` |
| 修改 skill 触发词 | 🔴 极高 | 可能影响所有项目 |

#### 3. 其他全局资源

| 资源 | 风险等级 | 说明 |
|------|---------|------|
| `~/.claude/scripts/**` | 🟡 中 | 全局脚本 |
| `~/.claude/templates/**` | 🟢 低 | 模板文件 |
| 全局环境变量 | 🟠 高 | `.bashrc`、`.zshrc` 等 |

---

## 🔍 审查流程（强制执行）

### 步骤 1: 自动检测触发

AI 在执行前，必须通过以下检查：

```python
# 伪代码：AI 内部检查
def before_tool_call(tool_name, tool_input):
    if is_global_modification(tool_input):
        # 检测到全局修改，进入强制审查
        trigger_global_change_review()
        # 暂停执行，等待审查完成
        wait_for_review_approval()

    # 审查通过后，继续执行
    execute_tool(tool_name, tool_input)

def is_global_modification(tool_input):
    """检测是否为全局修改"""
    global_paths = [
        "~/.claude/CLAUDE.md",
        "~/.claude/skills/",
        "~/.claude/memory-bank/rules.md",
        "~/.claude/hooks/",
        "~/.claude/config.json"
    ]

    if tool_name in ["Write", "Edit"]:
        path = tool_input.get("file_path", "")
        for global_path in global_paths:
            if global_path in path:
                return True

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for global_path in global_paths:
            if global_path in command:
                return True

    return False
```

### 步骤 2: 强制审查问题（AI 必须回答）

当检测到全局修改时，AI **必须**在执行前回答以下问题：

#### 问题 1: 作用域评估 ⭐⭐⭐⭐⭐

```
Q: 这个修改应该是全局的还是项目特定的？

必答要点：
1. 这个修改是否影响所有项目？
   - [ ] 是 → 继续审查
   - [ ] 否 → 改为项目级修改

2. 其他项目是否需要这个修改？
   - [ ] 是 → 继续审查
   - [ ] 否 → 改为项目级修改
   - [ ] 不确定 → 询问用户

3. 这个修改是否依赖当前项目的特定文件/逻辑？
   - [ ] 是 → 应该是项目级
   - [ ] 否 → 可以考虑全局
```

#### 问题 2: 跨项目影响分析 ⭐⭐⭐⭐⭐

```
Q: 在其他项目中，这个修改会产生什么影响？

必须模拟的场景：
1. 场景 A: 当前项目（claude-code-auto-decision）
   影响：[详细描述]

2. 场景 B: 其他正在进行的项目（web-app）
   影响：[详细描述]
   是否安全？ [ ] 是 [ ] 否 [ ] 不确定

3. 场景 C: 未来新项目
   影响：[详细描述]
   是否安全？ [ ] 是 [ ] 否 [ ] 不确定

如果任一场景不安全或不确定 → 询问用户或改为项目级
```

#### 问题 3: 回滚计划 ⭐⭐⭐⭐

```
Q: 如果这个修改导致问题，如何回滚？

必须提供：
1. 备份策略
   - [ ] 自动备份原文件（推荐）
   - [ ] 提示用户手动备份
   - [ ] 使用版本控制（Git）

2. 回滚命令
   示例：
   ```bash
   # 回滚到修改前
   cp ~/.claude/CLAUDE.md.backup ~/.claude/CLAUDE.md
   ```

3. 影响范围
   - 影响的项目：[列出]
   - 需要重启的服务：[列出]
```

#### 问题 4: 用户确认 ⭐⭐⭐

```
Q: 是否需要询问用户？

必须询问用户的情况：
- [ ] 跨项目影响不明确
- [ ] 可能破坏现有工作流
- [ ] 涉及敏感配置（规则、认证等）
- [ ] 不确定是否应该全局化

可以自动执行的情况（必须同时满足）：
- [ ] 影响明确且安全
- [ ] 有完整的回滚计划
- [ ] 用户之前明确授权过类似操作
```

### 步骤 3: 审查输出格式

AI 必须输出以下格式的审查报告：

```markdown
## 🔍 全局修改审查报告

### 修改描述
- **目标文件**: ~/.claude/skills/sync/SKILL.md
- **操作类型**: 创建全局 skill
- **修改原因**: 响应用户"同步到生产"请求

### 作用域评估
- **是否应该全局**: ❌ 否
- **原因**:
  - 包含硬编码项目路径 /Users/michael/projects/claude-code-auto-decision
  - 仅 claude-code-auto-decision 项目需要
  - 触发词"同步"过于通用，会在其他项目误触发

### 跨项目影响分析
| 项目 | 影响 | 安全性 |
|------|------|-------|
| claude-code-auto-decision | 可以使用同步功能 | ✅ 安全 |
| web-app | 说"同步"会误触发，尝试执行不存在的脚本 | ❌ 不安全 |
| 未来项目 | 同样会误触发 | ❌ 不安全 |

### 决策
- **最终决定**: 改为项目级 skill
- **部署位置**: .claude/skills/sync/
- **触发词调整**: "同步 Claude Code"（添加限定词）

### 回滚计划
- **备份**: 不需要（未修改全局文件）
- **回滚**: rm -rf .claude/skills/sync

### 用户确认
- **是否需要**: ❌ 否
- **原因**: 决策明确，改为项目级更安全
```

### 步骤 4: 执行或询问用户

根据审查结果：

**情况 A: 明确应该项目级**
```
→ 自动改为项目级修改
→ 输出审查报告
→ 继续执行
```

**情况 B: 明确应该全局，且安全**
```
→ 自动备份原文件
→ 输出审查报告
→ 执行修改
```

**情况 C: 不确定或有风险**
```
→ 输出审查报告
→ 使用 AskUserQuestion 询问用户
→ 等待用户确认后执行
```

---

## 🛠️ 实施方案

### 方案 1: 在 CLAUDE.md 中添加强制规则

在 `~/.claude/CLAUDE.md` 或项目 `CLAUDE.md` 中添加：

```markdown
## 🚨 全局修改强制审查规则

**触发条件**: 当你计划修改以下任一位置时

- `~/.claude/CLAUDE.md`
- `~/.claude/skills/**`
- `~/.claude/memory-bank/rules.md`
- `~/.claude/hooks/**`
- `~/.claude/config.json`

**强制流程**:

1. **暂停执行**，不要立即修改
2. **输出审查报告**，包含：
   - 作用域评估（全局 vs 项目）
   - 跨项目影响分析（至少 3 个场景）
   - 回滚计划
   - 是否需要用户确认
3. **决策**：
   - 如果应该项目级 → 改为项目级修改
   - 如果不确定 → 使用 AskUserQuestion 询问
   - 如果确定全局 → 备份后执行
4. **执行前**，向用户展示审查报告

**违规惩罚**: 如果你跳过审查直接修改全局文件，用户会回滚你的修改并要求你重新审查。

**检查方法**:
```bash
# 你可以在内部使用这个检查
is_global_path() {
    local path=$1
    case "$path" in
        */.claude/CLAUDE.md|*/.claude/skills/*|*/.claude/memory-bank/rules.md|*/.claude/hooks/*|*/.claude/config.json)
            return 0  # 是全局路径
            ;;
        *)
            return 1  # 不是全局路径
            ;;
    esac
}
```

**示例流程**:

```
用户: "添加一个自动格式化代码的 skill"

AI (内部检查):
→ 计划创建 ~/.claude/skills/code-formatter/SKILL.md
→ 检测到全局路径！
→ 触发强制审查流程

AI (输出):
"检测到全局修改请求，开始强制审查..."

[输出完整的审查报告]

"审查结论: 代码格式化是通用需求，应该是全局 skill。
 但需要确认：不同项目可能使用不同的格式化工具（prettier/black/gofmt）。

 建议: 创建通用框架，项目级配置具体格式化工具。

 是否继续创建全局 skill？"

[等待用户确认]
```
```

### 方案 2: 创建自动化检查脚本

创建 `scripts/check-global-impact.sh`:

```bash
#!/bin/bash
# check-global-impact.sh - 检查全局修改的影响

TARGET_PATH=$1

echo "=== 全局修改影响检查 ==="
echo "目标: $TARGET_PATH"
echo ""

# 检查是否为全局路径
if [[ $TARGET_PATH == *"/.claude/CLAUDE.md"* ]] || \
   [[ $TARGET_PATH == *"/.claude/skills/"* ]] || \
   [[ $TARGET_PATH == *"/.claude/memory-bank/rules.md"* ]]; then
    echo "⚠️  警告: 这是全局配置！"
    echo ""
    echo "影响范围:"
    echo "  - 所有当前项目"
    echo "  - 所有未来会话"
    echo "  - 所有 Claude Code 实例"
    echo ""
    echo "必须回答:"
    echo "  1. 这个修改是否应该全局化？"
    echo "  2. 在其他项目中会产生什么影响？"
    echo "  3. 如何回滚？"
    echo ""
    read -p "继续？ (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "已取消"
        exit 1
    fi
fi
```

### 方案 3: 在 generalizable-patterns.md 中添加模式

添加新的可泛化模式：

```markdown
### 模式 14: 全局修改强制审查 ⭐⭐⭐⭐⭐

**触发条件**: 计划修改 ~/.claude/ 下的任何文件

**执行流程**:
1. 暂停执行
2. 输出审查报告（作用域、影响、回滚）
3. 决策（全局/项目/询问用户）
4. 执行或询问

**检查清单**:
- [ ] 检测到全局路径
- [ ] 输出审查报告
- [ ] 评估作用域
- [ ] 分析跨项目影响
- [ ] 制定回滚计划
- [ ] 决定是否询问用户
```

---

## 📝 审查清单（AI 自检）

在执行全局修改前，AI 必须自检：

### 检测阶段
- [ ] 识别出这是全局修改
- [ ] 暂停执行，未立即修改文件

### 审查阶段
- [ ] 完成作用域评估
- [ ] 完成跨项目影响分析（≥3 个场景）
- [ ] 制定回滚计划
- [ ] 决定是否询问用户

### 输出阶段
- [ ] 输出完整审查报告
- [ ] 清晰说明决策理由
- [ ] 如需用户确认，使用 AskUserQuestion

### 执行阶段
- [ ] 备份原文件（如果修改全局）
- [ ] 执行修改
- [ ] 记录修改到日志

---

## 🔗 集成到工作流

### 在 RIPER-5 工作流中的位置

```
用户请求
  ↓
[MODE: RESEARCH]
  ↓
需求澄清
  ↓
执行调研
  ↓
[MODE: PLAN]
  ↓
创建计划
  ↓
📋 检查: 是否涉及全局修改？
  ├─ 是 → 🚨 触发全局修改审查流程
  │         ├─ 输出审查报告
  │         ├─ 决策（全局/项目/询问）
  │         └─ 用户确认后继续
  └─ 否 → 继续
  ↓
[MODE: EXECUTE]
  ↓
执行实现
```

### 与现有系统的关系

| 现有系统 | 关系 | 说明 |
|---------|------|------|
| Auto-Decision Rules | 互补 | 全局审查在执行前，规则系统在执行时 |
| Skill System | 约束 | 限制全局 skill 的随意创建 |
| RIPER-5 Workflow | 嵌入 | 在 PLAN 阶段强制执行 |
| Memory Bank | 协同 | 审查报告保存到 memory-bank/reviews/ |

---

## 📊 效果评估

### 成功指标

| 指标 | 目标 | 当前 | 说明 |
|------|------|------|------|
| 全局修改漏审率 | 0% | - | 所有全局修改都触发审查 |
| 误判率 | <5% | - | 不应该全局的被判定为全局 |
| 用户满意度 | >90% | - | 用户认为审查有价值 |
| 审查时间 | <30s | - | 审查流程不应太慢 |

### 失败案例记录

当审查机制失效时，记录到 `docs/review-failures.md`:

```markdown
## 失败案例 #1

- **日期**: 2026-01-23
- **修改**: 创建全局 sync skill
- **问题**: 未触发审查，直接创建到 ~/.claude/skills/
- **影响**: 在其他项目中误触发
- **原因**: AI 未检测到全局路径
- **改进**: 在 CLAUDE.md 中添加显式检查规则
```

---

## 🎯 总结

### 核心原则

1. **全局修改 = 强制审查**（无例外）
2. **默认项目级**（除非有充分理由全局化）
3. **跨场景测试**（至少 3 个场景）
4. **询问用户**（不确定时）
5. **备份优先**（修改前备份）

### 实施优先级

1. **P0（立即）**: 在 CLAUDE.md 中添加强制审查规则
2. **P1（本周）**: 在 generalizable-patterns.md 中添加模式
3. **P2（下周）**: 创建自动化检查脚本
4. **P3（未来）**: 集成到 RIPER-5 工作流的自动检查

---

## 📚 相关文档

- [skill-design-checklist.md](./skill-design-checklist.md) - Skill 设计检查清单
- [generalizable-patterns.md](./generalizable-patterns.md) - 可泛化模式
- [update-strategy.md](./update-strategy.md) - 更新策略
