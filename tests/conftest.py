import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _build_site(tmp_path, extra_args=None):
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
            *(extra_args or []),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "HUGO_PARAMS_SOCIAL_EMAIL": "leitor@example.com",
            "HUGO_PARAMS_ANALYTICS_GOATCOUNTER_CODE": "blog-de-teste",
        },
    )

    assert result.returncode == 0, result.stderr
    return destination


@pytest.fixture
def built_site(tmp_path):
    """Builds the full site (with drafts) once per test and returns the public/ dir."""
    return _build_site(tmp_path)


@pytest.fixture(scope="session")
def built_site_session(tmp_path_factory):
    """Session-scoped build for read-only checks that don't need build args/isolation."""
    return _build_site(tmp_path_factory.mktemp("public-session"))
