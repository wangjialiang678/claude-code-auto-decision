#!/bin/bash
#
# weekly-review.sh - 每周快速审查工具
#
# 检查全局配置的健康状况，发现潜在问题
#
# Usage:
#   ./weekly-review.sh              # 完整审查
#   ./weekly-review.sh --quick      # 仅检查关键项
#

set -e

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

print_issue() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_ok() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查全局 skills
check_global_skills() {
    print_section "全局 Skills 审查"

    if [ ! -d "$CLAUDE_HOME/skills" ]; then
        print_error "skills 目录不存在"
        return 1
    fi

    local skill_count=$(find "$CLAUDE_HOME/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    echo "全局 skills 数量: $skill_count"
    echo ""

    echo "Skills 清单:"
    find "$CLAUDE_HOME/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | while read skill; do
        local skill_path="$CLAUDE_HOME/skills/$skill"
        local skill_file="$skill_path/SKILL.md"

        if [ -f "$skill_file" ]; then
            # 检查是否包含硬编码路径
            if grep -q "/Users/\|/home/\|C:\\\\\\\\" "$skill_file" 2>/dev/null; then
                print_issue "  $skill - 包含硬编码路径（可能应该是项目级 skill）"
            else
                echo "  - $skill"
            fi

            # 检查最后修改时间
            local mtime=$(stat -f "%Sm" -t "%Y-%m-%d" "$skill_file" 2>/dev/null || stat -c "%y" "$skill_file" 2>/dev/null | cut -d' ' -f1)
            local days_ago=$(( ($(date +%s) - $(date -j -f "%Y-%m-%d" "$mtime" +%s 2>/dev/null || date -d "$mtime" +%s 2>/dev/null)) / 86400 ))

            if [ $days_ago -gt 90 ]; then
                print_issue "    └─ 超过 90 天未修改，是否还在使用？"
            fi
        else
            print_error "  $skill - 缺少 SKILL.md"
        fi
    done
}

# 检查触发词冲突
check_trigger_conflicts() {
    print_section "触发词冲突检测"

    local triggers_file="/tmp/claude_triggers_$$.txt"
    > "$triggers_file"

    # 提取所有触发词
    find "$CLAUDE_HOME/skills" -name "SKILL.md" -exec grep -h "^-" {} \; 2>/dev/null | \
        sed 's/^- //' | sed 's/"//g' | sed "s/'//g" | sort > "$triggers_file"

    # 检查重复
    local duplicates=$(uniq -d "$triggers_file")

    if [ -n "$duplicates" ]; then
        print_issue "发现重复触发词:"
        echo "$duplicates" | sed 's/^/  - /'
        echo ""
        echo "  建议: 为每个 skill 使用唯一的触发词"
    else
        print_ok "无触发词冲突"
    fi

    # 检查通用词（高风险）
    local generic_words="同步 更新 部署 检查 运行 测试 构建 sync update deploy check run test build"
    echo ""
    echo "通用触发词检测（可能误触发）:"

    for word in $generic_words; do
        if grep -q "^$word$" "$triggers_file"; then
            print_issue "  - \"$word\" (建议添加限定词，如 \"同步 Claude Code\")"
        fi
    done

    rm -f "$triggers_file"
}

# 检查全局配置文件
check_global_configs() {
    print_section "全局配置文件检查"

    local configs=(
        "CLAUDE.md"
        "memory-bank/rules.md"
        "config.json"
    )

    for config in "${configs[@]}"; do
        local path="$CLAUDE_HOME/$config"
        if [ -f "$path" ]; then
            local size=$(du -h "$path" | cut -f1)
            local lines=$(wc -l < "$path" | tr -d ' ')
            echo "  - $config: $size ($lines 行)"

            # 检查文件大小
            local size_bytes=$(du -b "$path" 2>/dev/null | cut -f1 || du -k "$path" | cut -f1)
            if [ $size_bytes -gt 102400 ]; then  # >100KB
                print_issue "    └─ 文件较大，建议检查是否有冗余内容"
            fi
        else
            print_issue "  - $config: 不存在"
        fi
    done
}

# 检查最近修改
check_recent_changes() {
    print_section "最近 7 天的修改"

    local changes_found=false

    # 检查全局 skills
    find "$CLAUDE_HOME/skills" -name "SKILL.md" -mtime -7 2>/dev/null | while read file; do
        changes_found=true
        local skill=$(dirname "$file" | xargs basename)
        local mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d'.' -f1)
        echo "  - $skill: $mtime"
    done

    # 检查全局配置
    for config in CLAUDE.md memory-bank/rules.md config.json; do
        local path="$CLAUDE_HOME/$config"
        if [ -f "$path" ]; then
            local mtime_epoch=$(stat -f "%m" "$path" 2>/dev/null || stat -c "%Y" "$path" 2>/dev/null)
            local now_epoch=$(date +%s)
            local days_ago=$(( ($now_epoch - $mtime_epoch) / 86400 ))

            if [ $days_ago -le 7 ]; then
                changes_found=true
                local mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$path" 2>/dev/null || stat -c "%y" "$path" 2>/dev/null | cut -d'.' -f1)
                echo "  - $config: $mtime"
            fi
        fi
    done

    if [ "$changes_found" = false ]; then
        print_ok "最近 7 天无全局修改"
    fi
}

