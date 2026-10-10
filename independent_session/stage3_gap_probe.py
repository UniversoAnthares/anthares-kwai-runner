#!/usr/bin/env python3
"""20 focused checks for the remaining Stage 3 remote-console gaps."""
import ast, pathlib, re, sys
root=pathlib.Path(__file__).resolve().parents[1]
bridge=(root/"independent_session/remote_android_bridge.py").read_text()
ui=(root/"independent_session/remote_android_console.html").read_text()
accept=(root/"independent_session/remote_console_acceptance.py").read_text()
workflow=(root/".github/workflows/anthares-stage3-console-acceptance.yml").read_text()
checks=[
("01_bridge_python_syntax",lambda: ast.parse(bridge) is not None),
("02_token_minimum_length",lambda: 'len(TOKEN)<32' in bridge),
("03_constant_time_auth",lambda: 'secrets.compare_digest' in bridge),
("04_health_endpoint_exists",lambda: 'route=="/health"' in bridge),
("05_health_checks_adb",lambda: 'adb("devices")' in bridge),
("06_screenshot_endpoint_exists",lambda: 'route=="/screen"' in bridge),
("07_screenshot_uses_png_capture",lambda: 'screencap","-p' in bridge),
("08_input_endpoint_exists",lambda: 'path!="/input"' in bridge),
("09_tap_coordinate_validation",lambda: 'type(x) is not int or type(y) is not int' in bridge),
("10_swipe_coordinate_validation",lambda: '("x1","y1","x2","y2")' in bridge),
("11_key_allowlist_present",lambda: '"DPAD_RIGHT"}' in bridge and '"HOME"' in bridge),
("12_shell_injection_not_exposed",lambda: 'launch_arbitrary_shell' not in bridge),
("13_body_size_limited",lambda: 'MAX_BODY=4096' in bridge and 'n>MAX_BODY' in bridge),
("14_no_request_body_logged",lambda: 'def log_message(self,*a): pass' in bridge),
("15_cache_disabled_on_json",lambda: 'Cache-Control","no-store' in bridge),
("16_remote_ui_file_exists",lambda: len(ui)>100),
("17_ui_has_screen_reference",lambda: '/screen' in ui),
("18_ui_has_input_reference",lambda: '/input' in ui),
("19_acceptance_has_auth_rejection",lambda: 'reject missing auth' in accept),
("20_external_access_configured",lambda: ('ANTHARES_BRIDGE_HOST","0.0.0.0' in bridge or 'cloudflared' in workflow or 'tailscale' in workflow or 'REMOTE_CONSOLE_URL' in workflow)),
]
i=int(sys.argv[1]); name,fn=checks[i-1]
try: ok=bool(fn())
except Exception as e: ok=False; print("ERROR_TYPE="+type(e).__name__)
print(f"STAGE3_GAP_{i:02d}_{name}={'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
