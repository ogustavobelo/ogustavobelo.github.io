#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE_URL = "https://www.gustavobelo.com/"
SITE_LABEL = "gustavobelo.com"

STORY_SIZE = (1080, 1920)
# Instagram draws the progress bar and avatar over the top and the reply bar
# over the bottom; the bottom band is also left free for the link sticker.
SAFE_TOP = 250
LINK_BAND = 300
SIDE_MARGIN = 80
GRADIENT_HEIGHT = 0.6
GRADIENT_OPACITY = 225

TITLE_SIZE = 72
TITLE_MAX_LINES = 4
DESCRIPTION_SIZE = 40
DESCRIPTION_MAX_LINES = 4
LABEL_SIZE = 32
LINE_SPACING = 1.2
# Theme accent color, from assets/css/_variables.scss.
ACCENT_COLOR = (0x2F, 0x8F, 0x83)

FONT_CANDIDATES = [
    Path("/System/Library/Fonts/SFNS.ttf"),
    Path("/System/Library/Fonts/Helvetica.ttc"),
]

FRONT_MATTER_PATTERN = re.compile(r"^\+\+\+\n(.*?\n)\+\+\+\n?(.*)", re.DOTALL)
IMAGE_SHORTCODE_PATTERN = re.compile(r'{{<\s*image\s+[^>]*?src="([^"]+)"')
IMAGE_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")
POST_PATH_PATTERN = re.compile(r"posts/(\d{4})/(\d{2})/(\d{2})/([^/]+)/?$")


class Post(NamedTuple):
    title: str
    description: str
    url: str
    slug: str
    image: Path | None


def read_post(post_dir: Path) -> tuple[dict, str]:
    text = (post_dir / "index.md").read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        raise ValueError(f"No TOML front matter found in {post_dir / 'index.md'}")
    return tomllib.loads(match.group(1)), match.group(2)


