"""
rules.py - 规则加载、解析、匹配

支持 Markdown 格式的规则文件，格式如下：

### rule-name
- tool: Bash
  action: allow
  pattern: ^npm test
  reason: 说明文字
"""

import re
from pathlib import Path
from typing import Optional
from . import (
    LEARNED_RULES_GLOBAL,
    LEARNED_RULES_PROJECT,
    RULES_GLOBAL,
    RULES_PROJECT,
)


def load_rules() -> list[dict]:
    """
    加载所有规则，按优先级排序：
    1. 项目 learned-rules.md（项目学习的规则，最高优先级）
    2. 项目 rules.md（项目手动规则）
    3. 全局 learned-rules.md（全局学习的规则）
    4. 全局 rules.md（全局手动规则，最低优先级）
    """
    rules = []

    # 优先级从高到低
    rule_files = [
        (LEARNED_RULES_PROJECT, "project-learned"),
        (RULES_PROJECT, "project-base"),
        (LEARNED_RULES_GLOBAL, "global-learned"),
        (RULES_GLOBAL, "global-base"),
    ]

    for file_path, source in rule_files:
        if file_path.exists():
            parsed = parse_rules_md(file_path.read_text())
            for rule in parsed:
                rule["source"] = source
            rules.extend(parsed)

    return rules


def parse_rules_md(content: str) -> list[dict]:
    """
    解析 Markdown 格式的规则文件

    支持的格式：
    ### rule-name
    - tool: Bash
      action: allow
      pattern: ^npm test
      reason: 说明
    """
    rules = []

    # 按 ### 分割，找到包含 "- tool:" 的块
    sections = re.split(r'\n###\s+', content)

    for section in sections:
        if '- tool:' not in section:
            continue

        # 提取规则 ID（第一行）
        lines = section.strip().split('\n')
        rule_id = lines[0].split()[0] if lines else "unknown"

        # 提取规则块（从 - tool: 开始）
        block_start = section.find('- tool:')
        if block_start == -1:
            continue

        block = section[block_start:]
        # 截取到下一个空行或文件结束
        block = block.split('\n\n')[0]

        rule = parse_rule_block(block)
        if rule and "tool" in rule:
            rule["id"] = rule_id
            rules.append(rule)

    return rules


def parse_rule_block(block: str) -> dict:
    """
    解析单个规则块

    输入格式：
    - tool: Bash
      action: allow
      pattern: ^npm test
      reason: 说明
    """
    rule = {}

    # 简单的 key: value 解析
    lines = block.strip().split('\n')
    for line in lines:
        # 去掉前导的 - 和空格
        line = re.sub(r'^[-\s]+', '', line)
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                rule[key] = value

    return rule


def match_rules(tool_name: str, tool_input: dict, rules: list[dict]) -> tuple[str, Optional[str]]:
    """
    匹配规则，返回 (action, reason)

    如果没有匹配的规则，返回 ("ask", None)
    """
    for rule in rules:
        if matches(rule, tool_name, tool_input):
            return rule.get("action", "ask"), rule.get("reason")

    return "ask", None


def matches(rule: dict, tool_name: str, tool_input: dict) -> bool:
    """检查单条规则是否匹配"""

    # 检查工具名（支持正则，如 "Write|Edit"）
    if "tool" in rule:
        tool_pattern = rule["tool"]
        if not re.match(f"^({tool_pattern})$", tool_name):
            return False

    # 检查命令/内容模式
    if "pattern" in rule:
        # 对于 Bash，匹配 command
        # 对于 Write/Edit，匹配 content 或 file_path
        text = tool_input.get("command", "") or tool_input.get("content", "") or ""
        try:
            if not re.search(rule["pattern"], text):
                return False
        except re.error:
            # 正则语法错误，跳过这条规则
            return False

    # 检查路径模式（glob）
    if "path" in rule:
        file_path = tool_input.get("file_path", "")
        if file_path:
            import fnmatch
            pattern = rule["path"].strip('"\'')  # 去掉引号
            # 支持 **/ 前缀（匹配任意目录）
            if pattern.startswith("**/"):
                # 只匹配文件名部分
                filename = Path(file_path).name
                file_pattern = pattern[3:]  # 去掉 **/
                if not fnmatch.fnmatch(filename, file_pattern):
                    return False
            else:
                if not fnmatch.fnmatch(file_path, pattern):
                    return False
        else:
            return False

    return True
