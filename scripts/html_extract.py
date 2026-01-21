#!/usr/bin/env python3
"""
Lightweight HTML extraction utilities for Reality Check.

Goals:
- Extract a reasonable title and publication date when present
- Extract main article text (prefer <article> / <main> / common content containers)
- Keep dependencies light (BeautifulSoup + stdlib only)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup


_META_TITLE_SELECTORS: tuple[tuple[str, str], ...] = (
    ("property", "og:title"),
    ("name", "twitter:title"),
    ("name", "title"),
)

_META_DATE_SELECTORS: tuple[tuple[str, str], ...] = (
    ("property", "article:published_time"),
    ("property", "article:published"),
    ("property", "og:published_time"),
    ("name", "date"),
    ("name", "pubdate"),
    ("name", "timestamp"),
    ("itemprop", "datePublished"),
)

_CONTENT_CLASS_RE = re.compile(
    r"(entry[-_ ]content|entry[-_ ]body|post[-_ ]content|post[-_ ]body|article[-_ ]content|content|main|body)",
    re.IGNORECASE,
)

_NOISE_TAGS = ("script", "style", "noscript", "svg", "canvas", "form")
_NOISE_LANDMARK_TAGS = ("nav", "footer", "header", "aside")


@dataclass(frozen=True)
class ExtractedHTML:
    title: Optional[str]
    published: Optional[str]
    text: str
    headings: list[str]

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def _first_meta_content(soup: BeautifulSoup, *, attr: str, value: str) -> Optional[str]:
    tag = soup.find("meta", attrs={attr: value})
    if not tag:
        return None
    content = tag.get("content")
    if not content:
        return None
    content = str(content).strip()
    return content or None


def _normalize_date(value: str) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw

    candidate = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    try:
        dt = datetime.fromisoformat(candidate)
        return dt.isoformat()
    except ValueError:
        return raw


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    for attr, value in _META_TITLE_SELECTORS:
        title = _first_meta_content(soup, attr=attr, value=value)
        if title:
            return title

    if soup.title and soup.title.string:
        title = str(soup.title.string).strip()
        if title:
            return title

    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text:
            return text

    return None


def _extract_date_from_json_ld(soup: BeautifulSoup) -> Optional[str]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        payload = script.string
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except Exception:
            continue

        items: list[Any]
        if isinstance(data, list):
            items = data
        else:
            items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ("datePublished", "dateCreated", "dateModified"):
                value = item.get(key)
                if isinstance(value, str):
                    normalized = _normalize_date(value)
                    if normalized:
                        return normalized
    return None


def _extract_published_date(soup: BeautifulSoup) -> Optional[str]:
    for attr, value in _META_DATE_SELECTORS:
        date_str = _first_meta_content(soup, attr=attr, value=value)
        normalized = _normalize_date(date_str) if date_str else None
        if normalized:
            return normalized

    json_ld_date = _extract_date_from_json_ld(soup)
    if json_ld_date:
        return json_ld_date

    time_tag = soup.find("time")
    if time_tag:
        dt = time_tag.get("datetime") or time_tag.get("content") or time_tag.get("title")
        if isinstance(dt, str) and dt.strip():
            normalized = _normalize_date(dt)
            if normalized:
                return normalized
        text = time_tag.get_text(" ", strip=True)
        normalized = _normalize_date(text)
        if normalized:
            return normalized

    abbr = soup.find(["abbr", "span"], class_=re.compile(r"(published|date|time)", re.I))
    if abbr:
        dt = abbr.get("title") or abbr.get("datetime") or abbr.get("content")
        if isinstance(dt, str) and dt.strip():
            normalized = _normalize_date(dt)
            if normalized:
                return normalized
        text = abbr.get_text(" ", strip=True)
        normalized = _normalize_date(text)
        if normalized:
            return normalized

    return None


def _strip_noise(soup: BeautifulSoup) -> None:
    for tag_name in _NOISE_TAGS + _NOISE_LANDMARK_TAGS:
        for node in soup.find_all(tag_name):
            node.decompose()


def _score_candidate(node: Any) -> int:
    try:
        text = node.get_text(" ", strip=True)
    except Exception:
        return 0
    return len(text or "")


def _select_main_container(soup: BeautifulSoup) -> Any:
    candidates: list[Any] = []

    for tag_name in ("article", "main"):
        candidates.extend(soup.find_all(tag_name))

    for tag_name in ("div", "section"):
        for node in soup.find_all(tag_name):
            class_list = node.get("class") or []
            class_str = " ".join(class_list) if isinstance(class_list, list) else str(class_list)
            node_id = str(node.get("id") or "")
            if _CONTENT_CLASS_RE.search(class_str) or _CONTENT_CLASS_RE.search(node_id):
                candidates.append(node)

    if candidates:
        return max(candidates, key=_score_candidate)

    return soup.body or soup


def _extract_headings(container: Any) -> list[str]:
    headings: list[str] = []
    for tag in container.find_all(["h1", "h2"]):
        text = tag.get_text(" ", strip=True)
        if text:
            headings.append(text)
    return headings


def _extract_text(container: Any) -> str:
    raw = container.get_text("\n", strip=True)
    lines: list[str] = []
    for line in raw.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def extract_html(html: str) -> ExtractedHTML:
    """
    Extract title, publication date, and main text from an HTML document.

    This is intentionally heuristic and lightweight; it is not a full readability implementation.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)
    published = _extract_published_date(soup)

    _strip_noise(soup)
    container = _select_main_container(soup)
    headings = _extract_headings(container)
    text = _extract_text(container)

    return ExtractedHTML(
        title=title,
        published=published,
        text=text,
        headings=headings,
    )


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract title/date/text from an HTML file")
    parser.add_argument("input", help="Path to HTML file, or '-' for stdin")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--max-chars", type=int, default=0, help="Truncate extracted text to N chars (0 = no limit)")

    args = parser.parse_args()

    try:
        html = _read_input(args.input)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: failed to read input: {e}", file=sys.stderr)
        return 2

    doc = extract_html(html)
    text = doc.text
    if args.max_chars and args.max_chars > 0:
        text = text[: args.max_chars]

    if args.format == "text":
        print(text)
        return 0

    payload = asdict(doc)
    payload["word_count"] = len(text.split())
    payload["text"] = text
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

