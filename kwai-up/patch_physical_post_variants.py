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


def trusted_focused_final_post(nodes: Iterable[dict[str, str]]) -> dict[str, str] | None:
    # The physical Kwai Lite UI morphs after HID TAB navigation: precommit can
    # expose right_btn="Publicar", while the keyboard focus graph then exposes
    # the historical basis:id/post ViewGroup. Accept either only after the
    # exact native control itself is proven focused, enabled and clickable.
    post = ku.find_id(nodes, FINAL_POST_ID)
    if post and all(post.get(k) == "true" for k in ("focused", "focusable", "clickable", "enabled")):
        return post
    right = ku.find_id(nodes, f"{BASIS}/right_btn")
    if right:
        text = (right.get("text") or "").strip().casefold()
        if (
            text in {"publicar", "publish"}
            and right.get("class") == "android.widget.Button"
            and all(right.get(k) == "true" for k in ("focused", "focusable", "clickable", "enabled"))
        ):
            return right
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
            focused_post = None
            for step in range(0, 41):
                nodes = self.dump(f"26-post-focus-{step}", screenshot=False)
                focused_post = trusted_focused_final_post(nodes)
                if focused_post:
                    break
                keyboard.tab()
            if not focused_post:
                raise ku.KwaiUpError("hid-focus-target-timeout:trusted-final-post")
            focused_rid = focused_post.get("resource-id", "")
            # Irreversible boundary starts only after a trusted native final
            # control is itself focused. Never use a blind coordinate tap.
            self.emit(
                "PUBLISH_REQUESTED",
                job=self.cfg.job_id,
                transport="hid-uhid",
                control=focused_rid.split('/')[-1],
            )
            keyboard.enter()
'''
if old_focus not in s:
    raise SystemExit('POST_FOCUS_TARGET_NOT_FOUND')
s = s.replace(old_focus, new_focus, 1)

p.write_text(s, encoding='utf-8', newline='\n')
print('KWAI_UP_POST_VARIANTS_PATCH=APPLIED')
print('KWAI_UP_DYNAMIC_FINAL_POST_FOCUS=ENABLED')

# The same physical run must also dismiss Kwai Lite's transient downloaded-video
# guide before identity checks. Apply that patch after this file's edits.
runpy.run_path(str(Path(__file__).with_name('patch_physical_overlays.py')), run_name='__main__')
