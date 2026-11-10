import importlib.util
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "story_emulator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("story_emulator", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sdk_root_prefers_env_over_default():
    module = load_module()

    assert module.sdk_root({"ANDROID_HOME": "/sdk"}) == Path("/sdk")
    assert module.sdk_root({"ANDROID_SDK_ROOT": "/other"}) == Path("/other")
    assert module.sdk_root({}).name == "sdk"


def test_create_avd_writes_both_ini_files(tmp_path):
    module = load_module()
    sdk = tmp_path / "sdk"
    (sdk / module.SYSTEM_IMAGE).mkdir(parents=True)
    home = tmp_path / "avd"

    avd_dir = module.create_avd(sdk, home)

    config = (avd_dir / "config.ini").read_text(encoding="utf-8")
    assert "PlayStore.enabled=true\n" in config
    assert "hw.lcd.width=720\n" in config
    assert f"image.sysdir.1={module.SYSTEM_IMAGE}/\n" in config
    pointer = (home / "Stories.ini").read_text(encoding="utf-8")
    assert f"path={avd_dir}\n" in pointer


def test_create_avd_requires_the_system_image(tmp_path):
    module = load_module()

    with pytest.raises(module.EmulatorError, match="sdkmanager"):
        module.create_avd(tmp_path / "sdk", tmp_path / "avd")


def test_emulator_command_uses_fixed_port_and_optional_window():
    module = load_module()

    command = module.emulator_command(Path("/sdk"), window=True)

    assert command[:3] == ["/sdk/emulator/emulator", "-avd", "Stories"]
    assert ["-port", "5554"] == command[3:5]
    assert "-no-window" not in command
    assert "-no-window" in module.emulator_command(Path("/sdk"), window=False)


def test_device_state_reads_the_emulator_line():
    module = load_module()
    header = "List of devices attached\n"

    assert module.device_state(header + "emulator-5554\tdevice\n") == "device"
    assert module.device_state(header + "emulator-5554\toffline\n") == "offline"
    assert module.device_state(header + "192.168.0.10:5555\tdevice\n") is None


def test_stop_warns_when_the_snapshot_is_not_saved(monkeypatch, capsys):
    module = load_module()
    states = iter(["device", None])
    monkeypatch.setattr(module, "current_state", lambda: next(states))
    calls = []

    def fake_adb(*args):
        calls.append(args)
        stdout = "KO: not enough space\n" if args[:2] == ("emu", "avd") else "OK\n"
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(module, "adb", fake_adb)

    module.stop()

    assert calls == [("emu", "avd", "snapshot", "save", "default_boot"), ("emu", "kill")]
    assert "cold boots" in capsys.readouterr().out
