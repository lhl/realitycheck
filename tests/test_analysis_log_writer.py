"""
Unit tests for scripts/analysis_log_writer.py

Tests cover:
- Inserting the Analysis Log section when missing
- Upserting rows by pass number (idempotent updates)
"""

from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from analysis_log_writer import upsert_analysis_log_section


class TestAnalysisLogWriter:
    def test_upsert_inserts_section_when_missing(self):
        content = "# Source Analysis: Test\n\nSome content.\n"
        updated = upsert_analysis_log_section(
            content,
            {
                "pass": 1,
                "tool": "codex",
                "model": "gpt-4o",
                "started_at": "2026-01-23T10:00:00Z",
                "duration_seconds": 480,
                "total_tokens": 3700,
                "cost_usd": 0.08,
                "notes": "Initial analysis",
            },
        )

        assert "## Analysis Log" in updated
        assert "| Pass | Date | Tool | Model | Duration | Tokens | Cost | Notes |" in updated
        assert "| 1 | 2026-01-23 10:00 | codex | gpt-4o |" in updated

    def test_upsert_replaces_existing_pass_row(self):
        content = """
# Source Analysis: Test

---

## Analysis Log

| Pass | Date | Tool | Model | Duration | Tokens | Cost | Notes |
|------|------|------|-------|----------|--------|------|-------|
| 1 | YYYY-MM-DD HH:MM | codex | gpt-5.2 | 8m | ? | ? | Initial 3-stage analysis |

### Revision Notes

**Pass 1**: placeholder
""".lstrip()

        updated = upsert_analysis_log_section(
            content,
            {
                "pass": 1,
                "tool": "codex",
                "model": "gpt-4o",
                "started_at": "2026-01-23T10:00:00Z",
                "duration_seconds": 480,
                "total_tokens": 3700,
                "cost_usd": 0.08,
                "notes": "Initial analysis",
            },
        )

        assert "YYYY-MM-DD HH:MM" not in updated
        assert "| 1 | 2026-01-23 10:00 | codex | gpt-4o | 8m0s | 3,700 | $0.0800 | Initial analysis |" in updated
        assert "**Pass 1**: Initial analysis" in updated

