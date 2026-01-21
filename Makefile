# Reality Check Makefile

.PHONY: help install-plugin uninstall-plugin install-skills uninstall-skills install-codex-skills uninstall-codex-skills test test-all init clean

help:
	@echo "Reality Check - Available targets:"
	@echo ""
	@echo "  install-plugin    Install Claude Code plugin (symlink to ~/.claude/plugins/local/)"
	@echo "  uninstall-plugin  Remove Claude Code plugin"
	@echo "  install-skills    Install Claude Code skills (symlink to ~/.claude/skills/)"
	@echo "  uninstall-skills  Remove Claude Code skills"
	@echo "  install-codex-skills    Install Codex skills (symlink)"
	@echo "  uninstall-codex-skills  Remove Codex skills"
	@echo "  test              Run tests (skip embedding tests)"
	@echo "  test-all          Run all tests including embeddings"
	@echo "  init              Initialize database"
	@echo "  clean             Remove generated files"
	@echo ""

# Plugin installation
PLUGIN_DIR := $(HOME)/.claude/plugins/local
PLUGIN_NAME := realitycheck

install-plugin:
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
	@ln -s "$(CURDIR)/plugin" "$(PLUGIN_DIR)/$(PLUGIN_NAME)"
	@echo "Plugin installed: $(PLUGIN_DIR)/$(PLUGIN_NAME) -> $(CURDIR)/plugin"
	@echo ""
	@echo "Restart Claude Code to load the plugin."
	@echo "Available commands: /check, /realitycheck, /analyze, /extract, /search, /validate, /export"

uninstall-plugin:
	@echo "Removing Reality Check plugin..."
	@if [ -L "$(PLUGIN_DIR)/$(PLUGIN_NAME)" ]; then \
		rm "$(PLUGIN_DIR)/$(PLUGIN_NAME)"; \
		echo "Plugin removed."; \
	else \
		echo "Plugin symlink not found at $(PLUGIN_DIR)/$(PLUGIN_NAME)"; \
	fi

# Claude Code skills installation (global skills)
SKILLS_DIR := $(HOME)/.claude/skills
SKILLS := check analyze extract search validate export stats realitycheck

install-skills:
	@echo "Installing Reality Check skills to Claude Code..."
	@mkdir -p $(SKILLS_DIR)
	@for skill in $(SKILLS); do \
		if [ -L "$(SKILLS_DIR)/$$skill" ]; then \
			rm "$(SKILLS_DIR)/$$skill"; \
		fi; \
		ln -s "$(CURDIR)/plugin/skills/$$skill" "$(SKILLS_DIR)/$$skill"; \
		echo "  Installed: $$skill"; \
	done
	@echo ""
	@echo "Skills installed to $(SKILLS_DIR)"
	@echo "Restart Claude Code and use /skills to see available skills."

uninstall-skills:
	@echo "Removing Reality Check skills..."
	@for skill in $(SKILLS); do \
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

# Testing
test:
	REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

test-all:
	uv run pytest -v

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
