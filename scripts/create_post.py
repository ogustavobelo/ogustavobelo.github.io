#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
import tomllib
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BRAZIL_TIMEZONE = ZoneInfo("America/Sao_Paulo")

FRONT_MATTER_PATTERN = re.compile(r"^\+\+\+\n(.*?\n)\+\+\+", re.DOTALL)


def normalize_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = ascii_title.lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "post"


def parse_tags(raw_tags: str) -> list[str]:
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def collect_tag_counts(repo_root: str | Path) -> list[tuple[str, int]]:
    posts_dir = Path(repo_root) / "content" / "posts"
    counts: Counter[str] = Counter()

    for index_file in posts_dir.glob("**/*.md"):
        text = index_file.read_text(encoding="utf-8")
        match = FRONT_MATTER_PATTERN.match(text)
        if not match:
            continue
        try:
            front_matter = tomllib.loads(match.group(1))
        except tomllib.TOMLDecodeError:
            continue
        for tag in front_matter.get("tags", []):
            tag = str(tag).strip()
            if tag:
                counts[tag] += 1

    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def merge_tags(selected: list[str], new: list[str]) -> list[str]:
    merged: list[str] = []
    for tag in [*selected, *new]:
        if tag not in merged:
            merged.append(tag)
    return merged


def select_tags_fallback(options: list[tuple[str, int]]) -> list[str]:
    print("Existing tags (most used first):")
    for index, (tag, count) in enumerate(options, start=1):
        print(f"  {index}) {tag} ({count})")
    raw = input("Select tags by number (e.g. 1,3,5), optional: ")

    selected: list[str] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk or not chunk.isdigit():
            continue
        position = int(chunk)
        if 1 <= position <= len(options):
            tag = options[position - 1][0]
            if tag not in selected:
                selected.append(tag)
    return selected


def select_tags(options: list[tuple[str, int]]) -> list[str]:
    if not options:
        return []

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return select_tags_fallback(options)

    import curses

    def run(stdscr: "curses._CursesWindow") -> list[str]:
        curses.curs_set(0)
        cursor = 0
        checked = [False] * len(options)

        while True:
            stdscr.erase()
            stdscr.addstr(0, 0, "Select tags (↑/↓ move, space toggle, enter confirm)")
            height, _ = stdscr.getmaxyx()
            visible_rows = max(height - 2, 1)
            top = max(0, min(cursor - visible_rows // 2, len(options) - visible_rows))
            top = max(top, 0)

            for row, index in enumerate(range(top, min(top + visible_rows, len(options)))):
                tag, count = options[index]
                marker = "◉" if checked[index] else "◯"
                pointer = "❯" if index == cursor else " "
                line = f"{pointer} {marker} {tag} ({count})"
                try:
                    stdscr.addstr(row + 1, 0, line)
                except curses.error:
                    pass

            stdscr.refresh()
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                cursor = (cursor - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                cursor = (cursor + 1) % len(options)
            elif key == ord(" "):
                checked[cursor] = not checked[cursor]
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                break
            elif key in (27, ord("q")):
                break

        return [tag for (tag, _), is_checked in zip(options, checked) if is_checked]

    try:
        return curses.wrapper(run)
    except curses.error:
        return select_tags_fallback(options)


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_post(
    title: str, tags: list[str], created_at: datetime, description: str = ""
) -> str:
    tag_text = ", ".join(f'"{toml_escape(tag)}"' for tag in tags)
    lines = [
        "+++",
        f'title = "{toml_escape(title)}"',
        f'date = "{created_at.isoformat(timespec="seconds")}"',
        "draft = true",
        f"tags = [{tag_text}]",
    ]
    description = description.strip()
    if description:
        # Used as the page's meta/OG/JSON-LD description; falls back to the
        # post's own summary when left unset. See the content-authoring skill.
        lines.append(f'description = "{toml_escape(description)}"')
    lines += ["+++", "", ""]
    return "\n".join(lines)


def create_post(
    title: str,
    tags: list[str],
    repo_root: str | Path,
    created_at: datetime | None = None,
    description: str = "",
) -> Path:
    title = title.strip()
    if not title:
        raise ValueError("Post title cannot be empty")

    current_time = created_at or datetime.now(BRAZIL_TIMEZONE)
    current_time = current_time.astimezone(BRAZIL_TIMEZONE)
    slug = normalize_slug(title)
    output_dir = (
        Path(repo_root)
        / "content"
        / "posts"
        / f"{current_time.year:04d}"
        / f"{current_time.month:02d}"
        / f"{current_time.day:02d}"
        / slug
    )
    output_file = output_dir / "index.md"

    if output_file.exists():
        raise FileExistsError(f"The target post already exists: {output_file}")

    output_dir.mkdir(parents=True, exist_ok=False)
    output_file.write_text(
        build_post(title, tags, current_time, description), encoding="utf-8"
    )
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new Hugo post bundle.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root where the post will be created",
    )
    args = parser.parse_args()

    try:
        title = input("Post title: ")

        tag_options = collect_tag_counts(args.repo_root)
        selected_tags = select_tags(tag_options)
        if selected_tags:
            print(f"Selected: {', '.join(selected_tags)}")

        new_tags = parse_tags(input("New tags (comma-separated, optional): "))
        tags = merge_tags(selected_tags, new_tags)

        description = input(
            "Description for search/social previews (optional, press Enter to"
            " derive it from the post's own text later): "
        )
        output_file = create_post(title, tags, args.repo_root, description=description)
    except (EOFError, KeyboardInterrupt):
        print("\nPost creation cancelled.", file=sys.stderr)
        return 1
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Created draft post at {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
