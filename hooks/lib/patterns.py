"""
patterns.py - 行为模式检测

从用户的审批行为中检测规律，生成规则建议
"""

import re
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from . import MEMORY_BANK_PROJECT, MEMORY_BANK_GLOBAL, AUTO_DECISION_DIR
from .storage import get_recent_feedback, load_config


def detect_patterns() -> list[dict]:
    """
    检测行为模式，返回规则建议

    检测逻辑：
    1. 对于 auto_decision="ask" 的请求，统计 executed 结果
    2. 如果连续 N 次相同选择，生成规则建议
    """
    config = load_config()
    threshold = config.get("learning", {}).get("threshold", 3)
    confidence_min = config.get("learning", {}).get("confidence_min", 0.8)

    feedback = get_recent_feedback(days=30)

    # 按工具和模式分组统计
    patterns = defaultdict(lambda: {"approved": 0, "rejected": 0, "samples": []})

    for entry in feedback:
        if entry.get("auto_decision") != "ask":
            continue  # 只分析需要用户确认的

        tool = entry.get("tool", "")
        input_data = entry.get("input", {})
        executed = entry.get("executed")

        if executed is None:
            continue  # 尚未确定结果

        # 生成模式 key
        pattern_key = generate_pattern_key(tool, input_data)

        if executed:
            patterns[pattern_key]["approved"] += 1
        else:
            patterns[pattern_key]["rejected"] += 1

        # 保存样本（最多 5 个）
        if len(patterns[pattern_key]["samples"]) < 5:
            patterns[pattern_key]["samples"].append(input_data)

    # 生成规则建议
    suggestions = []

    for pattern_key, stats in patterns.items():
        total = stats["approved"] + stats["rejected"]
        if total < threshold:
            continue

        # 计算置信度
        if stats["approved"] > stats["rejected"]:
            action = "allow"
            confidence = stats["approved"] / total
        else:
            action = "deny"
            confidence = stats["rejected"] / total

        if confidence < confidence_min:
            continue

        # 解析 pattern_key
        tool, pattern_type, pattern_value = parse_pattern_key(pattern_key)

        suggestion = {
            "tool": tool,
            "action": action,
            "confidence": round(confidence, 2),
            "based_on": {
                "approved": stats["approved"],
                "rejected": stats["rejected"],
                "samples": stats["samples"],
            },
        }

        if pattern_type == "command_prefix":
            suggestion["pattern"] = f"^{re.escape(pattern_value)}"
            suggestion["reason"] = f"用户{'总是批准' if action == 'allow' else '总是拒绝'} {pattern_value} 命令"
        elif pattern_type == "file_ext":
            suggestion["path"] = f"**/*{pattern_value}"
            suggestion["reason"] = f"用户对 {pattern_value} 文件{'总是批准' if action == 'allow' else '比较谨慎'}"

        suggestions.append(suggestion)

    return suggestions


def generate_pattern_key(tool: str, input_data: dict) -> str:
    """
    生成模式 key，用于分组统计

    例如：
    - Bash 命令按第一个单词分组：Bash:command_prefix:npm
    - 文件操作按扩展名分组：Write:file_ext:.ts
    """
    if tool == "Bash":
        command = input_data.get("command", "")
        # 提取命令前缀（第一个或前两个单词）
        parts = command.split()
        if len(parts) >= 2 and parts[0] in ("npm", "git", "yarn", "pnpm"):
            prefix = f"{parts[0]} {parts[1]}"
        elif parts:
            prefix = parts[0]
        else:
            prefix = "unknown"
        return f"{tool}:command_prefix:{prefix}"

    elif tool in ("Write", "Edit", "Read"):
        file_path = input_data.get("file_path", "")
        ext = Path(file_path).suffix if file_path else ""
        return f"{tool}:file_ext:{ext or 'no_ext'}"

    else:
        return f"{tool}:general:all"


def parse_pattern_key(key: str) -> tuple[str, str, str]:
    """解析 pattern key"""
    parts = key.split(":", 2)
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return key, "general", "all"


