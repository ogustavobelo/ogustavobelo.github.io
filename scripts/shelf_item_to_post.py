#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from create_post import (  # noqa: E402
    BRAZIL_TIMEZONE,
    FRONT_MATTER_PATTERN,
    ask_post_details,
    create_post,
    normalize_slug,
)
from create_shelf_item import KINDS, ask_date, build_item, select_one  # noqa: E402


class ShelfWork(NamedTuple):
    path: Path
    title: str
    kind: str
    start_date: date


def list_in_progress(repo_root: str | Path) -> list[ShelfWork]:
    """In-progress works, latest startDate first, as the shelf lists them."""
    works: list[ShelfWork] = []
    for index_file in (Path(repo_root) / "content" / "estante").glob("*/*/*/index.md"):
        match = FRONT_MATTER_PATTERN.match(index_file.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            front_matter = tomllib.loads(match.group(1))
        except tomllib.TOMLDecodeError:
            continue
        if front_matter.get("status") != "in-progress":
            continue
        works.append(
            ShelfWork(
                index_file,
                str(front_matter.get("title", "")),
                str(front_matter.get("kind", "")),
                front_matter["startDate"],
            )
        )
    return sorted(works, key=lambda work: (work.start_date, work.title), reverse=True)


def find_cover(bundle: Path) -> Path | None:
    return next(bundle.glob("cover.*"), None) or next(bundle.glob("image.*"), None)


def convert_to_post(
    work: ShelfWork,
    repo_root: str | Path,
    *,
    title: str,
    tags: list[str],
    description: str = "",
    end_date: date,
    created_at: datetime | None = None,
) -> tuple[Path, Path]:
    """Create a draft post about the work, move its cover into the post bundle
    (so the image isn't duplicated) and mark the work as concluded, linking the
    post and pointing its cover at the moved image."""
    if end_date < work.start_date:
        raise ValueError("End date cannot be before the start date")

    cover = find_cover(work.path.parent)
    # Named after the post, like the other post images (e.g. widows-bay.png).
    image = f"{normalize_slug(title.strip())}{cover.suffix.lower()}" if cover else ""
    post_file = create_post(
        title,
        tags,
        repo_root,
        created_at,
        description,
        image=image,
        image_alt=title.strip(),
    )
    post_dir = post_file.parent
    post_path = "/" + post_dir.relative_to(Path(repo_root) / "content").as_posix()
    if cover:
        shutil.move(cover, post_dir / image)

    text = work.path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(text)
    body = text[match.end() :].lstrip("\n") if match else ""
    item = build_item(
        work.title,
        work.kind,
        "concluded",
        work.start_date,
        end_date,
        post=post_path,
        cover=f"{post_path}/{image}" if image else "",
    )
    work.path.write_text(item + body, encoding="utf-8")
    return post_file, work.path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn an in-progress shelf work into a draft post."
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root holding the shelf and the posts",
    )
    args = parser.parse_args()

    works = list_in_progress(args.repo_root)
    if not works:
        print("No in-progress works on the shelf.", file=sys.stderr)
        return 1

    kind_labels = dict(KINDS)
    try:
        selected = select_one(
            "Work",
            [
                (
                    str(work.path),
                    f"{work.title} · {kind_labels.get(work.kind, work.kind)}"
                    f" · since {work.start_date.isoformat()}",
                )
                for work in works
            ],
        )
        work = next(work for work in works if str(work.path) == selected)
        print(f"Work: {work.title}")

        title = input(f"Post title (Enter for {work.title}): ").strip() or work.title
        tags, description = ask_post_details(args.repo_root)

        today = datetime.now(BRAZIL_TIMEZONE).date()
        while True:
            end_date = ask_date("End date", max(today, work.start_date))
            if end_date >= work.start_date:
                break
            print("End date cannot be before the start date.")

        post_file, shelf_file = convert_to_post(
            work,
            args.repo_root,
            title=title,
            tags=tags,
            description=description,
            end_date=end_date,
        )
    except (EOFError, KeyboardInterrupt):
        print("\nConversion cancelled.", file=sys.stderr)
        return 1
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Created draft post at {post_file}")
    print(f"Marked as concluded at {shelf_file}")
    if "cover = " not in shelf_file.read_text(encoding="utf-8"):
        print("No cover found: add an image to the post and a cover path to the work.")
    print(
        "Write the post and set draft = false. Until then the production shelf"
        " shows the work without its link and cover."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
