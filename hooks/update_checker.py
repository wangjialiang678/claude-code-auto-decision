#!/usr/bin/env python3
"""
update_checker.py - UserPromptSubmit Hook (Optional)

在新会话开始时检查是否有更新可用。
每天最多提醒一次。

要启用此功能，在 settings.json 的 UserPromptSubmit hooks 中添加此脚本。
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置
PROJECT_DIR = Path.home() / "projects" / "claude-code-auto-decision"
CLAUDE_HOME = Path.home() / ".claude"
CHECK_FILE = CLAUDE_HOME / "auto-decision" / ".last-update-check"
CHECK_INTERVAL_HOURS = 24


def should_check() -> bool:
    """是否应该检查更新（每天最多一次）"""
    if not CHECK_FILE.exists():
        return True

    try:
        last_check = datetime.fromisoformat(CHECK_FILE.read_text().strip())
        hours_since = (datetime.now() - last_check).total_seconds() / 3600
        return hours_since >= CHECK_INTERVAL_HOURS
    except:
        return True


def record_check():
    """记录本次检查时间"""
    CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECK_FILE.write_text(datetime.now().isoformat())


def check_for_updates() -> tuple[bool, str]:
    """
    检查是否有更新

    返回: (has_updates, message)
    """
    if not PROJECT_DIR.exists():
        return False, ""

    update_script = PROJECT_DIR / "update.sh"
    if not update_script.exists():
        return False, ""

    try:
        result = subprocess.run(
            [str(update_script), "--check"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_DIR),
        )
        # exit code 1 means updates available
        if result.returncode == 1:
            return True, "Auto-Decision 系统有更新可用"
        return False, ""
    except:
        return False, ""


def main():
    # 读取输入（必须消费 stdin）
    try:
        data = json.load(sys.stdin)
    except:
        data = {}

    # 检查是否应该检查更新
    if not should_check():
        sys.exit(0)

    record_check()

    has_updates, message = check_for_updates()

    if has_updates:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "message": f"🔄 {message}",
                "systemPrompt": (
                    "<update-reminder>\n"
                    "Auto-Decision 系统有更新可用。\n"
                    "用户可以运行以下命令来更新：\n"
                    f"cd {PROJECT_DIR} && git pull && ./update.sh\n"
                    "或者说「更新 auto-decision」让你帮忙执行。\n"
                    "</update-reminder>"
                ),
            }
        }
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # 更新检查失败不影响正常使用
