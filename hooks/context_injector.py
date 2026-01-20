#!/usr/bin/env python3
"""
context_injector.py - UserPromptSubmit Hook
智能上下文注入：在用户提交消息时，注入相关上下文信息
"""

import json
import sys
from pathlib import Path

CLAUDE_HOME = Path.home() / ".claude"
MEMORY_BANK_GLOBAL = CLAUDE_HOME / "memory-bank"
MEMORY_BANK_PROJECT = Path(".claude/memory-bank")

sys.path.insert(0, str(CLAUDE_HOME / "hooks"))
from lib.logger import log


def load_error_patterns() -> list:
    patterns = []
    for patterns_file in [MEMORY_BANK_PROJECT / "learnings" / "error-patterns.json",
                          MEMORY_BANK_GLOBAL / "learnings" / "error-patterns.json"]:
        if patterns_file.exists():
            try:
                data = json.loads(patterns_file.read_text())
                patterns.extend(data.get("patterns", [])[:3])
                patterns.extend(data.get("ai_error_patterns", [])[:2])
            except:
                pass
    return patterns[:5]


def load_core_lesson() -> str:
    for exp_file in [MEMORY_BANK_PROJECT / "learnings" / "experience-library.md",
                     MEMORY_BANK_GLOBAL / "learnings" / "experience-library.md"]:
        if exp_file.exists():
            try:
                content = exp_file.read_text()
                if "## 核心教训" in content:
                    start = content.find("## 核心教训")
                    for line in content[start:start+500].split("\n"):
                        if line.startswith("> 💡"):
                            return line[4:].strip()
            except:
                pass
    return ""


def detect_task_type(prompt: str) -> str:
    prompt_lower = prompt.lower()
    impl_kw = ["实现", "添加", "创建", "写", "修改", "修复", "implement", "add", "create", "fix"]
    simple_kw = ["你好", "谢谢", "好的", "继续", "hello", "thanks", "ok"]

    for kw in simple_kw:
        if kw in prompt_lower:
            return "simple"
    for kw in impl_kw:
        if kw in prompt_lower:
            return "implementation"
    return "general"


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    prompt = data.get("prompt", "")
    if not prompt:
        sys.exit(0)

    task_type = detect_task_type(prompt)
    log("PromptSubmit", f"任务类型: {task_type}")

    if task_type == "simple":
        sys.exit(0)

    context_parts = []

    if task_type == "implementation":
        errors = load_error_patterns()
        if errors:
            err_list = [p.get("pattern", str(p)) if isinstance(p, dict) else str(p) for p in errors]
            context_parts.append("⚠️ 注意避免:\n" + "\n".join(f"- {e}" for e in err_list[:3]))

    lesson = load_core_lesson()
    if lesson:
        context_parts.append(f"💡 {lesson}")

    if context_parts:
        log("PromptSubmit", "注入上下文")
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "message": "📚 已加载经验上下文",
                "systemPrompt": f"<context>\n{chr(10).join(context_parts)}\n</context>"
            }
        }
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("PromptSubmit", f"错误: {e}")
