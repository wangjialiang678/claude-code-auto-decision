"""
storage.py - 数据读写

处理 feedback 日志和 session 总结的读写
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from . import MEMORY_BANK_PROJECT, MEMORY_BANK_GLOBAL, CONFIG_FILE


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {
        "version": "1.0",
        "learning": {"enabled": True, "threshold": 3, "confidence_min": 0.8},
        "llm": {"enabled": False},
        "session_review": {"enabled": True, "min_actions": 5},
    }


def ensure_project_dirs():
    """确保项目级目录存在"""
    (MEMORY_BANK_PROJECT / "feedback").mkdir(parents=True, exist_ok=True)
    (MEMORY_BANK_PROJECT / "sessions").mkdir(parents=True, exist_ok=True)


def log_request(
    request_id: str,
    tool_name: str,
    tool_input: dict,
    auto_decision: str,
    session_id: str = "",
):
    """
    记录工具调用请求

    写入 .claude/memory-bank/feedback/{date}.jsonl
    """
    ensure_project_dirs()

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = MEMORY_BANK_PROJECT / "feedback" / f"{date_str}.jsonl"

    # 简化 input，避免存储过大内容
    simplified_input = simplify_input(tool_input)

    entry = {
        "id": request_id,
        "ts": datetime.now().isoformat(),
        "session_id": session_id,
        "tool": tool_name,
        "input": simplified_input,
        "auto_decision": auto_decision,
        "executed": None,  # 待 PostToolUse 更新
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def update_request_executed(request_id: str, executed: bool = True, search_days: int = 7) -> bool:
    """
    更新请求的执行状态

    在 PostToolUse 中调用，标记请求已执行（用户批准了）
    """
    for i in range(search_days):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        log_file = MEMORY_BANK_PROJECT / "feedback" / f"{date_str}.jsonl"

        if not log_file.exists():
            continue

        # 读取所有行，更新匹配的请求
        lines = log_file.read_text().strip().split("\n")
        updated_lines = []
        updated = False

        for line in lines:
            if line:
                entry = json.loads(line)
                if entry.get("id") == request_id:
                    entry["executed"] = executed
                    updated = True
                updated_lines.append(json.dumps(entry, ensure_ascii=False))

        if updated:
            log_file.write_text("\n".join(updated_lines) + "\n")
            return True

    return False


def get_recent_feedback(days: int = 7) -> list[dict]:
    """获取最近 N 天的反馈记录"""
    feedback_dir = MEMORY_BANK_PROJECT / "feedback"
    if not feedback_dir.exists():
        return []

    entries = []
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        log_file = feedback_dir / f"{date_str}.jsonl"

        if log_file.exists():
            for line in log_file.read_text().strip().split("\n"):
                if line:
                    entries.append(json.loads(line))

    return entries


def write_session_summary(session_id: str, summary: str):
    """
    写入会话总结

    写入 .claude/memory-bank/sessions/{session-id}.md
    """
    ensure_project_dirs()

    session_file = MEMORY_BANK_PROJECT / "sessions" / f"{session_id}.md"
    session_file.write_text(summary, encoding="utf-8")


def simplify_input(tool_input: dict) -> dict:
    """简化工具输入，避免存储过大内容"""
    result = {}

    if "command" in tool_input:
        # Bash 命令：保留完整命令（通常不长）
        result["command"] = tool_input["command"][:500]

    if "file_path" in tool_input:
        result["file_path"] = tool_input["file_path"]

    if "content" in tool_input:
        # 文件内容：只保留前 100 字符
        result["content_preview"] = tool_input["content"][:100] + "..."

    if "pattern" in tool_input:
        result["pattern"] = tool_input["pattern"]

    if "query" in tool_input:
        result["query"] = tool_input["query"][:200]

    return result
