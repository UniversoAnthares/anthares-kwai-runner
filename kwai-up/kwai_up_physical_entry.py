#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
import time

import kwai_up_physical_safe as ps

ku = ps.ku


def _visible_bounds(node: dict[str, str]):
    bounds = ku.bounds_tuple(node.get("bounds", ""))
    if not bounds:
        return None
    x1, y1, x2, y2 = bounds
    if x2 <= x1 or y2 <= y1:
        return None
    return bounds


def _visible_center(raw: str):
    bounds = ku.bounds_tuple(raw)
    if not bounds:
        return None
    x1, y1, x2, y2 = bounds
    if x2 <= x1 or y2 <= y1:
        return None
    return ((x1 + x2) // 2, (y1 + y2) // 2)


ku.center = _visible_center


def _uhid_available(self) -> bool:
    raw = self.adb.run("shell", "ls", "-l", "/dev/uhid", check=False)
    return "/dev/uhid" in raw and "No such file" not in raw


def _uhid_touch(self, x: int, y: int, hold: float = 0.10) -> None:
    if not _uhid_available(self):
        raise ku.KwaiUpError("uhid-unavailable")
    width, height = self._display_size()
    local = self.cfg.artifacts / "uhid"
    local.mkdir(parents=True, exist_ok=True)
    files = {
        "create.bin": ps._create_event(),
        "down.bin": ps._input_event(True, x, y, width, height),
        "up.bin": ps._input_event(False, x, y, width, height),
        "destroy.bin": ps.struct.pack("<I", 1),
    }
    remote_dir = "/data/local/tmp/kwaiup-uhid"
    self.adb.run("shell", "mkdir", "-p", remote_dir)
    for name, data in files.items():
        path = local / name
        path.write_bytes(data)
        self.adb.run("push", str(path), f"{remote_dir}/{name}")
    hold = max(0.05, min(2.0, hold))
    run_local = local / "run.sh"
    run_local.write_text(
        "#!/system/bin/sh\n"
        f"(cat {remote_dir}/create.bin; sleep 0.90; "
        f"cat {remote_dir}/down.bin; sleep {hold:.2f}; "
        f"cat {remote_dir}/up.bin; sleep 0.90; "
        f"cat {remote_dir}/destroy.bin) > /dev/uhid\n",
        encoding="utf-8",
        newline="\n",
    )
    self.adb.run("push", str(run_local), f"{remote_dir}/run.sh")
    out = self.adb.run("shell", "sh", f"{remote_dir}/run.sh", timeout=15, check=False)
    low = out.lower()
    if "permission denied" in low or "not permitted" in low:
        raise ku.KwaiUpError("uhid-touch-denied")
    time.sleep(0.25)


def _navigate_to_final(self):
    remote = getattr(self, "_staged_remote", "")
    if not remote:
        raise ku.KwaiUpError("staged-media-path-missing")

    self.adb.run("shell", "am", "force-stop", ps.PACKAGE, check=False)
    self.adb.run(
        "shell", "am", "start", "-W", "-a", "android.intent.action.VIEW",
        "-d", "kwai://album", "-p", ps.PACKAGE,
        "--es", "album_scroll_to_path", remote,
        "--ez", "album_select_as_result", "true",
        "--ei", "album_target_select_index", "0",
        timeout=60,
    )
    time.sleep(max(3, self.cfg.wait // 2))
    album = self.dismiss_known_overlays(self.dump("11-physical-album"), "11-physical-album")
    previews = []
    for node in album:
        if node.get("resource-id") != ku.PREVIEW_CONTAINER_ID or node.get("clickable") != "true":
            continue
        bounds = _visible_bounds(node)
        if bounds:
            previews.append((bounds, node))
    previews.sort(key=lambda item: (item[0][1], item[0][0], item[0][3], item[0][2]))
    if not previews:
        raise ku.KwaiUpError("physical-target-preview-missing")
    bounds, _ = previews[0]
    x = (bounds[0] + bounds[2]) // 2
    y = (bounds[1] + bounds[3]) // 2
    self.emit("PHYSICAL_TARGET", bounds="-".join(map(str, bounds)), x=x, y=y)
    self._uhid_touch(x, y)
    time.sleep(max(3, self.cfg.wait // 2))

    editor = self.dismiss_known_overlays(self.dump("13-physical-editor"), "13-physical-editor")
    activity = self.current_activity()
    if "EditorActivity" not in activity:
        raise ku.KwaiUpError(f"physical-editor-activity-mismatch:{activity or 'unknown'}")
    next_button = ku.find_id(editor, ku.NEXT_ID)
    if not next_button:
        raise ku.KwaiUpError("editor-next-missing")
    next_bounds = _visible_bounds(next_button)
    if not next_bounds:
        raise ku.KwaiUpError("editor-next-not-visible")
    nx = (next_bounds[0] + next_bounds[2]) // 2
    ny = (next_bounds[1] + next_bounds[3]) // 2
    self.emit("PHYSICAL_NEXT", x=nx, y=ny)
    self._uhid_touch(nx, ny)
    time.sleep(max(3, self.cfg.wait // 2))

    final = self.dismiss_known_overlays(self.dump("14-physical-final"), "14-physical-final")
    activity = self.current_activity()
    post = ku.find_id(final, ku.FINAL_POST_ID)
    field = ku.find_id(final, ku.EDITOR_ID) or next(
        (n for n in final if n.get("resource-id") == ku.EDITOR_ID), None
    )
    if "ShareActivity" not in activity or not post or not field:
        raise ku.KwaiUpError(f"final-screen-mismatch:{activity or 'unknown'}")
    privacy = ku.find_id(final, ku.PRIVACY_ID) or next(
        (n for n in final if n.get("resource-id") == ku.PRIVACY_ID), None
    )
    privacy_text = (privacy or {}).get("text", "").strip().casefold()
    public_ok = privacy_text in {"público", "publico", "public", "pÇ§blico"}
    return final, public_ok


ps.PhysicalSafePublisher._uhid_available = _uhid_available
ps.PhysicalSafePublisher._uhid_touch = _uhid_touch
ps.PhysicalSafePublisher.navigate_to_final = _navigate_to_final

if __name__ == "__main__":
    raise SystemExit(ps.main())
