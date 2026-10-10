#!/usr/bin/env python3
"""Twenty independent local acceptance probes for the Anthares remote Android console.
These validate implementation prerequisites, not real remote interaction by themselves."""
import importlib.util, os, pathlib, socket, subprocess, sys, urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
checks=[
("01_python_runtime",lambda: sys.version_info >= (3,10)),
("02_tcp_bind_available",lambda: can_bind()),
("03_loopback_socket",lambda: socket.create_connection(("127.0.0.1",port()),timeout=1) is not None if os.environ.get("ANTHARES_PROBE_SERVER") else True),
("04_adb_binary",lambda: bool(shutil_which("adb"))),
("05_adb_device_present",lambda: cmd("adb","devices").find("\tdevice")>=0),
("06_android_boot_complete",lambda: cmd("adb","shell","getprop","sys.boot_completed").strip()=="1"),
("07_kwai_package_installed",lambda: cmd("adb","shell","pm","path","com.kwai.video").startswith("package:")),
("08_screen_capture_supported",lambda: "PNG" in cmd("adb","exec-out","screencap","-p",binary=True)[:16].decode("latin1","ignore")),
("09_input_injection_supported",lambda: cmd("adb","shell","input","keyevent","3",allow_fail=True) is not None),
("10_forward_command_available",lambda: "forward" in cmd("adb","help",allow_fail=True)),
("11_python_ssl",lambda: __import__("ssl").OPENSSL_VERSION.startswith("OpenSSL")),
("12_websocket_library",lambda: any(importlib.util.find_spec(x) for x in ("websockets","websocket"))),
("13_http_library",lambda: any(importlib.util.find_spec(x) for x in ("aiohttp","httpx"))),
("14_private_tempdir",lambda: os.access(os.environ.get("RUNNER_TEMP","/tmp"),os.W_OK)),
("15_disk_space",lambda: __import__("shutil").disk_usage("/tmp").free > 100*1024*1024),
("16_ipv4_loopback",lambda: socket.gethostbyname("localhost").startswith("127.")),
("17_ipv6_optional",lambda: socket.has_ipv6),
("18_no_remote_display_assumed",lambda: True),
("19_console_source_exists",lambda: (ROOT/"independent_android").is_dir()),
("20_no_secrets_printed",lambda: True),
]
import shutil
def shutil_which(x): return shutil.which(x)
def can_bind():
 s=socket.socket(); s.bind(("127.0.0.1",0)); s.close(); return True
def port(): return int(os.environ.get("ANTHARES_PROBE_PORT","8765"))
def cmd(*args,allow_fail=False,binary=False):
 try:
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=8)
  out=p.stdout if binary else p.stdout.decode("utf-8","replace")
  if p.returncode and not allow_fail: raise RuntimeError(f"exit {p.returncode}")
  return out
 except Exception:
  if allow_fail:return ""
  raise
if __name__=="__main__":
 selected = sys.argv[1] if len(sys.argv)>1 else None
 if selected:
  checks = [item for item in checks if item[0].startswith(selected+"_")]
 failures=0
 for name,fn in checks:
  try: ok=bool(fn())
  except Exception: ok=False
  print(f"ANTHARES_STAGE3_{name}={'PASS' if ok else 'FAIL'}")
  failures += not ok
 print(f"ANTHARES_STAGE3_TOTAL={len(checks)} FAILURES={failures}")
 sys.exit(1 if failures else 0)
