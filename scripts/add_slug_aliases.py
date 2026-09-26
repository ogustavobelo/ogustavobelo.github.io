#!/usr/bin/env python3
"""Add `aliases = ["/{slug}/"]` to posts imported from Bear so old URLs keep working."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RESERVED_SLUGS = {"about", "tags", "posts", "blog", "page", "css", "js", "lib", "svg"}
ALIASES_RE = re.compile(r"^aliases\s*=\s*(\[.*\])\s*$", re.MULTILINE)


def add_alias(text: str, slug: str) -> str | None:
    """Return the updated text, or None when nothing needs to change."""
    if not text.startswith("+++"):
        return None
    end = text.find("\n+++", 3)
    if end == -1:
        return None
    front, rest = text[: end + 1], text[end + 1 :]
    if not re.search(r"^bear_uid\s*=", front, re.MULTILINE):
        return None

    alias = f"/{slug}/"
    match = ALIASES_RE.search(front)
    if match:
        current = json.loads(match.group(1))
        if alias in current:
            return None
        line = f"aliases = {json.dumps([alias, *current], ensure_ascii=False)}"
        front = front[: match.start()] + line + front[match.end() :]
    else:
        line = f'aliases = ["{alias}"]\n'
        bear = re.search(r"^bear_uid\s*=", front, re.MULTILINE)
        front = front[: bear.start()] + line + front[bear.start() :]
    return front + rest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--dry-run", action="store_true", help="List the files that would change")
    args = parser.parse_args(argv)

    changed = 0
    for path in sorted(Path(args.repo_root).glob("content/posts/*/*/*/*/index.md")):
        slug = path.parent.name
        with path.open(encoding="utf-8", newline="") as fh:
            updated = add_alias(fh.read(), slug)
        if updated is None:
            continue
        if slug in RESERVED_SLUGS:
            print(f"Error: slug '{slug}' collides with a site section ({path})", file=sys.stderr)
            return 1
        if not args.dry_run:
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write(updated)
        print(f"{'Would update' if args.dry_run else 'Updated'}: {path}")
        changed += 1

    print(f"{changed} file(s) {'to update' if args.dry_run else 'updated'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
