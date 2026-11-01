import importlib.util
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "create_story.py"


def load_module():
    spec = importlib.util.spec_from_file_location("create_story", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_post(tmp_path: Path, front_matter: str, body: str = "", images=()) -> Path:
    post = tmp_path / "content" / "posts" / "2026" / "10" / "25" / "meu-post"
    post.mkdir(parents=True)
    (post / "index.md").write_text(f"+++\n{front_matter}+++\n\n{body}", encoding="utf-8")
    for name in images:
        Image.new("RGB", (40, 30), "red").save(post / name)
    return post


def test_load_post_reads_front_matter_and_builds_url(tmp_path):
    module = load_module()
    post_dir = write_post(
        tmp_path,
        'title = "Meu post"\ndescription = "Uma descrição"\nimages = ["capa.webp"]\n',
        '{{< image src="outra.webp" alt="x" >}}\n',
        images=["capa.webp", "outra.webp"],
    )

    post = module.load_post(post_dir / "index.md")

    assert post.title == "Meu post"
    assert post.description == "Uma descrição"
    assert post.url == "https://www.gustavobelo.com/posts/2026/10/25/meu-post/"
    assert post.slug == "meu-post"
    assert post.image == post_dir / "capa.webp"


def test_url_honors_slug_and_url_front_matter(tmp_path):
    module = load_module()
    post_dir = write_post(tmp_path, 'title = "T"\nslug = "outro-slug"\n')
    assert module.load_post(post_dir).url.endswith("/posts/2026/10/25/outro-slug/")

    (post_dir / "index.md").write_text('+++\ntitle = "T"\nurl = "/sobre/"\n+++\n')
    assert module.load_post(post_dir).url == "https://www.gustavobelo.com/sobre/"


def test_cover_falls_back_to_shortcode_then_bundle_image(tmp_path):
    module = load_module()
    post_dir = write_post(
        tmp_path,
        'title = "T"\n',
        '{{< image src="b.webp" alt="x" >}}\n',
        images=["a.png", "b.webp"],
    )
    assert module.load_post(post_dir).image == post_dir / "b.webp"

    (post_dir / "index.md").write_text('+++\ntitle = "T"\n+++\n')
    assert module.load_post(post_dir).image == post_dir / "a.png"

    for image in post_dir.glob("*.*"):
        if image.name != "index.md":
            image.unlink()
    assert module.load_post(post_dir).image is None


def test_description_falls_back_to_first_paragraph(tmp_path):
    module = load_module()
    post_dir = write_post(
        tmp_path,
        'title = "T"\n',
        '{{< image src="a.webp" >}}\n\nTexto com [link](https://x.y) e *ênfase*.\n\nOutro.\n',
    )
    assert module.load_post(post_dir).description == "Texto com link e ênfase."


def test_wrap_text_truncates_with_ellipsis():
    module = load_module()
    font = module.load_font(40)

    lines = module.wrap_text("palavra " * 60, font, 400, 3)

    assert len(lines) == 3
    assert lines[-1].endswith("…")
    assert all(font.getlength(line) <= 400 for line in lines)
    assert module.wrap_text("curto", font, 400, 3) == ["curto"]


def test_create_story_writes_png_and_metadata(tmp_path):
    module = load_module()
    post_dir = write_post(
        tmp_path, 'title = "Meu post"\ndescription = "D"\n', images=["capa.webp"]
    )

    image_path, metadata_path = module.create_story(post_dir, tmp_path / "stories")

    assert image_path == tmp_path / "stories" / "meu-post.png"
    with Image.open(image_path) as image:
        assert image.size == (1080, 1920)
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == {
        "title": "Meu post",
        "description": "D",
        "url": "https://www.gustavobelo.com/posts/2026/10/25/meu-post/",
        "image": "meu-post.png",
    }