# 检查 hooks 健康状况
check_hooks_health() {
    print_section "Hooks 健康检查"

    local hooks_dir="$CLAUDE_HOME/hooks"

    if [ ! -d "$hooks_dir" ]; then
        print_error "hooks 目录不存在"
        return 1
    fi

    # 检查必需的 hook 文件
    local required_hooks=(
        "pre-tool-use.py"
        "post-tool-use.py"
        "user-prompt-submit.py"
        "stop.py"
    )

    for hook in "${required_hooks[@]}"; do
        if [ -f "$hooks_dir/$hook" ]; then
            print_ok "$hook 存在"
        else
            print_error "$hook 缺失"
        fi
    done

    # 检查 lib 目录
    if [ -d "$hooks_dir/lib" ]; then
        local lib_files=$(find "$hooks_dir/lib" -name "*.py" | wc -l | tr -d ' ')
        echo ""
        echo "lib 文件数量: $lib_files"
    fi
}

# 生成审查报告
generate_report() {
    print_header "审查摘要"

    echo "审查日期: $(date '+%Y-%m-%d %H:%M')"
    echo ""

    echo "建议操作:"
    echo ""

    # 检查是否有需要关注的项
    local has_issues=false

    # 检查 skills 数量
    local skill_count=$(find "$CLAUDE_HOME/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    if [ $skill_count -gt 10 ]; then
        has_issues=true
        echo "  1. 全局 skills 较多 ($skill_count 个)，建议审查是否都需要全局化"
    fi

    # 检查配置文件大小
    if [ -f "$CLAUDE_HOME/memory-bank/rules.md" ]; then
        local rules_lines=$(wc -l < "$CLAUDE_HOME/memory-bank/rules.md" | tr -d ' ')
        if [ $rules_lines -gt 500 ]; then
            has_issues=true
            echo "  2. 规则文件较大 ($rules_lines 行)，建议清理过期规则"
        fi
    fi

    # 检查长期未使用的 skills
    find "$CLAUDE_HOME/skills" -name "SKILL.md" -mtime +90 2>/dev/null | while read file; do
        has_issues=true
        local skill=$(dirname "$file" | xargs basename)
        echo "  3. $skill 超过 90 天未修改，建议检查是否还需要"
    done

    if [ "$has_issues" = false ]; then
        print_ok "未发现需要关注的问题"
    fi

    echo ""
    echo "下次审查: $(date -v+7d '+%Y-%m-%d' 2>/dev/null || date -d '+7 days' '+%Y-%m-%d' 2>/dev/null)"
}

# Main
print_header "Claude Code 每周审查"

check_global_skills
check_trigger_conflicts
check_global_configs
check_recent_changes
check_hooks_health
generate_report

echo ""
echo -e "${GREEN}✅ 审查完成${NC}"
echo ""
