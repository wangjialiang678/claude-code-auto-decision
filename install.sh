#!/bin/bash
#
# Claude Code Auto-Decision System Installer
#
# Usage:
#   ./install.sh          # Install (symlink mode, auto-sync on git pull)
#   ./install.sh --copy   # Install (copy mode, manual update needed)
#   ./install.sh --uninstall  # Remove installation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${HOME}/.claude"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

install_symlink() {
    log_info "Installing in symlink mode (auto-sync on git pull)..."

    # Backup existing hooks if not symlink
    if [ -d "$CLAUDE_HOME/hooks" ] && [ ! -L "$CLAUDE_HOME/hooks" ]; then
        log_warn "Backing up existing hooks to hooks.backup"
        mv "$CLAUDE_HOME/hooks" "$CLAUDE_HOME/hooks.backup"
    fi

    # Create symlinks
    ln -sf "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/hooks"
    log_info "Linked: hooks -> $SCRIPT_DIR/hooks"

    # Config directory
    mkdir -p "$CLAUDE_HOME/auto-decision"
    if [ ! -f "$CLAUDE_HOME/auto-decision/config.json" ]; then
        cp "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/"
        log_info "Copied: config.json (first install)"
    else
        log_warn "Skipped: config.json already exists"
    fi

    # Rules (only if not exists)
    mkdir -p "$CLAUDE_HOME/memory-bank"
    if [ ! -f "$CLAUDE_HOME/memory-bank/rules.md" ]; then
        cp "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md"
        log_info "Copied: rules.md (first install)"
    else
        log_warn "Skipped: rules.md already exists"
    fi

    # Skills (symlink)
    mkdir -p "$CLAUDE_HOME/skills"
    for skill in rule-editor experience-learner; do
        if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
            rm -rf "$CLAUDE_HOME/skills/$skill"
            ln -sf "$SCRIPT_DIR/skills/$skill" "$CLAUDE_HOME/skills/$skill"
            log_info "Linked: skills/$skill"
        fi
    done

    # Update settings.json hooks config
    update_settings

    log_info "Installation complete! Restart Claude Code to apply changes."
}

install_copy() {
    log_info "Installing in copy mode..."

    # Copy hooks
    cp -r "$SCRIPT_DIR/hooks" "$CLAUDE_HOME/"
    log_info "Copied: hooks/"

    # Config
    mkdir -p "$CLAUDE_HOME/auto-decision"
    cp "$SCRIPT_DIR/config/config.json" "$CLAUDE_HOME/auto-decision/"
    log_info "Copied: config.json"

    # Rules
    mkdir -p "$CLAUDE_HOME/memory-bank"
    cp "$SCRIPT_DIR/rules/global-rules.md" "$CLAUDE_HOME/memory-bank/rules.md"
    log_info "Copied: rules.md"

    # Skills
    mkdir -p "$CLAUDE_HOME/skills"
    cp -r "$SCRIPT_DIR/skills/"* "$CLAUDE_HOME/skills/"
    log_info "Copied: skills/"

    update_settings

    log_info "Installation complete! Restart Claude Code to apply changes."
    log_warn "Note: In copy mode, run install.sh again after git pull to update."
}

update_settings() {
    local settings_file="$CLAUDE_HOME/settings.json"

    if [ ! -f "$settings_file" ]; then
        log_info "Creating settings.json with hooks config..."
        cat > "$settings_file" << 'EOF'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/context_injector.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/auto_decision.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/feedback_collector.py"
          },
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/experience_saver.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/session_reviewer.py"
          }
        ]
      }
    ]
  }
}
EOF
    else
        log_warn "settings.json exists. Please manually add hooks config if needed."
        log_info "See README.md for hooks configuration."
    fi
}

uninstall() {
    log_info "Uninstalling..."

    # Remove symlinks or directories
    if [ -L "$CLAUDE_HOME/hooks" ]; then
        rm "$CLAUDE_HOME/hooks"
        log_info "Removed: hooks symlink"
    fi

    for skill in rule-editor experience-learner; do
        if [ -L "$CLAUDE_HOME/skills/$skill" ]; then
            rm "$CLAUDE_HOME/skills/$skill"
            log_info "Removed: skills/$skill symlink"
        fi
    done

    # Restore backup if exists
    if [ -d "$CLAUDE_HOME/hooks.backup" ]; then
        mv "$CLAUDE_HOME/hooks.backup" "$CLAUDE_HOME/hooks"
        log_info "Restored: hooks from backup"
    fi

    log_warn "Note: settings.json, config.json, rules.md were not removed."
    log_info "Uninstall complete."
}

# Main
case "${1:-}" in
    --copy)
        install_copy
        ;;
    --uninstall)
        uninstall
        ;;
    *)
        install_symlink
        ;;
esac
