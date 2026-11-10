import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "publish_story.py"


def load_module():
    spec = importlib.util.spec_from_file_location("publish_story", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_story(tmp_path: Path) -> Path:
    (tmp_path / "meu-post.png").write_bytes(b"png")
    metadata = tmp_path / "meu-post.json"
    metadata.write_text(
        json.dumps({"title": "T", "url": "https://x.y/p/", "image": "meu-post.png"}),
        encoding="utf-8",
    )
    return metadata


def fake_run(calls, outputs=None):
    def run(command, **kwargs):
        calls.append(command)
        stdout = (outputs or {}).get(command[1] if command[1] != "-s" else command[3], "")
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    return run


def test_load_story_accepts_json_or_png(tmp_path):
    module = load_module()
    metadata = write_story(tmp_path)

    story = module.load_story(metadata)

    assert story.url == "https://x.y/p/"
    assert story.image == tmp_path / "meu-post.png"
    assert story.slug == "meu-post"
    assert module.load_story(tmp_path / "meu-post.png") == story


def test_load_story_requires_the_image(tmp_path):
    module = load_module()
    metadata = write_story(tmp_path)
    (tmp_path / "meu-post.png").unlink()

    with pytest.raises(FileNotFoundError):
        module.load_story(metadata)


def test_resolve_device_prefers_cli_over_env():
    module = load_module()
    env = {module.DEVICE_ENV: "10.0.0.2:5555"}

    assert module.resolve_device("10.0.0.3:4444", env) == "10.0.0.3:4444"
    assert module.resolve_device(None, env) == "10.0.0.2:5555"
    with pytest.raises(ValueError):
        module.resolve_device(None, {})


def test_connect_checks_the_device_list(monkeypatch):
    module = load_module()
    calls = []
    outputs = {
        "connect": "connected to 10.0.0.2:5555\n",
        "devices": "List of devices attached\n10.0.0.2:5555\tdevice\nabc\toffline\n",
    }
    monkeypatch.setattr(module.subprocess, "run", fake_run(calls, outputs))

    module.connect("10.0.0.2:5555")
    assert calls == [["adb", "connect", "10.0.0.2:5555"], ["adb", "devices"]]

    with pytest.raises(module.StepFailed):
        module.connect("abc")


def test_push_image_copies_and_indexes_the_file(tmp_path, monkeypatch):
    module = load_module()
    story = module.load_story(write_story(tmp_path))
    calls = []
    monkeypatch.setattr(module.subprocess, "run", fake_run(calls))

    target = module.push_image("dev", story)

    assert target == "/sdcard/DCIM/Stories/meu-post.png"
    assert calls[1] == ["adb", "-s", "dev", "push", str(story.image), target]
    assert calls[2][-2:] == ["-d", f"file://{target}"]


class FakeElement:
    def __init__(self, device, selector):
        self.device = device
        self.selector = selector

    @property
    def exists(self):
        self.device.queries.append(self.selector)
        return self.selector in self.device.visible_after and (
            len(self.device.queries) > self.device.visible_after[self.selector]
        )


class FakeDevice:
    def __init__(self, visible_after):
        self.visible_after = visible_after
        self.queries = []

    def __call__(self, **selector):
        return FakeElement(self, tuple(selector.items()))

    def screenshot(self, path):
        Path(path).write_bytes(b"png")


def test_find_keeps_trying_every_selector_until_one_shows_up(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)
    first = tuple(module.SELECTORS["create"][0].items())
    # The screen shows up only after a few passes over all the selectors.
    device = FakeDevice({first: 3 * len(module.SELECTORS["create"])})
    publisher = module.Publisher(device, "serial", None, tmp_path)

    element = publisher.find("create", timeout=60)

    assert element.selector == first
    assert len(device.queries) > len(module.SELECTORS["create"])


def test_find_gives_up_with_a_screenshot(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.time, "sleep", lambda seconds: None)
    publisher = module.Publisher(FakeDevice({}), "serial", None, tmp_path)

    with pytest.raises(module.StepFailed, match="'create'"):
        publisher.find("create", timeout=0)

    assert (tmp_path / "01-missing-create.png").is_file()
