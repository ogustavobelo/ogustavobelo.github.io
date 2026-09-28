import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "create_post.py"


def load_module():
    spec = importlib.util.spec_from_file_location("create_post", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_post(repo_root: Path, path: str, front_matter: str) -> None:
    post_file = repo_root / "content" / "posts" / path / "index.md"
    post_file.parent.mkdir(parents=True, exist_ok=True)
    post_file.write_text(front_matter, encoding="utf-8")


def test_normalize_slug_removes_accents_and_punctuation():
    module = load_module()

    assert module.normalize_slug("Café, pão & ideias!") == "cafe-pao-ideias"


def test_create_post_uses_brazil_local_date_and_writes_front_matter(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 26, 1, 15, tzinfo=ZoneInfo("UTC"))

    output = module.create_post(
        "Uma nova ideia",
        ["ensaios", "leituras"],
        tmp_path,
        created_at,
    )

    assert output == (
        tmp_path
        / "content"
        / "posts"
        / "2026"
        / "09"
        / "25"
        / "uma-nova-ideia"
        / "index.md"
    )
    assert output.read_text(encoding="utf-8") == (
        "+++\n"
        'title = "Uma nova ideia"\n'
        'date = "2026-09-25T22:15:00-03:00"\n'
        "draft = true\n"
        'tags = ["ensaios", "leituras"]\n'
        "+++\n\n"
    )


def test_create_post_includes_description_when_provided(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 26, 1, 15, tzinfo=ZoneInfo("UTC"))

    output = module.create_post(
        "Uma nova ideia",
        ["ensaios"],
        tmp_path,
        created_at,
        description='Uma ideia com "aspas" e acentuação.',
    )

    assert output.read_text(encoding="utf-8") == (
        "+++\n"
        'title = "Uma nova ideia"\n'
        'date = "2026-09-25T22:15:00-03:00"\n'
        "draft = true\n"
        'tags = ["ensaios"]\n'
        'description = "Uma ideia com \\"aspas\\" e acentuação."\n'
        "+++\n\n"
    )


def test_create_post_rejects_existing_bundle(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 25, 12, 0, tzinfo=module.BRAZIL_TIMEZONE)
    module.create_post("Post repetido", [], tmp_path, created_at)

    with pytest.raises(FileExistsError):
        module.create_post("Post repetido", [], tmp_path, created_at)


def test_create_post_overwrite_replaces_existing_bundle(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 25, 12, 0, tzinfo=module.BRAZIL_TIMEZONE)
    module.create_post("Post repetido", ["velha"], tmp_path, created_at)

    output = module.create_post(
        "Post repetido", ["nova"], tmp_path, created_at, overwrite=True
    )

    assert 'tags = ["nova"]' in output.read_text(encoding="utf-8")


def test_create_post_recreates_bundle_after_index_deleted(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 25, 12, 0, tzinfo=module.BRAZIL_TIMEZONE)
    output = module.create_post("Post apagado", [], tmp_path, created_at)
    output.unlink()

    recreated = module.create_post("Post apagado", ["nova"], tmp_path, created_at)

    assert recreated == output
    assert 'tags = ["nova"]' in recreated.read_text(encoding="utf-8")


def test_create_post_rejects_empty_title(tmp_path):
    module = load_module()

    with pytest.raises(ValueError, match="cannot be empty"):
        module.create_post("   ", [], tmp_path)


def test_collect_tag_counts_orders_by_usage_then_alphabetically(tmp_path):
    module = load_module()
    write_post(
        tmp_path,
        "2026/01/01/post-a",
        '+++\ntitle = "A"\ntags = ["review", "filmes"]\n+++\n',
    )
    write_post(
        tmp_path,
        "2026/01/02/post-b",
        '+++\ntitle = "B"\ntags = ["review", "series"]\n+++\n',
    )
    write_post(
        tmp_path,
        "2026/01/03/post-c",
        '+++\ntitle = "C"\ntags = ["filmes"]\n+++\n',
    )

    assert module.collect_tag_counts(tmp_path) == [
        ("filmes", 2),
        ("review", 2),
        ("series", 1),
    ]


def test_collect_tag_counts_strips_whitespace_and_dedupes(tmp_path):
    module = load_module()
    write_post(
        tmp_path,
        "2026/01/01/post-a",
        '+++\ntitle = "A"\ntags = ["review "]\n+++\n',
    )
    write_post(
        tmp_path,
        "2026/01/02/post-b",
        '+++\ntitle = "B"\ntags = ["review"]\n+++\n',
    )

    assert module.collect_tag_counts(tmp_path) == [("review", 2)]


def test_collect_tag_counts_skips_files_without_toml_front_matter(tmp_path):
    module = load_module()
    write_post(
        tmp_path,
        "2026/01/01/post-a",
        '---\ntitle: "A"\n---\n',
    )
    write_post(
        tmp_path,
        "2026/01/02/post-b",
        '+++\ntitle = "B"\ntags = ["review"]\n+++\n',
    )

    assert module.collect_tag_counts(tmp_path) == [("review", 1)]


def test_collect_tag_counts_skips_invalid_toml(tmp_path):
    module = load_module()
    write_post(
        tmp_path,
        "2026/01/01/post-a",
        "+++\nthis is not valid toml\n+++\n",
    )
    write_post(
        tmp_path,
        "2026/01/02/post-b",
        '+++\ntitle = "B"\ntags = ["review"]\n+++\n',
    )

    assert module.collect_tag_counts(tmp_path) == [("review", 1)]


def test_collect_tag_counts_handles_posts_without_tags(tmp_path):
    module = load_module()
    write_post(
        tmp_path,
        "2026/01/01/post-a",
        '+++\ntitle = "A"\n+++\n',
    )

    assert module.collect_tag_counts(tmp_path) == []


def test_merge_tags_removes_duplicates_and_keeps_order():
    module = load_module()

    assert module.merge_tags(
        ["review", "series"], ["review", "hbo-max"]
    ) == ["review", "series", "hbo-max"]


def test_select_tags_fallback_parses_valid_indexes(monkeypatch):
    module = load_module()
    options = [("review", 3), ("series", 2), ("filmes", 1)]
    monkeypatch.setattr("builtins.input", lambda _: "1,3")

    assert module.select_tags_fallback(options) == ["review", "filmes"]


def test_select_tags_fallback_ignores_invalid_and_out_of_range_indexes(monkeypatch):
    module = load_module()
    options = [("review", 3), ("series", 2)]
    monkeypatch.setattr("builtins.input", lambda _: "0,1,abc,9,1")

    assert module.select_tags_fallback(options) == ["review"]


def test_select_tags_fallback_allows_empty_selection(monkeypatch):
    module = load_module()
    options = [("review", 3)]
    monkeypatch.setattr("builtins.input", lambda _: "")

    assert module.select_tags_fallback(options) == []


def test_select_tags_returns_empty_list_without_options():
    module = load_module()

    assert module.select_tags([]) == []
