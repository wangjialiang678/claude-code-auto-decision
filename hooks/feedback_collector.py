#!/usr/bin/env python3
"""
feedback_collector.py - PostToolUse Hook
记录工具执行结果：如果触发了这个 hook，说明用户批准了操作
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.logger import log
from lib.storage import update_request_executed


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_use_id = data.get("tool_use_id", "")

    if tool_use_id:
        updated = update_request_executed(tool_use_id, executed=True)
        if updated:
            log("PostToolUse", f"{tool_name} 已执行")
        else:
            log("PostToolUse", f"未找到记录: {tool_name} {tool_use_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("PostToolUse", f"错误: {e}")
