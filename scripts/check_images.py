#!/usr/bin/env python3
"""Pre-commit check: images under content/ must be WebP and reasonably small,
so heavy files never reach the Git history (see .githooks/pre-commit)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert_images import CONVERTIBLE_EXTENSIONS  # noqa: E402

IMAGE_EXTENSIONS = CONVERTIBLE_EXTENSIONS | {".webp", ".gif", ".avif"}
# The largest converted image is ~320 KB; anything bigger is worth a look.
MAX_IMAGE_SIZE = 500 * 1024


def find_problems(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        suffix = path.suffix.lower()
        if "content" not in path.parts or suffix not in IMAGE_EXTENSIONS or not path.is_file():
            continue
        if suffix in CONVERTIBLE_EXTENSIONS:
            problems.append(f"{path}: convert it to WebP")
        elif path.stat().st_size > MAX_IMAGE_SIZE:
            problems.append(
                f"{path}: {path.stat().st_size / 1024:.0f} KB, above the "
                f"{MAX_IMAGE_SIZE // 1024} KB limit"
            )
    return problems


def main() -> int:
    problems = find_problems([Path(arg) for arg in sys.argv[1:]])
    if not problems:
        return 0
    print("Images not ready to commit:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(
        "\nRun `python3 scripts/convert_images.py <files>` and stage the result,"
        "\nor commit with --no-verify to skip this check.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
