#!/usr/bin/env bash
set -Eeuo pipefail
base="$(find kwai-vault -type f \( -name 'com.kwai.video.apk' -o -name 'base.apk' \) -print -quit)"
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
aapt_bin="$(find "$sdk/build-tools" -type f -name aapt -perm -111 2>/dev/null | sort -V | tail -1)"
[ -f "$base" ] && [ -x "$aapt_bin" ] || { echo TEST_VALIDITY=TOOLS_OR_APK_MISSING; exit 90; }
"$aapt_bin" dump xmltree "$base" AndroidManifest.xml > manifest-tree.txt
python3 - <<'PY'
import re
s=open("manifest-tree.txt",errors="ignore").read().splitlines()
blocks=[]; cur=[]
for line in s:
 if re.match(r'\s*E: activity(?:-alias)? ',line):
  if cur: blocks.append(cur)
  cur=[line]
 elif cur:
  if re.match(r'\s*E: (service|receiver|provider|activity(?:-alias)?) ',line):
   blocks.append(cur);cur=[]
   if "activity" in line: cur=[line]
  else: cur.append(line)
if cur: blocks.append(cur)
keys=("login","auth","account","profile","user","signin","signup","authorization")
hits=[]
for b in blocks:
 t="\n".join(b)
 name=re.search(r'android:name[^=]*="([^"]+)"',t)
 exported=re.search(r'android:exported[^=]*=\(type 0x12\)(0xffffffff|0x0)',t)
 has_filter="E: intent-filter" in t
 if name and any(k in name.group(1).lower() for k in keys) and (has_filter or exported):
  hits.append((name.group(1),has_filter, exported.group(1) if exported else "implicit"))
for x in hits: print("CANDIDATE=%s INTENT_FILTER=%s EXPORTED_RAW=%s"%x)
print("CANDIDATE_COUNT="+str(len(hits)))
PY
echo TEST_VALIDITY=OK
