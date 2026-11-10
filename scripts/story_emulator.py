#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

AVD_NAME = "Stories"
PORT = 5554
SERIAL = f"emulator-{PORT}"
LOCALE = "pt-BR"
SYSTEM_IMAGE = "system-images/android-35/google_apis_playstore/arm64-v8a"
INSTAGRAM_PACKAGE = "com.instagram.android"
BOOT_TIMEOUT = 300
PLAY_STORE_PACKAGE = "com.android.vending"
SNAPSHOT = "default_boot"
# Google apps that run in the background and take memory Instagram needs.
# Disabled per user, so "adb shell pm enable PACKAGE" brings any of them back.
IDLE_PACKAGES = (
    "com.google.android.googlequicksearchbox",
    "com.google.android.apps.wellbeing",
    "com.google.android.as",
    "com.google.android.apps.messaging",
    "com.google.android.settings.intelligence",
)

# A light Play Store phone: Instagram runs in 3 GB, and publish_story.py works
# from on-screen bounds, so a smaller screen than the story is fine.
# Written by hand instead of with avdmanager, which needs a Java install.
AVD_CONFIG = {
    "AvdId": AVD_NAME,
    "avd.ini.displayname": AVD_NAME,
    "avd.ini.encoding": "UTF-8",
    "PlayStore.enabled": "true",
    "abi.type": "arm64-v8a",
    "hw.cpu.arch": "arm64",
    "hw.cpu.ncore": "4",
    "hw.ramSize": "3072",
    "disk.dataPartition.size": "8G",
    "hw.lcd.width": "720",
    "hw.lcd.height": "1600",
    "hw.lcd.density": "320",
    "hw.initialOrientation": "Portrait",
    "hw.keyboard": "yes",
    "hw.mainKeys": "no",
    "hw.gpu.enabled": "yes",
    "hw.gpu.mode": "host",
    "hw.sdCard": "no",
    "hw.camera.back": "virtualscene",
    "hw.camera.front": "emulated",
    "showDeviceFrame": "no",
    "skin.dynamic": "yes",
    "skin.name": "720x1600",
    "skin.path": "_no_skin",
    "image.sysdir.1": f"{SYSTEM_IMAGE}/",
    "tag.id": "google_apis_playstore",
    "tag.display": "Google Play",
    "target": "android-35",
    "fastboot.forceFastBoot": "yes",
}


class EmulatorError(RuntimeError):
    pass


def sdk_root(environ: dict[str, str] = os.environ) -> Path:
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if environ.get(name):
            return Path(environ[name])
    return Path.home() / "Library" / "Android" / "sdk"


def avd_home(environ: dict[str, str] = os.environ) -> Path:
    if environ.get("ANDROID_AVD_HOME"):
        return Path(environ["ANDROID_AVD_HOME"])
    return Path.home() / ".android" / "avd"


def render_ini(values: dict[str, str]) -> str:
    return "".join(f"{key}={value}\n" for key, value in values.items())


def create_avd(sdk: Path, home: Path) -> Path:
    if not (sdk / SYSTEM_IMAGE).is_dir():
        raise EmulatorError(
            f"System image missing: {sdk / SYSTEM_IMAGE}. Install it with"
            f" sdkmanager \"{SYSTEM_IMAGE.replace('/', ';')}\""
        )
    avd_dir = home / f"{AVD_NAME}.avd"
    avd_dir.mkdir(parents=True, exist_ok=True)
    (avd_dir / "config.ini").write_text(render_ini(AVD_CONFIG), encoding="utf-8")
    (home / f"{AVD_NAME}.ini").write_text(
        render_ini({
            "avd.ini.encoding": "UTF-8",
            "path": str(avd_dir),
            "path.rel": f"avd/{AVD_NAME}.avd",
            "target": "android-35",
        }),
        encoding="utf-8",
    )
    return avd_dir


def adb(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["adb", "-s", SERIAL, *args], capture_output=True, text=True, check=False
    )


def device_state(adb_devices_output: str) -> str | None:
    # "device" once usable; "offline" while booting or shutting down.
    for line in adb_devices_output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == SERIAL:
            return parts[1]
    return None


def current_state() -> str | None:
    return device_state(
        subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, check=False
        ).stdout
    )


def emulator_command(sdk: Path, window: bool) -> list[str]:
    command = [
        str(sdk / "emulator" / "emulator"),
        "-avd", AVD_NAME,
        "-port", str(PORT),
        "-no-boot-anim",
        # "auto" can fall back to rendering on the CPU (SwiftShader), which
        # makes Instagram crawl; the Mac's GPU is much faster.
        "-gpu", "host",
    ]
    if not window:
        command.append("-no-window")
    return command


