#!/usr/bin/env python3
"""Convert a simple content calendar into a dated posting schedule.

Supported inputs:
- CSV with date, channel, topic, format, and notes columns. CSV rows may
  also use repeat_days and occurrences columns to expand a recurring post.
- Markdown tables using the same column names.
- Markdown list lines in the form:
  - 2026-11-03 | Instagram | Launch teaser | Reel | Final caption review

The result can be written as a Markdown schedule, a CSV schedule, or both.
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Post:
    """One scheduled content item."""

    scheduled_date: date
    channel: str
    topic: str
    format: str = ""
    notes: str = ""

    def sort_key(self) -> tuple[date, str, str]:
        return (self.scheduled_date, self.channel.casefold(), self.topic.casefold())


def clean(value: str | None) -> str:
    """Normalize a calendar field."""

    return " ".join((value or "").strip().split())


def parse_date(value: str, source: str) -> date:
    """Parse an ISO calendar date and provide a useful error."""

    value = clean(value)
    if not DATE_RE.match(value):
        raise ValueError(f"{source}: expected a YYYY-MM-DD date, got {value!r}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{source}: invalid date {value!r}") from exc


def expand_row(row: dict[str, str], source: str) -> list[Post]:
    """Expand one normalized calendar row into one or more posts."""

    base_date = parse_date(row.get("date", ""), source)
    repeat_days = clean(row.get("repeat_days", ""))
    occurrences = clean(row.get("occurrences", ""))

    interval = int(repeat_days) if repeat_days else 0
    count = int(occurrences) if occurrences else 1
    if interval < 0:
        raise ValueError(f"{source}: repeat_days cannot be negative")
    if count < 1:
        raise ValueError(f"{source}: occurrences must be at least 1")
    if count > 1 and interval == 0:
        raise ValueError(f"{source}: repeat_days is required when occurrences is above 1")

    return [
        Post(
            scheduled_date=base_date + timedelta(days=interval * index),
            channel=clean(row.get("channel", "")),
            topic=clean(row.get("topic", "")),
            format=clean(row.get("format", "")),
            notes=clean(row.get("notes", "")),
        )
        for index in range(count)
    ]


def read_csv(path: Path) -> list[Post]:
    """Read and expand a CSV content calendar."""

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []

        normalized_fields = {clean(name).casefold(): name for name in reader.fieldnames if name}
        required = {"date", "channel", "topic"}
        missing = required - set(normalized_fields)
        if missing:
            raise ValueError(f"{path}: missing required CSV columns: {', '.join(sorted(missing))}")

        posts: list[Post] = []
        for line_number, raw_row in enumerate(reader, start=2):
            row = {
                clean(key).casefold(): clean(value)
                for key, value in raw_row.items()
                if key is not None
            }
            if not any(row.values()):
                continue
            posts.extend(expand_row(row, f"{path}:{line_number}"))
    return posts


def split_markdown_row(line: str) -> list[str]:
    """Split a Markdown table row or pipe-delimited list item."""

    value = line.strip()
    if value.startswith("- "):
        value = value[2:].strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [clean(part) for part in value.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    """Return whether a Markdown row is a table separator."""

    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def read_markdown(path: Path) -> list[Post]:
    """Read a Markdown table or simple pipe-delimited list."""

    posts: list[Post] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_number, line in enumerate(lines, start=1):
        if "|" not in line:
            continue
        cells = split_markdown_row(line)
        if is_separator_row(cells):
            continue
        if cells and cells[0].casefold() in {"date", "scheduled date"}:
            continue
        if len(cells) < 3 or not DATE_RE.match(cells[0]):
            continue

        row = {
            "date": cells[0],
            "channel": cells[1] if len(cells) > 1 else "",
            "topic": cells[2] if len(cells) > 2 else "",
            "format": cells[3] if len(cells) > 3 else "",
            "notes": cells[4] if len(cells) > 4 else "",
        }
        posts.extend(expand_row(row, f"{path}:{line_number}"))

    return posts


def read_calendar(path: Path) -> list[Post]:
    """Read a supported calendar file and return sorted posts."""

    suffix = path.suffix.casefold()
    if suffix == ".csv":
        posts = read_csv(path)
    elif suffix in {".md", ".markdown", ".txt"}:
        posts = read_markdown(path)
    else:
        raise ValueError("Input must be a .csv, .md, .markdown, or .txt file")

    if not posts:
        raise ValueError(f"No dated content items found in {path}")
    return sorted(posts, key=lambda post: post.sort_key())


def escape_markdown(value: str) -> str:
    """Escape pipe characters for a Markdown table."""

    return value.replace("|", "\\|")


def render_markdown(posts: Iterable[Post]) -> str:
    """Render posts as a Markdown posting schedule."""

    rows = [
        "# Posting Schedule",
        "",
        "| Date | Channel | Topic | Format | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for post in posts:
        values = [
            post.scheduled_date.isoformat(),
            post.channel,
            post.topic,
            post.format,
            post.notes,
        ]
        rows.append("| " + " | ".join(escape_markdown(value) for value in values) + " |")
    return "\n".join(rows) + "\n"


def write_csv(posts: Iterable[Post], path: Path) -> None:
    """Write posts as a CSV schedule."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "channel", "topic", "format", "notes"])
        for post in posts:
            writer.writerow(
                [
                    post.scheduled_date.isoformat(),
                    post.channel,
                    post.topic,
                    post.format,
                    post.notes,
                ]
            )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Build a dated posting schedule from a Markdown or CSV content calendar."
    )
    parser.add_argument("input", type=Path, help="Input .csv or Markdown calendar")
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Write the schedule as Markdown to this path",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        help="Write the schedule as CSV to this path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line program."""

    args = build_parser().parse_args(argv)
    try:
        posts = read_calendar(args.input)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    markdown = render_markdown(posts)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")

    if args.csv_output:
        write_csv(posts, args.csv_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
