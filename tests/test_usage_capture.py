"""
Unit tests for scripts/usage_capture.py

Tests cover:
- Parsing token usage from local tool session logs (Claude Code, Codex, Amp)
- Optional time-window filtering
- Cost estimation from model pricing
"""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from usage_capture import (
    UsageTotals,
    estimate_cost_usd,
    parse_usage_from_source,
)


class TestClaudeCodeUsageParsing:
    def test_parse_claude_jsonl_sums_tokens(self, tmp_path: Path):
        log_path = tmp_path / "claude.jsonl"
        log_path.write_text(
            "\n".join(
                [
                    '{"timestamp":"2026-01-23T10:00:00Z","message":{"usage":{"input_tokens":100,"output_tokens":200,"cache_creation_input_tokens":10,"cache_read_input_tokens":5}}}',
                    '{"timestamp":"2026-01-23T10:05:00Z","message":{"usage":{"input_tokens":50,"output_tokens":100}}}',
                    "",
                ]
            )
        )

        totals = parse_usage_from_source("claude", log_path)
        assert isinstance(totals, UsageTotals)
        assert totals.tokens_in == 165
        assert totals.tokens_out == 300
        assert totals.total_tokens == 465

    def test_parse_claude_jsonl_window_filters(self, tmp_path: Path):
        log_path = tmp_path / "claude.jsonl"
        log_path.write_text(
            "\n".join(
                [
                    '{"timestamp":"2026-01-23T10:00:00Z","message":{"usage":{"input_tokens":100,"output_tokens":200}}}',
                    '{"timestamp":"2026-01-23T10:05:00Z","message":{"usage":{"input_tokens":50,"output_tokens":100}}}',
                    "",
                ]
            )
        )

        totals = parse_usage_from_source(
            "claude",
            log_path,
            window_start="2026-01-23T10:03:00Z",
            window_end="2026-01-23T10:06:00Z",
        )
        assert totals.tokens_in == 50
        assert totals.tokens_out == 100
        assert totals.total_tokens == 150


class TestAmpUsageParsing:
    def test_parse_amp_json_sums_tokens(self, tmp_path: Path):
        log_path = tmp_path / "amp.json"
        log_path.write_text(
            """
{
  "messages": [
    {
      "timestamp": "2026-01-23T10:00:00Z",
      "model": "claude-sonnet-4",
      "usage": {
        "inputTokens": 100,
        "cacheCreationInputTokens": 10,
        "cacheReadInputTokens": 5,
        "outputTokens": 200
      }
    },
    {
      "timestamp": "2026-01-23T10:05:00Z",
      "usage": {
        "inputTokens": 50,
        "outputTokens": 100
      }
    }
  ]
}
""".lstrip()
        )

        totals = parse_usage_from_source("amp", log_path)
        assert totals.tokens_in == 165
        assert totals.tokens_out == 300
        assert totals.total_tokens == 465


class TestCodexUsageParsing:
    def test_parse_codex_jsonl_uses_final_totals(self, tmp_path: Path):
        log_path = tmp_path / "codex.jsonl"
        log_path.write_text(
            "\n".join(
                [
                    '{"payload":{"info":{"total_token_usage":{"input_tokens":0,"cached_input_tokens":0,"output_tokens":0,"reasoning_output_tokens":0,"total_tokens":0}}}}',
                    '{"payload":{"info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":20,"output_tokens":200,"reasoning_output_tokens":30,"total_tokens":350}}}}',
                    "",
                ]
            )
        )

        totals = parse_usage_from_source("codex", log_path)
        assert totals.tokens_in == 120
        assert totals.tokens_out == 230
        assert totals.total_tokens == 350


class TestCostEstimation:
    def test_estimate_cost_usd_known_model(self):
        cost = estimate_cost_usd("gpt-4o", tokens_in=1_000_000, tokens_out=1_000_000)
        assert cost == pytest.approx(12.5, rel=1e-6)

    def test_estimate_cost_usd_unknown_model_returns_none(self):
        assert estimate_cost_usd("unknown-model", tokens_in=100, tokens_out=100) is None

