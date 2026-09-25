#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import urlopen


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\").replace('"', '\\"')


def normalize_slug(raw: str | None, fallback: str = "post") -> str:
    value = (raw or fallback).strip()
    value = value.lower()
    value = value.replace("_", "-")
    value = re.sub(r"[^a-z0-9\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    value = value.strip("-")
    return value or fallback


def parse_tags(raw: str | None) -> list[str]:
    if not raw or raw.strip() == "":
        return []
    text = raw.strip()
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        parsed = [item.strip() for item in text.split(",") if item.strip()]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    if isinstance(parsed, str):
        return [parsed.strip()] if parsed.strip() else []
    return []


def parse_date(raw: str | None) -> str:
    text = (raw or "").strip()
    if not text:
        raise ValueError("Date is required")
    cleaned = text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    return dt.isoformat()


def convert_tab_links(text: str) -> str:
    return re.sub(r"\]\(tab:(https?://[^)]+)\)", r"](\1)", text or "")


def convert_first_image_to_frame(text: str) -> str:
    pattern = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<url>https?://[^)\s]+)\)")
    match = pattern.search(text)
    if not match:
        return text
    return text[: match.start()] + (
        '{{{{< image src="{url}" alt="{alt}" class="image-frame" >}}}}'.format(
            url=match.group("url"), alt=match.group("alt")
        )
    ) + text[match.end() :]


def image_filename(url: str, used_names: set[str]) -> str:
    name = Path(unquote(urlparse(url).path)).name or "image"
    if name in used_names:
        suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
        name = f"{Path(name).stem}-{suffix}{Path(name).suffix}"
    used_names.add(name)
    return name


def download_images(text: str, out_dir: Path) -> str:
    patterns = [
        re.compile(r"(?P<prefix>!\[[^\]]*\]\()(?P<url>https?://[^)\s]+)"),
        re.compile(r"(?P<prefix>\bsrc\s*=\s*[\"'])(?P<url>https?://[^\"']+)(?P<suffix>[\"'])"),
    ]
    replacements: dict[str, str] = {}
    used_names: set[str] = set()

    for pattern in patterns:
        for match in pattern.finditer(text):
            url = match.group("url")
            if url in replacements:
                continue
            filename = image_filename(url, used_names)
            target = out_dir / filename
            try:
                with urlopen(url, timeout=30) as response:
                    target.write_bytes(response.read())
            except OSError as exc:
                raise OSError(f"Could not download image '{url}': {exc}") from exc
            replacements[url] = filename

    for url, filename in replacements.items():
        text = text.replace(url, filename)
    return text


def load_post_row(csv_path: str | Path, uid: str) -> dict[str, str]:
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            normalized = {
                (key or "").lstrip("\ufeff").strip(): value
                for key, value in row.items()
            }
            rows.append(normalized)
        matches = [row for row in rows if row.get("uid") == uid]
    if not matches:
        raise FileNotFoundError(f"No Bear post found for uid '{uid}' in {path}")
    if len(matches) > 1:
        raise ValueError(f"Multiple Bear posts found for uid '{uid}' in {path}")
    return matches[0]


def build_hugo_post(record: dict[str, str]) -> str:
    title = (record.get("title") or "Untitled").strip()
    slug = normalize_slug(record.get("slug") or title)
    published = record.get("published date") or record.get("first published at") or "1970-01-01T00:00:00+00:00"
    date_text = parse_date(published)
    draft = not as_bool(record.get("publish", "True"))
    tags = parse_tags(record.get("all tags"))
    body = convert_first_image_to_frame(convert_tab_links((record.get("content") or "").strip()))
    alias = (record.get("alias") or "").strip()
    canonical_url = (record.get("canonical url") or "").strip()
    description = (record.get("meta description") or "").strip()

    lines = [
        "+++",
        f'title = "{toml_escape(title)}"',
        f'date = "{date_text}"',
        f"draft = {'true' if draft else 'false'}",
    ]

    if tags:
        lines.append(f"tags = {json.dumps(tags, ensure_ascii=False)}")
    if alias:
        lines.append(f'aliases = ["{toml_escape(alias)}"]')
    if canonical_url:
        lines.append(f'canonicalURL = "{toml_escape(canonical_url)}"')
    if description:
        lines.append(f'description = "{toml_escape(description)}"')
    lines.append(f'bear_uid = "{toml_escape(str(record.get("uid") or ""))}"')
    lines.append("+++")
    lines.append("")
    lines.append(body.rstrip())
    return "\n".join(lines) + "\n"


def write_hugo_post(record: dict[str, str], repo_root: str | Path, dry_run: bool = False, force: bool = False) -> Path:
    repo = Path(repo_root)
    slug = normalize_slug(record.get("slug") or record.get("title") or "post")
    published = record.get("published date") or record.get("first published at") or "1970-01-01T00:00:00+00:00"
    post_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
    out_dir = repo / "content" / "posts" / f"{post_date.year:04d}" / f"{post_date.month:02d}" / f"{post_date.day:02d}" / slug
    out_file = out_dir / "index.md"

    if out_file.exists() and not force:
        raise FileExistsError(f"The target post already exists: {out_file}")

    rendered = build_hugo_post(record)
    if dry_run:
        print(f"Dry run: would write {out_file}")
        print(rendered)
        return out_file

    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = download_images(rendered, out_dir)
    out_file.write_text(rendered, encoding="utf-8")
    return out_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a Bear post into a Hugo bundle by UID.")
    parser.add_argument("uid", help="UID of the Bear post to import")
    parser.add_argument("--csv", default="bear-data/Bear Blog Settings.csv", help="Path to the Bear export CSV")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root to write the Hugo bundle into")
    parser.add_argument("--dry-run", action="store_true", help="Print the generated content without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite the target file if it already exists")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = (repo_root / csv_path).resolve()

    try:
        record = load_post_row(csv_path, args.uid)
        output_path = write_hugo_post(record, repo_root, dry_run=args.dry_run, force=args.force)
        print(f"Imported Bear post '{args.uid}' into {output_path.parent}.")
        return 0
    except (FileNotFoundError, ValueError, FileExistsError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
