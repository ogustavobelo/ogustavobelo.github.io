import importlib.util
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "create_shelf_item.py"


def load_module():
    spec = importlib.util.spec_from_file_location("create_shelf_item", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_kinds_and_statuses_match_the_shelf_layout():
    module = load_module()
    layout = (ROOT / "layouts" / "estante" / "list.html").read_text(encoding="utf-8")

    kinds = " ".join(f'"{value}"' for value, _ in module.KINDS)
    statuses = " ".join(f'"{value}"' for value, _ in module.STATUSES)
    assert f"$kinds := slice {kinds}" in layout
    assert f"$statuses := slice {statuses}" in layout


def test_create_shelf_item_writes_concluded_work_with_cover(tmp_path):
    module = load_module()
    cover = tmp_path / "Poster Final.PNG"
    cover.write_bytes(b"png")

    output = module.create_shelf_item(
        "O segredo de Widow's Bay",
        "series",
        "concluded",
        tmp_path,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 10, 1),
        post="/posts/2026/10/02/o-segredo-de-widows-bay",
        cover=cover,
    )

    assert output == (
        tmp_path / "content" / "estante" / "o-segredo-de-widows-bay" / "index.md"
    )
    assert output.read_text(encoding="utf-8") == (
        "+++\n"
        'title = "O segredo de Widow\'s Bay"\n'
        'kind = "series"\n'
        'status = "concluded"\n'
        "startDate = 2026-09-01\n"
        "endDate = 2026-10-01\n"
        'post = "/posts/2026/10/02/o-segredo-de-widows-bay"\n'
        "+++\n"
    )
    assert (output.parent / "cover.png").read_bytes() == b"png"


def test_create_shelf_item_drops_end_date_for_in_progress_work(tmp_path):
    module = load_module()

    output = module.create_shelf_item(
        "Hades II",
        "game",
        "in-progress",
        tmp_path,
        start_date=date(2026, 9, 20),
        end_date=date(2026, 10, 1),
    )

    text = output.read_text(encoding="utf-8")
    assert "endDate" not in text
    assert 'status = "in-progress"' in text


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"kind": "movie"}, "Unknown kind"),
        ({"status": "paused"}, "Unknown status"),
        ({"end_date": date(2026, 8, 1)}, "End date"),
        ({"status": "abandoned", "post": "/posts/x"}, "Only concluded"),
        ({"title": "  "}, "Title cannot be empty"),
    ],
)
def test_create_shelf_item_rejects_invalid_input(tmp_path, kwargs, message):
    module = load_module()
    options = {
        "title": "Duna",
        "kind": "book",
        "status": "concluded",
        "repo_root": tmp_path,
        "start_date": date(2026, 9, 1),
        "end_date": date(2026, 9, 30),
        **kwargs,
    }

    with pytest.raises(ValueError, match=message):
        module.create_shelf_item(**options)


def test_create_shelf_item_refuses_to_overwrite_and_replaces_cover(tmp_path):
    module = load_module()
    old_cover = tmp_path / "old.jpg"
    old_cover.write_bytes(b"jpg")
    new_cover = tmp_path / "new.webp"
    new_cover.write_bytes(b"webp")
    options = {"start_date": date(2026, 9, 1), "end_date": date(2026, 9, 2)}

    output = module.create_shelf_item(
        "Duna", "book", "concluded", tmp_path, cover=old_cover, **options
    )
    with pytest.raises(FileExistsError):
        module.create_shelf_item("Duna", "book", "concluded", tmp_path, **options)

    module.create_shelf_item(
        "Duna", "book", "concluded", tmp_path, cover=new_cover, overwrite=True, **options
    )
    assert sorted(p.name for p in output.parent.glob("cover.*")) == ["cover.webp"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://ogustavobelo.com/posts/2026/10/02/slug/", "/posts/2026/10/02/slug"),
        ("posts/2026/10/02/slug", "/posts/2026/10/02/slug"),
        ("  ", ""),
    ],
)
def test_normalize_post_path(raw, expected):
    assert load_module().normalize_post_path(raw) == expected


def test_post_exists_checks_content_bundle(tmp_path):
    module = load_module()
    bundle = tmp_path / "content" / "posts" / "2026" / "10" / "02" / "slug"
    bundle.mkdir(parents=True)
    (bundle / "index.md").write_text("+++\n+++\n", encoding="utf-8")

    assert module.post_exists(tmp_path, "/posts/2026/10/02/slug")
    assert not module.post_exists(tmp_path, "/posts/2026/10/02/other")


def test_parse_cover_path_accepts_dragged_paths():
    module = load_module()

    assert module.parse_cover_path(r"/tmp/My\ Cover.png") == Path("/tmp/My Cover.png")
    assert module.parse_cover_path("'/tmp/My Cover.png'") == Path("/tmp/My Cover.png")
    assert module.parse_cover_path("") is None
