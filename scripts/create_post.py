#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BRAZIL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


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


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_post(title: str, tags: list[str], created_at: datetime) -> str:
    tag_text = ", ".join(f'"{toml_escape(tag)}"' for tag in tags)
    return "\n".join(
        [
            "+++",
            f'title = "{toml_escape(title)}"',
            f'date = "{created_at.isoformat(timespec="seconds")}"',
            "draft = true",
            f"tags = [{tag_text}]",
            "+++",
            "",
            "",
        ]
    )


def create_post(
    title: str,
    tags: list[str],
    repo_root: str | Path,
    created_at: datetime | None = None,
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
    output_file.write_text(build_post(title, tags, current_time), encoding="utf-8")
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
        tags = parse_tags(input("Tags (comma-separated, optional): "))
        output_file = create_post(title, tags, args.repo_root)
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