def determine_scope(rule: dict) -> tuple[str, str]:
    """
    智能判断规则应该存全局还是项目

    返回: (scope, reason)
    - scope: "global" 或 "project"
    - reason: 判断理由（用于显示给用户）
    """
    tool = rule.get("tool", "")
    action = rule.get("action", "")
    pattern = rule.get("pattern", "")
    path = rule.get("path", "")

    # 1. 危险命令拒绝规则 → 全局（所有项目都应该拒绝）
    if action == "deny":
        danger_patterns = ["rm -rf", "sudo rm", "chmod 777", "> /dev/", "mkfs", "dd if="]
        for danger in danger_patterns:
            if danger in pattern:
                return "global", f"危险命令 '{danger}' 应全局禁止"

    # 2. 只读工具规则 → 全局（Read/Glob/Grep 通常全局一致）
    if tool in ("Read", "Glob", "Grep", "WebSearch", "WebFetch"):
        return "global", f"{tool} 是只读操作，通常全局一致"

    # 3. 通用辅助工具 → 全局
    if tool in ("TodoWrite", "AskUserQuestion", "Task"):
        return "global", f"{tool} 是通用辅助工具"

    # 4. 包管理器命令 → 项目（不同项目技术栈不同）
    if tool == "Bash" and pattern:
        pkg_managers = ["npm", "yarn", "pnpm", "pip", "cargo", "go ", "bun", "poetry"]
        for pkg in pkg_managers:
            if pkg in pattern:
                return "project", f"包管理器 '{pkg}' 命令与项目技术栈相关"

    # 5. 文件类型规则 → 项目（.ts/.py/.rs 是项目特定的）
    if path:
        return "project", "文件路径规则与项目结构相关"

    # 6. Write/Edit 规则 → 项目（不同项目有不同的文件结构）
    if tool in ("Write", "Edit", "NotebookEdit"):
        return "project", "编辑操作与项目文件结构相关"

    # 7. 默认 → 项目（保守策略，避免污染全局）
    return "project", "默认存储到项目级别"


# 待确认的全局规则队列
PENDING_GLOBAL_RULES_FILE = AUTO_DECISION_DIR / "pending_global_rules.json"


def get_pending_global_rules() -> list[dict]:
    """获取待确认的全局规则"""
    if PENDING_GLOBAL_RULES_FILE.exists():
        try:
            return json.loads(PENDING_GLOBAL_RULES_FILE.read_text())
        except:
            pass
    return []


def add_pending_global_rule(rule: dict, reason: str) -> str:
    """
    添加待确认的全局规则

    返回: pending_id
    """
    pending = get_pending_global_rules()
    pending_id = f"pending-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(pending)}"

    pending.append({
        "id": pending_id,
        "rule": rule,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
    })

    PENDING_GLOBAL_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_GLOBAL_RULES_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))

    return pending_id


def confirm_pending_global_rule(pending_id: str, approved: bool) -> Optional[str]:
    """
    确认或拒绝待确认的全局规则

    返回: 如果批准，返回规则 ID；否则返回 None
    """
    pending = get_pending_global_rules()

    # 找到对应的规则
    rule_entry = None
    remaining = []
    for entry in pending:
        if entry["id"] == pending_id:
            rule_entry = entry
        else:
            remaining.append(entry)

    # 更新待确认列表
    PENDING_GLOBAL_RULES_FILE.write_text(json.dumps(remaining, ensure_ascii=False, indent=2))

    if rule_entry and approved:
        # 保存到全局
        return save_learned_rule(rule_entry["rule"], scope="global")

    return None


def save_learned_rule(rule: dict, scope: str = "project"):
    """
    保存学习到的规则到 learned-rules.md

    scope: "project" 或 "global"
    """
    if scope == "global":
        rules_file = MEMORY_BANK_GLOBAL / "learned-rules.md"
    else:
        rules_file = MEMORY_BANK_PROJECT / "learned-rules.md"

    rules_file.parent.mkdir(parents=True, exist_ok=True)

    # 生成规则 ID
    rule_id = f"learned-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 生成规则文本
    rule_text = f"""
### {rule_id}
- tool: {rule['tool']}
  action: {rule['action']}
"""

    if "pattern" in rule:
        rule_text += f"  pattern: {rule['pattern']}\n"
    if "path" in rule:
        rule_text += f"  path: {rule['path']}\n"

    rule_text += f"""  reason: {rule.get('reason', '从用户行为学习')}
  confidence: {rule.get('confidence', 0.8)}
  learned_at: {datetime.now().strftime('%Y-%m-%d')}
  based_on: 批准 {rule['based_on']['approved']} 次，拒绝 {rule['based_on']['rejected']} 次
"""

    # 追加到文件
    if rules_file.exists():
        content = rules_file.read_text()
        # 检查是否已存在类似规则（简单去重）
        if rule.get("pattern") and rule["pattern"] in content:
            return None
        if rule.get("path") and rule["path"] in content:
            return None
    else:
        content = f"# {'全局' if scope == 'global' else '项目'}学习规则\n\n## 学习到的规则\n"

    content += rule_text
    rules_file.write_text(content, encoding="utf-8")

    return rule_id
