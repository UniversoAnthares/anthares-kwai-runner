#!/usr/bin/env python3
import base64,json,pathlib,subprocess,tempfile,os,sys
case=sys.argv[1]; root=pathlib.Path(__file__).resolve().parents[1]
d0={"job_id":"job-1","media_sha256":"0123456789abcdef","expected_account":"expected-account","observed_account_match":True,"expected_title":"Canary title","observed_title_match":True,"profile_state":"ready"}
valid=False
if case=="observed-account-false": d0["observed_account_match"]=False
elif case=="observed-title-false": d0["observed_title_match"]=False
elif case=="profile-not-ready": d0["profile_state"]="loading"
elif case=="evidence-empty-object": d0={}
elif case=="evidence-extra-valid": d0["extra"]="ignored"; valid=True
else: raise SystemExit(2)
tok=base64.urlsafe_b64encode(json.dumps(d0,separators=(",",":")).encode()).decode().rstrip("=")
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td)
 for n in ["kwai_reconcile_uncertain.sh"]:
  (d/n).write_text((root/n).read_text())
 (d/"kwai_verify_publication.py").write_text(f"print('KWAI_CONFIRMATION_EVIDENCE={tok}')\nprint('KWAI_PUBLICATION_SPECIFICALLY_VERIFIED')\n")
 (d/"kwai_queue_state.sh").write_text("#!/usr/bin/env bash\necho CALLED >> queue.calls\nexit 0\n"); os.chmod(d/"kwai_queue_state.sh",0o755)
 env=os.environ|{"KWAI_QUEUE_JOB_ID":"job-1","KWAI_VIDEO_TITLE":"Canary title","KWAI_EXPECTED_ACCOUNT":"expected-account","KWAI_MEDIA_SHA256":"0123456789abcdef"}
 p=subprocess.run(["bash","kwai_reconcile_uncertain.sh"],cwd=d,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 called=(d/"queue.calls").exists()
 ok=(p.returncode==0 and called and "STATE=CONFIRMED" in p.stdout) if valid else (p.returncode==90 and not called and "STATE=UNCERTAIN" in p.stdout)
 print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_")); print(p.stdout)
 raise SystemExit(0 if ok else 1)
