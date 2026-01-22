# Reality Check Makefile

.PHONY: help install-claude-plugin uninstall-claude-plugin install-claude-skills uninstall-claude-skills install-codex-skills uninstall-codex-skills install-amp-skills uninstall-amp-skills test test-all init clean assemble-skills check-skills

help:
	@echo "Reality Check - Available targets:"
	@echo ""
	@echo "  Amp:"
	@echo "    install-amp-skills       Install Amp skills (~/.config/agents/skills/)"
	@echo "    uninstall-amp-skills     Remove Amp skills"
	@echo ""
	@echo "  Claude Code:"
	@echo "    install-claude-plugin    Install plugin (use with: claude --plugin-dir ...)"
	@echo "    uninstall-claude-plugin  Remove plugin"
	@echo "    install-claude-skills    Install global skills (~/.claude/skills/)"
	@echo "    uninstall-claude-skills  Remove global skills"
	@echo ""
	@echo "  Codex:"
	@echo "    install-codex-skills     Install Codex skills"
	@echo "    uninstall-codex-skills   Remove Codex skills"
	@echo ""
	@echo "  Development:"
	@echo "    assemble-skills          Generate skills from templates"
	@echo "    check-skills             Check if generated skills are up-to-date"
	@echo "    test                     Run tests (skip embedding tests)"
	@echo "    test-all                 Run all tests including embeddings"
	@echo "    init                     Initialize database"
	@echo "    clean                    Remove generated files"
	@echo ""

# Paths
CLAUDE_PLUGIN_SRC := $(CURDIR)/integrations/claude/plugin
CLAUDE_SKILLS_SRC := $(CURDIR)/integrations/claude/skills

# Claude Code plugin installation
# Note: Local plugin discovery from ~/.claude/plugins/local/ is currently broken.
# Use --plugin-dir flag instead: claude --plugin-dir /path/to/integrations/claude/plugin
PLUGIN_DIR := $(HOME)/.claude/plugins/local
PLUGIN_NAME := reality

install-claude-plugin:
	@echo "Installing Reality Check plugin to Claude Code..."
	@mkdir -p $(PLUGIN_DIR)
	@if [ -L "$(PLUGIN_DIR)/$(PLUGIN_NAME)" ]; then \
		echo "Removing existing symlink..."; \
		rm "$(PLUGIN_DIR)/$(PLUGIN_NAME)"; \
	elif [ -d "$(PLUGIN_DIR)/$(PLUGIN_NAME)" ]; then \
		echo "Warning: $(PLUGIN_DIR)/$(PLUGIN_NAME) exists as directory"; \
		echo "Remove it manually if you want to use symlink install"; \
		exit 1; \
	fi
	@ln -s "$(CLAUDE_PLUGIN_SRC)" "$(PLUGIN_DIR)/$(PLUGIN_NAME)"
	@echo "Plugin installed: $(PLUGIN_DIR)/$(PLUGIN_NAME) -> $(CLAUDE_PLUGIN_SRC)"
	@echo ""
	@echo "NOTE: Local plugin discovery is currently broken in Claude Code."
	@echo "Use the --plugin-dir flag instead:"
	@echo ""
	@echo "  claude --plugin-dir $(CLAUDE_PLUGIN_SRC)"
	@echo ""
	@echo "Commands will be available as: /reality:check, /reality:analyze, etc."

uninstall-claude-plugin:
	@echo "Removing Reality Check plugin..."
	@if [ -L "$(PLUGIN_DIR)/$(PLUGIN_NAME)" ]; then \
		rm "$(PLUGIN_DIR)/$(PLUGIN_NAME)"; \
		echo "Plugin removed."; \
	else \
		echo "Plugin symlink not found at $(PLUGIN_DIR)/$(PLUGIN_NAME)"; \
	fi

# Claude Code skills installation (global skills)
SKILLS_DIR := $(HOME)/.claude/skills
CLAUDE_SKILLS := check analyze extract search validate export stats realitycheck

install-claude-skills:
	@echo "Installing Reality Check skills to Claude Code..."
	@mkdir -p $(SKILLS_DIR)
	@for skill in $(CLAUDE_SKILLS); do \
		if [ -L "$(SKILLS_DIR)/$$skill" ]; then \
			rm "$(SKILLS_DIR)/$$skill"; \
		fi; \
		ln -s "$(CLAUDE_SKILLS_SRC)/$$skill" "$(SKILLS_DIR)/$$skill"; \
		echo "  Installed: $$skill"; \
	done
	@echo ""
	@echo "Skills installed to $(SKILLS_DIR)"
	@echo "Restart Claude Code and use /skills to see available skills."

uninstall-claude-skills:
	@echo "Removing Reality Check skills..."
	@for skill in $(CLAUDE_SKILLS); do \
		if [ -L "$(SKILLS_DIR)/$$skill" ]; then \
			rm "$(SKILLS_DIR)/$$skill"; \
			echo "  Removed: $$skill"; \
		fi; \
	done
	@echo "Skills removed."

# Codex skills installation
install-codex-skills:
	@echo "Installing Reality Check Codex skills..."
	@bash integrations/codex/install.sh

uninstall-codex-skills:
	@echo "Removing Reality Check Codex skills..."
	@bash integrations/codex/uninstall.sh

# Amp skills installation
install-amp-skills:
	@echo "Installing Reality Check Amp skills..."
	@bash integrations/amp/install.sh

uninstall-amp-skills:
	@echo "Removing Reality Check Amp skills..."
	@bash integrations/amp/uninstall.sh

# Testing
test:
	REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

test-all:
	uv run pytest -v

# Skill generation from templates
assemble-skills:
	@echo "Generating skills from templates..."
	@python integrations/assemble.py

check-skills:
	@echo "Checking if skills are up-to-date..."
	@python integrations/assemble.py --check

# Database
init:
	uv run python scripts/db.py init

# Cleanup
clean:
	rm -rf data/realitycheck.lance
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