def wait_for_boot(timeout: float = BOOT_TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if adb("shell", "getprop", "sys.boot_completed").stdout.strip() == "1":
            return
        time.sleep(2)
    raise EmulatorError(f"{SERIAL} did not finish booting in {timeout:.0f}s")


def has_instagram() -> bool:
    output = adb("shell", "pm", "list", "packages", INSTAGRAM_PACKAGE).stdout
    return f"package:{INSTAGRAM_PACKAGE}" in output.split()


def configure_system() -> None:
    # Every setting persists, but applying them on each start is cheap and
    # undoes anything changed by hand.
    # Fewer frames to render, and screens settle sooner for the selectors.
    for scale in ("window_animation_scale", "transition_animation_scale",
                  "animator_duration_scale"):
        adb("shell", "settings", "put", "global", scale, "0")
    for package in IDLE_PACKAGES:
        adb("shell", "pm", "disable-user", "--user", "0", package)
    # The emulator's -change-locale needs root, which Play Store images lack.
    # This setting does without it, but only applies on the next boot.
    adb("shell", "settings", "put", "system", "system_locales", LOCALE)


def configure_instagram() -> None:
    # Its background updates are the heaviest load after a boot; start turns
    # it back on when Instagram is missing.
    adb("shell", "pm", "disable-user", "--user", "0", PLAY_STORE_PACKAGE)
    # Applies right away, unlike the system locale.
    adb("shell", "cmd", "locale", "set-app-locales", INSTAGRAM_PACKAGE, "--locales", LOCALE)
    # On a phone the user answers the photo and camera dialogs; this emulator
    # only exists to post stories, so grant them up front.
    for permission in ("READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "CAMERA", "RECORD_AUDIO"):
        adb("shell", "pm", "grant", INSTAGRAM_PACKAGE, f"android.permission.{permission}")


def start(sdk: Path, home: Path, log_path: Path, window: bool = True) -> None:
    # Rewritten on every start so changes to AVD_CONFIG reach an existing AVD.
    create_avd(sdk, home)

    # Any state counts: launching again while it boots would clash on the port.
    if current_state() is None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Booting {AVD_NAME} (log: {log_path})...")
        with log_path.open("w") as log:
            subprocess.Popen(
                emulator_command(sdk, window),
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    else:
        print(f"{SERIAL} is already running.")
    subprocess.run(["adb", "-s", SERIAL, "wait-for-device"], check=False)
    wait_for_boot()
    configure_system()

    if not has_instagram():
        adb("shell", "pm", "enable", PLAY_STORE_PACKAGE)
        adb(
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", f"market://details?id={INSTAGRAM_PACKAGE}",
        )
        print(
            "Instagram is not installed: sign in to the Play Store on the"
            " emulator (just opened on the Instagram page), install it, log in,"
            " and start this again."
        )
        return

    configure_instagram()
    print(
        f"Ready. Publish with:\n"
        f"  python3 scripts/publish_story.py stories/<slug>.json"
        f" --device {SERIAL} --confirm"
    )


def stop() -> None:
    if current_state() is None:
        print(f"{SERIAL} is not running.")
        return
    # "emu kill" skips the Quick Boot snapshot; without one every start is a
    # cold boot, slowed down by Google apps catching up for minutes.
    print("Saving the Quick Boot snapshot...")
    saved = adb("emu", "avd", "snapshot", "save", SNAPSHOT).stdout
    if "OK" not in saved.split():
        # Usually the Mac swapping: the emulator falls back to a cold boot.
        print(f"Warning: the snapshot was not saved ({saved.strip() or 'no reply'});"
              " the next start cold boots.")
    adb("emu", "kill")
    deadline = time.monotonic() + 30
    while current_state() is not None and time.monotonic() < deadline:
        time.sleep(1)
    print(f"Stopped {SERIAL}.")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Run an Android emulator with Instagram for"
        " publish_story.py, instead of a phone."
    )
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Boot without the emulator window (once Instagram is set up)",
    )
    args = parser.parse_args()

    try:
        if args.action == "stop":
            stop()
        else:
            log_path = repo_root / "stories" / "debug" / "emulator.log"
            start(sdk_root(), avd_home(), log_path, window=not args.no_window)
    except (OSError, EmulatorError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
