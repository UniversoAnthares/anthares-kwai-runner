#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except Exception:  # pragma: no cover - probe reports this before live use
    Image = None

PACKAGE = "com.kwai.video"
MEDIA_URI = "content://media/external/video/media"
REMOTE_DIR = "/sdcard/Movies/KwaiUp"
RECORD_ID = "com.kwai.video.basis:id/id_record_layout"
FAKE_ADD_ID = "com.kwai.video.basis:id/fake_add_button"
PREVIEW_CONTAINER_ID = "com.kwai.video.basis:id/preview_container"
NEXT_ID = "com.kwai.video.ca_product:id/edit_next_button"
FINAL_POST_ID = "com.kwai.video.basis:id/post"
PRIVACY_ID = "com.kwai.video.ca_product:id/tv_select_permission"
EDITOR_ID = "com.kwai.video.basis:id/editor"
PROFILE_TAB_IDS = (
    "com.kwai.video.basis:id/id_home_bottom_tab_me",
    "com.kwai.video.basis:id/fake_me_button",
)
PROFILE_ROOT_ID = "com.kwai.video.basis_extension:id/profile_root"
PROFILE_THUMB_ID = "com.kwai.video.basis_extension:id/thumb"
NOTIFICATION_CLOSE_ID = "com.kwai.video:id/iv_close"
CREATOR_GUIDE_CLOSE_ID = "com.kwai.video.basis_extension:id/fmy_guide_close"

HUMAN_RE = re.compile(r"captcha|verifica|verification|security check|confirme", re.I)
SUCCESS_RE = re.compile(
    r"publicado\s+com\s+sucesso|publicado\s+con\s+[ée]xito|"
    r"enviado\s+com\s+sucesso|v[ií]deo\s+publicado|published|posted",
    re.I,
)
FAILURE_RE = re.compile(
    r"tente\s+novamente|try\s+again|falhou|failed|erro|error|upload\s+failed",
    re.I,
)
BOUND_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


class KwaiUpError(RuntimeError):
    pass


class HumanVerification(KwaiUpError):
    pass


@dataclass(frozen=True)
class Config:
    mode: str
    serial: str
    media: Path | None
    job_id: str
    expected_sha256: str
    caption: str
    artifacts: Path
    wait: int
    verify_timeout: int

    @classmethod
    def from_env(cls, mode: str) -> "Config":
        media_raw = os.getenv("KWAI_UP_MEDIA", "").strip()
        return cls(
            mode=mode,
            serial=os.getenv("KWAI_UP_ADB_SERIAL", "").strip(),
            media=Path(media_raw).expanduser().resolve() if media_raw else None,
            job_id=os.getenv("KWAI_UP_JOB_ID", "").strip(),
            expected_sha256=os.getenv("KWAI_UP_MEDIA_SHA256", "").strip().lower(),
            caption=os.getenv("KWAI_UP_CAPTION", "").strip(),
            artifacts=Path(os.getenv("KWAI_UP_ARTIFACT_DIR", ".kwai-up/artifacts")).expanduser(),
            wait=max(3, int(os.getenv("KWAI_UP_WAIT", "8") or 8)),
            verify_timeout=max(60, int(os.getenv("KWAI_UP_VERIFY_TIMEOUT", "150") or 150)),
        )


class ADB:
    def __init__(self, serial: str = "") -> None:
        self.serial = serial

    def _base(self) -> list[str]:
        cmd = ["adb"]
        if self.serial:
            cmd += ["-s", self.serial]
        return cmd

    def run(self, *args: str, timeout: int = 45, check: bool = True) -> str:
        p = subprocess.run(
            self._base() + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        if check and p.returncode:
            raise KwaiUpError(f"adb rc={p.returncode}: {' '.join(args)} :: {p.stdout[-800:]}")
        return p.stdout

    def binary(self, *args: str, timeout: int = 45, check: bool = True) -> bytes:
        p = subprocess.run(
            self._base() + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            timeout=timeout,
        )
        if check and p.returncode:
            tail = p.stdout[-800:].decode("utf-8", errors="replace")
            raise KwaiUpError(f"adb rc={p.returncode}: {' '.join(args)} :: {tail}")
        return p.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_token(value: str, fallback: str = "job") -> str:
    token = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip()).strip("._-")
    return (token or fallback)[:48]


