#!/usr/bin/env python3
"""
auto_decision.py - PreToolUse Hook
自动决策：根据规则决定是否批准工具调用
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.logger import log
from lib.rules import load_rules, match_rules
from lib.storage import log_request, load_config
from lib.llm import is_llm_enabled, llm_decide


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        log("PreToolUse", "JSON解析失败")
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_use_id = data.get("tool_use_id", "")
    session_id = data.get("session_id", "")

    # 加载规则并匹配
    rules = load_rules()
    decision, reason = match_rules(tool_name, tool_input, rules)

    # 如果规则没命中且启用了 LLM，尝试 LLM 决策
    if decision == "ask" and is_llm_enabled():
        decision, reason = llm_decide(tool_name, tool_input)

    # 简洁日志
    log("PreToolUse", f"{tool_name} → {decision}")

    # 记录请求到 feedback
    try:
        log_request(
            request_id=tool_use_id,
            tool_name=tool_name,
            tool_input=tool_input,
            auto_decision=decision,
            session_id=session_id,
        )
    except Exception as e:
        log("PreToolUse", f"记录失败: {e}")

    # 输出决策
    if decision in ("allow", "deny"):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason or f"Auto {decision}",
            }
        }
        print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("PreToolUse", f"错误: {e}")
