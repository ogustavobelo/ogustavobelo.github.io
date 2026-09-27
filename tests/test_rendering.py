import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_site(tmp_path):
    destination = tmp_path / "public"
    result = subprocess.run(
        [
            "hugo",
            "--source",
            str(ROOT),
            "--destination",
            str(destination),
            "--cacheDir",
            str(tmp_path / "cache"),
            "--buildDrafts",
            "--quiet",
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "HUGO_PARAMS_SOCIAL_EMAIL": "leitor@example.com",
            "HUGO_PARAMS_ANALYTICS_GOATCOUNTER_CODE": "blog-de-teste",
        },
    )

    assert result.returncode == 0, result.stderr
    return destination


def test_hugo_homepage_resolves_local_image_frame_background(tmp_path):
    homepage = (build_site(tmp_path) / "index.html").read_text(encoding="utf-8")

    assert "background-image: url('/posts/" in homepage
    assert "background-image: url('https://bear-images.sfo2.cdn.digitaloceanspaces.com/" not in homepage


def test_hugo_post_page_resolves_local_image_frame_background(tmp_path):
    destination = build_site(tmp_path)
    post_page = (
        destination / "posts" / "2026" / "01" / "05" / "a-cabeca-do-santo" / "index.html"
    ).read_text(encoding="utf-8")

    assert "background-image: url('/posts/2026/01/05/a-cabeca-do-santo/a-cabeca-do-santo.webp')" in post_page
    assert 'data-src="/posts/2026/01/05/a-cabeca-do-santo/a-cabeca-do-santo.webp"' in post_page
    assert "background-image: url('https://bear-images.sfo2.cdn.digitaloceanspaces.com/" not in post_page


def test_hugo_tag_links_resolve_to_generated_term_pages(tmp_path):
    destination = build_site(tmp_path)
    tag_page = destination / "tags" / "filmes" / "index.html"
    post_page = (
        destination / "posts" / "2025" / "03" / "04" / "flow" / "index.html"
    ).read_text(encoding="utf-8")

    assert tag_page.is_file()
    assert '<h3><a href="/tags/filmes/">#filmes</a></h3>' in post_page


def test_hugo_post_page_loads_goatcounter_and_tracks_contact_email(tmp_path):
    destination = build_site(tmp_path)
    post_page = (
        destination / "posts" / "2025" / "03" / "04" / "flow" / "index.html"
    ).read_text(encoding="utf-8")

    assert 'src="https://gc.zgo.at/count.js"' in post_page
    assert 'data-goatcounter="https://blog-de-teste.goatcounter.com/count"' in post_page
    assert 'href="mailto:leitor@example.com"' in post_page
    assert 'data-goatcounter-click="contato-email"' in post_page


def test_hugo_post_page_renders_share_links(tmp_path):
    destination = build_site(tmp_path)
    post_page = (
        destination / "posts" / "2026" / "01" / "05" / "a-cabeca-do-santo" / "index.html"
    ).read_text(encoding="utf-8")
    encoded_url = "https%3A%2F%2Fwww.gustavobelo.com%2Fposts%2F2026%2F01%2F05%2Fa-cabeca-do-santo%2F"

    assert '<aside class="post-share"' in post_page
    assert f'href="https://www.facebook.com/sharer/sharer.php?u={encoded_url}%3Fref%3Dfacebook"' in post_page
    assert f'href="https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}%3Fref%3Dlinkedin"' in post_page
    assert f"{encoded_url}%3Fref%3Dwhatsapp" in post_page
    assert f"url={encoded_url}%3Fref%3Dtelegram" in post_page
    assert 'class="post-share-copy" data-url="https://www.gustavobelo.com/posts/2026/01/05/a-cabeca-do-santo/"' in post_page
    assert 'data-url="https://www.gustavobelo.com/posts/2026/01/05/a-cabeca-do-santo/?ref=share"' in post_page


def test_hugo_post_page_falls_back_to_site_image_for_link_previews(tmp_path):
    destination = build_site(tmp_path)
    post_page = (
        destination / "posts" / "2026" / "09" / "25" / "nova-lataria-novas-ideias" / "index.html"
    ).read_text(encoding="utf-8")

    assert '<meta property="og:image" content="https://www.gustavobelo.com/android-chrome-512x512.png">' in post_page
