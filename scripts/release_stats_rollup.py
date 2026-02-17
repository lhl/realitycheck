#!/usr/bin/env python3
"""Generate per-tag development stats for Reality Check releases."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import tempfile
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None


@dataclass(frozen=True)
class TagInfo:
    name: str
    commit: str
    commit_short: str
    commit_time_utc: datetime
    tag_time_utc: datetime


@dataclass(frozen=True)
class TokenSnapshot:
    timestamp_utc: datetime
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CodexSession:
    path: Path
    session_id: str | None
    cwd: str | None
    model: str | None
    snapshots: list[TokenSnapshot]
    event_timestamps: list[datetime]
    coding_timestamps: list[datetime]


@dataclass(frozen=True)
class ClaudeUsageEvent:
    path: Path
    timestamp_utc: datetime
    model: str | None
    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    tokens_in: int
    tokens_out: int
    total_tokens: int
    is_tool_use: bool


DEFAULT_GPT5_INPUT_USD_PER_1M = 1.25
DEFAULT_GPT5_CACHED_INPUT_USD_PER_1M = 0.125
DEFAULT_GPT5_OUTPUT_USD_PER_1M = 10.00
DEFAULT_OPUS4_INPUT_USD_PER_1M = 15.00
DEFAULT_OPUS4_CACHE_WRITE_USD_PER_1M = 18.75
DEFAULT_OPUS4_CACHE_READ_USD_PER_1M = 1.50
DEFAULT_OPUS4_OUTPUT_USD_PER_1M = 75.00


def run_command(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_timestamp_utc(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)


def parse_numstat(output: str) -> tuple[int, int]:
    insertions = 0
    deletions = 0
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        added, removed = parts[0].strip(), parts[1].strip()
        if not added.isdigit() or not removed.isdigit():
            continue
        insertions += int(added)
        deletions += int(removed)
    return insertions, deletions


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def path_matches_repo(cwd: str | None, repo_root: Path) -> bool:
    if not cwd:
        return False
    try:
        cwd_path = Path(cwd).expanduser().resolve()
    except Exception:
        return False
    repo_resolved = repo_root.resolve()
    return cwd_path == repo_resolved or repo_resolved in cwd_path.parents


def list_tags(repo_root: Path) -> list[TagInfo]:
    names = [line.strip() for line in run_command(["git", "tag", "--sort=creatordate"], cwd=repo_root).splitlines() if line.strip()]
    tags: list[TagInfo] = []
    for name in names:
        commit = run_command(["git", "rev-parse", f"{name}^{{commit}}"], cwd=repo_root).strip()
        commit_short = run_command(["git", "rev-parse", "--short", f"{name}^{{commit}}"], cwd=repo_root).strip()
        commit_time_raw = run_command(["git", "show", "-s", "--format=%cI", f"{name}^{{commit}}"], cwd=repo_root).strip()
        tag_time_raw = run_command(
            ["git", "for-each-ref", f"refs/tags/{name}", "--format=%(creatordate:iso8601-strict)"],
            cwd=repo_root,
        ).strip()
        commit_time = parse_timestamp_utc(commit_time_raw)
        tag_time = parse_timestamp_utc(tag_time_raw) if tag_time_raw else commit_time
        tags.append(
            TagInfo(
                name=name,
                commit=commit,
                commit_short=commit_short,
                commit_time_utc=commit_time,
                tag_time_utc=tag_time,
            )
        )
    return tags


def git_range_arg(previous_tag: str | None, current_tag: str) -> str:
    return f"{previous_tag}..{current_tag}" if previous_tag else current_tag


def collect_git_range_stats(repo_root: Path, previous_tag: str | None, current_tag: str) -> dict[str, Any]:
    range_arg = git_range_arg(previous_tag, current_tag)
    commits_in_range = int(run_command(["git", "rev-list", "--count", range_arg], cwd=repo_root).strip() or "0")
    commits_to_tag = int(run_command(["git", "rev-list", "--count", current_tag], cwd=repo_root).strip() or "0")

    files_output = run_command(["git", "log", "--name-only", "--pretty=format:", range_arg], cwd=repo_root)
    unique_files = {line.strip() for line in files_output.splitlines() if line.strip()}

    numstat_output = run_command(["git", "log", "--pretty=tformat:", "--numstat", range_arg], cwd=repo_root)
    insertions, deletions = parse_numstat(numstat_output)

    commit_times_output = run_command(["git", "log", "--reverse", "--format=%cI", range_arg], cwd=repo_root)
    commit_times = [parse_timestamp_utc(line.strip()) for line in commit_times_output.splitlines() if line.strip()]
    first_commit = commit_times[0] if commit_times else None
    last_commit = commit_times[-1] if commit_times else None
    span_days = (last_commit.date() - first_commit.date()).days + 1 if first_commit and last_commit else 0
    work_duration_seconds = duration_seconds(first_commit, last_commit)
    commit_dates_output = run_command(["git", "log", "--date=short", "--format=%cd", range_arg], cwd=repo_root)
    day_counter = Counter(line.strip() for line in commit_dates_output.splitlines() if line.strip())
    commits_by_day = dict(sorted(day_counter.items(), key=lambda row: row[0]))
    peak_day = max(commits_by_day.items(), key=lambda row: row[1]) if commits_by_day else None
    commits_per_day_avg = (commits_in_range / span_days) if span_days > 0 else None
    commits_per_hour_active = (
        commits_in_range / (work_duration_seconds / 3600.0)
        if work_duration_seconds and work_duration_seconds > 0
        else None
    )

    return {
        "range": range_arg,
        "commits_in_range": commits_in_range,
        "commits_to_tag": commits_to_tag,
        "unique_files_touched": len(unique_files),
        "insertions": insertions,
        "deletions": deletions,
        "net_lines": insertions - deletions,
        "first_commit_utc": first_commit.isoformat() if first_commit else None,
        "last_commit_utc": last_commit.isoformat() if last_commit else None,
        "span_days_inclusive": span_days,
        "work_duration_seconds": work_duration_seconds,
        "work_duration_human": fmt_duration(work_duration_seconds),
        "commits_by_day": commits_by_day,
        "peak_commit_day": {"date": peak_day[0], "commits": peak_day[1]} if peak_day else None,
        "commits_per_day_avg": round(commits_per_day_avg, 2) if commits_per_day_avg is not None else None,
        "commits_per_hour_active_span": (
            round(commits_per_hour_active, 2) if commits_per_hour_active is not None else None
        ),
    }


def parse_codex_session(path: Path) -> CodexSession | None:
    cwd: str | None = None
    session_id: str | None = None
    model: str | None = None
    snapshots: list[TokenSnapshot] = []
    event_timestamps: list[datetime] = []
    coding_timestamps: list[datetime] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                obj_type = obj.get("type")
                payload = obj.get("payload")
                payload_dict = payload if isinstance(payload, dict) else {}
                ts_raw = obj.get("timestamp")
                ts: datetime | None = None
                if isinstance(ts_raw, str):
                    ts = parse_timestamp_utc(ts_raw)
                    event_timestamps.append(ts)

                if obj_type == "session_meta":
                    if session_id is None and isinstance(payload_dict.get("id"), str):
                        session_id = payload_dict.get("id")
                    if cwd is None and isinstance(payload_dict.get("cwd"), str):
                        cwd = payload_dict.get("cwd")

                if obj_type == "turn_context":
                    if cwd is None and isinstance(payload_dict.get("cwd"), str):
                        cwd = payload_dict.get("cwd")
                    if model is None and isinstance(payload_dict.get("model"), str):
                        model = payload_dict.get("model")

                if obj_type == "response_item" and ts is not None:
                    if payload_dict.get("type") == "function_call":
                        coding_timestamps.append(ts)

                if obj_type != "event_msg":
                    continue
                if payload_dict.get("type") != "token_count":
                    continue
                info = payload_dict.get("info")
                info_dict = info if isinstance(info, dict) else {}
                usage = info_dict.get("total_token_usage")
                usage_dict = usage if isinstance(usage, dict) else {}

                if ts is None:
                    continue
                input_tokens = safe_int(usage_dict.get("input_tokens"))
                cached_input_tokens = safe_int(usage_dict.get("cached_input_tokens"))
                output_tokens = safe_int(usage_dict.get("output_tokens"))
                total_tokens = safe_int(usage_dict.get("total_tokens")) or (input_tokens + output_tokens)
                snapshots.append(
                    TokenSnapshot(
                        timestamp_utc=ts,
                        input_tokens=input_tokens,
                        cached_input_tokens=cached_input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                    )
                )
    except OSError:
        return None

    if not snapshots:
        return None
    snapshots.sort(key=lambda row: row.timestamp_utc)
    return CodexSession(
        path=path,
        session_id=session_id,
        cwd=cwd,
        model=model,
        snapshots=snapshots,
        event_timestamps=sorted(event_timestamps),
        coding_timestamps=sorted(coding_timestamps),
    )


def codex_tokens_in_window(
    session: CodexSession,
    *,
    start_exclusive: datetime | None,
    end_inclusive: datetime,
) -> dict[str, int]:
    snapshots = session.snapshots
    if not snapshots:
        return {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "uncached_input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    timestamps = [row.timestamp_utc for row in snapshots]
    end_idx = bisect_right(timestamps, end_inclusive) - 1
    if end_idx < 0:
        return {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "uncached_input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
    final = snapshots[end_idx]
    if start_exclusive is not None and final.timestamp_utc <= start_exclusive:
        return {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "uncached_input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    base_in = 0
    base_cached = 0
    base_out = 0
    base_total = 0
    if start_exclusive is not None:
        base_idx = bisect_right(timestamps, start_exclusive) - 1
        if base_idx >= 0:
            baseline = snapshots[base_idx]
            base_in = baseline.input_tokens
            base_cached = baseline.cached_input_tokens
            base_out = baseline.output_tokens
            base_total = baseline.total_tokens

    tokens_in = max(0, final.input_tokens - base_in)
    cached_in = max(0, final.cached_input_tokens - base_cached)
    tokens_out = max(0, final.output_tokens - base_out)
    total_tokens = max(0, final.total_tokens - base_total)
    if total_tokens == 0 and (tokens_in > 0 or tokens_out > 0):
        total_tokens = tokens_in + tokens_out
    uncached_in = max(0, tokens_in - cached_in)
    return {
        "input_tokens": tokens_in,
        "cached_input_tokens": cached_in,
        "uncached_input_tokens": uncached_in,
        "output_tokens": tokens_out,
        "total_tokens": total_tokens,
    }


def load_codex_sessions(codex_root: Path, repo_root: Path) -> list[CodexSession]:
    sessions: list[CodexSession] = []
    for path in sorted(codex_root.rglob("rollout-*.jsonl")):
        session = parse_codex_session(path)
        if session is None:
            continue
        if not path_matches_repo(session.cwd, repo_root):
            continue
        sessions.append(session)
    return sessions


def parse_claude_usage_line(
    obj: dict[str, Any],
    *,
    repo_root: Path,
    file_is_repo_scoped: bool,
) -> ClaudeUsageEvent | None:
    ts_raw = obj.get("timestamp")
    if not isinstance(ts_raw, str):
        return None
    timestamp_utc = parse_timestamp_utc(ts_raw)

    cwd = obj.get("cwd")
    if cwd is not None and not isinstance(cwd, str):
        return None
    if isinstance(cwd, str):
        if not path_matches_repo(cwd, repo_root):
            return None
    elif not file_is_repo_scoped:
        return None

    usage_dict: dict[str, Any] | None = None
    model: str | None = None
    is_tool_use = False
    message = obj.get("message")
    if isinstance(message, dict):
        usage = message.get("usage")
        if isinstance(usage, dict):
            usage_dict = usage
        if isinstance(message.get("model"), str):
            model = message.get("model")
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    is_tool_use = True
                    break
    if usage_dict is None:
        usage = obj.get("usage")
        if isinstance(usage, dict):
            usage_dict = usage
    if usage_dict is None:
        return None

    input_tokens = safe_int(usage_dict.get("input_tokens") or usage_dict.get("inputTokens"))
    output_tokens = safe_int(usage_dict.get("output_tokens") or usage_dict.get("outputTokens"))
    cache_creation_tokens = safe_int(
        usage_dict.get("cache_creation_input_tokens") or usage_dict.get("cacheCreationInputTokens")
    )
    cache_read_tokens = safe_int(
        usage_dict.get("cache_read_input_tokens") or usage_dict.get("cacheReadInputTokens")
    )
    tokens_in = input_tokens + cache_creation_tokens + cache_read_tokens
    tokens_out = output_tokens
    total_tokens = tokens_in + tokens_out
    return ClaudeUsageEvent(
        path=Path(),
        timestamp_utc=timestamp_utc,
        model=model,
        input_tokens=input_tokens,
        cache_creation_input_tokens=cache_creation_tokens,
        cache_read_input_tokens=cache_read_tokens,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        total_tokens=total_tokens,
        is_tool_use=is_tool_use,
    )


def load_claude_events(claude_projects_root: Path, repo_root: Path) -> list[ClaudeUsageEvent]:
    encoded_repo = "-" + str(repo_root.resolve()).strip("/").replace("/", "-")
    preferred_dir = claude_projects_root / encoded_repo
    if preferred_dir.exists():
        candidate_files = sorted(preferred_dir.rglob("*.jsonl"))
    else:
        candidate_files = sorted(claude_projects_root.rglob("*.jsonl"))

    events: list[ClaudeUsageEvent] = []
    for path in candidate_files:
        file_is_repo_scoped = preferred_dir.exists() and preferred_dir in path.parents
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    event = parse_claude_usage_line(
                        obj,
                        repo_root=repo_root,
                        file_is_repo_scoped=file_is_repo_scoped,
                    )
                    if event is None:
                        continue
                    events.append(
                        ClaudeUsageEvent(
                            path=path,
                            timestamp_utc=event.timestamp_utc,
                            model=event.model,
                            input_tokens=event.input_tokens,
                            cache_creation_input_tokens=event.cache_creation_input_tokens,
                            cache_read_input_tokens=event.cache_read_input_tokens,
                            tokens_in=event.tokens_in,
                            tokens_out=event.tokens_out,
                            total_tokens=event.total_tokens,
                            is_tool_use=event.is_tool_use,
                        )
                    )
        except OSError:
            continue
    events.sort(key=lambda row: row.timestamp_utc)
    return events


def _filter_window_timestamps(
    timestamps: list[datetime],
    *,
    start_exclusive: datetime | None,
    end_inclusive: datetime,
) -> list[datetime]:
    return [
        ts
        for ts in timestamps
        if (start_exclusive is None or ts > start_exclusive) and ts <= end_inclusive
    ]


def estimate_active_seconds_from_points(
    timestamps: list[datetime],
    *,
    idle_threshold_seconds: int,
    min_burst_seconds: int,
) -> int:
    if not timestamps:
        return 0
    points = sorted(timestamps)
    threshold = max(0, idle_threshold_seconds)
    min_burst = max(0, min_burst_seconds)

    active = 0
    burst_start = points[0]
    prev = points[0]
    for ts in points[1:]:
        gap = int((ts - prev).total_seconds())
        if gap <= threshold:
            prev = ts
            continue
        burst_seconds = int((prev - burst_start).total_seconds())
        active += max(min_burst, burst_seconds)
        burst_start = ts
        prev = ts
    burst_seconds = int((prev - burst_start).total_seconds())
    active += max(min_burst, burst_seconds)
    return active


def activity_summary_from_points(
    *,
    all_points: list[datetime],
    coding_points: list[datetime],
    start_exclusive: datetime | None,
    end_inclusive: datetime,
    idle_threshold_seconds: int,
    min_burst_seconds: int,
) -> dict[str, Any]:
    filtered_all = _filter_window_timestamps(
        all_points,
        start_exclusive=start_exclusive,
        end_inclusive=end_inclusive,
    )
    filtered_coding = _filter_window_timestamps(
        coding_points,
        start_exclusive=start_exclusive,
        end_inclusive=end_inclusive,
    )
    wall_start = start_exclusive if start_exclusive is not None else (filtered_all[0] if filtered_all else None)
    wall_seconds = duration_seconds(wall_start, end_inclusive) if wall_start is not None else 0
    active_seconds = estimate_active_seconds_from_points(
        filtered_all,
        idle_threshold_seconds=idle_threshold_seconds,
        min_burst_seconds=min_burst_seconds,
    )
    coding_seconds = estimate_active_seconds_from_points(
        filtered_coding,
        idle_threshold_seconds=idle_threshold_seconds,
        min_burst_seconds=min_burst_seconds,
    )
    if wall_seconds is None:
        wall_seconds = 0
    active_seconds = min(active_seconds, wall_seconds)
    coding_seconds = min(coding_seconds, active_seconds)
    planning_seconds = max(0, active_seconds - coding_seconds)
    idle_seconds = max(0, wall_seconds - active_seconds)
    active_ratio = round((active_seconds / wall_seconds), 4) if wall_seconds else None
    return {
        "events": len(filtered_all),
        "coding_events": len(filtered_coding),
        "wall_seconds": wall_seconds,
        "active_seconds": active_seconds,
        "coding_seconds": coding_seconds,
        "planning_seconds": planning_seconds,
        "idle_seconds": idle_seconds,
        "active_ratio": active_ratio,
        "wall_human": fmt_duration(wall_seconds),
        "active_human": fmt_duration(active_seconds),
        "coding_human": fmt_duration(coding_seconds),
        "planning_human": fmt_duration(planning_seconds),
        "idle_human": fmt_duration(idle_seconds),
    }


def aggregate_usage_for_window(
    *,
    codex_sessions: list[CodexSession],
    claude_events: list[ClaudeUsageEvent],
    start_exclusive: datetime | None,
    end_inclusive: datetime,
    idle_threshold_seconds: int = 300,
    min_burst_seconds: int = 60,
    codex_price_in_per_1m: float = DEFAULT_GPT5_INPUT_USD_PER_1M,
    codex_price_cached_input_per_1m: float = DEFAULT_GPT5_CACHED_INPUT_USD_PER_1M,
    codex_price_out_per_1m: float = DEFAULT_GPT5_OUTPUT_USD_PER_1M,
    claude_price_in_per_1m: float = DEFAULT_OPUS4_INPUT_USD_PER_1M,
    claude_price_cache_write_per_1m: float = DEFAULT_OPUS4_CACHE_WRITE_USD_PER_1M,
    claude_price_cache_read_per_1m: float = DEFAULT_OPUS4_CACHE_READ_USD_PER_1M,
    claude_price_out_per_1m: float = DEFAULT_OPUS4_OUTPUT_USD_PER_1M,
) -> dict[str, Any]:
    codex_in = 0
    codex_cached_in = 0
    codex_uncached_in = 0
    codex_out = 0
    codex_total = 0
    codex_sessions_with_usage: set[str] = set()
    codex_files_with_usage = 0
    codex_model_totals: dict[str, int] = {}
    codex_all_points: list[datetime] = []
    codex_coding_points: list[datetime] = []

    for session in codex_sessions:
        delta = codex_tokens_in_window(
            session,
            start_exclusive=start_exclusive,
            end_inclusive=end_inclusive,
        )
        codex_all_points.extend(
            _filter_window_timestamps(
                session.event_timestamps,
                start_exclusive=start_exclusive,
                end_inclusive=end_inclusive,
            )
        )
        codex_coding_points.extend(
            _filter_window_timestamps(
                session.coding_timestamps,
                start_exclusive=start_exclusive,
                end_inclusive=end_inclusive,
            )
        )
        if safe_int(delta.get("total_tokens")) <= 0:
            continue
        codex_in += safe_int(delta.get("input_tokens"))
        codex_cached_in += safe_int(delta.get("cached_input_tokens"))
        codex_uncached_in += safe_int(delta.get("uncached_input_tokens"))
        codex_out += safe_int(delta.get("output_tokens"))
        codex_total += safe_int(delta.get("total_tokens"))
        codex_files_with_usage += 1
        codex_sessions_with_usage.add(session.session_id or str(session.path))
        model_key = session.model or "unknown"
        codex_model_totals[model_key] = codex_model_totals.get(model_key, 0) + safe_int(delta.get("total_tokens"))

    claude_in = 0
    claude_base_in = 0
    claude_cache_write_in = 0
    claude_cache_read_in = 0
    claude_out = 0
    claude_total = 0
    claude_files_with_usage: set[str] = set()
    claude_model_totals: dict[str, int] = {}
    claude_all_points: list[datetime] = []
    claude_coding_points: list[datetime] = []
    for event in claude_events:
        if start_exclusive is not None and event.timestamp_utc <= start_exclusive:
            continue
        if event.timestamp_utc > end_inclusive:
            continue
        claude_all_points.append(event.timestamp_utc)
        if event.is_tool_use:
            claude_coding_points.append(event.timestamp_utc)
        claude_base_in += event.input_tokens
        claude_cache_write_in += event.cache_creation_input_tokens
        claude_cache_read_in += event.cache_read_input_tokens
        claude_in += event.tokens_in
        claude_out += event.tokens_out
        claude_total += event.total_tokens
        claude_files_with_usage.add(str(event.path))
        model_key = event.model or "unknown"
        claude_model_totals[model_key] = claude_model_totals.get(model_key, 0) + event.total_tokens

    codex_timing = activity_summary_from_points(
        all_points=codex_all_points,
        coding_points=codex_coding_points,
        start_exclusive=start_exclusive,
        end_inclusive=end_inclusive,
        idle_threshold_seconds=idle_threshold_seconds,
        min_burst_seconds=min_burst_seconds,
    )
    claude_timing = activity_summary_from_points(
        all_points=claude_all_points,
        coding_points=claude_coding_points,
        start_exclusive=start_exclusive,
        end_inclusive=end_inclusive,
        idle_threshold_seconds=idle_threshold_seconds,
        min_burst_seconds=min_burst_seconds,
    )
    combined_timing = activity_summary_from_points(
        all_points=[*codex_all_points, *claude_all_points],
        coding_points=[*codex_coding_points, *claude_coding_points],
        start_exclusive=start_exclusive,
        end_inclusive=end_inclusive,
        idle_threshold_seconds=idle_threshold_seconds,
        min_burst_seconds=min_burst_seconds,
    )
    codex_cost = estimate_cost_usd(
        codex_uncached_in,
        codex_out,
        price_in_per_1m=codex_price_in_per_1m,
        price_out_per_1m=codex_price_out_per_1m,
    ) + estimate_cost_usd(
        codex_cached_in,
        0,
        price_in_per_1m=codex_price_cached_input_per_1m,
        price_out_per_1m=0.0,
    )
    claude_cost = estimate_cost_usd(
        claude_base_in,
        claude_out,
        price_in_per_1m=claude_price_in_per_1m,
        price_out_per_1m=claude_price_out_per_1m,
    ) + estimate_cost_usd(
        claude_cache_write_in,
        0,
        price_in_per_1m=claude_price_cache_write_per_1m,
        price_out_per_1m=0.0,
    ) + estimate_cost_usd(
        claude_cache_read_in,
        0,
        price_in_per_1m=claude_price_cache_read_per_1m,
        price_out_per_1m=0.0,
    )
    combined_cost = codex_cost + claude_cost

    return {
        "window": {
            "start_exclusive_utc": start_exclusive.isoformat() if start_exclusive else None,
            "end_inclusive_utc": end_inclusive.isoformat(),
        },
        "codex": {
            "sessions_considered": len(codex_sessions),
            "files_with_usage": codex_files_with_usage,
            "sessions_with_usage": len(codex_sessions_with_usage),
            "tokens_in": codex_in,
            "tokens_in_uncached": codex_uncached_in,
            "tokens_in_cached": codex_cached_in,
            "tokens_out": codex_out,
            "total_tokens": codex_total,
            "estimated_cost_usd": round(codex_cost, 2),
            "model_tokens": dict(sorted(codex_model_totals.items(), key=lambda row: row[0])),
        },
        "claude": {
            "events_considered": len(claude_events),
            "files_with_usage": len(claude_files_with_usage),
            "tokens_in": claude_in,
            "tokens_in_base": claude_base_in,
            "tokens_in_cache_write": claude_cache_write_in,
            "tokens_in_cache_read": claude_cache_read_in,
            "tokens_out": claude_out,
            "total_tokens": claude_total,
            "estimated_cost_usd": round(claude_cost, 2),
            "model_tokens": dict(sorted(claude_model_totals.items(), key=lambda row: row[0])),
        },
        "combined": {
            "tokens_in": codex_in + claude_in,
            "tokens_out": codex_out + claude_out,
            "total_tokens": codex_total + claude_total,
            "estimated_cost_usd": round(combined_cost, 2),
        },
        "cost_assumptions_usd_per_1m": {
            "codex_gpt5x": {
                "input_uncached": codex_price_in_per_1m,
                "input_cached": codex_price_cached_input_per_1m,
                "output": codex_price_out_per_1m,
            },
            "claude_opus4x": {
                "input_base": claude_price_in_per_1m,
                "input_cache_write": claude_price_cache_write_per_1m,
                "input_cache_read": claude_price_cache_read_per_1m,
                "output": claude_price_out_per_1m,
            },
        },
        "timing": {
            "idle_threshold_seconds": idle_threshold_seconds,
            "min_burst_seconds": min_burst_seconds,
            "codex": codex_timing,
            "claude": claude_timing,
            "combined": combined_timing,
        },
    }


def parse_scc_cocomo(text_output: str) -> dict[str, Any]:
    cost_match = re.search(r"Estimated Cost to Develop \(organic\)\s+\$([0-9,]+)", text_output)
    schedule_match = re.search(r"Estimated Schedule Effort \(organic\)\s+([0-9.]+)\s+months", text_output)
    people_match = re.search(r"Estimated People Required \(organic\)\s+([0-9.]+)", text_output)
    return {
        "estimated_cost_usd": int(cost_match.group(1).replace(",", "")) if cost_match else None,
        "estimated_schedule_months": float(schedule_match.group(1)) if schedule_match else None,
        "estimated_people": float(people_match.group(1)) if people_match else None,
    }


def collect_scc_snapshot(repo_root: Path, ref: str) -> dict[str, Any]:
    if shutil.which("scc") is None:
        return {"error": "scc not found in PATH"}

    with tempfile.TemporaryDirectory(prefix="realitycheck-scc-") as tmp_dir:
        tmp_path = Path(tmp_dir)

        archive_proc = subprocess.Popen(
            ["git", "archive", ref],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert archive_proc.stdout is not None
        extract = subprocess.run(
            ["tar", "-x", "-C", str(tmp_path)],
            stdin=archive_proc.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        archive_proc.stdout.close()
        archive_stderr = archive_proc.stderr.read().decode("utf-8", errors="replace") if archive_proc.stderr else ""
        archive_rc = archive_proc.wait()
        if archive_rc != 0:
            raise RuntimeError(f"git archive failed for {ref}: {archive_stderr.strip()}")
        if extract.returncode != 0:
            raise RuntimeError(f"tar extract failed for {ref}: {extract.stderr.strip()}")

        scc_json_raw = run_command(["scc", "--format", "json", str(tmp_path)])
        rows = json.loads(scc_json_raw)
        if not isinstance(rows, list):
            raise RuntimeError(f"unexpected scc JSON format for {ref}")

        totals = {
            "files": 0,
            "lines": 0,
            "code": 0,
            "comments": 0,
            "blanks": 0,
            "complexity": 0,
        }
        python_totals = {
            "files": 0,
            "lines": 0,
            "code": 0,
            "comments": 0,
            "blanks": 0,
            "complexity": 0,
        }
        for row_any in rows:
            if not isinstance(row_any, dict):
                continue
            count = safe_int(row_any.get("Count"))
            lines = safe_int(row_any.get("Lines"))
            code = safe_int(row_any.get("Code"))
            comments = safe_int(row_any.get("Comment"))
            blanks = safe_int(row_any.get("Blank"))
            complexity = safe_int(row_any.get("Complexity"))
            totals["files"] += count
            totals["lines"] += lines
            totals["code"] += code
            totals["comments"] += comments
            totals["blanks"] += blanks
            totals["complexity"] += complexity
            if row_any.get("Name") == "Python":
                python_totals = {
                    "files": count,
                    "lines": lines,
                    "code": code,
                    "comments": comments,
                    "blanks": blanks,
                    "complexity": complexity,
                }

        scc_text = run_command(["scc", str(tmp_path)])
        cocomo = parse_scc_cocomo(scc_text)
        return {
            "totals": totals,
            "python": python_totals,
            "cocomo": cocomo,
        }


def count_tests_in_file(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return 0

    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            count += 1
            continue
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                    count += 1
    return count


def classify_test_file(path: Path) -> str:
    name = path.name.lower()
    path_text = str(path).lower()
    if "adversarial" in name or "adversarial" in path_text:
        return "adversarial"
    if name == "test_e2e.py" or "integration" in name or "e2e" in name:
        return "integration"
    return "unit"


def collect_test_composition_from_tree(root: Path) -> dict[str, Any]:
    tests_root = root / "tests"
    if not tests_root.exists():
        return {
            "tests_root": "tests",
            "test_files": 0,
            "test_functions": 0,
            "by_category": {
                "unit": {"test_files": 0, "test_functions": 0},
                "integration": {"test_files": 0, "test_functions": 0},
                "adversarial": {"test_files": 0, "test_functions": 0},
            },
        }

    files = sorted(
        {
            path
            for pattern in ("test_*.py", "*_test.py")
            for path in tests_root.rglob(pattern)
            if path.is_file()
        }
    )
    by_category = {
        "unit": {"test_files": 0, "test_functions": 0},
        "integration": {"test_files": 0, "test_functions": 0},
        "adversarial": {"test_files": 0, "test_functions": 0},
    }
    total_functions = 0
    for file_path in files:
        category = classify_test_file(file_path)
        functions = count_tests_in_file(file_path)
        by_category[category]["test_files"] += 1
        by_category[category]["test_functions"] += functions
        total_functions += functions

    return {
        "tests_root": "tests",
        "test_files": len(files),
        "test_functions": total_functions,
        "by_category": by_category,
    }


def collect_test_composition_snapshot(repo_root: Path, ref: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="realitycheck-tests-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        archive_proc = subprocess.Popen(
            ["git", "archive", ref],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert archive_proc.stdout is not None
        extract = subprocess.run(
            ["tar", "-x", "-C", str(tmp_path)],
            stdin=archive_proc.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        archive_proc.stdout.close()
        archive_stderr = archive_proc.stderr.read().decode("utf-8", errors="replace") if archive_proc.stderr else ""
        archive_rc = archive_proc.wait()
        if archive_rc != 0:
            raise RuntimeError(f"git archive failed for {ref}: {archive_stderr.strip()}")
        if extract.returncode != 0:
            raise RuntimeError(f"tar extract failed for {ref}: {extract.stderr.strip()}")
        return collect_test_composition_from_tree(tmp_path)


def collect_documentation_churn(repo_root: Path, previous_tag: str | None, current_tag: str) -> dict[str, Any]:
    range_arg = git_range_arg(previous_tag, current_tag)
    paths = ["--", "docs", "README.md", "AGENTS.md", "methodology"]
    commit_output = run_command(["git", "log", "--format=%H", range_arg, *paths], cwd=repo_root)
    commits = [line.strip() for line in commit_output.splitlines() if line.strip()]
    numstat_output = run_command(["git", "log", "--pretty=tformat:", "--numstat", range_arg, *paths], cwd=repo_root)
    insertions, deletions = parse_numstat(numstat_output)
    files_output = run_command(["git", "log", "--name-only", "--pretty=format:", range_arg, *paths], cwd=repo_root)
    unique_files = {line.strip() for line in files_output.splitlines() if line.strip()}
    return {
        "scope": ["docs/**", "README.md", "AGENTS.md", "methodology/**"],
        "commits": len(set(commits)),
        "unique_files_touched": len(unique_files),
        "insertions": insertions,
        "deletions": deletions,
        "net_lines": insertions - deletions,
    }


def fmt_int(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}"


def fmt_money(value: float | None) -> str:
    if value is None:
        return "-"
    return f"${value:,.2f}"


def estimate_cost_usd(tokens_in: int, tokens_out: int, *, price_in_per_1m: float, price_out_per_1m: float) -> float:
    return (tokens_in / 1_000_000.0) * price_in_per_1m + (tokens_out / 1_000_000.0) * price_out_per_1m


def delta_row(current: int | float | None, previous: int | float | None) -> dict[str, Any]:
    if current is None or previous is None:
        return {"current": current, "previous": previous, "delta": None, "pct": None}
    delta = current - previous
    pct = (delta / previous * 100.0) if previous != 0 else None
    return {"current": current, "previous": previous, "delta": delta, "pct": pct}


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:+.1f}%"


def duration_seconds(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    delta = int((end - start).total_seconds())
    return max(0, delta)


def fmt_duration(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    if seconds == 0:
        return "0m"
    minutes, _ = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


def markdown_table(
    headers: list[str],
    rows: list[list[Any]],
    *,
    colalign: list[str] | None = None,
) -> str:
    if tabulate is not None:
        return tabulate(rows, headers=headers, tablefmt="pipe", colalign=colalign)

    # Fallback when tabulate is unavailable.
    all_rows = [headers, *rows]
    widths = [max(len(str(row[idx])) for row in all_rows) for idx in range(len(headers))]

    def _render_row(row: list[Any]) -> str:
        cells: list[str] = []
        for idx, value in enumerate(row):
            text = str(value)
            align = (colalign[idx] if colalign and idx < len(colalign) else "left").lower()
            if align == "right":
                cells.append(text.rjust(widths[idx]))
            elif align == "center":
                cells.append(text.center(widths[idx]))
            else:
                cells.append(text.ljust(widths[idx]))
        return "| " + " | ".join(cells) + " |"

    def _rule_row() -> str:
        cells: list[str] = []
        for idx, width in enumerate(widths):
            align = (colalign[idx] if colalign and idx < len(colalign) else "left").lower()
            w = max(3, width)
            if align == "right":
                cells.append("-" * (w - 1) + ":")
            elif align == "center":
                cells.append(":" + "-" * (w - 2) + ":")
            else:
                cells.append(":" + "-" * (w - 1))
        return "| " + " | ".join(cells) + " |"

    rendered = [_render_row(headers), _rule_row()]
    rendered.extend(_render_row(row) for row in rows)
    return "\n".join(rendered)


def render_markdown(payload: dict[str, Any]) -> str:
    releases = payload.get("releases", [])
    if not isinstance(releases, list):
        releases = []
    totals = payload.get("totals", {})
    cost_assumptions = payload.get("cost_assumptions_usd_per_1m", {})

    lines: list[str] = []
    lines.append("# Reality Check - Development Statistics by Tagged Release")
    lines.append("")
    lines.append(f"*Generated (UTC): `{payload.get('generated_at_utc')}`*")
    lines.append(f"*Repo: `{payload.get('repo_root')}`*")
    lines.append(f"*Tag count in report: `{len(releases)}`*")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- Git churn is computed from each release range (`prev_tag..tag`, first tag uses full history to tag).")
    lines.append("- Session usage is summed from local JSONL logs scoped to this repo path:")
    lines.append("  - Codex: `~/.codex/sessions/**/rollout-*.jsonl` (windowed counter deltas).")
    lines.append("  - Claude: `~/.claude/projects/-home-lhl-github-lhl-realitycheck/*.jsonl` (per-message usage sums).")
    lines.append("- Active/coding/planning times are estimates from timestamp bursts:")
    lines.append("  - `active`: contiguous event clusters (gap <= 5m).")
    lines.append("  - `coding`: tool-use/function-call clusters.")
    lines.append("  - `planning`: `active - coding`.")
    codex_pricing = cost_assumptions.get("codex_gpt5x", {})
    claude_pricing = cost_assumptions.get("claude_opus4x", {})
    lines.append("- Cost assumptions used for estimated USD:")
    lines.append(
        "  - Codex/gpt-5.x: "
        f"uncached input `${codex_pricing.get('input_uncached', DEFAULT_GPT5_INPUT_USD_PER_1M):.3f}` / "
        f"cached input `${codex_pricing.get('input_cached', DEFAULT_GPT5_CACHED_INPUT_USD_PER_1M):.3f}` / "
        f"output `${codex_pricing.get('output', DEFAULT_GPT5_OUTPUT_USD_PER_1M):.2f}` per 1M."
    )
    lines.append(
        "  - Claude/Opus-4.x: "
        f"base input `${claude_pricing.get('input_base', DEFAULT_OPUS4_INPUT_USD_PER_1M):.2f}` / "
        f"cache write `${claude_pricing.get('input_cache_write', DEFAULT_OPUS4_CACHE_WRITE_USD_PER_1M):.2f}` / "
        f"cache read `${claude_pricing.get('input_cache_read', DEFAULT_OPUS4_CACHE_READ_USD_PER_1M):.2f}` / "
        f"output `${claude_pricing.get('output', DEFAULT_OPUS4_OUTPUT_USD_PER_1M):.2f}` per 1M."
    )
    lines.append("- `scc` snapshots are taken from `git archive <tag>` extracts when `--with-scc` is enabled.")
    lines.append("")
    lines.append("## Project Totals")
    lines.append("")

    token_totals = totals.get("tokens", {})
    token_rows = [
        [
            "Codex",
            fmt_int(token_totals.get("codex", {}).get("tokens_in")),
            fmt_int(token_totals.get("codex", {}).get("tokens_out")),
            fmt_int(token_totals.get("codex", {}).get("total_tokens")),
            fmt_money(token_totals.get("codex", {}).get("estimated_cost_usd")),
        ],
        [
            "Claude",
            fmt_int(token_totals.get("claude", {}).get("tokens_in")),
            fmt_int(token_totals.get("claude", {}).get("tokens_out")),
            fmt_int(token_totals.get("claude", {}).get("total_tokens")),
            fmt_money(token_totals.get("claude", {}).get("estimated_cost_usd")),
        ],
        [
            "Combined",
            fmt_int(token_totals.get("combined", {}).get("tokens_in")),
            fmt_int(token_totals.get("combined", {}).get("tokens_out")),
            fmt_int(token_totals.get("combined", {}).get("total_tokens")),
            fmt_money(token_totals.get("combined", {}).get("estimated_cost_usd")),
        ],
    ]
    lines.append(
        markdown_table(
            ["Provider", "Input", "Output", "Total", "Est Cost (USD)"],
            token_rows,
            colalign=["left", "right", "right", "right", "right"],
        )
    )
    lines.append("")
    lines.append(
        markdown_table(
            ["Cache-Sensitive Input Breakdown", "Uncached/Base Input", "Cached Input", "Cache Write", "Cache Read"],
            [
                [
                    "Codex/gpt-5.x",
                    fmt_int(token_totals.get("codex", {}).get("tokens_in_uncached")),
                    fmt_int(token_totals.get("codex", {}).get("tokens_in_cached")),
                    "-",
                    "-",
                ],
                [
                    "Claude/Opus-4.x",
                    fmt_int(token_totals.get("claude", {}).get("tokens_in_base")),
                    "-",
                    fmt_int(token_totals.get("claude", {}).get("tokens_in_cache_write")),
                    fmt_int(token_totals.get("claude", {}).get("tokens_in_cache_read")),
                ],
            ],
            colalign=["left", "right", "right", "right", "right"],
        )
    )
    lines.append("")

    activity_totals = totals.get("activity_seconds", {})
    activity_total_rows = [
        ["Active (estimated)", activity_totals.get("active_human", "-"), fmt_int(activity_totals.get("active"))],
        ["Coding (estimated)", activity_totals.get("coding_human", "-"), fmt_int(activity_totals.get("coding"))],
        ["Planning (estimated)", activity_totals.get("planning_human", "-"), fmt_int(activity_totals.get("planning"))],
    ]
    lines.append(
        markdown_table(
            ["Activity", "Duration", "Seconds"],
            activity_total_rows,
            colalign=["left", "right", "right"],
        )
    )
    lines.append("")

    test_totals = totals.get("tests", {})
    lines.append(
        markdown_table(
            ["Test Composition (sum across tags)", "Value"],
            [
                ["Test files", fmt_int(test_totals.get("test_files_sum"))],
                ["Test functions", fmt_int(test_totals.get("test_functions_sum"))],
                ["Unit functions", fmt_int(test_totals.get("unit_functions_sum"))],
                ["Integration functions", fmt_int(test_totals.get("integration_functions_sum"))],
                ["Adversarial functions", fmt_int(test_totals.get("adversarial_functions_sum"))],
            ],
            colalign=["left", "right"],
        )
    )
    lines.append("")

    doc_totals = totals.get("documentation_churn", {})
    lines.append(
        markdown_table(
            ["Documentation Churn (sum across tags)", "Value"],
            [
                ["Commits touching docs scope", fmt_int(doc_totals.get("commits_sum"))],
                ["Unique doc files touched", fmt_int(doc_totals.get("unique_files_touched_sum"))],
                ["Insertions", fmt_int(doc_totals.get("insertions_sum"))],
                ["Deletions", fmt_int(doc_totals.get("deletions_sum"))],
                ["Net lines", fmt_int(doc_totals.get("net_lines_sum"))],
            ],
            colalign=["left", "right"],
        )
    )
    lines.append("")

    lines.append("## Summary Table")
    lines.append("")

    summary_headers = [
        "Tag",
        "Tag Commit (UTC)",
        "Prev Tag",
        "Cadence",
        "Work Span",
        "Commits",
        "Files",
        "+",
        "-",
        "Net",
        "Codex Tokens",
        "Claude Tokens",
        "Est Cost (USD)",
        "Active (est)",
        "Coding (est)",
        "Planning (est)",
        "Tests",
        "Doc Net",
        "Python LOC (scc)",
    ]
    summary_rows: list[list[Any]] = []
    for release in releases:
        tag = release.get("tag", {})
        rel_timing = release.get("timing", {})
        git_stats = release.get("git", {})
        usage = release.get("usage", {})
        codex = usage.get("codex", {})
        claude = usage.get("claude", {})
        combined = usage.get("combined", {})
        timing = usage.get("timing", {}).get("combined", {})
        tests = release.get("tests", {})
        docs = release.get("documentation_churn", {})
        scc = release.get("scc", {})
        python_code = scc.get("python", {}).get("code") if isinstance(scc, dict) else None
        summary_rows.append(
            [
                f"`{tag.get('name', '-')}`",
                f"`{tag.get('commit_time_utc', '-')}`",
                f"`{release.get('previous_tag') or '-'}`",
                rel_timing.get("cadence_since_prev_human", "-"),
                git_stats.get("work_duration_human", "-"),
                fmt_int(git_stats.get("commits_in_range")),
                fmt_int(git_stats.get("unique_files_touched")),
                fmt_int(git_stats.get("insertions")),
                fmt_int(git_stats.get("deletions")),
                fmt_int(git_stats.get("net_lines")),
                fmt_int(codex.get("total_tokens")),
                fmt_int(claude.get("total_tokens")),
                fmt_money(combined.get("estimated_cost_usd")),
                timing.get("active_human", "-"),
                timing.get("coding_human", "-"),
                timing.get("planning_human", "-"),
                fmt_int(tests.get("test_functions")),
                fmt_int(docs.get("net_lines")),
                fmt_int(python_code if isinstance(python_code, int) else None),
            ]
        )
    summary_rows.append(
        [
            "**TOTAL**",
            "-",
            "-",
            "-",
            "-",
            fmt_int(totals.get("commits")),
            fmt_int(totals.get("files_touched_sum")),
            fmt_int(totals.get("insertions")),
            fmt_int(totals.get("deletions")),
            fmt_int(totals.get("net_lines")),
            fmt_int(token_totals.get("codex", {}).get("total_tokens")),
            fmt_int(token_totals.get("claude", {}).get("total_tokens")),
            fmt_money(token_totals.get("combined", {}).get("estimated_cost_usd")),
            activity_totals.get("active_human", "-"),
            activity_totals.get("coding_human", "-"),
            activity_totals.get("planning_human", "-"),
            fmt_int(test_totals.get("test_functions_sum")),
            fmt_int(doc_totals.get("net_lines_sum")),
            "-",
        ]
    )
    lines.append(
        markdown_table(
            summary_headers,
            summary_rows,
            colalign=[
                "left",
                "left",
                "left",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
                "right",
            ],
        )
    )
    lines.append("")

    for release in releases:
        tag = release.get("tag", {})
        rel_timing = release.get("timing", {})
        release_delta = release.get("snapshot_delta_vs_prior_release")
        git_stats = release.get("git", {})
        usage = release.get("usage", {})
        codex = usage.get("codex", {})
        claude = usage.get("claude", {})
        combined = usage.get("combined", {})
        window = usage.get("window", {})
        timing = usage.get("timing", {})
        tests = release.get("tests", {})
        docs = release.get("documentation_churn", {})
        scc = release.get("scc", {})

        lines.append(f"## {tag.get('name', '-')}")
        lines.append("")
        lines.append(f"- Tag commit: `{tag.get('commit_short', '-')}` (`{tag.get('commit_time_utc', '-')}`)")
        lines.append(f"- Previous tag: `{release.get('previous_tag') or '-'}`")
        lines.append(f"- Cadence since previous tag: `{rel_timing.get('cadence_since_prev_human', '-')}`")
        lines.append(f"- Git range: `{git_stats.get('range', '-')}`")
        lines.append(f"- Range commit span: `{git_stats.get('first_commit_utc', '-')}` -> `{git_stats.get('last_commit_utc', '-')}`")
        lines.append(f"- Range work duration: `{git_stats.get('work_duration_human', '-')}`")
        lines.append(f"- Inclusive day span: `{git_stats.get('span_days_inclusive', 0)}`")
        lines.append("")
        lines.append(
            markdown_table(
                ["Metric", "Value"],
                [
                    ["Commits in range", fmt_int(git_stats.get("commits_in_range"))],
                    ["Unique files touched", fmt_int(git_stats.get("unique_files_touched"))],
                    ["Insertions", fmt_int(git_stats.get("insertions"))],
                    ["Deletions", fmt_int(git_stats.get("deletions"))],
                    ["Net lines", fmt_int(git_stats.get("net_lines"))],
                    ["Cumulative commits at tag", fmt_int(git_stats.get("commits_to_tag"))],
                ],
                colalign=["left", "right"],
            )
        )
        lines.append("")
        lines.append(
            markdown_table(
                ["Velocity", "Value"],
                [
                    ["Cadence since previous tag", rel_timing.get("cadence_since_prev_human", "-")],
                    ["Work span in range", git_stats.get("work_duration_human", "-")],
                    ["Commits/day (inclusive)", git_stats.get("commits_per_day_avg", "-")],
                    ["Commits/hour (active span)", git_stats.get("commits_per_hour_active_span", "-")],
                    [
                        "Peak commit day",
                        (
                            f"{git_stats.get('peak_commit_day', {}).get('date')} "
                            f"({git_stats.get('peak_commit_day', {}).get('commits')} commits)"
                            if git_stats.get("peak_commit_day")
                            else "-"
                        ),
                    ],
                ],
                colalign=["left", "right"],
            )
        )
        commits_by_day = git_stats.get("commits_by_day", {})
        if isinstance(commits_by_day, dict) and commits_by_day:
            lines.append("")
            lines.append(
                markdown_table(
                    ["Date", "Commits"],
                    [[day, count] for day, count in commits_by_day.items()],
                    colalign=["left", "right"],
                )
            )
        if isinstance(release_delta, dict):
            lines.append("")
            lines.append(
                markdown_table(
                    ["Release Snapshot Delta vs Prior", "Previous", "Current", "Delta", "Delta %"],
                    [
                        [
                            "Commits",
                            fmt_int(release_delta.get("commits", {}).get("previous")),
                            fmt_int(release_delta.get("commits", {}).get("current")),
                            fmt_int(release_delta.get("commits", {}).get("delta")),
                            fmt_pct(release_delta.get("commits", {}).get("pct")),
                        ],
                        [
                            "Net lines",
                            fmt_int(release_delta.get("net_lines", {}).get("previous")),
                            fmt_int(release_delta.get("net_lines", {}).get("current")),
                            fmt_int(release_delta.get("net_lines", {}).get("delta")),
                            fmt_pct(release_delta.get("net_lines", {}).get("pct")),
                        ],
                        [
                            "Combined tokens",
                            fmt_int(release_delta.get("combined_tokens", {}).get("previous")),
                            fmt_int(release_delta.get("combined_tokens", {}).get("current")),
                            fmt_int(release_delta.get("combined_tokens", {}).get("delta")),
                            fmt_pct(release_delta.get("combined_tokens", {}).get("pct")),
                        ],
                        [
                            "Estimated cost (USD)",
                            fmt_money(release_delta.get("combined_cost_usd", {}).get("previous")),
                            fmt_money(release_delta.get("combined_cost_usd", {}).get("current")),
                            fmt_money(release_delta.get("combined_cost_usd", {}).get("delta")),
                            fmt_pct(release_delta.get("combined_cost_usd", {}).get("pct")),
                        ],
                        [
                            "Test functions",
                            fmt_int(release_delta.get("test_functions", {}).get("previous")),
                            fmt_int(release_delta.get("test_functions", {}).get("current")),
                            fmt_int(release_delta.get("test_functions", {}).get("delta")),
                            fmt_pct(release_delta.get("test_functions", {}).get("pct")),
                        ],
                    ],
                    colalign=["left", "right", "right", "right", "right"],
                )
            )
        lines.append("")
        lines.append(f"- Usage window: `{window.get('start_exclusive_utc') or 'START'}` -> `{window.get('end_inclusive_utc')}`")
        lines.append("")
        lines.append(
            markdown_table(
                ["Usage Source", "Files/Sessions", "Input", "Output", "Total", "Est Cost (USD)"],
                [
                    [
                        "Codex",
                        f"{fmt_int(codex.get('sessions_with_usage'))} sessions / {fmt_int(codex.get('files_with_usage'))} files",
                        fmt_int(codex.get("tokens_in")),
                        fmt_int(codex.get("tokens_out")),
                        fmt_int(codex.get("total_tokens")),
                        fmt_money(codex.get("estimated_cost_usd")),
                    ],
                    [
                        "Claude",
                        f"{fmt_int(claude.get('files_with_usage'))} files",
                        fmt_int(claude.get("tokens_in")),
                        fmt_int(claude.get("tokens_out")),
                        fmt_int(claude.get("total_tokens")),
                        fmt_money(claude.get("estimated_cost_usd")),
                    ],
                    [
                        "Combined",
                        "-",
                        fmt_int(combined.get("tokens_in")),
                        fmt_int(combined.get("tokens_out")),
                        fmt_int(combined.get("total_tokens")),
                        fmt_money(combined.get("estimated_cost_usd")),
                    ],
                ],
                colalign=["left", "left", "right", "right", "right", "right"],
            )
        )
        lines.append("")
        lines.append(
            markdown_table(
                ["Cost Input Breakdown", "Uncached/Base Input", "Cached Input", "Cache Write", "Cache Read"],
                [
                    [
                        "Codex/gpt-5.x",
                        fmt_int(codex.get("tokens_in_uncached")),
                        fmt_int(codex.get("tokens_in_cached")),
                        "-",
                        "-",
                    ],
                    [
                        "Claude/Opus-4.x",
                        fmt_int(claude.get("tokens_in_base")),
                        "-",
                        fmt_int(claude.get("tokens_in_cache_write")),
                        fmt_int(claude.get("tokens_in_cache_read")),
                    ],
                ],
                colalign=["left", "right", "right", "right", "right"],
            )
        )
        lines.append("")
        lines.append(
            markdown_table(
                ["Activity (estimated)", "Events", "Wall", "Active", "Coding", "Planning", "Idle", "Active Ratio"],
                [
                    [
                        "Codex",
                        fmt_int(timing.get("codex", {}).get("events")),
                        timing.get("codex", {}).get("wall_human", "-"),
                        timing.get("codex", {}).get("active_human", "-"),
                        timing.get("codex", {}).get("coding_human", "-"),
                        timing.get("codex", {}).get("planning_human", "-"),
                        timing.get("codex", {}).get("idle_human", "-"),
                        timing.get("codex", {}).get("active_ratio"),
                    ],
                    [
                        "Claude",
                        fmt_int(timing.get("claude", {}).get("events")),
                        timing.get("claude", {}).get("wall_human", "-"),
                        timing.get("claude", {}).get("active_human", "-"),
                        timing.get("claude", {}).get("coding_human", "-"),
                        timing.get("claude", {}).get("planning_human", "-"),
                        timing.get("claude", {}).get("idle_human", "-"),
                        timing.get("claude", {}).get("active_ratio"),
                    ],
                    [
                        "Combined",
                        fmt_int(timing.get("combined", {}).get("events")),
                        timing.get("combined", {}).get("wall_human", "-"),
                        timing.get("combined", {}).get("active_human", "-"),
                        timing.get("combined", {}).get("coding_human", "-"),
                        timing.get("combined", {}).get("planning_human", "-"),
                        timing.get("combined", {}).get("idle_human", "-"),
                        timing.get("combined", {}).get("active_ratio"),
                    ],
                ],
                colalign=["left", "right", "right", "right", "right", "right", "right", "right"],
            )
        )

        lines.append("")
        lines.append(
            markdown_table(
                ["Test Composition", "Files", "Functions"],
                [
                    [
                        "Unit",
                        fmt_int(tests.get("by_category", {}).get("unit", {}).get("test_files")),
                        fmt_int(tests.get("by_category", {}).get("unit", {}).get("test_functions")),
                    ],
                    [
                        "Integration",
                        fmt_int(tests.get("by_category", {}).get("integration", {}).get("test_files")),
                        fmt_int(tests.get("by_category", {}).get("integration", {}).get("test_functions")),
                    ],
                    [
                        "Adversarial",
                        fmt_int(tests.get("by_category", {}).get("adversarial", {}).get("test_files")),
                        fmt_int(tests.get("by_category", {}).get("adversarial", {}).get("test_functions")),
                    ],
                    ["Total", fmt_int(tests.get("test_files")), fmt_int(tests.get("test_functions"))],
                ],
                colalign=["left", "right", "right"],
            )
        )

        lines.append("")
        lines.append(
            markdown_table(
                ["Documentation Churn", "Value"],
                [
                    ["Commits touching docs scope", fmt_int(docs.get("commits"))],
                    ["Unique files touched", fmt_int(docs.get("unique_files_touched"))],
                    ["Insertions", fmt_int(docs.get("insertions"))],
                    ["Deletions", fmt_int(docs.get("deletions"))],
                    ["Net lines", fmt_int(docs.get("net_lines"))],
                ],
                colalign=["left", "right"],
            )
        )

        if isinstance(scc, dict) and not scc.get("error"):
            python_row = scc.get("python", {})
            cocomo = scc.get("cocomo", {})
            lines.append("")
            schedule = cocomo.get("estimated_schedule_months")
            people = cocomo.get("estimated_people")
            lines.append(
                markdown_table(
                    ["scc Snapshot", "Value"],
                    [
                        ["Total files", fmt_int(scc.get("totals", {}).get("files"))],
                        ["Total code lines", fmt_int(scc.get("totals", {}).get("code"))],
                        ["Python files", fmt_int(python_row.get("files"))],
                        ["Python code lines", fmt_int(python_row.get("code"))],
                        ["COCOMO estimated cost (USD)", fmt_int(cocomo.get("estimated_cost_usd"))],
                        ["COCOMO schedule (months)", schedule if schedule is not None else "-"],
                        ["COCOMO people", people if people is not None else "-"],
                    ],
                    colalign=["left", "right"],
                )
            )
        lines.append("")

    lines.append("## Repro Commands")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/release_stats_rollup.py \\")
    lines.append("  --repo-root . \\")
    lines.append("  --with-scc \\")
    lines.append("  --with-test-composition \\")
    lines.append("  --output-json /tmp/realitycheck-release-stats.json \\")
    lines.append("  --output-markdown docs/STATUS-dev-stats.md")
    lines.append("```")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def select_tag_slice(tags: list[TagInfo], from_tag: str | None, to_tag: str | None) -> tuple[int, int]:
    if not tags:
        raise ValueError("no tags found")
    names = [tag.name for tag in tags]

    start_idx = 0
    if from_tag:
        if from_tag not in names:
            raise ValueError(f"--from-tag not found: {from_tag}")
        start_idx = names.index(from_tag)

    end_idx = len(tags) - 1
    if to_tag:
        if to_tag not in names:
            raise ValueError(f"--to-tag not found: {to_tag}")
        end_idx = names.index(to_tag)

    if start_idx > end_idx:
        raise ValueError("--from-tag must be earlier than or equal to --to-tag")
    return start_idx, end_idx


def build_report(
    *,
    repo_root: Path,
    tags: list[TagInfo],
    start_idx: int,
    end_idx: int,
    codex_sessions: list[CodexSession],
    claude_events: list[ClaudeUsageEvent],
    with_scc: bool,
    with_test_composition: bool,
    codex_price_in_per_1m: float,
    codex_price_cached_input_per_1m: float,
    codex_price_out_per_1m: float,
    claude_price_in_per_1m: float,
    claude_price_cache_write_per_1m: float,
    claude_price_cache_read_per_1m: float,
    claude_price_out_per_1m: float,
) -> dict[str, Any]:
    releases: list[dict[str, Any]] = []
    previous_release_for_delta: dict[str, Any] | None = None
    total_commits = 0
    total_files = 0
    total_insertions = 0
    total_deletions = 0
    total_net = 0
    total_codex_in = 0
    total_codex_uncached_in = 0
    total_codex_cached_in = 0
    total_codex_out = 0
    total_codex_total = 0
    total_claude_in = 0
    total_claude_base_in = 0
    total_claude_cache_write_in = 0
    total_claude_cache_read_in = 0
    total_claude_out = 0
    total_claude_total = 0
    total_combined_in = 0
    total_combined_out = 0
    total_combined_total = 0
    total_codex_cost = 0.0
    total_claude_cost = 0.0
    total_combined_cost = 0.0
    total_active = 0
    total_coding = 0
    total_planning = 0
    total_test_files = 0
    total_test_functions = 0
    total_test_unit_functions = 0
    total_test_integration_functions = 0
    total_test_adversarial_functions = 0
    total_doc_commits = 0
    total_doc_files = 0
    total_doc_insertions = 0
    total_doc_deletions = 0

    for idx in range(start_idx, end_idx + 1):
        tag = tags[idx]
        previous = tags[idx - 1] if idx > 0 else None
        git_stats = collect_git_range_stats(repo_root, previous.name if previous else None, tag.name)
        usage = aggregate_usage_for_window(
            codex_sessions=codex_sessions,
            claude_events=claude_events,
            start_exclusive=previous.commit_time_utc if previous else None,
            end_inclusive=tag.commit_time_utc,
            codex_price_in_per_1m=codex_price_in_per_1m,
            codex_price_cached_input_per_1m=codex_price_cached_input_per_1m,
            codex_price_out_per_1m=codex_price_out_per_1m,
            claude_price_in_per_1m=claude_price_in_per_1m,
            claude_price_cache_write_per_1m=claude_price_cache_write_per_1m,
            claude_price_cache_read_per_1m=claude_price_cache_read_per_1m,
            claude_price_out_per_1m=claude_price_out_per_1m,
        )
        scc_snapshot = collect_scc_snapshot(repo_root, tag.name) if with_scc else {"skipped": True}
        test_composition = (
            collect_test_composition_snapshot(repo_root, tag.name) if with_test_composition else {"skipped": True}
        )
        doc_churn = collect_documentation_churn(repo_root, previous.name if previous else None, tag.name)
        cadence_seconds = duration_seconds(previous.commit_time_utc, tag.commit_time_utc) if previous else None
        cadence_human = fmt_duration(cadence_seconds)

        release_row: dict[str, Any] = {
            "tag": {
                "name": tag.name,
                "commit": tag.commit,
                "commit_short": tag.commit_short,
                "commit_time_utc": tag.commit_time_utc.isoformat(),
                "tag_time_utc": tag.tag_time_utc.isoformat(),
            },
            "previous_tag": previous.name if previous else None,
            "timing": {
                "cadence_since_prev_seconds": cadence_seconds,
                "cadence_since_prev_human": cadence_human,
            },
            "git": git_stats,
            "usage": usage,
            "scc": scc_snapshot,
            "tests": test_composition,
            "documentation_churn": doc_churn,
        }

        if previous_release_for_delta is not None:
            prev_git = previous_release_for_delta.get("git", {})
            prev_usage = previous_release_for_delta.get("usage", {})
            prev_tests = previous_release_for_delta.get("tests", {})
            release_row["snapshot_delta_vs_prior_release"] = {
                "commits": delta_row(
                    safe_int(git_stats.get("commits_in_range")),
                    safe_int(prev_git.get("commits_in_range")),
                ),
                "net_lines": delta_row(
                    safe_int(git_stats.get("net_lines")),
                    safe_int(prev_git.get("net_lines")),
                ),
                "combined_tokens": delta_row(
                    safe_int(usage.get("combined", {}).get("total_tokens")),
                    safe_int(prev_usage.get("combined", {}).get("total_tokens")),
                ),
                "combined_cost_usd": delta_row(
                    float(usage.get("combined", {}).get("estimated_cost_usd") or 0.0),
                    float(prev_usage.get("combined", {}).get("estimated_cost_usd") or 0.0),
                ),
                "test_functions": delta_row(
                    safe_int(test_composition.get("test_functions")),
                    safe_int(prev_tests.get("test_functions")),
                ),
            }
        else:
            release_row["snapshot_delta_vs_prior_release"] = None

        total_commits += safe_int(git_stats.get("commits_in_range"))
        total_files += safe_int(git_stats.get("unique_files_touched"))
        total_insertions += safe_int(git_stats.get("insertions"))
        total_deletions += safe_int(git_stats.get("deletions"))
        total_net += safe_int(git_stats.get("net_lines"))
        total_codex_in += safe_int(usage.get("codex", {}).get("tokens_in"))
        total_codex_uncached_in += safe_int(usage.get("codex", {}).get("tokens_in_uncached"))
        total_codex_cached_in += safe_int(usage.get("codex", {}).get("tokens_in_cached"))
        total_codex_out += safe_int(usage.get("codex", {}).get("tokens_out"))
        total_codex_total += safe_int(usage.get("codex", {}).get("total_tokens"))
        total_claude_in += safe_int(usage.get("claude", {}).get("tokens_in"))
        total_claude_base_in += safe_int(usage.get("claude", {}).get("tokens_in_base"))
        total_claude_cache_write_in += safe_int(usage.get("claude", {}).get("tokens_in_cache_write"))
        total_claude_cache_read_in += safe_int(usage.get("claude", {}).get("tokens_in_cache_read"))
        total_claude_out += safe_int(usage.get("claude", {}).get("tokens_out"))
        total_claude_total += safe_int(usage.get("claude", {}).get("total_tokens"))
        total_combined_in += safe_int(usage.get("combined", {}).get("tokens_in"))
        total_combined_out += safe_int(usage.get("combined", {}).get("tokens_out"))
        total_combined_total += safe_int(usage.get("combined", {}).get("total_tokens"))
        total_codex_cost += float(usage.get("codex", {}).get("estimated_cost_usd") or 0.0)
        total_claude_cost += float(usage.get("claude", {}).get("estimated_cost_usd") or 0.0)
        total_combined_cost += float(usage.get("combined", {}).get("estimated_cost_usd") or 0.0)
        total_active += safe_int(usage.get("timing", {}).get("combined", {}).get("active_seconds"))
        total_coding += safe_int(usage.get("timing", {}).get("combined", {}).get("coding_seconds"))
        total_planning += safe_int(usage.get("timing", {}).get("combined", {}).get("planning_seconds"))
        total_test_files += safe_int(test_composition.get("test_files"))
        total_test_functions += safe_int(test_composition.get("test_functions"))
        total_test_unit_functions += safe_int(
            test_composition.get("by_category", {}).get("unit", {}).get("test_functions")
        )
        total_test_integration_functions += safe_int(
            test_composition.get("by_category", {}).get("integration", {}).get("test_functions")
        )
        total_test_adversarial_functions += safe_int(
            test_composition.get("by_category", {}).get("adversarial", {}).get("test_functions")
        )
        total_doc_commits += safe_int(doc_churn.get("commits"))
        total_doc_files += safe_int(doc_churn.get("unique_files_touched"))
        total_doc_insertions += safe_int(doc_churn.get("insertions"))
        total_doc_deletions += safe_int(doc_churn.get("deletions"))

        releases.append(release_row)
        previous_release_for_delta = release_row

    totals = {
        "releases": len(releases),
        "commits": total_commits,
        "files_touched_sum": total_files,
        "insertions": total_insertions,
        "deletions": total_deletions,
        "net_lines": total_net,
        "tokens": {
            "codex": {
                "tokens_in": total_codex_in,
                "tokens_in_uncached": total_codex_uncached_in,
                "tokens_in_cached": total_codex_cached_in,
                "tokens_out": total_codex_out,
                "total_tokens": total_codex_total,
                "estimated_cost_usd": round(total_codex_cost, 2),
            },
            "claude": {
                "tokens_in": total_claude_in,
                "tokens_in_base": total_claude_base_in,
                "tokens_in_cache_write": total_claude_cache_write_in,
                "tokens_in_cache_read": total_claude_cache_read_in,
                "tokens_out": total_claude_out,
                "total_tokens": total_claude_total,
                "estimated_cost_usd": round(total_claude_cost, 2),
            },
            "combined": {
                "tokens_in": total_combined_in,
                "tokens_out": total_combined_out,
                "total_tokens": total_combined_total,
                "estimated_cost_usd": round(total_combined_cost, 2),
            },
        },
        "activity_seconds": {
            "active": total_active,
            "coding": total_coding,
            "planning": total_planning,
            "active_human": fmt_duration(total_active),
            "coding_human": fmt_duration(total_coding),
            "planning_human": fmt_duration(total_planning),
        },
        "tests": {
            "test_files_sum": total_test_files,
            "test_functions_sum": total_test_functions,
            "unit_functions_sum": total_test_unit_functions,
            "integration_functions_sum": total_test_integration_functions,
            "adversarial_functions_sum": total_test_adversarial_functions,
        },
        "documentation_churn": {
            "commits_sum": total_doc_commits,
            "unique_files_touched_sum": total_doc_files,
            "insertions_sum": total_doc_insertions,
            "deletions_sum": total_doc_deletions,
            "net_lines_sum": total_doc_insertions - total_doc_deletions,
        },
    }

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "repo_root": str(repo_root),
        "tags_scanned": [tag.name for tag in tags],
        "selected_tags": [tag.name for tag in tags[start_idx : end_idx + 1]],
        "cost_assumptions_usd_per_1m": {
            "codex_gpt5x": {
                "input_uncached": codex_price_in_per_1m,
                "input_cached": codex_price_cached_input_per_1m,
                "output": codex_price_out_per_1m,
            },
            "claude_opus4x": {
                "input_base": claude_price_in_per_1m,
                "input_cache_write": claude_price_cache_write_per_1m,
                "input_cache_read": claude_price_cache_read_per_1m,
                "output": claude_price_out_per_1m,
            },
        },
        "totals": totals,
        "releases": releases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--from-tag", help="Inclusive starting tag for report")
    parser.add_argument("--to-tag", help="Inclusive ending tag for report")
    parser.add_argument("--skip-usage", action="store_true", help="Skip Codex/Claude usage aggregation")
    parser.add_argument("--with-scc", action="store_true", help="Collect per-tag scc snapshots")
    parser.add_argument(
        "--with-test-composition",
        action="store_true",
        help="Collect per-tag test composition snapshots from git archive",
    )
    parser.add_argument(
        "--price-gpt5-input-per-1m",
        type=float,
        default=DEFAULT_GPT5_INPUT_USD_PER_1M,
        help="Cost assumption for Codex/gpt-5.x uncached input tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-gpt5-cached-input-per-1m",
        type=float,
        default=DEFAULT_GPT5_CACHED_INPUT_USD_PER_1M,
        help="Cost assumption for Codex/gpt-5.x cached input tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-gpt5-output-per-1m",
        type=float,
        default=DEFAULT_GPT5_OUTPUT_USD_PER_1M,
        help="Cost assumption for Codex/gpt-5.x output tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-opus4-input-per-1m",
        type=float,
        default=DEFAULT_OPUS4_INPUT_USD_PER_1M,
        help="Cost assumption for Claude Opus 4.x base input tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-opus4-cache-write-per-1m",
        type=float,
        default=DEFAULT_OPUS4_CACHE_WRITE_USD_PER_1M,
        help="Cost assumption for Claude Opus 4.x cache-write tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-opus4-cache-read-per-1m",
        type=float,
        default=DEFAULT_OPUS4_CACHE_READ_USD_PER_1M,
        help="Cost assumption for Claude Opus 4.x cache-read tokens (USD per 1M)",
    )
    parser.add_argument(
        "--price-opus4-output-per-1m",
        type=float,
        default=DEFAULT_OPUS4_OUTPUT_USD_PER_1M,
        help="Cost assumption for Claude Opus 4.x output tokens (USD per 1M)",
    )
    parser.add_argument("--codex-root", default="~/.codex/sessions", help="Codex sessions root")
    parser.add_argument("--claude-projects-root", default="~/.claude/projects", help="Claude projects root")
    parser.add_argument("--output-json", help="Optional output JSON file path")
    parser.add_argument("--output-markdown", help="Optional output markdown file path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    tags = list_tags(repo_root)
    start_idx, end_idx = select_tag_slice(tags, args.from_tag, args.to_tag)

    codex_sessions: list[CodexSession] = []
    claude_events: list[ClaudeUsageEvent] = []
    if not args.skip_usage:
        codex_root = Path(args.codex_root).expanduser().resolve()
        claude_root = Path(args.claude_projects_root).expanduser().resolve()
        if codex_root.exists():
            codex_sessions = load_codex_sessions(codex_root, repo_root)
        if claude_root.exists():
            claude_events = load_claude_events(claude_root, repo_root)

    payload = build_report(
        repo_root=repo_root,
        tags=tags,
        start_idx=start_idx,
        end_idx=end_idx,
        codex_sessions=codex_sessions,
        claude_events=claude_events,
        with_scc=args.with_scc,
        with_test_composition=args.with_test_composition,
        codex_price_in_per_1m=args.price_gpt5_input_per_1m,
        codex_price_cached_input_per_1m=args.price_gpt5_cached_input_per_1m,
        codex_price_out_per_1m=args.price_gpt5_output_per_1m,
        claude_price_in_per_1m=args.price_opus4_input_per_1m,
        claude_price_cache_write_per_1m=args.price_opus4_cache_write_per_1m,
        claude_price_cache_read_per_1m=args.price_opus4_cache_read_per_1m,
        claude_price_out_per_1m=args.price_opus4_output_per_1m,
    )

    if args.output_json:
        output_json = Path(args.output_json).expanduser().resolve()
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    if args.output_markdown:
        output_md = Path(args.output_markdown).expanduser().resolve()
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(payload), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
