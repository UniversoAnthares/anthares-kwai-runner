#!/usr/bin/env python3
from pathlib import Path

p = Path(__file__).with_name('kwai_up_physical.py')
s = p.read_text(encoding='utf-8')

old = '''PROFILE_TAB_ID = f"{BASIS}/id_home_bottom_tab_me"
RECORD_ID = f"{BASIS}/id_record_layout"
'''
new = '''PROFILE_TAB_ID = f"{BASIS}/id_home_bottom_tab_me"
VIDEO_GUIDE_CLOSE_ID = f"{BASIS}/video_guide_close"
RECORD_ID = f"{BASIS}/id_record_layout"
'''
if old not in s:
    raise SystemExit('OVERLAY_CONSTANT_TARGET_NOT_FOUND')
s = s.replace(old, new, 1)

old = '''        with HIDKeyboard(self.adb, 311) as keyboard:
            self.focus_profile_tab(keyboard, "06-profile-tab")
            keyboard.enter()
            time.sleep(2)
'''
new = '''        with HIDKeyboard(self.adb, 311) as keyboard:
            overlay_nodes = self.dump("06-physical-auth-overlays", screenshot=False)
            if ku.find_id(overlay_nodes, VIDEO_GUIDE_CLOSE_ID):
                self.focus_target(keyboard, VIDEO_GUIDE_CLOSE_ID, "06-video-guide-close", max_steps=12)
                keyboard.enter()
                time.sleep(1)
            self.focus_profile_tab(keyboard, "06-profile-tab")
            keyboard.enter()
            time.sleep(2)
'''
if old not in s:
    raise SystemExit('OVERLAY_VERIFY_TARGET_NOT_FOUND')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8', newline='\n')
print('KWAI_UP_PHYSICAL_OVERLAYS_PATCH=APPLIED')
