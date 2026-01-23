# 定期审查指南

## 📌 为什么需要定期审查？

随着时间推移，全局配置会不断累积，可能导致：
- 配置臃肿、作用域混乱、触发冲突、性能下降

**定期审查**能及时发现和修复这些问题。

---

## 🔄 审查频率和工具

| 类型 | 频率 | 时长 | 工具 | 自动化 |
|------|------|------|------|--------|
| **实时审查** | 每次修改全局时 | 30s-2min | global-change-review-protocol | 100% |
| **快速审查** | 每周五 | 5-10min | weekly-review.sh | 80% |
| **深度审查** | 月末周末 | 30-60min | monthly-review.sh | 50% |
| **季度大扫除** | 季度末 | 2-4h | 手动 + 所有工具 | 30% |

---

## 🛠️ 工具 1: weekly-review.sh

**位置**: `scripts/weekly-review.sh`

**功能**:
- 检查全局 skills 清单（是否有硬编码路径？）
- 检测触发词冲突
- 检查配置文件大小
- 列出最近修改
- 检查 hooks 完整性

**使用**:
```bash
./scripts/weekly-review.sh
```

**输出示例**:
```
▶ 全局 Skills 审查
Skills 清单:
  - experience-learner
  ⚠️  sync - 包含硬编码路径（可能应该是项目级 skill）

▶ 触发词冲突检测
✓ 无触发词冲突
通用触发词检测:
  ⚠️  "同步" (建议添加限定词)

▶ 审查摘要
建议操作:
  1. sync skill 应改为项目级
下次审查: 2026-01-30
```

---

## 📅 每周审查流程（10分钟）

**时间**: 每周五 16:00

1. 运行 `./scripts/weekly-review.sh`
2. 查看输出，记录问题
3. 严重问题立即处理，其他加入月度清单

**自动化（可选）**:
```bash
# crontab
0 16 * * 5 cd ~/projects/claude-code-auto-decision && ./scripts/weekly-review.sh
```

---

## 📅 每月审查流程（60分钟）

**时间**: 月末周六上午

### 检查清单

**全局 Skills**:
- [ ] 所有全局 skills 都应该是全局的吗？
- [ ] 是否有 skills 应该改为项目级？
- [ ] 触发词是否有冲突？

**全局配置**:
- [ ] CLAUDE.md 是否需要更新？
- [ ] 规则文件是否有冗余？
- [ ] config.json 是否有过时配置？

**Memory Bank**:
- [ ] research/ 是否有过期报告（>3个月）？
- [ ] feedback/ 日志是否过大（>100MB）？

**性能**:
- [ ] 运行 test_hooks.py 检查速度

---

## 📅 季度大扫除流程（2-4小时）

### 阶段 1: 数据收集（30分钟）

```bash
./scripts/weekly-review.sh > /tmp/review.log

# 收集使用统计
find ~/.claude/memory-bank/feedback -name "*.jsonl" -mtime -90 | \
    xargs cat | jq '.tool' | sort | uniq -c | sort -nr
```

### 阶段 2: 全局 Skills 深度审查（60分钟）

对每个全局 skill 问：

| 问题 | 如果回答"否" → 行动 |
|------|-------------------|
| 过去 3 个月被使用过吗？ | 归档 |
| 在多个项目中使用吗？ | 改为项目级 |
| 触发词合理吗？ | 修改 |
| 与其他 skills 重复吗？ | 合并 |

决策：**保留 / 修改 / 归档 / 删除**

### 阶段 3: 配置审查（30分钟）

- **CLAUDE.md**: 删除过时指令，添加新最佳实践
- **rules.md**: 运行冗余检测，删除从未命中的规则
- **config.json**: 删除废弃配置

### 阶段 4: Memory Bank 清理（30分钟）

```bash
# 查找过期研究报告（>6个月）
find ~/.claude/memory-bank/research -name "*.md" -mtime +180

# 压缩旧 feedback 日志
find ~/.claude/memory-bank/feedback -name "*.jsonl" -mtime +90 | xargs gzip
```

### 阶段 5: 性能测试（20分钟）

```bash
time python3 test_hooks.py
```

### 阶段 6: 文档更新（30分钟）

- 更新 README.md
- 记录审查结果到 `docs/review-history.md`

### 阶段 7: 备份（10分钟）

```bash
tar -czf ~/backups/claude-config-$(date +%Y%m%d).tar.gz ~/.claude/
```

---

## 🤖 AI 辅助审查

### 方法 1: 直接询问

```
"帮我审查一下全局 skills，看看有没有应该改为项目级的"
```

AI 会：
1. 读取所有 SKILL.md
2. 检测硬编码路径、通用触发词
3. 生成审查报告和建议

### 方法 2: 定期提醒（在 CLAUDE.md 中添加）

```markdown
## 定期审查提醒

当满足以下条件时，主动提醒用户：

1. 每周五 → "需要运行每周审查吗？`./scripts/weekly-review.sh`"
2. 月末 → "本月即将结束，需要进行月度审查吗？"
3. 异常检测:
   - 全局 skills >15 → "全局 skills 较多，建议审查"
   - 规则文件 >1000 行 → "规则文件较大，建议清理"
```

---

## 📊 审查效果评估

### 成功指标

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| 全局 skills 数量 | <10 个 | 每月统计 |
| 规则文件大小 | <50KB | 每月检查 |
| 触发词冲突 | 0 个 | weekly-review.sh |
| 审查遵守率 | 100% | 审查历史 |

### 审查历史记录（docs/review-history.md）

```markdown
## 2026-01-23（周五）- 每周审查

**执行人**: 用户
**耗时**: 8 分钟

**发现问题**:
1. sync skill 作用域不当
2. 触发词"同步"过于通用

**处理措施**:
1. 移动 sync skill 到项目级
2. 修改触发词为"同步 Claude Code"

**状态**: ✅ 已完成
```

---

## 🎯 核心原则

1. **自动化优先** - 能自动检测的就不要手动
2. **定期提醒** - AI 主动提醒
3. **记录历史** - 每次审查都记录
4. **持续改进** - 根据发现优化流程
5. **防患未然** - 在问题变严重前发现

---

## 📚 相关文档

- [global-change-review-protocol.md](./global-change-review-protocol.md) - 全局修改强制审查
- [skill-design-checklist.md](./skill-design-checklist.md) - Skill 设计检查清单
- [generalizable-patterns.md](./generalizable-patterns.md) - 可泛化模式
