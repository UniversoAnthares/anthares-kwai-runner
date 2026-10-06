#!/usr/bin/env python3
import base64,json,pathlib,subprocess,tempfile,os,sys
case=sys.argv[1]; root=pathlib.Path(__file__).resolve().parents[1]
title="Canário çã 🚀" if case=="unicode-title-valid" else "Canary title"
base={"job_id":"job-1","media_sha256":"0123456789abcdef","expected_account":"expected-account","observed_account_match":True,"expected_title":title,"observed_title_match":True,"profile_state":"ready"}
def tok(d): return base64.urlsafe_b64encode(json.dumps(d,separators=(",",":"),ensure_ascii=False).encode()).decode().rstrip("=")
lines=[f"KWAI_CONFIRMATION_EVIDENCE={tok(base)}","KWAI_PUBLICATION_SPECIFICALLY_VERIFIED"]; expect_ok=True; queue_ok=True
if case=="missing-marker": lines=lines[:1]; expect_ok=False
elif case=="duplicate-evidence-last-invalid": lines=[lines[0],"KWAI_CONFIRMATION_EVIDENCE=bad","KWAI_PUBLICATION_SPECIFICALLY_VERIFIED"]; expect_ok=False
elif case=="sha-case-mismatch": base["media_sha256"]="0123456789ABCDEF"; lines=[f"KWAI_CONFIRMATION_EVIDENCE={tok(base)}","KWAI_PUBLICATION_SPECIFICALLY_VERIFIED"]; expect_ok=False
elif case=="queue-reconcile-reject": queue_ok=False; expect_ok=False
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td); (d/"kwai_reconcile_uncertain.sh").write_text((root/"kwai_reconcile_uncertain.sh").read_text())
 (d/"kwai_verify_publication.py").write_text("\n".join("print("+repr(x)+")" for x in lines)+"\n")
 (d/"kwai_queue_state.sh").write_text("#!/usr/bin/env bash\necho CALLED >> queue.calls\nexit "+("0" if queue_ok else "1")+"\n"); os.chmod(d/"kwai_queue_state.sh",0o755)
 env=os.environ|{"KWAI_QUEUE_JOB_ID":"job-1","KWAI_VIDEO_TITLE":title,"KWAI_EXPECTED_ACCOUNT":"expected-account","KWAI_MEDIA_SHA256":"0123456789abcdef"}
 p=subprocess.run(["bash","kwai_reconcile_uncertain.sh"],cwd=d,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 called=(d/"queue.calls").exists()
 ok=(p.returncode==0 and called and "STATE=CONFIRMED" in p.stdout) if expect_ok else (p.returncode==90 and "STATE=UNCERTAIN" in p.stdout)
 print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_")); print(p.stdout); raise SystemExit(0 if ok else 1)
