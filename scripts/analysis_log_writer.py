#!/usr/bin/env python3
"""Update in-document Analysis Log sections in analysis markdown files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional


def _parse_iso8601(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _format_date_for_table(entry: dict) -> str:
    dt = _parse_iso8601(entry.get("started_at") or entry.get("created_at") or entry.get("completed_at"))
    if not dt:
        return "?"
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_duration(entry: dict) -> str:
    duration = entry.get("duration_seconds")
    if duration is None:
        return "?"
    try:
        seconds = int(duration)
    except Exception:
        return "?"
    if seconds < 0:
        return "?"
    minutes, sec = divmod(seconds, 60)
    return f"{minutes}m{sec}s"


def _format_tokens(entry: dict) -> str:
    total = entry.get("total_tokens")
    if total is None:
        tokens_in = entry.get("tokens_in")
        tokens_out = entry.get("tokens_out")
        if isinstance(tokens_in, int) and isinstance(tokens_out, int):
            total = tokens_in + tokens_out
    if total is None:
        return "?"
    try:
        total_int = int(total)
    except Exception:
        return "?"
    return f"{total_int:,}"


def _format_cost(entry: dict) -> str:
    cost = entry.get("cost_usd")
    if cost is None:
        return "?"
    try:
        cost_f = float(cost)
    except Exception:
        return "?"
    return f"${cost_f:.4f}"


def _sanitize_cell(value: Any, max_len: int = 80) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "\\|")
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def _format_row(entry: dict) -> str:
    pass_num = entry.get("pass")
    try:
        pass_int = int(pass_num)
    except Exception:
        pass_int = "?"

    date_str = _format_date_for_table(entry)
    tool = _sanitize_cell(entry.get("tool") or "?", max_len=24)
    model = _sanitize_cell(entry.get("model") or "?", max_len=32)
    duration = _format_duration(entry)
    tokens = _format_tokens(entry)
    cost = _format_cost(entry)
    notes = _sanitize_cell(entry.get("notes") or "", max_len=80)

    return f"| {pass_int} | {date_str} | {tool} | {model} | {duration} | {tokens} | {cost} | {notes} |"


def upsert_analysis_log_section(content: str, entry: dict) -> str:
    """Ensure the content contains an Analysis Log section and upsert the pass row."""
    lines = content.splitlines()

    pass_num = entry.get("pass")
    try:
        pass_int = int(pass_num)
    except Exception:
        pass_int = None

    row = _format_row(entry)

    # Find heading
    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == "## analysis log":
            heading_idx = i
            break

    if heading_idx is None:
        # Append a new section.
        section_lines = [
            "",
            "---",
            "",
            "## Analysis Log",
            "",
            "| Pass | Date | Tool | Model | Duration | Tokens | Cost | Notes |",
            "|------|------|------|-------|----------|--------|------|-------|",
            row,
            "",
            "### Revision Notes",
            "",
        ]
        if pass_int is not None and (entry.get("notes") or "").strip():
            section_lines.append(f"**Pass {pass_int}**: {_sanitize_cell(entry.get('notes'), max_len=160)}")
        else:
            section_lines.append("**Pass 1**: [What changed in this pass? What was added/updated and why?]")
        return "\n".join(lines + section_lines).rstrip() + "\n"

    # Find the table header after the heading.
    header_idx = None
    for i in range(heading_idx + 1, min(len(lines), heading_idx + 50)):
        if re.match(r"^\|\s*Pass\s*\|\s*Date\s*\|", lines[i], re.IGNORECASE):
            header_idx = i
            break

    if header_idx is None or header_idx + 1 >= len(lines):
        # Malformed section; fall back to append a fresh one.
        return upsert_analysis_log_section(content.replace(lines[heading_idx], "## Analysis Log (legacy)"), entry)

    sep_idx = header_idx + 1

    # Collect existing row lines.
    row_start = sep_idx + 1
    row_end = row_start
    while row_end < len(lines) and lines[row_end].lstrip().startswith("|"):
        row_end += 1

    existing_rows = lines[row_start:row_end]

    updated_rows: list[tuple[int, str]] = []
    other_rows: list[str] = []
    found = False

    for r in existing_rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if not cells:
            other_rows.append(r)
            continue
        try:
            existing_pass = int(cells[0])
        except Exception:
            other_rows.append(r)
            continue

        if pass_int is not None and existing_pass == pass_int:
            updated_rows.append((existing_pass, row))
            found = True
        else:
            updated_rows.append((existing_pass, r))

    if pass_int is not None and not found:
        updated_rows.append((pass_int, row))

    updated_rows_sorted = [r for _, r in sorted(updated_rows, key=lambda t: t[0])]
    new_table_rows = updated_rows_sorted + other_rows

    new_lines = lines[:row_start] + new_table_rows + lines[row_end:]

    # Upsert revision note line if present and we have notes.
    notes_text = (entry.get("notes") or "").strip()
    if pass_int is not None and notes_text:
        rev_idx = None
        for i, line in enumerate(new_lines):
            if line.strip().lower() == "### revision notes":
                rev_idx = i
                break
        if rev_idx is None:
            # Add revision notes after the table.
            insert_at = row_start + len(new_table_rows)
            new_lines = (
                new_lines[:insert_at]
                + ["", "### Revision Notes", "", f"**Pass {pass_int}**: {_sanitize_cell(notes_text, max_len=160)}"]
                + new_lines[insert_at:]
            )
        else:
            # Replace or insert the line for this pass.
            pass_pat = re.compile(rf"^\*\*Pass\s+{pass_int}\*\*:", re.IGNORECASE)
            replaced = False
            j = rev_idx + 1
            while j < len(new_lines) and new_lines[j].strip() != "" and not new_lines[j].startswith("## "):
                if pass_pat.match(new_lines[j].strip()):
                    new_lines[j] = f"**Pass {pass_int}**: {_sanitize_cell(notes_text, max_len=160)}"
                    replaced = True
                    break
                j += 1
            if not replaced:
                new_lines.insert(rev_idx + 2, f"**Pass {pass_int}**: {_sanitize_cell(notes_text, max_len=160)}")

    return "\n".join(new_lines).rstrip() + "\n"

