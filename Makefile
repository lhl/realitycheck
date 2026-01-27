# Reality Check Makefile

.PHONY: help test test-all init clean
.PHONY: assemble-skills check-skills
.PHONY: install-skills-all install-skills-amp install-skills-claude install-skills-codex install-skills-opencode
.PHONY: uninstall-skills-all uninstall-skills-amp uninstall-skills-claude uninstall-skills-codex uninstall-skills-opencode
.PHONY: install-plugin-claude uninstall-plugin-claude

help:
	@echo "Reality Check - Available targets:"
	@echo ""
	@echo "  Skills (install to each tool):"
	@echo "    install-skills-all       Install skills for all integrations"
	@echo "    install-skills-amp       Install Amp skills (~/.config/agents/skills/)"
	@echo "    install-skills-claude    Install Claude Code skills (~/.claude/skills/)"
	@echo "    install-skills-codex     Install Codex skills"
	@echo "    install-skills-opencode  Install OpenCode skills (~/.config/opencode/skills/)"
	@echo ""
	@echo "    uninstall-skills-all     Remove skills from all integrations"
	@echo "    uninstall-skills-amp     Remove Amp skills"
	@echo "    uninstall-skills-claude  Remove Claude Code skills"
	@echo "    uninstall-skills-codex   Remove Codex skills"
	@echo "    uninstall-skills-opencode Remove OpenCode skills"
	@echo ""
	@echo "  Plugin (Claude Code only):"
	@echo "    install-plugin-claude    Install Claude plugin (--plugin-dir)"
	@echo "    uninstall-plugin-claude  Remove Claude plugin"
	@echo ""
	@echo "  Development:"
	@echo "    assemble-skills          Generate skills from templates"
	@echo "    check-skills             Check if generated skills are up-to-date"
	@echo "    test                     Run tests (skip embedding tests)"
	@echo "    test-all                 Run all tests including embeddings"
	@echo "    init                     Initialize database (requires REALITYCHECK_DATA)"
	@echo "    clean                    Remove Python caches"
	@echo ""

# =============================================================================
# Skill Generation
# =============================================================================

assemble-skills:
	@echo "Generating skills from templates..."
	@uv run python integrations/assemble.py --docs

check-skills:
	@echo "Checking if skills are up-to-date..."
	@uv run python integrations/assemble.py --docs --check

# =============================================================================
# Skills Installation
# =============================================================================

# Install all
install-skills-all: install-skills-amp install-skills-claude install-skills-codex install-skills-opencode
	@echo ""
	@echo "All skills installed. Restart your tools to use them."

uninstall-skills-all: uninstall-skills-amp uninstall-skills-claude uninstall-skills-codex uninstall-skills-opencode
	@echo ""
	@echo "All skills removed."

# Amp
AMP_SKILLS_SRC := $(CURDIR)/integrations/amp/skills
AMP_SKILLS_DST := $(HOME)/.config/agents/skills
AMP_SKILLS := realitycheck-check realitycheck-synthesize realitycheck-analyze realitycheck-extract realitycheck-search realitycheck-validate realitycheck-export realitycheck-stats

install-skills-amp:
	@echo "Installing Reality Check skills for Amp..."
	@mkdir -p $(AMP_SKILLS_DST)
	@for skill in $(AMP_SKILLS); do \
		if [ -L "$(AMP_SKILLS_DST)/$$skill" ]; then rm "$(AMP_SKILLS_DST)/$$skill"; fi; \
		if [ -d "$(AMP_SKILLS_SRC)/$$skill" ]; then \
			ln -s "$(AMP_SKILLS_SRC)/$$skill" "$(AMP_SKILLS_DST)/$$skill"; \
			echo "  Installed: $$skill"; \
		fi; \
	done
	@echo "Skills installed to $(AMP_SKILLS_DST)"

uninstall-skills-amp:
	@echo "Removing Amp skills..."
	@for skill in $(AMP_SKILLS); do \
		if [ -L "$(AMP_SKILLS_DST)/$$skill" ]; then \
			rm "$(AMP_SKILLS_DST)/$$skill"; \
			echo "  Removed: $$skill"; \
		fi; \
	done

# Claude Code
CLAUDE_SKILLS_SRC := $(CURDIR)/integrations/claude/skills
CLAUDE_SKILLS_DST := $(HOME)/.claude/skills
CLAUDE_SKILLS := check synthesize analyze extract search validate export stats realitycheck

install-skills-claude:
	@echo "Installing Reality Check skills for Claude Code..."
	@mkdir -p $(CLAUDE_SKILLS_DST)
	@for skill in $(CLAUDE_SKILLS); do \
		if [ -L "$(CLAUDE_SKILLS_DST)/$$skill" ]; then rm "$(CLAUDE_SKILLS_DST)/$$skill"; fi; \
		if [ -d "$(CLAUDE_SKILLS_SRC)/$$skill" ]; then \
			ln -s "$(CLAUDE_SKILLS_SRC)/$$skill" "$(CLAUDE_SKILLS_DST)/$$skill"; \
			echo "  Installed: $$skill"; \
		fi; \
	done
	@echo "Skills installed to $(CLAUDE_SKILLS_DST)"
	@echo "Restart Claude Code and use /skills to see available skills."

