#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).with_name('kwai_up_physical.py')
s = p.read_text(encoding='utf-8')
old = '''    def navigate_to_final(self, remote: str) -> tuple[list[dict[str, str]], bool]:
        self.open_album(remote)
        with HIDKeyboard(self.adb, 312) as keyboard:
            self.focus_target_hint(keyboard, PREVIEW_ID, "12-first-video", hint_steps=7, fallback_steps=40)
            keyboard.enter()
'''
new = '''    def navigate_to_final(self, remote: str) -> tuple[list[dict[str, str]], bool]:
        album = self.open_album(remote)

        # Resolve the exact staged media fail-closed. The deep link scrolls near the
        # requested path but does not guarantee that it is the first visible cell.
        media_file = pathlib.PurePosixPath(remote).name
        media_dump = (self.cfg.artifacts / "mediastore.txt").read_text(encoding="utf-8", errors="replace")
        media_rows = [line for line in media_dump.splitlines() if media_file in line]
        if len(media_rows) != 1:
            raise ku.KwaiUpError(f"target-media-row-ambiguous:{len(media_rows)}")
        duration_match = re.search(r"(?:^|,\\s*)duration=(\\d+)", media_rows[0])
        if not duration_match:
            raise ku.KwaiUpError("target-media-duration-missing")
        duration_seconds = max(0, int(round(int(duration_match.group(1)) / 1000.0)))
        duration_label = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"

        previews = [
            n for n in album
            if n.get("resource-id") == PREVIEW_ID
            and n.get("clickable") == "true"
            and ku.bounds_tuple(n.get("bounds", ""))
        ]
        duration_nodes = [
            n for n in album
            if n.get("resource-id") == f"{BASIS}/media_duration"
            and n.get("text", "").strip() == duration_label
            and ku.bounds_tuple(n.get("bounds", ""))
        ]
        target_bounds: list[str] = []
        for duration_node in duration_nodes:
            point = ku.center(duration_node.get("bounds", ""))
            if not point:
                continue
            x, y = point
            for preview in previews:
                bounds = ku.bounds_tuple(preview.get("bounds", ""))
                if not bounds:
                    continue
                x1, y1, x2, y2 = bounds
                if x1 <= x <= x2 and y1 <= y <= y2:
                    target_bounds.append(preview.get("bounds", ""))
        unique_bounds = sorted(set(target_bounds))
        if len(unique_bounds) != 1:
            raise ku.KwaiUpError(
                f"target-preview-ambiguous:duration={duration_label}:matches={len(unique_bounds)}"
            )
        exact_bounds = unique_bounds[0]
        self.emit("TARGET_MEDIA_RESOLVED", duration=duration_label, bounds=exact_bounds)

        with HIDKeyboard(self.adb, 312) as keyboard:
            found = False
            for step in range(0, 51):
                nodes = self.dump(f"12-target-video-{step}", screenshot=False)
                if any(
                    n.get("resource-id") == PREVIEW_ID
                    and n.get("focused") == "true"
                    and n.get("focusable") == "true"
                    and n.get("bounds") == exact_bounds
                    for n in nodes
                ):
                    found = True
                    break
                keyboard.tab()
            if not found:
                raise ku.KwaiUpError("target-preview-exact-focus-timeout")
            keyboard.enter()
'''
if old not in s:
    raise SystemExit('PATCH_TARGET_NOT_FOUND')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8', newline='\n')
print('KWAI_UP_EXACT_MEDIA_PATCH=APPLIED')