def strip_markdown(text: str) -> str:
    text = re.sub(r"{{<.*?>}}", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`#>]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def first_paragraph(body: str) -> str:
    for paragraph in re.split(r"\n\s*\n", body):
        text = strip_markdown(paragraph)
        if text:
            return text
    return ""


def find_cover(post_dir: Path, front_matter: dict, body: str) -> Path | None:
    candidates = [*front_matter.get("images", [])[:1]]
    match = IMAGE_SHORTCODE_PATTERN.search(body)
    if match:
        candidates.append(match.group(1))
    for name in candidates:
        path = post_dir / name
        if path.is_file():
            return path
    images = sorted(
        path for path in post_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS
    )
    return images[0] if images else None


def post_url(post_dir: Path, front_matter: dict) -> str:
    if front_matter.get("url"):
        return BASE_URL + str(front_matter["url"]).strip("/") + "/"
    match = POST_PATH_PATTERN.search(post_dir.resolve().as_posix())
    if not match:
        raise ValueError(
            f"{post_dir} is not under content/posts/YYYY/MM/DD/slug/"
        )
    year, month, day, folder = match.groups()
    slug = front_matter.get("slug") or folder
    return f"{BASE_URL}posts/{year}/{month}/{day}/{slug}/"


def load_post(post_dir: str | Path) -> Post:
    post_dir = Path(post_dir)
    if post_dir.name == "index.md":
        post_dir = post_dir.parent
    front_matter, body = read_post(post_dir)
    title = str(front_matter.get("title", "")).strip()
    if not title:
        raise ValueError(f"Post has no title: {post_dir}")
    description = str(front_matter.get("description", "")).strip()
    return Post(
        title=title,
        description=description or first_paragraph(body),
        url=post_url(post_dir, front_matter),
        slug=str(front_matter.get("slug") or post_dir.name),
        image=find_cover(post_dir, front_matter, body),
    )


def load_font(size: int, bold: bool = False, font_path: Path | None = None):
    for path in [font_path] if font_path else FONT_CANDIDATES:
        if not path.is_file():
            continue
        if path.suffix == ".ttc":
            # Helvetica.ttc: index 0 is Regular, 1 is Bold.
            return ImageFont.truetype(str(path), size, index=1 if bold else 0)
        font = ImageFont.truetype(str(path), size)
        try:
            font.set_variation_by_name("Bold" if bold else "Regular")
        except OSError:
            pass  # Not a variable font.
        return font
    return ImageFont.load_default(size=size)


def wrap_text(text: str, font, max_width: int, max_lines: int) -> list[str]:
    """Greedy word wrap; the last line gets an ellipsis when text is cut."""
    lines: list[str] = []
    current = ""
    words = text.split()
    for index, word in enumerate(words):
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= max_width or not current:
            current = candidate
            continue
        lines.append(current)
        current = word
        if len(lines) == max_lines:
            current = ""
            words = words[index:]
            break
    else:
        words = []
    if current:
        lines.append(current)

    if words and lines:
        last = lines[-1]
        while last and font.getlength(last + "…") > max_width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last.rstrip(" ,.;:") + "…"
    return lines


def cover_background(image_path: Path | None) -> Image.Image:
    if image_path is None:
        return Image.new("RGB", STORY_SIZE, ACCENT_COLOR)
    with Image.open(image_path) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
    return ImageOps.fit(image, STORY_SIZE, Image.Resampling.LANCZOS)


def draw_gradient(image: Image.Image) -> Image.Image:
    width, height = image.size
    gradient_height = int(height * GRADIENT_HEIGHT)
    mask = Image.new("L", (1, gradient_height))
    ramp = gradient_height * 0.45
    for y in range(gradient_height):
        # Fades in over the top of the band, then stays dark behind the text.
        mask.putpixel((0, y), int(GRADIENT_OPACITY * min(1.0, y / ramp) ** 1.3))
    mask = mask.resize((width, gradient_height))
    overlay = Image.new("RGB", (width, gradient_height), (0, 0, 0))
    image.paste(overlay, (0, height - gradient_height), mask)
    return image


def render_story(post: Post, font_path: Path | None = None) -> Image.Image:
    image = draw_gradient(cover_background(post.image))
    draw = ImageDraw.Draw(image)
    max_width = STORY_SIZE[0] - 2 * SIDE_MARGIN

    title_font = load_font(TITLE_SIZE, bold=True, font_path=font_path)
    description_font = load_font(DESCRIPTION_SIZE, font_path=font_path)
    label_font = load_font(LABEL_SIZE, bold=True, font_path=font_path)
    title_lines = wrap_text(post.title, title_font, max_width, TITLE_MAX_LINES)
    description_lines = wrap_text(
        post.description, description_font, max_width, DESCRIPTION_MAX_LINES
    )

    title_step = int(TITLE_SIZE * LINE_SPACING)
    description_step = int(DESCRIPTION_SIZE * LINE_SPACING)
    label_step = int(LABEL_SIZE * LINE_SPACING)
    gap = 32
    block_height = (
        label_step
        + gap
        + title_step * len(title_lines)
        + (gap + description_step * len(description_lines) if description_lines else 0)
    )
    # The text block sits right above the link band, never above the safe top.
    y = max(SAFE_TOP, STORY_SIZE[1] - LINK_BAND - block_height)

    draw.text((SIDE_MARGIN, y), SITE_LABEL.upper(), font=label_font, fill=ACCENT_COLOR)
    y += label_step + gap
    for line in title_lines:
        draw.text((SIDE_MARGIN, y), line, font=title_font, fill="white")
        y += title_step
    if description_lines:
        y += gap
        for line in description_lines:
            draw.text((SIDE_MARGIN, y), line, font=description_font, fill=(225, 225, 225))
            y += description_step
    return image


def create_story(
    post_dir: str | Path, output_dir: str | Path, font_path: Path | None = None
) -> tuple[Path, Path]:
    post = load_post(post_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{post.slug}.png"
    metadata_path = output_dir / f"{post.slug}.json"

    render_story(post, font_path).save(image_path, "PNG", optimize=True)
    metadata = {
        "title": post.title,
        "description": post.description,
        "url": post.url,
        "image": image_path.name,
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return image_path, metadata_path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Render an Instagram story image (1080x1920) for a post."
    )
    parser.add_argument("post", help="Post bundle folder (or its index.md)")
    parser.add_argument(
        "--output-dir",
        default=str(repo_root / "stories"),
        help="Where the PNG and its JSON metadata are written",
    )
    parser.add_argument("--font", type=Path, help="TTF/OTF font to use instead of the system one")
    args = parser.parse_args()

    try:
        image_path, metadata_path = create_story(args.post, args.output_dir, args.font)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    url = json.loads(metadata_path.read_text(encoding="utf-8"))["url"]
    print(f"Story image: {image_path}")
    print(f"Metadata:    {metadata_path}")
    print(f"Link:        {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
