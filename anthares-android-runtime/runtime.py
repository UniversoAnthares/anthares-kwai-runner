"""Anthares Android Runtime: backend discovery, ADB transport and conservative recovery."""
import argparse, json, os, pathlib, re, subprocess, time, datetime

ROOT = pathlib.Path(os.environ.get("ANTHARES_ANDROID_HOME", r"C:\ProgramData\AntharesAndroidRuntime"))
MEMU = pathlib.Path(os.environ.get("MEMU_HOME", r"D:\Program Files\Microvirt\MEmu"))
MANAGER = pathlib.Path(os.environ.get("MEMU_MANAGER", r"D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe"))
MEMUC = MEMU / "memuc.exe"
VM = "MEmu_4"
VM_INDEX = "4"

def run(argv, timeout=12, env=None):
    try:
        proc_env=os.environ.copy()
        if env: proc_env.update(env)
        p=subprocess.run([str(a) for a in argv],capture_output=True,text=True,timeout=timeout,errors="replace",env=proc_env)
        return {"ok":p.returncode==0,"code":p.returncode,"stdout":p.stdout[-5000:],"stderr":p.stderr[-2000:]}
    except (OSError,subprocess.TimeoutExpired) as e:
        return {"ok":False,"code":None,"stdout":"","stderr":type(e).__name__}

def info():
    r=run([MANAGER,"showvminfo",VM,"--machinereadable"])
    s=r["stdout"]
    state=re.search(r'^VMState="([^"]+)"',s,re.M)
    port=re.search(r'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),',s)
    return {"vm":VM,"vm_state":state.group(1) if state else "unknown","serial":"127.0.0.1:"+port.group(1) if port else None,"manager_ok":r["ok"]}

def adb(args,serial=None,timeout=12):
    exe=MEMU/"adb.exe"
    return run([exe]+(["-s",serial] if serial else [])+list(args),timeout)

def devices():
    r=adb(["devices","-l"])
    entries={}
    for line in r["stdout"].splitlines()[1:]:
        parts=line.split()
        if len(parts)>=2: entries[parts[0]]=parts[1]
    return {"ok":r["ok"],"devices":entries}

def health():
    vm=info(); ds=devices(); serial=vm["serial"]
    transport=ds["devices"].get(serial,"missing") if serial else "missing"
    result={"backend":"memu4",**vm,"transport_state":transport,"android_ready":False,"score":0}
    if vm["vm_state"]=="running": result["score"]+=25
    if transport=="device":
        result["score"]+=35
        boot=adb(["shell","getprop","sys.boot_completed"],serial)
        result["android_ready"]=boot["stdout"].strip()=="1"
        if result["android_ready"]: result["score"]+=40
    result["state"]=("ANDROID_READY" if result["android_ready"] else "RUNNING_TRANSPORT_OFFLINE" if vm["vm_state"]=="running" and transport!="device" else "STOPPED" if vm["vm_state"]!="running" else "ANDROID_BOOTING")
    return result

def record(operation,result):
    ROOT.mkdir(parents=True,exist_ok=True)
    event={"time":datetime.datetime.now(datetime.timezone.utc).isoformat(),"operation":operation,"result":result}
    with (ROOT/"events.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(event,ensure_ascii=False)+"\n")
    (ROOT/"state.json").write_text(json.dumps(event,indent=2),encoding="utf-8")
    return result

def start_memu_official():
    return run([MEMUC,"start","-i",VM_INDEX],timeout=35,env={"__COMPAT_LAYER":"RunAsInvoker"})

def recover(allow_vm_restart=False):
    h=health(); serial=h["serial"]
    if h["android_ready"]: return record("recover",{"ok":True,"action":"already_ready","health":h})
    if h["vm_state"]!="running":
        if h["vm_state"] not in ("poweroff","aborted","saved"): return record("recover",{"ok":False,"reason":"unexpected_vm_state","health":h})
        start=start_memu_official()
        if not start["ok"]: return record("recover",{"ok":False,"reason":"start_failed","detail":start})
    if not serial: return record("recover",{"ok":False,"reason":"serial_missing"})
    steps=[["disconnect",serial],["connect",serial],["kill-server"],["start-server"],["connect",serial]]
    for step in steps:
        adb(step)
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            h=health()
            if h["android_ready"]:return record("recover",{"ok":True,"action":"adb_recovered","health":h})
            time.sleep(1)
    if allow_vm_restart:
        return record("recover",{"ok":False,"reason":"vm_restart_requires_session_safety_validation","health":health()})
    return record("recover",{"ok":False,"reason":"transport_recovery_exhausted","health":health()})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["status","health","devices","backends","recover","screenshot","foreground","packages","launch"])
    p.add_argument("--package",default="")
    a=p.parse_args()
    h=health()
    if a.action in ("status","health","backends"):out=h
    elif a.action=="devices":out=devices()
    elif a.action=="recover":out=recover()
    elif h["transport_state"]!="device":out={"ok":False,"reason":"transport_unavailable","health":h}
    elif a.action=="foreground":out=adb(["shell","dumpsys","window","windows"],h["serial"])
    elif a.action=="packages":out=adb(["shell","pm","list","packages"],h["serial"])
    elif a.action=="launch":out=adb(["shell","monkey","-p",a.package,"1"],h["serial"]) if a.package else {"ok":False,"reason":"package_required"}
    else:
        target=ROOT/"screenshot.png";target.parent.mkdir(parents=True,exist_ok=True)
        r=run([MEMU/"adb.exe","-s",h["serial"],"exec-out","screencap","-p"])
        out={"ok":False,"reason":"binary_screenshot_requires_streaming_implementation"}
    print(json.dumps(out,ensure_ascii=False,default=str))
if __name__=="__main__":main()
