#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shlex
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from create_post import BRAZIL_TIMEZONE, normalize_slug, toml_escape  # noqa: E402

# Values stored in front matter (English, see layouts/estante/list.html) paired
# with the label shown while picking.
KINDS = [
    ("series", "Série"),
    ("movie", "Filme"),
    ("book", "Livro"),
    ("game", "Jogo"),
    ("comic", "Quadrinho"),
]
STATUSES = [
    ("in-progress", "Em andamento"),
    ("concluded", "Concluído"),
    ("abandoned", "Abandonado"),
]
COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def select_one_fallback(prompt: str, options: list[tuple[str, str]]) -> str:
    print(f"{prompt}:")
    for index, (value, label) in enumerate(options, start=1):
        print(f"  {index}) {label} ({value})")
    while True:
        raw = input("Select by number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        print(f"Type a number between 1 and {len(options)}.")


def select_one(prompt: str, options: list[tuple[str, str]]) -> str:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return select_one_fallback(prompt, options)

    import curses

    def run(stdscr: "curses._CursesWindow") -> str | None:
        curses.curs_set(0)
        cursor = 0

        while True:
            stdscr.erase()
            stdscr.addstr(0, 0, f"{prompt} (↑/↓ move, enter confirm)")
            for row, (value, label) in enumerate(options):
                pointer = "❯" if row == cursor else " "
                try:
                    stdscr.addstr(row + 1, 0, f"{pointer} {label} ({value})")
                except curses.error:
                    pass

            stdscr.refresh()
            key = stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                cursor = (cursor - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                cursor = (cursor + 1) % len(options)
            elif key in (curses.KEY_ENTER, ord("\n"), ord("\r")):
                return options[cursor][0]
            elif key in (27, ord("q")):
                return None

    try:
        selected = curses.wrapper(run)
    except curses.error:
        return select_one_fallback(prompt, options)
    if selected is None:
        raise KeyboardInterrupt
    return selected


def parse_date(raw: str, default: date) -> date:
    raw = raw.strip()
    if not raw:
        return default
    return date.fromisoformat(raw)


def ask_date(prompt: str, default: date) -> date:
    while True:
        raw = input(f"{prompt} (YYYY-MM-DD, Enter for {default.isoformat()}): ")
        try:
            return parse_date(raw, default)
        except ValueError:
            print("Invalid date, use YYYY-MM-DD.")


def normalize_post_path(raw: str) -> str:
    """Turn a post URL or path (with or without domain/trailing slash) into
    the content path used by site.GetPage, e.g. /posts/2026/10/02/slug."""
    path = raw.strip()
    if "://" in path:
        path = "/" + path.split("://", 1)[1].split("/", 1)[-1]
    path = "/" + path.strip("/")
    return "" if path == "/" else path


def post_exists(repo_root: str | Path, post: str) -> bool:
    base = Path(repo_root) / "content" / post.strip("/")
    return (base / "index.md").is_file() or base.with_suffix(".md").is_file()


def ask_post(repo_root: str | Path) -> str:
    while True:
        raw = input("Post about it (e.g. /posts/2026/10/02/slug, optional): ")
        post = normalize_post_path(raw)
        if not post or post_exists(repo_root, post):
            return post
        print(f"No post found at content{post}/, try again or press Enter to skip.")


def parse_cover_path(raw: str) -> Path | None:
    """Accept a path typed or dragged into the terminal (quoted or with
    backslash-escaped spaces)."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        parts = shlex.split(raw)
    except ValueError:
        parts = [raw]
    return Path(" ".join(parts)).expanduser()


def ask_cover() -> Path | None:
    while True:
        cover = parse_cover_path(
            input("Cover image path (drag the file here, optional): ")
        )
        if cover is None:
            return None
        if not cover.is_file():
            print(f"File not found: {cover}")
        elif cover.suffix.lower() not in COVER_EXTENSIONS:
            print(f"Unsupported image type, use one of {', '.join(sorted(COVER_EXTENSIONS))}.")
        else:
            return cover


def build_item(
    title: str,
    kind: str,
    status: str,
    start_date: date,
    end_date: date | None = None,
    post: str = "",
) -> str:
    lines = [
        "+++",
        f'title = "{toml_escape(title)}"',
        f'kind = "{kind}"',
        f'status = "{status}"',
        f"startDate = {start_date.isoformat()}",
    ]
    if end_date:
        lines.append(f"endDate = {end_date.isoformat()}")
    if post:
        lines.append(f'post = "{toml_escape(post)}"')
    lines += ["+++", ""]
    return "\n".join(lines)


def create_shelf_item(
    title: str,
    kind: str,
    status: str,
    repo_root: str | Path,
    start_date: date,
    end_date: date | None = None,
    post: str = "",
    cover: Path | None = None,
    overwrite: bool = False,
) -> Path:
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")
    if kind not in {value for value, _ in KINDS}:
        raise ValueError(f"Unknown kind: {kind}")
    if status not in {value for value, _ in STATUSES}:
        raise ValueError(f"Unknown status: {status}")
    if status == "in-progress":
        end_date = None
    if end_date and end_date < start_date:
        raise ValueError("End date cannot be before the start date")
    if post and status != "concluded":
        raise ValueError("Only concluded works can link to a post")

    output_dir = Path(repo_root) / "content" / "estante" / normalize_slug(title)
    output_file = output_dir / "index.md"

    if output_file.exists() and not overwrite:
        raise FileExistsError(f"The target work already exists: {output_file}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        build_item(title, kind, status, start_date, end_date, post), encoding="utf-8"
    )
    if cover:
        for old_cover in output_dir.glob("cover.*"):
            old_cover.unlink()
        shutil.copyfile(cover, output_dir / f"cover{cover.suffix.lower()}")
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a work to the shelf.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root where the work will be created",
    )
    args = parser.parse_args()

    try:
        title = input("Title: ")
        kind = select_one("Kind", KINDS)
        status = select_one("Status", STATUSES)
        print(f"Kind: {kind} · Status: {status}")

        today = datetime.now(BRAZIL_TIMEZONE).date()
        start_date = ask_date("Start date", today)
        end_date = None
        if status != "in-progress":
            while True:
                end_date = ask_date("End date", today)
                if end_date >= start_date:
                    break
                print("End date cannot be before the start date.")

        post = ask_post(args.repo_root) if status == "concluded" else ""
        cover = ask_cover()

        options = dict(
            start_date=start_date, end_date=end_date, post=post, cover=cover
        )
        try:
            output_file = create_shelf_item(
                title, kind, status, args.repo_root, **options
            )
        except FileExistsError as exc:
            answer = input(f"{exc} Overwrite? (y/N): ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Shelf item creation cancelled.", file=sys.stderr)
                return 1
            output_file = create_shelf_item(
                title, kind, status, args.repo_root, overwrite=True, **options
            )
    except (EOFError, KeyboardInterrupt):
        print("\nShelf item creation cancelled.", file=sys.stderr)
        return 1
    except (FileExistsError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Added to the shelf at {output_file}")
    if not cover:
        print("No cover yet: add a cover.* image to that folder.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