uninstall-skills-claude:
	@echo "Removing Claude Code skills..."
	@for skill in $(CLAUDE_SKILLS); do \
		if [ -L "$(CLAUDE_SKILLS_DST)/$$skill" ]; then \
			rm "$(CLAUDE_SKILLS_DST)/$$skill"; \
			echo "  Removed: $$skill"; \
		fi; \
	done

# Codex
install-skills-codex:
	@echo "Installing Reality Check skills for Codex..."
	@bash integrations/codex/install.sh

uninstall-skills-codex:
	@echo "Removing Codex skills..."
	@bash integrations/codex/uninstall.sh

# OpenCode
OPENCODE_SKILLS_SRC := $(CURDIR)/integrations/opencode/skills
OPENCODE_SKILLS_DST := $(HOME)/.config/opencode/skills
OPENCODE_SKILLS := realitycheck realitycheck-check realitycheck-synthesize realitycheck-analyze realitycheck-extract realitycheck-search realitycheck-validate realitycheck-export realitycheck-stats

install-skills-opencode:
	@echo "Installing Reality Check skills for OpenCode..."
	@mkdir -p $(OPENCODE_SKILLS_DST)
	@for skill in $(OPENCODE_SKILLS); do \
		if [ -L "$(OPENCODE_SKILLS_DST)/$$skill" ]; then rm "$(OPENCODE_SKILLS_DST)/$$skill"; fi; \
		if [ -d "$(OPENCODE_SKILLS_SRC)/$$skill" ]; then \
			ln -s "$(OPENCODE_SKILLS_SRC)/$$skill" "$(OPENCODE_SKILLS_DST)/$$skill"; \
			echo "  Installed: $$skill"; \
		fi; \
	done
	@echo "Skills installed to $(OPENCODE_SKILLS_DST)"
	@echo "Restart OpenCode to use them."

uninstall-skills-opencode:
	@echo "Removing OpenCode skills..."
	@for skill in $(OPENCODE_SKILLS); do \
		if [ -L "$(OPENCODE_SKILLS_DST)/$$skill" ]; then \
			rm "$(OPENCODE_SKILLS_DST)/$$skill"; \
			echo "  Removed: $$skill"; \
		fi; \
	done

# =============================================================================
# Claude Plugin (separate from skills)
# =============================================================================

CLAUDE_PLUGIN_SRC := $(CURDIR)/integrations/claude/plugin
CLAUDE_PLUGIN_DST := $(HOME)/.claude/plugins/local
PLUGIN_NAME := reality

install-plugin-claude:
	@echo "Installing Reality Check plugin for Claude Code..."
	@mkdir -p $(CLAUDE_PLUGIN_DST)
	@if [ -L "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)" ]; then \
		rm "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)"; \
	elif [ -d "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)" ]; then \
		echo "Warning: $(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME) exists as directory"; \
		echo "Remove it manually to use symlink install"; \
		exit 1; \
	fi
	@ln -s "$(CLAUDE_PLUGIN_SRC)" "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)"
	@echo "Plugin installed: $(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)"
	@echo ""
	@echo "NOTE: Local plugin discovery may be broken in Claude Code."
	@echo "Use the --plugin-dir flag instead:"
	@echo ""
	@echo "  claude --plugin-dir $(CLAUDE_PLUGIN_SRC)"

uninstall-plugin-claude:
	@echo "Removing Claude Code plugin..."
	@if [ -L "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)" ]; then \
		rm "$(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)"; \
		echo "Plugin removed."; \
	else \
		echo "Plugin not found at $(CLAUDE_PLUGIN_DST)/$(PLUGIN_NAME)"; \
	fi

# =============================================================================
# Development
# =============================================================================

test:
	REALITYCHECK_EMBED_SKIP=1 uv run pytest -v

test-all:
	uv run pytest -v

init:
	@if [ -z "$(REALITYCHECK_DATA)" ]; then \
		echo "ERROR: REALITYCHECK_DATA not set."; \
		echo ""; \
		echo "This target creates a database for actual analysis data."; \
		echo "Set REALITYCHECK_DATA to your data repository path:"; \
		echo ""; \
		echo "  export REALITYCHECK_DATA=/path/to/realitycheck-data"; \
		echo "  make init"; \
		echo ""; \
		echo "For development/testing, use:"; \
		echo "  REALITYCHECK_DATA=./data make init"; \
		exit 1; \
	fi
	uv run python scripts/db.py init

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
