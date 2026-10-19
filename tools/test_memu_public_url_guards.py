import sys,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
import kwai_physical_queue_daemon as q
jid='diag-memu-url-proof-only'
folder=root/'.state'/'kwai-memu-evidence'/jid
folder.mkdir(parents=True,exist_ok=True)
p=folder/'public-link-proof.json'
url='https://k.kwai.com/p/UNITTEST123'
p.write_text(json.dumps({'ok':True,'expected_account':'lucasrosalem','public_url':url,'kind':'verified'}),encoding='utf-8')
try:
 try:
  ev=q.evidence(jid)
 except Exception as e:
  print('POSITIVE_FAILED',type(e).__name__,str(e))
  raise
 assert ev['remote_id']==url
 print('MAIN_PROOF_REAL_URL_PASS')
 p.write_text(json.dumps({'ok':True,'expected_account':'someone_else','public_url':url}),encoding='utf-8')
 try:q.evidence(jid)
 except RuntimeError:print('MAIN_PROOF_ACCOUNT_REJECTED_PASS')
 else:raise AssertionError('wrong account allowed')
finally:
 shutil.rmtree(folder)
