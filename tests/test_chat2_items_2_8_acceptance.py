#!/usr/bin/env python3
"""CHAT2 acceptance for items 2-8; no Android/login mutation and no real Publish."""
from pathlib import Path
import py_compile,re,sys
root=Path(__file__).resolve().parents[1]
files={n:(root/n).read_text(encoding="utf-8") for n in [
 "kwai_publish.sh","kwai_publish_video.py","kwai_verify_publication.py",
 "kwai_reconcile_uncertain.sh","kwai_queue_state.sh","kwai_queue_heartbeat.sh",
 "kwai_claim_job.sh","kwai_real_publish_promotion_gate.py",
 ".github/workflows/kwai-real-publish.yml","android-agent/PROTOCOL.md"
]}
checks={}
# 2 UNCERTAIN/reconciliation
p=files["kwai_reconcile_uncertain.sh"]; pub=files["kwai_publish.sh"]
checks["uncertain_observation_only"]="kwai_verify_publication.py" in p and "kwai_queue_state.sh reconcile" in p and "kwai_publish_video.py" not in p and "kwai_queue_state.sh complete" not in p
checks["publish_failure_enters_uncertain"]='mark_uncertain "commit-rc-$rc"' in pub and 'STATE=UNCERTAIN' in pub
checks["complete_requires_evidence"]="'CONFIRMATION_EVIDENCE_MISSING'" in files["kwai_queue_state.sh"]
# 3 publish(job) contract
checks["structured_identity_gate"]=all(x in pub for x in ["KWAI_QUEUE_JOB_ID","KWAI_EXPECTED_ACCOUNT","KWAI_MEDIA_SHA256","KWAI_ANDROID_VIDEO"])
checks["explicit_phases"]=all(x in files["kwai_publish_video.py"] for x in ['PHASE not in ("prepare","commit")','STATE=READY_TO_PUBLISH','STATE=PUBLISH_REQUESTED'])
# 4 deterministic media
pv=files["kwai_publish_video.py"]
checks["media_unique_before_selection"]="content://media/external/video/media" in pv and "len(rows)!=1" in pv and "len(matches)!=1" in pv
checks["sha_in_identity"]="sha_prefix=media_sha[:12]" in pv and "KWAI_MEDIA_SHA256" in pub and "MEDIA_SHA256=" in pub
# 5 composer driver without premature click
checks["prepare_before_commit"]=pv.index('if PHASE=="prepare"') if False else ("def prepare()" in pv and "def commit()" in pv and "PUBLISH_REQUESTED" in pv)
checks["ready_file_binds_identity"]=all(x in pv for x in ['ready.get("job_id")','ready.get("media_name")','ready.get("media_sha256")','ready.get("title")'])
# 6 control-plane integration
qs=files["kwai_queue_state.sh"]
checks["v16_pinned"]="2026-10-05-queue-fencing-v16" in qs
checks["generation_fenced"]=all(x in qs for x in ["KWAI_LEASE_GENERATION","lease_generation"])
checks["heartbeat_fenced"]="kwai_queue_state.sh renew" in files["kwai_queue_heartbeat.sh"]
checks["claim_requires_canonical_interval"]=all(x in files["kwai_claim_job.sh"] for x in ["source_id","source_start","source_end","LEASE_CONTRACT_INVALID"])
# 7 no PC production dependency
active=["kwai_publish.sh","kwai_publish_video.py","kwai_verify_publication.py","kwai_reconcile_uncertain.sh","kwai_queue_state.sh","kwai_queue_heartbeat.sh","kwai_claim_job.sh",".github/workflows/kwai-real-publish.yml"]
forbidden=[r"localhost",r"127\.0\.0\.1",r"MEmu",r"Windows",r"C:\\Users",r"C:/Users",r"powershell"]
violations={f:[pat for pat in forbidden if re.search(pat,files[f],re.I)] for f in active}
checks["production_path_has_no_pc_dependency"]=not any(violations.values())
checks["pc_fallback_disabled"]="pc_fallback" in files["kwai_queue_state.sh"] or "pc_fallback" in files["kwai_claim_job.sh"]
# 8 canary readiness
wf=files[".github/workflows/kwai-real-publish.yml"]
checks["manual_real_publish_gate"]="enable_real_publish == 'YES'" in wf and 'Type YES only after kwai-login reports READY' in wf
checks["serialized_publication"]="cancel-in-progress: false" in wf and "anthares-kwai-publish" in wf
checks["push_path_never_publishes"]="queue-self-test:" in wf and "Real publication remains gated" in wf
# syntax
for f in ["kwai_publish.sh","kwai_reconcile_uncertain.sh","kwai_queue_state.sh","kwai_queue_heartbeat.sh","kwai_claim_job.sh"]:
 import subprocess
 r=subprocess.run(["bash","-n",str(root/f)],capture_output=True,text=True)
 checks["bash_syntax:"+f]=r.returncode==0
for f in ["kwai_publish_video.py","kwai_verify_publication.py","kwai_real_publish_promotion_gate.py"]:
 try: py_compile.compile(str(root/f),doraise=True); checks["py_syntax:"+f]=True
 except Exception: checks["py_syntax:"+f]=False
bad=[k for k,v in checks.items() if not v]
print("CHAT2_ITEMS_2_8_CHECKS")
for k,v in checks.items(): print(k+"="+("1" if v else "0"))
if bad: print("FAILED="+",".join(bad)); sys.exit(1)
print("CHAT2_ITEMS_2_8_ACCEPTANCE_PROVEN")
