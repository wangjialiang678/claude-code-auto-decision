"""
logger.py - 简洁的调试日志

日志格式：[时间] [Hook名] 消息
日志位置：~/.claude/auto-decision/hooks.log
"""

from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / ".claude" / "auto-decision" / "hooks.log"
MAX_LOG_SIZE = 500 * 1024  # 500KB，超过则截断


def log(hook_name: str, msg: str):
    """写入一行日志"""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # 检查文件大小，超过则截断保留后半部分
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            content = LOG_FILE.read_text()
            # 保留后半部分
            LOG_FILE.write_text(content[len(content)//2:])

        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] [{hook_name}] {msg}\n")
    except:
        pass  # 日志失败不影响主流程
