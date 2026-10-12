#!/usr/bin/env python3
from pathlib import Path
import runpy

p = Path(__file__).with_name('kwai_up_physical.py')
s = p.read_text(encoding='utf-8')

old = '''FINAL_POST_ID = f"{BASIS}/post"
EDITOR_ID = f"{BASIS}/editor"
'''
new = '''FINAL_POST_ID = f"{BASIS}/post"
FINAL_POST_IDS = (FINAL_POST_ID, f"{BASIS}/right_btn")
EDITOR_ID = f"{BASIS}/editor"
'''
if old not in s:
    raise SystemExit('POST_IDS_CONSTANT_TARGET_NOT_FOUND')
s = s.replace(old, new, 1)

marker = '''class PhysicalPublisher(safe.SafePublisher):
'''
helper = '''def find_final_post(nodes: Iterable[dict[str, str]]) -> dict[str, str] | None:
    for rid in FINAL_POST_IDS:
        node = ku.find_id(nodes, rid)
        if node:
            return node
    return None


class PhysicalPublisher(safe.SafePublisher):
'''
if marker not in s:
    raise SystemExit('POST_HELPER_MARKER_NOT_FOUND')
s = s.replace(marker, helper, 1)

s = s.replace('post = ku.find_id(final, FINAL_POST_ID)', 'post = find_final_post(final)')
s = s.replace('post = ku.find_id(nodes, FINAL_POST_ID)', 'post = find_final_post(nodes)')

old_focus = '''        with HIDKeyboard(self.adb, 314) as keyboard:
            self.focus_target(keyboard, FINAL_POST_ID, "26-post-focus", max_steps=35)
            # Irreversible boundary starts only after exact resource-id focus is proven.
            self.emit("PUBLISH_REQUESTED", job=self.cfg.job_id, transport="hid-uhid")
            keyboard.enter()
'''
new_focus = '''        post_rid = post.get("resource-id", "")
        if post_rid not in FINAL_POST_IDS:
            raise ku.KwaiUpError("publish-control-id-untrusted")
        with HIDKeyboard(self.adb, 314) as keyboard:
            self.focus_target(keyboard, post_rid, "26-post-focus", max_steps=35)
            # Irreversible boundary starts only after exact resource-id focus is proven.
            self.emit("PUBLISH_REQUESTED", job=self.cfg.job_id, transport="hid-uhid", control=post_rid.split('/')[-1])
            keyboard.enter()
'''
if old_focus not in s:
    raise SystemExit('POST_FOCUS_TARGET_NOT_FOUND')
s = s.replace(old_focus, new_focus, 1)

p.write_text(s, encoding='utf-8', newline='\n')
print('KWAI_UP_POST_VARIANTS_PATCH=APPLIED')

# The same physical run must also dismiss Kwai Lite's transient downloaded-video
# guide before identity checks. Apply that patch after this file's edits.
runpy.run_path(str(Path(__file__).with_name('patch_physical_overlays.py')), run_name='__main__')
