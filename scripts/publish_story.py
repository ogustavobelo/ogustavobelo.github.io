#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

INSTAGRAM_PACKAGE = "com.instagram.android"
REMOTE_DIR = "/sdcard/DCIM/Stories"
DEVICE_ENV = "STORY_ADB_DEVICE"
WAIT_TIMEOUT = 10
# Relative height where the link sticker is dropped: inside the band that
# create_story.py leaves free below the text.
STICKER_TARGET_Y = 0.95

# Instagram changes its UI often: every step tries these selectors in order
# (pt-BR first, then English), so a fix is usually a new entry here.
SELECTORS: dict[str, list[dict]] = {
    "create": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/action_bar_left_button"},
        {"description": "Criar"},
        {"descriptionContains": "Nova publicação"},
        {"description": "Create"},
        {"descriptionContains": "New post"},
    ],
    "permission_dialog": [
        {"textContains": "Permitir"},
        {"textContains": "Allow"},
    ],
    "story_tab": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/cam_dest_story"},
        {"text": "STORY"},
    ],
    "gallery": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/gallery_preview_button"},
        {"description": "Galeria"},
        {"description": "Gallery"},
    ],
    "gallery_item": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/gallery_grid_item_thumbnail"},
    ],
    "stickers": [
        {"description": "Figurinhas"},
        {"description": "Stickers"},
    ],
    "link_sticker": [
        {"description": "Figurinha de link"},
        {"description": "Link sticker"},
    ],
    "link_input": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/link_sticker_list_web_url_edit_text"},
        {"className": "android.widget.EditText"},
    ],
    "link_done": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/link_sticker_list_done_button"},
        {"text": "Concluir"},
        {"text": "Done"},
    ],
    # The link sticker once placed on the story.
    "placed_sticker": [
        {"descriptionStartsWith": "Figurinhas. Toque e mantenha"},
        {"descriptionStartsWith": "Stickers. Tap and hold"},
    ],
    "music_overlay": [
        {"descriptionStartsWith": "Figurinha de sobreposição de música"},
    ],
    "story_preview": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/camera_photo_texture_view"},
    ],
    "share": [
        {"resourceId": f"{INSTAGRAM_PACKAGE}:id/your_story_share_shortcut_button"},
        {"text": "Seu story"},
        {"descriptionContains": "Seu story"},
        {"text": "Compartilhar"},
        {"text": "Your story"},
        {"descriptionContains": "Your story"},
        {"text": "Share"},
    ],
}


class Story(NamedTuple):
    title: str
    url: str
    image: Path
    slug: str


class StepFailed(RuntimeError):
    pass


def load_story(metadata_path: str | Path) -> Story:
    metadata_path = Path(metadata_path)
    if metadata_path.suffix == ".png":
        metadata_path = metadata_path.with_suffix(".json")
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    image = metadata_path.parent / data["image"]
    if not image.is_file():
        raise FileNotFoundError(f"Story image not found: {image}")
    if not data.get("url"):
        raise ValueError(f"No url in {metadata_path}")
    return Story(
        title=data.get("title", ""), url=data["url"], image=image, slug=image.stem
    )


def resolve_device(cli_value: str | None, environ: dict[str, str] = os.environ) -> str:
    device = cli_value or environ.get(DEVICE_ENV, "")
    if not device:
        raise ValueError(
            f"No device given: pass --device IP:PORT or set {DEVICE_ENV}"
        )
    return device


def adb_command(device: str, *args: str) -> list[str]:
    return ["adb", "-s", device, *args]


