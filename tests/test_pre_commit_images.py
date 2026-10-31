import random
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def write_photo(path: Path) -> Path:
    """A noisy image, big enough for WebP to beat PNG."""
    rng = random.Random(42)
    image = Image.new("RGB", (64, 64))
    image.putdata([tuple(rng.randrange(256) for _ in "RGB") for _ in range(64 * 64)])
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def make_repo(tmp_path: Path) -> list[str]:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "config", "core.hooksPath", str(ROOT / ".githooks")], check=True)
    (tmp_path / "scripts").symlink_to(ROOT / "scripts")
    return git


def committed_files(git: list[str]) -> list[str]:
    return sorted(
        subprocess.run([*git, "ls-files"], capture_output=True, text=True, check=True)
        .stdout.split()
    )


def test_pre_commit_hook_converts_staged_png_and_references(tmp_path):
    git = make_repo(tmp_path)
    bundle = tmp_path / "content" / "post"
    write_photo(bundle / "image.png")
    (bundle / "index.md").write_text('{{< image src="image.png" >}}\n', encoding="utf-8")
    (tmp_path / "notes.md").write_text("draft\n", encoding="utf-8")

    subprocess.run([*git, "add", "content"], check=True)
    result = subprocess.run([*git, "commit", "-qm", "post"], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert "content/post/image.png → image.webp" in result.stderr
    assert committed_files(git) == ["content/post/image.webp", "content/post/index.md"]
    committed_markdown = subprocess.run(
        [*git, "show", "HEAD:content/post/index.md"], capture_output=True, text=True, check=True
    ).stdout
    assert committed_markdown == '{{< image src="image.webp" >}}\n'
    # Only the converted image and its references are staged, nothing else.
    assert subprocess.run(
        [*git, "status", "--porcelain"], capture_output=True, text=True, check=True
    ).stdout == "?? notes.md\n?? scripts\n"


def test_pre_commit_hook_warns_about_large_images(tmp_path):
    git = make_repo(tmp_path)
    large = tmp_path / "content" / "post" / "big.webp"
    large.parent.mkdir(parents=True)
    large.write_bytes(b"0" * (501 * 1024))

    subprocess.run([*git, "add", "content"], check=True)
    result = subprocess.run([*git, "commit", "-qm", "big"], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert "warning, content/post/big.webp has 501 KB, above 500 KB" in result.stderr
