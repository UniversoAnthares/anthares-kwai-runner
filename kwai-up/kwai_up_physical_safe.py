#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import re
import struct
import sys
import time

# Reuse the proven safety semantics, identity gate and post verification.
import kwai_up_safe as ks

ku = ks.ku
PACKAGE = os.getenv("KWAI_UP_PACKAGE", "kwai.lite.video").strip() or "kwai.lite.video"
if not re.fullmatch(r"[A-Za-z0-9_.]+", PACKAGE):
    raise SystemExit("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-package")

# Physical executor contract. Kwai Lite uses basis + product resource namespaces.
ku.PACKAGE = PACKAGE
BASIS = f"{PACKAGE}.basis:id/"
PRODUCT = f"{PACKAGE}.product:id/" if PACKAGE == "kwai.lite.video" else f"{PACKAGE}.ca_product:id/"
PROFILE = BASIS if PACKAGE == "kwai.lite.video" else f"{PACKAGE}.basis_extension:id/"
ku.RECORD_ID = BASIS + "id_record_layout"
ku.FAKE_ADD_ID = BASIS + "fake_add_button"
ku.PREVIEW_CONTAINER_ID = BASIS + "preview_container"
ku.NEXT_ID = PRODUCT + ("edit_post_next_step_button" if PACKAGE == "kwai.lite.video" else "edit_next_button")
ku.FINAL_POST_ID = BASIS + "post"
ku.PRIVACY_ID = PRODUCT + "tv_select_permission"
ku.EDITOR_ID = BASIS + "editor"
ku.PROFILE_TAB_IDS = (BASIS + "id_home_bottom_tab_me", BASIS + "fake_me_button")
ku.PROFILE_ROOT_ID = PROFILE + "profile_root"
ku.PROFILE_THUMB_ID = PROFILE + "thumb"
ku.NOTIFICATION_CLOSE_ID = f"{PACKAGE}:id/iv_close"
ku.CREATOR_GUIDE_CLOSE_ID = PROFILE + "fmy_guide_close"

if "KWAI_UP_ARTIFACT_DIR" not in os.environ:
    os.environ["KWAI_UP_ARTIFACT_DIR"] = str(pathlib.Path.home() / ".kwai-up" / "artifacts")

# Single-touch HID descriptor: Tip Switch + In Range + absolute X/Y (0..32767).
TOUCH_RDESC = bytes([
    0x05, 0x0D, 0x09, 0x04, 0xA1, 0x01, 0x09, 0x22, 0xA1, 0x02,
    0x09, 0x42, 0x09, 0x32, 0x15, 0x00, 0x25, 0x01, 0x75, 0x01,
    0x95, 0x02, 0x81, 0x02, 0x75, 0x06, 0x95, 0x01, 0x81, 0x03,
    0x05, 0x01, 0x09, 0x30, 0x09, 0x31, 0x16, 0x00, 0x00, 0x26,
    0xFF, 0x7F, 0x36, 0x00, 0x00, 0x46, 0xFF, 0x7F, 0x75, 0x10,
    0x95, 0x02, 0x81, 0x02, 0xC0, 0xC0,
])


def _create_event() -> bytes:
    name = b"KwaiUp Virtual Touch"
    return (
        struct.pack("<I", 11)
        + name.ljust(128, b"\0")
        + bytes(64)
        + bytes(64)
        + struct.pack("<HHIIII", len(TOUCH_RDESC), 3, 0x1209, 0x0001, 1, 0)
        + TOUCH_RDESC
    )


def _input_event(tip: bool, x: int, y: int, width: int, height: int) -> bytes:
    hx = max(0, min(32767, round(x * 32767 / width)))
    hy = max(0, min(32767, round(y * 32767 / height)))
    report = struct.pack("<BHH", 0x03 if tip else 0x00, hx, hy)
    return struct.pack("<IH", 12, len(report)) + report


