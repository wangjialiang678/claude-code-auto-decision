# Auto-Decision System Library
# 自动决策系统核心库

from pathlib import Path

# 路径常量
CLAUDE_HOME = Path.home() / ".claude"
AUTO_DECISION_DIR = CLAUDE_HOME / "auto-decision"
MEMORY_BANK_GLOBAL = CLAUDE_HOME / "memory-bank"
MEMORY_BANK_PROJECT = Path(".claude/memory-bank")
HOOKS_DIR = CLAUDE_HOME / "hooks"

# 配置文件
CONFIG_FILE = AUTO_DECISION_DIR / "config.json"
PROFILE_FILE = MEMORY_BANK_GLOBAL / "profile.md"
LEARNED_RULES_GLOBAL = MEMORY_BANK_GLOBAL / "learned-rules.md"
LEARNED_RULES_PROJECT = MEMORY_BANK_PROJECT / "learned-rules.md"
RULES_GLOBAL = MEMORY_BANK_GLOBAL / "rules.md"
RULES_PROJECT = MEMORY_BANK_PROJECT / "rules.md"
