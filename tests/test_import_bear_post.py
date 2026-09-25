import csv
import importlib.util
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "import_bear_post.py"


def load_module():
    spec = importlib.util.spec_from_file_location("import_bear_post", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path):
    rows = [
        {
            "uid": "abc123",
            "title": "A cabeça do santo",
            "slug": "a-cabeca-do-santo",
            "alias": "",
            "published date": "2026-01-05 20:26:00+00:00",
            "all tags": '["leituras", "livros", "review"]',
            "publish": "True",
            "discoverable": "True",
            "is page": "False",
            "content": '![a-cabeca-do-santo](https://bear-images.sfo2.cdn.digitaloceanspaces.com/gustavobelo/a-cabeca-do-santo.webp)\n\nLeia [este texto](tab:https://example.com/artigo) agora.\n',
            "canonical url": "",
            "meta description": "",
            "meta image": "",
            "lang": "",
            "class name": "",
            "first published at": "",
        }
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def test_load_post_row_returns_matching_record(tmp_path):
    csv_path = tmp_path / "Bear Blog Settings.csv"
    write_csv(csv_path)
    module = load_module()

    record = module.load_post_row(csv_path, "abc123")

    assert record["title"] == "A cabeça do santo"
    assert record["slug"] == "a-cabeca-do-santo"


def test_load_post_row_handles_utf8_bom(tmp_path):
    csv_path = tmp_path / "Bear Blog Settings.csv"
    csv_path.write_text(
        '\ufeffuid,title,slug\nabc123,A cabeça do santo,a-cabeca-do-santo\n',
        encoding="utf-8",
    )
    module = load_module()

    record = module.load_post_row(csv_path, "abc123")

    assert record["title"] == "A cabeça do santo"
    assert record["uid"] == "abc123"


def test_build_hugo_post_creates_front_matter_and_converts_tab_links(tmp_path):
    csv_path = tmp_path / "Bear Blog Settings.csv"
    write_csv(csv_path)
    module = load_module()

    record = module.load_post_row(csv_path, "abc123")
    post_text = module.build_hugo_post(record)

    assert 'title = "A cabeça do santo"' in post_text
    assert 'date = "2026-01-05T20:26:00+00:00"' in post_text
    assert 'draft = false' in post_text
    assert 'tags = ["leituras", "livros", "review"]' in post_text
    assert '[este texto](https://example.com/artigo)' in post_text
    assert '{{< image src="https://bear-images.sfo2.cdn.digitaloceanspaces.com/gustavobelo/a-cabeca-do-santo.webp" alt="a-cabeca-do-santo" class="image-frame" >}}' in post_text


def test_download_images_saves_files_and_replaces_markdown_and_shortcode_urls(tmp_path, monkeypatch):
    module = load_module()
    responses = {
        "https://example.com/markdown.webp": b"markdown image",
        "https://example.com/shortcode.webp": b"shortcode image",
    }

    def fake_urlopen(url, timeout):
        assert timeout == 30
        return BytesIO(responses[url])

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    text = (
        "![markdown](https://example.com/markdown.webp)\n"
        '{{< image src="https://example.com/shortcode.webp" >}}'
    )

    converted = module.download_images(text, tmp_path)

    assert "![markdown](markdown.webp)" in converted
    assert '{{< image src="shortcode.webp" >}}' in converted
    assert (tmp_path / "markdown.webp").read_bytes() == b"markdown image"
    assert (tmp_path / "shortcode.webp").read_bytes() == b"shortcode image"


def test_main_creates_bundle_in_content_posts(tmp_path):
    csv_path = tmp_path / "Bear Blog Settings.csv"
    write_csv(csv_path)
    module = load_module()

    repo_root = tmp_path
    output = module.main(["abc123", "--csv", str(csv_path), "--repo-root", str(repo_root)])

    assert output == 0
    created = repo_root / "content" / "posts" / "2026" / "01" / "05" / "a-cabeca-do-santo" / "index.md"
    assert created.exists()
    assert "A cabeça do santo" in created.read_text(encoding="utf-8")


