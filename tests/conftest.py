import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _run_hugo(tmp_path, extra_args=None, extra_env=None, quiet=True):
    """Runs a production build into tmp_path/public and returns the finished process."""
    return subprocess.run(
        [
            "hugo",
            "--source",
            str(ROOT),
            "--destination",
            str(tmp_path / "public"),
            "--cacheDir",
            str(tmp_path / "cache"),
            "--buildDrafts",
            *(["--quiet"] if quiet else []),
            *(extra_args or []),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "HUGO_PARAMS_SOCIAL_EMAIL": "leitor@example.com",
            "HUGO_PARAMS_ANALYTICS_GOATCOUNTER_CODE": "blog-de-teste",
            "HUGO_PARAMS_ANALYTICS_GOOGLE_ID": "G-TESTE1234",
            **(extra_env or {}),
        },
    )


def _build_site(tmp_path, extra_args=None, extra_env=None):
    result = _run_hugo(tmp_path, extra_args, extra_env)
    assert result.returncode == 0, result.stderr
    return tmp_path / "public"


@pytest.fixture
def built_site(tmp_path):
    """Builds the full site (with drafts) once per test and returns the public/ dir."""
    return _build_site(tmp_path)


@pytest.fixture(scope="session")
def built_site_session(tmp_path_factory):
    """Session-scoped build for read-only checks that don't need build args/isolation."""
    return _build_site(tmp_path_factory.mktemp("public-session"))
