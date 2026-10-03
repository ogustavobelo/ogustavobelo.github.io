"""
Regression tests for the SEO/crawling conventions documented in the "SEO and
Crawling" section of .github/ARCHITECTURE.md: robots.txt policy, per-page
description/canonical/JSON-LD, tag page noindex, sitemap.xml, RSS, the
Markdown output format and llms.txt/llms-full.txt.
"""

import json
import re
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


SITE_DESCRIPTION = "Reflexões, ideias e anotações sobre tecnologia, produtividade e curiosidade."

# A post whose front matter sets `description`/`images` (the "hand-authored"
# path through function/description.html and og:image).
POST_WITH_OWN_IMAGE = ("posts", "2026", "09", "27", "wolverine")
# A post relying on the derived-from-summary description and the site's
# default social image (the common, "no front matter override" path).
POST_WITHOUT_OWN_IMAGE = ("posts", "2026", "09", "25", "nova-lataria-novas-ideias")
# Tags with >= 2 and exactly 1 post respectively (see test_seo_content for how
# this is derived); kept as literals here since the term pages are look-up
# targets, not something worth recomputing at test time.
MULTI_POST_TAG = "ps5"
THIN_TAG = "hbo-max"


def read(built_site_session, *parts):
    path = built_site_session.joinpath(*parts)
    assert path.is_file(), f"expected {path} to exist"
    return path.read_text(encoding="utf-8")


def meta_content(html, name):
    match = re.search(
        rf'<meta\s+name="?{re.escape(name)}"?\s+content="([^"]*)"', html
    )
    assert match, f'<meta name="{name}"> not found'
    return match.group(1)


def genuine_post_pages(built_site_session):
    """posts/**/index.html also matches pagination (posts/page/2/) and Hugo's
    own page-1 alias redirect (posts/page/1/); only YYYY/MM/DD/slug/index.html
    is an actual post."""
    posts_dir = built_site_session / "posts"
    return [
        p
        for p in posts_dir.rglob("index.html")
        if len(p.relative_to(posts_dir).parts) == 5
    ]


def is_draft(post_html_path, built_site_session):
    """Maps a built posts/YYYY/MM/DD/slug/index.html back to its source
    content/posts/YYYY/MM/DD/slug/index.md and reads its `draft` flag. Drafts
    never reach the real deploy (hugo --gc --minify, no --buildDrafts), so
    their content/SEO quality isn't a live issue."""
    slug_path = post_html_path.relative_to(built_site_session / "posts").parent
    source = ROOT / "content" / "posts" / slug_path / "index.md"
    text = source.read_text(encoding="utf-8")
    front_matter = tomllib.loads(text[3 : text.index("+++", 3)])
    return bool(front_matter.get("draft"))


def json_ld_blocks(html):
    blocks = []
    for raw in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.S
    ):
        blocks.append(json.loads(raw))
    assert blocks, "no application/ld+json script found"
    return blocks


# --- robots.txt -------------------------------------------------------------


def test_robots_txt_allows_crawling_and_declares_sitemap(built_site_session):
    robots = read(built_site_session, "robots.txt")

    assert "User-agent: *" in robots
    assert "Disallow: /\n" not in robots.split("User-agent: *", 1)[1].split(
        "User-agent:", 2
    )[1]
    assert re.search(r"^Sitemap: https://www\.gustavobelo\.com/sitemap\.xml$", robots, re.M)


@pytest.mark.parametrize(
    "bot",
    ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot"],
)
def test_robots_txt_allows_on_demand_ai_bots(built_site_session, bot):
    robots = read(built_site_session, "robots.txt")
    block = re.search(rf"User-agent: {re.escape(bot)}\n(.*?)\n\n", robots, re.S)
    assert block, f"no rule block found for {bot}"
    assert "Allow: /" in block.group(1)


@pytest.mark.parametrize(
    "bot",
    ["GPTBot", "ClaudeBot", "Google-Extended", "CCBot", "Applebot-Extended"],
)
def test_robots_txt_blocks_training_only_ai_bots(built_site_session, bot):
    robots = read(built_site_session, "robots.txt")
    block = re.search(rf"User-agent: {re.escape(bot)}\n(.*?)(\n\n|\Z)", robots, re.S)
    assert block, f"no rule block found for {bot}"
    assert "Disallow: /" in block.group(1)


# --- post lists actually list posts (regression: the "Pager 1" / empty list bug) --


@pytest.mark.parametrize(
    "path,needle",
    [
        (("index.html",), 'class="single summary"'),
        (("posts", "index.html"), "archive-item"),
        (("tags", MULTI_POST_TAG, "index.html"), "archive-item"),
    ],
)
def test_list_pages_render_actual_posts_not_just_pagination(built_site_session, path, needle):
    html = read(built_site_session, *path)
    assert needle in html, (
        f"{'/'.join(path)} has no post entries - if this is the only thing "
        "that broke, check for a stray unassigned .Paginate call (see "
        "function/paginate.html)"
    )
    assert "Pager " not in html, (
        f"{'/'.join(path)} leaked a Pager's Go string representation into the "
        "page - a .Paginate/.Paginator call somewhere isn't being captured "
        "into a variable"
    )


def test_paginated_list_canonical_uses_the_pager_url(built_site_session):
    page_one = read(built_site_session, "posts", "index.html")
    page_two = read(built_site_session, "posts", "page", "2", "index.html")

    assert 'rel="canonical" href="https://www.gustavobelo.com/posts/"' in page_one
    assert (
        'rel="canonical" href="https://www.gustavobelo.com/posts/page/2/"' in page_two
    )


