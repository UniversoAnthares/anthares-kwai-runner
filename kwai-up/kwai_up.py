#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
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
        self.adb.run("shell", "uiautomator", "dump", remote)
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

    def cold_start(self, stage: str = "00-home") -> list[dict[str, str]]:
        self.adb.run("shell", "am", "start", "-S", "--activity-clear-task", "-n", self.launcher_component(), timeout=60)
        time.sleep(self.cfg.wait)
        deadline = time.time() + max(self.cfg.wait * 3, 45)
        last: list[dict[str, str]] = []
        while time.time() < deadline:
            last = self.dismiss_known_overlays(self.dump(stage), stage)
            if find_id(last, RECORD_ID) or find_id(last, FAKE_ADD_ID):
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
            raise KwaiUpError(f"staged-media-not-unique:matching={len(matching)}")
        # The proven publisher ran on a dedicated Android surface and selected one visible video.
        # Preserve that invariant for the publishing executor. The authentication phone is separate.
        videos = [row for row in rows if "_display_name=" in row]
        if len(videos) != 1:
            raise KwaiUpError(f"publisher-mediastore-not-dedicated:videos={len(videos)}")
        return sha, name

    def profile_tab(self, nodes: list[dict[str, str]]) -> dict[str, str] | None:
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
        deadline = time.time() + 35
        while time.time() < deadline:
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
            if root_ok:
                time.sleep(2)
            else:
                time.sleep(2)
        raise KwaiUpError("profile-thumbnails-timeout")

    def navigate_to_final(self) -> tuple[list[dict[str, str]], bool]:
        home = self.cold_start("10-home")
        create = find_id(home, RECORD_ID) or find_id(home, FAKE_ADD_ID)
        if not create:
            raise KwaiUpError("create-control-missing")
        self.long_press_node(create)
        time.sleep(max(2, self.cfg.wait - 2))

        album = self.dismiss_known_overlays(self.dump("11-album"), "11-album")
        videos_tab = find_text(album, ("Vídeos", "Videos"))
        if videos_tab:
            self.tap_node(videos_tab)
            time.sleep(3)

        videos = self.dismiss_known_overlays(self.dump("12-videos"), "12-videos")
        previews = [
            n for n in videos
            if n.get("resource-id") == PREVIEW_CONTAINER_ID
            and n.get("clickable") == "true"
            and center(n.get("bounds", ""))
        ]
        if len(previews) != 1:
            raise KwaiUpError(f"safe-video-selection-refused:visible={len(previews)}")
        self.tap_node(previews[0], self.cfg.wait)

        editor = self.dismiss_known_overlays(self.dump("13-editor"), "13-editor")
        next_button = find_id(editor, NEXT_ID)
        if not next_button:
            raise KwaiUpError("editor-next-missing")
        self.tap_node(next_button, self.cfg.wait)

        final = self.dismiss_known_overlays(self.dump("14-final"), "14-final")
        activity = self.current_activity()
        post = find_id(final, FINAL_POST_ID)
        field = find_id(final, EDITOR_ID) or next((n for n in final if n.get("resource-id") == EDITOR_ID), None)
        if "ShareActivity" not in activity or not post or not field:
            raise KwaiUpError(f"final-screen-mismatch:{activity or 'unknown'}")
        privacy = find_id(final, PRIVACY_ID) or next((n for n in final if n.get("resource-id") == PRIVACY_ID), None)
        privacy_text = (privacy or {}).get("text", "").strip().casefold()
        public_ok = privacy_text in {"público", "publico", "public"}
        return final, public_ok

    def fill_caption(self, nodes: list[dict[str, str]]) -> None:
        if not self.cfg.caption:
            return
        field = find_id(nodes, EDITOR_ID) or next((n for n in nodes if n.get("resource-id") == EDITOR_ID), None)
        if not field:
            raise KwaiUpError("caption-field-missing")
        self.tap_node(field, 1)
        self.adb.run("shell", "input", "keyevent", "KEYCODE_MOVE_END", check=False)
        safe = self.cfg.caption[:150].replace("%", "%25").replace(" ", "%s")
        for old, new in (("&", r"\&"), ("(", r"\("), (")", r"\)"), (";", r"\;")):
            safe = safe.replace(old, new)
        self.adb.run("shell", "input", "text", safe)
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
        if int(time.time()) - int(proof.get("created_at", 0)) > 1200:
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
        if "ShareActivity" not in activity or not post:
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
