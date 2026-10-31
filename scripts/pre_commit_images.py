#!/usr/bin/env python3
"""Pre-commit step (see .githooks/pre-commit): converts staged PNG/JPEG images
under content/ to WebP and stages the result, so heavy files never reach the
Git history. Oversized images only produce a warning."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert_images import CONVERTIBLE_EXTENSIONS, convert_image, format_size  # noqa: E402

IMAGE_EXTENSIONS = CONVERTIBLE_EXTENSIONS | {".webp", ".gif", ".avif"}
# The largest converted image is ~320 KB; anything bigger is worth a look.
MAX_IMAGE_SIZE = 500 * 1024


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def staged_images() -> list[Path]:
    """Added, copied, modified or renamed images under content/ in this commit."""
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0")
    paths = [Path(name) for name in names if name]
    return [
        path
        for path in paths
        if "content" in path.parts and path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file()
    ]


def main() -> int:
    for path in staged_images():
        if path.suffix.lower() in CONVERTIBLE_EXTENSIONS:
            result = convert_image(path.resolve())
            if result.target is None:
                print(f"pre-commit: kept {path} (WebP would be larger)")
                continue
            target = result.target.relative_to(Path.cwd())
            git("add", "-A", "--", str(path), str(target), *map(str, result.references))
            print(
                f"pre-commit: {path} → {target.name} "
                f"({format_size(result.size_before)} → {format_size(result.size_after)})"
            )
            path = target
        if path.stat().st_size > MAX_IMAGE_SIZE:
            print(
                f"pre-commit: warning, {path} has {format_size(path.stat().st_size)}, "
                f"above {format_size(MAX_IMAGE_SIZE)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
