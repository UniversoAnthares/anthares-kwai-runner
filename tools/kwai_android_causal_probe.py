#!/usr/bin/env python3
"""Privacy-minimal Android diagnosis: no log messages, URLs, account identifiers or UI dumps."""
import json
import re
import subprocess
from collections import Counter

PACKAGE="com.kwai.video"
ALLOWED_TAGS={"ActivityManager","ActivityTaskManager","AndroidRuntime","libc","PackageManager","WindowManager"}
ERROR_TYPES={
    "process_crash": re.compile(r"FATAL EXCEPTION|Fatal signal|Process .* has died|crash",re.I),
    "application_not_responding":re.compile(r"ANR in|not responding|Input dispatching timed out",re.I),
    "activity_launch_failure":re.compile(r"Unable to start activity|ActivityNotFoundException|Permission Denial.*start",re.I),
    "network_failure":re.compile(r"UnknownHostException|ConnectException|SocketTimeoutException|SSLHandshakeException",re.I),
}
LINE=re.compile(r"^\S+\s+\S+\s+\d+\s+\d+\s+([VDIWEF])\s+(\S+?):\s+(.*)$")

def classify(log_text):
    counts=Counter()
    for line in log_text.splitlines()[:12000]:
        match=LINE.match(line)
        if not match:
            continue
        level,tag,message=match.groups()
        if tag not in ALLOWED_TAGS or level not in "WEF":
            continue
        if PACKAGE not in message and tag not in {"AndroidRuntime","libc"}:
            continue
        for key,pattern in ERROR_TYPES.items():
            if pattern.search(message):
                counts[key]+=1
    return {"schema":"anthares.mobile.android-causal.v1",
            "signals":{k:min(counts[k],999) for k in ERROR_TYPES},
            "events_detected":sum(counts.values())}

def adb(*args,timeout=12):
    try:
        return subprocess.run(["adb",*args],capture_output=True,text=True,timeout=timeout,check=True).stdout
    except (OSError,subprocess.SubprocessError):
        return ""

def main():
    # Only system and crash buffers. Never export raw logcat or UI XML.
    raw=adb("logcat","-b","system","-b","crash","-d","-t","2500","-v","threadtime",timeout=18)
    report=classify(raw)
    report["app_installed"]=bool(adb("shell","pm","path",PACKAGE))
    report["app_process_running"]=bool(adb("shell","pidof",PACKAGE).strip())
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
