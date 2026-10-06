#!/usr/bin/env python3
import base64,json,pathlib,subprocess,tempfile,os,sys
case=sys.argv[1]
root=pathlib.Path(__file__).resolve().parents[1]
script=root/"kwai_reconcile_uncertain.sh"
base={"job_id":"job-1","media_sha256":"0123456789abcdef","expected_account":"expected-account","observed_account_match":True,"expected_title":"Canary title","observed_title_match":True,"profile_state":"ready"}
if case=="wrong-job": base["job_id"]="job-other"
elif case=="wrong-sha": base["media_sha256"]="deadbeef"
elif case=="wrong-account": base["expected_account"]="other-account"
elif case=="wrong-title": base["expected_title"]="Other title"
elif case=="malformed": pass
else: raise SystemExit(2)
token="%%%not-base64%%%" if case=="malformed" else base64.urlsafe_b64encode(json.dumps(base,separators=(",",":")).encode()).decode().rstrip("=")
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td)
 (d/"kwai_reconcile_uncertain.sh").write_text(script.read_text())
 (d/"kwai_verify_publication.py").write_text("print('KWAI_CONFIRMATION_EVIDENCE="+token+"')\nprint('KWAI_PUBLICATION_SPECIFICALLY_VERIFIED')\n")
 (d/"kwai_queue_state.sh").write_text("#!/usr/bin/env bash\necho CALLED >> queue.calls\nexit 0\n")
 os.chmod(d/"kwai_queue_state.sh",0o755)
 env=os.environ|{"KWAI_QUEUE_JOB_ID":"job-1","KWAI_VIDEO_TITLE":"Canary title","KWAI_EXPECTED_ACCOUNT":"expected-account","KWAI_MEDIA_SHA256":"0123456789abcdef"}
 p=subprocess.run(["bash","kwai_reconcile_uncertain.sh"],cwd=d,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 calls=(d/"queue.calls").exists()
 # Safe behavior: reject forged/stale evidence before central reconcile.
 if p.returncode==90 and not calls and "STATE=UNCERTAIN" in p.stdout:
  print("PROVEN_REJECT_"+case.upper().replace("-","_")); raise SystemExit(0)
 print("VULNERABLE_"+case.upper().replace("-","_"))
 print(p.stdout)
 raise SystemExit(1)

# rerun after evidence-binding hardening
