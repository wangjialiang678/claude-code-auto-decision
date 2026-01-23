# Skill 设计检查清单

本文档提供创建和修改 Skills 时的强制性检查清单，防止作用域污染、触发冲突等常见问题。

## 📋 创建新 Skill 前必答问题

### 1. 作用域评估（⭐⭐⭐⭐⭐ 最重要）

**问题**：这个 skill 应该是全局的还是项目特定的？

#### 判断标准

| 特征 | 全局 Skill | 项目 Skill |
|------|-----------|-----------|
| **使用范围** | 所有项目都需要 | 仅特定项目需要 |
| **依赖** | 不依赖特定文件/目录 | 依赖项目特定文件 |
| **路径** | 无硬编码项目路径 | 包含硬编码路径 |
| **通用性** | 通用工具（如代码审查） | 项目工具（如同步脚本） |
| **部署位置** | `~/.claude/skills/` | `.claude/skills/` |

#### 示例

✅ **全局 Skill**:
- `rule-editor` - 管理自动决策规则（所有项目都需要）
- `workflow-guide` - 工作流指南（通用）
- `github-search` - 搜索 GitHub 项目（通用）

✅ **项目 Skill**:
- `sync` (claude-code-auto-decision) - 同步项目到生产环境
- `deploy-prod` (web-app) - 部署到生产服务器
- `run-tests` (specific-project) - 运行项目测试套件

#### 决策流程

```
┌─ 创建新 Skill
│
├─❓ 其他项目需要这个功能吗？
│  │
│  ├─ 是 → 继续检查 ↓
│  └─ 否 → 项目 Skill (.claude/skills/)
│
├─❓ 是否依赖特定项目的文件/目录？
│  │
│  ├─ 是 → 项目 Skill (.claude/skills/)
│  └─ 否 → 继续检查 ↓
│
├─❓ 是否包含硬编码项目路径？
│  │
│  ├─ 是 → 项目 Skill (.claude/skills/)
│  └─ 否 → 全局 Skill (~/.claude/skills/)
│
└─ ✅ 作用域已确定
```

### 2. 触发词冲突检测（⭐⭐⭐⭐⭐ 非常重要）

**问题**：触发关键词是否会在其他上下文中误触发？

#### 风险评级

| 关键词类型 | 风险等级 | 示例 | 建议 |
|-----------|---------|------|------|
| **单字通用词** | 🔴 极高 | "同步"、"更新"、"部署" | ❌ 禁止使用 |
| **两字通用词** | 🟠 高 | "检查"、"运行"、"修复" | ⚠️ 谨慎使用 |
| **通用短语** | 🟡 中 | "检查更新"、"运行测试" | ⚠️ 需要限定词 |
| **项目特定短语** | 🟢 低 | "同步 Claude hooks"、"部署 auto-decision" | ✅ 推荐 |
| **唯一标识符** | 🟢 极低 | "sync-claude-code-hooks" | ✅ 最安全 |

#### 检查方法

**步骤 1: 列出所有触发词**

示例（sync skill）:
```
- "同步"
- "检查更新"
- "sync"
- "deploy"
```

**步骤 2: 跨场景模拟测试**

| 场景 | 用户可能说的话 | 会触发吗？ | 应该触发吗？ | 结论 |
|------|--------------|----------|------------|------|
| 场景 A: 目标项目 | "同步 Claude hooks" | ✅ | ✅ | ✅ 正确 |
| 场景 B: Web 项目 | "同步数据库" | ✅ | ❌ | ❌ 误触发！ |
| 场景 C: 无项目 | "检查更新" | ✅ | ❌ | ❌ 误触发！ |

**步骤 3: 重新设计触发词**

如果发现误触发，添加限定词：

```diff
- "同步"
+ "同步 Claude Code"

- "检查更新"
+ "检查 Claude Code 更新"

- "sync"
+ "sync claude code"
```

### 3. 路径硬编码检查（⭐⭐⭐⭐）

**问题**：Skill 是否包含硬编码的绝对路径？

#### 检查方法

```bash
# 检查是否有硬编码路径
grep -E "cd /Users/|/home/|C:\\\\Users" skills/*/SKILL.md
```

#### 处理方案

**如果是项目特定 Skill**：
```markdown
## 执行前检查

```bash
# 检查是否在正确的项目中
if [ ! -f "./check-updates.sh" ]; then
    echo "❌ 错误: 当前不在 claude-code-auto-decision 项目中"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 使用相对路径
./check-updates.sh
```
```

**如果是全局 Skill**：
```markdown
# ❌ 不要硬编码路径
cd /Users/michael/projects/my-project

# ✅ 使用相对路径或环境变量
cd $PROJECT_ROOT
```

### 4. 执行前安全检查（⭐⭐⭐）

**问题**：如何防止在错误上下文中执行？

#### 实施方案

对于**项目特定 Skill**，必须添加：

```markdown
## 执行前安全检查

触发后会先检查：
1. 当前目录是否包含项目特有的标志文件
2. 如果不在正确项目中，提示用户并退出
3. 仅在正确项目中继续执行

```bash
# 检查标志文件（选择项目特有的文件）
MARKERS=("package.json" "pyproject.toml" "check-updates.sh")
FOUND=false