def staged_name(job_id: str, sha256: str, suffix: str = ".mp4") -> str:
    suffix = suffix.lower() if re.fullmatch(r"\.[a-zA-Z0-9]{1,8}", suffix or "") else ".mp4"
    return f"kwaiup_{safe_token(job_id)}_{sha256[:12]}{suffix}"


def bounds_tuple(raw: str) -> tuple[int, int, int, int] | None:
    m = BOUND_RE.fullmatch(raw or "")
    if not m:
        return None
    return tuple(map(int, m.groups()))


def center(raw: str) -> tuple[int, int] | None:
    b = bounds_tuple(raw)
    if not b:
        return None
    x1, y1, x2, y2 = b
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def label(node: dict[str, str]) -> str:
    return " ".join(
        str(node.get(k, "")) for k in ("text", "content-desc", "resource-id")
    ).strip()


def text_blob(nodes: Iterable[dict[str, str]]) -> str:
    return "\n".join(label(n) for n in nodes)


def parse_nodes(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    keep = (
        "text", "content-desc", "resource-id", "class", "package",
        "clickable", "enabled", "selected", "checked", "bounds",
    )
    return [
        {k: n.attrib.get(k, "") for k in keep}
        for n in root.iter("node")
    ]


def find_id(nodes: Iterable[dict[str, str]], rid: str, clickable: bool = False) -> dict[str, str] | None:
    for node in nodes:
        if node.get("resource-id") != rid:
            continue
        if clickable and node.get("clickable") != "true":
            continue
        if center(node.get("bounds", "")):
            return node
    return None


def find_text(nodes: Iterable[dict[str, str]], values: Iterable[str], clickable: bool = True) -> dict[str, str] | None:
    wanted = {v.casefold() for v in values}
    for node in nodes:
        if clickable and node.get("clickable") != "true":
            continue
        visible = " ".join((node.get("text", ""), node.get("content-desc", ""))).strip().casefold()
        if visible in wanted and center(node.get("bounds", "")):
            return node
    return None


def profile_grid_changed(before: list[str], after: list[str]) -> bool:
    if not after:
        return False
    if not before:
        return bool(after)
    if after[0] == before[0]:
        return False
    old_front = before[:3]
    return any(value in after[1:4] for value in old_front)


class Publisher:
    def __init__(self, cfg: Config, adb: ADB | None = None) -> None:
        self.cfg = cfg
        self.adb = adb or ADB(cfg.serial)
        self.cfg.artifacts.mkdir(parents=True, exist_ok=True)
        self.ready_file = self.cfg.artifacts / "ready.json"

    def emit(self, state: str, **fields: object) -> None:
        parts = [f"KWAI_UP_STATE={state}"]
        parts += [f"{key.upper()}={value}" for key, value in fields.items()]
        print(" ".join(parts), flush=True)

    def probe(self) -> int:
        state = self.adb.run("get-state", check=False).strip()
        if state != "device":
            self.emit("FAILED_SAFE", reason="adb-device-unavailable", adb_state=state or "empty")
            return 20
        packages = self.adb.run("shell", "pm", "path", PACKAGE, check=False)
        if not packages.strip().startswith("package:"):
            self.emit("FAILED_SAFE", reason="kwai-package-missing")
            return 21
        sdk = self.adb.run("shell", "getprop", "ro.build.version.sdk", check=False).strip()
        model = self.adb.run("shell", "getprop", "ro.product.model", check=False).strip()
        self.emit("PROBE_OK", package=PACKAGE, sdk=sdk or "?", model=safe_token(model, "unknown"))
        return 0

    def current_activity(self) -> str:
        raw = self.adb.run("shell", "dumpsys", "activity", "activities", check=False)
        for pattern in (
            r"mResumedActivity:\s+ActivityRecord\{[^}\n]*?\s([A-Za-z0-9._$-]+/[A-Za-z0-9._$-]+)",
            r"topResumedActivity=ActivityRecord\{[^}\n]*?\s([A-Za-z0-9._$-]+/[A-Za-z0-9._$-]+)",
        ):
            m = re.search(pattern, raw)
            if m:
                return m.group(1)
        return ""

    def dump(self, stage: str, screenshot: bool = True) -> list[dict[str, str]]:
        remote = f"/sdcard/kwaiup-{safe_token(stage)}.xml"
        # Android may transiently terminate uiautomator with exit 137 under
        # memory pressure. Retry only the read-only UI dump, never publication.
        for attempt in range(3):
            try:
                self.adb.run("shell", "uiautomator", "dump", remote)
                break
            except KwaiUpError as exc:
                retryable = "adb rc=137" in str(exc) or "null root node" in str(exc).lower()
                if not retryable or attempt == 2:
                    raise
                time.sleep(3 * (attempt + 1))
        xml = self.adb.binary("exec-out", "cat", remote)
        (self.cfg.artifacts / f"{stage}.xml").write_bytes(xml)
        if screenshot:
            png = self.adb.binary("exec-out", "screencap", "-p", timeout=60)
            (self.cfg.artifacts / f"{stage}.png").write_bytes(png)
        nodes = parse_nodes(xml)
        if HUMAN_RE.search(text_blob(nodes)):
            raise HumanVerification(f"human-verification:{stage}")
        return nodes

    def tap_node(self, node: dict[str, str], pause: float = 2.0) -> None:
        p = center(node.get("bounds", ""))
        if not p:
            raise KwaiUpError("node-without-bounds")
        self.adb.run("shell", "input", "tap", str(p[0]), str(p[1]))
        time.sleep(pause)

    def long_press_node(self, node: dict[str, str]) -> None:
        p = center(node.get("bounds", ""))
        if not p:
            raise KwaiUpError("create-control-without-bounds")
        self.adb.run("shell", "input", "swipe", str(p[0]), str(p[1]), str(p[0]), str(p[1]), "1200")
        time.sleep(2)

    def dismiss_known_overlays(self, nodes: list[dict[str, str]], stage: str) -> list[dict[str, str]]:
        # Close only positively identified promotional overlays, preserving auth.
        ids={(n.get('resource-id') or '') for n in nodes}
        if ('com.kwai.video:id/close_button' in ids and
            'com.kwai.video:id/colored_button_bg' in ids and
            'com.kwai.video.basis:id/view_content' in ids):
            close=next(n for n in nodes if n.get('resource-id')=='com.kwai.video:id/close_button')
            self.tap_node(close,1)
            time.sleep(1)
            return self.dump(stage+'-promo-dismissed')
        texts=[(n.get('text') or '').casefold() for n in nodes]
        if any('recomendação de amigos' in t or 'recomendacao de amigos' in t or
               'friend recommendations' in t for t in texts):
            self.adb.run('shell','input','keyevent','4',check=False)
            time.sleep(1)
            return self.dump(stage+'-recommendation-dismissed')
        if any('ande para ganhar kwai golds' in t for t in texts):
            self.adb.run('shell','input','keyevent','4',check=False)
            time.sleep(1)
            return self.dump(stage+'-golds-dismissed')
        for rid in (NOTIFICATION_CLOSE_ID, CREATOR_GUIDE_CLOSE_ID):
            node = find_id(nodes, rid)
            if node:
                self.tap_node(node, 1)
                return self.dump(stage + "-clean")
        return nodes

    def launcher_component(self) -> str:
        raw = self.adb.run(
            "shell", "cmd", "package", "resolve-activity", "--brief",
            "-c", "android.intent.category.LAUNCHER", PACKAGE,
            check=False,
        )
        m = re.search(r"(com\.kwai\.video/[A-Za-z0-9_.$]+)", raw)
        return m.group(1) if m else f"{PACKAGE}/com.yxcorp.gifshow.tiny.TinyLaunchActivity"

    def cold_start(self, stage: str = "00-home", force_stop: bool = True) -> list[dict[str, str]]:
        # -S force-stops the app and must NEVER be used after publish was clicked.
        if force_stop:
            self.adb.run("shell", "am", "start", "-S", "--activity-clear-task", "-n", self.launcher_component(), timeout=60)
        else:
            self.adb.run("shell", "am", "start", "--activity-clear-top", "-n", "com.kwai.video/com.yxcorp.gifshow.homepage.HomeActivity", timeout=60)
        time.sleep(self.cfg.wait)
        deadline = time.time() + max(self.cfg.wait * 3, 45)
        last: list[dict[str, str]] = []
        while time.time() < deadline:
            last = self.dismiss_known_overlays(self.dump(stage), stage)
            if find_id(last, RECORD_ID) or find_id(last, FAKE_ADD_ID) or (not force_stop and self.profile_tab(last)):
                return last
            time.sleep(3)
        raise KwaiUpError("kwai-home-create-control-timeout")

    def query_media(self) -> str:
        return self.adb.run(
            "shell", "content", "query", "--uri", MEDIA_URI,
            "--projection", "_id:_display_name:_data:duration:width:height",
        )

    @staticmethod
    def media_rows(raw: str) -> list[str]:
        return [line.strip() for line in raw.splitlines() if line.strip().startswith("Row:")]

    def clean_own_staging(self) -> None:
        self.adb.run("shell", "mkdir", "-p", REMOTE_DIR)
        listing = self.adb.run("shell", "ls", "-1", REMOTE_DIR, check=False)
        for name in listing.splitlines():
            name = name.strip()
            if not name.startswith("kwaiup_"):
                continue
            path = f"{REMOTE_DIR}/{name}"
            self.adb.run("shell", "rm", "-f", path, check=False)
            self.adb.run(
                "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                "-d", f"file://{path}", check=False,
            )
        time.sleep(2)

    def validate_input(self) -> tuple[Path, str, str]:
        if not self.cfg.media or not self.cfg.media.is_file():
            raise KwaiUpError("KWAI_UP_MEDIA-missing")
        if not self.cfg.job_id:
            raise KwaiUpError("KWAI_UP_JOB_ID-missing")
        actual = sha256_file(self.cfg.media)
        if self.cfg.expected_sha256 and self.cfg.expected_sha256 != actual:
            raise KwaiUpError("media-sha256-mismatch")
        name = staged_name(self.cfg.job_id, actual, self.cfg.media.suffix or ".mp4")
        return self.cfg.media, actual, name

    def stage_media(self) -> tuple[str, str]:
        source, sha, name = self.validate_input()
        self.clean_own_staging()
        remote = f"{REMOTE_DIR}/{name}"
        # Mandatory pre-gallery transfer: retry and verify remote SHA256 before UI selection.
        transferred = False
        for transfer_attempt in range(1, 4):
            try:
                self.adb.run("push", str(source), remote, timeout=240)
                remote_hash_output = self.adb.run("shell", "sha256sum", remote, timeout=45, check=False)
                if remote_hash_output.split() and remote_hash_output.split()[0].lower() == sha.lower():
                    transferred = True
                    break
            except (KwaiUpError, OSError, subprocess.TimeoutExpired):
                pass  # pre-publication transfer only; retry is safe
            if transfer_attempt < 3:
                time.sleep(3)
        if not transferred:
            raise KwaiUpError("staged-media-transfer-sha256-not-verified")
        self.adb.run(
            "shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
            "-d", f"file://{remote}",
        )
        # Indexation is asynchronous: wait for the exact staged name before opening gallery.
        raw = ''
        for scan_attempt in range(1, 9):
            raw = self.query_media()
            current = self.media_rows(raw)
            exact = [row for row in current if f"_display_name={name}" in row]
            if len(exact) == 1:
                break
            if len(exact) > 1:
                raise KwaiUpError("staged-media-index-duplicate")
            self.adb.run("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{remote}", check=False)
            time.sleep(3)
        else:
            raise KwaiUpError("staged-media-index-timeout")
        (self.cfg.artifacts / "mediastore.txt").write_text(raw, encoding="utf-8")
        rows = self.media_rows(raw)
        matching = [row for row in rows if f"_display_name={name}" in row or name in row]
        if len(matching) != 1:
            raise KwaiUpError(f"staged-media-not-unique:matching={len(matching)}")
        # The proven publisher ran on a dedicated Android surface and selected one visible video.
        # Preserve that invariant for the publishing executor. The authentication phone is separate.
        videos = [row for row in rows if "_display_name=" in row]
        # Identity comes from the unique staged filename and SHA-256, not video duration.
        # Gallery selection still requires one unambiguous clickable preview.
        if not any(f'_display_name={name}' in row for row in videos):
            raise KwaiUpError('staged-media-not-in-mediastore')
        media_id = re.search(r'(?:^|[ ,])_id=(\d+)(?:[ ,]|$)', matching[0])
        if not media_id:
            raise KwaiUpError('staged-media-id-not-found')
        self._staged_media_id = int(media_id.group(1))
        return sha, name

    def profile_tab(self, nodes: list[dict[str, str]]) -> dict[str, str] | None:
        # Current Kwai home uses a reusable bottom-tab text view. Its exact
        # 'Perfil' label identifies our own profile rather than feed authors.
        current = [
            node for node in nodes
            if node.get("resource-id") == "com.kwai.video.basis:id/consume_tab_text"
            and (node.get("text") or "").strip().casefold() in {"perfil", "profile"}
            and center(node.get("bounds", ""))
        ]
        if len(current) == 1:
            return current[0]
        for rid in PROFILE_TAB_IDS:
            found = find_id(nodes, rid)
            if found:
                return found
        return None

    def profile_fingerprints(self, stage: str, cold: bool) -> list[str]:
        if Image is None:
            raise KwaiUpError("Pillow-required-for-profile-verification")
        nodes = self.cold_start(stage + "-home") if cold else self.dump(stage + "-home")
        tab = self.profile_tab(nodes)
        if not tab:
            raise KwaiUpError("profile-tab-missing")
        self.tap_node(tab)
        deadline = time.time() + 60
        attempts = 0
        while time.time() < deadline:
            attempts += 1
            nodes = self.dismiss_known_overlays(self.dump(stage + "-profile"), stage + "-profile")
            root_ok = find_id(nodes, PROFILE_ROOT_ID) is not None or PROFILE_ROOT_ID in text_blob(nodes)
            thumbs = [n for n in nodes if n.get("resource-id") == PROFILE_THUMB_ID and bounds_tuple(n.get("bounds", ""))]
            if thumbs:
                thumbs.sort(key=lambda n: bounds_tuple(n.get("bounds", "")) or (9999, 9999, 9999, 9999))
                png_path = self.cfg.artifacts / f"{stage}-profile.png"
                if not png_path.exists():
                    time.sleep(1)
                    continue
                img = Image.open(png_path).convert("RGB")
                hashes: list[str] = []
                for node in thumbs[:3]:
                    b = bounds_tuple(node.get("bounds", ""))
                    if not b:
                        continue
                    crop = img.crop(b)
                    hashes.append(hashlib.sha256(crop.tobytes()).hexdigest())
                return hashes
            if attempts % 2 == 0 and not thumbs:
                # Some feed tabs accept the tap without opening the profile.
                # Retry only read-only profile navigation, not upload or commit.
                next_tab = self.profile_tab(nodes)
                if next_tab:
                    self.tap_node(next_tab, 1)
            time.sleep(2)
        raise KwaiUpError("profile-thumbnails-timeout")

    def navigate_to_final(self) -> tuple[list[dict[str, str]], bool]:
        # Exact MediaStore URI is the only safe selector when other gallery
        # videos exist. URI is derived from the uniquely staged, SHA-verified file.
        media_id = getattr(self, "_staged_media_id", None)
        if not isinstance(media_id, int) or media_id <= 0:
            raise KwaiUpError("exact-staged-media-id-required")
        uri = f"content://media/external/video/media/{media_id}"
        result = self.adb.run(
            "shell", "am", "start", "-a", "android.intent.action.SEND",
            "-t", "video/mp4", "--eu", "android.intent.extra.STREAM", uri,
            "-f", "0x1", "-p", "com.kwai.video", timeout=40,
        )
        if "Error" in result or "Exception" in result:
            raise KwaiUpError("exact-media-share-intent-failed")
        # Media handoff is asynchronous on MEmu: never mistake an editor still
        # opening for failure, and never repeat the SEND intent blindly.
        editor_ready = False
        for _ in range(15):
            time.sleep(2)
            activity = self.current_activity()
            if "com.kwai.video/" in activity and "EditorActivity" in activity:
                editor_ready = True
                break
        if not editor_ready:
            raise KwaiUpError("exact-media-editor-not-open-after-30s")
        self.emit("MEDIA_SELECTED_EXACT", media_id=media_id)
        editor = self.dismiss_known_overlays(self.dump("13-editor"), "13-editor")
        next_button = find_id(editor, NEXT_ID)
        if not next_button:
            raise KwaiUpError("editor-next-missing")
        self.tap_node(next_button, self.cfg.wait)

        # Next may first display the media processing overlay. Wait for the
        # verified final share controls; do not click Next or Publish again.
        final = []
        activity = ""
        post = None
        field = None
        deadline = time.time() + 150
        while time.time() < deadline:
            final = self.dismiss_known_overlays(self.dump("14-final"), "14-final")
            activity = self.current_activity()
            post = find_id(final, FINAL_POST_ID)
            field = find_id(final, EDITOR_ID) or next((n for n in final if n.get("resource-id") == EDITOR_ID), None)
            if post and field and activity.startswith("com.kwai.video/") and any(a in activity for a in ("ShareActivity", "HomeActivity")):
                break
            if any("carregando" in (n.get("text", "").casefold()) for n in final):
                time.sleep(3)
                continue
            time.sleep(3)
        if not post or not field or not activity.startswith("com.kwai.video/") or not any(a in activity for a in ("ShareActivity", "HomeActivity")):
            raise KwaiUpError(f"final-screen-mismatch:{activity or 'unknown'}")
        privacy = find_id(final, PRIVACY_ID) or next((n for n in final if n.get("resource-id") == PRIVACY_ID), None)
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        normalized_privacy = "".join(c for c in unicodedata.normalize("NFKD",privacy_text) if not unicodedata.combining(c))
        public_ok = normalized_privacy in {"publico","public"}
        return final, public_ok

    def fill_caption(self, nodes: list[dict[str, str]]) -> None:
        if not self.cfg.caption:
            return
        field = find_id(nodes, EDITOR_ID) or next((n for n in nodes if n.get("resource-id") == EDITOR_ID), None)
        if not field:
            raise KwaiUpError("caption-field-missing")
        if os.getenv("KWAI_UP_CAPTION_INPUT_METHOD", "").strip().lower() == "adbkeyboard":
            current_ime = self.adb.run(
                "shell", "settings", "get", "secure", "default_input_method"
            ).strip()
            if current_ime != "com.android.adbkeyboard/.AdbIME":
                raise KwaiUpError("adbkeyboard-not-selected")
            self.tap_node(field, 1)
            self.adb.run("shell", "am", "broadcast", "-a", "ADB_CLEAR_TEXT")
            encoded = base64.b64encode(self.cfg.caption[:150].encode("utf-8")).decode("ascii")
            self.adb.run(
                "shell", "am", "broadcast", "-a", "ADB_INPUT_B64",
                "--es", "msg", encoded,
            )
            time.sleep(1)
        else:
            bridge = os.getenv("KWAI_UP_UIAUTOMATOR_JAR", "").strip()
            if bridge:
                # Use the Android UIAutomator setText API for complete UTF-8 input.
                # The legacy shell input method silently drops punctuation/spaces.
                local_jar = Path(bridge)
                if not local_jar.is_file():
                    raise KwaiUpError("caption-uiautomator-jar-missing")
                remote_jar = "/data/local/tmp/anthares-kwai-ui-driver.jar"
                self.adb.run("push", str(local_jar), remote_jar, timeout=45)
                encoded = base64.b64encode(self.cfg.caption[:150].encode("utf-8")).decode("ascii")
                raw = self.adb.run(
                    "shell", "uiautomator", "runtest", remote_jar,
                    "-c", "us.anthares.tools.KwaiUiDriver#testAction",
                    "-e", "action", "setFirstEditText",
                    "-e", "value_base64", encoded,
                    timeout=90, check=False,
                )
                if "ANTHARES_UI_OK action=setFirstEditText" not in raw or "OK (1 test)" not in raw:
                    raise KwaiUpError("caption-uiautomator-set-text-failed")
            else:
                self.tap_node(field, 1)
                self.adb.run("shell", "input", "keyevent", "KEYCODE_MOVE_END", check=False)
                # Legacy physical Android mode; retained for other verified devices.
                for index, token in enumerate(self.cfg.caption[:120].split()):
                    if index:
                        self.adb.run("shell", "input", "keyevent", "KEYCODE_SPACE")
                    self.adb.run("shell", "input", "text", token, timeout=20)
                    time.sleep(0.25)
        self.adb.run("shell", "input", "keyevent", "KEYCODE_BACK", check=False)
        time.sleep(1)

    def prepare(self) -> int:
        if self.probe() != 0:
            return 20
        sha, name = self.stage_media()
        before = self.profile_fingerprints("20-before", cold=True)
        final, public_ok = self.navigate_to_final()
        self.fill_caption(final)
        final = self.dump("21-ready")
        post = find_id(final, FINAL_POST_ID)
        if not post:
            raise KwaiUpError("publish-control-not-ready")
        if not public_ok:
            raise KwaiUpError("privacy-not-confirmed-public")
        proof = {
            "version": 1,
            "job_id": self.cfg.job_id,
            "media_sha256": sha,
            "staged_name": name,
            "caption": self.cfg.caption,
            "profile_before": before,
            "created_at": int(time.time()),
        }
        self.ready_file.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
        self.emit("READY_TO_PUBLISH", job=self.cfg.job_id, media=name, sha256=sha[:16])
        return 0

    def load_ready(self) -> dict[str, object]:
        if not self.ready_file.is_file():
            raise KwaiUpError("missing-ready-proof")
        proof = json.loads(self.ready_file.read_text(encoding="utf-8"))
        if proof.get("job_id") != self.cfg.job_id:
            raise KwaiUpError("ready-job-mismatch")
        if proof.get("caption") != self.cfg.caption:
            raise KwaiUpError("ready-caption-mismatch")
        # Read-only verification of an already attempted publication may run
        # hours later. Expiry still applies to prepare/commit to prevent stale posts.
        if self.cfg.mode != "verify" and int(time.time()) - int(proof.get("created_at", 0)) > 1200:
            raise KwaiUpError("ready-proof-expired")
        if self.cfg.media:
            sha = sha256_file(self.cfg.media)
            if proof.get("media_sha256") != sha:
                raise KwaiUpError("ready-media-mismatch")
        return proof

    def verify_after_post(self, before: list[str]) -> tuple[bool, str]:
        deadline = time.time() + self.cfg.verify_timeout
        structural_since: float | None = None
        saw_structural = False
        saw_text = False
        next_profile = 0.0
        last_error = ""
        attempt = 0
        while time.time() < deadline:
            attempt += 1
            activity = self.current_activity()
            try:
                nodes = self.dismiss_known_overlays(self.dump(f"30-after-{attempt}"), f"30-after-{attempt}")
                blob = text_blob(nodes)
            except HumanVerification:
                raise
            except Exception as exc:
                last_error = str(exc)
                time.sleep(3)
                continue
            if FAILURE_RE.search(blob):
                return False, "visible-post-error"
            saw_text = saw_text or bool(SUCCESS_RE.search(blob))
            structural_now = bool(activity) and PACKAGE in activity and "ShareActivity" not in activity
            if structural_now and not saw_structural:
                structural_since = time.time()
            saw_structural = saw_structural or structural_now
            if saw_text and saw_structural:
                return True, "textual-and-structural"
            if (
                saw_structural
                and structural_since is not None
                and time.time() - structural_since >= 10
                and time.time() >= next_profile
            ):
                try:
                    after = self.profile_fingerprints(f"31-profile-{attempt}", cold=False)
                    if profile_grid_changed(before, after):
                        return True, "structural-and-profile-grid"
                    last_error = f"profile-unchanged:{len(before)}:{len(after)}"
                except Exception as exc:
                    last_error = str(exc)
                next_profile = time.time() + 15
            time.sleep(4)
        return False, f"verification-timeout:{last_error or 'no-secondary-proof'}"

    def commit(self) -> int:
        proof = self.load_ready()
        nodes = self.dump("25-precommit")
        activity = self.current_activity()
        post = find_id(nodes, FINAL_POST_ID)
        field = find_id(nodes, EDITOR_ID)
        privacy = find_id(nodes, PRIVACY_ID)
        if not post or not field or not privacy or not activity.startswith("com.kwai.video/") or not any(a in activity for a in ("ShareActivity", "HomeActivity")):
            raise KwaiUpError("publish-boundary-lost")
        self.emit("PUBLISH_REQUESTED", job=self.cfg.job_id)
        self.tap_node(post, 1)
        ok, evidence = self.verify_after_post(list(proof.get("profile_before", [])))
        if ok:
            self.emit("VERIFIED", evidence=evidence, job=self.cfg.job_id)
            self.ready_file.unlink(missing_ok=True)
            return 0
        self.emit("UNCERTAIN", reason=evidence, job=self.cfg.job_id)
        return 90

    def verify(self) -> int:
        proof = self.load_ready()
        ok, evidence = self.verify_after_post(list(proof.get("profile_before", [])))
        if ok:
            self.emit("VERIFIED", evidence=evidence, job=self.cfg.job_id)
            self.ready_file.unlink(missing_ok=True)
            return 0
        self.emit("UNCERTAIN", reason=evidence, job=self.cfg.job_id)
        return 90


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "probe").strip().lower()
    if mode not in {"probe", "prepare", "commit", "verify"}:
        print("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-mode", flush=True)
        return 64
    cfg = Config.from_env(mode)
    pub = Publisher(cfg)
    try:
        if mode == "probe":
            return pub.probe()
        if mode == "prepare":
            return pub.prepare()
        if mode == "commit":
            return pub.commit()
        return pub.verify()
    except HumanVerification as exc:
        pub.emit("FAILED_SAFE", reason="human-verification", detail=safe_token(str(exc)))
        return 91
    except KwaiUpError as exc:
        pub.emit("FAILED_SAFE", reason=safe_token(str(exc), "kwai-up-error"))
        return 70
    except Exception as exc:
        pub.emit("FAILED_SAFE", reason="unexpected", detail=safe_token(type(exc).__name__))
        return 79


if __name__ == "__main__":
    raise SystemExit(main())
