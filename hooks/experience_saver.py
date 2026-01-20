#!/usr/bin/env python3
"""
experience_saver.py - PostToolUse Hook
经验沉淀：检测行为模式，自动生成规则
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.logger import log
from lib.storage import load_config
from lib.patterns import detect_patterns, save_learned_rule, determine_scope, add_pending_global_rule
from lib.llm import is_llm_enabled, llm_generate_rule_suggestion

DETECT_INTERVAL = 10
call_counter_file = Path(__file__).parent / ".experience_counter"


def get_call_count() -> int:
    if call_counter_file.exists():
        return int(call_counter_file.read_text().strip() or "0")
    return 0


def set_call_count(count: int):
    call_counter_file.write_text(str(count))


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    config = load_config()
    if not config.get("learning", {}).get("enabled", True):
        sys.exit(0)

    count = get_call_count() + 1
    set_call_count(count)

    if count % DETECT_INTERVAL != 0:
        sys.exit(0)

    log("ExpSaver", f"检测模式 (第{count}次)")

    suggestions = detect_patterns()
    if not suggestions:
        log("ExpSaver", "无新规则建议")
        sys.exit(0)

    for suggestion in suggestions:
        if is_llm_enabled():
            enhanced = llm_generate_rule_suggestion(suggestion)
            if enhanced:
                suggestion = {**suggestion, **enhanced}

        scope, scope_reason = determine_scope(suggestion)
        tool = suggestion.get('tool', '')
        action = suggestion.get('action', '')

        if scope == "global":
            pending_id = add_pending_global_rule(suggestion, scope_reason)
            log("ExpSaver", f"待确认全局规则: {tool}→{action}")

            pattern = suggestion.get('pattern', '')
            path = suggestion.get('path', '')
            reason = suggestion.get('reason', '')
            rule_desc = f"{tool} → {action}"
            if pattern:
                rule_desc += f" ({pattern[:20]}...)" if len(pattern) > 20 else f" ({pattern})"

            output = {
                "systemMessage": (
                    f"\n╔══════════════════════════════════════════════════════════╗\n"
                    f"║  🌐 检测到可能适用于【全局】的规则                        ║\n"
                    f"╠══════════════════════════════════════════════════════════╣\n"
                    f"║  规则: {rule_desc:<50} ║\n"
                    f"║  原因: {reason:<50} ║\n"
                    f"╠══════════════════════════════════════════════════════════╣\n"
                    f"║  💬 请回复:「同意全局」「仅本项目」「忽略」              ║\n"
                    f"╚══════════════════════════════════════════════════════════╝"
                )
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            rule_id = save_learned_rule(suggestion, scope="project")
            if rule_id:
                log("ExpSaver", f"保存项目规则: {tool}→{action}")
                output = {"systemMessage": f"📁 学习到项目规则: {suggestion.get('reason', '')}"}
                print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ExpSaver", f"错误: {e}")