for marker in "${MARKERS[@]}"; do
    if [ -f "./$marker" ]; then
        FOUND=true
        break
    fi
done

if [ "$FOUND" = false ]; then
    echo "❌ 错误: 当前不在预期的项目目录中"
    echo "当前目录: $(pwd)"
    exit 1
fi
```
```

---

## 📝 Skill 创建检查清单

创建新 Skill 时，请逐项检查：

### 设计阶段

- [ ] **作用域决策**: 确定是全局还是项目级
  - [ ] 完成决策流程图
  - [ ] 记录决策理由
- [ ] **触发词设计**: 列出所有触发关键词
  - [ ] 评估每个词的风险等级
  - [ ] 完成跨场景模拟测试
  - [ ] 如有高风险词，重新设计
- [ ] **路径检查**: 检查是否有硬编码路径
  - [ ] 如有，评估是否必要
  - [ ] 添加路径检测逻辑

### 实现阶段

- [ ] **安全检查**: 添加执行前验证
  - [ ] 项目 Skill 必须检查标志文件
  - [ ] 全局 Skill 检查依赖是否可用
- [ ] **错误处理**: 添加清晰的错误提示
  - [ ] 当前目录
  - [ ] 预期目录
  - [ ] 如何切换到正确目录
- [ ] **文档说明**: 在 SKILL.md 中添加
  - [ ] ⚠️ 作用域说明（全局/项目）
  - [ ] 触发条件（明确列出）
  - [ ] 执行前检查（如果需要）

### 部署阶段

- [ ] **部署位置**:
  - [ ] 项目 Skill → `.claude/skills/`
  - [ ] 全局 Skill → `~/.claude/skills/`
- [ ] **同步脚本**: 如果是项目 Skill
  - [ ] 不要添加到全局同步列表
  - [ ] 在 README 中说明如何启用

### 测试阶段

- [ ] **功能测试**:
  - [ ] 在目标项目中触发 ✅
  - [ ] 在其他项目中触发（应该失败或被阻止）✅
  - [ ] 在无项目上下文中触发（检查行为）✅
- [ ] **触发词测试**:
  - [ ] 使用每个触发词测试
  - [ ] 使用相似但不应触发的词测试
  - [ ] 在不同上下文中测试

---

## 🚨 常见错误案例

### 案例 1: sync skill（本项目）

**问题**:
- ❌ 部署到全局 `~/.claude/skills/sync/`
- ❌ 使用通用触发词 "同步"、"检查更新"
- ❌ 包含硬编码路径 `/Users/michael/projects/claude-code-auto-decision`

**影响**:
- 在任何项目说"同步"都会尝试执行
- 在其他项目说"检查更新"会执行错误的脚本

**修复**:
- ✅ 改为项目级 `.claude/skills/sync/`
- ✅ 使用特定触发词 "同步 Claude Code"
- ✅ 添加路径检测，不在正确项目中直接退出

### 案例 2: 假设的错误（通用部署脚本）

**错误设计**:
```markdown
# Deploy Skill

触发条件：
- "部署"、"deploy"

执行：
cd /Users/michael/projects/current-project && ./deploy.sh
```

**问题**:
- 硬编码路径
- 通用触发词
- 没有项目检测

**正确设计**:
```markdown
# Deploy Skill (项目特定)

⚠️ 作用域: 仅在 current-project 中使用

触发条件：
- "部署 current-project"、"deploy current-project"

执行前检查：
if [ ! -f "./deploy.sh" ]; then
    echo "错误：不在 current-project 目录"
    exit 1
fi

执行：
./deploy.sh
```

---

## 🔄 修改现有 Skill 的检查

当修改已有 Skill 时：

### 触发词修改

- [ ] 新增触发词前，完成冲突检测
- [ ] 删除触发词前，确认没有用户依赖
- [ ] 修改触发词后，更新文档

### 功能修改

- [ ] 如果添加路径依赖 → 添加路径检测
- [ ] 如果改变作用域 → 重新部署
- [ ] 如果修改执行逻辑 → 重新测试

### 作用域迁移

**从全局迁移到项目级**:
```bash
# 1. 复制到项目级
mkdir -p .claude/skills
cp -r ~/.claude/skills/skill-name .claude/skills/

# 2. 从全局删除
rm -rf ~/.claude/skills/skill-name

# 3. 更新触发词（添加项目限定词）
# 4. 添加路径检测
# 5. 测试验证
```

**从项目级迁移到全局**:
```bash
# 1. 移除所有硬编码路径
# 2. 改为通用触发词（但要避免冲突！）
# 3. 复制到全局
cp -r .claude/skills/skill-name ~/.claude/skills/

# 4. 从项目删除
rm -rf .claude/skills/skill-name

# 5. 跨项目测试
```

---

## 📚 相关文档

- [generalizable-patterns.md](./generalizable-patterns.md) - 可泛化模式
- [update-strategy.md](./update-strategy.md) - 更新策略
- [README.md](../README.md) - 项目概述
