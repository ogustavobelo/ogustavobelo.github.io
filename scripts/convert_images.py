#!/usr/bin/env python3

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageOps

CONVERTIBLE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
# High enough to be visually indistinguishable from the source, while method 6
# spends the most encoder effort on squeezing the file.
LOSSY_QUALITY = 90
METHOD = 6


class Conversion(NamedTuple):
    source: Path
    target: Path | None
    size_before: int
    size_after: int
    references: list[Path] = []


def encode_webp(source: Path) -> bytes:
    """Encode the image as WebP, keeping its color profile and transparency.
    PNGs (screenshots, illustrations) are also tried lossless, keeping
    whichever output is smaller."""
    with Image.open(source) as original:
        icc_profile = original.info.get("icc_profile")
        image = ImageOps.exif_transpose(original)
        has_alpha = image.mode in {"RGBA", "LA", "PA"} or (
            image.mode == "P" and "transparency" in image.info
        )
        image = image.convert("RGBA" if has_alpha else "RGB")

    options = {"method": METHOD}
    if icc_profile:
        options["icc_profile"] = icc_profile

    candidates = [(False, LOSSY_QUALITY)]
    if source.suffix.lower() == ".png":
        candidates.append((True, 100))

    best = b""
    for lossless, quality in candidates:
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", lossless=lossless, quality=quality, **options)
        if not best or buffer.tell() < len(best):
            best = buffer.getvalue()
    return best


def convert_to_webp(source: Path, destination: Path | None = None) -> Path:
    """Write the WebP version of source (next to it by default) and return its path."""
    destination = destination or source.with_suffix(".webp")
    destination.write_bytes(encode_webp(source))
    return destination


def update_references(source: Path, target: Path, content_dir: Path) -> list[Path]:
    """Point Markdown references to source at target: bare file names in the
    same bundle (images = [...], image shortcodes) and absolute site paths
    anywhere in content (shelf covers). Returns the files changed."""
    absolute = "/" + source.relative_to(content_dir).as_posix()
    absolute_pattern = re.compile(re.escape(absolute) + r"(?![\w.-])")
    bare_pattern = re.compile(r"(?<![\w./-])" + re.escape(source.name) + r"(?![\w.-])")
    absolute_target = absolute[: -len(source.name)] + target.name

    changed: list[Path] = []
    for markdown in content_dir.glob("**/*.md"):
        text = markdown.read_text(encoding="utf-8")
        updated = absolute_pattern.sub(absolute_target, text)
        if markdown.parent == source.parent:
            updated = bare_pattern.sub(target.name, updated)
        if updated != text:
            markdown.write_text(updated, encoding="utf-8")
            changed.append(markdown)
    return changed


def find_content_dir(path: Path) -> Path | None:
    return next((parent for parent in path.parents if parent.name == "content"), None)


def collect_images(paths: list[Path]) -> list[Path]:
    images: set[Path] = set()
    for path in paths:
        candidates = path.rglob("*") if path.is_dir() else [path]
        images.update(
            candidate.resolve()
            for candidate in candidates
            if candidate.is_file() and candidate.suffix.lower() in CONVERTIBLE_EXTENSIONS
        )
    return sorted(images)


def convert_image(source: Path, *, keep_original: bool = False, dry_run: bool = False) -> Conversion:
    """Convert one image, update the references in its content folder and drop
    the original. Images that would grow as WebP are left untouched."""
    size_before = source.stat().st_size
    encoded = encode_webp(source)
    if len(encoded) >= size_before:
        return Conversion(source, None, size_before, size_before)

    target = source.with_suffix(".webp")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    references: list[Path] = []
    if not dry_run:
        target.write_bytes(encoded)
        content_dir = find_content_dir(source)
        if content_dir:
            references = update_references(source, target, content_dir)
        if not keep_original:
            source.unlink()
    return Conversion(source, target, size_before, len(encoded), references)


def format_size(size: int) -> str:
    return f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert PNG/JPEG images to WebP and update their references in content/."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Image files or folders to scan")
    parser.add_argument("--keep-original", action="store_true", help="Don't delete the source images")
    parser.add_argument("--dry-run", action="store_true", help="Only report the expected savings")
    args = parser.parse_args()

    missing = [path for path in args.paths if not path.exists()]
    if missing:
        print(f"Not found: {', '.join(map(str, missing))}", file=sys.stderr)
        return 1

    images = collect_images(args.paths)
    if not images:
        print("No PNG/JPEG images found.")
        return 0

    total_before = total_after = 0
    for source in images:
        try:
            result = convert_image(source, keep_original=args.keep_original, dry_run=args.dry_run)
        except (OSError, FileExistsError) as error:
            print(f"Skipped {source}: {error}", file=sys.stderr)
            continue
        total_before += result.size_before
        total_after += result.size_after
        name = source.relative_to(Path.cwd()) if source.is_relative_to(Path.cwd()) else source
        if result.target is None:
            print(f"kept     {name} (WebP would be larger)")
        else:
            saved = 1 - result.size_after / result.size_before
            print(
                f"webp     {name}: {format_size(result.size_before)} → "
                f"{format_size(result.size_after)} (-{saved:.0%})"
            )

    if total_before:
        saved = 1 - total_after / total_before
        print(f"\nTotal: {format_size(total_before)} → {format_size(total_after)} (-{saved:.0%})")
    if args.dry_run:
        print("Dry run: nothing was written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
