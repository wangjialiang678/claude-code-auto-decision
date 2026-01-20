#!/bin/bash
#
# Claude Code Auto-Decision System Updater
#
# 从项目目录同步更新到 ~/.claude/ 配置目录
#
# Usage:
#   ./update.sh              # 同步所有文件到 ~/.claude/
#   ./update.sh --check      # 只检查是否有更新，不执行
#   ./update.sh --dry-run    # 显示将要执行的操作，不实际执行
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"
VERSION_FILE="${CLAUDE_HOME}/auto-decision/.installed-version"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_action() { echo -e "${BLUE}[ACTION]${NC} $1"; }

get_local_version() {
    if [ -f "$SCRIPT_DIR/.git/HEAD" ]; then
        git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

get_installed_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "not-installed"
    fi
}

check_for_updates() {
    local local_ver=$(get_local_version)
    local installed_ver=$(get_installed_version)

    if [ "$local_ver" = "$installed_ver" ]; then
        echo "up-to-date"
    else
        echo "needs-update"
    fi
}

show_diff() {
    log_info "Checking differences..."

    local has_diff=false

    # Check hooks
    if ! diff -rq "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks" > /dev/null 2>&1; then
        log_warn "hooks/ has changes"
        has_diff=true
    fi

    # Check config
    if ! diff -q "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/config.json" > /dev/null 2>&1; then
        log_warn "config/config.json has changes"
        has_diff=true
    fi

    # Check rules
    if ! diff -q "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md" > /dev/null 2>&1; then
        log_warn "rules/global-rules.md has changes"
        has_diff=true
    fi

    # Check skills
    for skill in rule-editor experience-learner; do
        if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
            if ! diff -rq "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/$skill" > /dev/null 2>&1; then
                log_warn "skills/$skill has changes"
                has_diff=true
            fi
        fi
    done

    if [ "$has_diff" = false ]; then
        log_info "No differences found. System is up to date."
        return 1
    fi
    return 0
}

do_update() {
    local dry_run=$1

    log_info "Updating Claude Code Auto-Decision System..."

    # Update hooks
    if [ "$dry_run" = true ]; then
        log_action "[DRY-RUN] Would copy hooks/ -> ~/.claude/hooks/"
    else
        # 备份现有 hooks（如果不是符号链接）
        if [ -d "$CLAUDE_HOME/hooks" ] && [ ! -L "$CLAUDE_HOME/hooks" ]; then
            cp -r "$CLAUDE_HOME/hooks" "$CLAUDE_HOME/hooks.backup.$(date +%Y%m%d%H%M%S)"
            log_info "Backed up existing hooks"
        fi
        rm -rf "$CLAUDE_HOME/hooks"
        cp -r "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks"
        log_info "Updated: hooks/"
    fi

    # Update config (preserve user modifications)
    if [ "$dry_run" = true ]; then
        log_action "[DRY-RUN] Would update config.json (preserving user settings)"
    else
        mkdir -p "$CLAUDE_HOME/auto-decision"
        # 只更新不存在的配置，保留用户自定义
        if [ ! -f "$CLAUDE_HOME/auto-decision/config.json" ]; then
            cp "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/"
            log_info "Created: config.json"
        else
            log_warn "Skipped: config.json (already exists, preserving user settings)"
        fi
    fi

    # Update global rules (only if user hasn't customized)
    if [ "$dry_run" = true ]; then
        log_action "[DRY-RUN] Would check/update rules.md"
    else
        mkdir -p "$CLAUDE_HOME/memory-bank"
        if [ ! -f "$CLAUDE_HOME/memory-bank/rules.md" ]; then
            cp "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md"
            log_info "Created: rules.md"
        else
            log_warn "Skipped: rules.md (already exists, preserving user rules)"
        fi
    fi

    # Update skills
    for skill in rule-editor experience-learner; do
        if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
            if [ "$dry_run" = true ]; then
                log_action "[DRY-RUN] Would copy skills/$skill"
            else
                mkdir -p "$CLAUDE_HOME/skills"
                rm -rf "$CLAUDE_HOME/skills/$skill"
                cp -r "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/"
                log_info "Updated: skills/$skill"
            fi
        fi
    done

    # Record installed version
    if [ "$dry_run" != true ]; then
        mkdir -p "$(dirname "$VERSION_FILE")"
        get_local_version > "$VERSION_FILE"
        log_info "Version recorded: $(get_local_version)"
    fi

    if [ "$dry_run" = true ]; then
        log_info "Dry run complete. No changes made."
    else
        log_info "Update complete! Restart Claude Code to apply changes."
    fi
}

# Main
case "${1:-}" in
    --check)
        local_ver=$(get_local_version)
        installed_ver=$(get_installed_version)

        log_info "Project version: $local_ver"
        log_info "Installed version: $installed_ver"

        if [ "$(check_for_updates)" = "needs-update" ]; then
            log_warn "Updates available!"
            show_diff
            exit 1
        else
            log_info "System is up to date."
            exit 0
        fi
        ;;
    --dry-run)
        do_update true
        ;;
    *)
        do_update false
        ;;
esac