class PhysicalSafePublisher(ks.SafePublisher):
    def _display_size(self) -> tuple[int, int]:
        raw = self.adb.run("shell", "wm", "size", check=False)
        m = re.search(r"Physical size:\s*(\d+)x(\d+)", raw)
        if not m:
            m = re.search(r"(\d+)x(\d+)", raw)
        if not m:
            raise ku.KwaiUpError("physical-display-size-unavailable")
        width, height = map(int, m.groups())
        if width < 300 or height < 500:
            raise ku.KwaiUpError("physical-display-size-invalid")
        return width, height

    def _uhid_available(self) -> bool:
        raw = self.adb.run("shell", "sh", "-c", "test -w /dev/uhid && echo YES || echo NO", check=False)
        return "YES" in raw

    def _uhid_touch(self, x: int, y: int, hold: float = 0.10) -> None:
        if not self._uhid_available():
            raise ku.KwaiUpError("uhid-unavailable")
        width, height = self._display_size()
        local = self.cfg.artifacts / "uhid"
        local.mkdir(parents=True, exist_ok=True)
        files = {
            "create.bin": _create_event(),
            "down.bin": _input_event(True, x, y, width, height),
            "up.bin": _input_event(False, x, y, width, height),
            "destroy.bin": struct.pack("<I", 1),
        }
        remote_dir = "/data/local/tmp/kwaiup-uhid"
        self.adb.run("shell", "mkdir", "-p", remote_dir)
        for name, data in files.items():
            path = local / name
            path.write_bytes(data)
            self.adb.run("push", str(path), f"{remote_dir}/{name}")
        hold = max(0.05, min(2.0, hold))
        script = (
            f"(cat {remote_dir}/create.bin; sleep 0.45; "
            f"cat {remote_dir}/down.bin; sleep {hold:.2f}; "
            f"cat {remote_dir}/up.bin; sleep 0.45; "
            f"cat {remote_dir}/destroy.bin) > /dev/uhid"
        )
        out = self.adb.run("shell", "sh", "-c", script, timeout=15, check=False)
        if "Permission denied" in out or "not permitted" in out.lower():
            raise ku.KwaiUpError("uhid-touch-denied")

    def tap_node(self, node: dict[str, str], pause: float = 2.0) -> None:
        point = ku.center(node.get("bounds", ""))
        if not point:
            raise ku.KwaiUpError("node-without-bounds")
        self._uhid_touch(point[0], point[1])
        time.sleep(pause)

    def long_press_node(self, node: dict[str, str]) -> None:
        point = ku.center(node.get("bounds", ""))
        if not point:
            raise ku.KwaiUpError("node-without-bounds")
        self._uhid_touch(point[0], point[1], hold=1.2)
        time.sleep(2)

    def stage_media(self) -> tuple[str, str]:
        source, sha, name = self.validate_input()
        self.clean_own_staging()
        remote = f"{ku.REMOTE_DIR}/{name}"
        self.adb.run("push", str(source), remote, timeout=180)
        self.adb.run(
            "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{remote}",
        )
        time.sleep(4)
        raw = self.query_media()
        (self.cfg.artifacts / "mediastore.txt").write_text(raw, encoding="utf-8")
        rows = self.media_rows(raw)
        matching = [row for row in rows if f"_display_name={name}" in row or name in row]
        if len(matching) != 1:
            raise ku.KwaiUpError(f"staged-media-not-unique:matching={len(matching)}")
        self._staged_remote = remote
        return sha, name

    def navigate_to_final(self) -> tuple[list[dict[str, str]], bool]:
        remote = getattr(self, "_staged_remote", "")
        if not remote:
            raise ku.KwaiUpError("staged-media-path-missing")

        self.adb.run("shell", "am", "force-stop", PACKAGE, check=False)
        self.adb.run(
            "shell", "am", "start", "-W", "-a", "android.intent.action.VIEW",
            "-d", "kwai://album", "-p", PACKAGE,
            "--es", "album_scroll_to_path", remote,
            "--ez", "album_select_as_result", "true",
            "--ei", "album_target_select_index", "0",
            timeout=60,
        )
        time.sleep(max(3, self.cfg.wait // 2))
        album = self.dismiss_known_overlays(self.dump("11-physical-album"), "11-physical-album")
        previews = [
            n for n in album
            if n.get("resource-id") == ku.PREVIEW_CONTAINER_ID
            and n.get("clickable") == "true"
            and ku.center(n.get("bounds", ""))
        ]
        if not previews:
            raise ku.KwaiUpError("physical-target-preview-missing")
        previews.sort(key=lambda n: ku.bounds_tuple(n.get("bounds", "")) or (9999, 9999, 9999, 9999))
        self.tap_node(previews[0], max(3, self.cfg.wait // 2))

        editor = self.dismiss_known_overlays(self.dump("13-physical-editor"), "13-physical-editor")
        if "EditorActivity" not in self.current_activity():
            raise ku.KwaiUpError("physical-editor-activity-mismatch")
        next_button = ku.find_id(editor, ku.NEXT_ID)
        if not next_button:
            raise ku.KwaiUpError("editor-next-missing")
        self.tap_node(next_button, max(3, self.cfg.wait // 2))

        final = self.dismiss_known_overlays(self.dump("14-physical-final"), "14-physical-final")
        activity = self.current_activity()
        post = ku.find_id(final, ku.FINAL_POST_ID)
        field = ku.find_id(final, ku.EDITOR_ID) or next((n for n in final if n.get("resource-id") == ku.EDITOR_ID), None)
        if "ShareActivity" not in activity or not post or not field:
            raise ku.KwaiUpError(f"final-screen-mismatch:{activity or 'unknown'}")
        privacy = ku.find_id(final, ku.PRIVACY_ID) or next((n for n in final if n.get("resource-id") == ku.PRIVACY_ID), None)
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        public_ok = privacy_text in {"público", "publico", "public", "pÇ§blico"}
        return final, public_ok

    def fill_caption(self, nodes: list[dict[str, str]]) -> None:
        # Captionless publishing is fully automated now. Text injection on this
        # MIUI build remains fail-closed until a verified keyboard path is added.
        if self.cfg.caption:
            raise ku.KwaiUpError("physical-caption-input-not-yet-verified")


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "probe").strip().lower()
    if mode not in {"probe", "auth", "prepare", "commit", "verify"}:
        print("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-mode", flush=True)
        return 64
    cfg = ku.Config.from_env("probe" if mode == "auth" else mode)
    pub = PhysicalSafePublisher(cfg)
    try:
        if mode == "probe":
            return pub.probe()
        if mode == "auth":
            if pub.probe() != 0:
                return 20
            return pub.verify_identity()
        if mode == "prepare":
            return pub.prepare()
        if mode == "commit":
            return pub.commit()
        return pub.verify()
    except ku.HumanVerification as exc:
        pub.emit("FAILED_SAFE", reason="human-verification", detail=ku.safe_token(str(exc)))
        return 91
    except ku.KwaiUpError as exc:
        pub.emit("FAILED_SAFE", reason=ku.safe_token(str(exc), "kwai-up-error"))
        return 70
    except Exception as exc:
        pub.emit("FAILED_SAFE", reason="unexpected", detail=ku.safe_token(type(exc).__name__))
        return 79


if __name__ == "__main__":
    raise SystemExit(main())
