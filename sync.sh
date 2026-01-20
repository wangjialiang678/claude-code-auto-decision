#!/bin/bash
#
# sync.sh - 同步项目到 Claude Code 生产环境
#
# 将项目目录的改动同步到 ~/.claude/，使修改生效
#
# Usage:
#   ./sync.sh              # 同步所有文件
#   ./sync.sh --dry-run    # 预览将要同步的内容，不实际执行
#   ./sync.sh --diff       # 显示差异
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}!${NC} $1"; }
log_action() { echo -e "${BLUE}→${NC} $1"; }

show_diff() {
    echo ""
    echo "=== 差异检查 ==="
    echo ""

    local has_diff=false

    # Check hooks
    echo "📁 hooks/"
    if diff -rq "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks" > /dev/null 2>&1; then
        echo "   (无变化)"
    else
        diff -rq "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks" 2>/dev/null | head -10 | sed 's/^/   /'
        has_diff=true
    fi

    # Check skills
    for skill in rule-editor experience-learner; do
        echo ""
        echo "📁 skills/$skill/"
        if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
            if diff -rq "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/$skill" > /dev/null 2>&1; then
                echo "   (无变化)"
            else
                diff -rq "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/$skill" 2>/dev/null | head -5 | sed 's/^/   /'
                has_diff=true
            fi
        fi
    done

    # Check config (info only, we preserve user config)
    echo ""
    echo "📄 config.json"
    if diff -q "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/config.json" > /dev/null 2>&1; then
        echo "   (无变化)"
    else
        echo "   (有差异，但会保留用户配置)"
    fi

    # Check rules (info only, we preserve user rules)
    echo ""
    echo "📄 rules.md"
    if diff -q "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md" > /dev/null 2>&1; then
        echo "   (无变化)"
    else
        echo "   (有差异，但会保留用户规则)"
    fi

    echo ""
    if [ "$has_diff" = true ]; then
        return 0
    else
        echo "所有文件已同步，无需更新。"
        return 1
    fi
}

do_sync() {
    local dry_run=$1

    echo ""
    echo "=== 同步到 Claude Code 生产环境 ==="
    echo "源: $SCRIPT_DIR"
    echo "目标: $CLAUDE_HOME"
    echo ""

    # Sync hooks (always overwrite - this is the main code)
    if [ "$dry_run" = true ]; then
        log_action "[预览] hooks/ → ~/.claude/hooks/"
    else
        # 如果是符号链接，先删除
        if [ -L "$CLAUDE_HOME/hooks" ]; then
            rm "$CLAUDE_HOME/hooks"
        fi
        # 复制（覆盖）
        rm -rf "$CLAUDE_HOME/hooks"
        cp -r "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks"
        log_info "hooks/ 已同步"
    fi

    # Sync skills (always overwrite)
    for skill in rule-editor experience-learner; do
        if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
            if [ "$dry_run" = true ]; then
                log_action "[预览] skills/$skill/ → ~/.claude/skills/$skill/"
            else
                mkdir -p "$CLAUDE_HOME/skills"
                if [ -L "$CLAUDE_HOME/skills/$skill" ]; then
                    rm "$CLAUDE_HOME/skills/$skill"
                fi
                rm -rf "$CLAUDE_HOME/skills/$skill"
                cp -r "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/"
                log_info "skills/$skill/ 已同步"
            fi
        fi
    done

    # Config: only create if not exists (preserve user settings)
    if [ ! -f "$CLAUDE_HOME/auto-decision/config.json" ]; then
        if [ "$dry_run" = true ]; then
            log_action "[预览] 创建 config.json"
        else
            mkdir -p "$CLAUDE_HOME/auto-decision"
            cp "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/"
            log_info "config.json 已创建"
        fi
    else
        log_warn "config.json 已存在，保留用户配置"
    fi

    # Rules: only create if not exists (preserve user rules)
    if [ ! -f "$CLAUDE_HOME/memory-bank/rules.md" ]; then
        if [ "$dry_run" = true ]; then
            log_action "[预览] 创建 rules.md"
        else
            mkdir -p "$CLAUDE_HOME/memory-bank"
            cp "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md"
            log_info "rules.md 已创建"
        fi
    else
        log_warn "rules.md 已存在，保留用户规则"
    fi

    echo ""
    if [ "$dry_run" = true ]; then
        echo "预览完成，未执行任何操作。"
        echo "运行 ./sync.sh 来执行同步。"
    else
        echo "✅ 同步完成！修改已生效。"
    fi
}

# Main
case "${1:-}" in
    --diff)
        show_diff
        ;;
    --dry-run)
        do_sync true
        ;;
    *)
        do_sync false
        ;;
esac
