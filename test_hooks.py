#!/usr/bin/env python3
"""
测试脚本 - 验证 hooks 的关键功能
"""

import sys
import json
from pathlib import Path

# 添加 hooks 路径
hooks_path = Path(__file__).parent / "hooks"
sys.path.insert(0, str(hooks_path))

# 临时设置规则路径为项目路径（测试用）
from lib import rules as rules_module
project_root = Path(__file__).parent
rules_module.RULES_GLOBAL = project_root / "rules" / "global-rules.md"

from lib.rules import load_rules, match_rules, _rule_key, parse_rules_md
from lib.storage import simplify_input
from lib.patterns import determine_scope


def test_rule_loading():
    """测试规则加载"""
    print("\n=== 测试 1: 规则加载 ===")
    rules = load_rules()
    print(f"✓ 成功加载 {len(rules)} 条规则")

    # 验证规则去重
    keys = set()
    duplicates = []
    for rule in rules:
        key = _rule_key(rule)
        if key in keys:
            duplicates.append(rule.get('id'))
        keys.add(key)

    if duplicates:
        print(f"✗ 发现重复规则: {duplicates}")
    else:
        print("✓ 无重复规则")

    return len(rules) > 0


def test_grep_command():
    """测试 grep 命令是否被允许"""
    print("\n=== 测试 2: Bash grep 命令 ===")
    rules = load_rules()

    # 测试 grep 命令
    test_cases = [
        ("grep", {"command": "grep -r 'test' ."}),
        ("find", {"command": "find . -name '*.py'"}),
        ("awk", {"command": "awk '{print $1}' file.txt"}),
        ("sed", {"command": "sed 's/foo/bar/g' file.txt"}),
    ]

    all_passed = True
    for name, (tool, input_data) in [("Bash", case) for case in test_cases]:
        action, reason = match_rules(name, input_data, rules)
        if action == "allow":
            print(f"✓ {input_data['command'][:30]}... → {action}")
        else:
            print(f"✗ {input_data['command'][:30]}... → {action} (应该是 allow)")
            all_passed = False

    return all_passed


def test_rule_matching():
    """测试规则匹配"""
    print("\n=== 测试 3: 规则匹配 ===")
    rules = load_rules()

    test_cases = [
        ("Read", {"file_path": "/tmp/test.txt"}, "allow"),
        ("Write", {"file_path": "/tmp/.env"}, "deny"),
        ("Bash", {"command": "rm -rf /"}, "deny"),
        ("Bash", {"command": "npm test"}, "allow"),
        ("TodoWrite", {"todos": []}, "allow"),
    ]

    all_passed = True
    for tool, input_data, expected in test_cases:
        action, reason = match_rules(tool, input_data, rules)
        status = "✓" if action == expected else "✗"
        print(f"{status} {tool} → {action} (期望: {expected})")
        if action != expected:
            all_passed = False

    return all_passed


def test_scope_determination():
    """测试 scope 判断"""
    print("\n=== 测试 4: Scope 智能判断 ===")

    test_cases = [
        ({"tool": "Read", "action": "allow"}, "global"),
        ({"tool": "Bash", "action": "deny", "pattern": "rm -rf"}, "global"),
        ({"tool": "Bash", "action": "allow", "pattern": "^npm test"}, "project"),
        ({"tool": "Write", "action": "allow", "path": "**/*.ts"}, "project"),
        ({"tool": "TodoWrite", "action": "allow"}, "global"),
    ]

    all_passed = True
    for rule, expected_scope in test_cases:
        scope, reason = determine_scope(rule)
        status = "✓" if scope == expected_scope else "✗"
        tool = rule.get('tool', '')
        print(f"{status} {tool} → {scope} (期望: {expected_scope})")
        if scope != expected_scope:
            all_passed = False

    return all_passed


def test_input_simplification():
    """测试输入简化"""
    print("\n=== 测试 5: 输入简化 ===")

    # 测试长内容截断
    long_content = "x" * 200
    result = simplify_input({"content": long_content})

    if "content_preview" in result and len(result["content_preview"]) <= 104:
        print(f"✓ 长内容已截断: {len(long_content)} → {len(result['content_preview'])}")
    else:
        print(f"✗ 内容截断失败")
        return False

    # 测试命令保留
    result = simplify_input({"command": "npm test", "file_path": "/tmp/test.py"})
    if result.get("command") == "npm test" and result.get("file_path") == "/tmp/test.py":
        print("✓ 命令和路径正确保留")
    else:
        print("✗ 命令或路径丢失")
        return False

    return True


def main():
    print("=" * 60)
    print("Claude Code Auto-Decision System - 测试套件")
    print("=" * 60)

    results = []

    results.append(("规则加载", test_rule_loading()))
    results.append(("Bash grep 命令", test_grep_command()))
    results.append(("规则匹配", test_rule_matching()))
    results.append(("Scope 判断", test_scope_determination()))
    results.append(("输入简化", test_input_simplification()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status:10} - {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过!")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
