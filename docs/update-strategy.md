# 更新同步策略

## 当前部署状态

- **部署时间**: 2026-01-23
- **部署方式**: 复制模式（不是符号链接）
- **规则总数**: 22 条
- **备份位置**: `~/.claude/memory-bank/rules.md.backup`

## 文件同步机制

### sync.sh 的行为

```
hooks/           → 总是覆盖（核心代码）
skills/          → 总是覆盖（技能定义）
config.json      → 仅创建，不覆盖（保留用户配置）
rules.md         → 仅创建，不覆盖（保留用户规则）
```

### 问题分析

**问题**: `rules.md` 和 `config.json` 在首次安装后不会再更新，导致：
- 新增的规则不会自动生效
- 规则顺序优化不会应用
- 配置项的新增/修改需要手动合并

## 未来更新策略

### 策略 1: 手动合并（推荐用于规则文件）

**适用场景**: 用户已自定义规则

**步骤**:
```bash
# 1. 拉取最新代码
cd ~/projects/claude-code-auto-decision
git pull

# 2. 查看规则差异
diff -u ~/.claude/memory-bank/rules.md rules/global-rules.md

# 3. 备份当前规则
cp ~/.claude/memory-bank/rules.md ~/.claude/memory-bank/rules.md.backup

# 4. 选择合并方式:
# 方式 A: 完全替换（如果没有自定义规则）
cp rules/global-rules.md ~/.claude/memory-bank/rules.md

# 方式 B: 手动合并（如果有自定义规则）
# 编辑 ~/.claude/memory-bank/rules.md，合并新规则

# 5. 同步代码
./sync.sh
```

**优点**: 安全，不会丢失用户自定义内容
**缺点**: 需要手动操作

---

### 策略 2: 分层规则文件（未来改进）

**设计思路**: 将规则分为两个文件
```
~/.claude/memory-bank/
├── rules.md              # 项目提供的基础规则（可覆盖）
└── custom-rules.md       # 用户自定义规则（不覆盖）
```

**加载顺序**:
```
1. 项目 custom-rules.md  (最高优先级)
2. 项目 rules.md
3. 全局 custom-rules.md
4. 全局 rules.md          (最低优先级)
```

**优点**: 用户自定义和项目更新分离
**缺点**: 需要修改代码

---

### 策略 3: 版本检测 + 智能合并（未来改进）

**设计思路**: 在规则文件头部添加版本号

```markdown
# 全局规则
# Version: 1.1.0
# Last-Update: 2026-01-23

## 读取类
...
```

**更新流程**:
1. `sync.sh` 检测版本号差异
2. 如果版本不同，提示用户
3. 提供三种选项:
   - 自动合并（基于规则 ID 去重）
   - 查看差异后手动合并
   - 跳过更新

**优点**: 自动化程度高
**缺点**: 实现复杂

---

## 推荐的最佳实践

### 对于普通用户

1. **定期检查更新**:
   ```bash
   cd ~/projects/claude-code-auto-decision
   git pull
   ./sync.sh --diff  # 查看差异
   ```

2. **规则文件策略**:
   - 不修改 `rules.md` → 每次更新时直接覆盖
   - 需要自定义规则 → 使用项目级 `.claude/memory-bank/rules.md`

3. **更新检查清单**:
   ```
   □ hooks/ 代码有更新？         → ./sync.sh 自动同步
   □ 全局 rules.md 有更新？      → 手动决定是否覆盖
   □ config.json 有新配置项？    → 手动添加到现有配置
   ```

### 对于开发者

1. **提交时添加 CHANGELOG**:
   - 标注是否需要更新 rules.md
   - 标注是否需要更新 config.json
   - 提供迁移脚本（如果需要）

2. **重大规则变更**:
   - 在 `docs/test-cases.md` 中添加测试用例
   - 在 `README.md` 中更新默认规则列表
   - 在提交信息中明确说明影响

---

## 当前更新记录

### 2026-01-23 更新

**变更内容**:
- ✅ 添加 grep/find/awk/sed 到只读命令
- ✅ 重组规则顺序（deny 优先）
- ✅ 修复 .env 文件保护问题
- ✅ 优化规则冲突检测
- ✅ 清理代码冗余

**更新方式**: 手动覆盖 rules.md（用户无自定义规则）

**验证结果**: ✅ 所有测试通过

---

## 未来改进建议

### 短期（1-2 周）
1. ✅ 创建本文档
2. 添加 `update.sh` 脚本，自动检测版本并提示
3. 在 `sync.sh` 中添加 `--force-rules` 选项

### 中期（1-2 月）
1. 实现分层规则文件（custom-rules.md）
2. 添加规则文件版本检测
3. 提供规则合并工具

### 长期（3+ 月）
1. 实现规则 Web UI 管理
2. 支持规则导入/导出
3. 规则版本历史和回滚

---

## 相关文件

- [sync.sh](../sync.sh) - 同步脚本
- [install.sh](../install.sh) - 安装脚本
- [test_hooks.py](../test_hooks.py) - 测试脚本
- [test-cases.md](./test-cases.md) - 测试用例
