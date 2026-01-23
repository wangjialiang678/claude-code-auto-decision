#!/bin/bash
#
# check-updates.sh - 检查项目更新并提供同步建议
#
# Usage:
#   ./check-updates.sh              # 检查所有更新
#   ./check-updates.sh --auto-sync  # 自动同步代码（不包括规则）
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
}

check_git_status() {
    print_section "Git 仓库状态"

    # 检查是否有未提交的本地修改
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "${YELLOW}⚠ 有未提交的本地修改${NC}"
        git status -s | head -5
    else
        echo -e "${GREEN}✓ 工作目录干净${NC}"
    fi

    # 检查远程更新
    echo ""
    echo "检查远程更新..."
    git fetch origin main 2>/dev/null || true

    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse origin/main 2>/dev/null)

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}⚠ 远程仓库有新提交${NC}"
        echo ""
        echo "新提交:"
        git log --oneline HEAD..origin/main | head -5
        echo ""
        echo -e "${CYAN}运行 'git pull' 来更新${NC}"
        return 1
    else
        echo -e "${GREEN}✓ 已是最新版本${NC}"
        return 0
    fi
}

check_hooks_diff() {
    print_section "Hooks 代码差异"

    if [ ! -d "$CLAUDE_HOME/hooks" ]; then
        echo -e "${RED}✗ hooks 目录不存在${NC}"
        return 1
    fi

    # 排除临时文件的差异检查
    local diff_output=$(diff -rq "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks" 2>/dev/null | grep -v ".experience_counter" | grep -v "^Only in")

    if [ -z "$diff_output" ]; then
        echo -e "${GREEN}✓ hooks 已同步${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ hooks 有差异${NC}"
        echo ""
        echo "$diff_output" | head -10
        echo ""
        echo -e "${CYAN}运行 './sync.sh' 来同步${NC}"
        return 1
    fi
}

check_rules_diff() {
    print_section "规则文件差异"

    if [ ! -f "$CLAUDE_HOME/memory-bank/rules.md" ]; then
        echo -e "${YELLOW}⚠ 规则文件不存在${NC}"
        return 1
    fi

    if diff -q "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 规则文件已同步${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 规则文件有差异${NC}"
        echo ""
        echo "差异摘要:"
        diff -u "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md" 2>/dev/null | grep "^[+-]" | grep -v "^[+-][+-][+-]" | head -10
        echo ""
        echo -e "${CYAN}检查差异: diff -u rules/global-rules.md ~/.claude/memory-bank/rules.md${NC}"
        echo -e "${CYAN}更新规则: cp rules/global-rules.md ~/.claude/memory-bank/rules.md${NC}"
        echo -e "${YELLOW}注意: 更新前请确认没有自定义规则${NC}"
        return 1
    fi
}

check_config_diff() {
    print_section "配置文件检查"

    if [ ! -f "$CLAUDE_HOME/auto-decision/config.json" ]; then
        echo -e "${YELLOW}⚠ 配置文件不存在${NC}"
        return 1
    fi

    if diff -q "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/config.json" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 配置文件已同步${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 配置文件有差异${NC}"
        echo ""
        echo "差异:"
        diff -u "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/config.json" 2>/dev/null | grep "^[+-]" | grep -v "^[+-][+-][+-]"
        echo ""
        echo -e "${CYAN}建议: 手动合并新配置项到现有配置${NC}"
        return 1
    fi
}

run_tests() {
    print_section "运行测试"

    if [ ! -f "$SCRIPT_DIR/test_hooks.py" ]; then
        echo -e "${YELLOW}⚠ 测试脚本不存在${NC}"
        return 0
    fi

    if python3 "$SCRIPT_DIR/test_hooks.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 所有测试通过${NC}"
        return 0
    else
        echo -e "${RED}✗ 测试失败${NC}"
        echo ""
        echo "运行测试查看详情: python3 test_hooks.py"
        return 1
    fi
}

print_summary() {
    local git_ok=$1
    local hooks_ok=$2
    local rules_ok=$3
    local config_ok=$4
    local tests_ok=$5

    print_header "更新检查摘要"

    echo "状态:"
    [ $git_ok -eq 0 ] && echo -e "  ${GREEN}✓${NC} Git 仓库最新" || echo -e "  ${YELLOW}⚠${NC} Git 有更新"
    [ $hooks_ok -eq 0 ] && echo -e "  ${GREEN}✓${NC} Hooks 已同步" || echo -e "  ${YELLOW}⚠${NC} Hooks 需同步"
    [ $rules_ok -eq 0 ] && echo -e "  ${GREEN}✓${NC} 规则文件已同步" || echo -e "  ${YELLOW}⚠${NC} 规则文件有差异"
    [ $config_ok -eq 0 ] && echo -e "  ${GREEN}✓${NC} 配置文件已同步" || echo -e "  ${YELLOW}⚠${NC} 配置文件有差异"
    [ $tests_ok -eq 0 ] && echo -e "  ${GREEN}✓${NC} 测试通过" || echo -e "  ${RED}✗${NC} 测试失败"

    echo ""

    if [ $git_ok -ne 0 ] || [ $hooks_ok -ne 0 ] || [ $rules_ok -ne 0 ] || [ $config_ok -ne 0 ]; then
        echo "建议操作:"
        [ $git_ok -ne 0 ] && echo "  1. git pull"
        [ $hooks_ok -ne 0 ] && echo "  2. ./sync.sh"
        [ $rules_ok -ne 0 ] && echo "  3. 检查并更新 rules.md（见上文）"
        [ $config_ok -ne 0 ] && echo "  4. 合并新配置项（见上文）"
        echo ""
        echo "详细说明: docs/update-strategy.md"
    else
        echo -e "${GREEN}✅ 所有组件都是最新版本！${NC}"
    fi

    echo ""
}

# Main
print_header "Claude Code Auto-Decision - 更新检查"

# 执行检查
check_git_status
git_status=$?

check_hooks_diff
hooks_status=$?

check_rules_diff
rules_status=$?

check_config_diff
config_status=$?

run_tests
tests_status=$?

# 输出摘要
print_summary $git_status $hooks_status $rules_status $config_status $tests_status

# 自动同步模式
if [ "${1:-}" = "--auto-sync" ]; then
    if [ $hooks_status -ne 0 ]; then
        echo ""
        echo -e "${BLUE}自动同步 hooks...${NC}"
        ./sync.sh
    fi
fi

# 返回状态
if [ $git_status -ne 0 ] || [ $hooks_status -ne 0 ] || [ $rules_status -ne 0 ] || [ $config_status -ne 0 ]; then
    exit 1
else
    exit 0
fi