def run_adb(*args: str, device: str | None = None) -> str:
    command = adb_command(device, *args) if device else ["adb", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise StepFailed(f"{' '.join(command)} failed: {result.stderr.strip()}")
    return result.stdout


def connected_devices(adb_devices_output: str) -> list[str]:
    devices = []
    for line in adb_devices_output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def connect(device: str) -> None:
    # A USB serial has no port; only network devices need "adb connect".
    if ":" in device:
        output = run_adb("connect", device)
        if "connected" not in output:
            raise StepFailed(f"Could not connect to {device}: {output.strip()}")
    if device not in connected_devices(run_adb("devices")):
        raise StepFailed(
            f"{device} is not available. Is wireless debugging on and paired"
            " (adb pair IP:PORT)?"
        )


def remote_path(story: Story) -> str:
    return f"{REMOTE_DIR}/{story.slug}.png"


def push_image(device: str, story: Story) -> str:
    target = remote_path(story)
    run_adb("shell", "mkdir", "-p", REMOTE_DIR, device=device)
    run_adb("push", str(story.image), target, device=device)
    # Indexes the file so it shows up first in Instagram's gallery picker.
    run_adb(
        "shell", "am", "broadcast",
        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", f"file://{target}",
        device=device,
    )
    return target


def center(bounds: dict) -> tuple[int, int]:
    return (bounds["left"] + bounds["right"]) // 2, (bounds["top"] + bounds["bottom"]) // 2


class Publisher:
    def __init__(self, device, serial: str, story: Story, debug_dir: Path):
        self.d = device
        self.serial = serial
        self.story = story
        self.debug_dir = debug_dir
        self.step = 0

    def snapshot(self, name: str) -> None:
        self.step += 1
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.d.screenshot(str(self.debug_dir / f"{self.step:02d}-{name}.png"))

    def find(self, key: str, timeout: float = WAIT_TIMEOUT):
        for selector in SELECTORS[key]:
            element = self.d(**selector)
            if element.wait(timeout=timeout / len(SELECTORS[key])):
                return element
        self.snapshot(f"missing-{key}")
        raise StepFailed(
            f"Could not find '{key}' on screen; see {self.debug_dir} and"
            " update SELECTORS"
        )

    def input(self, *args: object) -> None:
        # The story editor ignores uiautomator2's injected clicks and drags,
        # but takes adb's own input events.
        run_adb("shell", "input", *map(str, args), device=self.serial)

    def tap(self, key: str, timeout: float = WAIT_TIMEOUT) -> None:
        self.input("tap", *center(self.find(key, timeout).info["bounds"]))

    def open_story_camera(self) -> None:
        self.d.app_start(INSTAGRAM_PACKAGE, stop=True)
        self.find("create", timeout=WAIT_TIMEOUT * 2)
        self.snapshot("home")
        self.tap("create")
        self.check_permission_dialog()
        self.tap("story_tab")
        self.snapshot("story-camera")

    def check_permission_dialog(self) -> None:
        # Granting Instagram access to the gallery is left to the user.
        if self.d(**SELECTORS["permission_dialog"][0]).wait(timeout=2):
            self.snapshot("permission")
            raise StepFailed(
                "Instagram is asking for photo access: answer it on the phone"
                " and run the script again"
            )

    def pick_latest_image(self) -> None:
        self.tap("gallery")
        self.input("tap", *center(self.find("gallery_item")[0].info["bounds"]))
        self.snapshot("image-selected")

    def add_link_sticker(self) -> None:
        self.d.clipboard = self.story.url
        self.tap("stickers")
        self.tap("link_sticker")
        self.find("link_input").set_text(self.story.url)
        self.snapshot("link-typed")
        self.tap("link_done")

        # The sticker lands in the middle of the story; drag it to the band
        # left free at the bottom of the image.
        x, y = center(self.find("placed_sticker").info["bounds"])
        preview = self.find("story_preview").info["bounds"]
        target_y = preview["top"] + int(
            (preview["bottom"] - preview["top"]) * STICKER_TARGET_Y
        )
        self.input("swipe", x, y, x, target_y, 1500)
        self.snapshot("link-sticker")

    def check_music(self) -> None:
        # Instagram may attach a suggested song (shown as lyrics) to the story.
        if self.d(**SELECTORS["music_overlay"][0]).exists:
            self.snapshot("music")
            raise StepFailed(
                "Instagram added a song to the story: remove it on the phone,"
                " check the link sticker, and tap 'Seu story' to post"
            )

    def share(self) -> None:
        self.tap("share")
        if not self.d(**SELECTORS["share"][0]).wait_gone(timeout=WAIT_TIMEOUT):
            self.snapshot("share-failed")
            raise StepFailed("Tapped 'Seu story' but the editor is still open")
        self.snapshot("shared")


def publish(story: Story, device: str, debug_dir: Path, share: bool = True) -> None:
    try:
        import uiautomator2 as u2
    except ImportError as exc:
        raise StepFailed("uiautomator2 is missing: pip install uiautomator2") from exc

    print(f"Connecting to {device}...")
    connect(device)
    print(f"Sending {story.image.name}...")
    push_image(device, story)

    publisher = Publisher(u2.connect(device), device, story, debug_dir)
    print("Opening the story camera...")
    publisher.open_story_camera()
    publisher.pick_latest_image()
    print(f"Adding link sticker: {story.url}")
    publisher.add_link_sticker()
    publisher.check_music()
    if not share:
        print("Stopped before sharing (--no-share). Review it on the phone.")
        return
    publisher.share()
    print("Story shared.")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Publish a story made by create_story.py on an Android"
        " phone over adb, with a link sticker to the post."
    )
    parser.add_argument("story", help="stories/<slug>.json (or its .png)")
    parser.add_argument("--device", help=f"adb device, e.g. 192.168.0.10:5555 (default: ${DEVICE_ENV})")
    parser.add_argument(
        "--no-share",
        action="store_true",
        help="Stop right before sharing, to review the story on the phone",
    )
    args = parser.parse_args()

    try:
        story = load_story(args.story)
        device = resolve_device(args.device)
        debug_dir = repo_root / "stories" / "debug" / story.slug
        publish(story, device, debug_dir, share=not args.no_share)
    except (OSError, ValueError, KeyError, StepFailed) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
