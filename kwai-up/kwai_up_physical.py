#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from typing import Iterable

# Physical executor defaults to the Kwai Lite package found on the dedicated Redmi.
os.environ.setdefault("KWAI_UP_PACKAGE", "kwai.lite.video")

SAFE_PATH = pathlib.Path(__file__).with_name("kwai_up_safe.py")
SPEC = importlib.util.spec_from_file_location("kwai_up_safe_base", SAFE_PATH)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("KWAI_UP_STATE=FAILED_SAFE REASON=safe-core-load-failed")
safe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = safe
SPEC.loader.exec_module(safe)
ku = safe.ku

PACKAGE = os.getenv("KWAI_UP_PACKAGE", "kwai.lite.video").strip() or "kwai.lite.video"
ku.PACKAGE = PACKAGE

BASIS = f"{PACKAGE}.basis:id"
PRODUCT = f"{PACKAGE}.product:id"
PROFILE_TAB_ID = f"{BASIS}/id_home_bottom_tab_me"
RECORD_ID = f"{BASIS}/id_record_layout"
PREVIEW_ID = f"{BASIS}/preview_container"
EDITOR_NEXT_ID = f"{PRODUCT}/edit_post_next_step_button"
FINAL_POST_ID = f"{BASIS}/post"
EDITOR_ID = f"{BASIS}/editor"
PRIVACY_ID = f"{PRODUCT}/tv_select_permission"
REMOTE_DIR = "/sdcard/Movies/KwaiUp"
MEDIA_URI = "content://media/external/video/media"

HID_DESCRIPTOR = [
    0x05,0x01,0x09,0x06,0xA1,0x01,
    0x05,0x07,0x19,0xE0,0x29,0xE7,0x15,0x00,0x25,0x01,0x75,0x01,0x95,0x08,0x81,0x02,
    0x95,0x01,0x75,0x08,0x81,0x01,
    0x95,0x06,0x75,0x08,0x15,0x00,0x25,0x65,0x05,0x07,0x19,0x00,0x29,0x65,0x81,0x00,
    0xC0,
]

TAB = 0x2B
ENTER = 0x28
SHIFT = 0x02
CTRL = 0x01


