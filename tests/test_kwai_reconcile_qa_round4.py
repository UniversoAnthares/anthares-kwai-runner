#!/usr/bin/env python3
import base64,json,pathlib,subprocess,tempfile,os,sys
case=sys.argv[1]; root=pathlib.Path(__file__).resolve().parents[1]
b={"job_id":"job-1","media_sha256":"0123456789abcdef","expected_account":"expected-account","observed_account_match":True,"expected_title":"Canary title","observed_title_match":True,"profile_state":"ready"}
def enc(x): return base64.urlsafe_b64encode(json.dumps(x,separators=(",",":")).encode()).decode().rstrip("=")
token=enc(b); valid=False
if case=="truncated-token": token=token[:-5]
elif case=="leading-space-token": token=" "+token; valid=True
elif case=="boolean-as-string": b["observed_account_match"]="true"; token=enc(b)
elif case=="null-profile": b["profile_state"]=None; token=enc(b)
elif case=="padded-valid": token=base64.urlsafe_b64encode(json.dumps(b,separators=(",",":")).encode()).decode(); valid=True
else: raise SystemExit(2)
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td); (d/"kwai_reconcile_uncertain.sh").write_text((root/"kwai_reconcile_uncertain.sh").read_text())
 (d/"kwai_verify_publication.py").write_text(f"print('KWAI_CONFIRMATION_EVIDENCE={token}')\nprint('KWAI_PUBLICATION_SPECIFICALLY_VERIFIED')\n")
 (d/"kwai_queue_state.sh").write_text("#!/usr/bin/env bash\necho CALLED >> queue.calls\nexit 0\n");os.chmod(d/"kwai_queue_state.sh",0o755)
 env=os.environ|{"KWAI_QUEUE_JOB_ID":"job-1","KWAI_VIDEO_TITLE":"Canary title","KWAI_EXPECTED_ACCOUNT":"expected-account","KWAI_MEDIA_SHA256":"0123456789abcdef"}
 p=subprocess.run(["bash","kwai_reconcile_uncertain.sh"],cwd=d,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); called=(d/"queue.calls").exists()
 ok=(p.returncode==0 and called) if valid else (p.returncode==90 and not called)
 print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"));print(p.stdout);raise SystemExit(0 if ok else 1)
