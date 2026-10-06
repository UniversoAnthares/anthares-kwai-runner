from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
FILES=["cloudflare-worker/src/index.js","direct-tiktok-publisher/publisher_common.py","direct-tiktok-publisher/tiktok_worker.py","direct-tiktok-publisher/tiktok_web_publish.py","direct-tiktok-publisher/tiktok_cloud_publish.py","kwai_run_next_job.sh","kwai_claim_job.sh","kwai_queue_state.sh","kwai_queue_heartbeat.sh","kwai_publish.sh",".github/workflows/kwai-real-publish.yml",".github/workflows/tiktok-real-publish.yml",".github/workflows/tiktok-github-direct-publisher.yml"]
forbidden={"memu":r"MEmu","local-executor-env":r"LOCAL_EXECUTOR_[A-Z0-9_]+","cookie-bridge":r"Cookie[ _-]?Bridge","windows-user-path":r"C:[\\/]Users[\\/]","anthares-d-drive":r"D:[\\/]AntharesWork[\\/]","self-hosted-runner":r"runs-on:\s*.*self-hosted","windows-runner":r"runs-on:\s*(?:\[[^\]]*)?windows(?:-|\b)","scheduled-task":r"\bschtasks\b"}
viol=[]
for rel in FILES:
 p=ROOT/rel; assert p.exists(), rel
 text=p.read_text(encoding="utf-8-sig")
 for name,pat in forbidden.items():
  flags=0 if name=="local-executor-env" else re.I
  if re.search(pat,text,flags): viol.append((rel,name))
worker=(ROOT/"cloudflare-worker/src/index.js").read_text(encoding="utf-8-sig")
assert 'const RETIRED_EXECUTORS=new Set(["local","pc","windows","oracle","google","google_compute"])' in worker
m=re.search(r'function priorities\(\)\{return (\{.*?\});\}',worker); assert m
for retired in ('local','pc','windows','oracle','google','google_compute'):
 assert f'"{retired}"' not in m.group(1), (retired,m.group(1))
for signal in ('recovery_returns_render','retired_injected_never_selected','stale_heartbeat_github','circuit_breaker_github','capacity_github'):
 assert signal in worker, signal
assert worker.count('error:"retired_executor"') >= 3, 'retired executor not rejected across auth/heartbeat/job surfaces'
assert not (ROOT/"direct-tiktok-publisher/tiktok_web_publish_local.py").exists(), "legacy local-named publisher still tracked"
assert "tiktok_web_publish_local.py" not in (ROOT/".github/workflows/tiktok-github-direct-publisher.yml").read_text(encoding="utf-8-sig")
assert not viol, viol
print("CLOUD_ONLY_RUNTIME=PROVEN")
