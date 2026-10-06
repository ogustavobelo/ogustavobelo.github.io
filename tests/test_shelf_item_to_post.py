import importlib.util
from datetime import date, datetime
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "shelf_item_to_post.py"


def load_module():
    spec = importlib.util.spec_from_file_location("shelf_item_to_post", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_work(repo_root: Path, path: str, front_matter: str, cover: str = "") -> Path:
    bundle = repo_root / "content" / "estante" / path
    bundle.mkdir(parents=True, exist_ok=True)
    index_file = bundle / "index.md"
    index_file.write_text(f"+++\n{front_matter}+++\n", encoding="utf-8")
    if cover:
        (bundle / cover).write_bytes(b"image")
    return index_file


def in_progress(title: str, kind: str, start: str) -> str:
    return (
        f'title = "{title}"\nkind = "{kind}"\nstatus = "in-progress"\n'
        f"startDate = {start}\n"
    )


def test_list_in_progress_skips_finished_works_and_sorts_newest_first(tmp_path):
    module = load_module()
    write_work(tmp_path, "2026/09/ironias-do-tempo", in_progress("Ironias do tempo", "book", "2026-09-16"))
    write_work(tmp_path, "2026/10/a-hora-da-estrela", in_progress("A hora da estrela", "book", "2026-10-03"))
    write_work(
        tmp_path,
        "2026/09/duna",
        'title = "Duna"\nkind = "book"\nstatus = "concluded"\n'
        "startDate = 2026-09-01\nendDate = 2026-09-30\n",
    )

    works = module.list_in_progress(tmp_path)

    assert [work.title for work in works] == ["A hora da estrela", "Ironias do tempo"]
    assert works[0].kind == "book"
    assert works[0].start_date == date(2026, 10, 3)


def test_convert_to_post_moves_cover_and_concludes_work(tmp_path):
    module = load_module()
    index_file = write_work(
        tmp_path,
        "2026/09/hacks-5a-temporada",
        in_progress("Hacks - 5a temporada", "series", "2026-09-24"),
        cover="cover.PNG",
    )
    work = module.list_in_progress(tmp_path)[0]

    post_file, shelf_file = module.convert_to_post(
        work,
        tmp_path,
        title="Hacks",
        tags=["review", "series"],
        end_date=date(2026, 10, 5),
        created_at=datetime(2026, 10, 6, 9, 0, tzinfo=module.BRAZIL_TIMEZONE),
    )

    post_dir = tmp_path / "content" / "posts" / "2026" / "10" / "06" / "hacks"
    assert post_file == post_dir / "index.md"
    assert post_file.read_text(encoding="utf-8") == (
        "+++\n"
        'title = "Hacks"\n'
        'date = "2026-10-06T09:00:00-03:00"\n'
        "draft = true\n"
        'tags = ["review", "series"]\n'
        'images = ["hacks.png"]\n'
        "+++\n\n"
        '{{< image src="hacks.png" alt="Hacks" class="image-frame" >}}\n\n'
    )
    assert (post_dir / "hacks.png").read_bytes() == b"image"
    assert list(index_file.parent.glob("cover.*")) == []
    assert shelf_file == index_file
    assert index_file.read_text(encoding="utf-8") == (
        "+++\n"
        'title = "Hacks - 5a temporada"\n'
        'kind = "series"\n'
        'status = "concluded"\n'
        "startDate = 2026-09-24\n"
        "endDate = 2026-10-05\n"
        'post = "/posts/2026/10/06/hacks"\n'
        'cover = "/posts/2026/10/06/hacks/hacks.png"\n'
        "+++\n"
    )


def test_convert_to_post_without_cover_leaves_image_out(tmp_path):
    module = load_module()
    index_file = write_work(tmp_path, "2026/10/duna", in_progress("Duna", "book", "2026-10-01"))
    work = module.list_in_progress(tmp_path)[0]

    post_file, _ = module.convert_to_post(
        work,
        tmp_path,
        title="Duna",
        tags=[],
        end_date=date(2026, 10, 5),
        created_at=datetime(2026, 10, 6, 9, 0, tzinfo=module.BRAZIL_TIMEZONE),
    )

    post_text = post_file.read_text(encoding="utf-8")
    assert "images" not in post_text
    assert "{{< image" not in post_text
    shelf_text = index_file.read_text(encoding="utf-8")
    assert 'post = "/posts/2026/10/06/duna"' in shelf_text
    assert "cover" not in shelf_text


def test_convert_to_post_keeps_work_untouched_when_post_exists(tmp_path):
    module = load_module()
    created_at = datetime(2026, 10, 6, 9, 0, tzinfo=module.BRAZIL_TIMEZONE)
    index_file = write_work(
        tmp_path, "2026/10/duna", in_progress("Duna", "book", "2026-10-01"), cover="cover.jpg"
    )
    original = index_file.read_text(encoding="utf-8")
    work = module.list_in_progress(tmp_path)[0]
    module.create_post("Duna", [], tmp_path, created_at)

    with pytest.raises(FileExistsError):
        module.convert_to_post(
            work, tmp_path, title="Duna", tags=[], end_date=date(2026, 10, 5), created_at=created_at
        )

    assert index_file.read_text(encoding="utf-8") == original
    assert (index_file.parent / "cover.jpg").is_file()


def test_convert_to_post_rejects_end_date_before_start(tmp_path):
    module = load_module()
    write_work(tmp_path, "2026/10/duna", in_progress("Duna", "book", "2026-10-01"))
    work = module.list_in_progress(tmp_path)[0]

    with pytest.raises(ValueError, match="End date"):
        module.convert_to_post(
            work, tmp_path, title="Duna", tags=[], end_date=date(2026, 9, 30)
        )

    assert not (tmp_path / "content" / "posts").exists()