# --- per-post description / JSON-LD / og:image ------------------------------


def test_every_post_has_a_specific_non_generic_description(built_site_session):
    offenders = []
    for index_html in genuine_post_pages(built_site_session):
        if is_draft(index_html, built_site_session):
            continue
        html = index_html.read_text(encoding="utf-8")
        description = meta_content(html, "Description")
        if not description.strip() or description.strip() == SITE_DESCRIPTION:
            offenders.append(str(index_html.relative_to(built_site_session)))

    assert not offenders, (
        "post(s) rendered with an empty or generic site-wide description "
        "(the description derivation in function/description.html failed for "
        f"these, likely an empty/near-empty post body): {offenders}"
    )


def test_post_json_ld_is_valid_and_matches_the_page(built_site_session):
    html = read(built_site_session, *POST_WITH_OWN_IMAGE, "index.html")
    blogposting = next(b for b in json_ld_blocks(html) if b.get("@type") == "BlogPosting")

    assert blogposting["headline"] == "Wolverine"
    assert blogposting["description"].strip()
    assert blogposting["description"] != SITE_DESCRIPTION
    assert blogposting["datePublished"]
    assert blogposting["image"][0]["url"].startswith(
        "https://www.gustavobelo.com/posts/2026/09/27/wolverine/"
    )


def test_post_with_own_image_uses_it_for_og_image(built_site_session):
    html = read(built_site_session, *POST_WITH_OWN_IMAGE, "index.html")
    og_image = re.search(r'<meta property="og:image" content="([^"]*)"', html).group(1)

    assert og_image.startswith("https://www.gustavobelo.com/posts/2026/09/27/wolverine/")


def test_post_without_own_image_falls_back_to_site_image(built_site_session):
    html = read(built_site_session, *POST_WITHOUT_OWN_IMAGE, "index.html")
    og_image = re.search(r'<meta property="og:image" content="([^"]*)"', html).group(1)

    assert og_image == "https://www.gustavobelo.com/android-chrome-512x512.png"


# --- tag pages: specific description + thin-tag noindex ---------------------


def test_multi_post_tag_page_is_indexable_with_a_specific_description(built_site_session):
    html = read(built_site_session, "tags", MULTI_POST_TAG, "index.html")

    assert 'name="robots" content="index, follow"' in html
    description = meta_content(html, "Description")
    assert description != SITE_DESCRIPTION
    assert MULTI_POST_TAG.capitalize() in description or MULTI_POST_TAG in description.lower()


def test_thin_tag_page_is_noindexed(built_site_session):
    html = read(built_site_session, "tags", THIN_TAG, "index.html")

    assert 'name="robots" content="noindex, follow"' in html


# --- sitemap.xml --------------------------------------------------------------


def test_sitemap_has_no_priority_or_changefreq(built_site_session):
    sitemap = read(built_site_session, "sitemap.xml")

    assert "<priority>" not in sitemap
    assert "<changefreq>" not in sitemap


def test_sitemap_includes_image_entries_for_posts_with_images(built_site_session):
    sitemap = read(built_site_session, "sitemap.xml")

    assert (
        "<image:loc>https://www.gustavobelo.com/posts/2026/09/27/wolverine/"
        "wolverine-ps5-gameplay.webp</image:loc>" in sitemap
    )


def test_sitemap_does_not_list_legacy_aliases_separately(built_site_session):
    """The "flow" post has a legacy Bear alias (/flow/); the sitemap must only
    list its canonical URL, not a second entry for the alias."""
    sitemap = read(built_site_session, "sitemap.xml")

    assert sitemap.count("<loc>https://www.gustavobelo.com/posts/2025/03/04/flow/</loc>") == 1
    assert "<loc>https://www.gustavobelo.com/flow/</loc>" not in sitemap


# --- RSS ----------------------------------------------------------------------


def test_home_rss_feed_has_expected_item_count_and_self_link(built_site_session):
    rss = read(built_site_session, "index.xml")

    assert rss.count("<item>") == 30
    assert 'rel="self"' in rss


def test_rss_full_text_items_have_no_leftover_lazyload_markup(built_site_session):
    rss = read(built_site_session, "index.xml")

    for item in re.findall(r"<item>.*?</item>", rss, re.S):
        assert "image-frame" not in item, "RSS item still contains the lazysizes image wrapper"
        assert "lazyload" not in item
        assert "<img" not in item


# --- Markdown output + llms.txt/llms-full.txt --------------------------------


def test_post_has_a_markdown_alternate_with_no_leftover_shortcode_syntax(built_site_session):
    markdown = read(built_site_session, *POST_WITH_OWN_IMAGE, "index.md")

    assert "{{<" not in markdown and "{{%" not in markdown
    assert "Fonte: https://www.gustavobelo.com/posts/2026/09/27/wolverine/" in markdown
    assert "![wolverine]" in markdown


def test_markdown_alternate_is_linked_from_the_post_head(built_site_session):
    html = read(built_site_session, *POST_WITH_OWN_IMAGE, "index.html")

    assert 'type="text/markdown"' in html


def test_llms_txt_lists_every_published_post(built_site_session):
    llms = read(built_site_session, "llms.txt")

    assert llms.count("\n- [") == len(genuine_post_pages(built_site_session))


def test_llms_full_txt_has_no_leftover_shortcode_syntax(built_site_session):
    llms_full = read(built_site_session, "llms-full.txt")

    assert "{{<" not in llms_full and "{{%" not in llms_full
