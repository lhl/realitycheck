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


# =============================================================================
# Session Detection Tests (Phase 1 of token-usage implementation)
# =============================================================================

class TestSessionDetection:
    """Tests for session auto-detection and token counting."""

    def test_get_current_session_path_claude_single(self, tmp_path: Path):
        """When exactly one Claude session exists, return it."""
        from usage_capture import get_current_session_path

        # Create mock Claude session structure
        project_sessions = tmp_path / ".claude" / "projects" / "test-project"
        project_sessions.mkdir(parents=True)
        session_file = project_sessions / "abc12345-1234-5678-9abc-def012345678.jsonl"
        session_file.write_text('{"timestamp":"2026-01-25T10:00:00Z","message":{"usage":{"input_tokens":100}}}\n')

        path, uuid = get_current_session_path("claude", project_path=tmp_path)
        assert path == session_file
        assert uuid == "abc12345-1234-5678-9abc-def012345678"

    def test_get_current_session_path_claude_ambiguous(self, tmp_path: Path):
        """When multiple Claude sessions exist, raise AmbiguousSessionError."""
        from usage_capture import get_current_session_path, AmbiguousSessionError

        project_sessions = tmp_path / ".claude" / "projects" / "test-project"
        project_sessions.mkdir(parents=True)

        # Create two session files
        (project_sessions / "abc12345-1234-5678-9abc-def012345678.jsonl").write_text('{"message":{}}\n')
        (project_sessions / "def67890-1234-5678-9abc-def012345678.jsonl").write_text('{"message":{}}\n')

        with pytest.raises(AmbiguousSessionError) as exc_info:
            get_current_session_path("claude", project_path=tmp_path)

        # Error should include candidate list with context
        assert "abc12345" in str(exc_info.value) or "def67890" in str(exc_info.value)

    def test_get_current_session_path_no_session(self, tmp_path: Path):
        """When no sessions exist, raise NoSessionFoundError."""
        from usage_capture import get_current_session_path, NoSessionFoundError

        with pytest.raises(NoSessionFoundError):
            get_current_session_path("claude", project_path=tmp_path)

    def test_get_current_session_path_codex(self, tmp_path: Path):
        """Find Codex session file."""
        from usage_capture import get_current_session_path

        codex_sessions = tmp_path / ".codex" / "sessions" / "2026" / "01" / "25"
        codex_sessions.mkdir(parents=True)
        session_file = codex_sessions / "rollout-1737820800-abc12345-1234-5678-9abc-def012345678.jsonl"
        session_file.write_text('{"payload":{"info":{}}}\n')

        path, uuid = get_current_session_path("codex", project_path=tmp_path)
        assert path == session_file
        assert uuid == "abc12345-1234-5678-9abc-def012345678"

    def test_get_current_session_path_amp(self, tmp_path: Path):
        """Find Amp session file."""
        from usage_capture import get_current_session_path

        amp_threads = tmp_path / ".local" / "share" / "amp" / "threads"
        amp_threads.mkdir(parents=True)
        session_file = amp_threads / "T-abc12345-1234-5678-9abc-def012345678.json"
        session_file.write_text('{"messages":[]}\n')

        path, uuid = get_current_session_path("amp", project_path=tmp_path)
        assert path == session_file
        assert uuid == "abc12345-1234-5678-9abc-def012345678"


class TestSessionTokenCount:
    """Tests for computing cumulative token counts from sessions."""

    def test_get_session_token_count_claude(self, tmp_path: Path):
        """Sum all per-message usage for Claude sessions."""
        from usage_capture import get_session_token_count

        session_file = tmp_path / "session.jsonl"
        session_file.write_text(
            "\n".join([
                '{"message":{"usage":{"input_tokens":100,"output_tokens":200}}}',
                '{"message":{"usage":{"input_tokens":50,"output_tokens":100}}}',
                "",
            ])
        )

        count = get_session_token_count(session_file, "claude")
        assert count == 450  # 100+200+50+100

    def test_get_session_token_count_codex(self, tmp_path: Path):
        """Use final total_token_usage counter for Codex."""
        from usage_capture import get_session_token_count

        session_file = tmp_path / "rollout.jsonl"
        session_file.write_text(
            "\n".join([
                '{"payload":{"info":{"total_token_usage":{"total_tokens":100}}}}',
                '{"payload":{"info":{"total_token_usage":{"total_tokens":350}}}}',
                "",
            ])
        )

        count = get_session_token_count(session_file, "codex")
        assert count == 350  # Final counter value

    def test_get_session_token_count_codex_multi_rollout(self, tmp_path: Path):
        """Aggregate across multiple rollout files for same UUID."""
        from usage_capture import get_session_token_count_by_uuid

        codex_sessions = tmp_path / ".codex" / "sessions" / "2026" / "01" / "25"
        codex_sessions.mkdir(parents=True)

        uuid = "abc12345-1234-5678-9abc-def012345678"

        # First rollout file
        (codex_sessions / f"rollout-1737820800-{uuid}.jsonl").write_text(
            '{"payload":{"info":{"total_token_usage":{"total_tokens":200}}}}\n'
        )
        # Second rollout file (resumed session)
        (codex_sessions / f"rollout-1737824400-{uuid}.jsonl").write_text(
            '{"payload":{"info":{"total_token_usage":{"total_tokens":150}}}}\n'
        )

        count = get_session_token_count_by_uuid(uuid, "codex", base_path=tmp_path)
        assert count == 350  # Aggregated: 200 + 150

    def test_get_session_token_count_amp(self, tmp_path: Path):
        """Sum all per-message usage for Amp sessions."""
        from usage_capture import get_session_token_count

        session_file = tmp_path / "thread.json"
        session_file.write_text(
            """
{
  "messages": [
    {"usage": {"inputTokens": 100, "outputTokens": 200}},
    {"usage": {"inputTokens": 50, "outputTokens": 100}}
  ]
}
""".strip()
        )

        count = get_session_token_count(session_file, "amp")
        assert count == 450  # 100+200+50+100


class TestListSessions:
    """Tests for session listing/discovery."""

    def test_list_sessions_returns_candidates(self, tmp_path: Path):
        """List sessions with metadata for discovery."""
        from usage_capture import list_sessions

        project_sessions = tmp_path / ".claude" / "projects" / "test-project"
        project_sessions.mkdir(parents=True)

        # Create session with some content
        session_file = project_sessions / "abc12345-1234-5678-9abc-def012345678.jsonl"
        session_file.write_text(
            '{"timestamp":"2026-01-25T10:00:00Z","message":{"content":"Hello","usage":{"input_tokens":100,"output_tokens":50}}}\n'
        )

        sessions = list_sessions("claude", limit=10, base_path=tmp_path)

        assert len(sessions) == 1
        assert sessions[0]["uuid"] == "abc12345-1234-5678-9abc-def012345678"
        assert sessions[0]["path"] == session_file
        assert "last_modified" in sessions[0]
        assert sessions[0]["tokens_so_far"] == 150
        # Should include context snippet
        assert "context_snippet" in sessions[0]

