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


def test_create_post_rejects_existing_bundle(tmp_path):
    module = load_module()
    created_at = datetime(2026, 9, 25, 12, 0, tzinfo=module.BRAZIL_TIMEZONE)
    module.create_post("Post repetido", [], tmp_path, created_at)

    with pytest.raises(FileExistsError):
        module.create_post("Post repetido", [], tmp_path, created_at)


def test_create_post_rejects_empty_title(tmp_path):
    module = load_module()

    with pytest.raises(ValueError, match="cannot be empty"):
        module.create_post("   ", [], tmp_path)
