#!/usr/bin/env python3
"""
session_reviewer.py - Stop Hook
会话总结：在会话结束时生成总结报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.logger import log
from lib.storage import load_config, get_recent_feedback, write_session_summary
from lib.llm import is_llm_enabled, llm_generate_session_summary, generate_simple_summary


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}

    session_id = data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))

    config = load_config()
    if not config.get("session_review", {}).get("enabled", True):
        sys.exit(0)

    feedback = get_recent_feedback(days=1)
    session_feedback = [f for f in feedback if f.get("session_id") == session_id]

    min_actions = config.get("session_review", {}).get("min_actions", 5)
    if len(session_feedback) < min_actions:
        log("Stop", f"操作数不足 ({len(session_feedback)}<{min_actions})")
        sys.exit(0)

    stats = {
        "total": len(session_feedback),
        "auto_allowed": sum(1 for f in session_feedback if f.get("auto_decision") == "allow"),
        "auto_denied": sum(1 for f in session_feedback if f.get("auto_decision") == "deny"),
        "user_approved": sum(1 for f in session_feedback if f.get("auto_decision") == "ask" and f.get("executed") is True),
    }

    if is_llm_enabled():
        summary_content = llm_generate_session_summary(session_feedback, stats)
    else:
        summary_content = generate_simple_summary(stats)

    summary = f"""# 会话总结

**日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{summary_content}

## 统计
- 总操作: {stats['total']}
- 自动允许: {stats['auto_allowed']}
- 用户批准: {stats['user_approved']}
"""

    write_session_summary(session_id, summary)
    log("Stop", f"会话总结已保存 ({stats['total']}次操作)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("Stop", f"错误: {e}")
