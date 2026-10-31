import importlib.util
import os
import random
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "convert_images.py"


def load_module():
    spec = importlib.util.spec_from_file_location("convert_images", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_photo(path: Path, mode: str = "RGB") -> Path:
    """A noisy image, big enough for WebP to beat PNG/JPEG."""
    rng = random.Random(42)
    image = Image.new(mode, (64, 64))
    image.putdata(
        [tuple(rng.randrange(256) for _ in mode) for _ in range(64 * 64)]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def test_encode_webp_keeps_transparency(tmp_path):
    module = load_module()
    source = write_photo(tmp_path / "logo.png", mode="RGBA")

    target = module.convert_to_webp(source)

    assert target == tmp_path / "logo.webp"
    with Image.open(target) as image:
        assert image.format == "WEBP"
        assert image.mode == "RGBA"
        assert image.size == (64, 64)


def test_convert_image_updates_references_and_drops_original(tmp_path):
    module = load_module()
    content = tmp_path / "content"
    post = content / "posts" / "2026" / "10" / "06" / "hacks"
    source = write_photo(post / "image.png")
    (post / "index.md").write_text(
        'images = ["image.png"]\n{{< image src="image.png" >}}\nold-image.png\n',
        encoding="utf-8",
    )
    shelf = content / "estante" / "2026" / "09" / "hacks"
    shelf.mkdir(parents=True)
    (shelf / "index.md").write_text(
        'cover = "/posts/2026/10/06/hacks/image.png"\n', encoding="utf-8"
    )
    # Another bundle with an image of the same name must stay untouched.
    other = content / "posts" / "2026" / "10" / "07" / "other"
    other.mkdir(parents=True)
    (other / "index.md").write_text('{{< image src="image.png" >}}\n', encoding="utf-8")

    result = module.convert_image(source)

    assert result.target == post / "image.webp"
    assert result.size_after < result.size_before
    assert not source.exists()
    assert (post / "index.md").read_text(encoding="utf-8") == (
        'images = ["image.webp"]\n{{< image src="image.webp" >}}\nold-image.png\n'
    )
    assert (shelf / "index.md").read_text(encoding="utf-8") == (
        'cover = "/posts/2026/10/06/hacks/image.webp"\n'
    )
    assert (other / "index.md").read_text(encoding="utf-8") == (
        '{{< image src="image.png" >}}\n'
    )


def test_convert_image_keeps_original_and_dry_run(tmp_path):
    module = load_module()
    source = write_photo(tmp_path / "content" / "about" / "profile.png")

    dry = module.convert_image(source, dry_run=True)
    assert dry.target == source.with_suffix(".webp")
    assert not dry.target.exists()

    kept = module.convert_image(source, keep_original=True)
    assert kept.target.is_file()
    assert source.is_file()


def test_convert_image_skips_when_webp_is_larger(tmp_path, monkeypatch):
    module = load_module()
    source = tmp_path / "tiny.png"
    Image.new("RGB", (1, 1)).save(source)
    monkeypatch.setattr(module, "encode_webp", lambda _: os.urandom(source.stat().st_size))

    result = module.convert_image(source)

    assert result.target is None
    assert source.is_file()
    assert not (tmp_path / "tiny.webp").exists()


def test_collect_images_only_picks_png_and_jpeg(tmp_path):
    module = load_module()
    for name in ["a.PNG", "b.jpg", "nested/c.jpeg", "d.webp", "e.gif", "f.md"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")

    images = module.collect_images([tmp_path])

    assert [p.relative_to(tmp_path.resolve()).as_posix() for p in images] == [
        "a.PNG",
        "b.jpg",
        "nested/c.jpeg",
    ]
