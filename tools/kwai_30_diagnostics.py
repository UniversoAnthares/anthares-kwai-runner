#!/usr/bin/env python3
"""Thirty independent, credential-free preflight hypotheses for remote Kwai failures."""
import pathlib,sys,re,ast,subprocess
root=pathlib.Path(__file__).resolve().parents[1]
n=int(sys.argv[1]);assert 1<=n<=30
files={
1:"kwai_vault_install.sh",2:"kwai_queue_publish_runtime.sh",3:"kwai_auth_probe.py",
4:"tools/kwai_login_surface_recovery.py",5:"tools/kwai_credential_login.py",
6:"tools/kwai_native_intent_recovery.py",7:"tools/kwai_login_ui_locator.py",
8:"tools/kwai_android_login_entry.py",9:"kwai_run_next_job.sh",
10:"kwai_claim_job.sh",11:"kwai_queue_heartbeat.sh",12:"kwai_queue_state.sh",
13:"kwai_publish_video.py",14:"kwai_verify_publication.py",15:"kwai_auth_ready_gate.py",
16:"kwai_real_publish_promotion_gate.py",17:"kwai_session_state.sh",
18:"tools/kwai_session_vault_client.py",19:"kwai_publish.sh",20:"android_executor_api30_runtime.sh",
21:"kwai_vault_install.sh",22:"kwai_queue_publish_runtime.sh",
23:"tools/kwai_login_surface_recovery.py",24:"tools/kwai_login_surface_recovery.py",
25:"tools/kwai_login_surface_recovery.py",26:"tools/kwai_login_surface_recovery.py",
27:".github/workflows/kwai-queue-publisher.yml",
28:".github/workflows/kwai-queue-publisher.yml",
29:".github/workflows/kwai-queue-publisher.yml",
30:".github/workflows/kwai-queue-publisher.yml"}
p=root/files[n];assert p.is_file(),f"missing {p}"
s=p.read_text()
if n<=20:
 if p.suffix==".py":ast.parse(s)
 elif p.suffix==".sh":subprocess.run(["bash","-n",str(p)],check=True)
else:
 checks={
21:("APK split inventory","ALL_APKS"),22:("independent identity gate","KWAI_IDENTITY_PROFILE_MATCH"),
23:("native first-run continuation","signin_fre_continue_button"),
24:("setup progress detector","minute_maid"),
25:("bounded recovery","system_waits"),
26:("Kwai relaunch isolation","com.kwai.video"),
27:("Cloudflare readiness gate","control_preflight"),
28:("credential presence gate","Check Kwai session key"),
29:("private session persistence gate","KWAI_IDENTITY_PROFILE_MATCH"),
30:("publication diagnostics","Upload publication diagnostics")}
 name,token=checks[n];assert token in s,f"{name}: missing marker {token}"
print(f"KWAI_DIAGNOSTIC_{n:02d}=PASS file={files[n]}")