def parse_nodes_full(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    keep = (
        "text", "content-desc", "resource-id", "class", "package",
        "clickable", "enabled", "selected", "checked", "bounds",
        "focusable", "focused",
    )
    return [{k: n.attrib.get(k, "") for k in keep} for n in root.iter("node")]


# Publisher.dump resolves this global at runtime. Add focus metadata only for this
# physical adapter process; the original publisher stays untouched on disk.
ku.parse_nodes = parse_nodes_full


def online_devices(raw: str) -> list[str]:
    devices: list[str] = []
    for line in raw.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def choose_serial(raw: str, requested: str = "") -> str:
    devices = online_devices(raw)
    if requested and requested in devices:
        return requested
    network = [d for d in devices if ":" in d]
    if len(network) == 1:
        return network[0]
    if len(devices) == 1:
        return devices[0]
    if requested:
        raise ku.KwaiUpError(f"adb-serial-stale:{requested}:online={len(devices)}")
    raise ku.KwaiUpError(f"adb-device-ambiguous:online={len(devices)}:network={len(network)}")


class PhysicalADB(ku.ADB):
    def __init__(self, serial: str = "") -> None:
        self.executable = os.getenv("KWAI_UP_ADB_BIN", "").strip() or "adb"
        probe = subprocess.run(
            [self.executable, "devices", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
        )
        if probe.returncode:
            raise ku.KwaiUpError(f"adb-list-failed:{probe.returncode}")
        self.serial = choose_serial(probe.stdout, serial)

    def _base(self) -> list[str]:
        cmd = [self.executable]
        if self.serial:
            cmd += ["-s", self.serial]
        return cmd


class HIDKeyboard:
    def __init__(self, adb: PhysicalADB, device_id: int = 301) -> None:
        self.adb = adb
        self.device_id = device_id
        self.proc: subprocess.Popen[str] | None = None

    def __enter__(self) -> "HIDKeyboard":
        self.proc = subprocess.Popen(
            self.adb._base() + ["shell", "hid", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self._emit({
            "id": self.device_id,
            "command": "register",
            "name": "KwaiUpPersistentKeyboard",
            "vid": 0x18D1,
            "pid": 0x4EE9,
            "bus": "usb",
            "descriptor": HID_DESCRIPTOR,
        })
        time.sleep(1.0)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.proc is None:
            return
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        finally:
            self.proc = None

    def _emit(self, event: dict[str, object]) -> None:
        if not self.proc or not self.proc.stdin:
            raise ku.KwaiUpError("hid-session-not-open")
        self.proc.stdin.write(json.dumps(event, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def key(self, code: int, modifier: int = 0, pause: float = 0.18) -> None:
        self._emit({
            "id": self.device_id,
            "command": "report",
            "report": [modifier, 0, code, 0, 0, 0, 0, 0],
        })
        time.sleep(0.07)
        self._emit({
            "id": self.device_id,
            "command": "report",
            "report": [0, 0, 0, 0, 0, 0, 0, 0],
        })
        time.sleep(pause)

    def tab(self, reverse: bool = False) -> None:
        self.key(TAB, SHIFT if reverse else 0)

    def enter(self) -> None:
        self.key(ENTER)

    @staticmethod
    def _ascii_key(ch: str) -> tuple[int, int]:
        if "a" <= ch <= "z":
            return 0x04 + ord(ch) - ord("a"), 0
        if "A" <= ch <= "Z":
            return 0x04 + ord(ch) - ord("A"), SHIFT
        if "1" <= ch <= "9":
            return 0x1E + ord(ch) - ord("1"), 0
        if ch == "0":
            return 0x27, 0
        direct = {
            " ": (0x2C, 0), "-": (0x2D, 0), "=": (0x2E, 0),
            "[": (0x2F, 0), "]": (0x30, 0), "\\": (0x31, 0),
            ";": (0x33, 0), "'": (0x34, 0), "`": (0x35, 0),
            ",": (0x36, 0), ".": (0x37, 0), "/": (0x38, 0),
        }
        shifted = {
            "!": (0x1E, SHIFT), "@": (0x1F, SHIFT), "#": (0x20, SHIFT),
            "$": (0x21, SHIFT), "%": (0x22, SHIFT), "^": (0x23, SHIFT),
            "&": (0x24, SHIFT), "*": (0x25, SHIFT), "(": (0x26, SHIFT),
            ")": (0x27, SHIFT), "_": (0x2D, SHIFT), "+": (0x2E, SHIFT),
            "{": (0x2F, SHIFT), "}": (0x30, SHIFT), "|": (0x31, SHIFT),
            ":": (0x33, SHIFT), '"': (0x34, SHIFT), "~": (0x35, SHIFT),
            "<": (0x36, SHIFT), ">": (0x37, SHIFT), "?": (0x38, SHIFT),
        }
        if ch in direct:
            return direct[ch]
        if ch in shifted:
            return shifted[ch]
        raise ku.KwaiUpError(f"caption-non-ascii-unsupported:U+{ord(ch):04X}")

    def type_ascii(self, text: str) -> None:
        for ch in text:
            code, mod = self._ascii_key(ch)
            self.key(code, mod, pause=0.035)


class PhysicalPublisher(safe.SafePublisher):
    def __init__(self, cfg: ku.Config) -> None:
        super().__init__(cfg, adb=PhysicalADB(cfg.serial))
        self.adb: PhysicalADB
        self.remote_media = ""

    def emit(self, state: str, **fields: object) -> None:
        fields.setdefault("serial", self.adb.serial)
        fields.setdefault("package", PACKAGE)
        super().emit(state, **fields)

    def probe(self) -> int:
        state = self.adb.run("get-state", check=False).strip()
        if state != "device":
            self.emit("FAILED_SAFE", reason="adb-device-unavailable", adb_state=state or "empty")
            return 20
        packages = self.adb.run("shell", "pm", "path", PACKAGE, check=False)
        if not packages.strip().startswith("package:"):
            self.emit("FAILED_SAFE", reason="kwai-package-missing")
            return 21
        hid = self.adb.run("shell", "command", "-v", "hid", check=False).strip()
        uhid = self.adb.run("shell", "sh", "-c", "test -w /dev/uhid && echo yes", check=False).strip()
        if not hid or uhid != "yes":
            self.emit("FAILED_SAFE", reason="hid-control-unavailable")
            return 22
        sdk = self.adb.run("shell", "getprop", "ro.build.version.sdk", check=False).strip()
        model = self.adb.run("shell", "getprop", "ro.product.model", check=False).strip()
        self.emit("PHYSICAL_PROBE_OK", sdk=sdk or "?", model=ku.safe_token(model, "unknown"), transport="hid-uhid")
        return 0

    def launcher_component(self) -> str:
        raw = self.adb.run(
            "shell", "cmd", "package", "resolve-activity", "--brief",
            "-c", "android.intent.category.LAUNCHER", PACKAGE,
            check=False,
        )
        for line in reversed(raw.splitlines()):
            line = line.strip()
            if line.startswith(PACKAGE + "/"):
                return line
        return f"{PACKAGE}/com.yxcorp.gifshow.tiny.TinyLaunchActivity"

    def cold_start_home(self, stage: str) -> list[dict[str, str]]:
        self.adb.run(
            "shell", "am", "start", "-S", "--activity-clear-task",
            "-n", self.launcher_component(), timeout=60,
        )
        deadline = time.time() + max(30, self.cfg.wait * 3)
        last: list[dict[str, str]] = []
        while time.time() < deadline:
            time.sleep(2)
            last = self.dump(stage, screenshot=False)
            if ku.find_id(last, PROFILE_TAB_ID) or ku.find_id(last, RECORD_ID):
                return last
        raise ku.KwaiUpError("kwai-lite-home-timeout")

    def focused_target(self, nodes: Iterable[dict[str, str]], rid: str) -> bool:
        return any(
            n.get("resource-id") == rid
            and n.get("focused") == "true"
            and n.get("focusable") == "true"
            for n in nodes
        )

    def focus_target(
        self,
        keyboard: HIDKeyboard,
        rid: str,
        stage: str,
        max_steps: int = 50,
        reverse: bool = False,
    ) -> list[dict[str, str]]:
        nodes = self.dump(stage + "-0", screenshot=False)
        if self.focused_target(nodes, rid):
            return nodes
        for step in range(1, max_steps + 1):
            keyboard.tab(reverse=reverse)
            nodes = self.dump(f"{stage}-{step}", screenshot=False)
            if self.focused_target(nodes, rid):
                return nodes
        raise ku.KwaiUpError(f"hid-focus-target-timeout:{rid.split('/')[-1]}")

    def verify_identity(self) -> int:
        expected = self.expected_account()
        pattern = safe.account_pattern(expected)
        home = self.cold_start_home("05-physical-auth-home")
        if safe.AUTH_REQUIRED_RE.search(ku.text_blob(home)):
            raise ku.KwaiUpError("auth-required")
        with HIDKeyboard(self.adb, 311) as keyboard:
            self.focus_target(keyboard, PROFILE_TAB_ID, "06-profile-tab", max_steps=30)
            keyboard.enter()
            time.sleep(2)
        deadline = time.time() + 25
        last_blob = ""
        while time.time() < deadline:
            nodes = self.dump("07-profile-identity", screenshot=False)
            last_blob = ku.text_blob(nodes)
            if safe.AUTH_REQUIRED_RE.search(last_blob):
                raise ku.KwaiUpError("auth-required")
            if pattern.search(last_blob.casefold()):
                self.emit("AUTHENTICATED_IDENTITY", account=expected.lstrip("@"))
                return 0
            time.sleep(2)
        raise ku.KwaiUpError("authenticated-identity-unverified")

    def stage_media(self) -> tuple[str, str, str]:
        source, sha, name = self.validate_input()
        self.clean_own_staging()
        remote = f"{REMOTE_DIR}/{name}"
        self.adb.run("push", str(source), remote, timeout=180)
        self.adb.run(
            "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{remote}",
        )
        time.sleep(3)
        raw = self.adb.run(
            "shell", "content", "query", "--uri", MEDIA_URI,
            "--projection", "_id:_display_name:_data:duration:width:height",
        )
        (self.cfg.artifacts / "mediastore.txt").write_text(raw, encoding="utf-8")
        matches = [line for line in raw.splitlines() if name in line]
        if len(matches) != 1:
            raise ku.KwaiUpError(f"staged-media-not-unique:matching={len(matches)}")
        self.remote_media = remote
        return sha, name, remote

    def open_album(self, remote: str) -> list[dict[str, str]]:
        self.adb.run(
            "shell", "am", "start", "-W",
            "-a", "android.intent.action.VIEW", "-d", "kwai://album",
            "--es", "album_scroll_to_path", remote,
            PACKAGE,
            timeout=60,
        )
        time.sleep(max(2, self.cfg.wait // 2))
        nodes = self.dump("11-physical-album")
        activity = self.current_activity()
        previews = [
            n for n in nodes
            if n.get("resource-id") == PREVIEW_ID
            and n.get("clickable") == "true"
            and ku.center(n.get("bounds", ""))
        ]
        if "VideoPhotoPickActivity" not in activity or not previews:
            raise ku.KwaiUpError(f"physical-album-mismatch:{activity or 'unknown'}")
        return nodes

    def navigate_to_final(self, remote: str) -> tuple[list[dict[str, str]], bool]:
        self.open_album(remote)
        with HIDKeyboard(self.adb, 312) as keyboard:
            self.focus_target(keyboard, PREVIEW_ID, "12-first-video", max_steps=40)
            keyboard.enter()
            time.sleep(max(2, self.cfg.wait // 2))
            editor = self.dump("13-physical-editor")
            activity = self.current_activity()
            if "EditorActivity" not in activity or not ku.find_id(editor, EDITOR_NEXT_ID):
                raise ku.KwaiUpError(f"physical-editor-mismatch:{activity or 'unknown'}")
            self.focus_target(keyboard, EDITOR_NEXT_ID, "13-editor-next", max_steps=45)
            keyboard.enter()
            time.sleep(max(2, self.cfg.wait // 2))
        final = self.dump("14-physical-final")
        activity = self.current_activity()
        post = ku.find_id(final, FINAL_POST_ID)
        field = ku.find_id(final, EDITOR_ID) or next((n for n in final if n.get("resource-id") == EDITOR_ID), None)
        privacy = ku.find_id(final, PRIVACY_ID) or next((n for n in final if n.get("resource-id") == PRIVACY_ID), None)
        if "ShareActivity" not in activity or not post or not field or not privacy:
            raise ku.KwaiUpError(f"physical-final-screen-mismatch:{activity or 'unknown'}")
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        public_ok = privacy_text in {"público", "publico", "public", "pãºblico", "pç§blico"}
        return final, public_ok

    def fill_caption(self, nodes: list[dict[str, str]]) -> None:
        caption = self.cfg.caption[:150]
        if not caption:
            return
        # HID typing is deliberately ASCII-only; never silently alter the requested caption.
        caption.encode("ascii")
        if not any(n.get("resource-id") == EDITOR_ID for n in nodes):
            raise ku.KwaiUpError("caption-field-missing")
        with HIDKeyboard(self.adb, 313) as keyboard:
            self.focus_target(keyboard, EDITOR_ID, "15-caption", max_steps=35)
            keyboard.key(0x04, CTRL)  # Ctrl+A
            keyboard.type_ascii(caption)
        time.sleep(1)

    def prepare(self) -> int:
        if self.probe() != 0:
            return 20
        self.verify_identity()
        sha, name, remote = self.stage_media()
        final, public_ok = self.navigate_to_final(remote)
        self.fill_caption(final)
        final = self.dump("21-physical-ready")
        post = ku.find_id(final, FINAL_POST_ID)
        privacy = ku.find_id(final, PRIVACY_ID) or next((n for n in final if n.get("resource-id") == PRIVACY_ID), None)
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        public_ok = public_ok and privacy_text in {"público", "publico", "public", "pãºblico", "pç§blico"}
        if not post:
            raise ku.KwaiUpError("publish-control-not-ready")
        if not public_ok:
            raise ku.KwaiUpError("privacy-not-confirmed-public")
        proof = {
            "version": 2,
            "physical": True,
            "package": PACKAGE,
            "serial": self.adb.serial,
            "job_id": self.cfg.job_id,
            "media_sha256": sha,
            "staged_name": name,
            "remote_media": remote,
            "caption": self.cfg.caption,
            "created_at": int(time.time()),
        }
        self.ready_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
        self.emit("READY_TO_PUBLISH", job=self.cfg.job_id, media=name, sha256=sha[:16], transport="hid-uhid")
        return 0

    def verify_after_post_physical(self) -> tuple[bool, str]:
        deadline = time.time() + self.cfg.verify_timeout
        saw_structural = False
        saw_text = False
        last_activity = ""
        for attempt in range(1, 1 + max(1, self.cfg.verify_timeout // 3)):
            if time.time() >= deadline:
                break
            last_activity = self.current_activity()
            try:
                nodes = self.dump(f"30-physical-after-{attempt}", screenshot=False)
                blob = ku.text_blob(nodes)
            except ku.HumanVerification:
                raise
            except Exception:
                time.sleep(3)
                continue
            if ku.FAILURE_RE.search(blob):
                return False, "visible-post-error"
            saw_text = saw_text or bool(ku.SUCCESS_RE.search(blob))
            structural = bool(last_activity) and PACKAGE in last_activity and "ShareActivity" not in last_activity
            saw_structural = saw_structural or structural
            if saw_text and saw_structural:
                return True, "textual-and-structural"
            time.sleep(3)
        reason = "verification-timeout"
        if saw_structural and not saw_text:
            reason = "structural-without-textual-proof"
        elif saw_text and not saw_structural:
            reason = "textual-without-structural-proof"
        return False, f"{reason}:{ku.safe_token(last_activity, 'unknown')}"

    def commit(self) -> int:
        proof = self.load_ready()
        if not proof.get("physical") or proof.get("package") != PACKAGE:
            raise ku.KwaiUpError("physical-ready-proof-mismatch")
        nodes = self.dump("25-physical-precommit")
        activity = self.current_activity()
        post = ku.find_id(nodes, FINAL_POST_ID)
        privacy = ku.find_id(nodes, PRIVACY_ID) or next((n for n in nodes if n.get("resource-id") == PRIVACY_ID), None)
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        if "ShareActivity" not in activity or not post:
            raise ku.KwaiUpError("publish-boundary-lost")
        if privacy_text not in {"público", "publico", "public", "pãºblico", "pç§blico"}:
            raise ku.KwaiUpError("privacy-not-confirmed-public")
        with HIDKeyboard(self.adb, 314) as keyboard:
            self.focus_target(keyboard, FINAL_POST_ID, "26-post-focus", max_steps=35)
            # Irreversible boundary starts only after exact resource-id focus is proven.
            self.emit("PUBLISH_REQUESTED", job=self.cfg.job_id, transport="hid-uhid")
            keyboard.enter()
        ok, evidence = self.verify_after_post_physical()
        if ok:
            self.emit("VERIFIED", evidence=evidence, job=self.cfg.job_id)
            self.ready_file.unlink(missing_ok=True)
            return 0
        self.emit("UNCERTAIN", reason=evidence, job=self.cfg.job_id)
        return 90

    def verify(self) -> int:
        self.load_ready()
        ok, evidence = self.verify_after_post_physical()
        if ok:
            self.emit("VERIFIED", evidence=evidence, job=self.cfg.job_id)
            self.ready_file.unlink(missing_ok=True)
            return 0
        self.emit("UNCERTAIN", reason=evidence, job=self.cfg.job_id)
        return 90


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "probe").strip().lower()
    if mode not in {"probe", "auth", "prepare", "commit", "verify"}:
        print("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-mode", flush=True)
        return 64
    cfg = ku.Config.from_env("probe" if mode == "auth" else mode)
    try:
        pub = PhysicalPublisher(cfg)
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
    except UnicodeEncodeError as exc:
        print(f"KWAI_UP_STATE=FAILED_SAFE REASON=caption-non-ascii-unsupported DETAIL=U+{ord(exc.object[exc.start]):04X}", flush=True)
        return 70
    except ku.HumanVerification as exc:
        print(f"KWAI_UP_STATE=FAILED_SAFE REASON=human-verification DETAIL={ku.safe_token(str(exc))}", flush=True)
        return 91
    except ku.KwaiUpError as exc:
        print(f"KWAI_UP_STATE=FAILED_SAFE REASON={ku.safe_token(str(exc), 'kwai-up-error')}", flush=True)
        return 70
    except Exception as exc:
        print(f"KWAI_UP_STATE=FAILED_SAFE REASON=unexpected DETAIL={ku.safe_token(type(exc).__name__)}", flush=True)
        return 79


if __name__ == "__main__":
    raise SystemExit(main())
