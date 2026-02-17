from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from scripts import release_stats_rollup as rollup


def _dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts).astimezone(UTC)


def test_parse_numstat_ignores_non_numeric_rows() -> None:
    output = "\n".join(
        [
            "10\t3\ta.py",
            "-\t-\tbinary.dat",
            "5\t0\tb.py",
            "not-a-row",
        ]
    )
    assert rollup.parse_numstat(output) == (15, 3)


def test_codex_tokens_in_window_uses_counter_delta() -> None:
    session = rollup.CodexSession(
        path=Path("/tmp/rollout.jsonl"),
        session_id="sess-1",
        cwd="/repo",
        model="gpt-5",
        snapshots=[
            rollup.TokenSnapshot(
                timestamp_utc=_dt("2026-01-01T00:00:00+00:00"),
                input_tokens=100,
                cached_input_tokens=20,
                output_tokens=50,
                total_tokens=150,
            ),
            rollup.TokenSnapshot(
                timestamp_utc=_dt("2026-01-01T00:10:00+00:00"),
                input_tokens=140,
                cached_input_tokens=30,
                output_tokens=80,
                total_tokens=220,
            ),
        ],
        event_timestamps=[
            _dt("2026-01-01T00:00:00+00:00"),
            _dt("2026-01-01T00:10:00+00:00"),
        ],
        coding_timestamps=[_dt("2026-01-01T00:10:00+00:00")],
    )

    delta = rollup.codex_tokens_in_window(
        session,
        start_exclusive=_dt("2026-01-01T00:05:00+00:00"),
        end_inclusive=_dt("2026-01-01T00:15:00+00:00"),
    )
    assert delta["input_tokens"] == 40
    assert delta["cached_input_tokens"] == 10
    assert delta["uncached_input_tokens"] == 30
    assert delta["output_tokens"] == 30
    assert delta["total_tokens"] == 70


def test_parse_claude_usage_line_includes_cache_tokens() -> None:
    obj = {
        "timestamp": "2026-01-02T00:00:00Z",
        "cwd": "/repo",
        "message": {
            "model": "claude-opus",
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 7,
                "output_tokens": 3,
            },
        },
    }
    event = rollup.parse_claude_usage_line(
        obj,
        repo_root=Path("/repo"),
        file_is_repo_scoped=False,
    )
    assert event is not None
    assert event.input_tokens == 10
    assert event.cache_creation_input_tokens == 5
    assert event.cache_read_input_tokens == 7
    assert event.tokens_in == 22
    assert event.tokens_out == 3
    assert event.total_tokens == 25
    assert event.is_tool_use is False


def test_activity_summary_splits_coding_and_planning() -> None:
    summary = rollup.activity_summary_from_points(
        all_points=[
            _dt("2026-01-01T00:01:00+00:00"),
            _dt("2026-01-01T00:02:00+00:00"),
            _dt("2026-01-01T00:12:00+00:00"),
        ],
        coding_points=[_dt("2026-01-01T00:02:00+00:00")],
        start_exclusive=_dt("2026-01-01T00:00:00+00:00"),
        end_inclusive=_dt("2026-01-01T00:30:00+00:00"),
        idle_threshold_seconds=300,
        min_burst_seconds=60,
    )
    assert summary["active_seconds"] > 0
    assert summary["coding_seconds"] > 0
    assert summary["planning_seconds"] >= 0


def test_render_markdown_includes_summary_row() -> None:
    payload = {
        "generated_at_utc": "2026-02-17T00:00:00+00:00",
        "repo_root": "/repo",
        "totals": {
            "commits": 3,
            "files_touched_sum": 4,
            "insertions": 10,
            "deletions": 2,
            "net_lines": 8,
            "tokens": {
                "codex": {"tokens_in": 20, "tokens_out": 10, "total_tokens": 30},
                "claude": {"tokens_in": 5, "tokens_out": 2, "total_tokens": 7},
                "combined": {"tokens_in": 25, "tokens_out": 12, "total_tokens": 37},
            },
            "activity_seconds": {
                "active": 120,
                "coding": 60,
                "planning": 60,
                "active_human": "2m",
                "coding_human": "1m",
                "planning_human": "1m",
            },
        },
        "releases": [
            {
                "tag": {
                    "name": "v0.1.0",
                    "commit_short": "abc1234",
                    "commit_time_utc": "2026-01-01T00:00:00+00:00",
                },
                "previous_tag": None,
                "timing": {
                    "cadence_since_prev_human": "-",
                    "cadence_since_prev_seconds": None,
                },
                "git": {
                    "range": "v0.1.0",
                    "commits_in_range": 3,
                    "unique_files_touched": 4,
                    "insertions": 10,
                    "deletions": 2,
                    "net_lines": 8,
                    "commits_to_tag": 3,
                    "first_commit_utc": "2026-01-01T00:00:00+00:00",
                    "last_commit_utc": "2026-01-01T01:00:00+00:00",
                    "span_days_inclusive": 1,
                    "work_duration_human": "1h",
                },
                "usage": {
                    "window": {
                        "start_exclusive_utc": None,
                        "end_inclusive_utc": "2026-01-01T00:00:00+00:00",
                    },
                    "codex": {
                        "sessions_with_usage": 1,
                        "files_with_usage": 1,
                        "tokens_in": 20,
                        "tokens_out": 10,
                        "total_tokens": 30,
                    },
                    "claude": {
                        "files_with_usage": 1,
                        "tokens_in": 5,
                        "tokens_out": 2,
                        "total_tokens": 7,
                    },
                    "combined": {
                        "tokens_in": 25,
                        "tokens_out": 12,
                        "total_tokens": 37,
                    },
                    "timing": {
                        "codex": {
                            "events": 1,
                            "wall_human": "1h",
                            "active_human": "1m",
                            "coding_human": "1m",
                            "planning_human": "0m",
                            "idle_human": "59m",
                            "active_ratio": 0.01,
                        },
                        "claude": {
                            "events": 1,
                            "wall_human": "1h",
                            "active_human": "1m",
                            "coding_human": "0m",
                            "planning_human": "1m",
                            "idle_human": "59m",
                            "active_ratio": 0.01,
                        },
                        "combined": {
                            "events": 2,
                            "wall_human": "1h",
                            "active_human": "2m",
                            "coding_human": "1m",
                            "planning_human": "1m",
                            "idle_human": "58m",
                            "active_ratio": 0.03,
                        },
                    },
                },
                "scc": {"skipped": True},
            }
        ],
    }
    markdown = rollup.render_markdown(payload)
    assert "## Project Totals" in markdown
    assert "## Summary Table" in markdown
    assert "`v0.1.0`" in markdown
    assert "Combined" in markdown
    assert "**TOTAL**" in markdown
