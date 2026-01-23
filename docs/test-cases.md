# 测试用例（手动）

以下用例用于验证自动决策系统的关键行为与日志输出。

## 1. 反馈跨天更新

目的：确保 `PostToolUse` 可以回溯更新最近 7 天的日志。

步骤：
1. 手动在 `.claude/memory-bank/feedback/` 中创建或保留一条历史日志（日期为昨天或更早），包含 `id`。
2. 触发一次 `PostToolUse`，传入相同 `tool_use_id`。

期望：
- 对应历史日志的 `executed` 字段被更新为 `true`。
- `~/.claude/auto-decision/hooks.log` 中出现 “已执行” 的记录。

## 2. 反馈记录缺失日志

目的：当找不到对应 `tool_use_id` 时有可观测日志。

步骤：
1. 触发一次 `PostToolUse`，传入一个不存在的 `tool_use_id`。

期望：
- `~/.claude/auto-decision/hooks.log` 中出现 “未找到记录” 的日志。

## 3. 规则冲突检测

目的：检测同一 tool + pattern/path 且 action 不一致时输出冲突日志。

步骤：
1. 在项目或全局规则中添加两条规则，保持 `tool` + `pattern`（或 `path`）相同，但 `action` 不同。
2. 触发一次 `PreToolUse`。

期望：
- `~/.claude/auto-decision/hooks.log` 中记录冲突信息，包含两个规则 ID 与来源。

## 4. 规则优先级验证

目的：确保规则加载优先级正确。

步骤：
1. 在项目 `learned-rules.md` 中写一条允许规则。
2. 在全局 `rules.md` 中写相同匹配条件但拒绝的规则。
3. 触发匹配的 `PreToolUse`。

期望：
- 结果为允许（优先级 1 覆盖优先级 4）。

