#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
import time

import kwai_up_physical_safe as ps

ku = ps.ku


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
        f"(cat {remote_dir}/create.bin; sleep 0.45; "
        f"cat {remote_dir}/down.bin; sleep {hold:.2f}; "
        f"cat {remote_dir}/up.bin; sleep 0.45; "
        f"cat {remote_dir}/destroy.bin) > /dev/uhid\n",
        encoding="utf-8",
        newline="\n",
    )
    self.adb.run("push", str(run_local), f"{remote_dir}/run.sh")
    out = self.adb.run("shell", "sh", f"{remote_dir}/run.sh", timeout=15, check=False)
    low = out.lower()
    if "permission denied" in low or "not permitted" in low:
        raise ku.KwaiUpError("uhid-touch-denied")
    time.sleep(0.15)


ps.PhysicalSafePublisher._uhid_available = _uhid_available
ps.PhysicalSafePublisher._uhid_touch = _uhid_touch

if __name__ == "__main__":
    raise SystemExit(ps.main())
