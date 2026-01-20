# 开发历史记录

## 2026-01-19 - 初始开发

### 背景
用户希望构建一个 Claude Code 的自动决策系统，能够：
- 根据规则自动批准/拒绝工具调用
- 从用户行为中学习生成新规则
- 区分全局规则和项目级规则

### 开发过程
1. 设计了基于 Hooks 的系统架构
2. 实现了 PreToolUse、PostToolUse、UserPromptSubmit、Stop 四个 hook
3. 创建了 Markdown 格式的规则系统
4. 实现了行为学习机制（每 10 次工具调用检测一次模式）
5. 添加了智能 scope 判断（全局 vs 项目）

---

## 2026-01-20 - 调试与项目整理

### 会话摘要

| # | 用户问题 | 回答要点 |
|---|---------|---------|
| 1 | 检查系统是否正常运行，是否有命令自动允许了 | 查看了 hooks.log，确认 hooks 正在执行，部分命令已自动允许 |
| 2 | rm 操作有自动允许吗？ | 检查了规则，rm 只有危险模式（`rm -rf /` 或 `rm -rf ~`）会被拒绝，普通 rm 返回 ask |
| 3 | grep 操作也提示了，为什么？ | Bash 的 grep 命令不在只读命令允许列表中（只有 ls/pwd/cat/head/tail 等），所以返回 ask |
| 4 | 是不是 grep 里带了 rm 触发了 ask？ | 不是，grep 命令本身就没有匹配到 allow 规则，所以默认返回 ask |
| 5 | 手动批准两次后，应该会自动学习吧？ | 学习阈值设置为 3 次，只批准 2 次还不够。需要达到阈值才会生成规则 |
| 6 | detect_patterns 到底有没有触发点？你之前说错了？ | **纠正**：之前说错了。`detect_patterns()` 在 `experience_saver.py` 中有触发，每 10 次工具调用检测一次 |
| 7 | 这些原理在 README 里有吗？ | 有，`auto-decision-system.md` 文档很完整，包含架构、流程、配置等 |
| 8 | 创建项目目录，复制文件，推送到 GitHub | 创建了 `/Users/michael/projects/claude-code-auto-decision`，复制了所有相关文件，创建了 install.sh，推送到了 GitHub |
| 9 | 如何自动同步更新到 Claude Code 配置？ | install.sh 使用符号链接模式，但只链接了 hooks 目录。需要更完善的更新机制 |
| 10 | 把 gh 加入 PATH，创建开发历史，创建手动更新脚本 | 正在处理中... |

### 关键发现

1. **学习机制触发点**：`experience_saver.py`（PostToolUse hook），每 10 次调用触发一次
2. **学习阈值**：`config.json` 中 `learning.threshold = 3`
3. **计数器位置**：`~/.claude/hooks/.experience_counter`
4. **规则优先级**：项目学习 > 项目手动 > 全局学习 > 全局手动

### 待改进

1. `grep` 命令可以考虑加入只读命令允许列表

---

| # | 用户问题 | 回答要点 |
|---|---------|---------|
| 11 | 澄清更新需求：是项目→生产环境同步，不是 GitHub 更新 | 创建 sync.sh 脚本，用于将项目改动同步到 ~/.claude/；创建 sync skill 让 Claude 能响应「同步」指令 |

---

## 项目仓库

- GitHub: https://github.com/wangjialiang678/claude-code-auto-decision
