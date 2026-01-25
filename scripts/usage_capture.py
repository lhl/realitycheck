#!/usr/bin/env python3
"""
Usage capture helpers for Reality Check audit logs.

This module parses local agent session logs (Claude Code, Codex CLI, Amp) and
extracts aggregated token usage (and optionally cost when available).

Privacy note: For session identification purposes, a brief context snippet
(first line of the conversation) may be extracted to help users identify
which session is which when multiple sessions exist. Full transcript content
is not retained or stored in the database.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class UsageTotals:
    tokens_in: Optional[int]
    tokens_out: Optional[int]
    total_tokens: Optional[int]
    cost_usd: Optional[float] = None


class NoSessionFoundError(Exception):
    """Raised when no session files are found for a tool."""
    pass


class AmbiguousSessionError(Exception):
    """Raised when multiple session candidates exist and explicit selection is required."""

    def __init__(self, message: str, candidates: list[dict]):
        super().__init__(message)
        self.candidates = candidates


MODEL_PRICING_USD_PER_1M: dict[str, tuple[float, float]] = {
    # NOTE: Prices change frequently. Treat these as a convenience default.
    # See docs/PLAN-audit-log.md for the reference table and update policy.
    "claude-sonnet-4": (3.00, 15.00),
    "claude-opus-4": (15.00, 75.00),
    "gpt-4o": (2.50, 10.00),
    "o1-preview": (15.00, 60.00),
}


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        # Heuristic: treat as seconds; if it's in ms it's likely very large.
        ts = float(value)
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        # Support Z suffix.
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return None


def _in_window(ts: Optional[datetime], window_start: Optional[datetime], window_end: Optional[datetime]) -> bool:
    if window_start is None and window_end is None:
        return True
    if ts is None:
        return False
    if window_start is not None and ts < window_start:
        return False
    if window_end is not None and ts > window_end:
        return False
    return True


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _extract_tokens_claude_usage(usage: dict) -> tuple[int, int, int]:
    input_tokens = _as_int(usage.get("input_tokens") or usage.get("inputTokens"))
    output_tokens = _as_int(usage.get("output_tokens") or usage.get("outputTokens"))
    cache_creation = _as_int(usage.get("cache_creation_input_tokens") or usage.get("cacheCreationInputTokens"))
    cache_read = _as_int(usage.get("cache_read_input_tokens") or usage.get("cacheReadInputTokens"))
    tokens_in = input_tokens + cache_creation + cache_read
    tokens_out = output_tokens
    total_tokens = tokens_in + tokens_out
    return tokens_in, tokens_out, total_tokens


def _parse_claude_jsonl(
    path: Path,
    window_start: Optional[datetime],
    window_end: Optional[datetime],
) -> UsageTotals:
    tokens_in_total = 0
    tokens_out_total = 0
    saw_usage = False

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = _parse_timestamp(obj.get("timestamp") or obj.get("created_at") or obj.get("time"))
            if not _in_window(ts, window_start, window_end):
                continue

            message = obj.get("message")
            if isinstance(message, dict):
                usage = message.get("usage")
            else:
                usage = obj.get("usage")

            if not isinstance(usage, dict):
                continue

            saw_usage = True
            tin, tout, _ = _extract_tokens_claude_usage(usage)
            tokens_in_total += tin
            tokens_out_total += tout

    if not saw_usage:
        return UsageTotals(tokens_in=None, tokens_out=None, total_tokens=None, cost_usd=None)

    return UsageTotals(
        tokens_in=tokens_in_total,
        tokens_out=tokens_out_total,
        total_tokens=tokens_in_total + tokens_out_total,
        cost_usd=None,
    )


def _parse_amp_json(
    path: Path,
    window_start: Optional[datetime],
    window_end: Optional[datetime],
) -> UsageTotals:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return UsageTotals(tokens_in=None, tokens_out=None, total_tokens=None, cost_usd=None)

    messages = data.get("messages")
    if not isinstance(messages, list):
        return UsageTotals(tokens_in=None, tokens_out=None, total_tokens=None, cost_usd=None)

    tokens_in_total = 0
    tokens_out_total = 0
    saw_usage = False

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        ts = _parse_timestamp(msg.get("timestamp") or msg.get("created_at") or msg.get("time"))
        if not _in_window(ts, window_start, window_end):
            continue

        usage = msg.get("usage")
        if not isinstance(usage, dict):
            continue

        saw_usage = True
        input_tokens = _as_int(usage.get("totalInputTokens") or usage.get("inputTokens"))
        if usage.get("totalInputTokens") is None:
            input_tokens += _as_int(usage.get("cacheCreationInputTokens"))
            input_tokens += _as_int(usage.get("cacheReadInputTokens"))

        output_tokens = _as_int(usage.get("outputTokens") or usage.get("output_tokens"))

        tokens_in_total += input_tokens
        tokens_out_total += output_tokens

    if not saw_usage:
        return UsageTotals(tokens_in=None, tokens_out=None, total_tokens=None, cost_usd=None)

    return UsageTotals(
        tokens_in=tokens_in_total,
        tokens_out=tokens_out_total,
        total_tokens=tokens_in_total + tokens_out_total,
        cost_usd=None,
    )


def _parse_codex_jsonl(
    path: Path,
    window_start: Optional[datetime],
    window_end: Optional[datetime],
) -> UsageTotals:
    latest: Optional[dict[str, Any]] = None

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = _parse_timestamp(obj.get("timestamp") or obj.get("created_at") or obj.get("time"))
            if not _in_window(ts, window_start, window_end):
                continue

            info = obj.get("payload", {}).get("info", {}) if isinstance(obj, dict) else {}
            total_usage = info.get("total_token_usage")
            if isinstance(total_usage, dict):
                latest = total_usage

    if not isinstance(latest, dict):
        return UsageTotals(tokens_in=None, tokens_out=None, total_tokens=None, cost_usd=None)

    input_tokens = _as_int(latest.get("input_tokens"))
    cached_input_tokens = _as_int(latest.get("cached_input_tokens"))
    output_tokens = _as_int(latest.get("output_tokens"))
    reasoning_output_tokens = _as_int(latest.get("reasoning_output_tokens"))

    tokens_in = input_tokens + cached_input_tokens
    tokens_out = output_tokens + reasoning_output_tokens
    total_tokens = _as_int(latest.get("total_tokens")) or (tokens_in + tokens_out)

    return UsageTotals(tokens_in=tokens_in, tokens_out=tokens_out, total_tokens=total_tokens, cost_usd=None)


def parse_usage_from_source(
    provider: str,
    path: Path,
    window_start: str | None = None,
    window_end: str | None = None,
) -> UsageTotals:
    """Parse aggregated usage totals from a specific local session log."""
    provider_norm = provider.strip().lower()

    start_dt = _parse_timestamp(window_start) if window_start else None
    end_dt = _parse_timestamp(window_end) if window_end else None

    if provider_norm == "claude":
        return _parse_claude_jsonl(path, start_dt, end_dt)
    if provider_norm == "amp":
        return _parse_amp_json(path, start_dt, end_dt)
    if provider_norm == "codex":
        return _parse_codex_jsonl(path, start_dt, end_dt)

    raise ValueError(f"Unsupported provider for usage capture: '{provider}'")


def estimate_cost_usd(
    model: str,
    tokens_in: int,
    tokens_out: int,
    *,
    price_in_per_1m: float | None = None,
    price_out_per_1m: float | None = None,
) -> Optional[float]:
    """Estimate cost in USD based on tokens and a pricing table.

    Returns None when the model is unknown and no explicit pricing override is provided.
    """
    if tokens_in < 0 or tokens_out < 0:
        return None

    if price_in_per_1m is not None or price_out_per_1m is not None:
        if price_in_per_1m is None or price_out_per_1m is None:
            raise ValueError("Both price_in_per_1m and price_out_per_1m are required when overriding pricing.")
        return (tokens_in / 1_000_000.0) * price_in_per_1m + (tokens_out / 1_000_000.0) * price_out_per_1m

    model_key = model.strip().lower()
    matched: Optional[tuple[float, float]] = None
    for key, prices in MODEL_PRICING_USD_PER_1M.items():
        if model_key == key or model_key.startswith(key):
            matched = prices
            break

    if matched is None:
        return None

    price_in, price_out = matched
    return (tokens_in / 1_000_000.0) * price_in + (tokens_out / 1_000_000.0) * price_out


# =============================================================================
# Session Detection and Token Counting
# =============================================================================

import re
import os
from glob import glob


def _extract_uuid_from_filename(filename: str, tool: str) -> Optional[str]:
    """Extract session UUID from filename based on tool patterns."""
    name = Path(filename).stem

    if tool == "claude":
        # Claude: <uuid>.jsonl - the filename IS the UUID
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        uuid_pattern = r"^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
        match = re.match(uuid_pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    elif tool == "codex":
        # Codex: rollout-<timestamp>-<uuid>.jsonl
        uuid_pattern = r"rollout-\d+-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
        match = re.search(uuid_pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    elif tool == "amp":
        # Amp: T-<uuid>.json
        uuid_pattern = r"^T-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
        match = re.match(uuid_pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).lower()

    return None


def _get_session_paths(tool: str, base_path: Optional[Path] = None) -> list[Path]:
    """Find all session files for a tool."""
    home = base_path or Path.home()

    if tool == "claude":
        # Claude: ~/.claude/projects/*/*.jsonl
        pattern = str(home / ".claude" / "projects" / "*" / "*.jsonl")
    elif tool == "codex":
        # Codex: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
        pattern = str(home / ".codex" / "sessions" / "*" / "*" / "*" / "rollout-*.jsonl")
    elif tool == "amp":
        # Amp: ~/.local/share/amp/threads/T-*.json
        pattern = str(home / ".local" / "share" / "amp" / "threads" / "T-*.json")
    else:
        return []

    paths = [Path(p) for p in glob(pattern)]
    return sorted(paths, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)


def _get_first_content_line(path: Path, tool: str) -> str:
    """Extract first meaningful content line for context snippet."""
    try:
        if tool in ("claude", "codex"):
            # JSONL format
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        # Look for content in message
                        if tool == "claude":
                            content = obj.get("message", {}).get("content")
                            if isinstance(content, list) and content:
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text = block.get("text", "")[:80]
                                        return text
                            elif isinstance(content, str):
                                return content[:80]
                        else:  # codex
                            # Try to find user message
                            payload = obj.get("payload", {})
                            if payload.get("type") == "message":
                                return str(payload.get("content", ""))[:80]
                    except json.JSONDecodeError:
                        continue
        elif tool == "amp":
            # JSON format
            data = json.loads(path.read_text(encoding="utf-8"))
            messages = data.get("messages", [])
            for msg in messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        return content[:80]
    except Exception:
        pass
    return ""


def get_current_session_path(
    tool: str,
    project_path: Optional[Path] = None,
) -> tuple[Path, str]:
    """Auto-detect current session file and UUID.

    Returns (session_path, session_uuid).

    Selection logic:
    1. If exactly one candidate session exists, return it
    2. If multiple candidates exist, raise AmbiguousSessionError with candidate list
    3. If no candidates exist, raise NoSessionFoundError

    Does NOT default to "most recently modified" when ambiguous.
    """
    # Normalize tool name (claude-code -> claude)
    provider = _tool_to_provider(tool)
    paths = _get_session_paths(provider, base_path=project_path)

    if not paths:
        raise NoSessionFoundError(f"No {tool} session files found")

    # Extract UUIDs and build candidate list
    candidates = []
    for path in paths:
        uuid = _extract_uuid_from_filename(path.name, provider)
        if uuid:
            context = _get_first_content_line(path, provider)
            candidates.append({
                "uuid": uuid,
                "path": path,
                "last_modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
                "context_snippet": context,
            })

    if not candidates:
        raise NoSessionFoundError(f"No valid {tool} session files found")

    if len(candidates) == 1:
        return candidates[0]["path"], candidates[0]["uuid"]

    # Multiple candidates - build helpful error message
    msg_lines = [f"Multiple {tool} sessions found. Please specify --usage-session-id:"]
    for c in candidates[:5]:  # Show top 5
        snippet = c["context_snippet"][:40] + "..." if len(c["context_snippet"]) > 40 else c["context_snippet"]
        msg_lines.append(f"  {c['uuid']}: {snippet or '(no content preview)'}")
    if len(candidates) > 5:
        msg_lines.append(f"  ... and {len(candidates) - 5} more")

    raise AmbiguousSessionError("\n".join(msg_lines), candidates)


def _tool_to_provider(tool: str) -> str:
    """Map tool name to provider name for session parsing."""
    mapping = {
        "claude-code": "claude",
        "claude": "claude",
        "codex": "codex",
        "amp": "amp",
    }
    return mapping.get(tool.lower(), tool.lower())


def get_session_token_count(path: Path, tool: str) -> int:
    """Compute current cumulative token count for a session file."""
    provider = _tool_to_provider(tool)
    totals = parse_usage_from_source(provider, path)
    return totals.total_tokens or 0


def get_session_token_count_by_uuid(
    uuid: str,
    tool: str,
    base_path: Optional[Path] = None,
) -> int:
    """Compute aggregate token count across all files for a UUID.

    For Codex, a single UUID may span multiple rollout-*.jsonl files (resumes).
    This function finds all matching files and aggregates their token counts.
    """
    provider = _tool_to_provider(tool)
    paths = _get_session_paths(provider, base_path=base_path)

    total = 0
    for path in paths:
        file_uuid = _extract_uuid_from_filename(path.name, provider)
        if file_uuid and file_uuid.lower() == uuid.lower():
            totals = parse_usage_from_source(provider, path)
            total += totals.total_tokens or 0

    return total


def list_sessions(
    tool: str,
    limit: int = 10,
    base_path: Optional[Path] = None,
) -> list[dict]:
    """List candidate sessions for discovery/debugging.

    Returns list of {uuid, path, last_modified, tokens_so_far, context_snippet}.
    """
    provider = _tool_to_provider(tool)
    paths = _get_session_paths(provider, base_path=base_path)

    results = []
    for path in paths[:limit * 2]:  # Check more files to handle duplicates
        uuid = _extract_uuid_from_filename(path.name, provider)
        if not uuid:
            continue

        try:
            totals = parse_usage_from_source(provider, path)
            tokens = totals.total_tokens or 0
        except Exception:
            tokens = 0

        context = _get_first_content_line(path, provider)

        results.append({
            "uuid": uuid,
            "path": path,
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
            "tokens_so_far": tokens,
            "context_snippet": context,
        })

        if len(results) >= limit:
            break

    return results

