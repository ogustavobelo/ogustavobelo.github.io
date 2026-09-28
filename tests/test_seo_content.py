"""
Front-matter-level SEO checks that don't need a Hugo build.

Per .github/skills/content-authoring/SKILL.md, `description` and `images` are
optional front matter fields: the site derives a description from the post's
own summary, and falls back to the site's default image, so omitting them is
a legitimate editorial choice for shorter or more casual posts. The tests
below are informational (they warn, not fail) for that reason - see
tests/test_seo.py for the hard assertions that the *rendered* fallback
actually produces something usable.
"""

import tomllib
import warnings
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "content" / "posts"


def _iter_posts():
    for path in sorted(POSTS_DIR.rglob("index.md")):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("+++"), f"{path} is missing TOML front matter"
        end = text.index("+++", 3)
        front_matter = tomllib.loads(text[3:end])
        yield path, front_matter, text[end + 3 :]


def _relative(paths):
    return [str(path.relative_to(ROOT)) for path in paths]


def _warn_if_any(paths, message):
    if not paths:
        return
    shown = _relative(paths[:5])
    more = f", and {len(paths) - 5} more" if len(paths) > 5 else ""
    warnings.warn(f"{message}: {', '.join(shown)}{more}", stacklevel=2)


def test_posts_missing_description_are_reported():
    missing = [
        path
        for path, front_matter, _ in _iter_posts()
        if not (front_matter.get("draft") or False)
        and not (front_matter.get("description") or "").strip()
    ]
    _warn_if_any(
        missing,
        f"{len(missing)} published post(s) have no explicit `description` front matter "
        "(fine per content-authoring policy - the site derives one from the summary; "
        "consider setting one for posts that deserve a hand-written hook)",
    )


def test_posts_missing_images_are_reported():
    missing = [
        path
        for path, front_matter, _ in _iter_posts()
        if not (front_matter.get("draft") or False) and not front_matter.get("images")
    ]
    _warn_if_any(
        missing,
        f"{len(missing)} published post(s) have no `images` front matter "
        "(fine per content-authoring policy - link previews fall back to the site's "
        "default image; consider setting one for posts with a cover photo)",
    )


def test_posts_images_field_references_files_that_actually_exist():
    """Unlike an *absent* `images` field, a filename that doesn't exist in the
    page bundle is always a real bug: og:image, JSON-LD and the sitemap's
    image entries would silently resolve to nothing or to the wrong image."""
    broken = []
    for path, front_matter, _ in _iter_posts():
        bundle = path.parent
        for filename in front_matter.get("images") or []:
            if not (bundle / filename).is_file():
                broken.append(f"{path.relative_to(ROOT)} -> images = [{filename!r}]")

    assert not broken, "images front matter references missing file(s):\n" + "\n".join(broken)


def test_posts_shortcode_usage_is_covered_by_the_markdown_rewrite_partial():
    """layouts/partials/function/markdown.html (used by the Markdown/llms
    outputs and the full-text RSS feed) only knows how to rewrite `image`,
    `ref` and `admonition`. A new shortcode name in content/posts needs a
    matching rewrite rule there, or its raw {{< ... >}} syntax will leak into
    those outputs."""
    import re

    known = {"image", "ref", "admonition"}
    unknown = set()
    for path, _, body in _iter_posts():
        for match in re.finditer(r"\{\{[%<]\s*/?\s*(\w+)", body):
            name = match.group(1)
            if name not in known:
                unknown.add(name)

    assert not unknown, (
        "content/posts uses shortcode(s) not handled by function/markdown.html: "
        f"{sorted(unknown)}. Add a rewrite rule there or the Markdown/llms/RSS "
        "outputs will leak raw shortcode syntax."
    )
