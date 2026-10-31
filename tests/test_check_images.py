import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_images.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_images", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, size: int = 10) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"0" * size)
    return path


def test_find_problems_flags_png_jpeg_and_large_images(tmp_path):
    module = load_module()
    bundle = tmp_path / "content" / "posts" / "hacks"
    png = write(bundle / "image.PNG")
    jpeg = write(bundle / "photo.jpeg")
    large = write(bundle / "big.webp", module.MAX_IMAGE_SIZE + 1024)
    small = write(bundle / "small.webp", module.MAX_IMAGE_SIZE)
    markdown = write(bundle / "index.md")
    favicon = write(tmp_path / "static" / "favicon.png")

    problems = module.find_problems([png, jpeg, large, small, markdown, favicon])

    assert problems == [
        f"{png}: convert it to WebP",
        f"{jpeg}: convert it to WebP",
        f"{large}: 501 KB, above the 500 KB limit",
    ]


def test_find_problems_ignores_deleted_files(tmp_path):
    module = load_module()

    assert module.find_problems([tmp_path / "content" / "gone.png"]) == []


def test_pre_commit_hook_blocks_staged_png(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "config", "core.hooksPath", str(ROOT / ".githooks")], check=True)
    (tmp_path / "scripts").symlink_to(ROOT / "scripts")
    write(tmp_path / "content" / "post" / "image.png")
    write(tmp_path / "content" / "post" / "index.md")

    subprocess.run([*git, "add", "content/post/index.md"], check=True)
    ok = subprocess.run([*git, "commit", "-qm", "text"], capture_output=True, text=True)
    subprocess.run([*git, "add", "content/post/image.png"], check=True)
    blocked = subprocess.run([*git, "commit", "-qm", "png"], capture_output=True, text=True)

    assert ok.returncode == 0, ok.stderr
    assert blocked.returncode != 0
    assert "content/post/image.png: convert it to WebP" in blocked.stderr
