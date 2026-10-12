#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
TEST = ROOT / "tests" / "test_physical_contract.py"

def run_case(case: int):
    env=os.environ.copy(); env["KWAI_UP_CASE"]=f"{case:02d}"
    p=subprocess.run([sys.executable,str(TEST),"-v"],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60)
    return case,p.returncode,p.stdout

def main():
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        futs=[pool.submit(run_case,i) for i in range(1,31)]
        for f in concurrent.futures.as_completed(futs): out.append(f.result())
    failed=[]
    for case,rc,text in sorted(out):
        print(f"KWAI_UP_PHYSICAL_CASE={case:02d} RESULT={'PASS' if rc==0 else 'FAIL'}",flush=True)
        if rc:
            failed.append(case); print(text[-4000:],flush=True)
    if failed:
        print("KWAI_UP_PHYSICAL_30_RESULT=FAIL CASES="+','.join(f"{x:02d}" for x in failed),flush=True); return 1
    print("KWAI_UP_PHYSICAL_30_RESULT=PASS CASES=30",flush=True); return 0

if __name__ == "__main__": raise SystemExit(main())
