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
